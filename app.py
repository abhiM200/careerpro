import os
import json
import logging
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import razorpay

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'careerpro-secret-2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

from models.database import init_db, create_user, get_user_by_email, get_user_by_id

init_db()

# ================== ROUTES ==================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return "Dashboard Working ✅"


# ================== REGISTER ==================

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True) or request.form

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({'error': 'All fields required'}), 400

        if get_user_by_email(email):
            return jsonify({'error': 'Email already exists'}), 400

        user_id = create_user(name, email, generate_password_hash(password))

        session['user_id'] = user_id
        return jsonify({'success': True, 'redirect': '/dashboard'})

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify({'error': str(e)}), 500


# ================== LOGIN (FIXED) ==================

@app.route('/api/login', methods=['POST'])
def login():
    try:
        # 🔥 FIX — form + json dono handle
        data = request.get_json(silent=True)

        if not data:
            data = request.form

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email & Password required'}), 400

        user = get_user_by_email(email)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Wrong password'}), 401

        session['user_id'] = user['id']

        return jsonify({'success': True, 'redirect': '/dashboard'})

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({'error': str(e)}), 500


# ================== LOGOUT ==================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ================== RUN ==================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
