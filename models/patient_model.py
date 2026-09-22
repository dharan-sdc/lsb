from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base import Base

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)
    condition = Column(String(255), nullable=True)  # e.g., Surgery, Thalassemia, Trauma
    contact = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    admission_date = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    status = Column(String(20), default='Admitted')  # Admitted, Discharged, Transferred
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    blood_group = relationship('BloodGroup')
    hospital = relationship('Hospital')
    requests = relationship('BloodRequest', back_populates='patient', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital.name if self.hospital else 'Direct / Walk-in',
            'condition': self.condition,
            'contact': self.contact,
            'address': self.address,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
