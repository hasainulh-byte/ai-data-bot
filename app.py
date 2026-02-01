import os, time, requests, pandas as pd
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from geopy.geocoders import Nominatim

# 1. SETUP: Load keys from GitHub Secrets (Environment Variables)
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
geolocator = Nominatim(user_agent="efazi_world_robot")

# 2. MAPPING ENGINE: Calculate Road Distance (Worldwide)
def get_road_distance(lat1, lon1, lat2, lon2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        res = requests.get(url, timeout=5).json()
        if res.get('code') == 'Ok':
            return round(res['routes'][0]['distance'] / 1000, 2)
        return 0
    except:
        return 0

# 3. DAMMAM SCRAPER: Get all 100+ areas automatically
def scrape_dammam_districts():
    query = """
    [out:json];
    area["name:en"="Dammam"]->.a;
    (node["place"~"suburb|neighbourhood"](area.a););
    out center;
    """
    response = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
    return response.json().get('elements', [])

# 4. MAIN HANDLER: AI Brain + Data Processor
async def efazi_core(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower() if update.message.text else ""

    # Command: Automatic Dammam Report
    if "dammam" in text and "report" in text:
        await update.message.reply_text("🤖 Efazi: Scraping Dammam areas and calculating road distances from Nakheel Mall...")
        areas = scrape_dammam_districts()
        nakheel_lat, nakheel_lon = 26.4398, 50.1057
        
        report = []
        for area in areas[:100]: # Limit to 100 for safety
            name = area.get('tags', {}).get('name:en', 'Unknown Area')
            lat, lon = area['center']['lat'], area['center']['lon']
            dist = get_road_distance(nakheel_lat, nakheel_lon, lat, lon)
            report.append({"Area": name, "Lat": lat, "Lon": lon, "KM_from_Nakheel": dist})
            time.sleep(1.1) # Free tier delay

        pd.DataFrame(report).to_excel("Dammam_Report.xlsx", index=False)
        await update.message.reply_document(open("Dammam_Report.xlsx", "rb"), caption="✅ Here is your Dammam Data.")

    # Generic AI Chat: Using Groq
    else:
        chat = GROQ_CLIENT.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": "You are Efazi, a global mapping robot."},
                      {"role": "user", "content": text}]
        )
        await update.message.reply_text(chat.choices[0].message.content)

# 5. START BOT
if __name__ == "__main__":
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, efazi_core))
    print("Efazi Robot is Online...")
    app.run_polling()
