from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base import Base

class Donor(Base):
    __tablename__ = 'donors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)  # Male, Female, Other
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    contact = Column(String(50), nullable=False)
    email = Column(String(150), nullable=True)
    address = Column(Text, nullable=True)
    medical_notes = Column(Text, nullable=True)
    last_donation_date = Column(Date, nullable=True)
    total_donations = Column(Integer, default=0)
    status = Column(String(20), default='Eligible')  # Eligible, Ineligible, Deferred
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    blood_group = relationship('BloodGroup')
    donations = relationship('BloodDonation', back_populates='donor', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'contact': self.contact,
            'email': self.email,
            'address': self.address,
            'medical_notes': self.medical_notes,
            'last_donation_date': self.last_donation_date.isoformat() if self.last_donation_date else None,
            'total_donations': self.total_donations,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
