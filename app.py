import streamlit as st
import requests
import yfinance as yf
import pandas as pd
from openai import OpenAI
from datetime import date, datetime
import re

# 1. SETUP & DESIGN
st.set_page_config(page_title="Pro-Investor Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stInfo { border-left: 5px solid #1f77b4; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# Clients initialisieren aus den Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    NEWS_KEY = st.secrets["NEWS_API_KEY"]
except Exception as e:
    st.error("🚨 Secrets nicht gefunden! Bitte trage OPENAI_API_KEY und NEWS_API_KEY in den Streamlit Settings ein.")

# --- FUNKTIONEN ---

def fetch_global_news():
    """Zieht die aktuellsten Business-Headlines"""
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=de&apiKey={NEWS_KEY}"
    try:
        response = requests.get(url, timeout=10).json()
        articles = response.get("articles", [])
        if not articles:
            return "Keine aktuellen News gefunden."
        return " | ".join([a["title"] for a in articles[:10]])
    except Exception as e:
        return f"News-Fehler: {str(e)}"

def get_ai_analysis(news_context):
    """KI-Analyse basierend auf 40 Jahren Erfahrung"""
    try:
        prompt = f"""
        Analysiere diese Schlagzeilen: {news_context}
        
        Aufgabe:
        1. Kurze Einschätzung der Marktlage (Fokus auf Chancen).
        2. Nenne 3 konkrete Aktien-Ticker (z.B. AAPL, TSLA, NVDA), die jetzt spannend sind.
        3. Begründe die Auswahl kurz.
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein Senior-Finanzstratege. Antworte klar und strukturiert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"KI-Fehler: {str(e)}"

def get_live_data(ticker):
    """Holt Echtzeitkurse über Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty: return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[0]
        change = ((current_price - prev_close) / prev_close) * 100
        
        return {
            "price": current_price,
            "change": change,
            "volatility": (hist['High'].iloc[-1] - hist['Low'].iloc[-1]) / current_price * 100
        }
    except:
        return None

# --- SIDEBAR & WATCHLIST ---
st.sidebar.title("🛡️ Investor Control")

# Patentanwalt Disclaimer
st.sidebar.info("""
**⚖️ Patentanwalt-Check**
Dieses Tool wurde von einem Patentanwalt mitentwickelt. Logik wasserdicht, aber: Marktbewegungen sind nicht patentierbar. Keine Anlageberatung!
""")

# Watchlist Logik
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = pd.DataFrame(columns=['Ticker', 'Startpreis'])

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Watchlist")
with st.sidebar.form("add_form"):
    t_input = st.text_input("Ticker hinzufügen").upper()
    if st.form_submit_button("Hinzufügen"):
        data = get_live_data(t_input)
        if data:
            new_entry = pd.DataFrame({'Ticker': [t_input], 'Startpreis': [data['price']]})
            st.session_state.watchlist = pd.concat([st.session_state.watchlist, new_entry], ignore_index=True)

if not st.session_state.watchlist.empty:
    for idx, row in st.session_state.watchlist.iterrows():
        l_data = get_live_data(row['Ticker'])
        if l_data:
            perf = ((l_data['price'] - row['Startpreis']) / row['Startpreis']) * 100
            st.sidebar.write(f"**{row['Ticker']}**: {l_data['price']:.2f}$ ({perf:+.2f}%)")

# Geburtstag Gruß
st.sidebar.markdown("---")
st.sidebar.write("🎂 **Happy Birthday!**")
st.sidebar.write("Möge dein Portfolio heute grün schließen.")

# --- HAUPTBEREICH ---
st.title(f"🌍 Market Intelligence Briefing")
st.write(f"Datum: {date.today().strftime('%d.%m.%Y')}")

if st.button("🚀 Analyse jetzt starten"):
    with st.spinner("Sammle Weltnachrichten und berechne Chancen..."):
        # 1. News holen
        news_data = fetch_global_news()
        
        # 2. KI Analyse
        analysis = get_ai_analysis(news_data)
        
        # 3. Darstellung
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.subheader("📰 Aktuelle Schlagzeilen")
            st.caption("Was den Markt gerade bewegt:")
            for h in news_data.split(" | ")[:8]:
                st.write(f"• {h}")

        with col2:
            st.subheader("🎯 Strategie-Auswertung")
            st.info(analysis)
            
            # Ticker automatisch finden
            tickers = re.findall(r'\b[A-Z]{2,5}\b', analysis)
            valid_tickers = [t for t in list(set(tickers)) if t not in ["NEWS", "USA", "FED", "USD", "AI", "KI"]]
            
            if valid_tickers:
                st.markdown("---")
                st.subheader("📈 Live-Check der Ticker")
                for t in valid_tickers[:4]:
                    data = get_live_data(t)
                    if data:
                        c1, c2, c3 = st.columns([1, 1, 1])
                        c1.metric(t, f"{data['price']:.2f}$")
                        c2.metric("Trend", f"{data['change']:.2f}%")
                        if abs(data['change']) > 5:
                            c3.warning("⚡ Hohe Dynamik!")
                        else:
                            c3.write("稳定 Stabil")
    st.balloons()
