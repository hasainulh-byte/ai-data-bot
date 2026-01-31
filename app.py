import streamlit as st
import pandas as pd
from groq import Groq
import io
from datetime import datetime

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Efazi - Careem ROD Automation", layout="wide", page_icon="🚀")

# Professional CSS Styling
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #10B981; color: white; font-weight: bold; border: none; }
    .stDownloadButton>button { width: 100%; border-radius: 12px; background-color: #4338CA; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- API SETUP ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API Key missing. Please add GROQ_API_KEY to Streamlit Secrets.")
    st.stop()

# --- HELPER FUNCTIONS (CAREEM ROD LOGIC) ---
def parse_date(d):
    if pd.isna(d) or d == '': return None
    try:
        return pd.to_datetime(str(d).replace("'", ""))
    except:
        return None

def calculate_minutes(end, start):
    if end and start:
        diff = (end - start).total_seconds() / 60
        return round(diff, 2)
    return 0

# --- DASHBOARD HEADER ---
st.title("🚀 Efazi: Careem ROD Report Maker")
st.markdown("Automated Data Processor • Direct ID Matching • Professional RCA Generation")
st.divider()

# --- UPLOAD SECTION ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📍 Source-1")
    st.caption("Tracking & Dates")
    s1_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'], key="s1")

with col2:
    st.subheader("📍 Source-2")
    st.caption("Shipped Qty & Stores")
    s2_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'], key="s2")

with col3:
    st.subheader("📍 Report Base")
    st.caption("Main Rider Sheet")
    base_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'], key="base")

# --- PROCESSING ENGINE ---
if s1_file and s2_file and base_file:
    # Load Data
    @st.cache_data
    def load_data(file):
        return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)

    df_s1 = load_data(s1_file)
    df_s2 = load_data(s2_file)
    df_base = load_data(base_file)

    if st.button("🚀 RUN AUTOMATION"):
        with st.spinner("Efazi is replicating the report structure..."):
            
            # 1. Normalize IDs for VLOOKUP
            df_s1['order_id'] = df_s1.iloc[:, 0].astype(str).str.strip()
            df_s2['order_id'] = df_s2.iloc[:, 0].astype(str).str.strip()
            df_base['order_id'] = df_base.get('order_id', df_base.iloc[:, 0]).astype(str).str.strip()

            # 2. Merge Data (VLOOKUP Logic)
            merged = pd.merge(df_base, df_s1, on='order_id', how='left', suffixes=('', '_s1'))
            merged = pd.merge(merged, df_s2, on='order_id', how='left', suffixes=('', '_s2'))

            # 3. Apply Careem ROD Mathematical Logic
            processed_rows = []
            for _, row in merged.iterrows():
                # Date Parsing
                o_date = parse_date(row.get('order_date', ''))
                p_date = parse_date(row.get('order_process', ''))
                d_end = parse_date(row.get('delivery_ended_at', ''))
                c_assign = parse_date(row.get('captain_assigned_at', ''))
                c_arrive = parse_date(row.get('captain_arrived_for_pickup_at', ''))
                d_start = parse_date(row.get('delivery_started_at', ''))

                # Metrics Calculation
                otp = calculate_minutes(p_date, o_date) # Order to Process
                otd = calculate_minutes(d_end, o_date)  # Order to Delivery
                ota = calculate_minutes(c_assign, o_date) # Order to Assign
                atra = calculate_minutes(c_arrive, c_assign) # Assign to Arrive
                atp = calculate_minutes(d_start, c_arrive)  # Arrive to Pickup
                ptd = calculate_minutes(d_end, d_start)     # Pickup to Delivery
                
                pickup_time = atra + atp
                dist = float(row.get('distance_to_customer_km', 0))

                # Remark Logic
                remark = "On time"
                if otp <= 0: remark = "CS Cancelled/ST rejected"
                elif otd > 90:
                    remark = "LM breach" if otp <= 20 else "Store Breach"
                elif otd <= 0:
                    remark = "Rider Cancelled"

                # RCA Logic
                rca = ""
                if remark == "Store Breach":
                    rca = f"{int(otp)} min taken for store processing."
                elif remark == "LM breach":
                    if ota > 5 and pickup_time > 20: rca = f"{int(ota)} min assigning, {int(pickup_time)} min pickup."
                    elif ota > 5: rca = f"{int(ota)} min taken for assigning."
                    elif ptd > 60: rca = f"{int(ptd)} min pickup to delivery for {dist} KM."
                    else: rca = "Last Mile delay during delivery."

                # Build final dictionary matching your HTML structure
                processed_rows.append({
                    'Order_ID': row['order_id'],
                    'Shipped_Qty': row.get('shipped_qty', 0),
                    'Store_Name': row.get('store_name', ''),
                    'Order_to_Process': otp,
                    'Order_to_Delivery': otd,
                    'Remark': remark,
                    'RCA': rca
                })

            final_df = pd.DataFrame(processed_rows)

            # 4. Show Result & Export
            st.subheader("✅ Report Preview")
            st.dataframe(final_df.head(10), use_container_width=True)
            
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 DOWNLOAD COMPLETED REPORT", data=csv, file_name="Careem_ROD_Final.csv", mime='text/csv')

# --- FOOTER ---
st.divider()
st.caption("Developed by Hasainul | Efazi AI Engine v2.0")
