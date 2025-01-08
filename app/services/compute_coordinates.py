from typing import List, Tuple
from pyproj import Proj, transform
from app.config.settings import Settings
from app.utils.logging import setup_logging
from app.utils.convert_string_to_float import to_float


class ComputeCoordinates:

    def __init__(self, settings: Settings):
        """
        Initialize the processor with coordinate transformation settings.
        Sets up the coordinate transformer from Ghana National Grid (EPSG:25000) to WGS84 (EPSG:4326).
        """
        # Initialize coordinate transformer for Ghana National Grid to WGS84
        self.settings = settings
        self.logging = setup_logging(app_name=__name__)

    def convert_dms_to_decimal(self, dms_str: str) -> float:
        """
        Convert bearing from Degrees-Minutes-Seconds (DMS) format to decimal degrees.

        Args:
            dms_str (str): Bearing in DMS format (e.g., "13°10'")

        Returns:
            float: Bearing in decimal degrees

        Examples:
            >>> convert_dms_to_decimal("13°10'")
            13.166666666666666
        """
        if not dms_str:
            return 0.0

        # Split the DMS string into components
        parts = dms_str.replace("°", " ").replace("'", " ").strip().split()
        degrees = to_float(parts[0])
        minutes = to_float(parts[1]) if len(parts) > 1 else 0
        return degrees + (minutes / 60)

    def convert_to_latlon(self, easting: float, northing: float) -> Tuple[float, float]:
        """
        Convert coordinates from Ghana National Grid to WGS84 latitude/longitude.

        Args:
            easting (float): Easting coordinate in Ghana National Grid
            northing (float): Northing coordinate in Ghana National Grid

        Returns:
            Tuple[float, float]: (latitude, longitude) in decimal degrees
        """
        # Transform coordinates using the initialized transformer
        # lon, lat = self.transformer.transform(easting, northing)
        ghana_proj = Proj(init=self.settings.LOCALEPSG)
        wgs84_proj = Proj(init=self.settings.GLOBALEPSG)

        lon, lat = transform(ghana_proj, wgs84_proj, northing, easting)
        return (lat, lon)

    def order_points_by_bearing(self, point_list):
        """
        Order points based on clockwise bearing from the first point.
        """
        return self.corr_arrange_points(point_list)

    def corr_arrange_points(self, points):
        """
        Rearrange points to form a non-intersecting polygon using Graham Scan algorithm.

        Args:
            points (list): List of dictionaries containing latitude and longitude coordinates

        Returns:
            list: Rearranged points forming a non-intersecting polygon
        """

        def find_bottom_point(points):
            # Find the point with the lowest y-coordinate (latitude)
            return min(points, key=lambda p: (p["latitude"], p["longitude"]))

        def calculate_angle(p1, p2):
            # Calculate the angle between two points relative to the horizontal
            import math

            dx = p2["longitude"] - p1["longitude"]
            dy = p2["latitude"] - p1["latitude"]
            return math.atan2(dy, dx)

        def orientation(p1, p2, p3):
            # Calculate the orientation of three points
            # Returns: 0 --> collinear, 1 --> clockwise, 2 --> counterclockwise
            val = (p2["latitude"] - p1["latitude"]) * (
                p3["longitude"] - p2["longitude"]
            ) - (p2["longitude"] - p1["longitude"]) * (p3["latitude"] - p2["latitude"])
            if val == 0:
                return 0
            return 1 if val > 0 else 2

        if len(points) < 3:
            return points

        # Find the bottommost point
        bottom_point = find_bottom_point(points)

        # Sort points based on polar angle with respect to the bottom point
        sorted_points = sorted(
            [p for p in points if p != bottom_point],
            key=lambda p: (
                calculate_angle(bottom_point, p),
                (p["longitude"] - bottom_point["longitude"]) ** 2
                + (p["latitude"] - bottom_point["latitude"]) ** 2,
            ),
        )

        # Initialize the stack with the first three points
        stack = [bottom_point, sorted_points[0]]

        # Process remaining points
        for i in range(1, len(sorted_points)):
            while (
                len(stack) > 1
                and orientation(stack[-2], stack[-1], sorted_points[i]) != 2
            ):
                stack.pop()
            stack.append(sorted_points[i])

        return stack

    def find_reference_point(self, points: List[dict]) -> int:
        """Identify the reference point in a set of coordinates."""
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
            return max_index
        except Exception:
            raise

    def process_data(self, data: dict) -> dict:
        survey_points = data["survey_points"]
        for index, point in enumerate(survey_points):
            original_coords = point["original_coords"]

            lat, lon = self.convert_to_latlon(
                original_coords["x"], original_coords["y"]
            )
            converted_coords = {
                "latitude": lat,
                "longitude": lon,
                "ref_point": False,
            }

            data["survey_points"][index]["converted_coords"] = converted_coords

        point_list = []
        for coord in data["survey_points"]:
            if not coord["converted_coords"]["ref_point"]:
                point_list.append(coord["converted_coords"])

        ref_index = self.find_reference_point(point_list)
        point_list.pop(ref_index)
        data["point_list"] = self.order_points_by_bearing(point_list)

        for index, boundary in enumerate(data["boundary_points"]):
            lat, lon = self.convert_to_latlon(boundary["northing"], boundary["easting"])
            data["boundary_points"][index]["latitude"] = lat
            data["boundary_points"][index]["longitude"] = lon

        return data
