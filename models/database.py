"""
Database models for CareerPro SaaS Platform
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'careerpro.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_paid INTEGER DEFAULT 0,
        payment_id TEXT,
        order_id TEXT,
        paid_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT,
        candidate_name TEXT,
        ats_score REAL,
        ats_tier TEXT,
        skills_count INTEGER,
        top_job_match TEXT,
        full_analysis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

def create_user(name, email, password_hash):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)', (name, email, password_hash))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_payment_status(user_id, payment_id, order_id):
    conn = get_connection()
    conn.execute('UPDATE users SET is_paid=1, payment_id=?, order_id=?, paid_at=? WHERE id=?',
                 (payment_id, order_id, datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def save_analysis(user_id, filename, analysis):
    conn = get_connection()
    c = conn.cursor()
    parsed = analysis.get('parsed_resume', {})
    ats = analysis.get('ats_score', {})
    jobs = analysis.get('job_matches', [])
    c.execute('''INSERT INTO analyses (user_id, filename, candidate_name, ats_score, ats_tier, skills_count, top_job_match, full_analysis)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, filename, parsed.get('name', 'Unknown'), ats.get('total_score', 0),
               ats.get('tier', 'N/A'), len(parsed.get('skills', [])),
               jobs[0]['title'] if jobs else None, json.dumps(analysis)))
    record_id = c.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_user_analyses(user_id, limit=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM analyses WHERE user_id=? ORDER BY created_at DESC LIMIT ?', (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, email, is_paid, paid_at, created_at FROM users ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_analyses(limit=50):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT a.*, u.name as user_name, u.email as user_email
                 FROM analyses a JOIN users u ON a.user_id = u.id
                 ORDER BY a.created_at DESC LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
