import base64
import json
from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import Select, and_, cast, func, or_, select

from src.database import Database
from src.dto import (
    Activity,
    Building,
    BuildingFilter,
    Organization,
    OrganizationFilter,
    OrganizationPhoneNumber,
    PaginatedBuildings,
    PaginatedOrganizations,
)

from .model import (
    Activity as ActivityModel,
)
from .model import (
    Building as BuildingModel,
)
from .model import Organization as OrganizationModel
from .model import OrganizationPhoneNumber as OrganizationPhoneNumberModel


class KeysetCursorCodec:
    @staticmethod
    def encode(created_at: datetime, entity_id: UUID) -> str:
        payload = {"created_at": created_at.isoformat(), "id": str(entity_id)}
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8"))
        return encoded.decode("utf-8")

    @staticmethod
    def decode(cursor: str) -> tuple[datetime, UUID]:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
            payload = json.loads(decoded)
            return datetime.fromisoformat(payload["created_at"]), UUID(payload["id"])
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid pagination cursor") from exc


class PostgresDirectoryRepository:
    def __init__(self, database: Database):
        self.database = database

    async def get_organizations(
        self, filter: OrganizationFilter
    ) -> PaginatedOrganizations:
        """Get organization list"""
        page_size = filter.pagination.limit
        stmt = (
            Select(
                OrganizationModel.id.label("org_id"),
                OrganizationModel.created_at.label("org_created_at"),
                OrganizationModel.name.label("org_name"),
                ActivityModel.id.label("act_id"),
                ActivityModel.name.label("act_name"),
                BuildingModel.id.label("bld_id"),
                BuildingModel.address.label("bld_address"),
                func.ST_Y(cast(BuildingModel.location, Geometry)).label("bld_lat"),
                func.ST_X(cast(BuildingModel.location, Geometry)).label("bld_lon"),
            )
            .join(ActivityModel)
            .join(BuildingModel)
        )

        if filter.name:
            stmt = stmt.where(OrganizationModel.name.ilike(f"%{filter.name}%"))

        if filter.building_uuid:
            stmt = stmt.where(BuildingModel.id == filter.building_uuid)

        if filter.activity:
            if filter.activity.include_children:
                children_subquery = select(ActivityModel.id).where(
                    ActivityModel.parent_id == filter.activity.activity_uuid
                )
                stmt = stmt.where(
                    or_(
                        ActivityModel.id == filter.activity.activity_uuid,
                        ActivityModel.parent_id == filter.activity.activity_uuid,
                        ActivityModel.parent_id.in_(children_subquery),
                    )
                )
            else:
                stmt = stmt.where(ActivityModel.id == filter.activity.activity_uuid)

        if filter.within_radius:
            stmt = stmt.where(
                func.ST_DWithin(
                    BuildingModel.location,
                    cast(
                        func.ST_SetSRID(
                            func.ST_MakePoint(
                                filter.within_radius.center_long,
                                filter.within_radius.center_lat,
                            ),
                            4326,
                        ),
                        Geometry("POINT", srid=4326),
                    ),
                    filter.within_radius.radius,
                )
            )

        if filter.pagination.cursor:
            cursor_created_at, cursor_id = KeysetCursorCodec.decode(
                filter.pagination.cursor
            )
            stmt = stmt.where(
                or_(
                    OrganizationModel.created_at > cursor_created_at,
                    and_(
                        OrganizationModel.created_at == cursor_created_at,
                        OrganizationModel.id > cursor_id,
                    ),
                )
            )

        stmt = stmt.order_by(
            OrganizationModel.created_at.asc(), OrganizationModel.id.asc()
        ).limit(page_size + 1)
        result = await self.database.fetch_all(stmt)

        has_next = len(result) > page_size
        rows = result[:page_size]

        organizations: list[Organization] = []
        for row in rows:
            organizations.append(
                Organization(
                    uuid=row.org_id,
                    name=row.org_name,
                    phone_numbers=[],
                    activity=Activity(uuid=row.act_id, name=row.act_name)
                    if row.act_id
                    else None,
                    building=Building(
                        uuid=row.bld_id,
                        address=row.bld_address,
                        coordinate_lat=row.bld_lat,
                        coordinate_long=row.bld_lon,
                    )
                    if row.bld_id
                    else None,
                )
            )

        next_cursor: str | None = (
            KeysetCursorCodec.encode(
                created_at=rows[-1].org_created_at,
                entity_id=rows[-1].org_id,
            )
            if has_next
            else None
        )
        return PaginatedOrganizations(items=organizations, next_cursor=next_cursor)

    async def get_organization_by_uuid(
        self, organization_uuid: str
    ) -> Organization | None:
        """Get detail info about organization by uuid"""
        org_stmt = (
            Select(
                OrganizationModel.id.label("org_id"),
                OrganizationModel.name.label("org_name"),
                ActivityModel.id.label("act_id"),
                ActivityModel.name.label("act_name"),
                BuildingModel.id.label("bld_id"),
                BuildingModel.address.label("bld_address"),
                func.ST_Y(cast(BuildingModel.location, Geometry)).label("bld_lat"),
                func.ST_X(cast(BuildingModel.location, Geometry)).label("bld_lon"),
            )
            .join(ActivityModel)
            .join(BuildingModel)
        ).where(OrganizationModel.id == organization_uuid)

        numbers_stmt = Select(OrganizationPhoneNumberModel).where(
            OrganizationPhoneNumberModel.organization_id == organization_uuid
        )

        org_result = await self.database.fetch_one(org_stmt)

        if org_result:
            phone_numbers = [
                OrganizationPhoneNumber(number=org_number.phone_number)
                for org_number in await self.database.fetch_all(numbers_stmt)
            ]

            return (
                Organization(
                    uuid=org_result.org_id,
                    name=org_result.org_name,
                    phone_numbers=phone_numbers,
                    activity=Activity(uuid=org_result.act_id, name=org_result.act_name)
                    if org_result.act_id
                    else None,
                    building=Building(
                        uuid=org_result.bld_id,
                        address=org_result.bld_address,
                        coordinate_lat=org_result.bld_lat,
                        coordinate_long=org_result.bld_lon,
                    )
                    if org_result.bld_id
                    else None,
                )
                if org_result
                else None
            )

    async def get_buildings(self, filter: BuildingFilter) -> PaginatedBuildings:
        page_size = filter.pagination.limit
        stmt = Select(
            BuildingModel.id.label("bld_id"),
            BuildingModel.created_at.label("bld_created_at"),
            BuildingModel.address.label("bld_address"),
            func.ST_Y(cast(BuildingModel.location, Geometry)).label("bld_lat"),
            func.ST_X(cast(BuildingModel.location, Geometry)).label("bld_lon"),
        )

        if filter.pagination.cursor:
            cursor_created_at, cursor_id = KeysetCursorCodec.decode(
                filter.pagination.cursor
            )
            stmt = stmt.where(
                or_(
                    BuildingModel.created_at > cursor_created_at,
                    and_(
                        BuildingModel.created_at == cursor_created_at,
                        BuildingModel.id > cursor_id,
                    ),
                )
            )

        stmt = stmt.order_by(
            BuildingModel.created_at.asc(), BuildingModel.id.asc()
        ).limit(page_size + 1)
        result = await self.database.fetch_all(stmt)

        has_next = len(result) > page_size
        rows = result[:page_size]

        buildings = [
            Building(
                uuid=row.bld_id,
                address=row.bld_address,
                coordinate_lat=row.bld_lat,
                coordinate_long=row.bld_lon,
            )
            for row in rows
        ]
        next_cursor: str | None = (
            KeysetCursorCodec.encode(
                created_at=rows[-1].bld_created_at,
                entity_id=rows[-1].bld_id,
            )
            if has_next
            else None
        )
        return PaginatedBuildings(items=buildings, next_cursor=next_cursor)
