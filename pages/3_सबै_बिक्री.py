import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="सबै बिक्री", page_icon="📜", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

@st.cache_data(ttl=60)
def get_all_sales(username, search="", date_filter=""):
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    query = 'SELECT invoice, date, time, customer, amount, payment, photo, notes, id FROM sales WHERE username=?'
    params = [username]
    if search:
        query += ' AND invoice LIKE ?'
        params.append(f'%{search}%')
    if date_filter:
        query += ' AND date=?'
        params.append(date_filter)
    query += ' ORDER BY date DESC, time DESC'
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

def delete_sale(sale_id):
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    c.execute('DELETE FROM sales WHERE id=?', (sale_id,))
    conn.commit()
    conn.close()
    st.cache_data.clear()

st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:1.5rem;">
    <span style="font-size:2rem;">📜</span>
    <div>
        <h1 style="margin:0; font-size:1.8rem;">सबै बिक्री</h1>
        <p style="margin:0; color:#888; font-size:0.9rem;">सबै रेकर्ड एकै ठाउँमा</p>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    search = st.text_input("🔍 इनभ्वाइस खोज्नुहोस्", placeholder="INV-")
with col2:
    date_obj = st.date_input("📅 मिति", value=None)
    date_filter = str(date_obj) if date_obj else ""

data = get_all_sales(USER, search, date_filter)
st.caption(f"📊 जम्मा {len(data)} वटा बिक्री")

for row in data:
    inv, date, time, customer, amount, payment, photo, notes, sale_id = row
    with st.expander(f"🧾 {inv}  •  {date} {time}  •  रू. {amount:,.2f}"):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.write(f"👤 {customer if customer else '-'}")
            st.write(f"💳 {payment}")
            if notes:
                st.write(f"📝 {notes}")
        with col_b:
            if photo and photo.startswith('http'):
                st.image(photo, width=150)
            else:
                st.caption("📷 फोटो छैन")
        if st.button(f"🗑️ मेट्नुहोस्", key=f"del_{sale_id}"):
            delete_sale(sale_id)
            st.success("✅ मेटियो!")
            st.rerun()
