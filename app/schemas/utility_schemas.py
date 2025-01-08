from typing import List, Optional
from openai import BaseModel

from app.schemas.schemas import ConvertedCoords


class SearchFilters(BaseModel):
    country: Optional[str] = None
    locality: Optional[str] = None
    district: Optional[str] = None
    search_radius: Optional[int] = None
    match: Optional[str] = None
    coordinates: List[Optional[ConvertedCoords]]
