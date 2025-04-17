import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for, g, flash
from models import User

# JWT configuration
JWT_SECRET = os.environ.get('SESSION_SECRET', 'dev_secret_key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(days=1)

def generate_token(user_id, role):
    """Generate JWT token for a user"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('token')
        
        if not token:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        payload = decode_token(token)
        if 'error' in payload:
            flash('Session expired. Please log in again', 'warning')
            return redirect(url_for('auth.login'))
        
        g.user_id = payload['user_id']
        g.role = payload['role']
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user is an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('token')
        
        if not token:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        payload = decode_token(token)
        if 'error' in payload:
            flash('Session expired. Please log in again', 'warning')
            return redirect(url_for('auth.login'))
        
        if payload['role'] != 'admin':
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('user.leads'))
        
        g.user_id = payload['user_id']
        g.role = payload['role']
        
        return f(*args, **kwargs)
    return decorated_function
