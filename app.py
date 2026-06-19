import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px
import pandas as pd

st.set_page_config(
    page_title="कमल कोड",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS ==========
st.markdown("""
<style>
    /* Main */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .main-header h1 { font-size: 2rem; margin: 0; font-weight: 700; }
    .main-header p { margin: 0; opacity: 0.9; font-size: 0.95rem; }
    .main-header .user-info { text-align: right; }
    
    /* Cards */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #667eea;
        margin-bottom: 0.5rem;
        transition: all 0.2s;
    }
    .stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
    .stat-card .label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-card .value { font-size: 1.8rem; font-weight: 700; color: #1a1a2e; margin-top: 4px; }
    .stat-card .sub { font-size: 0.8rem; color: #999; margin-top: 2px; }
    
    .stat-card.green { border-left-color: #2ecc71; }
    .stat-card.orange { border-left-color: #f39c12; }
    .stat-card.red { border-left-color: #e74c3c; }
    .stat-card.purple { border-left-color: #9b59b6; }
    
    /* Menu Cards */
    .menu-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        cursor: pointer;
        transition: all 0.2s;
        height: 100%;
    }
    .menu-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        border-color: #667eea;
    }
    .menu-card .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .menu-card .title { font-weight: 600; font-size: 1rem; }
    .menu-card .desc { font-size: 0.8rem; color: #888; margin-top: 4px; }
    
    /* Divider */
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1a1a2e;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-title span { background: #667eea; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; }
    
    /* Responsive */
    @media (max-width: 640px) {
        .main-header { flex-direction: column; text-align: center; }
        .main-header .user-info { text-align: center; margin-top: 10px; }
        .stat-card .value { font-size: 1.4rem; }
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
    <div style="text-align: center; padding: 4rem 1rem;">
        <span style="font-size: 4rem;">📸</span>
        <h1 style="font-size: 2.5rem; margin: 0.5rem 0; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">कमल कोड</h1>
        <p style="color: #666; font-size: 1.1rem;">बिक्री रेकर्ड व्यवस्थापन</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### 🔐 लगइन")
            username = st.text_input("प्रयोगकर्ता नाम", placeholder="admin / ram / sita / hari")
            password = st.text_input("पासवर्ड", type="password", placeholder="••••••••")
            if st.button("🚀 लगइन", use_container_width=True, type="primary"):
                fullname = verify_user(username, password)
                if fullname:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.user_fullname = fullname
                    st.rerun()
                else:
                    st.error("❌ गलत प्रयोगकर्ता वा पासवर्ड!")
    st.stop()

# ========== Main Dashboard ==========
# Header
st.markdown(f"""
<div class="main-header">
    <div>
        <h1>📸 कमल कोड</h1>
        <p>बिक्री रेकर्ड ड्यासबोर्ड</p>
    </div>
    <div class="user-info">
        <div style="font-size: 1.1rem; font-weight: 500;">👤 {st.session_state.user_fullname}</div>
        <div style="font-size: 0.8rem; opacity: 0.8;">@{st.session_state.current_user}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ========== Stats ==========
conn = sqlite3.connect('kamal.db')
c = conn.cursor()
today = str(datetime.now().date())

# Today
c.execute('SELECT COUNT(*), SUM(amount) FROM sales WHERE username=? AND date=?', (st.session_state.current_user, today))
today_count, today_total = c.fetchone()
today_count = today_count or 0
today_total = today_total or 0

# This Month
month = datetime.now().strftime('%Y-%m')
c.execute('SELECT COUNT(*), SUM(amount) FROM sales WHERE username=? AND date LIKE ?', (st.session_state.current_user, f'{month}%'))
month_count, month_total = c.fetchone()
month_count = month_count or 0
month_total = month_total or 0

# Total
c.execute('SELECT COUNT(*), SUM(amount) FROM sales WHERE username=?', (st.session_state.current_user,))
total_count, total_amount = c.fetchone()
total_count = total_count or 0
total_amount = total_amount or 0

# Photo count
c.execute('SELECT COUNT(*) FROM sales WHERE username=? AND photo IS NOT NULL AND photo!=""', (st.session_state.current_user,))
photo_count = c.fetchone()[0] or 0
conn.close()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="label">💰 आजको बिक्री</div>
        <div class="value">रू. {today_total:,.2f}</div>
        <div class="sub">{today_count} वटा बिल</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stat-card green">
        <div class="label">📅 यस महिना</div>
        <div class="value">रू. {month_total:,.2f}</div>
        <div class="sub">{month_count} वटा बिल</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="stat-card purple">
        <div class="label">📊 कुल बिक्री</div>
        <div class="value">रू. {total_amount:,.2f}</div>
        <div class="sub">{total_count} वटा बिल</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="stat-card orange">
        <div class="label">📸 फोटो सहित</div>
        <div class="value">{photo_count}</div>
        <div class="sub">{total_count - photo_count} वटा फोटो बिना</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== Quick Menu ==========
st.markdown('<div class="section-title"><span>📌</span> द्रुत मेनु</div>', unsafe_allow_html=True)

menu_items = [
    {"icon": "💰", "title": "नयाँ बिक्री", "desc": "बिक्री थप्नुहोस् र फोटो लिनुहोस्", "page": "1_नयाँ_बिक्री"},
    {"icon": "📅", "title": "आजको बिक्री", "desc": "आजको दिनको सारांश", "page": "2_आजको_बिक्री"},
    {"icon": "📜", "title": "सबै बिक्री", "desc": "सबै रेकर्ड हेर्नुहोस्", "page": "3_सबै_बिक्री"},
    {"icon": "👥", "title": "ग्राहक रिपोर्ट", "desc": "ग्राहक अनुसार विश्लेषण", "page": "4_ग्राहक_रिपोर्ट"},
    {"icon": "⚙️", "title": "व्यवस्थापन", "desc": "डाटा र सेटिङ", "page": "5_व्यवस्थापन"},
]

cols = st.columns(5)
for i, item in enumerate(menu_items):
    with cols[i]:
        st.markdown(f"""
        <div class="menu-card">
            <div class="icon">{item['icon']}</div>
            <div class="title">{item['title']}</div>
            <div class="desc">{item['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"खोल्नुहोस् →", key=f"menu_{i}", use_container_width=True):
            st.switch_page(f"pages/{item['page']}.py")

st.markdown("---")

# ========== Recent Sales ==========
st.markdown('<div class="section-title"><span>🕐</span> हालैका बिक्रीहरू</div>', unsafe_allow_html=True)

conn = sqlite3.connect('kamal.db')
c = conn.cursor()
c.execute('SELECT invoice, date, time, customer, amount, payment FROM sales WHERE username=? ORDER BY date DESC, time DESC LIMIT 5', (st.session_state.current_user,))
recent = c.fetchall()
conn.close()

if recent:
    for row in recent:
        inv, date, time, customer, amount, payment = row
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"**🧾 {inv}**")
            st.caption(f"{date} {time}")
        with col2:
            st.write(f"👤 {customer if customer else '-'}")
            st.write(f"💳 {payment}")
        with col3:
            st.write(f"💰 रू. {amount:,.2f}")
        st.divider()
else:
    st.info("📭 हालसम्म कुनै बिक्री छैन")

# ========== Logout ==========
if st.button("🚪 लगआउट", type="secondary", use_container_width=False):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.user_fullname = ""
    st.rerun()

st.caption(f"📱 कमल कोड v4.0  •  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
