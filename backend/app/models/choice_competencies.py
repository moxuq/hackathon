import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChoiceCompetencie(Base):
    __tablename__ = 'choicecompotencies'

    choice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('choices.id'), nullable=False)
    competency_code: Mapped[str] = mapped_column(ForeignKey('competencies.code'), nullable=False)
    delta: Mapped[int] = mapped_column(nullable=False)
