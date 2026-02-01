import os
import time
import threading
import requests
import pandas as pd
from flask import Flask
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. RENDER HEALTH CHECK (THE HEARTBEAT) ---
app_server = Flask(__name__)

@app_server.route('/')
def health_check():
    return "Efazi Robot is online and healthy!", 200

def run_web_server():
    # Render requires binding to 0.0.0.0 and a specific port
    port = int(os.environ.get("PORT", 10000))
    app_server.run(host='0.0.0.0', port=port)

# Start the web server in a background thread
threading.Thread(target=run_web_server, daemon=True).start()

# --- 2. EFAZI ROBOT SETUP ---
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Mapping Config
NAKHEEL_MALL = (26.4398, 50.1057)

def get_road_distance(lat1, lon1, lat2, lon2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        res = requests.get(url, timeout=10).json()
        return round(res['routes'][0]['distance'] / 1000, 2) if 'routes' in res else 0
    except:
        return 0

# --- 3. BOT LOGIC ---
async def efazi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower() if update.message.text else ""

    # Feature: Dammam Area Report
    if "dammam" in user_text and "report" in user_text:
        await update.message.reply_text("🤖 Scraping 100+ Dammam areas from Nakheel Mall... please wait about 2 mins.")
        
        # Overpass API to get Dammam suburbs
        query = '[out:json];area["name:en"="Dammam"]->.a;(node["place"~"suburb|neighbourhood"](area.a););out center;'
        areas = requests.get("http://overpass-api.de/api/interpreter", params={'data': query}).json().get('elements', [])
        
        data_list = []
        for area in areas[:100]:
            name = area.get('tags', {}).get('name:en', 'Unknown')
            lat, lon = area['center']['lat'], area['center']['lon']
            dist = get_road_distance(NAKHEEL_MALL[0], NAKHEEL_MALL[1], lat, lon)
            data_list.append({"Area": name, "Lat": lat, "Lon": lon, "Distance_KM": dist})
            time.sleep(1.1) # Rate limit safety

        df = pd.DataFrame(data_list)
        file_name = "Dammam_Efazi_Report.xlsx"
        df.to_excel(file_name, index=False)
        await update.message.reply_document(open(file_name, 'rb'), caption="📍 Dammam Global Data Complete.")

    # Feature: Groq AI Chat
    else:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": "You are Efazi, a global AI robot."},
                      {"role": "user", "content": user_text}]
        )
        await update.message.reply_text(response.choices[0].message.content)

# --- 4. EXECUTION ---
if __name__ == "__main__":
    bot_app = Application.builder().token(TG_TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.ALL, efazi_handler))
    print("Efazi is live on Render!")
    bot_app.run_polling()
