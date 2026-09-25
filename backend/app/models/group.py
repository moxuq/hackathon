from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GroupsType(str, Enum):
    COMPANY = 'company'
    DEPOT = 'depot'
    BRIGADE = 'brigade'

class Group(Base):
    __tablename__ = 'groups'
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[GroupsType] = mapped_column(SQLEnum(GroupsType), nullable=False)
    parent_id: Mapped[str] = mapped_column(ForeignKey('groups.id'))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
