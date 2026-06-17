import streamlit as st
import sqlite3
from datetime import datetime
import os
import uuid
import io
import json
from PIL import Image
import streamlit.components.v1 as components
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

# ========== Google Drive Upload with Debug Logs ==========
@st.cache_data(ttl=3600)
def get_drive_creds():
    try:
        from google.oauth2 import service_account
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
        logger.info(f"🔍 GOOGLE_CREDENTIALS_JSON length: {len(creds_json)}")
        
        if not creds_json or len(creds_json) < 50:
            logger.warning("⚠️ GOOGLE_CREDENTIALS_JSON सेट छैन वा गलत छ!")
            return None
        
        creds_info = json.loads(creds_json)
        logger.info("✅ JSON सफलतापूर्वक पढियो")
        return service_account.Credentials.from_service_account_info(
            creds_info, scopes=['https://www.googleapis.com/auth/drive.file']
        )
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON पढ्न सकिएन: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ क्रेडेन्सियल बनाउन सकिएन: {e}")
        return None

def upload_photo(image_file, invoice_no):
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        
        logger.info(f"📸 फोटो अपलोड सुरु: {invoice_no}")
        
        # 1. Credentials check
        creds = get_drive_creds()
        if not creds:
            logger.error("❌ क्रेडेन्सियल छैन")
            return None
        
        # 2. Folder ID check
        folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
        logger.info(f"🔍 GOOGLE_DRIVE_FOLDER_ID: {folder_id}")
        
        if not folder_id:
            logger.error("❌ Folder ID छैन")
            return None
        
        # 3. Drive Service Build
        try:
            drive_service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Drive Service बन्यो")
        except Exception as e:
            logger.error(f"❌ Drive Service बनाउन सकिएन: {e}")
            return None
        
        # 4. Image Processing
        try:
            img = Image.open(image_file)
            img = img.resize((400, 400))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=70)
            img_bytes.seek(0)
            logger.info(f"✅ छवि प्रशोधन भयो: {len(img_bytes.getvalue())} bytes")
        except Exception as e:
            logger.error(f"❌ छवि प्रशोधन सकिएन: {e}")
            return None
        
        # 5. Upload to Drive
        try:
            file_name = f"{invoice_no}_{uuid.uuid4().hex[:6]}.jpg"
            media = MediaIoBaseUpload(img_bytes, mimetype='image/jpeg', resumable=True)
            file_metadata = {'name': file_name, 'parents': [folder_id]}
            
            file = drive_service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"✅ फोटो अपलोड भयो! File ID: {file_id}")
            
            photo_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
            return photo_url
            
        except Exception as e:
            logger.error(f"❌ अपलोड असफल: {e}")
            return None
            
    except Exception as e:
        logger.error(f"❌ अज्ञात त्रुटि: {e}")
        return None

# ========== Session State ==========
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

st.title("💰 नयाँ बिक्री")
st.caption(f"📅 मिति: {datetime.now().strftime('%Y-%m-%d')}")

col1, col2 = st.columns([1, 1])

# ========== COLUMN 1: रकम थप्ने (number_input) ==========
with col1:
    st.subheader("📊 रकम थप्नुहोस्")
    st.caption("रकम लेख्नुहोस् वा ▲/▼ बटन प्रयोग गर्नुहोस्")
    
    # संख्या बाकस (number_input)
    amount = st.number_input(
        "रकम (रू.)",
        min_value=0.0,
        step=100.0,
        format="%.2f",
        key="amount_number"
    )
    
    # थप्ने बटन
    if st.button("➕ थप्नुहोस्", use_container_width=True):
        if amount > 0:
            st.session_state.temp_items.append({
                "रकम": amount,
                "समय": datetime.now().strftime("%H:%M:%S")
            })
            # थपेपछि number_input 0.0 मा रिसेट गर्न
            # (Streamlit को session_state मा सेट गर्न सकिँदैन, तर सकिन्छ)
            st.rerun()
        else:
            st.warning("⚠️ कृपया ० भन्दा बढी रकम राख्नुहोस्।")
    
    # थपिएका रकमहरूको सूची
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
    else:
        st.info("📭 अहिलेसम्म कुनै रकम थपिएको छैन")

# ========== COLUMN 2: बिक्री विवरण र फोटो ==========
with col2:
    st.subheader("📝 बिक्री विवरण")
    customer = st.text_input("👤 ग्राहक (ऐच्छिक)", placeholder="खाली छोड्नुहोस्")
    payment = st.selectbox("💳 भुक्तानी", ["नगद", "QR", "बैंक", "चेक"])
    notes = st.text_area("📝 नोट्स", placeholder="थप जानकारी", height=80)
    
    st.markdown("### 📸 फोटो")
    st.caption("मोबाइलको पछाडिको क्यामेरा खुल्छ")
    
    # HTML क्यामेरा (पछाडिको)
    components.html("""
        <input type="file" accept="image/*" capture="environment" id="camInput" 
               style="width:100%; padding:12px; border:2px solid #4CAF50; border-radius:10px; cursor:pointer; font-size:16px;">
        <p style="font-size:12px; color:#888; text-align:center; margin-top:5px;">
            📸 पछाडिको क्यामेरा • फोटो छान्नुहोस्
        </p>
    """, height=100)
    
    photo = st.file_uploader("वा ग्यालरीबाट", type=["jpg","jpeg","png"], key="photo_upload")
    
    # फोटो पूर्वावलोकन
    if photo:
        st.image(photo, caption="📸 चयन गरिएको फोटो", width=200)

# ========== Save Button ==========
st.markdown("---")

if st.session_state.temp_items:
    if st.button("✅ बिक्री सेभ गर्नुहोस्", type="primary", use_container_width=True):
        inv = generate_invoice()
        total = sum(i["रकम"] for i in st.session_state.temp_items)
        today = str(datetime.now().date())
        
        logger.info(f"📝 नयाँ बिक्री सेभ हुँदै: {inv}")
        
        # फोटो अपलोड
        photo_link = ""
        if photo:
            with st.spinner("📸 फोटो अपलोड..."):
                logger.info("📸 फोटो अपलोड सुरु...")
                photo_link = upload_photo(photo, inv) or ""
                if photo_link:
                    logger.info(f"✅ फोटो लिङ्क: {photo_link[:50]}...")
                else:
                    logger.warning("⚠️ फोटो अपलोड भएन")
        else:
            logger.info("📸 फोटो छैन (खिचिएको छैन)")
        
        # डाटाबेसमा सेभ
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO sales (username, date, time, invoice, customer, amount, payment, photo, notes)
                     VALUES (?,?,?,?,?,?,?,?,?)''',
                  (USER, today, datetime.now().strftime("%H:%M:%S"),
                   inv, customer, total, payment, photo_link, notes))
        conn.commit()
        conn.close()
        
        st.session_state.temp_items = []
        
        logger.info(f"✅ बिक्री सेभ भयो: {inv}")
        
        st.balloons()
        st.success(f"✅ बिक्री सेभ भयो!\n\n🧾 {inv}\n💰 रू. {total:,.2f}")
        if photo_link:
            st.image(photo_link, caption="📸 अपलोड गरिएको फोटो", width=200)
            st.success("✅ फोटो पनि सेभ भयो!")
        else:
            st.warning("⚠️ फोटो सेभ भएन। कृपया Render Logs हेर्नुहोस्।")
        st.rerun()
else:
    st.info("👈 पहिले रकम थप्नुहोस्")
