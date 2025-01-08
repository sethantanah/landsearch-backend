from functools import lru_cache
from typing import Annotated

import cyberdb

from fastapi import Depends
from app.config.settings import Settings
from app.services.document_storage import SuperBaseStorage
from app.services.storage_cache import document_data_cache, unedited_document_data_cache


@lru_cache(maxsize=None, typed=False)
def get_settings() -> Settings:
    return Settings()


# @lru_cache(maxsize=None, typed=False)
def get_supabase_storage(
    settings: Annotated[Settings, Depends(get_settings)]
) -> SuperBaseStorage:
    return SuperBaseStorage(settings=settings)


def get_document_cache():
    return document_data_cache


def get_unedited_document_cache():
    return unedited_document_data_cache


def get_cyberdb():
    client = cyberdb.connect(host="127.0.0.1", port=9980, password="123456")
    return client
