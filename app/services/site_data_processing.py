from dataclasses import dataclass
import math
import re
from typing import List, Tuple, Optional
from pyproj import Proj, Transformer, transform
from app.utils.convert_string_to_float import to_float
from app.utils.logging import setup_logging


logger = setup_logging(app_name=f"{__name__}_LandDataProcessor")


@dataclass
class Point:
    """
    Data class representing a survey point with its coordinates and relationships.
    """

    name: str
    x_coord: float
    y_coord: float
    bearing_to_next: Optional[str] = None
    distance_to_next: Optional[float] = None
    reference_point: Optional[bool] = False
    next_point: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LandDataProcessor:
    """
    Processes land survey data and converts coordinates between Ghana National Grid and WGS84.
    """

    def __init__(self):
        """Initialize the processor with coordinate transformation settings."""
        logger.info("Initializing LandDataProcessor")
        try:
            self.transformer = Transformer.from_crs(
                "epsg:2136", "epsg:4326", always_xy=True
            )
            logger.debug("Transformer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize transformer: {str(e)}")
            raise

    def convert_dms_to_decimal(self, dms_str: str) -> float:
        """Convert bearing from DMS format to decimal degrees."""
        logger.debug(f"Converting DMS string: {dms_str}")
        try:
            if not dms_str:
                return 0.0

            parts = dms_str.replace("°", " ").replace("'", " ").strip().split()
            degrees = to_float(parts[0])
            minutes = to_float(parts[1]) if len(parts) > 1 else 0
            result = degrees + (minutes / 60)
            logger.debug(f"Converted {dms_str} to {result} decimal degrees")
            return result
        except Exception as e:
            logger.error(f"Error converting DMS string '{dms_str}': {str(e)}")
            raise

    def ghana_grid_to_latlon(
        self, easting: float, northing: float
    ) -> Tuple[float, float]:
        """Convert coordinates from Ghana National Grid to WGS84."""
        logger.debug(
            f"Converting coordinates - Easting: {easting}, Northing: {northing}"
        )
        try:
            ghana_proj = Proj(init="EPSG:2136")
            wgs84_proj = Proj(init="EPSG:4326")
            lon, lat = transform(ghana_proj, wgs84_proj, northing, easting)
            logger.debug(f"Converted to Lat: {lat}, Lon: {lon}")
            return (lat, lon)
        except Exception as e:
            logger.error(f"Coordinate conversion failed: {str(e)}")
            raise

    def identify_reference_point_pattern(self, text: str) -> bool:
        """Identify if a given text matches reference point patterns."""
        logger.debug(f"Checking reference point pattern for: {text}")
        pattern = r"^[A-Z]+(?:\.[A-Z]+)?\s[A-Z0-9]+\s(?:\d+\s?)+$"
        result = bool(re.match(pattern, text))
        logger.debug(f"Pattern match result for '{text}': {result}")
        return result

    def find_reference_point(self, points: List[dict]) -> int:
        """Identify the reference point in a set of coordinates."""
        logger.info(f"Finding reference point among {len(points)} points")
        try:

            def calculate_distance(p1, p2):
                return (
                    (p1["latitude"] - p2["latitude"]) ** 2
                    + (p1["longitude"] - p2["longitude"]) ** 2
                ) ** 0.5

            def find_outlier_score(points):
                scores = []
                for i, point in enumerate(points):
                    total_distance = 0
                    for j, other_point in enumerate(points):
                        if i != j:
                            total_distance += calculate_distance(point, other_point)
                    avg_distance = total_distance / (len(points) - 1)
                    scores.append((avg_distance, i))
                return scores

            outlier_scores = find_outlier_score(points)
            max_score, max_index = max(outlier_scores)
            logger.info(
                f"Reference point found at index {max_index} with score {max_score}"
            )
            return max_index
        except Exception as e:
            logger.error(f"Error finding reference point: {str(e)}")
            raise

    def corr_arrange_points(self, points: List[dict]) -> List[dict]:
        """Rearrange points using Graham Scan algorithm."""
        logger.info(f"Arranging {len(points)} points")
        try:

            def find_bottom_point(points):
                return min(points, key=lambda p: (p["latitude"], p["longitude"]))

            def calculate_angle(p1, p2):
                dx = p2["longitude"] - p1["longitude"]
                dy = p2["latitude"] - p1["latitude"]
                return math.atan2(dy, dx)

            def orientation(p1, p2, p3):
                val = (p2["latitude"] - p1["latitude"]) * (
                    p3["longitude"] - p2["longitude"]
                ) - (p2["longitude"] - p1["longitude"]) * (
                    p3["latitude"] - p2["latitude"]
                )
                if val == 0:
                    return 0
                return 1 if val > 0 else 2

            if len(points) < 3:
                logger.warning("Less than 3 points provided, returning original points")
                return points

            bottom_point = find_bottom_point(points)
            sorted_points = sorted(
                [p for p in points if p != bottom_point],
                key=lambda p: (
                    calculate_angle(bottom_point, p),
                    (p["longitude"] - bottom_point["longitude"]) ** 2
                    + (p["latitude"] - bottom_point["latitude"]) ** 2,
                ),
            )

            stack = [bottom_point, sorted_points[0]]
            for i in range(1, len(sorted_points)):
                while (
                    len(stack) > 1
                    and orientation(stack[-2], stack[-1], sorted_points[i]) != 2
                ):
                    stack.pop()
                stack.append(sorted_points[i])

            logger.debug(f"Points arranged successfully, returning {len(stack)} points")
            return stack
        except Exception as e:
            logger.error(f"Error arranging points: {str(e)}")
            raise

    def process_land_data(self, data: dict) -> dict:
        """Process land survey data and convert coordinates."""
        logger.info("Starting land data processing")
        try:
            # Extract coordinate data
            plan_data = data["site_plan_data"]["plan_data"]
            points: List[Point] = []
            logger.debug(f"Processing {len(plan_data)} plan data points")

            # Process survey points
            for i in range(len(plan_data)):
                try:
                    if plan_data["x_coords"][i] and plan_data["y_coords"][i]:
                        name = (
                            plan_data["from"][i] if i < len(plan_data["from"]) else None
                        )
                        x_coord = (
                            to_float(plan_data["x_coords"][i])
                            if i < len(plan_data["x_coords"])
                            else None
                        )
                        y_coord = (
                            to_float(plan_data["y_coords"][i])
                            if i < len(plan_data["y_coords"])
                            else None
                        )
                        bearing_to_next = (
                            plan_data["bearing"][i]
                            if i < len(plan_data["bearing"])
                            else None
                        )
                        distance_to_next = (
                            to_float(plan_data["distance"][i])
                            if i < len(plan_data["distance"])
                            else None
                        )
                        next_point = (
                            plan_data["to"][i] if i < len(plan_data["to"]) else None
                        )

                        point = Point(
                            name=name,
                            x_coord=x_coord,
                            y_coord=y_coord,
                            bearing_to_next=bearing_to_next,
                            distance_to_next=distance_to_next,
                            next_point=next_point,
                            reference_point=self.identify_reference_point_pattern(name),
                        )

                        lat, lon = self.ghana_grid_to_latlon(
                            point.x_coord, point.y_coord
                        )
                        point.latitude = lat
                        point.longitude = lon
                        points.append(point)
                        logger.debug(f"Processed point {name} successfully")
                except Exception as e:
                    logger.error(f"Error processing point at index {i}: {str(e)}")
                    continue

            # Process boundary coordinates
            logger.info("Processing boundary coordinates")
            boundary_coords = []
            north_easterns = data["site_plan_data"]["north_easterns"]

            for i in range(len(north_easterns["norths"])):
                try:
                    north = (
                        to_float(north_easterns["norths"][i])
                        if i < len(north_easterns["norths"])
                        else 0
                    )
                    east = (
                        to_float(north_easterns["easterns"][i])
                        if i < len(north_easterns["easterns"])
                        else 0
                    )
                    lat, lon = self.ghana_grid_to_latlon(north, east)
                    boundary_coords.append(
                        {
                            "point": f"Boundary_{i+1}",
                            "northing": north,
                            "easting": east,
                            "latitude": round(lat, 8),
                            "longitude": round(lon, 8),
                        }
                    )
                    logger.debug(f"Processed boundary point {i+1}")
                except Exception as e:
                    logger.error(
                        f"Error processing boundary point at index {i}: {str(e)}"
                    )
                    continue

            # Construct result dictionary
            result = {
                "plot_info": {
                    "plot_number": data.get("plot_number", ""),
                    "area": to_float(data["area"]),
                    "metric": data.get("metric", ""),
                    "locality": data.get("locality", ""),
                    "district": data.get("district", ""),
                    "region": data.get("region", ""),
                    "owners": data.get("owners", []),
                    "date": data.get("date", ""),
                    "scale": data.get("scale", ""),
                    "other_location_details": data.get("other_location_details", ""),
                    "surveyors_name": data.get("surveyors_name", ""),
                    "surveyors_location": data.get("surveyors_location", ""),
                    "surveyors_reg_number": data.get("surveyors_reg_number", ""),
                    "regional_number": data.get("regional_number", ""),
                    "reference_number": data.get("reference_number", ""),
                },
                "survey_points": [
                    {
                        "point_name": p.name,
                        "original_coords": {
                            "x": p.x_coord,
                            "y": p.y_coord,
                            "ref_point": p.reference_point,
                        },
                        "converted_coords": {
                            "latitude": p.latitude,
                            "longitude": p.longitude,
                            "ref_point": p.reference_point,
                        },
                        "next_point": {
                            "name": p.next_point,
                            "bearing": p.bearing_to_next,
                            "bearing_decimal": (
                                self.convert_dms_to_decimal(p.bearing_to_next)
                                if p.bearing_to_next
                                else None
                            ),
                            "distance": p.distance_to_next,
                        },
                    }
                    for p in points
                ],
                "boundary_points": boundary_coords,
            }

            # Process point list
            point_list = [p["converted_coords"] for p in result["survey_points"]]
            ref_index = self.find_reference_point(point_list)
            point_list.pop(ref_index)
            result["point_list"] = self.corr_arrange_points(point_list)

            logger.info("Land data processing completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error in process_land_data: {str(e)}")
            raise
