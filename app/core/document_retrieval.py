from app.services.document_loaders import SuperBaseDataLoader
from app.services.document_storage import SuperBaseStorage


async def get_documents_superbase(storage: SuperBaseStorage, user_id: str = None):
    data_loader = SuperBaseDataLoader(storage=storage)

    return data_loader.load_all_and_validate(user_id=user_id)


async def get_unprocessed_documents_superbase(
    storage: SuperBaseStorage, user_id: str, upload_id: str, status: int = 1
):
    data_loader = SuperBaseDataLoader(storage=storage)

    return data_loader.load_and_validate_unprocessed_data(
        user_id=user_id, upload_id=upload_id, status=status
    )


def delete_documents_superbase(
    storage: SuperBaseStorage,
    doc_id: str,
    table: str
):
    data_loader = SuperBaseDataLoader(storage=storage)

    return data_loader.storage.delete_document(
        doc_id=doc_id, table=table
    )
