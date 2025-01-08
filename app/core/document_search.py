from typing import List
from app.schemas.schemas import ProcessedLandData
from app.schemas.utility_schemas import SearchFilters
from app.services.core_utils.search import overlap_search


async def coordinates_search(
    land_data: List[ProcessedLandData], filters: SearchFilters
):
    results = overlap_search(land_data, filters)
    return results
