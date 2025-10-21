"""
Database models for the submission service
SQLAlchemy ORM models matching the PostgreSQL schema

Author: TUS Development Team
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime,
    Date, Text, ForeignKey, Enum, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from database.db_connection import Base


# Enumerations
import enum


class UserRole(enum.Enum):
    """User role enumeration"""
    executive = "executive"
    staff = "staff"
    public = "public"
    admin = "admin"


class UploadStatus(enum.Enum):
    """File upload status enumeration"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"


class User(Base):
    """
    User model for authentication and authorization
    Maps to 'users' table in PostgreSQL
    """
    __tablename__ = 'users'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole, name='user_role'), nullable=False, default=UserRole.public, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    
    # Relationships
    uploaded_files = relationship('UploadedFile', back_populates='uploader', lazy='dynamic')
    created_templates = relationship('UploadTemplate', back_populates='creator', lazy='dynamic')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'user_id': str(self.user_id),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value if self.role else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class UploadedFile(Base):
    """
    Uploaded files tracking model
    Maps to 'uploaded_files' table in PostgreSQL
    """
    __tablename__ = 'uploaded_files'
    
    file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100))
    upload_status = Column(Enum(UploadStatus, name='upload_status'), default=UploadStatus.pending, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), index=True)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    processed_at = Column(DateTime(timezone=True))
    rows_processed = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    error_message = Column(Text)
    validation_notes = Column(Text)
    
    # Relationships
    uploader = relationship('User', back_populates='uploaded_files')
    engagement_data = relationship('EngagementData', back_populates='file', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('file_size > 0', name='valid_file_size'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'file_id': str(self.file_id),
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'upload_status': self.upload_status.value if self.upload_status else None,
            'uploaded_by': str(self.uploaded_by) if self.uploaded_by else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'rows_processed': self.rows_processed,
            'rows_failed': self.rows_failed
        }


class EngagementData(Base):
    """
    Main engagement data model with flexible JSONB storage
    Maps to 'engagement_data' table in PostgreSQL
    """
    __tablename__ = 'engagement_data'
    
    data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey('uploaded_files.file_id', ondelete='CASCADE'), index=True)
    row_number = Column(Integer, nullable=False)
    
    # Core fields
    submission_date = Column(Date, index=True)
    department = Column(String(255), index=True)
    category = Column(String(255), index=True)
    
    # Flexible JSONB storage for dynamic fields
    data_fields = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    file = relationship('UploadedFile', back_populates='engagement_data')
    
    __table_args__ = (
        CheckConstraint("jsonb_typeof(data_fields) = 'object'", name='valid_data_fields'),
        Index('idx_engagement_data_fields_gin', 'data_fields', postgresql_using='gin'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'data_id': str(self.data_id),
            'file_id': str(self.file_id),
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'department': self.department,
            'category': self.category,
            'data_fields': self.data_fields,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ValidationRule(Base):
    """
    Validation rules for file uploads
    Maps to 'validation_rules' table in PostgreSQL
    """
    __tablename__ = 'validation_rules'
    
    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), unique=True, nullable=False)
    rule_description = Column(Text)
    field_name = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)
    is_required = Column(Boolean, default=False)
    validation_regex = Column(String(500))
    min_value = Column(Integer)
    max_value = Column(Integer)
    allowed_values = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class UploadTemplate(Base):
    """
    Upload template configurations
    Maps to 'upload_templates' table in PostgreSQL
    """
    __tablename__ = 'upload_templates'
    
    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), unique=True, nullable=False)
    template_version = Column(String(50), nullable=False)
    description = Column(Text)
    headers = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    
    # Relationships
    creator = relationship('User', back_populates='created_templates')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'template_id': str(self.template_id),
            'template_name': self.template_name,
            'template_version': self.template_version,
            'description': self.description,
            'headers': self.headers,
            'is_active': self.is_active
        }


class AuditLog(Base):
    """
    Audit logging model
    Maps to 'audit_log' table in PostgreSQL
    """
    __tablename__ = 'audit_log'
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), index=True)
    action = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), index=True)
    record_id = Column(UUID(as_uuid=True))
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
