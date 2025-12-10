"""
Base SQLAlchemy models and utilities.
"""
from sqlalchemy import Column, DateTime, func, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TimestampMixin:
    """Adds created_at and updated_at columns to a model."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SoftDeleteMixin:
    """Adds soft delete functionality to a model."""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
