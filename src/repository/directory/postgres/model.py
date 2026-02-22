import datetime
import uuid

from geoalchemy2 import Geography
from sqlalchemy import VARCHAR, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Organization(Base):
    __tablename__ = "organization"
    __table_args__ = (
        Index(
            "ix_organization_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index("ix_organization_created_at_id", "created_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    name: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )

    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("building.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Building(Base):
    __tablename__ = "building"
    __table_args__ = (Index("ix_building_created_at_id", "created_at", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    address: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )

    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Activity(Base):
    __tablename__ = "activity"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    name: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )


class OrganizationPhoneNumber(Base):
    __tablename__ = "organization_phone_number"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization.id", ondelete="SET NULL"),
        nullable=True,
    )

    phone_number: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
