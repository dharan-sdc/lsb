from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from models.base import Base

class BloodCamp(Base):
    __tablename__ = 'blood_camps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    camp_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    organizer = Column(String(150), nullable=False)
    camp_date = Column(Date, nullable=False)
    start_time = Column(String(30), default='09:00 AM')
    end_time = Column(String(30), default='05:00 PM')
    location = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), default='Metro City')
    state = Column(String(100), default='State')
    map_link = Column(String(255), nullable=True)
    contact_person = Column(String(120), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    contact_email = Column(String(120), nullable=True)
    capacity = Column(Integer, default=100)
    target_units = Column(Integer, default=50)
    collected_units = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(String(30), default='Upcoming')  # Upcoming, In-Progress, Completed, Cancelled
    blood_bank_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    registrations = relationship('CampRegistration', back_populates='camp', cascade='all, delete-orphan')

    def to_dict(self):
        reg_count = len(self.registrations) if self.registrations else 0
        attended_count = sum(1 for r in self.registrations if r.status in ['Attended', 'Screened', 'Eligible', 'Donated']) if self.registrations else 0
        donated_count = sum(1 for r in self.registrations if r.status == 'Donated') if self.registrations else 0
        eligible_count = sum(1 for r in self.registrations if r.status in ['Eligible', 'Donated']) if self.registrations else 0

        return {
            'id': self.id,
            'camp_code': self.camp_code,
            'name': self.name,
            'organizer': self.organizer,
            'camp_date': self.camp_date.isoformat() if self.camp_date else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'map_link': self.map_link,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'capacity': self.capacity,
            'target_units': self.target_units,
            'collected_units': self.collected_units,
            'description': self.description,
            'instructions': self.instructions,
            'status': self.status,
            'registered_count': reg_count,
            'attended_count': attended_count,
            'eligible_count': eligible_count,
            'donated_count': donated_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CampRegistration(Base):
    __tablename__ = 'camp_registrations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    camp_id = Column(Integer, ForeignKey('blood_camps.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    donor_id = Column(Integer, ForeignKey('donors.id'), nullable=True)
    donor_name = Column(String(150), nullable=False)
    donor_phone = Column(String(30), nullable=True)
    donor_email = Column(String(120), nullable=True)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    registration_code = Column(String(50), unique=True, nullable=False)
    status = Column(String(30), default='Registered')  # Registered, Attended, Screened, Eligible, Ineligible, Donated, Cancelled
    blood_pressure = Column(String(30), nullable=True)
    hemoglobin = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    eligibility_notes = Column(Text, nullable=True)
    units_donated = Column(Integer, default=0)
    blood_unit_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    camp = relationship('BloodCamp', back_populates='registrations')
    user = relationship('User', foreign_keys=[user_id])
    blood_group = relationship('BloodGroup')

    def to_dict(self):
        return {
            'id': self.id,
            'camp_id': self.camp_id,
            'camp_name': self.camp.name if self.camp else None,
            'camp_code': self.camp.camp_code if self.camp else None,
            'camp_date': self.camp.camp_date.isoformat() if self.camp and self.camp.camp_date else None,
            'camp_location': self.camp.location if self.camp else None,
            'user_id': self.user_id,
            'donor_id': self.donor_id,
            'donor_name': self.donor_name,
            'donor_phone': self.donor_phone,
            'donor_email': self.donor_email,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'age': self.age,
            'gender': self.gender,
            'registration_code': self.registration_code,
            'status': self.status,
            'blood_pressure': self.blood_pressure,
            'hemoglobin': self.hemoglobin,
            'weight_kg': self.weight_kg,
            'temperature': self.temperature,
            'eligibility_notes': self.eligibility_notes,
            'units_donated': self.units_donated,
            'blood_unit_code': self.blood_unit_code,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
