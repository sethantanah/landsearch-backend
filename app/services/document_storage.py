from typing import Dict
from functools import lru_cache
from supabase import create_client, Client

from app.config.settings import Settings
from app.utils.logging import setup_logging


class SuperBaseStorage:

    def __init__(self, settings: Settings, table_name: str = None):
        self.url: str = settings.SUPABASE_URL
        self.key: str = settings.SUPABASE_KEY
        self.table_name = settings.SUPABASE_TABLE

        self.supabase: Client = None
        self.logger = setup_logging(app_name=__name__)

        # Connect to client
        self.__connect_client()

    @lru_cache(maxsize=None)
    def __connect_client(self):
        if not self.url or not self.key:
            self.logger.warning("Supabase URL or API Key not set.")
            raise Exception("Supabase URL or API Key not set.")
        else:
            self.supabase = create_client(self.url, self.key)
            
    def get_data(self, user_id: str = None, table: str = None) -> Dict:
        table_name = table or self.table_name
        response = (
            self.supabase.table(table_name)
            .select("*")
            .filter("user_id", "eq", user_id)
            .execute()
        )
        return response.data

    def get_data_all(self, table: str = None) -> Dict:
        table_name = table or self.table_name
        response = (
            self.supabase.table(table_name)
            .select("*")
            .execute()
        )
        return response.data

    def store_data(self, data: Dict, user_id: str = None, table: str = None) -> Dict:
        table_name = table or self.table_name
        try:
            try:
                id = data.get("id", "")
                try:
                    id = int(id)
                except Exception:
                    pass
                self.supabase.from_("data_processing_temp").delete().eq("id", id).execute()
            except Exception as e:
                self.logger.warning(f"Could not delete data {str(e)}")
            payload: Dict = {"data": data, "user_id": user_id}
            response = self.supabase.table(table_name).insert(payload).execute()
        except Exception as e:
            self.logger.warning(f"Could not save site data {str(e)}")
            return None
        else:
            return response

    def delete_document(self, table: str = None, doc_id: str = None):
        table_name = table or self.table_name
        return self.supabase.table(table_name).delete().eq("id", 4).execute()

    def get_unprocessed_data(
        self,
        user_id: str = None,
        upload_id: str = None,
        status: int = 1,
        table: str = "data_processing_temp",
    ) -> Dict:
        table_name = table or self.table_name
        response = (
            self.supabase.table(table_name)
            .select("*")
            .filter("user_id", "eq", user_id)
            # .filter("status", "eq", status)
            .execute()
        )
        return response.data

    def store_data_temp(
        self,
        data: Dict,
        user_id: str = None,
        upload_id: str = None,
        file_name: str = None,
        status: int = 0,
        table: str = "data_processing_temp",
    ) -> Dict:
        table_name = table or self.table_name
        try:
            payload: Dict = {
                "user_id": user_id,
                "file_name": file_name,
                "status": status,
                "upload_id": upload_id,
                "data": data,
            }
            response = self.supabase.table(table_name).insert(payload).execute()
        except Exception as e:
            self.logger.warning(f"Could not save site data {str(e)}")
            return None
        else:
            return response
