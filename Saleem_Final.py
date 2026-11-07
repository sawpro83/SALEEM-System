import streamlit as st, sqlite3, os, requests, pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="نظام الصيانة", layout="centered")
URL = "https://supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF3d2NhanlsbGV0cWdneXNmeGx3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQwNjM0MzYsImV4cCI6MjEwOTYzOTQzNn0.ZnbxHoJHocMdokrU4V0nD8E7AC8YPj3tYPWT3eZfje0"
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

conn = sqlite3.connect("saleem_local_cache.db")
conn.execute("CREATE TABLE IF NOT EXISTS repairs (id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, phone_number TEXT, device_model TEXT, issue TEXT, cost REAL, part_cost REAL, status TEXT, date_added TEXT, synced INTEGER DEFAULT 1)")
conn.execute("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, part_name TEXT, quantity INTEGER, price REAL, synced INTEGER DEFAULT 1)")
conn.commit(); conn.close()

def sync():
    try:
        c = sqlite3.connect("saleem_local_cache.db")
        for r in c.execute("SELECT client_name,phone_number,device_model,issue,cost,part_cost,status,date_added FROM repairs WHERE synced=0").fetchall():
            requests.post(f"{URL}/repairs", headers=H, json={"client_name":r,"phone_number":r,"device_model":r,"issue":r,"cost":r,"part_cost":r,"status":r,"date_added":r}, timeout=5)
        for i in c.execute("SELECT part_name,quantity,price FROM inventory WHERE synced=0").fetchall():
            requests.post(f"{URL}/inventory", headers=H, json={"part_name":i,"quantity":i,"price":i}, timeout=5)
        rr = requests.get(f"{URL}/repairs?select=*&order=id.desc", headers=H, timeout=5).json()
        ri = requests.get(f"{URL}/inventory?select=*&order=id.desc", headers=H, timeout=5).json()
        c.execute("DELETE FROM repairs")
        for r in rr: c.execute("INSERT INTO repairs VALUES (?,?,?,?,?,?,?,?,?,1)", (r['id'],r['client_name'],r['phone_number'],r['device_model'],r['issue'],r['cost'],r.get('part_cost',0),r['status'],r['date_added']))
        c.execute("DELETE FROM inventory")
        for i in ri: c.execute("INSERT INTO inventory VALUES (?,?,?,?,1)", (i['id'],i['part_name'],i['quantity'],i['price']))
        c.commit(); c.close()
        st.session_state.on = True; st.session_state.err = ""
    except Exception as e:
        st.session_state.on = False; st.session_state.err = str(e)

if 'init' not in st.session_state: sync(); st.session_state.init = True
on = st.session_state.get('on', False)

