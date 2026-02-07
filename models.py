from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class BaseModel:
    def to_dict(self):
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            # Convert datetime objects to ISO format strings
            if isinstance(val, datetime):
                result[c.name] = val.isoformat()
            else:
                result[c.name] = val
        return result


class Contact(db.Model, BaseModel):
    __tablename__ = 'contacts'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)

    # Name fields
    full_name = db.Column(db.String(255))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # Contact information
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    mobile = db.Column(db.String(50))

    # Account relationship
    account_name = db.Column(db.String(255))

    # Professional details
    title = db.Column(db.String(100))
    department = db.Column(db.String(100))

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Mailing address
    mailing_street = db.Column(db.Text)
    mailing_city = db.Column(db.String(100))
    mailing_state = db.Column(db.String(100))
    mailing_zip = db.Column(db.String(20))
    mailing_country = db.Column(db.String(100))

    # Additional fields
    description = db.Column(db.Text)
    lead_source = db.Column(db.String(100))

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Account(db.Model, BaseModel):
    __tablename__ = 'accounts'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)
    last_activity_time = db.Column(db.DateTime)

    # Account names
    account_name = db.Column(db.String(255))
    firm_name = db.Column(db.String(255))

    # Contact information
    phone = db.Column(db.String(50))
    website = db.Column(db.String(255))

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Billing address
    billing_street = db.Column(db.Text)
    billing_city = db.Column(db.String(100))
    billing_state = db.Column(db.String(100))
    billing_code = db.Column(db.String(20))
    billing_country = db.Column(db.String(100))

    # Business details
    line_of_business = db.Column(db.String(100))
    no_of_branches = db.Column(db.Integer)
    revenue_type = db.Column(db.String(100))
    payment_terms = db.Column(db.String(100))
    gstin_uin = db.Column(db.String(100))
    expected_services_type = db.Column(db.String(255))

    # Additional fields
    description = db.Column(db.Text)

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Pipeline(db.Model, BaseModel):
    __tablename__ = 'pipelines'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)
    last_activity_time = db.Column(db.DateTime)

    # Deal information
    deal_name = db.Column(db.String(255))
    account_name = db.Column(db.String(255))
    contact_name = db.Column(db.String(255))

    # Deal status
    stage = db.Column(db.String(100))
    amount = db.Column(db.Numeric(15, 2))
    closing_date = db.Column(db.Date)

    # Pipeline details
    pipeline = db.Column(db.String(100))
    sub_pipeline = db.Column(db.String(100))

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Deal classification
    deal_type = db.Column(db.String(100))
    business_type = db.Column(db.String(100))
    expected_services_type = db.Column(db.String(255))

    # Lead information
    lead_source = db.Column(db.String(100))
    lead_source_from = db.Column(db.String(100))
    lead_origin = db.Column(db.String(100))

    # Deal metrics
    probability = db.Column(db.Numeric(5, 2))
    next_step = db.Column(db.String(255))

    # Revenue details
    revenue_type = db.Column(db.String(100))
    recurring_mode = db.Column(db.String(100))

    # Follow-up
    follow_up_date = db.Column(db.Date)

    # Additional fields
    description = db.Column(db.Text)

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Call(db.Model, BaseModel):
    __tablename__ = 'calls'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)

    # Call details
    subject = db.Column(db.String(255))
    call_type = db.Column(db.String(50))
    call_status = db.Column(db.String(50))
    call_purpose = db.Column(db.String(100))
    call_agenda = db.Column(db.Text)

    # Call timing
    call_duration = db.Column(db.String(20))  # Format: HH:MM
    call_duration_seconds = db.Column(db.Integer)
    call_start_time = db.Column(db.DateTime)

    # Call participants
    caller_id = db.Column(db.String(100))
    who_id_name = db.Column(db.String(255))

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Additional fields
    description = db.Column(db.Text)
    voice_recording = db.Column(db.String(500))
    reminder = db.Column(db.String(100))

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model, BaseModel):
    __tablename__ = 'events'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)

    # Event details
    event_title = db.Column(db.String(255))
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    all_day = db.Column(db.Boolean, default=False)
    venue = db.Column(db.String(255))

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Event description and participants
    description = db.Column(db.Text)
    participants = db.Column(db.Text)  # JSON array as string

    # Reminders and check-in
    remind_at = db.Column(db.DateTime)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    time_spent_mins = db.Column(db.Integer)

    # Related information
    related_module = db.Column(db.String(100))
    booking_id = db.Column(db.String(100))

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model, BaseModel):
    __tablename__ = 'tasks'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)

    # Task details
    subject = db.Column(db.String(255))
    due_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    priority = db.Column(db.String(50))

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Related information
    related_to_name = db.Column(db.String(255))
    related_to_module = db.Column(db.String(100))

    # Task description
    description = db.Column(db.Text)

    # Reminder
    remind_at = db.Column(db.DateTime)

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Note(db.Model, BaseModel):
    __tablename__ = 'notes'

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Zoho ID and timestamps
    zoho_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    created_time = db.Column(db.DateTime)
    modified_time = db.Column(db.DateTime)

    # Note details
    note_title = db.Column(db.String(255))
    note_content = db.Column(db.Text)

    # Owner information
    owner_name = db.Column(db.String(255))
    owner_email = db.Column(db.String(255))

    # Related information
    parent_id_name = db.Column(db.String(255))
    parent_module = db.Column(db.String(100))

    # Store full JSON for any unmapped fields
    data = db.Column(db.Text)

    # Local timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SyncLog(db.Model):
    __tablename__ = 'sync_logs'

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(100))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    message = db.Column(db.Text)
    records_synced = db.Column(db.Integer, default=0)


def init_db(app=None):
    if app:
        db.init_app(app)
        with app.app_context():
            db.create_all()