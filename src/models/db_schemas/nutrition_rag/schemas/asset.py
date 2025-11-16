from .nutrition_rag_base import SQLAlchemyBase
from sqlalchemy import Column, INTEGER, DateTime, func, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
import uuid


class Asset(SQLAlchemyBase):
    """
    This class represents an asset in the database.
    """

    __tablename__ = "assets"

    # The unique ID of the asset.
    asset_id = Column(INTEGER, primary_key=True, autoincrement=True)
    # The UUID of the asset.
    asset_uuid = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )

    # The type of the asset.
    asset_type = Column(String, nullable=False)
    # The name of the asset.
    asset_name = Column(String, nullable=False)
    # The size of the asset in bytes.
    asset_size = Column(INTEGER, nullable=False)
    # The configuration of the asset.
    asset_config = Column(JSONB, nullable=True)

    # The ID of the project that the asset belongs to.
    asset_project_id = Column(INTEGER, ForeignKey("projects.id"), nullable=False)
    # The date and time when the asset was created.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # The date and time when the asset was last updated.
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # The project that the asset belongs to.
    project = relationship("Project", back_populates="assets")
    # The chunks that belong to the asset.
    chunks = relationship("DataChunk", back_populates="asset")

    __table_args__ = (
        Index("idx_asset_project_id", asset_project_id),
        Index("ix_asset_type", asset_type),
    )
