import streamlit as st
import sqlite3

st.set_page_config(page_title="व्यवस्थापन", page_icon="⚙️", layout="wide")

if not st.session_state.get("logged_in", False):
    st.warning("लगइन गर्नुहोस्")
    st.stop()

USER = st.session_state.current_user

def get_stats():
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*), SUM(amount) FROM sales WHERE username=?', (USER,))
    count, total = c.fetchone()
    conn.close()
    return count or 0, total or 0

def delete_all_data():
    conn = sqlite3.connect('kamal.db')
    c = conn.cursor()
    c.execute('DELETE FROM sales WHERE username=?', (USER,))
    conn.commit()
    conn.close()
    st.cache_data.clear()

st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:1.5rem;">
    <span style="font-size:2rem;">⚙️</span>
    <div>
        <h1 style="margin:0; font-size:1.8rem;">व्यवस्थापन</h1>
        <p style="margin:0; color:#888; font-size:0.9rem;">डाटा जानकारी र सेटिङ</p>
    </div>
</div>
""", unsafe_allow_html=True)

count, total = get_stats()

col1, col2, col3 = st.columns(3)
col1.metric("📊 जम्मा बिल", count)
col2.metric("💰 जम्मा रकम", f"रू. {total:,.2f}" if total else "रू. ०")

conn = sqlite3.connect('kamal.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM sales WHERE username=? AND photo IS NOT NULL AND photo!=""', (USER,))
photo_count = c.fetchone()[0]
conn.close()
col3.metric("📸 फोटो सहित", photo_count)

st.divider()

st.warning("⚠️ यो कार्यले तपाईंको सबै डाटा स्थायी रूपमा मेट्नेछ।")
if st.button("🗑️ सबै डाटा मेट्नुहोस्", type="secondary", use_container_width=True):
    delete_all_data()
    st.success("✅ सबै डाटा मेटियो!")
    st.rerun()

st.caption("📌 डाटा मेटेपछि फिर्ता हुँदैन। कृपया पक्का गर्नुहोस्।")
