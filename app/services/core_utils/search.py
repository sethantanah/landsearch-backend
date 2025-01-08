from enum import Enum
from typing import Dict, List, Optional
from math import radians, sin, cos, sqrt, atan2

from shapely.geometry import Polygon

from app.schemas.schemas import ProcessedLandData
from app.schemas.utility_schemas import SearchFilters
from app.utils.logging import setup_logging

logger = setup_logging(app_name=__name__)


class MatchTypes(Enum):
    EXACT = "exact"
    RADIUS = "radius"


def radius_search(
    land_data: List[ProcessedLandData], filters: SearchFilters
) -> List[Optional[ProcessedLandData]]:
    filtered_data: List[Optional[ProcessedLandData]] = []
    # Coordinate search
    if filters.coordinates:
        if filters.match == MatchTypes.RADIUS:
            # Filter by radius
            filtered_data = [
                plot
                for plot in land_data
                if any(
                    any(
                        haversine_distance(lat, lon, point.longitude, point.latitude)
                        <= filters.search_radius
                        for lat, lon in plot.point_list
                    )
                    for point in plot.point_list
                )
            ]
        else:
            filtered_data = [
                plot
                for plot in land_data
                if any(
                    any(
                        approx_match(lat, lon, point.latitude, point.longitude)
                        for lat, lon in filters.coordinates
                    )
                    for point in plot.point_list
                )
            ]

    return filtered_data


def overlap_search(
    land_data: List[ProcessedLandData], filters: SearchFilters
) -> tuple[List[Optional[ProcessedLandData]], List[Optional[Dict]]]:
    filtered_data: List[Optional[ProcessedLandData]] = []
    """Find all plots that overlap with any other plot"""
    from shapely.geometry import Polygon

    overlaps = []
    filtered_data: List[Optional[ProcessedLandData]] = []

    _coords = [
        (coord.longitude, coord.latitude) for coord in filters.coordinates if coord
    ]

    try:
        # Skip if less than 3 points (not a valid polygon)
        if len(_coords) >= 3:
            try:
                poly1 = Polygon(_coords)
                if poly1.is_valid:
                    for plot in land_data:
                        if len(plot.point_list) < 3:
                            continue
                        coords_ = [
                            (point.longitude, point.latitude)
                            for point in plot.point_list
                        ]
                        poly2 = Polygon(coords_)
                        if not poly2.is_valid:
                            continue
                        if poly1.intersects(poly2):
                            filtered_data.append(plot)
                            overlap = compute_overlap(_coords, coords_)
                            overlaps.append(overlap)

            except Exception as e:
                logger.error(f"Error processing plot coordinates: {str(e)}")

    except Exception as e:
        logger.error(f"Error in overlap detection: {str(e)}")
    else:
        return filtered_data, overlaps


# Utility Functions
def haversine_distance(lat1=0, lon1=0, lat2=0, lon2=0):
    """
    Calculate the Haversine distance between two points on the Earth's surface.

    Args:
        lat1 (float): Latitude of the first point (default 0 if not provided).
        lon1 (float): Longitude of the first point (default 0 if not provided).
        lat2 (float): Latitude of the second point (default 0 if not provided).
        lon2 (float): Longitude of the second point (default 0 if not provided).

    Returns:
        float: Distance in kilometers between the two points.
    """
    R = 6371  # Earth radius in kilometers

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance


# Match by approximate latitude and longitude
def approx_match(lat1, lon1, lat2, lon2, tolerance=0.01):
    """
    Check if two coordinates match approximately within a tolerance.

    Args:
        lat1 (float): Latitude of the first point.
        lon1 (float): Longitude of the first point.
        lat2 (float): Latitude of the second point.
        lon2 (float): Longitude of the second point.
        tolerance (float): Acceptable difference for latitude and longitude.

    Returns:
        bool: True if coordinates match approximately, False otherwise.
    """
    return (lat1 is None or lat2 is None or abs(lat1 - lat2) <= tolerance) and (
        lon1 is None or lon2 is None or abs(lon1 - lon2) <= tolerance
    )


def compute_overlap(coords1, coords2):
    """
    Calculate the percentage overlap between two polygons.

    Args:
        poly1_points: List of points for first polygon
        poly2_points: List of points for second polygon

    Returns:
        dict: Overlap percentage and areas
    """
    try:
        # Validate minimum points
        if len(coords1) < 3 or len(coords2) < 3:
            return {
                "overlap_percentage": 0,
                "overlap_area": 0,
                "poly1_area": 0,
                "poly2_area": 0,
                "error": "Insufficient points",
            }

        # Create Shapely polygons
        poly1 = Polygon(coords1)
        poly2 = Polygon(coords2)

        # Validate polygons
        if not poly1.is_valid or not poly2.is_valid:
            return {
                "overlap_percentage": 0,
                "overlap_area": 0,
                "poly1_area": 0,
                "poly2_area": 0,
                "error": "Invalid polygon",
            }

        # Calculate areas
        area1 = poly1.area
        area2 = poly2.area

        # Calculate intersection if polygons overlap
        if poly1.intersects(poly2):
            intersection = poly1.intersection(poly2)
            overlap_area = intersection.area
            # Calculate percentage relative to smaller polygon
            overlap_percentage = (overlap_area / min(area1, area2)) * 100
        else:
            overlap_area = 0
            overlap_percentage = 0

        return {
            "overlap_percentage": round(overlap_percentage, 2),
            "overlap_area": round(overlap_area, 6),
            "poly1_area": round(area1, 6),
            "poly2_area": round(area2, 6),
            "error": None,
        }

    except Exception as e:
        return {
            "overlap_percentage": 0,
            "overlap_area": 0,
            "poly1_area": 0,
            "poly2_area": 0,
            "error": str(e),
        }
