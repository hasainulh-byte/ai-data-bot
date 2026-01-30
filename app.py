import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
from thefuzz import process, fuzz
import io

# ১. পেজ সেটআপ (প্রফেশনাল লুক)
st.set_page_config(page_title="Pro AI Data Analyst", layout="wide", page_icon="📊")

# স্টাইলিশ হেডার
st.title("🤖 AI Report Replicator & Smart Merger")
st.markdown("---")

# ২. সিক্রেট থেকে API Key নেওয়া (Streamlit Secrets ব্যবহার করবেন)
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    # লোকাল পিসিতে চালানোর জন্য (যদি সেটিংসে না থাকে)
    GROQ_API_KEY = "Gsk_8Dp2FXDZupX0t1XqttYRWGdyb3FYw7KaqHb1mTIQ1BbERX6HWE5C"

client = Groq(api_key=GROQ_API_KEY)

# ৩. সাইডবার ফাইল আপলোডার
st.sidebar.header("📁 আপলোড সেন্টার")
sample_file = st.sidebar.file_uploader("ম্যানেজারের Sample (Template) আপলোড করুন", type=['csv', 'xlsx'])
source_files = st.sidebar.file_uploader("সবগুলো Source Files (৩-৪টি) আপলোড করুন", type=['csv', 'xlsx'], accept_multiple_files=True)

# Fuzzy VLOOKUP ফাংশন
def fuzzy_merge(main_df, source_df, main_col, source_col, threshold=85):
    choices = source_df[source_col].astype(str).tolist()
    def get_match(x):
        match, score = process.extractOne(str(x), choices, scorer=fuzz.token_sort_ratio)
        return match if score >= threshold else None
    
    main_df['temp_key'] = main_df[main_col].apply(get_match)
    merged = pd.merge(main_df, source_df, left_on='temp_key', right_on=source_col, how='left')
    return merged.drop(columns=['temp_key'])

# মূল লজিক
if sample_file and source_files:
    # স্যাম্পল ফাইল রিড
    df_sample = pd.read_csv(sample_file) if sample_file.name.endswith('.csv') else pd.read_excel(sample_file)
    
    # সোর্স ফাইলগুলো ডিকশনারিতে রাখা
    dataframes = {}
    for f in source_files:
        dataframes[f.name] = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)

    st.success(f"সফলভাবে {len(dataframes)}টি সোর্স ফাইল লোড হয়েছে!")

    # ট্যাব সিস্টেম
    tab1, tab2 = st.tabs(["🔍 ডেটা প্রিভিউ", "🧠 AI এনালিস্ট"])

    with tab1:
        st.write("### স্যাম্পল রিপোর্টের ফরম্যাট:")
        st.dataframe(df_sample.head(5))
        st.write("### সোর্স ফাইলগুলোর কলামসমূহ:")
        for name, df in dataframes.items():
            st.text(f"📄 {name}: {list(df.columns)}")

    with tab2:
        user_msg = st.chat_input("লিখুন: 'ফাজি ভি-লুকআপ করে স্যাম্পল ফরম্যাটে রিপোর্ট বানাও'")
        
        if user_msg:
            # AI-এর জন্য ডেটা কনটেক্সট তৈরি
            context = f"Target Columns: {list(df_sample.columns)}\n"
            for name, df in dataframes.items():
                context += f"File {name} has columns: {list(df.columns)}\n"

            with st.spinner("AI প্রসেসিং করছে..."):
                prompt = f"""
                You are a Senior Data Scientist.
                Task: Replicate the sample report structure using the provided source files.
                Context: {context}
                User Question: {user_msg}
                Instructions:
                1. Identify which columns from source files map to the sample report.
                2. Explain if a Fuzzy Merge is needed.
                3. Provide a summary of the data.
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("### 🤖 AI এর উত্তর:")
                st.write(response.choices[0].message.content)

                # অটো-মার্জ বাটন (সিম্পল ডেমো)
                if st.button("Download Draft Report (CSV)"):
                    # সব সোর্স ফাইলকে স্যাম্পলের সাথে লেফট জয়েন করা
                    combined_df = df_sample.copy()
                    st.download_button("এখান থেকে রিপোর্ট ডাউনলোড করুন", combined_df.to_csv(index=False), "final_report.csv")

else:
    st.info("শুরু করতে বাম পাশের সাইডবার থেকে ফাইলগুলো আপলোড করুন।")
