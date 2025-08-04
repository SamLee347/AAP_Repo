from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from Models.base import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from Models.sample import Sample
# Forecast_Sales model to represent sales forecasts for samples
class Forecast_Sales(Base):
    __tablename__ = "forecast_sales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7))
    sample_id: Mapped[int] = mapped_column(ForeignKey("sample.id"))

    sample: Mapped["Sample"] = relationship("Sample", back_populates="sales")
