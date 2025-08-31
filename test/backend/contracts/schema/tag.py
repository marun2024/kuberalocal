from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel
from backend.src.backend.core.auditbase import AuditBase

class TagBase(AuditBase):
    name: str

class TagCreate(TagBase):
    pass

class TagUpdate(TagBase):
    name: Optional[str] = None

class TagResponse(TagBase):
    id: int

class TagRead(TagBase):
    id: int
    class Config:
        from_attributes = True


