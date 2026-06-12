import streamlit as st
import pandas as pd
from datetime import datetime
import os, uuid, io, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image

st.set_page_config(page_title="नयाँ बिक्री", page_icon="💰", layout="wide")
if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्"); st.stop()
USER = st.session_state.current_user

# Google Drive सेटअप
# Render मा हामी secrets.toml वा environment variable प्रयोग गर्छौं
# यहाँ सजिलोको लागि JSON फाइल राख्ने छैनौं, बरु Render को Secret मा राख्छौं
try:
    # Render मा राखिएको सर्भिस अकाउन्ट JSON पढ्ने
    creds_info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON", "{}"))
    if creds_info:
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/drive.file'])
        drive_service = build('drive', 'v3', credentials=creds)
    else:
        st.error("Google Drive क्रेडेन्सियल सेटअप छैन। Render Dashboard मा Environment Variable थप्नुहोस्।")
        st.stop()
except Exception as e:
    st.error(f"Drive क्रेडेन्सियल पढ्न समस्या: {e}")
    st.stop()

FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
if not FOLDER_ID:
    st.error("Google Drive फोल्डर ID सेट छैन।")
    st.stop()

def upload_to_drive(image_file, invoice_no):
    img = Image.open(image_file)
    img = img.resize((600,600))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=80)
    img_bytes.seek(0)
    file_name = f"{invoice_no}_{uuid.uuid4().hex[:6]}.jpg"
    media = MediaIoBaseUpload(img_bytes, mimetype='image/jpeg', resumable=True)
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return f"https://drive.google.com/thumbnail?id={file['id']}&sz=w600"

def delete_from_drive(link):
    import re
    match = re.search(r'id=([^&]+)', link)
    if match:
        drive_service.files().delete(fileId=match.group(1)).execute()

CSV_FILE = f"sales_{USER}.csv"
def load():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["मिति","समय","इनभ्वाइस","ग्राहक","रकम","भुक्तानी","फोटो","नोट्स"])
def save(df):
    df.to_csv(CSV_FILE, index=False)
def gen_invoice():
    today = datetime.now().strftime("%y%m%d")
    df = load()
    cnt = len(df[df["मिति"] == str(datetime.now().date())]) + 1
    return f"INV-{today}-{cnt:03d}"

if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

st.title("💰 नयाँ बिक्री")
c1, c2 = st.columns(2)
with c1:
    st.subheader("रकम थप्नुहोस् (Enter थिचेपछि थपिन्छ)")
    def add_cb():
        if st.session_state.quick_amt > 0:
            st.session_state.temp_items.append({"रकम": st.session_state.quick_amt, "समय": datetime.now().strftime("%H:%M:%S")})
            st.session_state.quick_amt = 0.0
    st.number_input("रकम (रू.)", key="quick_amt", step=100.0, format="%.2f", on_change=add_cb)
    if st.button("➕ थप्नुहोस्"):
        if st.session_state.quick_amt > 0:
            st.session_state.temp_items.append({"रकम": st.session_state.quick_amt, "समय": datetime.now().strftime("%H:%M:%S")})
            st.session_state.quick_amt = 0.0
            st.rerun()
    if st.session_state.temp_items:
        total = 0
        for i, it in enumerate(st.session_state.temp_items):
            total += it["रकम"]
            a,b,c = st.columns([3,2,1])
            a.write(f"💰 रू. {it['रकम']:,.2f}")
            b.caption(f"⏰ {it['समय']}")
            c.button("❌", key=f"del_{i}", on_click=lambda idx=i: st.session_state.temp_items.pop(idx))
        st.success(f"**जम्मा:** रू. {total:,.2f}")
with c2:
    customer = st.text_input("👤 ग्राहक (ऐच्छिक)")
    payment = st.selectbox("💳 भुक्तानी", ["नगद","QR","बैंक","चेक"])
    notes = st.text_area("📝 नोट्स")
    photo = st.camera_input("📸 फोटो खिच्नुहोस्")
    if photo is None: photo = st.file_uploader("वा ग्यालरी", type=["jpg","jpeg","png"])
if st.session_state.temp_items and st.button("✅ बिक्री सेभ गर्नुहोस्", type="primary"):
    inv = gen_invoice()
    link = ""
    if photo:
        with st.spinner("Google Drive मा अपलोड हुँदै..."):
            link = upload_to_drive(photo, inv)
    total = sum(i["रकम"] for i in st.session_state.temp_items)
    df = load()
    new = pd.DataFrame([{
        "मिति": str(datetime.now().date()), "समय": datetime.now().strftime("%H:%M:%S"),
        "इनभ्वाइस": inv, "ग्राहक": customer, "रकम": total, "भुक्तानी": payment,
        "फोटो": link, "नोट्स": notes
    }])
    df = pd.concat([df, new], ignore_index=True)
    save(df)
    st.session_state.temp_items = []
    st.success(f"✅ सेभ भयो! इनभ्वाइस: {inv} | रकम: रू. {total:,.2f}")
    if link:
        st.image(link, width=200)
    st.balloons()
    st.rerun()
