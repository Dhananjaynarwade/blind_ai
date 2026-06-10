from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import pyotp
import os
import secrets
import json
from datetime import datetime, timedelta
from config import Config

# Load email config from json if exists
if os.path.exists('email_config.json'):
    try:
        with open('email_config.json', 'r') as f:
            email_config = json.load(f)
            os.environ['MAIL_USERNAME'] = email_config.get('MAIL_USERNAME', '')
            os.environ['MAIL_PASSWORD'] = email_config.get('MAIL_PASSWORD', '')
            if not email_config.get('TESTING', True):
                os.environ['TESTING'] = 'False'
    except Exception as e:
        print(f"Error loading email configuration: {e}")

# Configure Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp_secret = db.Column(db.String(32), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_otp(self):
        self.otp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(self.otp_secret, interval=300)  # 5 minute interval
        self.otp_expiry = datetime.now() + timedelta(minutes=5)
        return totp.now()
    
    def verify_otp(self, otp):
        if datetime.now() > self.otp_expiry:
            return False
        totp = pyotp.TOTP(self.otp_secret, interval=300)
        return totp.verify(otp)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def send_verification_email(user, otp):
    msg = Message('Email Verification OTP', recipients=[user.email])
    msg.body = f'''Hello {user.username},

Thank you for registering with our Flask Auth System.

Your OTP for email verification is: {otp}

This OTP is valid for 5 minutes.

If you did not register for our service, please ignore this email.

Best regards,
Flask Auth Team
'''
    if app.config['TESTING']:
        # For testing, print the email content instead of sending
        print(f"\n---------- EMAIL TO: {user.email} ----------")
        print(f"Subject: {msg.subject}")
        print(f"Body: {msg.body}")
        print("-------------------------------------------\n")
        return True
    else:
        # In production, actually send the email
        mail.send(msg)
        return True

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would implement email sending functionality
        # For now we'll just flash a message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                flash('Username already exists. Please choose a different one.', 'danger')
            else:
                flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        # Generate OTP
        otp = new_user.generate_otp()
        
        db.session.add(new_user)
        db.session.commit()
        
        # Send verification email
        try:
            send_verification_email(new_user, otp)
            if app.config['TESTING']:
                flash(f'Registration successful! For testing purposes, your OTP is: {otp}', 'success')
            else:
                flash('Registration successful! Please check your email for OTP to verify your account.', 'success')
            # Store user ID in session for verification page
            session['user_id_for_verification'] = new_user.id
            return redirect(url_for('verify_email'))
        except Exception as e:
            db.session.delete(new_user)
            db.session.commit()
            flash(f'Failed to send verification email. Please try again. Error: {str(e)}', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user_id = session.get('user_id_for_verification')
    if not user_id:
        flash('Invalid session. Please register again.', 'danger')
        return redirect(url_for('register'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please register again.', 'danger')
        session.pop('user_id_for_verification', None)
        return redirect(url_for('register'))
    
    # Get the current OTP for testing purposes
    current_otp = None
    if app.config['TESTING']:
        totp = pyotp.TOTP(user.otp_secret, interval=300)
        current_otp = totp.now()
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        if user.verify_otp(otp):
            user.is_verified = True
            db.session.commit()
            session.pop('user_id_for_verification', None)
            flash('Email verified successfully! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('verify_email.html', email=user.email, testing_otp=current_otp)

@app.route('/resend-otp', methods=['GET'])
def resend_otp():
    user_id = session.get('user_id_for_verification')
    if not user_id:
        flash('Invalid session. Please register again.', 'danger')
        return redirect(url_for('register'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please register again.', 'danger')
        session.pop('user_id_for_verification', None)
        return redirect(url_for('register'))
    
    # Generate new OTP
    otp = user.generate_otp()
    db.session.commit()
    
    # Send verification email
    try:
        send_verification_email(user, otp)
        if app.config['TESTING']:
            flash(f'OTP resent successfully! For testing purposes, your OTP is: {otp}', 'success')
        else:
            flash('OTP resent successfully! Please check your email.', 'success')
    except Exception as e:
        flash(f'Failed to resend OTP. Please try again. Error: {str(e)}', 'danger')
    
    return redirect(url_for('verify_email'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with this email. Please register first.', 'danger')
            return redirect(url_for('login'))
        
        if not user.is_verified:
            flash('Your email is not verified. Please verify your email first.', 'danger')
            # Store user ID in session for verification page
            session['user_id_for_verification'] = user.id
            # Generate new OTP
            otp = user.generate_otp()
            db.session.commit()
            # Send verification email
            try:
                send_verification_email(user, otp)
                flash('Verification email sent. Please check your email for OTP.', 'info')
            except Exception as e:
                flash(f'Failed to send verification email. Error: {str(e)}', 'danger')
            return redirect(url_for('verify_email'))
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'danger')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/object-detection')
@login_required
def object_detection():
    return render_template('camera.html')

@app.route('/navigation-assistance')
@login_required
def navigation_assistance():
    return render_template('navigation.html')

@app.route('/camera')
@login_required
def camera():
    return render_template('camera.html')

@app.route('/color-detection')
@login_required
def color_detection():
    return render_template('color_detection.html')

@app.route('/mobile-test')
def mobile_test():
    return render_template('mobile_friendly.html')

@app.route('/storytelling')
@login_required
def storytelling():
    return render_template('storytelling.html')

@app.route('/api/navigation/start', methods=['POST'])
@login_required
def start_navigation():
    data = request.get_json()
    goal_type = data.get('goal_type', 'exit')
    params = data.get('params', {})
    
    try:
        from services.navigation_service import navigation_service
        success, message = navigation_service.start_navigation(goal_type, params)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error starting navigation: {str(e)}"})

@app.route('/api/navigation/stop', methods=['POST'])
@login_required
def stop_navigation():
    try:
        from services.navigation_service import navigation_service
        success, message = navigation_service.stop_navigation()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error stopping navigation: {str(e)}"})

@app.route('/api/navigation/status', methods=['GET'])
@login_required
def navigation_status():
    try:
        from services.navigation_service import navigation_service
        guidance = navigation_service.get_current_guidance()
        return jsonify({'success': True, 'guidance': guidance})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error getting navigation status: {str(e)}"})

@app.route('/api/navigation/voice', methods=['POST'])
@login_required
def toggle_voice():
    data = request.get_json()
    enabled = data.get('enabled')
    
    try:
        from services.navigation_service import navigation_service
        voice_enabled = navigation_service.toggle_voice(enabled)
        return jsonify({'success': True, 'voice_enabled': voice_enabled})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error toggling voice: {str(e)}"})

@app.route('/api/navigation/update_objects', methods=['POST'])
@login_required
def update_detected_objects():
    data = request.get_json()
    objects = data.get('objects', [])
    
    try:
        from services.navigation_service import navigation_service
        navigation_service.update_detected_objects(objects)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error updating objects: {str(e)}"})

@app.route('/api/navigation/process_voice', methods=['POST'])
@login_required
def process_voice_command():
    data = request.get_json()
    voice_input = data.get('voice_input', '')
    
    try:
        from services.navigation_service import navigation_service
        result = navigation_service.process_voice_command(voice_input, user_id=current_user.id)
        
        # Extract message from result
        message = result.get('message', 'Command processed')
        if 'action_result' in result and 'message' in result['action_result']:
            message = result['action_result']['message']
        
        return jsonify({
            'success': result.get('success', False),
            'message': message,
            'command_type': result.get('command_type'),
            'action': result.get('action')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error processing voice command: {str(e)}"})

if __name__ == '__main__':
    # Create database and tables if they don't exist
    with app.app_context():
        if not os.path.exists('instance/users.db'):
            db.create_all()
    
    # Check if running with HTTPS is requested
    use_https = os.environ.get('USE_HTTPS', 'False').lower() == 'true'
    
    if use_https:
        try:
            # Run with HTTPS using a self-signed certificate
            # Note: requires 'pip install pyopenssl' for the adhoc SSL context
            print("Starting server with HTTPS (self-signed certificate)...")
            app.run(debug=True, host='0.0.0.0', ssl_context='adhoc')
        except Exception as e:
            print(f"Error starting with HTTPS: {e}")
            print("Install pyOpenSSL with: pip install pyopenssl")
            print("Falling back to HTTP (not secure, camera may not work)...")
            app.run(debug=True, host='0.0.0.0')
    else:
        # Run with HTTP (default)
        print("Starting server with HTTP. For camera access, use localhost or set USE_HTTPS=True")
        print("To enable HTTPS, run with: SET USE_HTTPS=True (Windows) or export USE_HTTPS=True (Linux/Mac)")
        app.run(debug=True, host='0.0.0.0') 