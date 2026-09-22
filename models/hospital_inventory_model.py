from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from models.base import Base

class HospitalInventory(Base):
    __tablename__ = 'hospital_inventory'
    __table_args__ = (
        UniqueConstraint('hospital_id', 'blood_group_id', name='uq_hospital_blood_group'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    units_available = Column(Integer, default=0, nullable=False)
    total_ml = Column(Float, default=0.0, nullable=False)
    low_stock_threshold = Column(Integer, default=3, nullable=False)
    storage_fridge = Column(String(100), default='Hospital Emergency Fridge - Unit 1')
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    hospital = relationship('Hospital', back_populates='inventory')
    blood_group = relationship('BloodGroup')

    def to_dict(self):
        return {
            'id': self.id,
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital.name if self.hospital else 'Hospital',
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'units_available': self.units_available,
            'total_ml': self.total_ml,
            'low_stock_threshold': self.low_stock_threshold,
            'is_low_stock': self.units_available <= self.low_stock_threshold,
            'storage_fridge': self.storage_fridge,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
