from typing import Protocol
from uuid import UUID

from src.dto import (
    BuildingFilter,
    Organization,
    OrganizationFilter,
    PaginatedBuildings,
    PaginatedOrganizations,
)


class DirectoryServiceProtocol(Protocol):
    async def get_organizations(
        self, filter: OrganizationFilter
    ) -> PaginatedOrganizations: ...

    async def get_organization(
        self, organization_uuid: UUID
    ) -> Organization | None: ...

    async def get_buildings(self, filter: BuildingFilter) -> PaginatedBuildings: ...
