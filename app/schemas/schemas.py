from typing import List, Optional
from pydantic import BaseModel, Field


class RawPlanData(BaseModel):
    from_: Optional[List[str]] = Field(default_factory=list, alias="from")
    x_coords: Optional[List[float]] = Field(default_factory=list)
    ref: Optional[List[bool]] = Field(default_factory=list)
    y_coords: Optional[List[float]] = Field(default_factory=list)
    bearing: Optional[List[str]] = Field(default_factory=list)
    distance: Optional[List[float]] = Field(default_factory=list)
    to: Optional[List[str]] = Field(default_factory=list)


class RawNorthEasterns(BaseModel):
    norths: Optional[List[float]] = Field(default_factory=list)
    easterns: Optional[List[float]] = Field(default_factory=list)


class RawSitePlanData(BaseModel):
    plan_data: Optional[RawPlanData] = None
    north_easterns: Optional[RawNorthEasterns] = None


class RawLandData(BaseModel):
    owners: Optional[List[str]] = Field(default_factory=list)
    plot_number: Optional[str] = None
    date: Optional[str] = None
    area: Optional[str] = None
    metric: Optional[str] = None
    scale: Optional[str] = None
    locality: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    other_location_details: Optional[str] = None
    surveyors_name: Optional[str] = None
    surveyors_location: Optional[str] = None
    surveyors_reg_number: Optional[str] = None
    regional_number: Optional[str] = None
    reference_number: Optional[str] = None
    site_plan_data: Optional[RawSitePlanData] = None

    class Config:
        populate_by_name = True
        json_encoders = {float: lambda v: round(v, 6) if v is not None else None}


# Processed LandData
class OriginalCoords(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    ref_point: Optional[bool] = False


class ConvertedCoords(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ref_point: Optional[bool] = False


class NextPoint(BaseModel):
    name: Optional[str] = None
    bearing: Optional[str] = None
    bearing_decimal: Optional[float] = None
    distance: Optional[float] = None


class SurveyPoint(BaseModel):
    point_name: Optional[str] = None
    original_coords: Optional[OriginalCoords] = None
    converted_coords: Optional[ConvertedCoords] = None
    next_point: Optional[NextPoint] = None


class BoundaryPoint(BaseModel):
    point: Optional[str] = None
    northing: Optional[float] = None
    easting: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PointList(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ref_point: Optional[bool] = None


class PlotInfo(BaseModel):
    plot_number: Optional[str] = ""
    area: Optional[float] = None
    metric: Optional[str] = None
    locality: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    owners: Optional[List[str]] = Field(default_factory=list)
    date: Optional[str] = None
    scale: Optional[str] = None
    other_location_details: Optional[str] = None
    surveyors_name: Optional[str] = None
    surveyors_location: Optional[str] = None
    surveyors_reg_number: Optional[str] = None
    regional_number: Optional[str] = None
    reference_number: Optional[str] = None


class ProcessedLandData(BaseModel):
    id: Optional[str] = None
    plot_info: Optional[PlotInfo] = None
    survey_points: Optional[List[SurveyPoint]] = None
    boundary_points: Optional[List[BoundaryPoint]] = None
    point_list: Optional[List[PointList]] = None

    class Config:
        populate_by_name = True
        json_encoders = {float: lambda v: round(v, 6) if v is not None else None}


class APIResponse(BaseModel):
    data: Optional[ProcessedLandData] = None
    message: Optional[str] = None
    success: Optional[bool] = True
