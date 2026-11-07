import streamlit as st
import sqlite3
import streamlit.components.v1 as components

def show_mgmt(supabase, is_online):
    if st.button("العودة للشاشة الرئيسية"):
        st.session_state.page = 'welcome'
        st.rerun()

    sec = st.radio("القسم:", ["قسم الصيانة", "قسم المخزن"], horizontal=True, label_visibility="collapsed")

    if sec == "قسم المخزن":
        st.markdown("### إضافة صنف للمخزن")
        pn = st.text_input("اسم الصنف", key="in_n")
        c1, c2 = st.columns(2)
        pq = c1.number_input("الكمية", min_value=1, step=1, key="in_q")
        pp = c2.number_input("السعر (د.ل)", min_value=0.0, step=5.0, key="in_p")
        if st.button("حفظ الصنف") and pn.strip():
            if is_online:
                supabase.table("inventory").insert({"part_name": pn.strip(), "quantity": int(pq), "price": float(pp)}).execute()
            else:
                conn = sqlite3.connect("saleem_local_cache.db")
                conn.execute("INSERT INTO inventory (part_name,quantity,price,synced) VALUES (?,?,?,0)", (pn.strip(), int(pq), float(pp)))
                conn.commit()
                conn.close()
            st.rerun()

        conn = sqlite3.connect("saleem_local_cache.db")
        rows = conn.execute("SELECT id, part_name, quantity, price FROM inventory ORDER BY id DESC").fetchall()
        conn.close()
        for r in rows:
            st.markdown(f"<div class='card'><b>{r[1]}</b> | الكمية: <b>{r[2]}</b> | السعر: <b>{r[3]} د.ل</b></div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            if b1.button("زيادة", key=f"a_{r[0]}"):
                if is_online:
                    supabase.table("inventory").update({"quantity": int(r[2]) + 1}).eq("id", int(r[0])).execute()
                else:
                    conn = sqlite3.connect("saleem_local_cache.db")
                    conn.execute("UPDATE inventory SET quantity=quantity+1 WHERE id=?", (int(r[0]),))
                    conn.commit()
                    conn.close()
                st.rerun()
            if b2.button("سحب", key=f"u_{r[0]}") and r[2] > 0:
                if is_online:
                    supabase.table("inventory").update({"quantity": int(r[2]) - 1}).eq("id", int(r[0])).execute()
                else:
                    conn = sqlite3.connect("saleem_local_cache.db")
                    conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=?", (int(r[0]),))
                    conn.commit()
                    conn.close()
                st.rerun()
            if b3.button("حذف", key=f"di_{r[0]}"):
                if is_online:
                    supabase.table("inventory").delete().eq("id", int(r[0])).execute()
                else:
                    conn = sqlite3.connect("saleem_local_cache.db")
                    conn.execute("DELETE FROM inventory WHERE id=?", (int(r[0]),))
                    conn.commit()
                    conn.close()
                st.rerun()

    else:
        st.markdown("### تسجيل جهاز صيانة")
        cn = st.text_input("اسم الزبون", key="cn")
        cp = st.text_input("رقم الهاتف", key="cp")
        cd = st.text_input("نوع الجهاز", key="cd")
        ci = st.text_input("وصف العطل", key="ci")
        c1, c2 = st.columns(2)
        cc = c1.number_input("السعر للزبون (د.ل)", min_value=0.0, step=5.0, key="cc")
        cpc = c2.number_input("تكلفة القطعة (د.ل)", min_value=0.0, step=5.0, key="cpc")
        cs = st.selectbox("الحالة", ["قيد الانتظار", "تحت الصيانة", "تمت صيانته", "تم تسليمه"], key="cs")
        if st.button("حفظ الجهاز") and cn.strip() and cd.strip():
            if is_online:
                supabase.table("repairs").insert({"client_name": cn, "phone_number": cp, "device_model": cd, "issue": ci, "cost": cc, "part_cost": cpc, "status": cs}).execute()
            else:
                conn = sqlite3.connect("saleem_local_cache.db")
                conn.execute("INSERT INTO repairs (client_name,phone_number,device_model,issue,cost,part_cost,status,date_added,synced) VALUES (?,?,?,?,?,?,?,date('now'),0)", (cn, cp, cd, ci, cc, cpc, cs))
                conn.commit()
                conn.close()
            st.rerun()

        conn = sqlite3.connect("saleem_local_cache.db")
        repairs = conn.execute("SELECT id, client_name, phone_number, device_model, issue, cost, status FROM repairs ORDER BY id DESC").fetchall()
        conn.close()
        for r in repairs:
            st.markdown(f"<div class='card'><b>#{r[0]} | {r[1]} ({r[3]})</b><br>الهاتف: {r[2]} | العطل: {r[4]} | السعر: {r[5]} د.ل</div>", unsafe_allow_html=True)
            st_list = ["قيد الانتظار", "تحت الصيانة", "تمت صيانته", "تم تسليمه"]
            ns = st.selectbox("الحالة", st_list, index=st_list.index(r[6]) if r[6] in st_list else 0, key=f"s_{r[0]}")
            if ns != r[6]:
                if is_online:
                    supabase.table("repairs").update({"status": ns}).eq("id", int(r[0])).execute()
                else:
                    conn = sqlite3.connect("saleem_local_cache.db")
                    conn.execute("UPDATE repairs SET status=? WHERE id=?", (ns, int(r[0])))
                    conn.commit()
                    conn.close()
                st.rerun()
            c_p, c_d = st.columns(2)
            with c_p:
                btn = f'<button onclick="var w=window.open(\'\',\'\',\'width=400,height=400\');w.document.write(\'<div dir=rtl style=text-align:center><h2>وصل #{r[0]}</h2><p>{r[1]} - {r[3]}</p><p>{r[5]} د.ل</p></div>\');w.print();w.close();" style="background:#00807d;color:white;border:none;padding:14px;border-radius:16px;width:100%;min-height:68px;font-weight:bold;font-size:24px;cursor:pointer;margin-top:8px;">طباعة</button>'
                components.html(btn, height=85)
            if c_d.button("حذف", key=f"d_{r[0]}"):
                if is_online:
                    supabase.table("repairs").delete().eq("id", int(r[0])).execute()
                else:
                    conn = sqlite3.connect("saleem_local_cache.db")
                    conn.execute("DELETE FROM repairs WHERE id=?", (int(r[0]),))
                    conn.commit()
                    conn.close()
                st.rerun()