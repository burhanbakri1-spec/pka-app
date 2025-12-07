import streamlit as st
import database
import os
import json
import pandas as pd
from card_generator import generate_member_card
from doc_generator import generate_bilingual_profile_doc
from bilingual_labels import *

# إعداد الصفحة
st.set_page_config(page_title="PKF Portal", layout="wide", page_icon="🥋")

# التأكد من مجلدات الأصول
os.makedirs("assets/member_files", exist_ok=True)
os.makedirs("output", exist_ok=True)

# تهيئة قاعدة البيانات
if "db_initialized" not in st.session_state:
    database.init_db()
    st.session_state["db_initialized"] = True

# --- القائمة الجانبية ---
with st.sidebar:
    st.title("لوحة التحكم 🥋")
    menu = st.radio("القائمة:", [
        "الرئيسية", 
        "إدارة الأعضاء", 
        "إدارة الأندية", 
        "التقارير والطباعة", 
        "التنبيهات"
    ])
    st.markdown("---")
    st.info("نظام الاتحاد الفلسطيني للكاراتيه")

# ==========================================
# 1. الرئيسية (Dashboard)
# ==========================================
if menu == "الرئيسية":
    st.title("🏠 لوحة المعلومات")
    
    # إحصائيات سريعة
    all_members = database.search_members("")
    all_clubs = database.get_all_clubs()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("عدد الأعضاء", len(all_members))
    col2.metric("عدد الأندية", len(all_clubs))
    col3.metric("اللاعبين المسجلين", len([m for m in all_members if m['role'] == 'Player']))

# ==========================================
# 2. إدارة الأعضاء (إضافة وتعديل)
# ==========================================
elif menu == "إدارة الأعضاء":
    st.title("👤 تسجيل الأعضاء")
    
    # جلب قائمة الأندية
    clubs_list = {c['name']: c['id'] for c in database.get_all_clubs()}
    
    with st.form("member_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name_ar = st.text_input("الاسم الكامل (عربي)*")
            pkf_id = st.text_input("رقم العضوية (PKF ID)*")
            id_number = st.text_input("رقم الهوية")
            role = st.selectbox("الدور", ["Player", "Coach", "Referee", "Admin"])
            dob = st.date_input("تاريخ الميلاد")
            
        with col2:
            name_en = st.text_input("الاسم الكامل (إنجليزي)")
            club_name = st.selectbox("النادي", [""] + list(clubs_list.keys()))
            gender = st.selectbox("الجنس", ["Male", "Female"])
            photo = st.file_uploader("الصورة الشخصية", type=['jpg', 'png'])
            
        st.markdown("---")
        st.subheader("تفاصيل إضافية")
        
        # حقول متغيرة حسب الدور
        specific_data = {}
        
        if role == "Player":
            c1, c2, c3 = st.columns(3)
            weight = c1.text_input("الوزن (كغ)")
            belt = c2.text_input("الحزام الحالي")
            belt_date = c3.date_input("تاريخ الحزام")
            
            st.write("الفئات:")
            kc = st.checkbox("كاتا")
            ku = st.checkbox("كوميتيه")
            
            specific_data = {
                "weight": weight, "kata_check": kc, "kumite_check": ku,
                "nat_rank": st.text_input("التصنيف الوطني"),
                "int_rank": st.text_input("التصنيف الدولي")
            }
            
        elif role == "Coach":
            col_a, col_b = st.columns(2)
            specific_data['coach_national_degree'] = col_a.text_input("درجة التدريب الوطنية")
            specific_data['coach_asian_degree'] = col_b.text_input("درجة التدريب الآسيوية")
            
        elif role == "Referee":
            col_a, col_b = st.columns(2)
            specific_data['ref_kumite_rb'] = col_a.text_input("درجة تحكيم (كوميتيه)")
            specific_data['ref_kata_ja'] = col_b.text_input("درجة تحكيم (كاتا)")
            
        elif role == "Admin":
            specific_data['admin_title'] = st.text_input("المسمى الوظيفي")

        expiry_date = st.date_input("تاريخ انتهاء الاشتراك")
        
        submitted = st.form_submit_button("💾 حفظ العضو")
        
        if submitted:
            if not name_ar or not pkf_id:
                st.error("الاسم ورقم العضوية حقول إجبارية")
            else:
                # معالجة الصورة
                photo_path = ""
                if photo:
                    # حفظ الصورة في مجلد assets محلياً
                    save_dir = f"assets/member_files/{pkf_id}"
                    os.makedirs(save_dir, exist_ok=True)
                    photo_path = os.path.join(save_dir, photo.name)
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())

                member_data = {
                    "full_name_ar": name_ar, "full_name": name_en, "pkf_id": pkf_id,
                    "id_number": id_number, "role": role, "dob": str(dob), 
                    "gender": gender, "photo_path": photo_path,
                    "club_name": club_name, "club_id": clubs_list.get(club_name),
                    "expiry_date": str(expiry_date),
                    # بيانات خاصة
                    "current_belt": belt if role == "Player" else "",
                    "belt_date": str(belt_date) if role == "Player" else "",
                    "specific_data": json.dumps(specific_data), # نحفظ التفاصيل كـ JSON
                    # تعبئة حقول التصنيف المباشرة لسهولة البحث
                    "rank_local": specific_data.get('nat_rank', ''),
                    "rank_intl": specific_data.get('int_rank', '')
                }
                
                success, msg = database.add_member(member_data)
                if success: st.success(f"✅ {msg}")
                else: st.error(f"❌ {msg}")

