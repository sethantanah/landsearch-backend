import json
from logging import Logger
import re
from typing import Dict, Optional
from app.utils.logging import setup_logging


logger = setup_logging(app_name=__name__)


class JSONExtractionError(Exception):
    """
    Custom exception for JSON extraction errors with detailed error information.

    Attributes:
        message (str): Error message
        error_type (str): Type of error encountered
        error_location (str): Where in the extraction process the error occurred
        original_error (Exception, optional): The original exception that caused this error
        input_data (str, optional): Snippet of the problematic input data
    """

    def __init__(
        self,
        message: str,
        error_type: str = "Unknown",
        error_location: str = "Unknown",
        original_error: Exception = None,
        input_data: str = None,
    ):
        self.message = message
        self.error_type = error_type
        self.error_location = error_location
        self.original_error = original_error
        self.input_data = (
            input_data[:100] if input_data else None
        )  # Limit input data length

        # Build detailed error message
        detailed_message = f"""
                JSON Extraction Error:
                - Message: {self.message}
                - Error Type: {self.error_type}
                - Location: {self.error_location}
                - Original Error: {str(self.original_error) if self.original_error else 'None'}
                - Input Data Preview: {self.input_data + '...' if self.input_data else 'None'}
                """
        super().__init__(detailed_message)

    @classmethod
    def from_parsing_error(
        cls, error: Exception, input_data: str = None
    ) -> "JSONExtractionError":
        """
        Create an extraction error from a JSON parsing error.

        Args:
            error (Exception): The original parsing error
            input_data (str, optional): The input data that caused the error

        Returns:
            JSONExtractionError: New instance with parsing error details
        """
        return cls(
            message="Failed to parse JSON data",
            error_type="ParseError",
            error_location="JSON Parser",
            original_error=error,
            input_data=input_data,
        )

    @classmethod
    def from_validation_error(
        cls, message: str, input_data: str = None
    ) -> "JSONExtractionError":
        """
        Create an extraction error from a validation failure.

        Args:
            message (str): Description of the validation failure
            input_data (str, optional): The input data that failed validation

        Returns:
            JSONExtractionError: New instance with validation error details
        """
        return cls(
            message=message,
            error_type="ValidationError",
            error_location="Data Validator",
            input_data=input_data,
        )

    @classmethod
    def from_extraction_failure(
        cls, method: str, error: Exception = None, input_data: str = None
    ) -> "JSONExtractionError":
        """
        Create an error for when extraction methods fail.

        Args:
            method (str): The extraction method that failed
            error (Exception, optional): The original error if any
            input_data (str, optional): The input data that caused the failure

        Returns:
            JSONExtractionError: New instance with extraction failure details
        """
        return cls(
            message=f"Failed to extract JSON using {method}",
            error_type="ExtractionError",
            error_location=method,
            original_error=error,
            input_data=input_data,
        )

    def get_error_dict(self) -> dict:
        """
        Get error information as a dictionary.

        Returns:
            dict: Error information in dictionary format
        """
        return {
            "message": self.message,
            "error_type": self.error_type,
            "location": self.error_location,
            "original_error": str(self.original_error) if self.original_error else None,
            "input_preview": self.input_data,
        }

    def log_error(self, logger: Logger) -> None:
        """
        Log the error using the provided logger.

        Args:
            logger: Logger instance to use for logging
        """
        logger.error(f"JSON Extraction Error: {self.message}")
        logger.debug(f"Error Type: {self.error_type}")
        logger.debug(f"Location: {self.error_location}")
        if self.original_error:
            logger.debug(f"Original Error: {str(self.original_error)}")
        if self.input_data:
            logger.debug(f"Input Preview: {self.input_data}")


class JSONProcessor:
    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """
        Extract and parse JSON from text string with enhanced error handling and logging.

        Args:
            text (str): Input text containing JSON data

        Returns:
            Optional[Dict]: Parsed JSON dictionary or None if extraction fails

        Raises:
            JSONExtractionError: If JSON extraction fails after all attempts
        """
        logger.debug("Starting JSON extraction from text")

        if not text:
            logger.warning("Empty text provided for JSON extraction")
            return None

        # Store the original text length for logging
        original_length = len(text)
        logger.debug(f"Input text length: {original_length} characters")

        def attempt_json_load(json_str: str, context: str) -> Optional[Dict]:
            """Helper function to attempt JSON loading with consistent error handling."""
            try:
                result = json.loads(json_str)
                if not isinstance(result, dict):
                    logger.debug(
                        f"{context}: Result is not a dictionary, attempting conversion"
                    )
                    # If result is a string containing JSON, try parsing it
                    if isinstance(result, str):
                        result = json.loads(result)
                if isinstance(result, dict):
                    logger.debug(f"Successfully parsed JSON in {context}")
                    return result
                else:
                    logger.debug(
                        f"{context}: Result is not a dictionary after conversion"
                    )
                    return None
            except json.JSONDecodeError as e:
                logger.debug(f"JSON parsing failed in {context}: {str(e)}")
                return None
            except Exception as e:
                logger.debug(f"Unexpected error in {context}: {str(e)}")
                return None

        # Method 1: Direct JSON parsing after cleaning markdown
        try:
            logger.debug("Attempting Method 1: Markdown cleanup and direct parsing")
            cleaned_text = re.sub(r"```json|```", "", text).strip()
            logger.debug(f"Cleaned text length: {len(cleaned_text)} characters")

            print(cleaned_text)

            clean_json = json.dumps(cleaned_text)
            result = attempt_json_load(clean_json, "Method 1")
            if result:
                return result
        except Exception as e:
            logger.debug(f"Method 1 failed: {str(e)}")

        # Method 2: Direct JSON parsing of original text
        try:
            logger.debug("Attempting Method 2: Direct parsing of original text")
            result = attempt_json_load(text.strip(), "Method 2")
            if result:
                return result
        except Exception as e:
            logger.debug(f"Method 2 failed: {str(e)}")

        # Method 3: Regex extraction and parsing
        try:
            logger.debug("Attempting Method 3: Regex extraction")
            json_pattern = r"{.*?}"
            json_match = re.search(json_pattern, text, re.DOTALL)

            if json_match:
                json_data = json_match.group(0)
                logger.debug(f"Found JSON match of length: {len(json_data)} characters")

                clean_json = json.dumps(json_data)
                result = attempt_json_load(clean_json, "Method 3")
                if result:
                    return result
            else:
                logger.debug("No JSON pattern match found")
        except Exception as e:
            logger.debug(f"Method 3 failed: {str(e)}")

        # If all methods fail
        logger.error("All JSON extraction methods failed")
        error_msg = (
            f"Failed to extract valid JSON from text of length {original_length}"
        )
        logger.error(error_msg)
        raise JSONExtractionError(error_msg)

    @classmethod
    def extract_json_safely(cls, text: str) -> Optional[Dict]:
        """
        Public wrapper method for JSON extraction with high-level error handling.

        Args:
            text (str): Input text containing JSON data

        Returns:
            Optional[Dict]: Parsed JSON dictionary or None if extraction fails
        """
        try:
            return cls._extract_json(text)
        except JSONExtractionError as e:
            logger.error(f"JSON extraction error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JSON extraction: {str(e)}")
            return None
