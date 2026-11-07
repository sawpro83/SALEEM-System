import streamlit as st
import sqlite3, os
import pandas as pd
from supabase import create_client
from mgmt import show_mgmt

st.set_page_config(page_title="نظام إدارة الصيانة", layout="centered")
PASSWORD_PROFITS = "1234"
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_99S_RRCdvgeR5RYHIz6HEQ_2liMn71n"

conn = sqlite3.connect("saleem_local_cache.db")
conn.execute("CREATE TABLE IF NOT EXISTS repairs (id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, phone_number TEXT, device_model TEXT, issue TEXT, cost REAL, part_cost REAL, status TEXT, date_added TEXT, synced INTEGER DEFAULT 1)")
conn.execute("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, part_name TEXT, quantity INTEGER, price REAL, synced INTEGER DEFAULT 1)")
conn.commit()
conn.close()

def sync_db():
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        conn = sqlite3.connect("saleem_local_cache.db")
        
        for r in conn.execute("SELECT client_name,phone_number,device_model,issue,cost,part_cost,status,date_added FROM repairs WHERE synced=0").fetchall():
            sb.table("repairs").insert({"client_name":r,"phone_number":r,"device_model":r,"issue":r,"cost":r,"part_cost":r,"status":r,"date_added":r}).execute()
            
        for i in conn.execute("SELECT part_name,quantity,price FROM inventory WHERE synced=0").fetchall():
            sb.table("inventory").insert({"part_name":i,"quantity":i,"price":i}).execute()
            
        r_data = sb.table("repairs").select("*").order("id", desc=True).execute().data
        i_data = sb.table("inventory").select("*").order("id", desc=True).execute().data
        
        conn.execute("DELETE FROM repairs")
        for r in r_data:
            conn.execute("INSERT INTO repairs VALUES (?,?,?,?,?,?,?,?,?,1)", (r['id'],r['client_name'],r['phone_number'],r['device_model'],r['issue'],r['cost'],r.get('part_cost',0),r['status'],r['date_added']))
            
        conn.execute("DELETE FROM inventory")
        for i in i_data:
            conn.execute("INSERT INTO inventory VALUES (?,?,?,?,1)", (i['id'],i['part_name'],i['quantity'],i['price']))
            
        conn.commit()
        conn.close()
        return sb, True
    except Exception as e:
        st.warning(f"سبب عدم الاتصال بالسحابة: {e}")
        return None, False

supabase, is_online = sync_db()

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

st.markdown("<div style='background:#dcfce7;color:#166534;padding:8px;border-radius:10px;text-align:center;font-weight:bold;margin-bottom:10px;'>متصل بالسحابة</div>" if is_online else "<div style='background:#fef3c7;color:#92400e;padding:8px;border-radius:10px;text-align:center;font-weight:bold;margin-bottom:10px;'>وضع عدم الاتصال (حفظ محلي)</div>", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    for n in ["logo.jpg", "logo", "logo.jpg.jpg", "logo.png", "logo.jpeg"]:
        if os.path.exists(n):
            st.image(n, use_container_width=True)
            break
    c1, c2 = st.columns(2, gap="large")
    if c1.button("المدير"):
        st.session_state.page = 'auth'
        st.rerun()
    if c2.button("الدخول للمنظومة"):
        st.session_state.page = 'mgmt'
        st.rerun()

elif st.session_state.page == 'auth':
    st.markdown("<h2 style='color:#007a78;text-align:center;'>دخول المدير</h2>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("دخول"):
        if pwd == PASSWORD_PROFITS:
            st.session_state.page = 'profits'
            st.rerun()
        else:
            st.error("كلمة المرور خاطئة!")
    if c2.button("الشاشة الرئيسية"):
        st.session_state.page = 'welcome'
        st.rerun()

elif st.session_state.page == 'profits':
    if st.button("العودة للشاشة الرئيسية"):
        st.session_state.page = 'welcome'
        st.rerun()
    st.markdown("<h2 style='color:#007a78;'>الأرباح الشهرية للصيانة</h2><hr>", unsafe_allow_html=True)
    conn = sqlite3.connect("saleem_local_cache.db")
    df = pd.read_sql_query("SELECT * FROM repairs", conn)
    conn.close()
    if not df.empty:
        df['net'] = df['cost'] - df['part_cost'].fillna(0)
        df['month'] = pd.to_datetime(df['date_added']).dt.strftime('%Y-%m')
        sel_m = st.selectbox("اختر الشهر:", sorted(df['month'].unique(), reverse=True))
        m_df = df[df['month'] == sel_m]
        done = m_df[m_df['status'].isin(['تمت صيانته', 'تم تسليمه'])]
        st.markdown(f"<div style='display:flex;gap:12px;margin-bottom:15px;'><div class='card' style='flex:1;'>إجمالي الدخل<br><b style='font-size:26px;'>{done['cost'].sum():.2f} د.ل</b></div><div class='card' style='flex:1;'>صافي الربح<br><b style='font-size:26px;color:#007a78;'>{done['net'].sum():.2f} د.ل</b></div></div>", unsafe_allow_html=True)
        st.dataframe(m_df[['id','client_name','device_model','cost','part_cost','net','status']], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات صيانة مسجلة.")

elif st.session_state.page == 'mgmt':
    show_mgmt(supabase, is_online)
