from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base import Base

class BloodRequest(Base):
    __tablename__ = 'blood_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_code = Column(String(50), unique=True, nullable=False)
    requester_type = Column(String(30), default='User')  # User, Hospital
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    patient_name = Column(String(150), nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), nullable=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    quantity_units = Column(Integer, default=1, nullable=False)
    urgency = Column(String(30), default='Normal')  # Normal, Urgent, Critical
    required_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(30), default='Pending')  # Pending, Approved, Rejected, Completed, Cancelled
    rejection_reason = Column(Text, nullable=True)
    requested_by = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship('User', foreign_keys=[user_id])
    patient = relationship('Patient', foreign_keys=[patient_id], back_populates='requests')
    hospital = relationship('Hospital', foreign_keys=[hospital_id])
    blood_group = relationship('BloodGroup')
    issue = relationship('BloodIssue', back_populates='request', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        resolved_patient = 'Unknown'
        if self.patient_name:
            resolved_patient = self.patient_name
        elif self.patient:
            resolved_patient = self.patient.name
        elif self.user:
            resolved_patient = self.user.name

        return {
            'id': self.id,
            'request_code': self.request_code,
            'requester_type': self.requester_type,
            'user_id': self.user_id,
            'patient_id': self.patient_id,
            'patient_name': resolved_patient,
            'patient_age': self.patient_age or (self.patient.age if self.patient else (self.user.age if self.user else None)),
            'patient_gender': self.patient_gender or (self.patient.gender if self.patient else (self.user.gender if self.user else None)),
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital.name if self.hospital else ('Direct User Request' if self.requester_type == 'User' else 'General Clinic'),
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'quantity_units': self.quantity_units,
            'urgency': self.urgency,
            'required_date': self.required_date.isoformat() if self.required_date else None,
            'reason': self.reason,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'requested_by': self.requested_by or (self.user.name if self.user else None),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_issued': self.issue is not None
        }
