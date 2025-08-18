from typing import TYPE_CHECKING, List
from sqlalchemy import String, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from Database_Table.base import Base

if TYPE_CHECKING:
    from Database_Table.order import Order

# Inventory model to represent inventory items related to orders
class Inventory(Base, SerializerMixin):
    __tablename__ = "Inventory"

    ItemId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    Date: Mapped[str] = mapped_column(String(10))
    ItemQuantity: Mapped[int] = mapped_column(Integer, nullable=True)
    ItemCategory: Mapped[str] = mapped_column(String(50), nullable=True)
    UnitsSold: Mapped[int] = mapped_column(Integer, nullable=True)
    Weight: Mapped[float] = mapped_column(Float, nullable=True)
    Size: Mapped[float] = mapped_column(Float, nullable=True)
    Priority: Mapped[str] = mapped_column(String(50))
    Dispose: Mapped[bool] = mapped_column(Boolean, nullable=True)

    # Defining relationship with Order model
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="inventory_item")