from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from models.base import Base

class BloodInventory(Base):
    __tablename__ = 'blood_inventory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), unique=True, nullable=False)
    units_available = Column(Integer, default=0, nullable=False)
    total_ml = Column(Float, default=0.0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
    storage_fridge = Column(String(100), default='Main Blood Bank Fridge - Rack A')
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    blood_group = relationship('BloodGroup', back_populates='inventory')

    def to_dict(self):
        return {
            'id': self.id,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'units_available': self.units_available,
            'total_ml': self.total_ml,
            'low_stock_threshold': self.low_stock_threshold,
            'is_low_stock': self.units_available <= self.low_stock_threshold,
            'storage_fridge': self.storage_fridge,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
