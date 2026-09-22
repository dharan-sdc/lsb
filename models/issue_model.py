from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class BloodIssue(Base):
    __tablename__ = 'blood_issues'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_code = Column(String(50), unique=True, nullable=False)
    request_id = Column(Integer, ForeignKey('blood_requests.id'), nullable=False)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    quantity_units = Column(Integer, default=1, nullable=False)
    issue_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    issued_by = Column(String(120), nullable=False)
    recipient_name = Column(String(150), nullable=False)
    recipient_contact = Column(String(50), nullable=True)
    certificate_no = Column(String(100), unique=True, nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    request = relationship('BloodRequest', back_populates='issue')
    blood_group = relationship('BloodGroup')

    def to_dict(self):
        return {
            'id': self.id,
            'issue_code': self.issue_code,
            'request_id': self.request_id,
            'request_code': self.request.request_code if self.request else None,
            'patient_name': self.request.patient.name if self.request and self.request.patient else 'Unknown',
            'hospital_name': self.request.hospital.name if self.request and self.request.hospital else 'Direct Hospital',
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'quantity_units': self.quantity_units,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'issued_by': self.issued_by,
            'recipient_name': self.recipient_name,
            'recipient_contact': self.recipient_contact,
            'certificate_no': self.certificate_no,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
