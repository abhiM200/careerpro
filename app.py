"""
CareerPro - AI-Powered Career Acceleration Platform
Full Stack Flask Application with Login, Payment & AI Analysis
Developed by: Abhishek Kumar Mishra
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import razorpay

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'careerpro-secret-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Razorpay
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
PLAN_PRICE = int(os.getenv('PLAN_PRICE', '49900'))  # Rs 499 in paise
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@careerpro.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin@CareerPro2024')

from models.database import init_db, create_user, get_user_by_email, save_analysis, get_user_analyses, get_all_users, get_all_analyses, update_payment_status, get_user_by_id
from utils.file_extractor import extract_text
from utils.resume_parser import parse_resume
from utils.ats_scorer import calculate_ats_score
from utils.ai_suggestions import generate_suggestions
from utils.job_matcher import match_jobs

try:
    init_db()
    logger.info("CareerPro started successfully")
except Exception as e:
    logger.error(f"DB init failed: {e}")


# ─── Decorators ───────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

def payment_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        # BYPASS PAYMENT FOR TESTING
        bypass = os.getenv('BYPASS_PAYMENT', 'false').lower() == 'true'
        if bypass:
            return f(*args, **kwargs)
        user = get_user_by_id(session['user_id'])
        if not user or not user.get('is_paid'):
            return redirect(url_for('pricing_page'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Pages ────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/pricing')
def pricing_page():
    return render_template('pricing.html', razorpay_key=RAZORPAY_KEY_ID, price=PLAN_PRICE)

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_user_by_id(session['user_id'])
    analyses = get_user_analyses(session['user_id'], limit=10)
    return render_template('dashboard.html', user=user, analyses=analyses)

@app.route('/analyze-page')
@payment_required
def analyze_page():
    user = get_user_by_id(session['user_id'])
    return render_template('analyze.html', user=user)


# ─── Auth APIs ────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not all([name, email, password]):
            return jsonify({'error': 'All fields required'}), 400
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'Invalid email'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if get_user_by_email(email):
            return jsonify({'error': 'Email already registered'}), 409

        user_id = create_user(name, email, generate_password_hash(password))
        session.permanent = True
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        return jsonify({'success': True, 'redirect': '/pricing'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = get_user_by_email(email)
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        session.permanent = True
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        if user.get('is_paid'):
            return jsonify({'success': True, 'redirect': '/dashboard'})
        return jsonify({'success': True, 'redirect': '/pricing'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ─── Payment APIs ─────────────────────────────────────────
@app.route('/api/create-order', methods=['POST'])
@login_required
def create_order():
    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order = client.order.create({
            'amount': PLAN_PRICE,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {'user_id': str(session['user_id']), 'email': session.get('user_email')}
        })
        return jsonify({'order_id': order['id'], 'amount': PLAN_PRICE, 'currency': 'INR'})
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        return jsonify({'error': 'Payment initiation failed'}), 500

@app.route('/api/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    try:
        data = request.get_json()
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        update_payment_status(session['user_id'], data['razorpay_payment_id'], data['razorpay_order_id'])
        return jsonify({'success': True, 'redirect': '/dashboard'})
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        return jsonify({'error': 'Payment verification failed'}), 400


# ─── Analysis API ─────────────────────────────────────────
@app.route('/api/analyze', methods=['POST'])
@payment_required
def analyze():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume uploaded'}), 400
        file = request.files['resume']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF/DOCX allowed'}), 400

        jd = request.form.get('job_description', 'software engineer python developer')
        linkedin_url = request.form.get('linkedin_url', '')

        filename = secure_filename(file.filename)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{ts}_{filename}")
        file.save(filepath)

        text = extract_text(filepath)
        if not text or len(text.strip()) < 50:
            os.remove(filepath)
            return jsonify({'error': 'Could not extract text from file'}), 422

        parsed = parse_resume(text)
        ats = calculate_ats_score(text, jd, parsed.get('contact', {}))
        jobs = match_jobs(parsed.get('skills', []), top_n=5)
        suggestions = generate_suggestions(text, parsed.get('skills', []), ats.get('total_score', 0), ats.get('missing_keywords', []))

        linkedin_feedback = None
        if linkedin_url:
            linkedin_feedback = generate_linkedin_feedback(linkedin_url, parsed)

        analysis = {
            'filename': filename,
            'parsed_resume': parsed,
            'ats_score': ats,
            'job_matches': jobs,
            'suggestions': suggestions,
            'linkedin_feedback': linkedin_feedback,
            'analyzed_at': datetime.now().isoformat()
        }

        record_id = save_analysis(session['user_id'], filename, analysis)
        analysis['record_id'] = record_id

        try:
            os.remove(filepath)
        except Exception:
            pass

        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def generate_linkedin_feedback(url, parsed):
    skills = parsed.get('skills', [])
    name = parsed.get('name', 'Professional')
    return {
        'profile_url': url,
        'tips': [
            {'icon': '📸', 'title': 'Professional Photo', 'detail': 'Use a high-quality headshot with neutral background. Profiles with photos get 21x more views.', 'priority': 'High'},
            {'icon': '✍️', 'title': 'Compelling Headline', 'detail': f'Go beyond job title. Try: "{name} | {skills[0].title() if skills else "Professional"} | Helping companies grow"', 'priority': 'High'},
            {'icon': '📝', 'title': 'About Section', 'detail': 'Write 3-5 paragraphs about your journey, skills, and what you bring. Use keywords recruiters search for.', 'priority': 'High'},
            {'icon': '🎯', 'title': 'Skills Section', 'detail': f'Add all {len(skills)} detected skills. Get endorsements from colleagues for top skills.', 'priority': 'Medium'},
            {'icon': '🏆', 'title': 'Achievements', 'detail': 'Quantify results: "Increased sales by 40%" beats "Responsible for sales". Add numbers everywhere.', 'priority': 'Medium'},
            {'icon': '🔗', 'title': 'Custom URL', 'detail': 'Set linkedin.com/in/yourname — looks professional on resume and emails.', 'priority': 'Low'},
        ],
        'score': min(95, 60 + len(skills) * 2),
        'summary': f'Your LinkedIn profile can be significantly improved. Focus on headline and about section first.'
    }


# ─── Admin ────────────────────────────────────────────────
@app.route('/admin')
def admin_login_page():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('email') == ADMIN_EMAIL and data.get('password') == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login_page'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = get_all_users()
    analyses = get_all_analyses(limit=50)
    total_revenue = sum(1 for u in users if u.get('is_paid')) * (PLAN_PRICE / 100)
    return render_template('admin_dashboard.html', users=users, analyses=analyses, total_revenue=total_revenue)


# ─── Health ───────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'app': 'CareerPro'})

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Max 16MB.'}), 413

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
