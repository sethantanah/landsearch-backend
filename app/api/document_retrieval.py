from typing import Annotated
from fastapi import APIRouter, Depends

from app.config.dependencies import (
    get_document_cache,
    get_settings,
    get_supabase_storage,
)
from app.config.settings import Settings
from app.core.document_retrieval import (
    delete_documents_superbase,
    get_documents_superbase,
    get_unprocessed_documents_superbase,
)
from app.core.document_search import coordinates_search
from app.schemas.utility_schemas import SearchFilters
from app.services.document_storage import SuperBaseStorage

router = APIRouter(prefix="/site-plans", tags=["site-plans"])


@router.get("/all/")
async def get_documents(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    document_cache=Depends(get_document_cache),
    user: str = None,
):
    """Retrieve all site plan documents.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        document_cache: Cache for storing documents\n
        user: Optional user ID to filter documents\n
    Returns:\n
        Dictionary containing documents, success status, and message\n
    """
    documents = await get_documents_superbase(storage=storage, user_id=user)
    # document_cache.extend(documents)
    return {"data": {"items": documents}, "success": True, "message": "Data loaded"}


@router.get("/unapproved")
async def get_unprocessed_documents(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    userId: str = None,
    upload_id: str = None,
):
    """Retrieve unapproved/unprocessed site plan documents.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        userId: Optional user ID to filter documents\n
        upload_id: Optional upload ID to filter documents\n
    Returns:\n
        Dictionary containing unprocessed documents, success status, and message\n
    """
    documents = await get_unprocessed_documents_superbase(
        storage=storage, user_id=userId, upload_id=upload_id
    )
    return {"data": {"items": documents}, "success": True, "message": "Data loaded"}


@router.get("/failed-uploads")
async def get_failed_documents(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    user_id: str = None,
):
    """Retrieve documents that failed to upload.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        user_id: Optional user ID to filter documents\n
    Returns:\n
        Dictionary containing failed documents, success status, and message\n
    """
    documents = await get_unprocessed_documents_superbase(
        storage=storage, user_id=user_id, upload_id=None, status=0
    )
    return {"data": {"items": documents}, "success": True, "message": "Data loaded"}


@router.post("/document-search")
async def coords_search(
    storage: Annotated[SuperBaseStorage, Depends(get_supabase_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    search_params: SearchFilters,
    document_cache=Depends(get_document_cache),
):
    """Search documents based on coordinates and filters.\n
    Args:\n
        storage: Storage service instance\n
        settings: Application settings\n
        search_params: Search filters and parameters\n
        document_cache: Cache for storing documents\n
    Returns:\n
        Dictionary containing search results, success status, and message\n
    """
    land_data = list(document_cache)
    if len(land_data) < 1:
        land_data = await get_documents_superbase(storage=storage)
        document_cache.extend(land_data)

    search_data = []
    for item in land_data:
        if item.plot_info.plot_number == search_params.country:
            item.plot_info.is_search_plan = True
        search_data.append(item)
    results = await coordinates_search(search_data, search_params)
    return {"data": {"items": results[0]}, "success": True, "message": "Search Results"}
