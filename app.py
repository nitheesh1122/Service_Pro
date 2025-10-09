from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import uuid
from werkzeug.utils import secure_filename
from config import Config
import pytz

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directories exist
os.makedirs(os.path.join(app.root_path, 'uploads', 'verification_docs'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'uploads', 'profiles'), exist_ok=True)

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, provider, admin
    address = db.Column(db.Text)
    pincode = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    provider_profile = db.relationship('ServiceProvider', backref='user', uselist=False)
class ServiceProvider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_categories = db.Column(db.Text)  # JSON string of categories
    service_pincodes = db.Column(db.Text)  # JSON string of pincodes
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    availability = db.Column(db.Text)  # JSON string of availability
    hourly_rate = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    # Relationships
    bookings = db.relationship('Booking', backref='provider', lazy=True)
    verification_docs = db.relationship('VerificationDocument', backref='provider', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('service_provider.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, in_progress, completed, cancelled
    address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    service = db.relationship('Service', backref='bookings')
    reviews = db.relationship('Review', backref='booking', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('service_provider.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VerificationDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('service_provider.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # government_id, business_license, profile_photo
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text)
    type = db.Column(db.String(30), default='system')  # system, approved, rejected, message
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Timezone helpers
def get_indian_time():
    """Get current datetime in Indian timezone (Asia/Kolkata)"""
    indian_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(indian_tz)

def parse_booking_datetime(datetime_str):
    """Parse booking datetime string and return Indian timezone datetime"""
    # Parse the datetime string (assumes it's in Indian time)
    dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')

    # Assume the input is in Indian time and localize it
    indian_tz = pytz.timezone('Asia/Kolkata')
    indian_dt = indian_tz.localize(dt)

    return indian_dt

def get_utc_from_indian(indian_dt):
    """Convert Indian datetime to UTC for database storage"""
    indian_tz = pytz.timezone('Asia/Kolkata')
    utc_tz = pytz.timezone('UTC')

    # Ensure the datetime is timezone-aware
    if indian_dt.tzinfo is None:
        indian_dt = indian_tz.localize(indian_dt)

    return indian_dt.astimezone(utc_tz)

def validate_booking_time(booking_datetime):
    """
    Validate that booking time is within allowed hours for IST (8 AM to 8 PM)
    Returns None if valid, or error message if invalid
    """
    # Convert to Indian time for validation
    indian_tz = pytz.timezone('Asia/Kolkata')
    if booking_datetime.tzinfo is None:
        booking_datetime = indian_tz.localize(booking_datetime)

    indian_time = booking_datetime.astimezone(indian_tz)
    hour = indian_time.hour

    # Allow bookings between 8 AM and 8 PM IST
    if hour < 8:
        return f"Bookings are only allowed from 8:00 AM onwards. Selected time: {indian_time.strftime('%Y-%m-%d ') + str(hour) + indian_time.strftime(':%M %p')}"
    elif hour >= 20:  # 8 PM
        return f"Bookings are only allowed until 8:00 PM. Selected time: {indian_time.strftime('%Y-%m-%d ') + str(hour) + indian_time.strftime(':%M %p')}"

    return None

# Helper functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_verification_document(file, provider_id, document_type):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{provider_id}_{document_type}_{str(uuid.uuid4())[:8]}.{file.filename.rsplit('.', 1)[1].lower()}")
        upload_path = os.path.join(app.root_path, 'uploads', 'verification_docs', filename)
        file.save(upload_path)
        return filename
    return None

def require_verified_provider(f):
    def decorated_function(provider_id, *args, **kwargs):
        provider = ServiceProvider.query.get_or_404(provider_id)
        if provider.verification_status != 'verified':
            return jsonify({'error': 'Provider is not verified'}), 403
        return f(provider_id, *args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Availability helpers
def _parse_simple_availability(text):
    # Supports formats like "Mon-Fri 09:00-17:00" or JSON with days
    try:
        import re
        text = (text or '').strip()
        if not text:
            return {}
        # Try JSON first
        try:
            data = json.loads(text)
            # Expected: {"mon": [["09:00","17:00"]], ...}
            return {k.lower()[:3]: v for k, v in data.items()}
        except Exception:
            pass
        # Simple pattern Mon-Fri 09:00-17:00
        m = re.match(r"([A-Za-z]{3})-([A-Za-z]{3})\s+(\d{2}:\d{2})-(\d{2}:\d{2})", text)
        if m:
            days_order = ['mon','tue','wed','thu','fri','sat','sun']
            start_day, end_day, start_time, end_time = m.groups()
            start_idx = days_order.index(start_day.lower())
            end_idx = days_order.index(end_day.lower())
            rng = []
            i = start_idx
            while True:
                rng.append(days_order[i])
                if i == end_idx:
                    break
                i = (i + 1) % 7
            return {d: [[start_time, end_time]] for d in rng}
        return {}
    except Exception:
        return {}

def check_provider_availability(provider_id, requested_datetime):
    """
    Check if provider is available at the requested datetime.
    Returns None if available, or a message explaining why not available.
    """
    # Convert requested datetime to UTC for database queries
    requested_datetime_utc = get_utc_from_indian(requested_datetime)

    # Check for conflicting bookings
    conflicting_bookings = Booking.query.filter(
        Booking.provider_id == provider_id,
        Booking.booking_date == requested_datetime_utc,
        Booking.status.in_(['pending', 'accepted', 'in_progress'])
    ).all()

    if conflicting_bookings:
        # Convert conflicting booking time to Indian time for display
        conflicting_indian = conflicting_bookings[0].booking_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Kolkata'))
        return f"Provider already has a booking scheduled for {conflicting_indian.strftime('%Y-%m-%d ') + str(conflicting_indian.hour) + conflicting_indian.strftime(':%M %p')}"

    # Check provider's availability schedule if set
    provider = ServiceProvider.query.get(provider_id)
    if provider and provider.availability:
        try:
            # Try to parse availability schedule
            availability_info = _parse_simple_availability(provider.availability)
            if availability_info:
                requested_day = requested_datetime.strftime('%a').lower()[:3]  # mon, tue, etc.
                requested_time = requested_datetime.strftime('%H:%M')

                if requested_day not in availability_info:
                    return f"Provider is not available on {requested_datetime.strftime('%A')}s"

                # Check if requested time falls within available time slots
                available_slots = availability_info[requested_day]
                for slot in available_slots:
                    start_time, end_time = slot
                    if start_time <= requested_time <= end_time:
                        return None  # Available

                return f"Provider is not available at {requested_datetime.strftime('%Y-%m-%d ') + str(requested_datetime.hour) + requested_datetime.strftime(':%M %p')} on {requested_datetime.strftime('%A')}"
        except Exception as e:
            # If we can't parse availability, assume available
            print(f"Error parsing availability for provider {provider_id}: {e}")
            pass

def compute_next_available(availability_text):
    """
    Compute next available datetime for a provider based on their availability schedule.
    Returns None if no availability info or if provider is not available.
    """
    if not availability_text or not availability_text.strip():
        return None

    try:
        # Try to parse availability schedule
        availability_info = _parse_simple_availability(availability_text)
        if not availability_info:
            return None

        now_indian = get_indian_time()
        current_day = now_indian.strftime('%a').lower()[:3]  # mon, tue, etc.
        current_time = now_indian.strftime('%H:%M')

        # Check if provider is available today
        if current_day in availability_info:
            slots = availability_info[current_day]
            for slot in slots:
                start_time, end_time = slot
                if start_time <= current_time <= end_time:
                    # Provider is available now, return current time + 1 hour as next available
                    next_available = now_indian + timedelta(hours=1)
                    return next_available

        # Find next available day
        days_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        current_day_idx = days_order.index(current_day)

        # Look for next 7 days
        for i in range(1, 8):
            next_day_idx = (current_day_idx + i) % 7
            next_day = days_order[next_day_idx]

            if next_day in availability_info:
                slots = availability_info[next_day]
                if slots:
                    # Return the start time of the first slot on the next available day
                    start_time = slots[0][0]
                    next_day_date = now_indian + timedelta(days=i)
                    next_datetime_str = next_day_date.strftime('%Y-%m-%d ') + start_time
                    return datetime.strptime(next_datetime_str, '%Y-%m-%d %H:%M')

        return None  # No availability found

    except Exception as e:
        print(f"Error computing next availability: {e}")
        return None

def send_service_reminders(provider_id, upcoming_bookings):
    """
    Send service reminder notifications for upcoming bookings.
    This function is called from the provider dashboard to check for upcoming services.
    """
    now_indian = get_indian_time()

    for booking in upcoming_bookings:
        # Convert booking time to Indian timezone for comparison
        booking_indian = booking.booking_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Kolkata'))
        time_until_booking = (booking_indian - now_indian).total_seconds()

        # Send reminder if booking is within 2 hours and we haven't sent a reminder recently
        if 0 < time_until_booking <= 7200:  # Within 2 hours
            # Check if we've already sent a reminder for this booking recently (within last hour)
            recent_reminder = Notification.query.filter(
                Notification.user_id == booking.provider.user_id,
                Notification.type == 'reminder',
                Notification.created_at >= now_indian - timedelta(hours=1),
                Notification.message.contains(f'Booking #{booking.id}')
            ).first()

            if not recent_reminder:
                # Send service reminder
                svc = booking.service.category if booking.service else 'Service'
                # Convert booking time to Indian time for display
                booking_indian = booking.booking_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Kolkata'))
                when_str = booking_indian.strftime('%Y-%m-%d ') + str(booking_indian.hour) + booking_indian.strftime(':%M %p')
                address = booking.address[:50] + '...' if len(booking.address) > 50 else booking.address

                reminder_notif = Notification(
                    user_id=booking.provider.user_id,
                    title=f'Service Reminder - Booking #{booking.id}',
                    message=f'You have a {svc} service scheduled for {when_str} at {address}. Please arrive 15 minutes early.',
                    type='reminder'
                )
                db.session.add(reminder_notif)

    # Commit all reminder notifications
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error sending service reminders: {e}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/verification_docs/<path:filename>')
@login_required
def serve_verification_file(filename):
    # Only admins and the owning provider should be able to access
    if current_user.role not in ['admin', 'provider']:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    # If provider, ensure the requested file belongs to them
    if current_user.role == 'provider':
        # Find provider profile
        provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
        if not provider:
            flash('Access denied!', 'error')
            return redirect(url_for('index'))
        # Verify the file belongs to this provider
        doc = VerificationDocument.query.filter_by(file_path=filename, provider_id=provider.id).first()
        if not doc:
            flash('Access denied!', 'error')
            return redirect(url_for('index'))
    upload_dir = os.path.join(app.root_path, 'uploads', 'verification_docs')
    return send_from_directory(upload_dir, filename, as_attachment=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        phone = request.form['phone']
        address = request.form['address']
        pincode = request.form['pincode']
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            phone=phone,
            address=address,
            pincode=pincode
        )
        db.session.add(user)
        db.session.commit()
        
        if role == 'provider':
            # Collect provider-specific fields
            service_categories = request.form.getlist('service_categories') or []
            # Normalize categories to CSV to match templates
            categories_csv = ','.join([c.strip() for c in service_categories if c.strip()])
            service_pincodes = request.form.get('service_pincodes', '')
            hourly_rate = float(request.form.get('hourly_rate', 0) or 0)
            experience_years = int(request.form.get('experience_years', 0) or 0)
            description = request.form.get('description', '')
            availability = request.form.get('availability', '')

            provider = ServiceProvider(
                user_id=user.id,
                service_categories=categories_csv,
                service_pincodes=service_pincodes,
                hourly_rate=hourly_rate,
                experience_years=experience_years,
                description=description,
                availability=availability,
                status='pending',
                verification_status='pending'
            )
            db.session.add(provider)
            db.session.commit()

            # Optional: handle initial verification document uploads during registration
            try:
                government_id = request.files.get('government_id')
                business_license = request.files.get('business_license')
                profile_photo = request.files.get('profile_photo')

                uploaded_any = False
                if government_id:
                    filename = save_verification_document(government_id, provider.id, 'government_id')
                    if filename:
                        db.session.add(VerificationDocument(provider_id=provider.id, document_type='government_id', file_path=filename))
                        uploaded_any = True
                if business_license:
                    filename = save_verification_document(business_license, provider.id, 'business_license')
                    if filename:
                        db.session.add(VerificationDocument(provider_id=provider.id, document_type='business_license', file_path=filename))
                        uploaded_any = True
                if profile_photo:
                    filename = save_verification_document(profile_photo, provider.id, 'profile_photo')
                    if filename:
                        db.session.add(VerificationDocument(provider_id=provider.id, document_type='profile_photo', file_path=filename))
                        uploaded_any = True

                if uploaded_any:
                    db.session.commit()
            except Exception:
                # Do not block registration on file upload issues
                db.session.rollback()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'provider':
                return redirect(url_for('provider_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    # Compute next availability for each booking's provider
    availability_info = {}
    for b in bookings:
        try:
            next_avail_dt = compute_next_available(b.provider.availability)
            availability_info[b.id] = next_avail_dt
        except Exception:
            availability_info[b.id] = None
    # Notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('user_dashboard.html', bookings=bookings, availability_info=availability_info, notifications=notifications)

@app.route('/provider/dashboard')
@login_required
def provider_dashboard():
    if current_user.role != 'provider':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('Provider profile not found!', 'error')
        return redirect(url_for('index'))
    
    bookings = Booking.query.filter_by(provider_id=provider.id).order_by(Booking.created_at.desc()).all()
    
    # Get verification status and documents
    verification_docs = VerificationDocument.query.filter_by(provider_id=provider.id).all()
    
    # Show verification status message
    if provider.verification_status == 'pending':
        flash('Your account is pending admin verification. Please upload your verification documents.', 'warning')
    elif provider.verification_status == 'rejected':
        flash('Your verification was rejected. Please contact admin or upload new documents.', 'error')
    elif provider.verification_status == 'verified':
        pass
    
    # Get upcoming bookings for reminders (next 24 hours)
    now_indian = get_indian_time()
    now_utc = get_utc_from_indian(now_indian)

    upcoming_bookings = Booking.query.filter(
        Booking.provider_id == provider.id,
        Booking.booking_date >= now_utc,
        Booking.booking_date <= now_utc + timedelta(hours=24),
        Booking.status.in_(['accepted', 'in_progress'])
    ).order_by(Booking.booking_date).all()

    # Send service reminders for upcoming bookings
    send_service_reminders(provider.id, upcoming_bookings)

    # Notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('provider_dashboard.html', 
                         provider=provider, 
                         bookings=bookings,
                         verification_docs=verification_docs,
                         notifications=notifications,
                         upcoming_bookings=upcoming_bookings)

@app.route('/provider/upload_verification')
@login_required
def upload_verification():
    if current_user.role != 'provider':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('Provider profile not found!', 'error')
        return redirect(url_for('index'))

    verification_docs = VerificationDocument.query.filter_by(provider_id=provider.id).all()
    return render_template('upload_verification.html', provider=provider, verification_docs=verification_docs)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    # Fetch real data from database
    # Providers pending verification review (includes re-applied ones)
    pending_providers = db.session.query(ServiceProvider, User).join(User).filter(
        ServiceProvider.verification_status == 'pending'
    ).all()

    pending_verifications = db.session.query(ServiceProvider, User).join(User).filter(
        ServiceProvider.verification_status == 'pending'
    ).all()

    # Get comprehensive statistics
    total_users = User.query.filter_by(role='user').count()
    total_providers = User.query.filter_by(role='provider').count()
    total_bookings = Booking.query.count()

    # Get booking statistics by status
    pending_bookings = Booking.query.filter_by(status='pending').count()
    in_progress_bookings = Booking.query.filter_by(status='in_progress').count()
    completed_bookings = Booking.query.filter_by(status='completed').count()
    cancelled_bookings = Booking.query.filter_by(status='cancelled').count()

    # Get recent activity for the activity feed
    recent_bookings = db.session.query(Booking, User, ServiceProvider).join(
        User, Booking.user_id == User.id
    ).join(
        ServiceProvider, Booking.provider_id == ServiceProvider.id
    ).order_by(Booking.id.desc()).limit(10).all()

    recent_users = User.query.order_by(User.id.desc()).limit(5).all()

    # Get recent notifications for activity feed
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(10).all()

    # Get recent reviews for activity feed
    recent_reviews = db.session.query(Review, User, ServiceProvider).join(
        User, Review.user_id == User.id
    ).join(
        ServiceProvider, Review.provider_id == ServiceProvider.id
    ).order_by(Review.id.desc()).limit(5).all()

    # Get verification statistics
    verified_providers = ServiceProvider.query.filter_by(verification_status='verified').count()
    rejected_providers = ServiceProvider.query.filter_by(verification_status='rejected').count()

    # Fetch rejected providers list (recent)
    rejected_list = db.session.query(ServiceProvider, User).join(User).\
        filter(ServiceProvider.verification_status == 'rejected').\
        order_by(ServiceProvider.id.desc()).limit(20).all()

    return render_template('admin_dashboard.html',
                         pending_providers=pending_providers,
                         pending_verifications=pending_verifications,
                         total_users=total_users,
                         total_providers=total_providers,
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         in_progress_bookings=in_progress_bookings,
                         completed_bookings=completed_bookings,
                         cancelled_bookings=cancelled_bookings,
                         recent_bookings=recent_bookings,
                         recent_users=recent_users,
                         recent_notifications=recent_notifications,
                         recent_reviews=recent_reviews,
                         verified_providers=verified_providers,
                         rejected_providers=rejected_providers,
                         rejected_list=rejected_list)

@app.route('/admin/pending_verifications')
@login_required
def admin_pending_verifications():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    pending_verifications = db.session.query(ServiceProvider, User).join(User).filter(
        ServiceProvider.verification_status == 'pending'
    ).all()

    return render_template('admin_verifications.html', pending_verifications=pending_verifications)

@app.route('/admin/manage_users')
@login_required
def admin_manage_users():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_manage_users.html', users=users)

@app.route('/admin/manage_providers')
@login_required
def admin_manage_providers():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    providers = db.session.query(ServiceProvider, User).join(User).all()
    return render_template('admin_manage_providers.html', providers=providers)

@app.route('/admin/provider_docs/<int:provider_id>')
@login_required
def admin_provider_docs(provider_id):
    """Return JSON list of verification documents for a provider (admin only)."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    provider = ServiceProvider.query.get_or_404(provider_id)
    docs = VerificationDocument.query.filter_by(provider_id=provider.id).order_by(VerificationDocument.uploaded_at.desc()).all()

    def doc_to_dict(doc):
        return {
            'id': doc.id,
            'document_type': doc.document_type,
            'status': doc.status,
            'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M') if getattr(doc, 'uploaded_at', None) else None,
            'url': url_for('serve_verification_file', filename=doc.file_path)
        }

    return jsonify({'provider_id': provider.id, 'documents': [doc_to_dict(d) for d in docs]})

@app.route('/admin/view_ratings')
@login_required
def admin_view_ratings():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    reviews = db.session.query(Review, User, ServiceProvider, Booking).join(
        User, Review.user_id == User.id
    ).join(
        ServiceProvider, Review.provider_id == ServiceProvider.id
    ).join(
        Booking, Review.booking_id == Booking.id
    ).order_by(Review.created_at.desc()).all()

    # Calculate average ratings
    avg_rating = db.session.query(db.func.avg(Review.rating)).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 0

    # Get rating distribution with percentages
    rating_counts = db.session.query(Review.rating, db.func.count(Review.id)).group_by(Review.rating).all()
    total_reviews = sum(count for _, count in rating_counts) if rating_counts else 0
    rating_distribution = []
    for rating, count in rating_counts:
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_distribution.append((rating, count, round(percentage, 1)))

    # Calculate positive reviews count (rating > 3)
    positive_reviews = Review.query.filter(Review.rating > 3).count()

    return render_template('admin_view_ratings.html',
                         reviews=reviews,
                         avg_rating=avg_rating,
                         rating_counts=rating_counts,
                         positive_reviews=positive_reviews)

@app.route('/admin/approve_provider', methods=['POST'])
@login_required
def approve_provider():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    provider_id = request.form.get('provider_id')
    action = request.form.get('action')
    
    provider = ServiceProvider.query.get_or_404(provider_id)
    
    if action == 'approve':
        provider.status = 'approved'
        # Notification to provider
        notif = Notification(
            user_id=provider.user_id,
            title='Provider Approved',
            message='Your service provider account has been approved by admin.',
            type='approved'
        )
        db.session.add(notif)
    elif action == 'reject':
        provider.status = 'rejected'
        reason = request.form.get('reason', '').strip()
        notif = Notification(
            user_id=provider.user_id,
            title='Provider Rejected',
            message=f'Your provider profile was rejected. {("Reason: " + reason) if reason else ""}',
            type='rejected'
        )
        db.session.add(notif)
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Provider profile update route
@app.route('/provider/update_profile', methods=['POST'])
@login_required
def update_provider_profile():
    if current_user.role != 'provider':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('Provider profile not found!', 'error')
        return redirect(url_for('provider_dashboard'))
    
    # Update provider profile
    service_categories = request.form.getlist('service_categories')
    provider.service_categories = ','.join([c.strip() for c in service_categories if c.strip()])
    provider.service_pincodes = request.form.get('service_pincodes', '')
    provider.hourly_rate = float(request.form.get('hourly_rate', 0))
    provider.experience_years = int(request.form.get('experience_years', 0))
    provider.description = request.form.get('description', '')
    provider.availability = request.form.get('availability', provider.availability or '')

    # Handle optional verification document uploads
    uploaded_any = False
    try:
        government_id = request.files.get('government_id')
        business_license = request.files.get('business_license')
        profile_photo = request.files.get('profile_photo')

        if government_id and getattr(government_id, 'filename', ''):
            filename = save_verification_document(government_id, provider.id, 'government_id')
            if filename:
                db.session.add(VerificationDocument(provider_id=provider.id, document_type='government_id', file_path=filename))
                uploaded_any = True

        if business_license and getattr(business_license, 'filename', ''):
            filename = save_verification_document(business_license, provider.id, 'business_license')
            if filename:
                db.session.add(VerificationDocument(provider_id=provider.id, document_type='business_license', file_path=filename))
                uploaded_any = True

        if profile_photo and getattr(profile_photo, 'filename', ''):
            filename = save_verification_document(profile_photo, provider.id, 'profile_photo')
            if filename:
                db.session.add(VerificationDocument(provider_id=provider.id, document_type='profile_photo', file_path=filename))
                uploaded_any = True
    except Exception as e:
        print(f"Error handling document uploads: {e}")

    # If any new document uploaded, reset verification to pending for re-review
    if uploaded_any:
        provider.verification_status = 'pending'

    db.session.commit()

    # Send notifications about profile update
    try:
        db.session.add(Notification(
            user_id=current_user.id,
            title='Profile Updated',
            message=f'Your service provider profile has been updated successfully.' + (' Verification documents uploaded. Awaiting admin review.' if uploaded_any else ''),
            type='profile'
        ))

        # Notify admin about profile changes
        admin = User.query.filter_by(role='admin').first()
        if admin:
            db.session.add(Notification(
                user_id=admin.id,
                title='Provider Profile Updated',
                message=f'Provider {current_user.name} has updated their profile information.' + (' New verification documents were uploaded and need review.' if uploaded_any else ''),
                type='system'
            ))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error sending profile update notifications: {e}")

    return redirect(url_for('provider_dashboard'))

@app.route('/search_providers')
def search_providers():
    pincode = request.args.get('pincode')
    category = request.args.get('category')

    query = db.session.query(ServiceProvider, User).join(User)

    if pincode:
        query = query.filter(ServiceProvider.service_pincodes.contains(pincode))
    if category:
        query = query.filter(ServiceProvider.service_categories.contains(category))

    # Always show only verified providers in search
    query = query.filter(ServiceProvider.verification_status == 'verified')

    # Execute the query and get results
    providers = query.all()

    # Render HTML template for search results
    return render_template('search_results.html', providers=providers)

@app.route('/book_service/<int:provider_id>', methods=['GET', 'POST'])
@login_required
@require_verified_provider
def book_service(provider_id):
    provider = ServiceProvider.query.get_or_404(provider_id)
    
    if request.method == 'POST':
        booking_date_str = request.form['booking_date']
        address = request.form['address']
        service_id = request.form.get('service_id')

        # Parse booking datetime as Indian time
        booking_date = parse_booking_datetime(booking_date_str)

        # Validate booking time is within allowed hours
        time_validation_error = validate_booking_time(booking_date)
        if time_validation_error:
            flash(time_validation_error, 'error')
            # Re-determine services for the error case
            all_services = Service.query.filter_by(is_active=True).all()
            if provider.service_categories and provider.service_categories.strip():
                try:
                    provider_services = [cat.strip().lower() for cat in provider.service_categories.split(',') if cat.strip()]
                    all_service_categories = [(s.category.strip().lower(), s) for s in all_services]
                    filtered_services = [s for cat, s in all_service_categories if cat in provider_services]
                    if filtered_services:
                        services = filtered_services
                    else:
                        partial_matches = []
                        for cat, s in all_service_categories:
                            if any(provider_cat in cat or cat in provider_cat for provider_cat in provider_services):
                                partial_matches.append(s)
                        services = partial_matches if partial_matches else []
                except:
                    services = all_services
            else:
                services = all_services
            return render_template('book_service.html', provider=provider, services=services)

        # Validate that we have a valid service_id
        if not service_id:
            flash('No service selected. Please choose a provider that offers available services.', 'error')
            # Re-determine services for the error case
            all_services = Service.query.filter_by(is_active=True).all()
            if provider.service_categories and provider.service_categories.strip():
                try:
                    provider_services = [cat.strip().lower() for cat in provider.service_categories.split(',') if cat.strip()]
                    all_service_categories = [(s.category.strip().lower(), s) for s in all_services]
                    filtered_services = [s for cat, s in all_service_categories if cat in provider_services]
                    if filtered_services:
                        services = filtered_services
                    else:
                        partial_matches = []
                        for cat, s in all_service_categories:
                            if any(provider_cat in cat or cat in provider_cat for provider_cat in provider_services):
                                partial_matches.append(s)
                        services = partial_matches if partial_matches else []
                except:
                    services = all_services
            else:
                services = all_services
            return render_template('book_service.html', provider=provider, services=services)

        # Check provider availability
        availability_conflict = check_provider_availability(provider.id, booking_date)
        if availability_conflict:
            flash(f'Provider is not available at the selected time. {availability_conflict}', 'error')
            # For error cases, we need to determine the appropriate services to show
            all_services = Service.query.filter_by(is_active=True).all()
            if provider.service_categories and provider.service_categories.strip():
                try:
                    # Use the same matching logic as the GET request
                    provider_services = [cat.strip().lower() for cat in provider.service_categories.split(',') if cat.strip()]
                    all_service_categories = [(s.category.strip().lower(), s) for s in all_services]

                    filtered_services = [s for cat, s in all_service_categories if cat in provider_services]
                    if filtered_services:
                        services = filtered_services
                    else:
                        # Try partial matches
                        partial_matches = []
                        for cat, s in all_service_categories:
                            if any(provider_cat in cat or cat in provider_cat for provider_cat in provider_services):
                                partial_matches.append(s)

                        services = partial_matches if partial_matches else []
                except:
                    services = all_services
            else:
                services = all_services
            return render_template('book_service.html', provider=provider, services=services)

        # Calculate total amount using provider's hourly rate
        service = Service.query.get(service_id)
        total_amount = provider.hourly_rate if service else 0.0

        # Convert to UTC for database storage
        booking_date_utc = get_utc_from_indian(booking_date)

        # Prevent user from double-booking at the same date/time
        existing_user_conflict = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.booking_date == booking_date_utc,
            Booking.status.in_(['pending', 'accepted', 'in_progress'])
        ).first()
        if existing_user_conflict:
            flash('You already have a booking at this date and time. Please choose a different time.', 'error')
            # Re-render with appropriate services like other error branches
            all_services = Service.query.filter_by(is_active=True).all()
            if provider.service_categories and provider.service_categories.strip():
                try:
                    provider_services = [cat.strip().lower() for cat in provider.service_categories.split(',') if cat.strip()]
                    all_service_categories = [(s.category.strip().lower(), s) for s in all_services]
                    filtered_services = [s for cat, s in all_service_categories if cat in provider_services]
                    if filtered_services:
                        services = filtered_services
                    else:
                        partial_matches = []
                        for cat, s in all_service_categories:
                            if any(provider_cat in cat or cat in provider_cat for provider_cat in provider_services):
                                partial_matches.append(s)
                        services = partial_matches if partial_matches else []
                except:
                    services = all_services
            else:
                services = all_services
            return render_template('book_service.html', provider=provider, services=services)

        booking = Booking(
            user_id=current_user.id,
            provider_id=provider.id,
            service_id=service_id,
            booking_date=booking_date_utc,
            address=address,
            total_amount=total_amount
        )
        db.session.add(booking)
        db.session.commit()
        # Notifications with booking details
        try:
            svc = service.category if service else 'Service'
            # Convert booking time back to Indian time for display
            booking_indian = booking_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Kolkata'))
            when_str = booking_indian.strftime('%Y-%m-%d ') + str(booking_indian.hour) + booking_indian.strftime(':%M %p')
            # Notify provider
            db.session.add(Notification(
                user_id=provider.user_id,
                title='New Booking',
                message=f'New booking (#{booking.id}) for {svc} on {when_str} at {address[:60]}',
                type='booking'
            ))
            # Notify user (confirmation)
            db.session.add(Notification(
                user_id=current_user.id,
                title='Booking Confirmed',
                message=f'Booking (#{booking.id}) with {provider.user.name} for {svc} on {when_str} created successfully.',
                type='booking'
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        return redirect(url_for('user_dashboard'))
    
    # Get services offered by this provider
    # First, get all active services
    all_services = Service.query.filter_by(is_active=True).all()

    if not all_services:
        flash('No services are currently available.', 'warning')
        return redirect(url_for('search_providers'))

    # Filter services to only include those the provider offers
    services = all_services  # Default to all services for compatibility

    if provider.service_categories and provider.service_categories.strip():
        try:
            # Parse provider's service categories (case-insensitive, trimmed)
            provider_services = [cat.strip().lower() for cat in provider.service_categories.split(',') if cat.strip()]
            all_service_categories = [(s.category.strip().lower(), s) for s in all_services]

            print(f"DEBUG: Provider services (normalized): {provider_services}")
            print(f"DEBUG: Available services (normalized): {[cat for cat, s in all_service_categories]}")

            if provider_services:
                # Filter services to only include those the provider offers (case-insensitive match)
                filtered_services = [s for cat, s in all_service_categories if cat in provider_services]

                # Only use filtered services if we found matching services
                if filtered_services:
                    services = filtered_services
                    print(f"DEBUG: Found {len(filtered_services)} matching services for provider {provider.id}")
                else:
                    print(f"DEBUG: No matching services found for provider {provider.id}")
                    print(f"DEBUG: Provider categories: {provider.service_categories}")
                    print(f"DEBUG: Available categories: {[s.category for s in all_services]}")

                    # If no exact matches, try to find partial matches or show error
                    partial_matches = []
                    for cat, s in all_service_categories:
                        if any(provider_cat in cat or cat in provider_cat for provider_cat in provider_services):
                            partial_matches.append(s)

                    if partial_matches:
                        services = partial_matches
                        print(f"DEBUG: Found {len(partial_matches)} partial matches")
                    else:
                        # Show error if no matches at all
                        flash(f'This provider offers services ({", ".join(provider_services)}) that are not currently available in our system.', 'warning')
                        services = []
        except Exception as e:
            print(f"DEBUG: Error processing service categories for provider {provider.id}: {e}")
            # If there's any error processing the service categories, fall back to all services
            services = all_services
    else:
        print(f"DEBUG: Provider {provider.id} has no service categories")
        services = all_services

    return render_template('book_service.html', provider=provider, services=services)

@app.route('/update_booking_status/<int:booking_id>', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form['status']
    
    if current_user.role == 'provider':
        provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
        if booking.provider_id != provider.id:
            flash('Access denied!', 'error')
            return redirect(url_for('provider_dashboard'))
    
    booking.status = new_status
    db.session.commit()

    # Send additional notifications for specific status changes
    try:
        svc = booking.service.category if getattr(booking, 'service', None) else 'Service'
        booking_indian = booking.booking_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Kolkata'))
        when_str = booking_indian.strftime('%Y-%m-%d ') + str(booking_indian.hour) + booking_indian.strftime(':%M %p') if booking.booking_date else ''
        status_title = booking.status.replace('_', ' ').title()

        # Additional notifications based on status
        if new_status == 'completed':
            # Notify user about service completion
            db.session.add(Notification(
                user_id=booking.user_id,
                title=f'Service Completed',
                message=f'Your {svc} service on {when_str} has been marked as completed. Thank you for using ServicePro!',
                type='completion'
            ))

        elif new_status == 'cancelled':
            # Notify about cancellation
            db.session.add(Notification(
                user_id=booking.user_id,
                title=f'Booking Cancelled',
                message=f'Your {svc} booking on {when_str} has been cancelled.',
                type='cancellation'
            ))

        elif new_status == 'in_progress':
            # Notify about service starting
            db.session.add(Notification(
                user_id=booking.user_id,
                title=f'Service Started',
                message=f'Your {svc} service on {when_str} is now in progress.',
                type='progress'
            ))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error sending additional status notifications: {e}")

    # Notifications with booking details on status update
    try:
        svc = booking.service.category if getattr(booking, 'service', None) else 'Service'
        # Convert booking time to Indian time for display
        booking_indian = booking.booking_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Kolkata'))
        when_str = booking_indian.strftime('%Y-%m-%d ') + str(booking_indian.hour) + booking_indian.strftime(':%M %p') if booking.booking_date else ''
        status_title = booking.status.replace('_', ' ').title()
        # To user
        db.session.add(Notification(
            user_id=booking.user_id,
            title=f'Booking #{booking.id} {status_title}',
            message=f'Your booking for {svc} on {when_str} is now {status_title}.',
            type='booking'
        ))
        # To provider
        db.session.add(Notification(
            user_id=ServiceProvider.query.get(booking.provider_id).user_id,
            title=f'Booking #{booking.id} {status_title}',
            message=f'Booking for {svc} on {when_str} is now {status_title}.',
            type='booking'
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    if current_user.role == 'provider':
        return redirect(url_for('provider_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

# Review system routes
@app.route('/add_review/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def add_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if current_user.id != booking.user_id:
        flash('Access denied!', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comments = request.form['comments']
        
        # Check if review already exists
        existing_review = Review.query.filter_by(booking_id=booking_id).first()
        if existing_review:
            flash('Review already exists for this booking!', 'error')
            return redirect(url_for('user_dashboard'))
        
        review = Review(
            booking_id=booking_id,
            user_id=current_user.id,
            provider_id=booking.provider_id,
            rating=rating,
            comments=comments
        )
        db.session.add(review)
        db.session.commit()

        # Send notifications about the review
        try:
            # Notify provider about new review
            provider_user_id = booking.provider.user_id
            db.session.add(Notification(
                user_id=provider_user_id,
                title=f'New Review Received',
                message=f'You received a {rating}-star review for booking #{booking_id}. Check your dashboard for details.',
                type='review'
            ))

            # Notify user that review was submitted
            db.session.add(Notification(
                user_id=current_user.id,
                title='Review Submitted',
                message=f'Your {rating}-star review for booking #{booking_id} has been submitted successfully.',
                type='review'
            ))

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error sending review notifications: {e}")

        return redirect(url_for('user_dashboard'))
    
    return render_template('add_review.html', booking=booking)

@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    return render_template('chat.html', other_user=other_user, messages=messages)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form['receiver_id']
    message_text = request.form['message']
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message_text
    )
    db.session.add(message)
    db.session.commit()
    # Create notification for receiver
    notif = Notification(
        user_id=receiver_id,
        title='New Message',
        message=message_text,
        type='message'
    )
    db.session.add(notif)
    db.session.commit()
    
    return jsonify({'status': 'success'})

# Verification API routes
@app.route('/provider/upload_verification_docs', methods=['POST'])
@login_required
def upload_verification_docs():
    if current_user.role != 'provider':
        return jsonify({'error': 'Access denied'}), 403

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        return jsonify({'error': 'Provider profile not found'}), 404

    # Handle file uploads
    government_id = request.files.get('government_id')
    business_license = request.files.get('business_license')
    profile_photo = request.files.get('profile_photo')

    uploaded_files = []

    if government_id:
        filename = save_verification_document(government_id, provider.id, 'government_id')
        if filename:
            doc = VerificationDocument(
                provider_id=provider.id,
                document_type='government_id',
                file_path=filename
            )
            db.session.add(doc)
            uploaded_files.append('government_id')

    if business_license:
        filename = save_verification_document(business_license, provider.id, 'business_license')
        if filename:
            doc = VerificationDocument(
                provider_id=provider.id,
                document_type='business_license',
                file_path=filename
            )
            db.session.add(doc)
            uploaded_files.append('business_license')

    if profile_photo:
        filename = save_verification_document(profile_photo, provider.id, 'profile_photo')
        if filename:
            doc = VerificationDocument(
                provider_id=provider.id,
                document_type='profile_photo',
                file_path=filename
            )
            db.session.add(doc)
            uploaded_files.append('profile_photo')

    if uploaded_files:
        db.session.commit()

        # Send notifications about document uploads
        try:
            # Notify provider about successful upload
            db.session.add(Notification(
                user_id=current_user.id,
                title='Documents Uploaded',
                message=f'Successfully uploaded {len(uploaded_files)} verification document(s).',
                type='document'
            ))

            # Notify admin about new document uploads
            admin = User.query.filter_by(role='admin').first()
            if admin:
                db.session.add(Notification(
                    user_id=admin.id,
                    title='New Documents Uploaded',
                    message=f'Provider {current_user.name} has uploaded {len(uploaded_files)} verification document(s) for review.',
                    type='system'
                ))

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error sending document upload notifications: {e}")

        return jsonify({'message': f'Successfully uploaded {len(uploaded_files)} document(s)', 'uploaded': uploaded_files}), 200

    return jsonify({'error': 'No valid files uploaded'}), 400

@app.route('/admin/providers/pending_verification')
@login_required
def get_pending_verifications():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    providers = db.session.query(ServiceProvider, User).join(User).filter(
        ServiceProvider.verification_status == 'pending'
    ).all()

    result = []
    for provider, user in providers:
        docs = VerificationDocument.query.filter_by(provider_id=provider.id).all()
        result.append({
            'provider_id': provider.id,
            'user_name': user.name,
            'user_email': user.email,
            'documents': [
                {
                    'id': doc.id,
                    'type': doc.document_type,
                    'status': doc.status,
                    'uploaded_at': doc.uploaded_at.isoformat()
                } for doc in docs
            ]
        })

    return jsonify(result)

@app.route('/admin/provider/verify/<int:provider_id>', methods=['PUT'])
@login_required
def verify_provider(provider_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    provider = ServiceProvider.query.get_or_404(provider_id)
    action = request.json.get('action')
    admin_notes = request.json.get('admin_notes', '')

    if action not in ['verify', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400

    # Update provider verification status
    provider.verification_status = 'verified' if action == 'verify' else 'rejected'
    db.session.commit()

    # Notify provider
    notif = Notification(
        user_id=provider.user_id,
        title='Verification ' + ('Approved' if action == 'verify' else 'Rejected'),
        message=(admin_notes or ''),
        type=('approved' if action == 'verify' else 'rejected')
    )
    db.session.add(notif)
    db.session.commit()

    # Update document statuses if provided
    document_ids = request.json.get('document_ids', [])
    if document_ids:
        docs = VerificationDocument.query.filter(
            VerificationDocument.id.in_(document_ids),
            VerificationDocument.provider_id == provider_id
        ).all()

        for doc in docs:
            doc.status = 'approved' if action == 'verify' else 'rejected'
            doc.admin_notes = admin_notes
        db.session.commit()

    return jsonify({
        'message': f'Provider {"verified" if action == "verify" else "rejected"} successfully',
        'provider_id': provider_id,
        'status': provider.verification_status
    })

@app.route('/bulk_verify_providers', methods=['POST'])
@login_required
def bulk_verify_providers():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    try:
        data = request.get_json()
        provider_ids = data.get('provider_ids', [])
        action = data.get('action')
        admin_notes = data.get('admin_notes', '')

        if not provider_ids:
            return jsonify({'error': 'No provider IDs provided'}), 400

        if action not in ['verify', 'reject']:
            return jsonify({'error': 'Invalid action'}), 400

        # Update all providers
        updated_count = 0
        for provider_id in provider_ids:
            try:
                provider = ServiceProvider.query.get(provider_id)
                if provider:
                    # Update provider verification status
                    provider.verification_status = 'verified' if action == 'verify' else 'rejected'

                    # Notify provider
                    notif = Notification(
                        user_id=provider.user_id,
                        title='Verification ' + ('Approved' if action == 'verify' else 'Rejected'),
                        message=(admin_notes or ''),
                        type=('approved' if action == 'verify' else 'rejected')
                    )
                    db.session.add(notif)
                    updated_count += 1

            except Exception as e:
                print(f"Error updating provider {provider_id}: {e}")
                continue

        # Update document statuses for verified/rejected providers
        if updated_count > 0:
            docs = VerificationDocument.query.filter(
                VerificationDocument.provider_id.in_(provider_ids)
            ).all()

            for doc in docs:
                doc.status = 'approved' if action == 'verify' else 'rejected'
                doc.admin_notes = admin_notes

        db.session.commit()

        return jsonify({
            'message': f'Successfully {action}ed {updated_count} provider(s)',
            'updated_count': updated_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Bulk action failed: {str(e)}'}), 500

@app.route('/provider/reapply', methods=['GET', 'POST'])
@login_required
def provider_reapply():
    if current_user.role != 'provider':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('Provider profile not found!', 'error')
        return redirect(url_for('index'))

    # Check if provider was rejected
    if provider.verification_status != 'rejected':
        flash('You can only reapply if your application was rejected.', 'warning')
        return redirect(url_for('provider_dashboard'))

    if request.method == 'POST':
        # Handle document uploads
        government_id = request.files.get('government_id')
        business_license = request.files.get('business_license')
        profile_photo = request.files.get('profile_photo')

        # Handle profile updates
        service_categories = request.form.getlist('service_categories')
        provider.service_categories = ','.join([c.strip() for c in service_categories if c.strip()])
        provider.service_pincodes = request.form.get('service_pincodes', '')
        provider.hourly_rate = float(request.form.get('hourly_rate', 0) or 0)
        provider.experience_years = int(request.form.get('experience_years', 0) or 0)
        provider.description = request.form.get('description', '')
        provider.availability = request.form.get('availability', '')

        # Reset verification status to pending
        provider.verification_status = 'pending'

        # Handle document uploads
        uploaded_any = False
        if government_id:
            filename = save_verification_document(government_id, provider.id, 'government_id')
            if filename:
                # Update existing or create new document
                existing_doc = VerificationDocument.query.filter_by(provider_id=provider.id, document_type='government_id').first()
                if existing_doc:
                    existing_doc.file_path = filename
                    existing_doc.status = 'pending'
                    existing_doc.admin_notes = None
                else:
                    db.session.add(VerificationDocument(provider_id=provider.id, document_type='government_id', file_path=filename))
                uploaded_any = True

        if business_license:
            filename = save_verification_document(business_license, provider.id, 'business_license')
            if filename:
                existing_doc = VerificationDocument.query.filter_by(provider_id=provider.id, document_type='business_license').first()
                if existing_doc:
                    existing_doc.file_path = filename
                    existing_doc.status = 'pending'
                    existing_doc.admin_notes = None
                else:
                    db.session.add(VerificationDocument(provider_id=provider.id, document_type='business_license', file_path=filename))
                uploaded_any = True

        if profile_photo:
            filename = save_verification_document(profile_photo, provider.id, 'profile_photo')
            if filename:
                existing_doc = VerificationDocument.query.filter_by(provider_id=provider.id, document_type='profile_photo').first()
                if existing_doc:
                    existing_doc.file_path = filename
                    existing_doc.status = 'pending'
                    existing_doc.admin_notes = None
                else:
                    db.session.add(VerificationDocument(provider_id=provider.id, document_type='profile_photo', file_path=filename))
                uploaded_any = True

        db.session.commit()

        # Notify admin about reapplication
        admin = User.query.filter_by(role='admin').first()
        if admin:
            notif = Notification(
                user_id=admin.id,
                title='Provider Reapplied',
                message=f'Provider {current_user.name} has reapplied for verification with updated documents.',
                type='system'
            )
            db.session.add(notif)
            db.session.commit()

        return redirect(url_for('provider_dashboard'))

    # Get existing documents for display
    verification_docs = VerificationDocument.query.filter_by(provider_id=provider.id).all()

    return render_template('provider_reapply.html', provider=provider, verification_docs=verification_docs)

@app.route('/provider/verification_status')
@login_required
def get_verification_status():
    if current_user.role != 'provider':
        return jsonify({'error': 'Access denied'}), 403

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        return jsonify({'error': 'Provider profile not found'}), 404

    docs = VerificationDocument.query.filter_by(provider_id=provider.id).all()

    return jsonify({
        'verification_status': provider.verification_status,
        'documents': [
            {
                'id': doc.id,
                'type': doc.document_type,
                'status': doc.status,
                'uploaded_at': doc.uploaded_at.isoformat()
            } for doc in docs
        ]
    })

# API Routes for Notifications
@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()

    result = []
    for notification in notifications:
        result.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat()
        })

    return jsonify(result)

@app.route('/api/notifications/unread_count')
@login_required
def get_unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@app.route('/api/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all current user's notifications as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    return jsonify({'status': 'ok'})

# WebSocket events
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'User has joined the room: {room}'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'User has left the room: {room}'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    emit('message', {'message': message, 'user': current_user.name}, room=room)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return render_template('405.html'), 405

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                name='Admin',
                email='admin@servicepro.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        
        # Create default services if not exists
        services = Service.query.all()
        if not services:
            default_services = [
                Service(category='Plumber', description='Plumbing services', base_price=500),
                Service(category='Electrician', description='Electrical services', base_price=400),
                Service(category='Cleaner', description='Cleaning services', base_price=300),
                Service(category='Carpenter', description='Carpentry services', base_price=450),
                Service(category='Painter', description='Painting services', base_price=350)
            ]
            for service in default_services:
                db.session.add(service)
            db.session.commit()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 