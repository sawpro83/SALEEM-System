import streamlit as st
import os
import pandas as pd
import streamlit.components.v1 as components
from supabase import create_client

st.set_page_config(page_title="نظام إدارة الصيانة", layout="centered")
PASSWORD_PROFITS = "1234"

SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_99S_RRCdvgeR5RYHIz6HEQ_2liMn71n"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.markdown("""
<style>
@import url('https://googleapis.com');
html, body, .stApp, p, h1, h2, h3, label, input, textarea, select, button { font-family: 'Cairo', sans-serif !important; }
[data-testid="stIconMaterial"], .material-symbols-rounded, span[translate="no"] { font-family: 'Material Symbols Rounded' !important; }
.main { background-color: #f8fafc; text-align: right; direction: rtl; }
div.stButton > button { background: linear-gradient(135deg, #00807d, #004d4b) !important; color: white !important; border: 2px solid #00a39f !important; border-radius: 16px !important; width: 100% !important; min-height: 68px !important; margin-top: 8px !important; }
div.stButton > button p { font-size: 24px !important; font-weight: 800 !important; color: white !important; margin: 0 !important; }
div[role="radiogroup"] { display: flex; justify-content: center; gap: 15px; background: #fff; padding: 10px; border-radius: 14px; border: 2px solid #00807d; margin-bottom: 15px; }
div[role="radiogroup"] label p { font-size: 22px !important; font-weight: 800 !important; color: #004d4b !important; }
.card { background: white; padding: 18px; border-radius: 14px; border: 1px solid #e2e8f0; border-right: 6px solid #007a78; margin-bottom: 12px; text-align: right; direction: rtl; }
h1, h2, h3, p, label { text-align: right; direction: rtl; }
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    for n in ["logo.jpg", "logo", "logo.jpg.jpg", "logo.png", "logo.jpeg"]:
        if os.path.exists(n):
            st.image(n, use_container_width=True)
            break
    c1, c2 = st.columns(2, gap="large")
    if c1.button("🔐 المدير"):
        st.session_state.page = 'auth'
        st.rerun()
    if c2.button("🛠️ الدخول للمنظومة"):
        st.session_state.page = 'mgmt'
        st.rerun()

elif st.session_state.page == 'auth':
    st.markdown("<h2 style='color:#007a78;text-align:center;'>🔒 دخول المدير</h2>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("✅ دخول"):
        if pwd == PASSWORD_PROFITS:
            st.session_state.page = 'profits'
            st.rerun()
        else:
            st.error("كلمة المرور خاطئة!")
    if c2.button("🏠 الشاشة الرئيسية"):
        st.session_state.page = 'welcome'
        st.rerun()

elif st.session_state.page == 'profits':
    if st.button("🏠 العودة للشاشة الرئيسية"):
        st.session_state.page = 'welcome'
        st.rerun()
    st.markdown("<h2 style='color:#007a78;'>📊 الأرباح الشهرية للصيانة</h2><hr>", unsafe_allow_html=True)
    res = supabase.table("repairs").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['net'] = df['cost'] - df['part_cost'].fillna(0)
        df['month'] = pd.to_datetime(df['date_added']).dt.strftime('%Y-%m')
        sel_m = st.selectbox("اختر الشهر:", sorted(df['month'].unique(), reverse=True))
        m_df = df[df['month'] == sel_m]
        done = m_df[m_df['status'].isin(['تمت صيانته', 'تم تسليمه'])]
        st.markdown(f"<div style='display:flex;gap:12px;margin-bottom:15px;'><div class='card' style='flex:1;'>إجمالي الدخل<br><b style='font-size:26px;'>{done['cost'].sum():.2f} د.ل</b></div><div class='card' style='flex:1;'>صافي الربح<br><b style='font-size:26px;color:#007a78;'>{done['net'].sum():.2f} د.ل</b></div></div>", unsafe_allow_html=True)
        st.dataframe(m_df[['id', 'client_name', 'device_model', 'cost', 'part_cost', 'net', 'status']], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات صيانة مسجلة حتى الآن.")

elif st.session_state.page == 'mgmt':
    if st.button("🏠 العودة للشاشة الرئيسية"):
        st.session_state.page = 'welcome'
        st.rerun()
    sec = st.radio("القسم:", ["📱 قسم الصيانة", "📦 قسم المخزن"], horizontal=True, label_visibility="collapsed")

    if sec == "📦 قسم المخزن":
        st.markdown("### ➕ إضافة صنف للمخزن")
        pn = st.text_input("اسم الصنف", key="in_n")
        c1, c2 = st.columns(2)
        pq = c1.number_input("الكمية", min_value=1, step=1, key="in_q")
        pp = c2.number_input("السعر (د.ل)", min_value=0.0, step=5.0, key="in_p")
        if st.button("💾 حفظ الصنف") and pn.strip():
            supabase.table("inventory").insert({"part_name": pn.strip(), "quantity": int(pq), "price": float(pp)}).execute()
            st.rerun()
        res_i = supabase.table("inventory").select("*").order("id", desc=True).execute()
        for r in res_i.data:
            st.markdown(f"<div class='card'><b>{r['part_name']}</b> | الكمية: <b>{r['quantity']}</b> | السعر: <b>{r['price']} د.ل</b></div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            if b1.button("➕", key=f"a_{r['id']}"):
                supabase.table("inventory").update({"quantity": r['quantity'] + 1}).eq("id", r['id']).execute()
                st.rerun()
            if b2.button("➖", key=f"u_{r['id']}") and r['quantity'] > 0:
                supabase.table("inventory").update({"quantity": r['quantity'] - 1}).eq("id", r['id']).execute()
                st.rerun()
            if b3.button("🗑️", key=f"di_{r['id']}"):
                supabase.table("inventory").delete().eq("id", r['id']).execute()
                st.rerun()

    elif sec == "📱 قسم الصيانة":
        st.markdown("### ➕ تسجيل جهاز صيانة")
        cn = st.text_input("اسم الزبون", key="cn")
        cp = st.text_input("رقم الهاتف", key="cp")
        cd = st.text_input("نوع الجهاز", key="cd")
        ci = st.text_input("وصف العطل", key="ci")
        c1, c2 = st.columns(2)
        cc = c1.number_input("السعر للزبون (د.ل)", min_value=0.0, step=5.0, key="cc")
        cpc = c2.number_input("تكلفة القطعة (د.ل)", min_value=0.0, step=5.0, key="cpc")
        cs = st.selectbox("الحالة", ["قيد الانتظار", "تحت الصيانة", "تمت صيانته", "تم تسليمه"], key="cs")
        if st.button("💾 حفظ الجهاز") and cn.strip() and cd.strip():
            supabase.table("repairs").insert({"client_name": cn, "phone_number": cp, "device_model": cd, "issue": ci, "cost": cc, "part_cost": cpc, "status": cs}).execute()
            st.rerun()
        res_r = supabase.table("repairs").select("*").order("id", desc=True).execute()
        for r in res_r.data:
            st.markdown(f"<div class='card'><b>#{r['id']} | {r['client_name']} ({r['device_model']})</b><br>الهاتف: {r['phone_number']} | العطل: {r['issue']} | السعر: {r['cost']} د.ل</div>", unsafe_allow_html=True)
            st_list = ["قيد الانتظار", "تحت الصيانة", "تمت صيانته", "تم تسليمه"]
            ns = st.selectbox("الحالة", st_list, index=st_list.index(r['status']) if r['status'] in st_list else 0, key=f"s_{r['id']}")
            if ns != r['status']:
                supabase.table("repairs").update({"status": ns}).eq("id", r['id']).execute()
                st.rerun()
            c_p, c_d = st.columns(2)
            with c_p:
                btn = f'<button onclick="var w=window.open(\'\',\'\',\'width=400,height=400\');w.document.write(\'<div dir=rtl style=text-align:center><h2>وصل #{r["id"]}</h2><p>{r["client_name"]} - {r["device_model"]}</p><p>{r["cost"]} د.ل</p></div>\');w.print();w.close();" style="background:#00807d;color:white;border:none;padding:14px;border-radius:16px;width:100%;min-height:68px;font-weight:bold;font-size:24px;cursor:pointer;margin-top:8px;">🖨️ طباعة</button>'
                components.html(btn, height=85)
            if c_d.button("🗑️ حذف", key=f"d_{r['id']}"):
                supabase.table("repairs").delete().eq("id", r['id']).execute()
                st.rerun()
