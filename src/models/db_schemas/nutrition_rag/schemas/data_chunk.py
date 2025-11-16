from .nutrition_rag_base import SQLAlchemyBase
from sqlalchemy import Column, INTEGER, DateTime, func, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from pydantic import BaseModel


class DataChunk(SQLAlchemyBase):
    """
    This class represents a data chunk in the database.
    """

    __tablename__ = "chunks"

    # The unique ID of the chunk.
    chunk_id = Column(INTEGER, primary_key=True, autoincrement=True)
    # The UUID of the chunk.
    chunk_uuid = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )

    # The content of the chunk.
    chunk_content = Column(String, nullable=False)
    # The metadata of the chunk.
    chunk_metadata = Column(JSONB, nullable=True)
    # The order of the chunk within the asset.
    chunk_order = Column(INTEGER, nullable=False)

    # The ID of the project that the chunk belongs to.
    chunk_project_id = Column(INTEGER, ForeignKey("projects.id"), nullable=False)
    # The ID of the asset that the chunk belongs to.
    chunk_asset_id = Column(INTEGER, ForeignKey("assets.asset_id"), nullable=False)

    # The date and time when the chunk was created.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # The date and time when the chunk was last updated.
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # The project that the chunk belongs to.
    project = relationship("Project", back_populates="chunks")
    # The asset that the chunk belongs to.
    asset = relationship("Asset", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunk_project_id", chunk_project_id),
        Index("idx_chunk_asset_id", chunk_asset_id),
    )


class RetrievedDocument(BaseModel):
    """
    This class represents a retrieved document.
    """
    text: str
    score: float
