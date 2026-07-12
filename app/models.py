import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class UserRole(str, Enum):
    CITIZEN = "Citizen"
    CONSTITUENCY_ADMIN = "Constituency Administrator"
    NATIONAL_ADMIN = "National Administrator"

class ProjectStatus(str, Enum):
    PROPOSED = "Proposed"
    APPROVED = "Approved"
    IN_PROGRESS = "In Progress"
    ABANDONED = "Abandoned"
    COMPLETED = "Completed"

class VerificationStatus(str, Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CITIZEN, nullable=False)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    feedbacks = db.relationship('CitizenFeedback', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Province(db.Model):
    __tablename__ = 'provinces'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationships
    districts = db.relationship('District', backref='province', lazy=True)

class District(db.Model):
    __tablename__ = 'districts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.id'), nullable=False)
    
    # Relationships
    constituencies = db.relationship('Constituency', backref='district', lazy=True)

class Constituency(db.Model):
    __tablename__ = 'constituencies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, index=True)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Relationships
    allocations = db.relationship('CDFAllocation', backref='constituency', lazy=True)
    projects = db.relationship('Project', backref='constituency', lazy=True)
    users = db.relationship('User', backref='constituency', lazy=True)

class CDFAllocation(db.Model):
    __tablename__ = 'cdf_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=False)
    fiscal_year = db.Column(db.Integer, nullable=False)
    allocated_amount = db.Column(db.Numeric(15, 2), nullable=False)
    disbursed_amount = db.Column(db.Numeric(15, 2), default=0.00)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('constituency_id', 'fiscal_year', name='_constituency_year_uc'),)

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Numeric(15, 2), nullable=False)
    expended_amount = db.Column(db.Numeric(15, 2), default=0.00)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=False)
    contractor_name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PROPOSED, nullable=False, index=True)
    progress_percentage = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    financial_records = db.relationship('FinancialTransaction', backref='project', lazy=True, cascade="all, delete-orphan")
    feedbacks = db.relationship('CitizenFeedback', backref='project', lazy=True, cascade="all, delete-orphan")

class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    recipient = db.Column(db.String(150), nullable=False)
    reference_number = db.Column(db.String(100), unique=True, nullable=False)

# app/models.py
class CitizenFeedback(db.Model):
    __tablename__ = 'citizen_feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    # Set nullable=True so public users can submit feedback without an account
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    feedback_type = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    # Ensure this matches your Enum or String status
    verification_status = db.Column(db.String(20), default='PENDING', nullable=False)
    upvote_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    evidence_attachments = db.relationship(
        'UploadedEvidence', backref='feedback', lazy=True,
        cascade='all, delete-orphan'
    )

class UploadedEvidence(db.Model):
    __tablename__ = 'uploaded_evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    feedback_id = db.Column(db.Integer, db.ForeignKey('citizen_feedbacks.id'), nullable=False)
    file_secure_url = db.Column(db.String(500), nullable=False) # Cloud storage/S3 public address path
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ReportExportLog(db.Model):
    __tablename__ = 'report_export_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=True)
    report_type = db.Column(db.String(50), nullable=False) # e.g., "PDF_Summary", "CSV_Transactions"
    generated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=True) # Remote or temporary path reference
    
    # Relationship
    generator = db.relationship('User', backref='reports_generated', lazy=True)