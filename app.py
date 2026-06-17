import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(
    page_title="कमल कोड",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== Custom CSS ==========
st.markdown("""
<style>
    /* Main container */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        font-size: 2.2rem;
        margin: 0;
        font-weight: 700;
    }
    .main-header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border: 1px solid #f0f0f0;
        transition: all 0.2s;
    }
    .card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }
    .card-icon {
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .card-title {
        font-weight: 600;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .card-desc {
        color: #666;
        font-size: 0.9rem;
        text-align: center;
    }
    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    /* Login */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2.5rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    .login-container h2 {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    /* Mobile */
    @media (max-width: 640px) {
        .main-header h1 { font-size: 1.6rem; }
        .card { padding: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# ========== Database ==========
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

# ========== Session ==========
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
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1rem;">
        <span style="font-size: 4rem;">📸</span>
        <h1 style="font-size: 2.5rem; margin: 0.5rem 0; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">कमल कोड</h1>
        <p style="color: #666; font-size: 1.1rem;">बिक्री रेकर्ड व्यवस्थापन</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("### 🔐 लगइन")
            username = st.text_input("प्रयोगकर्ता नाम", placeholder="admin / ram / sita / hari")
            password = st.text_input("पासवर्ड", type="password", placeholder="••••••••")
            if st.button("🚀 लगइन गर्नुहोस्", use_container_width=True, type="primary"):
                fullname = verify_user(username, password)
                if fullname:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.user_fullname = fullname
                    st.rerun()
                else:
                    st.error("❌ गलत प्रयोगकर्ता वा पासवर्ड!")
            st.caption("🔑 admin / admin123  |  ram / ram123")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ========== Main ==========
# Header
st.markdown(f"""
<div class="main-header">
    <h1>📸 कमल कोड</h1>
    <p>👤 {st.session_state.user_fullname}  •  @{st.session_state.current_user}</p>
</div>
""", unsafe_allow_html=True)

# Quick Stats
conn = sqlite3.connect('kamal.db')
c = conn.cursor()
c.execute('SELECT COUNT(*), SUM(amount) FROM sales WHERE username=? AND date=?', (st.session_state.current_user, str(datetime.now().date())))
today_count, today_total = c.fetchone()
today_count = today_count or 0
today_total = today_total or 0
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("💰 आजको बिक्री", f"रू. {today_total:,.2f}")
col2.metric("🧾 आजको बिल", today_count)
col3.metric("👤 प्रयोगकर्ता", st.session_state.user_fullname)

st.markdown("---")

# ========== Pages as Cards ==========
st.markdown("### 📍 मुख्य मेनु")

pages = [
    {"icon": "💰", "title": "नयाँ बिक्री", "desc": "बिक्री थप्नुहोस् र फोटो लिनुहोस्", "page": "1_नयाँ_बिक्री"},
    {"icon": "📅", "title": "आजको बिक्री", "desc": "आजको दिनको सारांश", "page": "2_आजको_बिक्री"},
    {"icon": "📜", "title": "सबै बिक्री", "desc": "सबै रेकर्ड हेर्नुहोस् र खोज्नुहोस्", "page": "3_सबै_बिक्री"},
    {"icon": "👥", "title": "ग्राहक रिपोर्ट", "desc": "ग्राहक अनुसार विश्लेषण", "page": "4_ग्राहक_रिपोर्ट"},
    {"icon": "⚙️", "title": "व्यवस्थापन", "desc": "डाटा र सेटिङ", "page": "5_व्यवस्थापन"},
]

# 3 columns layout
cols = st.columns(3)
for i, page in enumerate(pages):
    with cols[i % 3]:
        st.markdown(f"""
        <div class="card">
            <div class="card-icon">{page['icon']}</div>
            <div class="card-title">{page['title']}</div>
            <div class="card-desc">{page['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"खोल्नुहोस् →", key=f"page_{i}"):
            st.switch_page(f"pages/{page['page']}.py")

st.markdown("---")

# Logout
if st.button("🚪 लगआउट", type="secondary"):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.user_fullname = ""
    st.rerun()

st.caption(f"📱 कमल कोड v3.0  •  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
