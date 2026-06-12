import streamlit as st
import pandas as pd
from datetime import datetime
import os
st.set_page_config(page_title="आजको बिक्री", layout="wide")
if not st.session_state.get("logged_in", False): st.warning("लगइन गर्नुहोस्"); st.stop()
USER = st.session_state.current_user
CSV = f"sales_{USER}.csv"
def load():
    if os.path.exists(CSV): return pd.read_csv(CSV)
    return pd.DataFrame()
def safe(v): return "" if pd.isna(v) else str(v)
st.title("📅 आजको बिक्री")
df = load()
today = str(datetime.now().date())
tdf = df[df["मिति"] == today] if not df.empty else pd.DataFrame()
if not tdf.empty:
    c1,c2,c3 = st.columns(3)
    c1.metric("💰 जम्मा", f"रू. {tdf['रकम'].sum():,.2f}")
    c2.metric("🧾 बिल", len(tdf))
    c3.metric("👥 ग्राहक", tdf['ग्राहक'].nunique())
    for _, row in tdf.iterrows():
        with st.container():
            a,b = st.columns([2,1])
            with a:
                st.markdown(f"### 🧾 {safe(row['इनभ्वाइस'])}")
                st.write(f"👤 {safe(row['ग्राहक']) or '-'}")
                st.write(f"💰 रू. {row['रकम']:,.2f}  💳 {safe(row['भुक्तानी'])}")
                st.caption(f"⏰ {safe(row['समय'])}")
            with b:
                if safe(row['फोटो']):
                    st.image(row['फोटो'], width=200)
                else:
                    st.caption("📷 फोटो छैन")
            st.divider()
else: st.info("आज कुनै बिक्री छैन।")
