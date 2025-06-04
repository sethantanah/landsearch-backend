from typing import Annotated, List
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config.dependencies import get_settings, get_supabase_storage
from app.config.settings import Settings
from app.core.document_retrieval import delete_documents_superbase
from app.core.document_upload import prepare_doc, update_site_plan_coordinates
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
    """Upload documents for processing.\n
    Args:\n
        settings: Application settings\n
        storage: Storage service instance\n
        user_id: ID of the user uploading documents\n
        upload_id: ID for this upload session\n
        files: List of files to upload\n
        store: Whether to store the processed documents\n
    Returns:\n
        List of processed land data objects\n
    """
    res = await prepare_doc(settings, files, storage, user_id, upload_id, store=store)
    return res


@router.put("/update-coordinates/{id}", response_model=APIResponse)
async def document_update_coordinates(
    settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    data: ProcessedLandData,
    id: str = None,
    removeRef: bool = False,
):
    """Update coordinates for a site plan document.\n
    Args:\n
        settings: Application settings\n
        storage: Storage service instance\n
        data: Processed land data containing new coordinates\n
        id: Document ID to update\n
        removeRef: Whether to remove reference coordinates\n
    Returns:\n
        API response indicating success/failure\n
    """
    res = await update_site_plan_coordinates(
        settings=settings, data=data, removeRef=removeRef
    )
    response = APIResponse(data=res, message="Update sucessful", success=True)
    return response


@router.post("/store-unapproved-siteplan/{user_id}", response_model=APIResponse)
async def store_unapproved_document(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    data: ProcessedLandData,
    user_id: str = None,
):
    """Store an unapproved site plan document temporarily.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        data: Processed land data to store\n
        user_id: ID of the user storing the document\n
    Returns:\n
        API response indicating success/failure\n
    """
    if data:
        document = data.model_dump()
        storage.store_data(document, user_id=user_id)
        return APIResponse(data=data, message="Sucessfully Stored", success=True)
    return APIResponse(data=data, message="Invalid Data", success=False)


@router.put("/update-siteplan-unapproved/{id}", response_model=APIResponse)
async def update_unapproved_document(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    data: ProcessedLandData,
    id: str = None,
):
    """Update an unapproved site plan document.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        data: Updated processed land data\n
        id: Document ID to update\n
    Returns:\n
        API response indicating success/failure\n
    """
    if data:
        document = data.model_dump()
        storage.update_data(document, table="data_processing_temp")
        return APIResponse(data=data, message="Sucessfully Stored", success=True)
    return APIResponse(data=data, message="Invalid Data", success=False)


@router.put("/update-siteplan/{id}", response_model=APIResponse)
async def update_approved_document(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    data: ProcessedLandData,
    id: str = None,
):
    """Update an approved site plan document.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        data: Updated processed land data\n
        id: Document ID to update\n
    Returns:\n
        API response indicating success/failure\n
    """
    if data:
        document = data.model_dump()
        storage.update_data(document)
        return APIResponse(data=data, message="Sucessfully Stored", success=True)
    return APIResponse(data=data, message="Invalid Data", success=False)


@router.post("/store/all")
async def store_documents(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    documents: List[ProcessedLandData],
):
    """Store multiple documents at once.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        documents: List of processed land data objects to store\n
    Returns:\n
        The first document from the stored list\n
    """
    if documents:
        for document in documents:
            data = document.model_dump()
            storage.store_data(data)

    return documents[0]


@router.delete("/delete-unapproved-document/{doc_id}")
async def delete_unapproved_document(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)], doc_id: str
):
    """Delete an unapproved document.\n
    Args:\n
        storage: Storage service instance\n
        doc_id: ID of the document to delete\n
    Returns:\n
        API response indicating success/failure\n
    """
    delete_documents_superbase(storage, doc_id, table="data_processing_temp")
    return APIResponse(data={"doc": doc_id}, message="Delete Succesful", success=True)


@router.delete("/delete-document/{doc_id}")
async def delete_document(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)], doc_id: str
):
    """Delete an approved document.\n
    Args:\n
        storage: Storage service instance\n
        doc_id: ID of the document to delete\n
    Returns:\n
        API response indicating success/failure\n
    """
    delete_documents_superbase(storage, doc_id, table="LandSearch")
    return APIResponse(data={"doc": doc_id}, message="Delete Succesful", success=True)