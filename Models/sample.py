from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from Models.base import Base


if TYPE_CHECKING:
    from Models.forecast_sales import Forecast_Sales
    from Models.inventory import Inventory

# Sample model to represent a sample with related sales and inventory
class Sample(Base):
    __tablename__ = "sample"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(30))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Sales forecasts related to this sample
    sales: Mapped[List["Forecast_Sales"]] = relationship(
        "Forecast_Sales", back_populates="sample", cascade="all, delete-orphan"
    )
    # Inventory items related to this sample
    inventory: Mapped[List["Inventory"]] = relationship(
        "Inventory", back_populates="sample", cascade="all, delete-orphan"
    )
