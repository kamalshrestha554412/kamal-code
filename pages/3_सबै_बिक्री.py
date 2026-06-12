import streamlit as st
import pandas as pd
from datetime import datetime
import os
st.set_page_config(page_title="सबै बिक्री", layout="wide")
if not st.session_state.get("logged_in", False): st.warning("लगइन गर्नुहोस्"); st.stop()
USER = st.session_state.current_user
CSV = f"sales_{USER}.csv"
def load():
    if os.path.exists(CSV): return pd.read_csv(CSV)
    return pd.DataFrame()
def save(df): df.to_csv(CSV, index=False)
def safe(v): return "" if pd.isna(v) else str(v)
st.title("📜 सबै बिक्री")
df = load()
if not df.empty:
    search = st.text_input("🔍 इनभ्वाइस")
    filtered = df[df["इनभ्वाइस"].str.contains(search, case=False)] if search else df
    st.caption(f"जम्मा {len(filtered)} वटा")
    for idx, row in filtered.iterrows():
        with st.expander(f"🧾 {safe(row['इनभ्वाइस'])} | {safe(row['मिति'])} | रू. {row['रकम']:,.2f}"):
            a,b = st.columns([2,1])
            with a:
                st.write(f"⏰ {safe(row['समय'])} | 💳 {safe(row['भुक्तानी'])}")
                st.write(f"👤 {safe(row['ग्राहक']) or '-'}")
            with b:
                if safe(row['फोटो']): st.image(row['फोटो'], width=150)
                else: st.caption("📷 फोटो छैन")
            if st.button(f"🗑️ मेट्नुहोस्", key=f"del_{idx}"):
                new_df = df.drop(index=idx).reset_index(drop=True)
                save(new_df); st.success("मेटियो"); st.rerun()
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 CSV डाउनलोड", csv, f"bikri_{datetime.now().date()}.csv")
else: st.info("कुनै डाटा छैन।")
