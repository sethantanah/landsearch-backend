import tempfile
from typing import List
from fastapi import UploadFile

from app.config.settings import Settings
from app.schemas.schemas import ProcessedLandData
from app.schemas.test_data import EMPTY_DATA
from app.services.compute_coordinates import ComputeCoordinates
from app.services.document_processing import DocumentProcessor
from app.services.document_storage import SuperBaseStorage
from app.utils.data_serializer import dict_to_proccessed_data_model


async def prepare_doc(
    settings: Settings,
    files: List[UploadFile],
    storage: SuperBaseStorage,
    user_id: str = None,
    upload_id: str = None,
    store: bool = True,
):
    doc_processor = DocumentProcessor(settings=settings)
    results = []

    for file in files:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
        with open(temp_file.name, "wb") as f:
            f.write(await file.read())

        data = doc_processor.process_document(
            temp_file.name, file.filename, model_type="GEMINI"
        )

        if data.success:
            land_data = dict_to_proccessed_data_model(data.data["results"])
            data = land_data.model_dump()
            if store:
                storage.store_data_temp(
                    data,
                    user_id=user_id,
                    upload_id=upload_id,
                    file_name=file.filename,
                    status=1,
                )
            results.append(land_data)
        else:
            data = EMPTY_DATA
            data["plot_info"]["plot_number"] = file.filename
            if store:
                storage.store_data_temp(
                    data,
                    user_id=user_id,
                    upload_id=upload_id,
                    file_name=file.filename,
                    status=0,
                )
            results.append(dict_to_proccessed_data_model(data))
    return results


async def update_document(settings: Settings, data: ProcessedLandData):
    # Recompute Corordinates
    doc_processor = ComputeCoordinates(settings=settings)
    results = doc_processor.process_data(data.model_dump())
    return ProcessedLandData.model_validate(results)
