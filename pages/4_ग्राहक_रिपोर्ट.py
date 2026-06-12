import streamlit as st
import pandas as pd
import os
st.set_page_config(page_title="ग्राहक रिपोर्ट", layout="wide")
if not st.session_state.get("logged_in", False): st.warning("लगइन गर्नुहोस्"); st.stop()
USER = st.session_state.current_user
CSV = f"sales_{USER}.csv"
def load():
    if os.path.exists(CSV): return pd.read_csv(CSV)
    return pd.DataFrame()
def safe(v): return "" if pd.isna(v) else str(v)
st.title("👥 ग्राहक रिपोर्ट")
df = load()
if not df.empty:
    customers = [c for c in df["ग्राहक"].unique() if not pd.isna(c) and c]
    if customers:
        sel = st.selectbox("ग्राहक चयन", sorted(customers))
        cdf = df[df["ग्राहक"] == sel]
        c1,c2,c3 = st.columns(3)
        c1.metric("💰 कुल बिक्री", f"रू. {cdf['रकम'].sum():,.2f}")
        c2.metric("🧾 बिल", len(cdf))
        c3.metric("📅 पहिलो", cdf["मिति"].iloc[-1] if not cdf.empty else "-")
        for _, row in cdf.iterrows():
            with st.expander(f"🧾 {safe(row['इनभ्वाइस'])} | {safe(row['मिति'])} | रू. {row['रकम']:,.2f}"):
                a,b = st.columns([2,1])
                with a: st.write(f"⏰ {safe(row['समय'])} | 💳 {safe(row['भुक्तानी'])}")
                with b:
                    if safe(row['फोटो']): st.image(row['फोटो'], width=150)
    else: st.info("कुनै ग्राहक छैन।")
else: st.info("डाटा छैन।")
