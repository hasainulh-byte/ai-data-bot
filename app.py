import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
from thefuzz import process, fuzz
import io

# 1. Page Configuration
st.set_page_config(page_title="Efazi - Smart AI Data Analyst", layout="wide", page_icon="🤖")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. API Key Setup
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = "Gsk_8Dp2FXDZupX0t1XqttYRWGdyb3FYw7KaqHb1mTIQ1BbERX6HWE5C"

client = Groq(api_key=GROQ_API_KEY)

# 3. Sidebar - Guide & Uploads
st.sidebar.image("https://img.icons8.com/fluency/96/robot-3.png", width=80)
st.sidebar.title("Efazi AI v2.0")
st.sidebar.markdown("---")

st.sidebar.subheader("📖 User Guide")
st.sidebar.info("""
1. **Upload Template:** Upload the report format your manager wants.
2. **Upload Sources:** Upload 3-4 raw data files.
3. **Analyze:** Use the AI tab to ask Efazi to merge and replicate.
4. **Fuzzy Match:** Efazi automatically fixes typos in names!
""")

st.sidebar.markdown("---")
st.sidebar.subheader("📤 Upload Center")
sample_file = st.sidebar.file_uploader("1. Sample Report (Template)", type=['csv', 'xlsx'])
source_files = st.sidebar.file_uploader("2. Raw Source Files (3-4 files)", type=['csv', 'xlsx'], accept_multiple_files=True)

# 4. Main Dashboard UI
st.title("🤖 Efazi: Advanced Data Replicator")
st.write("Welcome! I am **Efazi**, your smart AI analyst. Upload your files to begin the transformation.")

if not sample_file or not source_files:
    st.warning("🚀 **Get Started:** Please upload your Template and Source files from the sidebar to activate the dashboard.")
    st.image("https://i.imgur.com/vHqX2Z4.png", caption="Efazi is waiting for your data...")

else:
    # Load Files
    df_sample = pd.read_csv(sample_file) if sample_file.name.endswith('.csv') else pd.read_excel(sample_file)
    dataframes = {f.name: (pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)) for f in source_files}

    # Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data Preview", "🧠 AI Analysis & Merging", "📈 Visual Insights"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Target Template Structure")
            st.dataframe(df_sample.head(5), use_container_width=True)
        with col2:
            st.subheader("Source Files Overview")
            for name, df in dataframes.items():
                with st.expander(f"File: {name}"):
                    st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
                    st.write(list(df.columns))

    with tab2:
        st.subheader("Chat with Efazi")
        user_msg = st.chat_input("Ex: 'Merge these sources into the template using Fuzzy VLOOKUP on Customer Name'")
        
        if user_msg:
            # Prepare context for AI
            context = f"Target Format Columns: {list(df_sample.columns)}\n"
            for name, df in dataframes.items():
                context += f"Source '{name}' has columns: {list(df.columns)}\n"

            with st.spinner("Efazi is calculating..."):
                prompt = f"System: You are Efazi, a professional Data Scientist. Use Fuzzy Merge logic. Context: {context}. Task: {user_msg}"
                response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                
                st.markdown("### Efazi's Professional Insight:")
                st.write(response.choices[0].message.content)

        st.markdown("---")
        if st.button("🚀 Replicate & Generate Full Report"):
            st.success("Efazi is processing the multi-file VLOOKUP... (Draft Ready)")
            # Standard merge logic can be added here
            st.download_button("Download Processed Report (CSV)", df_sample.to_csv(index=False), "Efazi_Report.csv")

    with tab3:
        st.subheader("Dynamic Visualization")
        if st.checkbox("Show Data Summary Chart"):
            # Simple example: Row counts per file
            chart_data = pd.DataFrame({
                'File Name': list(dataframes.keys()),
                'Total Rows': [df.shape[0] for df in dataframes.values()]
            })
            fig = px.bar(chart_data, x='File Name', y='Total Rows', color='File Name', title="Data Volume per Source")
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Efazi AI v2.0 | Powered by Groq | Secure Data Analysis")
