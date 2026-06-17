import streamlit as st
import sqlite3
from datetime import datetime
import os
import uuid
import io
import json
from PIL import Image
import logging

# ========== Logging Setup ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="नयाँ बिक्री", page_icon="💰", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("कृपया पहिले लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

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

# ========== Google Drive Upload ==========
@st.cache_data(ttl=3600)
def get_drive_creds():
    try:
        from google.oauth2 import service_account
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
        logger.info(f"🔍 GOOGLE_CREDENTIALS_JSON length: {len(creds_json)}")
        if not creds_json or len(creds_json) < 50:
            logger.warning("⚠️ GOOGLE_CREDENTIALS_JSON सेट छैन")
            return None
        creds_info = json.loads(creds_json)
        logger.info("✅ JSON पढियो")
        return service_account.Credentials.from_service_account_info(
            creds_info, scopes=['https://www.googleapis.com/auth/drive.file']
        )
    except Exception as e:
        logger.error(f"❌ क्रेडेन्सियल त्रुटि: {e}")
        return None

def upload_photo(image_file, invoice_no):
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload

        creds = get_drive_creds()
        if not creds:
            return None

        folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
        if not folder_id:
            logger.error("❌ Folder ID छैन")
            return None

        drive_service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Drive Service बन्यो")

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

        file_id = file.get('id')
        logger.info(f"✅ फोटो अपलोड भयो! ID: {file_id}")
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"

    except Exception as e:
        logger.error(f"❌ अपलोड असफल: {e}")
        return None

# ========== Session ==========
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

st.title("💰 नयाँ बिक्री")
st.caption(f"📅 मिति: {datetime.now().strftime('%Y-%m-%d')}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 रकम थप्नुहोस्")
    amount = st.number_input("रकम (रू.)", min_value=0.0, step=100.0, format="%.2f", key="amount_number")
    
    if st.button("➕ थप्नुहोस्", use_container_width=True):
        if amount > 0:
            st.session_state.temp_items.append({
                "रकम": amount,
                "समय": datetime.now().strftime("%H:%M:%S")
            })
            st.rerun()
        else:
            st.warning("⚠️ ० भन्दा बढी रकम राख्नुहोस्")
    
    if st.session_state.temp_items:
        with st.expander(f"📋 थपिएका रकमहरू ({len(st.session_state.temp_items)})", expanded=True):
            total = 0
            for idx, item in enumerate(st.session_state.temp_items):
                total += item['रकम']
                a, b, c = st.columns([3, 2, 1])
                a.write(f"💰 रू. {item['रकम']:,.2f}")
                b.caption(f"⏰ {item['समय']}")
                c.button("❌", key=f"del_{idx}", on_click=lambda i=idx: st.session_state.temp_items.pop(i))
            st.success(f"### 💰 जम्मा: रू. {total:,.2f}")

with col2:
    st.subheader("📝 बिक्री विवरण")
    customer = st.text_input("👤 ग्राहक (ऐच्छिक)")
    payment = st.selectbox("💳 भुक्तानी", ["नगद", "QR", "बैंक", "चेक"])
    notes = st.text_area("📝 नोट्स")
    
    st.markdown("### 📸 फोटो")
    # ✅ सही तरिका: सिधै st.camera_input प्रयोग गर्ने
    photo = st.camera_input("क्यामेराबाट फोटो लिनुहोस्", key="camera_input")
    if photo is None:
        photo = st.file_uploader("वा ग्यालरीबाट", type=["jpg", "jpeg", "png"], key="file_uploader")
    
    if photo:
        st.image(photo, caption="📸 चयन गरिएको फोटो", width=150)

st.markdown("---")

if st.session_state.temp_items:
    if st.button("✅ बिक्री सेभ गर्नुहोस्", type="primary", use_container_width=True):
        inv = generate_invoice()
        total = sum(i["रकम"] for i in st.session_state.temp_items)
        today = str(datetime.now().date())
        
        photo_link = ""
        if photo:
            with st.spinner("📸 फोटो अपलोड..."):
                photo_link = upload_photo(photo, inv) or ""
                if photo_link:
                    logger.info(f"✅ फोटो लिङ्क: {photo_link[:50]}...")
                else:
                    logger.warning("⚠️ फोटो अपलोड भएन")
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO sales (username, date, time, invoice, customer, amount, payment, photo, notes)
                     VALUES (?,?,?,?,?,?,?,?,?)''',
                  (USER, today, datetime.now().strftime("%H:%M:%S"),
                   inv, customer, total, payment, photo_link, notes))
        conn.commit()
        conn.close()
        
        st.session_state.temp_items = []
        st.balloons()
        st.success(f"✅ बिक्री सेभ भयो!\n\n🧾 {inv}\n💰 रू. {total:,.2f}")
        if photo_link:
            st.image(photo_link, caption="📸 अपलोड गरिएको फोटो", width=150)
        st.rerun()
else:
    st.info("👈 पहिले रकम थप्नुहोस्")
