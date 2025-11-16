from .nutrition_rag_base import SQLAlchemyBase
from sqlalchemy import Column, INTEGER, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship


class Project(SQLAlchemyBase):
    """
    This class represents a project in the database.
    """

    __tablename__ = "projects"

    # The unique ID of the project.
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    # The UUID of the project.
    project_uuid = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )

    # The date and time when the project was created.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # The date and time when the project was last updated.
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # The chunks that belong to the project.
    chunks = relationship("DataChunk", back_populates="project")
    # The assets that belong to the project.
    assets = relationship("Asset", back_populates="project")
