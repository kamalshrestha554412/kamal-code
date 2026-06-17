import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(page_title="कमल कोड", page_icon="🚀", layout="wide")

# ========== Database Setup ==========
def init_db():
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        full_name TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        date TEXT,
        time TEXT,
        invoice TEXT,
        customer TEXT,
        amount REAL,
        payment TEXT,
        photo TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    default_users = [
        ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'Admin', 'admin'),
        ('ram', hashlib.sha256('ram123'.encode()).hexdigest(), 'Ram Sharma', 'staff'),
        ('sita', hashlib.sha256('sita123'.encode()).hexdigest(), 'Sita Devi', 'staff'),
        ('hari', hashlib.sha256('hari123'.encode()).hexdigest(), 'Hari Thapa', 'staff')
    ]
    for u, p, n, r in default_users:
        c.execute('INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES (?,?,?,?)', (u,p,n,r))
    conn.commit()
    conn.close()

init_db()

# ========== Session State ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "user_fullname" not in st.session_state:
    st.session_state.user_fullname = ""

# ========== Login ==========
def verify_user(username, password):
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute('SELECT full_name FROM users WHERE username=? AND password=?', (username, hashed))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

if not st.session_state.logged_in:
    st.title("🚀 कमल कोड - बिक्री रेकर्ड")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown("### 🔐 लगइन गर्नुहोस्")
            username = st.text_input("प्रयोगकर्ता नाम")
            password = st.text_input("पासवर्ड", type="password")
            if st.button("लगइन", use_container_width=True, type="primary"):
                fullname = verify_user(username, password)
                if fullname:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.user_fullname = fullname
                    st.rerun()
                else:
                    st.error("❌ गलत प्रयोगकर्ता वा पासवर्ड!")
    st.stop()

# ========== Main Page ==========
st.markdown(f"### 🚀 कमल कोड - स्वागत छ, {st.session_state.user_fullname}!")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_fullname}")
    st.markdown(f"*@{st.session_state.current_user}*")
    st.markdown("---")
    st.markdown("### 📍 पेजहरू")
    st.markdown("1️⃣ **नयाँ बिक्री** - बिक्री थप्ने")
    st.markdown("2️⃣ **आजको बिक्री** - दैनिक रिपोर्ट")
    st.markdown("3️⃣ **सबै बिक्री** - खोज/फिल्टर")
    st.markdown("4️⃣ **ग्राहक रिपोर्ट** - ग्राहक अनुसार")
    st.markdown("5️⃣ **व्यवस्थापन** - डाटा सेटिङ")
    st.markdown("---")
    if st.button("🚪 लगआउट", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state.user_fullname = ""
        st.rerun()

st.info("👈 बायाँपट्टिको साइडबारबाट पेज चयन गर्नुहोस्।")
st.success("📌 **नयाँ बिक्री** पेजमा गएर रकम थप्नुहोस् र फोटो लिनुहोस्।")

# Performance Info
with st.expander("⚡ एपको जानकारी"):
    st.caption("✅ SQLite Database (छिटो)")
    st.caption("✅ Caching Enabled")
    st.caption("✅ Google Drive Ready (यदि सेट छ भने)")
    st.caption("✅ UptimeRobot Friendly")
