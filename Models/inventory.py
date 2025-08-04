from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from Models.base import Base

if TYPE_CHECKING:
    from Models.sample import Sample

# Inventory model to represent inventory items related to samples
class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String(50))
    capacity: Mapped[int]
    inventory_level: Mapped[int]
    demand_forecast: Mapped[int]
    dispose: Mapped[bool]
    sample_id: Mapped[int] = mapped_column(ForeignKey("sample.id"))

    sample: Mapped["Sample"] = relationship("Sample", back_populates="inventory")
