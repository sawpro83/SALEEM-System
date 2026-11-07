import streamlit as st
import sqlite3, os, requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="نظام إدارة الصيانة", layout="centered")
PASSWORD_PROFITS = "1234"
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF3d2NhanlsbGV0cWdneXNmeGx3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQwNjM0MzYsImV4cCI6MjEwOTYzOTQzNn0.ZnbxHoJHocMdokrU4V0nD8E7AC8YPj3tYPWT3eZfje0"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def init_db():
    conn = sqlite3.connect("saleem_local_cache.db")
    conn.execute("CREATE TABLE IF NOT EXISTS repairs (id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, phone_number TEXT, device_model TEXT, issue TEXT, cost REAL, part_cost REAL, status TEXT, date_added TEXT, synced INTEGER DEFAULT 1)")
    conn.execute("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, part_name TEXT, quantity INTEGER, price REAL, synced INTEGER DEFAULT 1)")
    conn.commit()
    conn.close()

init_db()

def sync_db():
    try:
        conn = sqlite3.connect("saleem_local_cache.db")
        for r in conn.execute("SELECT client_name,phone_number,device_model,issue,cost,part_cost,status,date_added FROM repairs WHERE synced=0").fetchall():
            requests.post(f"{SUPABASE_URL}/repairs", headers=HEADERS, json={"client_name":r[0],"phone_number":r[1],"device_model":r[2],"issue":r[3],"cost":r[4],"part_cost":r[5],"status":r[6],"date_added":r[7]}, timeout=5)
        for i in conn.execute("SELECT part_name,quantity,price FROM inventory WHERE synced=0").fetchall():
            requests.post(f"{SUPABASE_URL}/inventory", headers=HEADERS, json={"part_name":i[0],"quantity":i[1],"price":i[2]}, timeout=5)
            
        res_r = requests.get(f"{SUPABASE_URL}/repairs?select=*&order=id.desc", headers=HEADERS, timeout=5)
        res_i = requests.get(f"{SUPABASE_URL}/inventory?select=*&order=id.desc", headers=HEADERS, timeout=5)
        res_r.raise_for_status()
        res_i.raise_for_status()
        
        conn.execute("DELETE FROM repairs")
        for r in res_r.json():
            conn.execute("INSERT INTO repairs VALUES (?,?,?,?,?,?,?,?,?,1)", (r['id'],r['client_name'],r['phone_number'],r['device_model'],r['issue'],r['cost'],r.get('part_cost',0),r['status'],r['date_added']))
        conn.execute("DELETE FROM inventory")
        for i in res_i.json():
            conn.execute("INSERT INTO inventory VALUES (?,?,?,?,1)", (i['id'],i['part_name'],i['quantity'],i['price']))
        conn.commit()
        conn.close()
        st.session_state.is_online = True
        st.session_state.sync_err = ""
    except Exception as e:
        st.session_state.is_online = False
        st.session_state.sync_err = str(e)

# المزامنة تتم مرة واحدة فقط عند فتح الصفحة لسرعة فائقة
if 'synced_once' not in st.session_state:
    sync_db()
    st.session_state.synced_once = True

is_online = st.session_state.get('is_online', False)

st.markdown("""
<style>
@import url('https://googleapis.com');
html, body, .stApp, p, h1, h2, h3, label, input, textarea, select, button { font-family: 'Cairo', sans-serif !important; }
[data-testid="stIconMaterial"], .material-symbols-rounded, span[translate="no"] { font-family: 'Material Symbols Rounded' !important; }
.main { background-color: #f8fafc; text-align: right; direction: rtl; }
div.stButton > button { background: linear-gradient(135deg, #00807d, #004d4b) !important; color: white !important; border: 2px solid #00a39f !important; border-radius: 16px !important; width: 100% !important; min-height: 60px !important; margin-top: 6px !important; }
div.stButton > button p { font-size: 22px !important; font-weight: 800 !important; color: white !important; margin: 0 !important; }
div[role="radiogroup"] { display: flex; justify-content: center; gap: 15px; background: #fff; padding: 10px; border-radius: 14px; border: 2px solid #00807d; margin-bottom: 15px; }
div[role="radiogroup"] label p { font-size: 22px !important; font-weight: 800 !important; color: #004d4b !important; }
.card { background: white; padding: 16px; border-radius: 14px; border: 1px solid #e2e8f0; border-right: 6px solid #007a78; margin-bottom: 10px; text-align: right; direction: rtl; }
h1, h2, h3, p, label { text-align: right; direction: rtl; }
</style>
""", unsafe_allow_html=True)

