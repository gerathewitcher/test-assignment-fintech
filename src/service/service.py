from uuid import UUID

from src.dto import (
    BuildingFilter,
    Organization,
    OrganizationFilter,
    PaginatedBuildings,
    PaginatedOrganizations,
)
from src.repository.directory import DirectoryRepositoryProtocol


class DirectoryService:
    def __init__(self, directory_repository: DirectoryRepositoryProtocol):
        self.directory_repository = directory_repository

    async def get_organizations(
        self, filter: OrganizationFilter
    ) -> PaginatedOrganizations:
        organizations = await self.directory_repository.get_organizations(filter)
        return organizations

    async def get_organization(self, organization_uuid: UUID) -> Organization | None:
        return await self.directory_repository.get_organization_by_uuid(
            organization_uuid
        )

    async def get_buildings(self, filter: BuildingFilter) -> PaginatedBuildings:
        return await self.directory_repository.get_buildings(filter)
