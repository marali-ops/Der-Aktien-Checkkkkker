import streamlit as st
import requests
import yfinance as yf
import pandas as pd
from openai import OpenAI
from datetime import date, datetime

# 1. SETUP & DESIGN
st.set_page_config(page_title="Pro-Investor Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stInfo { border-left: 5px solid #1f77b4; }
    .stSuccess { border-left: 5px solid #2ca02c; }
    .stWarning { border-left: 5px solid #ffa500; }
    </style>
    """, unsafe_allow_html=True)

# Clients initialisieren (Hinweis: API Keys müssen in Streamlit Secrets liegen)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
NEWS_KEY = st.secrets["NEWS_API_KEY"]

# --- FUNKTIONEN ---

def fetch_global_news():
    """Zieht die aktuellsten Business-Headlines"""
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=de&apiKey={NEWS_KEY}"
    try:
        response = requests.get(url).json()
        articles = response.get("articles", [])
        return " | ".join([a["title"] for a in articles[:10]])
    except Exception:
        return "News-Server aktuell nicht erreichbar."

def get_ai_analysis(news_context):
    """Kombiniert News mit 40 Jahren Börsenerfahrung"""
    prompt = f"""
    Analysiere diese Schlagzeilen: {news_context}
    
    Aufgabe:
    1. Kurze Einschätzung der Marktlage (Weltpolitik & Wirtschaft).
    2. Identifiziere die Top 3 Aktien (Ticker-Symbole), die das Potenzial für einen >10% Sprung haben.
    
    Antworte exakt in diesem Format:
    MARKTANALYSE: [Deine Analyse]
    TICKER: [TICKER1, TICKER2, TICKER3]
    BEGRÜNDUNG: [Warum diese Aktien?]
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Du bist ein Senior-Finanzstratege mit Fokus auf Patentstärke und Marktmomentum."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_live_data(ticker):
    """Holt Echtzeitkurse und fundamentale Daten"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty: return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[0]
        change = ((current_price - prev_close) / prev_close) * 100
        
        return {
            "name": stock.info.get('shortName', ticker),
            "price": current_price,
            "change": change,
            "volatility": (hist['High'].iloc[-1] - hist['Low'].iloc[-1]) / current_price * 100
        }
    except Exception:
        return None

# --- WATCHLIST LOGIK ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = pd.DataFrame(columns=['Ticker', 'Startpreis', 'Datum'])

def add_to_watchlist(ticker):
    data = get_live_data(ticker)
    if data:
        new_entry = pd.DataFrame({'Ticker': [ticker], 'Startpreis': [data['price']], 'Datum': [datetime.now().strftime("%d.%m.%y")]})
        st.session_state.watchlist = pd.concat([st.session_state.watchlist, new_entry], ignore_index=True)

# --- SIDEBAR: JURISTISCHES, WATCHLIST & GEBURTSTAG ---
st.sidebar.title("🛡️ Investor Control")

# Der Patentanwalts-Disclaimer
st.sidebar.info("""
**⚖️ Patentanwalt-Check**
Dieses Tool wurde von einem Patentanwalt mitentwickelt. Die Logik ist präzise, aber: *Marktbewegungen sind nicht patentierbar.* Keine Anlageberatung, nur Information!
""")

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Watchlist")
with st.sidebar.form("add_form"):
    t_input = st.text_input("Ticker hinzufügen").upper()
    if st.form_submit_button("Hinzufügen"):
        add_to_watchlist(t_input)

if not st.session_state.watchlist.empty:
    for idx, row in st.session_state.watchlist.iterrows():
        l_data = get_live_data(row['Ticker'])
        if l_data:
            perf = ((l_data['price'] - row['Startpreis']) / row['Startpreis']) * 100
            st.sidebar.write(f"**{row['Ticker']}**: {l_data['price']:.2f} ({perf:+.2f}%)")
    if st.sidebar.button("Watchlist leeren"):
        st.session_state.watchlist = pd.DataFrame(columns=['Ticker', 'Startpreis', 'Datum'])
        st.rerun()

# Kleiner persönlicher Gruß (Geburtstags-Touch)
st.sidebar.markdown("---")
st.sidebar.write("🎂 **Happy Birthday!**")
st.sidebar.write("Möge dein Portfolio heute grün schließen.")

# --- HAUPTBEREICH ---
st.title(f"🌍 Intelligence Briefing: {date.today().strftime('%d.%m.%Y')}")
st.caption("Analysiert Weltpolitik, Wirtschaftslage und spezifische Markttrends durch die Brille von 40 Jahren Erfahrung.")

if st.button("🚀 Heutiges Briefing generieren"):
    with st.spinner("Sammle Daten von globalen News-Servern..."):
        news = fetch_global_news()
        analysis_text = get_ai_analysis(news)
        
        # Parsen der KI-Antwort
        lines = analysis_text.split("\n")
        markt_anlyse = next((l for l in lines if "MARKTANALYSE:" in l), "N/A")
        ticker_line = next((l for l in lines if "TICKER:" in l), "")
        begruendung = next((l for l in lines if "BEGRÜNDUNG:" in l), "N/A")
        
        tickers = [t.strip() for t in ticker_line.replace("TICKER:", "").split(",")]

        # UI LAYOUT
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📰 Aktuelle Schlagzeilen")
            for h in news.split(" | "):
                st.write(f"• {h}")

        with col2:
            st.subheader("🎯 KI-Analyse & Top Picks")
            st.info(markt_anlyse.replace("MARKTANALYSE:", ""))
            st.write(f"**Strategie-Begründung:** {begruendung.replace('BEGRÜNDUNG:', '')}")
            
            st.markdown("---")
            st.subheader("📈 Live Marktdaten")
            for t in tickers:
                data = get_live_data(t)
                if data:
                    c1, c2, c3 = st.columns([1, 1, 1.5])
                    c1.metric(t, f"{data['price']:.2f}$")
                    color = "normal" if data['change'] >= 0 else "inverse"
                    c2.metric("Change", f"{data['change']:.2f}%", delta_color=color)
                    
                    # Logik für Kurssprünge
                    if data['change'] > 8:
                        c3.success("🚀 Target Jump (>10%) fast erreicht!")
                    elif data['volatility'] > 4:
                        c3.warning("🔥 Hohe Volatilität erkannt!")
                    else:
                        c3.write("⌛ Momentum baut sich auf...")
                    st.divider()

    st.balloons()
else:
    st.info("Klicke auf den Button, um den Tag mit einer frischen Analyse zu starten.")

st.markdown("---")
st.caption("Dieses Dashboard kombiniert technisches Patentwissen mit jahrzehntelanger Börsenerfahrung. Viel Erfolg!")