c_stat, c_btn = st.columns([3, 1])
with c_stat:
    if is_online:
        st.markdown("<div style='background:#dcfce7;color:#166534;padding:12px;border-radius:12px;text-align:center;font-weight:bold;margin-top:6px;'>🟢 متصل بالسحابة</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:#fef3c7;color:#92400e;padding:12px;border-radius:12px;text-align:center;font-weight:bold;margin-top:6px;'>🟠 وضع عدم الاتصال (حفظ محلي)</div>", unsafe_allow_html=True)
with c_btn:
    if st.button("🔄 مزامنة"):
        sync_db()
        st.rerun()

if not is_online and st.session_state.get('sync_err'):
    st.caption(f"ملاحظة الاتصال: {st.session_state.sync_err}")

if 'page' not in st.session_state: st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    for n in ["logo.jpg", "logo", "logo.jpg.jpg", "logo.png", "logo.jpeg"]:
        if os.path.exists(n): st.image(n, use_container_width=True); break
    c1, c2 = st.columns(2, gap="large")
    if c1.button("🔐 المدير"): st.session_state.page = 'auth'; st.rerun()
    if c2.button("🛠️ الدخول للمنظومة"): st.session_state.page = 'mgmt'; st.rerun()

elif st.session_state.page == 'auth':
    st.markdown("<h2 style='color:#007a78;text-align:center;'>🔒 دخول المدير</h2>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("✅ دخول"):
        if pwd == PASSWORD_PROFITS: st.session_state.page = 'profits'; st.rerun()
        else: st.error("كلمة المرور خاطئة!")
    if c2.button("🏠 الشاشة الرئيسية"): st.session_state.page = 'welcome'; st.rerun()

elif st.session_state.page == 'profits':
    if st.button("🏠 العودة للشاشة الرئيسية"): st.session_state.page = 'welcome'; st.rerun()
    st.markdown("<h2 style='color:#007a78;'>📊 الأرباح الشهرية للصيانة</h2><hr>", unsafe_allow_html=True)
    conn = sqlite3.connect("saleem_local_cache.db")
    df = pd.read_sql_query("SELECT * FROM repairs", conn); conn.close()
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
    if st.button("🏠 العودة للشاشة الرئيسية"): st.session_state.page = 'welcome'; st.rerun()
    sec = st.radio("القسم:", ["📱 قسم الصيانة", "📦 قسم المخزن"], horizontal=True, label_visibility="collapsed")

    if sec == "📦 قسم المخزن":
        st.markdown("### ➕ إضافة صنف للمخزن")
        pn = st.text_input("اسم الصنف", key="in_n")
        c1, c2 = st.columns(2)
        pq = c1.number_input("الكمية", min_value=1, step=1, key="in_q")
        pp = c2.number_input("السعر (د.ل)", min_value=0.0, step=5.0, key="in_p")
        if st.button("💾 حفظ الصنف") and pn.strip():
            conn = sqlite3.connect("saleem_local_cache.db")
            if is_online:
                try:
                    res = requests.post(f"{SUPABASE_URL}/inventory", headers=HEADERS, json={"part_name": pn.strip(), "quantity": int(pq), "price": float(pp)}, timeout=4).json()
                    conn.execute("INSERT INTO inventory VALUES (?,?,?,?,1)", (res[0]['id'], pn.strip(), int(pq), float(pp)))
                except Exception:
                    conn.execute("INSERT INTO inventory (part_name,quantity,price,synced) VALUES (?,?,?,0)", (pn.strip(), int(pq), float(pp)))
            else:
                conn.execute("INSERT INTO inventory (part_name,quantity,price,synced) VALUES (?,?,?,0)", (pn.strip(), int(pq), float(pp)))
            conn.commit(); conn.close(); st.rerun()

        conn = sqlite3.connect("saleem_local_cache.db")
        rows = conn.execute("SELECT id, part_name, quantity, price FROM inventory ORDER BY id DESC").fetchall(); conn.close()
        for r in rows:
            st.markdown(f"<div class='card'><b>{r[1]}</b> | الكمية: <b>{r[2]}</b> | السعر: <b>{r[3]} د.ل</b></div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            if b1.button("➕ زيادة", key=f"a_{r[0]}"):
                conn = sqlite3.connect("saleem_local_cache.db"); conn.execute("UPDATE inventory SET quantity=quantity+1 WHERE id=?", (r[0],)); conn.commit(); conn.close()
                if is_online:
                    try: requests.patch(f"{SUPABASE_URL}/inventory?id=eq.{r[0]}", headers=HEADERS, json={"quantity": int(r[2]) + 1}, timeout=3)
                    except Exception: pass
                st.rerun()
            if b2.button("➖ سحب", key=f"u_{r[0]}") and r[2] > 0:
                conn = sqlite3.connect("saleem_local_cache.db"); conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=?", (r[0],)); conn.commit(); conn.close()
                if is_online:
