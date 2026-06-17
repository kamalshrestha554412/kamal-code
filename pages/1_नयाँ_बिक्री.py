import streamlit as st
import sqlite3
from datetime import datetime
import os
import uuid
import io
import json
from PIL import Image
from nepali_date_library import NepaliDate

st.set_page_config(page_title="नयाँ बिक्री", page_icon="💰", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("कृपया पहिले लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

# ========== Database ==========
def get_db():
    return sqlite3.connect('kamal.db', check_same_thread=False)

def generate_invoice():
    today_eng = str(datetime.now().date())
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM sales WHERE username=? AND eng_date=?', (USER, today_eng))
    count = c.fetchone()[0] + 1
    conn.close()
    return f"INV-{datetime.now().strftime('%y%m%d')}-{count:03d}"

def get_nepali_date():
    return NepaliDate.today().format("YYYY-MM-DD")

# ========== Google Drive Upload ==========
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

def upload_photo(image_file, invoice_no):
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
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        return f"https://drive.google.com/thumbnail?id={file['id']}&sz=w400"
    except Exception as e:
        st.warning(f"⚠️ फोटो अपलोड भएन: {str(e)[:80]}")
        return None

# ========== Session State ==========
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

st.title("💰 नयाँ बिक्री")

# नेपाली मिति देखाउने
st.caption(f"📅 नेपाली मिति: {get_nepali_date()}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 रकम थप्नुहोस्")
    st.caption("Enter थिच्नुहोस् वा ➕ बटन थिच्नुहोस्")
    
    def add_callback():
        if st.session_state.get("quick_amt", 0) > 0:
            st.session_state.temp_items.append({
                "रकम": st.session_state.quick_amt,
                "समय": datetime.now().strftime("%H:%M:%S")
            })
            st.session_state.quick_amt = 0.0
    
    st.number_input("रकम (रू.)", key="quick_amt", step=100.0, format="%.2f", on_change=add_callback)
    
    if st.button("➕ थप्नुहोस्", use_container_width=True):
        if st.session_state.quick_amt > 0:
            st.session_state.temp_items.append({"रकम": st.session_state.quick_amt, "समय": datetime.now().strftime("%H:%M:%S")})
            st.session_state.quick_amt = 0.0
            st.rerun()
    
    if st.session_state.temp_items:
        with st.expander(f"📋 थपिएका रकमहरू ({len(st.session_state.temp_items)})", expanded=True):
            total = 0
            for idx, item in enumerate(st.session_state.temp_items):
                total += item['रकम']
                a,b,c = st.columns([3,2,1])
                a.write(f"💰 रू. {item['रकम']:,.2f}")
                b.caption(f"⏰ {item['समय']}")
                c.button("❌", key=f"del_{idx}", on_click=lambda i=idx: st.session_state.temp_items.pop(i))
            st.success(f"### 💰 जम्मा: रू. {total:,.2f}")

with col2:
    st.subheader("📝 बिक्री विवरण")
    customer = st.text_input("👤 ग्राहक (ऐच्छिक)", placeholder="खाली छोड्नुहोस्")
    payment = st.selectbox("💳 भुक्तानी", ["नगद", "QR", "बैंक", "चेक"])
    notes = st.text_area("📝 नोट्स", placeholder="थप जानकारी")
    
    st.markdown("### 📸 फोटो")
    photo = st.camera_input("क्यामेराबाट", key="cam")
    if photo is None:
        photo = st.file_uploader("वा ग्यालरीबाट", type=["jpg","jpeg","png"])

if st.session_state.temp_items and st.button("✅ बिक्री सेभ गर्नुहोस्", type="primary", use_container_width=True):
    inv = generate_invoice()
    total = sum(i["रकम"] for i in st.session_state.temp_items)
    nep_date = get_nepali_date()
    eng_date = str(datetime.now().date())
    
    photo_link = ""
    if photo:
        with st.spinner("📸 फोटो अपलोड..."):
            photo_link = upload_photo(photo, inv) or ""
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO sales (username, eng_date, nep_date, time, invoice, customer, amount, payment, photo, notes)
                 VALUES (?,?,?,?,?,?,?,?,?,?)''',
              (USER, eng_date, nep_date, datetime.now().strftime("%H:%M:%S"),
               inv, customer, total, payment, photo_link, notes))
    conn.commit()
    conn.close()
    
    st.session_state.temp_items = []
    st.success(f"✅ बिक्री सेभ भयो! {inv} | रू. {total:,.2f} | {nep_date}")
    if photo_link:
        st.image(photo_link, width=150)
    st.balloons()
    st.rerun()
else:
    st.info("👈 पहिले रकम थप्नुहोस्")
