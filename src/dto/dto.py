from uuid import UUID

from pydantic import BaseModel, Field


class WithinRadiusFilter(BaseModel):
    """
    Filter by radius
    """

    radius: float = Field(default=1000.0, description="Radius in meters")
    center_lat: float = Field(default=0.0, description="Latitude of the center")
    center_long: float = Field(default=0.0, description="Longitude of the center")


class OrganizationActivityFilter(BaseModel):
    """
    Filter organizations by activity
    """

    activity_uuid: UUID | None = Field(default=None, description="UUID of the activity")
    include_children: bool = Field(
        default=False, description="Include organizations with child activities"
    )


class OrganizationFilter(BaseModel):
    """
    Filter organizations by various criteria
    """

    building_uuid: UUID | None = Field(
        default=None, description="filter by UUID of the building"
    )
    activity: OrganizationActivityFilter | None = Field(
        default=None, description="Filter by activity"
    )
    within_radius: WithinRadiusFilter | None = Field(
        default=None, description="Filter by radius"
    )
    name: str | None = Field(
        default=None, description="filter by name of the organization"
    )
    pagination: "PaginationParams" = Field(description="Pagination params")


class PaginationParams(BaseModel):
    cursor: str | None = Field(default=None, description="Pagination cursor")
    limit: int = Field(default=20, ge=1, le=100, description="Page size")


class BuildingFilter(BaseModel):
    pagination: PaginationParams = Field(description="Pagination params")


class Building(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the building")
    address: str = Field(description="Address of the building")
    coordinate_lat: float = Field(description="Latitude coordinate of the building")
    coordinate_long: float = Field(description="Longitude coordinate of the building")


class Activity(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the activity")
    name: str = Field(description="Name of the activity")
    parent: "Activity | None" = Field(description="Parent activity", default=None)


class OrganizationPhoneNumber(BaseModel):
    number: str = Field(description="Phone number")


class Organization(BaseModel):
    uuid: UUID = Field(description="Unique identifier for the organization")
    name: str = Field(description="Name of the organization")
    building: Building | None = Field(
        description="Building associated with the organization", default=None
    )
    activity: Activity | None = Field(
        description="Activity associated with the organization", default=None
    )
    phone_numbers: list[OrganizationPhoneNumber] = Field(
        description="Phone numbers associated with the organization"
    )


class PaginatedOrganizations(BaseModel):
    items: list[Organization] = Field(description="Organization list")
    next_cursor: str | None = Field(
        default=None, description="Cursor for the next page"
    )


class PaginatedBuildings(BaseModel):
    items: list[Building] = Field(description="Building list")
    next_cursor: str | None = Field(
        default=None, description="Cursor for the next page"
    )
