import streamlit as st
import sqlite3
from datetime import datetime
from nepali_date_library import NepaliDate

st.set_page_config(page_title="सबै बिक्री", page_icon="📜", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

@st.cache_data(ttl=60)
def get_all_sales(username, search="", date_filter=""):
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    query = 'SELECT invoice, eng_date, nep_date, time, customer, amount, payment, photo, notes, id FROM sales WHERE username=?'
    params = [username]
    if search:
        query += ' AND invoice LIKE ?'
        params.append(f'%{search}%')
    if date_filter:
        query += ' AND eng_date=?'
        params.append(date_filter)
    query += ' ORDER BY eng_date DESC, time DESC'
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

st.title("📜 सबै बिक्री")

col1, col2 = st.columns(2)
with col1:
    search = st.text_input("🔍 इनभ्वाइस खोज्नुहोस्", placeholder="INV-")
with col2:
    date_obj = st.date_input("📅 मिति (अंग्रेजी)", value=None)
    date_filter = str(date_obj) if date_obj else ""

data = get_all_sales(USER, search, date_filter)
st.caption(f"📊 जम्मा {len(data)} वटा बिक्री")

for row in data:
    inv, eng_date, nep_date, time, customer, amount, payment, photo, notes, sale_id = row
    with st.expander(f"🧾 {inv}  |  {nep_date}  |  रू. {amount:,.2f}"):
        a,b = st.columns([2,1])
        with a:
            st.write(f"📅 {nep_date} ({eng_date}) | ⏰ {time}")
            st.write(f"👤 {customer if customer else '-'}")
            st.write(f"💳 {payment}")
            if notes:
                st.write(f"📝 {notes}")
        with b:
            if photo and photo.startswith('http'):
                st.image(photo, width=150)
            else:
                st.caption("📷 फोटो छैन")
        if st.button(f"🗑️ मेट्नुहोस्", key=f"del_{sale_id}"):
            delete_sale(sale_id)
            st.success("✅ मेटियो!")
            st.rerun()
