import streamlit as st
st.set_page_config(page_title="कमल कोड", page_icon="📸", layout="wide")
USERS = {"admin":"admin123","ram":"ram123","sita":"sita123","hari":"hari123"}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if not st.session_state.logged_in:
    st.title("🔐 कमल कोड - बिक्री रेकर्ड")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("प्रयोगकर्ता")
        p = st.text_input("पासवर्ड", type="password")
        if st.button("लगइन"):
            if u in USERS and USERS[u] == p:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.rerun()
            else: st.error("गलत")
    st.stop()
st.title(f"📸 कमल कोड - {st.session_state.current_user}")
with st.sidebar:
    st.write(f"👤 {st.session_state.current_user}")
    if st.button("🚪 लगआउट"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("---")
    st.markdown("📌 **पेजहरू**")
    st.markdown("1️⃣ नयाँ बिक्री\n2️⃣ आजको बिक्री\n3️⃣ सबै बिक्री\n4️⃣ ग्राहक रिपोर्ट\n5️⃣ व्यवस्थापन")
    st.info("📸 फोटोहरू Google Drive मा सुरक्षित हुन्छन्।")
