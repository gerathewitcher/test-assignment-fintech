from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter

from src.api.security import verify_api_key
from src.dto import Organization
from src.service import DirectoryServiceProtocol

from .constants import API_V1_DIRECTORY_PREFIX
from .schema import (
    BuildingPageSchema,
    BuildingQueryParams,
    OrganizationFullSchema,
    OrganizationPageSchema,
    OrganizationQueryParams,
)

router = APIRouter(
    prefix=API_V1_DIRECTORY_PREFIX,
    route_class=DishkaRoute,
    dependencies=[Depends(verify_api_key)],
)


@router.get("/organization", response_model=OrganizationPageSchema)
async def get_organizations(
    params: Annotated[OrganizationQueryParams, Query()],
    directory_service: FromDishka[DirectoryServiceProtocol],
):
    """Get organizations"""
    try:
        organizations = await directory_service.get_organizations(params.to_dto())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrganizationPageSchema.from_dto(organizations)


@router.get("/organization/{organization_uuid}", response_model=OrganizationFullSchema)
async def get_organization(
    organization_uuid: UUID,
    directory_service: FromDishka[DirectoryServiceProtocol],
):
    """Get organization by uuid"""
    organization: Organization | None = await directory_service.get_organization(
        organization_uuid
    )

    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationFullSchema.from_dto(organization)


@router.get("/building", response_model=BuildingPageSchema)
async def get_buildings(
    params: Annotated[BuildingQueryParams, Query()],
    directory_service: FromDishka[DirectoryServiceProtocol],
):
    """Get buildings"""
    try:
        buildings = await directory_service.get_buildings(params.to_dto())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BuildingPageSchema.from_dto(buildings)
