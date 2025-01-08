from typing import Dict
import uuid
from app.schemas.schemas import (
    BoundaryPoint,
    ConvertedCoords,
    NextPoint,
    OriginalCoords,
    PlotInfo,
    PointList,
    ProcessedLandData,
    SurveyPoint,
)


def dict_to_proccessed_data_model(data: Dict) -> ProcessedLandData:
    plot_info = PlotInfo.model_validate(data["plot_info"])
    survey_points = []

    for coords in data["survey_points"]:
        original_coords = OriginalCoords.model_validate(coords["original_coords"])
        converted_coords = ConvertedCoords.model_validate(coords["converted_coords"])
        next_point = NextPoint.model_validate(coords["next_point"])
        survey_point = SurveyPoint(
            point_name=coords["point_name"],
            original_coords=original_coords,
            converted_coords=converted_coords,
            next_point=next_point,
        )

        survey_points.append(survey_point)

        boundary_points = []
        for boundary in data["boundary_points"]:
            boundary_point = BoundaryPoint.model_validate(boundary)
            boundary_points.append(boundary_point)

        point_lists = []
        for point in data["point_list"]:
            point_list = PointList.model_validate(point)
            point_lists.append(point_list)

        land_id = data.get("id", str(uuid.uuid4()))
        processed_data = ProcessedLandData(
            id=land_id,
            plot_info=plot_info,
            survey_points=survey_points,
            boundary_points=boundary_points,
            point_list=point_lists,
        )

    return processed_data
