from typing import Dict, List, Optional
from app.schemas.schemas import ProcessedLandData

from app.services.document_storage import SuperBaseStorage
from app.utils.data_serializer import dict_to_proccessed_data_model
from app.utils.logging import setup_logging


class SuperBaseDataLoader:
    def __init__(self, storage: SuperBaseStorage):
        self.storage = storage
        self.logger = setup_logging(app_name=__name__)

    def load_all_and_validate(self, user_id: str) -> List[Optional[ProcessedLandData]]:
        """
        Load and validate the uploaded JSON file

        Args:
            uploaded_file: Uploaded file from Streamlit

        Returns:
            Validated data dictionary or None
        """
        try:
            data = self.storage.get_data_all()
            land_data: List[Optional[ProcessedLandData]] = []
            for plot in data:
                plot_data: Dict = plot["data"]
                plot_data["id"] = plot_data.get("id", str(plot["id"]))
                try:
                    plot_data = dict_to_proccessed_data_model(plot_data)
                    land_data.append(plot_data)
                except Exception:
                    continue
        except Exception as e:
            self.logger.error(f"Unexpected error in data loading: {e}")
            return None
        else:
            return land_data

    def load_and_validate(self, user_id: str) -> List[Optional[ProcessedLandData]]:
        """
        Load and validate the uploaded JSON file

        Args:
            uploaded_file: Uploaded file from Streamlit

        Returns:
            Validated data dictionary or None
        """
        try:
            data = self.storage.get_data(user_id=user_id)
            land_data: List[Optional[ProcessedLandData]] = []
            for plot in data:
                plot_data: Dict = plot["data"]
                plot_data["id"] = str(
                    plot["id"]
                )  # plot_data.get("id", str(plot["id"]))
                try:
                    plot_data = dict_to_proccessed_data_model(plot_data)
                    land_data.append(plot_data)
                except Exception:
                    continue
        except Exception as e:
            self.logger.error(f"Unexpected error in data loading: {e}")
            return None
        else:
            return land_data

    def load_and_validate_unprocessed_data(
        self, user_id: str, upload_id: str, status: int = 1
    ) -> List[Optional[ProcessedLandData]]:
        """
        Load and validate the uploaded JSON file

        Args:
            uploaded_file: Uploaded file from Streamlit

        Returns:
            Validated data dictionary or None
        """
        try:
            data = self.storage.get_unprocessed_data(
                user_id=user_id, upload_id=upload_id, status=status
            )
            land_data: List[Optional[ProcessedLandData]] = []
            for plot in data:
                plot_data: Dict = plot["data"]
                plot_data["id"] = str(
                    plot["id"]
                )  # plot_data.get("id", str(plot["id"]))
                try:
                    plot_data = dict_to_proccessed_data_model(plot_data)
                    land_data.append(plot_data)
                except Exception:
                    self.logger.error(f"Unexpected error transforming data : {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Unexpected error in data loading: {e}")
            return None
        else:
            return land_data

    @staticmethod
    def extract_plot_metadata(plots: List[ProcessedLandData]) -> Dict:
        """
        Extract metadata from plots for filtering and display

        Args:
            plots: List of plot dictionaries

        Returns:
            Dictionary of extracted metadata
        """
        metadata = {
            "regions": set(),
            "districts": set(),
            "localities": set(),
            "plot_numbers": set(),
        }

        for plot in plots:
            plot_info = plot.plot_info

            # Safely extract and add metadata
            metadata["regions"].add(plot_info.region or "Unknown")
            metadata["districts"].add(plot_info.district or "Unknown")
            metadata["localities"].add(plot_info.locality or "Unknown")
            metadata["plot_numbers"].add(plot_info.plot_number or "Unknown")

        # Filter out None values and sort
        return {k: sorted(filter(None, v)) for k, v in metadata.items()}
