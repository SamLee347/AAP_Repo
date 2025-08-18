from typing import List, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from sqlalchemy_serializer import SerializerMixin
from Database_Table.base import Base


if TYPE_CHECKING:
    from Database_Table.inventory import Inventory

# Sample model to represent a sample with related sales and inventory
class Order(Base, SerializerMixin):
    __tablename__ = "Order"
    serialize_rules = ("-inventory_item.orders",)

    OrderId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ItemId: Mapped[int] = mapped_column(ForeignKey("Inventory.ItemId"), nullable=False)
    OrderQuantity: Mapped[int] = mapped_column(Integer, nullable=False)
    Sales: Mapped[int] = mapped_column(Integer, nullable=False)
    Price: Mapped[float] = mapped_column(Float, nullable=False)
    Discount: Mapped[float] = mapped_column(Float, nullable=False)
    Profit: Mapped[float] = mapped_column(Float, nullable=False)
    DateOrdered: Mapped[str] = mapped_column(String(10), nullable=False)
    DateReceived: Mapped[str] = mapped_column(String(10), nullable=False)
    CustomerSegment: Mapped[str] = mapped_column(String(50), nullable=False)


    # Inventory items related to this order
    inventory_item: Mapped["Inventory"] = relationship("Inventory", back_populates="orders")

