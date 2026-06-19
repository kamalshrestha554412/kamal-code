import streamlit as st
import sqlite3

st.set_page_config(page_title="ग्राहक रिपोर्ट", page_icon="👥", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

@st.cache_data(ttl=60)
def get_customer_data(username, customer_name=""):
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    if customer_name:
        c.execute('''SELECT invoice, date, time, amount, payment, photo, notes 
                     FROM sales WHERE username=? AND customer=? ORDER BY date DESC''', (username, customer_name))
        data = c.fetchall()
        c.execute('SELECT SUM(amount), COUNT(*) FROM sales WHERE username=? AND customer=?', (username, customer_name))
        total, count = c.fetchone()
        conn.close()
        return data, total or 0, count or 0
    else:
        c.execute('SELECT DISTINCT customer FROM sales WHERE username=? AND customer!="" ORDER BY customer', (username,))
        customers = [row[0] for row in c.fetchall()]
        conn.close()
        return customers, 0, 0

st.title("👥 ग्राहक रिपोर्ट")

customers, _, _ = get_customer_data(USER)

if not customers:
    st.info("📭 हालसम्म कुनै ग्राहक डाटा छैन")
    st.stop()

selected = st.selectbox("👤 ग्राहक चयन गर्नुहोस्", customers)

if selected:
    data, total, count = get_customer_data(USER, selected)
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 कुल बिक्री", f"रू. {total:,.2f}")
    col2.metric("🧾 बिल संख्या", count)
    col3.metric("📅 पहिलो बिक्री", data[-1][1] if data else "-")
    
    st.divider()
    for row in data:
        inv, date, time, amount, payment, photo, notes = row
        with st.expander(f"🧾 {inv}  |  {date} {time}  |  रू. {amount:,.2f}"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"💳 {payment}")
                if notes: st.write(f"📝 {notes}")
            with col_b:
                if photo and photo.startswith('http'):
                    st.image(photo, width=150)
                else:
                    st.caption("📷 फोटो छैन")
