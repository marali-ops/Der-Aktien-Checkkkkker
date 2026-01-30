import streamlit as st
import requests
from openai import OpenAI
from datetime import date

# 1. Setup & Design
st.set_page_config(page_title="Morning Briefing Admin", layout="wide")

# Custom CSS für den Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Clients initialisieren
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
NEWS_KEY = st.secrets["NEWS_API_KEY"]

# 2. Funktion: Echte News laden
def fetch_global_news():
    # Wir ziehen News zu Weltpolitik, Wirtschaft und Deutschland
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=de&apiKey={NEWS_KEY}"
    response = requests.get(url).json()
    articles = response.get("articles", [])
    headlines = [a["title"] for a in articles[:10]] # Top 10 Schlagzeilen
    return " | ".join(headlines)

# 3. Funktion: KI-Analyse (Das Gehirn)
def get_ai_analysis(news_context):
    prompt = f"""
    Analysiere die aktuelle Lage basierend auf diesen Schlagzeilen: {news_context}
    
    Aufgabe:
    1. Bewerte die Weltpolitik, Weltwirtschaft, Europa und Deutschland.
    2. Identifiziere die 'Top 3 Aktien des Tages' (mit Ticker-Symbol), die von dieser speziellen Lage profitieren (z.B. Rüstung bei Konflikten, Auto bei Subventionen).
    3. Gib für jede Aktie eine kurze, logische Begründung an.
    
    Formatierung: Nutze Markdown-Listen und fette die Aktiennamen.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Du bist ein präziser Finanz-Stratege für politische Börsen."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- UI STRUKTUR ---

st.title(f"🌍 Intelligence Briefing: {date.today().strftime('%d.%m.%Y')}")
st.caption("Analysiert Weltpolitik, Wirtschaftslage und spezifische Markttrends.")

if st.button("🚀 Heutiges Briefing generieren"):
    with st.spinner("Sammle Daten von globalen News-Servern..."):
        # Daten sammeln
        raw_news = fetch_global_news()
        
        # UI Spalten
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📰 Aktuelle Schlagzeilen")
            for h in raw_news.split(" | "):
                st.write(f"• {h}")
        
        with col2:
            st.subheader("🎯 KI-Analyse & Top Picks")
            analysis = get_ai_analysis(raw_news)
            st.info(analysis)
            
    st.balloons()
else:
    st.info("Klicke auf den Button, um den Tag mit einer frischen Analyse zu starten.")

# Kleiner persönlicher Gruß (Geburtstags-Touch)
st.sidebar.markdown("---")
st.sidebar.write("🎂 **Happy Birthday!**")
st.sidebar.write("Möge dein Portfolio heute grün schließen.")
