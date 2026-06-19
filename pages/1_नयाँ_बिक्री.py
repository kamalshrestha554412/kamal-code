import streamlit as st
import sqlite3
from datetime import datetime
import os
import uuid
import io
import json
from PIL import Image

st.set_page_config(page_title="नयाँ बिक्री", page_icon="💰", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

# ========== CSS ==========
st.markdown("""
<style>
    .form-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        margin-bottom: 1rem;
    }
    .total-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .total-box h2 { margin: 0; font-size: 2rem; }
    .total-box p { margin: 0; opacity: 0.9; }
    .item-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        border-bottom: 1px solid #f0f0f0;
        align-items: center;
    }
    .item-row:hover { background: #f9f9f9; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ========== Database ==========
def get_db():
    return sqlite3.connect('kamal.db', check_same_thread=False)

def generate_invoice():
    today = str(datetime.now().date())
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM sales WHERE username=? AND date=?', (USER, today))
    count = c.fetchone()[0] + 1
    conn.close()
    return f"INV-{datetime.now().strftime('%y%m%d')}-{count:03d}"

# ========== Google Drive ==========
@st.cache_data(ttl=3600)
def get_drive_creds():
    try:
        from google.oauth2 import service_account
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
        if not creds_json:
            return None
        creds_info = json.loads(creds_json)
        return service_account.Credentials.from_service_account_info(
            creds_info, scopes=['https://www.googleapis.com/auth/drive.file']
        )
    except:
        return None

def upload_photo_drive(image_file, invoice_no):
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload

        creds = get_drive_creds()
        if not creds:
            return None

        folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
        if not folder_id:
            return None

        drive_service = build('drive', 'v3', credentials=creds)
        
        img = Image.open(image_file)
        img = img.resize((400, 400))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=70)
        img_bytes.seek(0)

        file_name = f"{invoice_no}_{uuid.uuid4().hex[:6]}.jpg"
        media = MediaIoBaseUpload(img_bytes, mimetype='image/jpeg', resumable=True)
        file_metadata = {'name': file_name, 'parents': [folder_id]}

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return f"https://drive.google.com/thumbnail?id={file['id']}&sz=w400"

    except Exception as e:
        return None

# ========== Session ==========
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

st.title("💰 नयाँ बिक्री")
st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d')}")

# === Amount Section ===
st.markdown('<div class="form-card">', unsafe_allow_html=True)
st.subheader("📊 रकम थप्नुहोस्")

col1, col2 = st.columns([3, 1])
with col1:
    amount = st.number_input(
        "रकम (रू.)",
        min_value=0.0,
        step=100.0,
        format="%.2f",
        key="amount_new"
    )
with col2:
    if st.button("➕ थप्नुहोस्", use_container_width=True):
        if amount > 0:
            st.session_state.temp_items.append({
                "रकम": amount,
                "समय": datetime.now().strftime("%H:%M:%S")
            })
            st.rerun()
        else:
            st.warning("० भन्दा बढी रकम राख्नुहोस्")

if st.session_state.temp_items:
    total = 0
    for idx, item in enumerate(st.session_state.temp_items):
        total += item['रकम']
        col_a, col_b, col_c = st.columns([3, 2, 1])
        col_a.write(f"💰 रू. {item['रकम']:,.2f}")
        col_b.caption(f"⏰ {item['समय']}")
        with col_c:
            if st.button("✕", key=f"del_{idx}"):
                st.session_state.temp_items.pop(idx)
                st.rerun()
    
    st.markdown(f"""
    <div class="total-box">
        <p>📊 कुल जम्मा</p>
        <h2>रू. {total:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("📭 अहिलेसम्म कुनै रकम थपिएको छैन")
st.markdown('</div>', unsafe_allow_html=True)

# === Customer & Photo ===
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.subheader("👤 ग्राहक विवरण")
    customer = st.text_input("ग्राहकको नाम", placeholder="ऐच्छिक")
    payment = st.selectbox("भुक्तानी विधि", ["नगद", "QR", "बैंक", "चेक"])
    notes = st.text_area("नोट्स", placeholder="थप जानकारी", height=100)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.subheader("📸 फोटो")
    st.caption("बिक्रीको प्रमाणको लागि फोटो लिनुहोस्")
    photo = st.camera_input("क्यामेराबाट", key="cam_new2")
    if photo is None:
        photo = st.file_uploader("वा ग्यालरीबाट", type=["jpg", "jpeg", "png"], key="upload_new2")
    if photo:
        st.image(photo, caption="चयन गरिएको फोटो", width=200)
    st.markdown('</div>', unsafe_allow_html=True)

# === Save ===
st.markdown("---")

if st.session_state.temp_items:
    if st.button("✅ बिक्री सेभ गर्नुहोस्", type="primary", use_container_width=True):
        inv = generate_invoice()
        total = sum(i["रकम"] for i in st.session_state.temp_items)
        
        photo_link = ""
        if photo:
            with st.spinner("📸 फोटो अपलोड..."):
                photo_link = upload_photo_drive(photo, inv) or ""

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO sales (username, date, time, invoice, customer, amount, payment, photo, notes)
                     VALUES (?,?,?,?,?,?,?,?,?)''',
                  (USER, str(datetime.now().date()), datetime.now().strftime("%H:%M:%S"),
                   inv, customer, total, payment, photo_link, notes))
        conn.commit()
        conn.close()

        st.session_state.temp_items = []
        st.balloons()
        st.success(f"✅ बिक्री सेभ भयो!\n\n🧾 {inv}\n💰 रू. {total:,.2f}")
        if photo_link:
            st.image(photo_link, caption="अपलोड गरिएको फोटो", width=150)
        st.rerun()
else:
    st.info("👈 पहिले रकम थप्नुहोस्")
