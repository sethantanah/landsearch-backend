from typing import Annotated, List
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config.dependencies import get_settings, get_supabase_storage
from app.config.settings import Settings
from app.core.document_upload import prepare_doc, update_document
from app.schemas.schemas import APIResponse, ProcessedLandData
from app.services.document_storage import SuperBaseStorage

router = APIRouter(prefix="/document-processing", tags=["document-processing"])


@router.post("/upload", response_model=List[ProcessedLandData])
async def document_uploads(
    settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    user_id: Annotated[str, Form()] = None,
    upload_id: Annotated[str, Form()] = None,
    files: List[UploadFile] = List[File(None)],
    store: Annotated[bool, Form()] = True,
):
    res = await prepare_doc(settings, files, storage, user_id, upload_id, store=store)
    return res


@router.put("/update/{id}", response_model=APIResponse)
async def document_update(
    settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    data: ProcessedLandData,
    id: str = None,
):

    res = await update_document(settings=settings, data=data)
    response = APIResponse(data=res, message="Update sucessful", success=True)
    return response


@router.post("/store/{user_id}", response_model=APIResponse)
async def store_document(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    data: ProcessedLandData,
    user_id: str = None,
):
    if data:
        document = data.model_dump()
        storage.store_data(document, user_id=user_id)
        return APIResponse(data=data, message="Sucessfully Stored", success=True)
    return APIResponse(data=data, message="Invalid Data", success=False)


@router.post("/store/all")
async def store_documents(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    documents: List[ProcessedLandData],
):

    if documents:
        for document in documents:
            data = document.model_dump()
            storage.store_data(data)

    return documents[0]
