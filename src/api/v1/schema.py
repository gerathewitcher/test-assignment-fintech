from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.dto import (
    Building,
    BuildingFilter,
    Organization,
    OrganizationActivityFilter,
    OrganizationFilter,
    PaginatedBuildings,
    PaginatedOrganizations,
    PaginationParams,
    WithinBoundingBoxFilter,
    WithinRadiusFilter,
)


class OrganizationPhoneNumberSchema(BaseModel):
    number: str


class BuildingSchema(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the building")
    address: str = Field(description="Address of the building")
    coordinate_lat: float = Field(description="Latitude coordinate of the building")
    coordinate_long: float = Field(description="Longitude coordinate of the building")

    @classmethod
    def from_dto(cls, dto: Building) -> "BuildingSchema":
        return cls(
            uuid=dto.uuid,
            address=dto.address,
            coordinate_lat=dto.coordinate_lat,
            coordinate_long=dto.coordinate_long,
        )


class ActivitySchema(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the activity")
    name: str = Field(description="Name of the activity")


class OrganizationFullSchema(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the organization")
    name: str = Field(description="Name of the organization")
    building: BuildingSchema | None = Field(
        description="Building associated with the organization"
    )

    phone_numbers: list[OrganizationPhoneNumberSchema] = Field(
        description="Phone numbers associated with the organization"
    )

    activities: list[ActivitySchema] = Field(
        description="Activities associated with the organization"
    )

    @classmethod
    def from_dto(cls, dto: Organization) -> "OrganizationFullSchema":
        return cls(
            uuid=dto.uuid,
            name=dto.name,
            building=BuildingSchema(
                uuid=dto.building.uuid,
                address=dto.building.address,
                coordinate_lat=dto.building.coordinate_lat,
                coordinate_long=dto.building.coordinate_long,
            )
            if dto.building
            else None,
            phone_numbers=[
                OrganizationPhoneNumberSchema(
                    number=phone_number.number,
                )
                for phone_number in dto.phone_numbers
            ],
            activities=[
                ActivitySchema(uuid=activity.uuid, name=activity.name)
                for activity in dto.activities
            ],
        )


class OrganizationSchema(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the organization")
    name: str = Field(description="Name of the organization")
    building: BuildingSchema | None = Field(
        description="Building associated with the organization"
    )

    @classmethod
    def from_dto(cls, dto: Organization) -> "OrganizationSchema":
        return cls(
            uuid=dto.uuid,
            name=dto.name,
            building=BuildingSchema(
                uuid=dto.building.uuid,
                address=dto.building.address,
                coordinate_lat=dto.building.coordinate_lat,
                coordinate_long=dto.building.coordinate_long,
            )
            if dto.building
            else None,
        )


class OrganizationPageSchema(BaseModel):
    items: list[OrganizationSchema] = Field(description="Organizations page")
    next_cursor: str | None = Field(
        default=None, description="Cursor for next organizations page"
    )

    @classmethod
    def from_dto(cls, dto: PaginatedOrganizations) -> "OrganizationPageSchema":
        return cls(
            items=[OrganizationSchema.from_dto(org) for org in dto.items],
            next_cursor=dto.next_cursor,
        )


class BuildingPageSchema(BaseModel):
    items: list[BuildingSchema] = Field(description="Buildings page")
    next_cursor: str | None = Field(
        default=None, description="Cursor for next buildings page"
    )

    @classmethod
    def from_dto(cls, dto: PaginatedBuildings) -> "BuildingPageSchema":
        return cls(
            items=[BuildingSchema.from_dto(building) for building in dto.items],
            next_cursor=dto.next_cursor,
        )


class OrganizationQueryParams(BaseModel):
    building_uuid: UUID | None = Field(
        default=None,
        description="Filter organizations by building UUID",
    )
    activity_uuid: UUID | None = Field(
        default=None,
        description="Filter organizations by activity UUID",
    )
    include_children: bool = Field(
        default=False,
        description="Include organizations from child activities of the selected activity",
    )
    radius: float | None = Field(
        default=None,
        ge=1,
        le=100_000,
        description="Search radius in meters (works only with center_lat and center_long)",
    )
    center_lat: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitude of search center for radius filter",
    )
    center_long: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitude of search center for radius filter",
    )
    min_lat: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Minimum latitude for rectangular area filter",
    )
    max_lat: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Maximum latitude for rectangular area filter",
    )
    min_long: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Minimum longitude for rectangular area filter",
    )
    max_long: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Maximum longitude for rectangular area filter",
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        description="Filter organizations by partial name match",
    )
    cursor: str | None = Field(
        default=None,
        description="Cursor from the previous page (exclusive)",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Page size")

    @model_validator(mode="after")
    def validate_geo_filters(self) -> "OrganizationQueryParams":
        radius_values = [self.radius, self.center_lat, self.center_long]
        bbox_values = [self.min_lat, self.max_lat, self.min_long, self.max_long]
        has_radius_filter = any(value is not None for value in radius_values)
        has_bbox_filter = any(value is not None for value in bbox_values)

        if has_radius_filter and has_bbox_filter:
            raise ValueError(
                "Use either radius filter or rectangular area filter, not both"
            )

        if has_radius_filter and not all(value is not None for value in radius_values):
            raise ValueError(
                "Radius filter requires radius, center_lat and center_long"
            )

        if has_bbox_filter and not all(value is not None for value in bbox_values):
            raise ValueError(
                "Rectangular area filter requires min_lat, max_lat, min_long and max_long"
            )

        if has_bbox_filter:
            assert self.min_lat is not None
            assert self.max_lat is not None
            assert self.min_long is not None
            assert self.max_long is not None

            if self.min_lat >= self.max_lat:
                raise ValueError("min_lat must be less than max_lat")

            if self.min_long >= self.max_long:
                raise ValueError("min_long must be less than max_long")

        return self

    def to_dto(self) -> OrganizationFilter:
        return OrganizationFilter(
            building_uuid=self.building_uuid,
            activity=OrganizationActivityFilter(
                activity_uuid=self.activity_uuid,
                include_children=self.include_children,
            )
            if self.activity_uuid
            else None,
            within_radius=WithinRadiusFilter(
                radius=self.radius,
                center_lat=self.center_lat,
                center_long=self.center_long,
            )
            if (
                self.radius is not None
                and self.center_lat is not None
                and self.center_long is not None
            )
            else None,
            within_bounding_box=WithinBoundingBoxFilter(
                min_lat=self.min_lat,
                max_lat=self.max_lat,
                min_long=self.min_long,
                max_long=self.max_long,
            )
            if (
                self.min_lat is not None
                and self.max_lat is not None
                and self.min_long is not None
                and self.max_long is not None
            )
            else None,
            name=self.name,
            pagination=PaginationParams(cursor=self.cursor, limit=self.limit),
        )


class BuildingQueryParams(BaseModel):
    cursor: str | None = Field(
        default=None,
        description="Cursor from the previous page (exclusive)",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Page size")

    def to_dto(self) -> BuildingFilter:
        return BuildingFilter(
            pagination=PaginationParams(cursor=self.cursor, limit=self.limit)
        )
