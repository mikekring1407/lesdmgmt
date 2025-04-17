from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app import db
from models import User
from auth import generate_token, decode_token, login_required
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.before_request
def load_user():
    if session.get('token'):
        payload = decode_token(session['token'])
        if 'error' not in payload:
            g.user_id = payload['user_id']
            g.role = payload['role']
            # Get the username for the logged-in user
            user = User.query.get(payload['user_id'])
            if user:
                g.username = user.username

@auth_bp.route('/')
def index():
    """Redirect to login page or dashboard based on login status"""
    if session.get('token'):
        # Check token validity
        payload = decode_token(session['token'])
        if 'error' not in payload:
            # Valid token, redirect based on role
            if payload['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.leads'))
    
    # No token or invalid token, redirect to login
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        # Generate token and store in session
        token = generate_token(user.id, user.role)
        session['token'] = token
        
        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.leads'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.pop('token', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new user (admin only)"""
    # Check if user is admin
    if g.role != 'admin':
        flash('You do not have permission to register new users', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if not username or not email or not password:
            flash('Please fill all required fields', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            role=role
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
    
    return render_template('register.html')