# ==========================================
# 3. إدارة الأندية
# ==========================================
elif menu == "إدارة الأندية":
    st.title("🏢 إدارة الأندية")
    with st.form("club_form"):
        name = st.text_input("اسم النادي")
        rep_name = st.text_input("اسم الممثل")
        phone = st.text_input("رقم الهاتف")
        
        if st.form_submit_button("حفظ النادي"):
            data = {"name": name, "representative_name": rep_name, "phone": phone}
            database.add_club(data)
            st.success("تم الحفظ")

    # عرض الأندية
    clubs = database.get_all_clubs()
    if clubs:
        st.dataframe(pd.DataFrame(clubs)[['name', 'representative_name', 'phone']])

# ==========================================
# 4. التقارير والطباعة (الجوهر)
# ==========================================
elif menu == "التقارير والطباعة":
    st.title("🖨️ إصدار البطاقات والتقارير")
    
    # فلتر البحث
    col1, col2, col3 = st.columns(3)
    search_q = col1.text_input("بحث بالاسم/الرقم")
    role_filter = col2.selectbox("تصفية بالدور", ["All Roles", "Player", "Coach", "Referee"])
    club_filter = col3.selectbox("تصفية بالنادي", ["All Clubs"] + database.get_unique_clubs())
    
    # جلب النتائج
    filters = {"query": search_q}
    if role_filter != "All Roles": filters["role"] = role_filter
    if club_filter != "All Clubs": filters["club"] = club_filter
    
    results = database.search_members_advanced(**filters)
    
    if results:
        for m in results:
            with st.expander(f"{m['full_name_ar']} | {m['role']} | {m['pkf_id']}"):
                c1, c2, c3 = st.columns([1, 2, 2])
                
                with c1:
                    if m['photo_path'] and os.path.exists(m['photo_path']):
                        st.image(m['photo_path'], width=100)
                    else: st.info("بدون صورة")
                
                with c2:
                    st.write(f"**English:** {m['full_name']}")
                    st.write(f"**Club:** {m['club_name']}")
                    st.write(f"**Expiry:** {m['expiry_date']}")
                
                with c3:
                    st.write("**الإجراءات:**")
                    
                    # 1. طباعة البطاقة (Word)
                    if st.button("💳 إصدار البطاقة", key=f"card_{m['id']}"):
                        try:
                            # نستخدم الكود الذي أرسلته لي (card_generator)
                            doc_path = generate_member_card(m)
                            with open(doc_path, "rb") as f:
                                st.download_button(
                                    "📥 تحميل البطاقة (Word)", f, 
                                    file_name=os.path.basename(doc_path),
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_card_{m['id']}"
                                )
                        except Exception as e:
                            st.error(f"خطأ: {e}")

                    # 2. طباعة التقرير (Profile)
                    if st.button("📄 طباعة الملف الشخصي", key=f"prof_{m['id']}"):
                        try:
                            doc_path = generate_bilingual_profile_doc(
                                m, MEMBER_LABELS_EN, MEMBER_LABELS_AR, {}, {}, {}, {}, 'member'
                            )
                            with open(doc_path, "rb") as f:
                                st.download_button(
                                    "📥 تحميل الملف (Word)", f, 
                                    file_name=os.path.basename(doc_path),
                                    key=f"dl_prof_{m['id']}"
                                )
                        except Exception as e:
                            st.error(f"خطأ: {e}")

# ==========================================
# 5. التنبيهات
# ==========================================
elif menu == "التنبيهات":
    st.title("⚠️ تنبيهات انتهاء الصلاحية")
    
    days = st.slider("عرض المنتهي خلال (أيام):", 30, 180, 60)
    
    st.subheader("اشتراكات تنتهي قريباً")
    exp_members = database.get_expiring_members(days)
    if exp_members:
        st.dataframe(pd.DataFrame(exp_members)[['full_name_ar', 'club_name', 'expiry_date']])
    else:
        st.success("لا توجد اشتراكات تنتهي قريباً.")
        
    st.subheader("جوازات سفر تنتهي قريباً")
    exp_pass = database.get_expiring_passports(days)
    if exp_pass:
        st.dataframe(pd.DataFrame(exp_pass)[['full_name_ar', 'passport_number', 'passport_expiry_date']])
