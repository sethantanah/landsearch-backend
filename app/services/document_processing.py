import base64
from pathlib import Path
from typing import Union, Optional
from PIL import Image
import pdf2image
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import requests
import backoff
import json
from dataclasses import dataclass
from enum import Enum

from openai import OpenAI
import google.generativeai as genai

from app.config.settings import Settings
from app.services.site_data_processing import LandDataProcessor
from app.utils.json_processing import JSONProcessor
from app.utils.logging import setup_logging

logger = setup_logging(app_name=__name__, log_dir="logs")


class DocumentType(Enum):
    PDF = "pdf"
    IMAGE = "image"


class AIModelType(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass
class ProcessingResult:
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


MAX_RETRIES: int = 1


class DocumentProcessor:
    def __init__(self, settings: Settings):
        self.max_retries = settings.MAX_RETRIES
        self.settings = settings
        self.retry_queue = Queue()
        self.ai_client = OpenAI()
        self.executor = ThreadPoolExecutor(max_workers=3)

    def process_document(
        self,
        file_path: Union[str, Path],
        original_file_path: Union[str, Path],
        model_type=AIModelType.GEMINI.value,
    ) -> ProcessingResult:
        """Main entry point for document processing."""
        try:
            file_path = Path(file_path)
            logger.info(f"Starting processing of {file_path}")

            # Determine document type
            original_file_path = Path(original_file_path)
            doc_type = self._get_document_type(original_file_path)

            # Convert to image if PDF
            if doc_type == DocumentType.PDF:
                image = self._convert_pdf_to_image(file_path)
            else:
                image = self._load_image(file_path)

            # Process image
            return self._process_image(image, model_type)

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return ProcessingResult(success=False, error=str(e))

    @staticmethod
    def _get_document_type(file_path: Path) -> DocumentType:
        """Determine the type of document based on file extension."""
        if file_path.suffix.lower() == ".pdf":
            return DocumentType.PDF
        return DocumentType.IMAGE

    @backoff.on_exception(backoff.expo, Exception, max_tries=MAX_RETRIES)
    def _convert_pdf_to_image(self, file_path: Path) -> Image.Image:
        """Convert PDF to image with retry mechanism."""
        logger.info(f"Converting PDF to image: {file_path}")
        try:
            images = pdf2image.convert_from_path(file_path)
            return images[-1]  # Return first page
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise

    @staticmethod
    def _load_image(file_path: Path) -> Image.Image:
        """Load image file with basic validation."""
        try:
            image = Image.open(file_path)
            return image
        except Exception as e:
            logger.error(f"Image loading failed: {str(e)}")
            raise

    def _process_image(self, image: Image.Image, model_type: str) -> ProcessingResult:
        """Process image through LLM with retry mechanism."""
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Prepare image for LLM
                processed_image = self._preprocess_image(image)
                logger.info("Image processing complete")

                # Send to LLM for extraction
                logger.info("LLM Processing Started")
                result = self._send_to_llm(processed_image, model_type)
                logger.info("LLM Processing Completed")

                # process extracted data
                logger.info("Validation and Processing Started")
                result = JSONProcessor.extract_json_safely(
                    result
                )

                # result = {
                #     "owners": ["TRANSPORT RESEARCH & EDUCATION CENTRE, KUMASI (TRECK)"],
                #     "plot_number": "15B",
                #     "date": "02/02/2022",
                #     "area": "1.78",
                #     "metric": "Acres (0.72 Ha)",
                #     "scale": "1: 2500",
                #     "locality": "KNUST",
                #     "district": "OFORIKROM",
                #     "region": "ASHANTI",
                #     "other_location_details": "Research Hills",
                #     "surveyors_name": "DR. A. ARKO-ADJEI",
                #     "surveyors_location": "P.O BOX UP 1703 KNUST-KUMASI",
                #     "surveyors_reg_number": "316",
                #     "regional_number": None,
                #     "reference_number": None,
                #     "site_plan_data": {
                #         "plan_data": {
                #             "from": [
                #                 "KNUST.TREK.10/2021/1",
                #                 "KNUST.TREK.10/2021/2",
                #                 "KNUST.TREK.10/2021/3",
                #                 "KNUST.TREK.10/2021/4",
                #                 "KNUST.TREK.10/2021/5",
                #                 "KNUST.CEPB.10/2021/2",
                #                 "KNUST.CEPB.10/2021/3",
                #                 "SGA.CORS 2020 3",
                #             ],
                #             "x_coords": [
                #                 724125.686,
                #                 724103.844,
                #                 724089.96,
                #                 724057.009,
                #                 724197.311,
                #                 724330.685,
                #                 724294.927,
                #                 732285.928,
                #             ],
                #             "ref": [True, True, True, True, True, True, True, True],
                #             "y_coords": [
                #                 695158.748,
                #                 695149.339,
                #                 695129.526,
                #                 694842.085,
                #                 694820.23,
                #                 695135.853,
                #                 694811.094,
                #                 673148.096,
                #             ],
                #             "bearing": [],
                #             "distance": [],
                #             "to": [],
                #         },
                #         "north_easterns": {
                #             "norths": [694500, 695500],
                #             "easterns": [723500, 724500],
                #         },
                #     },
                # }

                result = self._process_site_data(result)
                logger.info("Validation and Processing Completed")

                # # Validate result
                if result:  # self._validate_result(result):
                    logger.info("Document processed successfully")
                    return ProcessingResult(
                        success=True, data={"image": processed_image, "results": result}
                    )

                logger.warning("Invalid result received, retrying...")
                retry_count += 1

            except Exception as e:
                logger.error(f"Processing attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                time.sleep(2**retry_count)  # Exponential backoff

        return ProcessingResult(success=False, error="Max retries exceeded")

    @staticmethod
    def _preprocess_image(image: Image.Image) -> Image.Image:
        """Preprocess image before sending to LLM."""
        # Add image preprocessing steps here (resize, enhance, etc.)
        return image

    @backoff.on_exception(
        backoff.expo, requests.exceptions.RequestException, max_tries=MAX_RETRIES
    )
    def _send_to_llm(self, image: Image.Image, model_type: str = "OPENAI") -> dict:
        """Send image to LLM for analysis."""

        prompt: str = """
                The provided document contains a sample site plan. 
                The objective is to extract and structure specific information accurately. 
                ### Target Data to Extract:
                1. **Landowners**: Names of the landowners. Look for text starting with **FOR:** on the land plan.
                2. **Plot Number**: The plot number of the site plan.
                3. **Date**: The date mentioned in the document, if specified.
                4. **Area**: The area of the site plan.
                5. **Metric**: Units of the area (e.g., hectares or acres).
                6. **Scale**: The scale of the plan.
                7. **Locality**: The locality information of the site.
                8. **District**: The district name.
                9. **Region**: The region name.
                10. **Other Location Details**: Any additional location-related details.
                11. **Surveyers Name**: The name of the surveyor.
                12. **Suryors Location**: Location of the surveyor.
                13. **Suryors Number**: The registration number of the surveyor.
                11. **Regional Number**: The regional number associated with the plan.
                12. **Reference Number**: The reference number of the document.
                13. **Site Plan Data**:
                    - **Plan Data** (if in tabular form): Extract values from headings like:
                    - `From`
                    - `X (N) Coords`
                    - `Y (E) Coords`
                    - `Bearing`
                    - `Distance`
                    - `To`
                    - **North-Eastern Coordinates**: These may be found around the site plan image, in formats like:
                    - Example: `1245500E`, `1246000E`, `400000N`, `400500N`
                    - Or as numbers without directional indicators: `1245500`, `1246000`, `400000`, `400500`
                    
                **Note!**
                For X and Y coords add another property called ref
                IF the ENDING OF FROM TEXT FROMAT IS LIKE  10/2021/1 ref is false
                IF the ENDING OF FROM TEXT FROMAT IS LIKE CORS 2023 3 OR  A001 19 1 ref is True
                This is neccesary for accuratly plotting
                

                ### Output Format:
                Return the extracted information in JSON format with the following structure:
                ```json
                {
                "owners": [],
                "plot_number": "",
                "date": "",
                "area": "",
                "metric": "",
                "scale": "",
                "locality": "",
                "district": "",
                "region": "",
                "other_location_details": "",
                "surveyors_name: "",
                "surveyors_location: "",
                "surveyors_reg_number": "",
                "regional_number": "",
                "reference_number": "",
                "site_plan_data": {
                    "plan_data": {
                    "from": [],
                    "x_coords": [],
                    "y_coords": [],
                    "bearing": [],
                    "distance": [],
                    "to": []
                    },
                    "north_easterns": {
                    "norths": [],
                    "easterns": []
                    }
                }
                }
                ```
                ### Instructions:
                - Carefully analyze the document and execute the following instructions systematically.
                - If a field is not available in the document, leave it empty in the JSON output.
                - Pay special attention to coordinates and data tables. Ensure values align with their respective fields.
                - For **site plan data**, prioritize structured table data if available. Use surrounding context for coordinate extraction when no table is present.
                """

        if model_type == "GEMINI":
            response = self._gemini_model(image, prompt)
        else:
            response = self._openai_model(image, prompt)
        return response

    def _openai_model(self, image: Image.Image, prompt: str) -> Union[str, any]:

        # Convert image to bytes
        def encode_image():
            import io

            try:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="png")
                img_byte_arr = img_byte_arr.getvalue()
            except Exception as e:
                logger.info(f"Image Conversion to Bytes Failed: {str(e)}")
                raise e
            else:
                return encode_base_64_image(img_byte_arr)

        def encode_base_64_image(image_bytes):
            return base64.b64encode(image_bytes).decode("utf-8")

        try:
            image_data = encode_image()
            logger.info("OPENAI CALL!")
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                ],
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.info(f"OPENAI Failed to Extract Site Plan Data: {str(e)}")
            raise e

    def _gemini_model(self, image: Image.Image, prompt: str) -> Union[str, any]:
        try:
            logger.info("GEMINI CALL!")
            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name=self.settings.GEMINI_MODEL)
            response = model.generate_content([prompt, image]).to_dict()
            try:
                return response["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                return response
        except Exception as e:
            logger.info(f"GEMINI Failed to Extract Site Plan Data: {str(e)}")
            raise e

    @staticmethod
    def _validate_result(result: dict) -> bool:
        """Validate LLM response."""
        required_fields = ["text", "confidence"]
        return all(field in result for field in required_fields)

    @staticmethod
    def _extract_json(text: str) -> dict:
        import re

        output_dict = {}

        if text:
            try:
                # Regex pattern to remove ```json and ```
                cleaned_text = re.sub(r"```json|```", "", text).strip()
                clean_json = json.dumps(cleaned_text)
                output_dict = json.loads(clean_json)
            except Exception:
                try:
                    output_dict = json.loads(text.strip())
                except Exception:
                    try:
                        # Regex pattern to extract JSON
                        json_pattern = r"{.*?}"
                        # Extract JSON using regex
                        json_match = re.search(json_pattern, text, re.DOTALL)
                        if json_match:
                            json_data = json_match.group(0)  # Get the matched JSON
                            clean_json = json.dumps(json_data)
                            output_dict = json.loads(clean_json)
                        else:
                            return None
                    except Exception:
                        return None

            if not isinstance(output_dict, dict):
                output_dict = json.loads(output_dict)
            return output_dict

    @staticmethod
    def _process_site_data(site_data) -> dict:
        try:
            processor = LandDataProcessor()
            results = processor.process_land_data(site_data)
            return results
        except Exception as e:
            logger.error(f"Failed to Process Site Data: {str(e)}")
            return None
