from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, String, func

class CoreCommonBase(SQLModel):
    """Base class for all models with audit fields."""
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={
            "name": "created_at",
            "server_default": func.now(),
            "nullable": False
        }
    )

    last_updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={
            "name": "last_updated_at",
            "onupdate": func.now(),
            "nullable": True
        }
    )

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={
            "name": "deleted_at",
            "nullable": True
        }
    )

    created_by: Optional[str] = Field(
        default=None,
        sa_type=String(255),
        sa_column_kwargs={
            "name": "created_by",
            "nullable": True
        }
    )
    
    last_updated_by: Optional[str] = Field(
        default=None,
        sa_type=String(255),
        sa_column_kwargs={
            "name": "last_updated_by",
            "nullable": True
        }
    )