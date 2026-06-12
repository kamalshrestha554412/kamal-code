import streamlit as st
import pandas as pd
import os, shutil
st.set_page_config(page_title="व्यवस्थापन", layout="wide")
if not st.session_state.get("logged_in", False): st.warning("लगइन गर्नुहोस्"); st.stop()
USER = st.session_state.current_user
CSV = f"sales_{USER}.csv"
def load():
    if os.path.exists(CSV): return pd.read_csv(CSV)
    return pd.DataFrame()
def safe(v): return "" if pd.isna(v) else str(v)
st.title("⚙️ व्यवस्थापन")
df = load()
c1,c2,c3 = st.columns(3)
c1.metric("📊 कुल बिल", len(df))
c2.metric("💰 कुल रकम", f"रू. {df['रकम'].sum():,.2f}" if not df.empty else "०")
c3.metric("📸 फोटो सहित", sum(1 for p in df['फोटो'] if safe(p)) if not df.empty else 0)
st.divider()
if st.button("🗑️ सबै डाटा मेट्नुहोस्", type="secondary"):
    if os.path.exists(CSV): os.remove(CSV)
    st.success("मेटियो")
    st.rerun()
