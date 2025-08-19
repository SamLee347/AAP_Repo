from typing import TYPE_CHECKING, List
from sqlalchemy import String, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from Database_Table.base import Base
import numpy as np

if TYPE_CHECKING:
    from Database_Table.order import Order

# Inventory model to represent inventory items related to orders
class Inventory(Base, SerializerMixin):
    __tablename__ = "Inventory"
    serialize_rules = ("-orders.inventory_item",)

    ItemId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ItemName: Mapped[str] = mapped_column(String(100), nullable=True)
    ItemCategory: Mapped[str] = mapped_column(String(50), nullable=True)
    ItemQuantity: Mapped[int] = mapped_column(Integer, nullable=True)
    UnitsSold: Mapped[int] = mapped_column(Integer, nullable=True)
    Weight: Mapped[float] = mapped_column(Float, nullable=True)
    Size: Mapped[str] = mapped_column(String(10), nullable=True)
    Priority: Mapped[str] = mapped_column(String(50))
    Location: Mapped[str] = mapped_column(String(100), nullable=True)
    Date: Mapped[str] = mapped_column(String(10))
    Dispose: Mapped[bool] = mapped_column(Boolean, nullable=True)
    DemandForecast: Mapped[float] = mapped_column(Float, nullable=True)

    # Defining relationship with Order model
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="inventory_item")

    def get_disposal_features(self):
        return [
            self.ItemQuantity,          # Inventory_Level
            (self.UnitsSold / self.ItemQuantity) if self.ItemQuantity > 0 else 0,  # Inventory_Turnover
            self.UnitsSold,             # Units_Sold
            self.DemandForecast,        # Demand_Forecast (placeholder)
            np.nan,                          # Inventory_Lag_1 (placeholder)
            (self.UnitsSold / self.ItemQuantity) if self.ItemQuantity > 0 else 0,    # Turnover_Lag_1 (placeholder)
        ]