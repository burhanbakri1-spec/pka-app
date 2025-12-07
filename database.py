import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from datetime import datetime, timedelta

# رابط الاتصال (تأكد من صحته)
DB_URI = "postgresql://postgres.oemxebsztjydpfeoleya:imkanWB123@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

def get_connection():
    try:
        return psycopg2.connect(DB_URI)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # جدول الأندية
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS clubs (
                        id SERIAL PRIMARY KEY,
                        club_membership_id TEXT, name TEXT, representative_name TEXT,
                        address TEXT, email TEXT, phone TEXT, classification TEXT,
                        points INTEGER DEFAULT 0, affiliation_date TEXT,
                        subscription_expiry_date TEXT, representative_gender TEXT,
                        club_subscription_fee REAL, admin_subscription_fee REAL,
                        attachments_data TEXT
                    );
                ''')
                
                # جدول الأعضاء
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS members (
                        id SERIAL PRIMARY KEY,
                        pkf_id TEXT UNIQUE, full_name TEXT, full_name_ar TEXT,
                        id_number TEXT, role TEXT, dob TEXT, gender TEXT,
                        phone TEXT, email TEXT, photo_path TEXT,
                        club_id INTEGER REFERENCES clubs(id) ON DELETE SET NULL,
                        club_name TEXT, 
                        weight TEXT, discipline TEXT, current_belt TEXT,
                        belt_rank TEXT, belt_date TEXT,
                        rank_local TEXT, rank_intl TEXT,
                        degree_level TEXT, license_date TEXT, job_title TEXT,
                        expiry_date TEXT, passport_number TEXT, passport_expiry_date TEXT,
                        specific_data TEXT, notes TEXT, admin_title TEXT
                    );
                ''')
                conn.commit()
        finally:
            conn.close()

# --- دوال الإضافة والتعديل ---
def add_member(data):
    conn = get_connection()
    if not conn: return False, "No connection"
    try:
        with conn.cursor() as cur:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ["%s"] * len(values)
            sql = f"INSERT INTO members ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cur.execute(sql, values)
            conn.commit()
            return True, "Added successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_member(pkf_id, data):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
            values = list(data.values())
            values.append(pkf_id)
            sql = f"UPDATE members SET {set_clause} WHERE pkf_id = %s"
            cur.execute(sql, values)
            conn.commit()
            return True
    except Exception as e:
        return False
    finally:
        conn.close()

def delete_member(pkf_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM members WHERE pkf_id = %s", (pkf_id,))
            conn.commit()
    finally:
        conn.close()

def add_club(data):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ["%s"] * len(values)
            sql = f"INSERT INTO clubs ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cur.execute(sql, values)
            conn.commit()
            return True
    except Exception as e:
        return False
    finally:
        conn.close()

# --- دوال البحث المتقدم ---
def search_members_advanced(**kwargs):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql = "SELECT * FROM members WHERE 1=1"
            params = []
            
            if kwargs.get('query'):
                sql += " AND (full_name ILIKE %s OR full_name_ar ILIKE %s OR pkf_id ILIKE %s)"
                q = f"%{kwargs['query']}%"
                params.extend([q, q, q])
            
            if kwargs.get('role') and kwargs['role'] != "All Roles":
                sql += " AND role = %s"
                params.append(kwargs['role'])
                
            if kwargs.get('club') and kwargs['club'] != "All Clubs":
                sql += " AND club_name = %s"
                params.append(kwargs['club'])

            # يمكن إضافة المزيد من الفلاتر هنا (الحزام، المهنة، التواريخ)
            
            sql += " ORDER BY id DESC LIMIT 100"
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_all_clubs():
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM clubs ORDER BY name ASC")
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_unique_clubs():
    clubs = get_all_clubs()
    return [c['name'] for c in clubs]

# --- دوال التنبيهات (Alerts) ---
def get_expiring_members(days):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # PostgreSQL logic for date comparison
            # نفترض أن التواريخ مخزنة كنص YYYY-MM-DD
            target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            sql = """
                SELECT * FROM members 
                WHERE expiry_date IS NOT NULL 
                AND expiry_date != ''
                AND expiry_date <= %s 
                AND expiry_date >= %s
                ORDER BY expiry_date ASC
            """
            cur.execute(sql, (target_date, current_date))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_expiring_passports(days):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            sql = """
                SELECT * FROM members 
                WHERE passport_expiry_date IS NOT NULL 
                AND passport_expiry_date != ''
                AND passport_expiry_date <= %s 
                AND passport_expiry_date >= %s
                ORDER BY passport_expiry_date ASC
            """
            cur.execute(sql, (target_date, current_date))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
