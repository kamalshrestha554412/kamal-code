import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="आजको बिक्री", page_icon="📅", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

@st.cache_data(ttl=60)
def get_today_sales(username):
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    today = str(datetime.now().date())
    c.execute('''SELECT invoice, time, customer, amount, payment, photo, notes 
                 FROM sales WHERE username=? AND date=? ORDER BY time''', (username, today))
    data = c.fetchall()
    conn.close()
    return data

st.title("📅 आजको बिक्री")
st.caption(f"📅 मिति: {datetime.now().strftime('%Y-%m-%d')}")

data = get_today_sales(USER)

if data:
    total = sum(row[3] for row in data)
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 जम्मा", f"रू. {total:,.2f}")
    col2.metric("🧾 बिल", len(data))
    customers = len(set(row[2] for row in data if row[2]))
    col3.metric("👥 ग्राहक", customers)
    
    st.divider()
    
    for row in data:
        inv, time, customer, amount, payment, photo, notes = row
        with st.container():
            a,b = st.columns([2,1])
            with a:
                st.markdown(f"### 🧾 {inv}")
                st.write(f"⏰ {time}")
                st.write(f"👤 {customer if customer else '-'}")
                st.write(f"💰 रू. {amount:,.2f}  |  💳 {payment}")
                if notes:
                    st.caption(f"📝 {notes}")
            with b:
                if photo and photo.startswith('http'):
                    st.image(photo, width=150)
                else:
                    st.caption("📷 फोटो छैन")
            st.divider()
else:
    st.info("📭 आज कुनै बिक्री छैन।")