st.markdown("<style>html,body,.stApp{direction:rtl;text-align:right;} div.stButton>button{background:#00807d;color:white;border-radius:12px;width:100%;min-height:55px;font-size:20px;font-weight:bold;} .card{background:white;padding:14px;border-radius:12px;border-right:5px solid #00807d;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);}</style>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
c1.success("متصل بالسحابة") if on else c1.warning(f"حفظ محلي ({st.session_state.get('err','')})")
if c2.button("مزامنة"): sync(); st.rerun()

if 'p' not in st.session_state: st.session_state.p = 'w'

if st.session_state.p == 'w':
    for n in ["logo.jpg", "logo.png", "logo.jpeg"]:
        if os.path.exists(n): st.image(n, use_container_width=True); break
    a, b = st.columns(2)
    if a.button("المدير"): st.session_state.p = 'auth'; st.rerun()
    if b.button("المنظومة"): st.session_state.p = 'mgmt'; st.rerun()

elif st.session_state.p == 'auth':
    pwd = st.text_input("كلمة المرور:", type="password")
    if st.button("دخول") and pwd == "1234": st.session_state.p = 'prof'; st.rerun()
    if st.button("رجوع"): st.session_state.p = 'w'; st.rerun()

elif st.session_state.p == 'prof':
    if st.button("رجوع"): st.session_state.p = 'w'; st.rerun()
    c = sqlite3.connect("saleem_local_cache.db"); df = pd.read_sql_query("SELECT * FROM repairs", c); c.close()
    if not df.empty:
        df['net'] = df['cost'] - df['part_cost'].fillna(0)
        done = df[df['status'].isin(['تمت صيانته', 'تم تسليمه'])]
        st.info(f"إجمالي الدخل: {done['cost'].sum():.2f} د.ل | صافي الربح: {done['net'].sum():.2f} د.ل")
        st.dataframe(df[['id','client_name','device_model','cost','part_cost','net','status']], use_container_width=True, hide_index=True)

elif st.session_state.p == 'mgmt':
    if st.button("رجوع"): st.session_state.p = 'w'; st.rerun()
    sec = st.radio("القسم", ["الصيانة", "المخزن"], horizontal=True)
    if sec == "المخزن":
        pn = st.text_input("اسم الصنف"); pq = st.number_input("الكمية", 1); pp = st.number_input("السعر", 0.0)
        if st.button("حفظ الصنف") and pn:
            c = sqlite3.connect("saleem_local_cache.db")
            if on:
                res = requests.post(f"{URL}/inventory", headers=H, json={"part_name":pn,"quantity":pq,"price":pp}).json()
                c.execute("INSERT INTO inventory VALUES (?,?,?,?,1)", (res['id'],pn,pq,pp))
            else: c.execute("INSERT INTO inventory (part_name,quantity,price,synced) VALUES (?,?,?,0)", (pn,pq,pp))
            c.commit(); c.close(); st.rerun()
        c = sqlite3.connect("saleem_local_cache.db"); rows = c.execute("SELECT id,part_name,quantity,price FROM inventory ORDER BY id DESC").fetchall(); c.close()
        for r in rows:
            st.markdown(f"<div class='card'><b>{r}</b> | الكمية: {r} | السعر: {r} د.ل</div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            if b1.button("زيادة", key=f"a{r}"):
                c = sqlite3.connect("saleem_local_cache.db"); c.execute("UPDATE inventory SET quantity=quantity+1 WHERE id=?", (r,)); c.commit(); c.close()
                if on: requests.patch(f"{URL}/inventory?id=eq.{r}", headers=H, json={"quantity":r+1})
                st.rerun()
            if b2.button("سحب", key=f"u{r}") and r > 0:
                c = sqlite3.connect("saleem_local_cache.db"); c.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=?", (r,)); c.commit(); c.close()
                if on: requests.patch(f"{URL}/inventory?id=eq.{r}", headers=H, json={"quantity":r-1})
                st.rerun()
            if b3.button("حذف", key=f"d{r}"):
                c = sqlite3.connect("saleem_local_cache.db"); c.execute("DELETE FROM inventory WHERE id=?", (r,)); c.commit(); c.close()
                if on: requests.delete(f"{URL}/inventory?id=eq.{r}", headers=H)
                st.rerun()
    else:
        cn = st.text_input("الزبون"); cp = st.text_input("الهاتف"); cd = st.text_input("الجهاز"); ci = st.text_input("العطل")
        cc = st.number_input("السعر", 0.0); cpc = st.number_input("التكلفة", 0.0); cs = st.selectbox("الحالة", ["قيد الانتظار","تحت الصيانة","تمت صيانته","تم تسليمه"])
        if st.button("حفظ الجهاز") and cn and cd:
            c = sqlite3.connect("saleem_local_cache.db")
            if on:
                res = requests.post(f"{URL}/repairs", headers=H, json={"client_name":cn,"phone_number":cp,"device_model":cd,"issue":ci,"cost":cc,"part_cost":cpc,"status":cs}).json()
                c.execute("INSERT INTO repairs VALUES (?,?,?,?,?,?,?,?,?,1)", (res['id'],cn,cp,cd,ci,cc,cpc,cs,res['date_added']))
            else: c.execute("INSERT INTO repairs (client_name,phone_number,device_model,issue,cost,part_cost,status,date_added,synced) VALUES (?,?,?,?,?,?,?,date('now'),0)", (cn,cp,cd,ci,cc,cpc,cs))
            c.commit(); c.close(); st.rerun()
        c = sqlite3.connect("saleem_local_cache.db"); reps = c.execute("SELECT id,client_name,phone_number,device_model,issue,cost,status FROM repairs ORDER BY id DESC").fetchall(); c.close()
        for r in reps:
            st.markdown(f"<div class='card'><b>#{r} | {r} ({r})</b><br>{r} | {r} | {r} د.ل</div>", unsafe_allow_html=True)
            st_l = ["قيد الانتظار","تحت الصيانة","تمت صيانته","تم تسليمه"]
            ns = st.selectbox("الحالة", st_l, index=st_l.index(r) if r in st_l else 0, key=f"s{r}")
            if ns != r:
                c = sqlite3.connect("saleem_local_cache.db"); c.execute("UPDATE repairs SET status=? WHERE id=?", (ns,r)); c.commit(); c.close()
                if on: requests.patch(f"{URL}/repairs?id=eq.{r}", headers=H, json={"status":ns})
                st.rerun()
            if st.button("حذف", key=f"dr{r}"):
                c = sqlite3.connect("saleem_local_cache.db"); c.execute("DELETE FROM repairs WHERE id=?", (r,)); c.commit(); c.close()
                if on: requests.delete(f"{URL}/repairs?id=eq.{r}", headers=H)
                st.rerun()
