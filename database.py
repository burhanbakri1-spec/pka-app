import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

# ---------------------------------------------------------
#  إعدادات الاتصال (Supabase)
# ---------------------------------------------------------

# ضع الرابط الذي نسخته هنا بين علامتي التنصيص
# مثال: "postgresql://postgres.user:pass@host:port/postgres"
DB_URI = "postgresql://postgres.oemxebsztjydpfeoleya:imkanWB123@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

def get_connection():
    """إنشاء اتصال جديد بقاعدة البيانات"""
    try:
        conn = psycopg2.connect(DB_URI)
        return conn
    except Exception as e:
        st.error(f"فشل الاتصال بقاعدة البيانات: {e}")
        return None

def init_db():
    """إنشاء جدول الأعضاء إذا لم يكن موجوداً"""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # ملاحظة: في PostgreSQL نستخدم SERIAL بدلاً من AUTOINCREMENT
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS members (
                        id SERIAL PRIMARY KEY,
                        full_name TEXT NOT NULL,
                        full_name_en TEXT,
                        pkf_id TEXT UNIQUE,
                        role TEXT NOT NULL,
                        dob TEXT,
                        club_name TEXT,
                        photo_path TEXT,
                        
                        weight TEXT,
                        discipline TEXT,
                        belt_rank TEXT,
                        
                        rank_local TEXT,
                        rank_intl TEXT,
                        belt_date TEXT,
                        
                        degree_level TEXT,
                        license_date TEXT,
                        job_title TEXT
                    );
                ''')
                conn.commit()
                print("✅ Database initialized successfully (Supabase).")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
        finally:
            conn.close()

def add_member(data):
    """إضافة عضو جديد"""
    conn = get_connection()
    if not conn:
        return False, "فشل الاتصال بالسيرفر"
    
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO members (
                    full_name, full_name_en, pkf_id, role, dob, club_name, photo_path,
                    weight, discipline, belt_rank, 
                    rank_local, rank_intl, belt_date,
                    degree_level, license_date, job_title
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                data.get('full_name'), data.get('full_name_en'), data.get('pkf_id'), data.get('role'), data.get('dob'),
                data.get('club_name'), data.get('photo_path'), 
                data.get('weight'), data.get('discipline'), data.get('belt_rank'), 
                data.get('rank_local'), data.get('rank_intl'), data.get('belt_date'),
                data.get('degree_level'), data.get('license_date'), data.get('job_title')
            ))
            conn.commit()
            return True, "تمت الإضافة بنجاح"
    except psycopg2.IntegrityError:
        return False, "رقم العضوية (PKF ID) موجود مسبقاً!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def search_members(query=""):
    """البحث عن الأعضاء"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        # RealDictCursor يرجع النتائج كقاموس (مثل SQLite Row)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if query:
                # البحث بالاسم أو الرقم
                cur.execute("SELECT * FROM members WHERE full_name ILIKE %s OR pkf_id ILIKE %s LIMIT 50", (f'%{query}%', f'%{query}%'))
            else:
                # عرض آخر 20 مضافاً
                cur.execute("SELECT * FROM members ORDER BY id DESC LIMIT 20")
            
            rows = cur.fetchall()
            # تحويل RealDictRow إلى dict عادي لتجنب مشاكل التوافق
            return [dict(row) for row in rows]
    except Exception as e:
        st.error(f"خطأ في البحث: {e}")
        return []
    finally:
        conn.close()