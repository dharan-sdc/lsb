from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from models.base import Base

class BloodGroup(Base):
    __tablename__ = 'blood_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(10), unique=True, nullable=False)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    rh_factor = Column(String(10), nullable=False)  # Positive, Negative
    description = Column(Text, nullable=True)
    can_donate_to = Column(String(100), nullable=True)  # e.g., "A+, AB+"
    can_receive_from = Column(String(100), nullable=True)  # e.g., "A+, A-, O+, O-"
    
    inventory = relationship('BloodInventory', back_populates='blood_group', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'group_name': self.group_name,
            'rh_factor': self.rh_factor,
            'description': self.description,
            'can_donate_to': self.can_donate_to,
            'can_receive_from': self.can_receive_from,
            'units_available': self.inventory.units_available if self.inventory else 0,
            'low_stock_threshold': self.inventory.low_stock_threshold if self.inventory else 5,
            'is_low_stock': (self.inventory.units_available <= self.inventory.low_stock_threshold) if self.inventory else False
        }
