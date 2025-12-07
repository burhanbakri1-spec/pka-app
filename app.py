import streamlit as st
import database
from id_generator import generate_card_image
import os

# تهيئة قاعدة البيانات عند بدء التشغيل
database.init_db()

# 1. إعداد الصفحة
st.set_page_config(page_title="PKF Card System", layout="wide")

# 2. العنوان والتصميم
st.title("🥋 الاتحاد الفلسطيني للكاراتيه - نظام البطاقات")
st.markdown("---")

# 3. القائمة الجانبية (إضافة عضو)
with st.sidebar:
    st.header("➕ إضافة عضو جديد")
    with st.form("add_member"):
        name_ar = st.text_input("الاسم (عربي)")
        name_en = st.text_input("الاسم (إنجليزي)")
        pkf_id = st.text_input("رقم العضوية (PKF ID)")
        role = st.selectbox("الدور", ["Player", "Coach", "Referee", "Admin"])
        dob = st.text_input("تاريخ الميلاد")
        club = st.text_input("النادي / الهيئة")
        
        # حقول إضافية
        weight = st.text_input("الوزن (للاعبين)")
        belt = st.text_input("الحزام")
        belt_date = st.text_input("تاريخ الحزام")
        
        # حقول التصنيف (للحكام والمدربين)
        rank_local = st.text_input("التصنيف الوطني / درجة التدريب")
        rank_intl = st.text_input("التصنيف الدولي")
        
        # لا يمكن رفع الصور بسهولة هنا بدون إعدادات إضافية، لذا نتركها فارغة مؤقتاً
        
        submitted = st.form_submit_button("حفظ البيانات")
        if submitted:
            data = {
                "full_name": name_ar, "full_name_en": name_en, "pkf_id": pkf_id,
                "role": role, "dob": dob, "club_name": club,
                "weight": weight, "belt_rank": belt, "belt_date": belt_date,
                "rank_local": rank_local, "rank_intl": rank_intl,
                "photo_path": "" # مؤقتاً
            }
            success, msg = database.add_member(data)
            if success:
                st.success(msg)
            else:
                st.error(msg)

# 4. منطقة البحث والطباعة (الوسط)
st.header("🔍 البحث والطباعة")
search_query = st.text_input("ابحث بالاسم أو رقم العضوية...")

if search_query:
    results = database.search_members(search_query)
    
    if not results:
        st.warning("لا توجد نتائج.")
    else:
        for member in results:
            with st.expander(f"{member['full_name']} - {member['role']} ({member['pkf_id']})"):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    # عرض الصورة إذا وجدت (محلياً)
                    if member['photo_path'] and os.path.exists(member['photo_path']):
                        st.image(member['photo_path'], width=150)
                    else:
                        st.info("لا توجد صورة")
                
                with col2:
                    st.write(f"**النادي:** {member['club_name']}")
                    st.write(f"**الحزام:** {member['belt_rank']}")
                    
                    # زر توليد البطاقة
                    generate_btn = st.button(f"📄 تجهيز بطاقة {member['full_name']}", key=member['id'])
                    
                    if generate_btn:
                        with st.spinner("جاري إعداد ملف الوورد..."):
                            # استدعاء دالة التوليد التي كتبناها سابقاً
                            docx_path, preview_img = generate_card_image(member)
                            
                            if docx_path and os.path.exists(docx_path):
                                st.success("تم التجهيز!")
                                # عرض زر التحميل
                                with open(docx_path, "rb") as f:
                                    st.download_button(
                                        label="📥 تحميل ملف الوورد للطباعة",
                                        data=f,
                                        file_name=os.path.basename(docx_path),
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )