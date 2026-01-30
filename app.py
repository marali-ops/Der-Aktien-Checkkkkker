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
    .stSuccess { border-left: 5px solid #2ca02c; }
    </style>
    """, unsafe_allow_html=True)

# Clients initialisieren
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    NEWS_KEY = st.secrets["NEWS_API_KEY"]
except Exception:
    st.error("🚨 Secrets fehlen! Bitte OPENAI_API_KEY und NEWS_API_KEY in Streamlit hinterlegen.")

# --- FUNKTIONEN ---

def fetch_global_news():
    """Zieht News mit mehreren Fallbacks (DE -> EN -> Everything)"""
    all_titles = []
    
    # Versuch 1: Deutsche Wirtschaftsnews
    try:
        url_de = f"https://newsapi.org/v2/top-headlines?category=business&language=de&apiKey={NEWS_KEY}"
        res_de = requests.get(url_de, timeout=10).json()
        all_titles.extend([a["title"] for a in res_de.get("articles", [])[:5]])
    except: pass

    # Versuch 2: Englische Wirtschaftsnews (Falls DE leer oder wenig)
    if len(all_titles) < 3:
        try:
            url_en = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_KEY}"
            res_en = requests.get(url_en, timeout=10).json()
            all_titles.extend([a["title"] for a in res_en.get("articles", [])[:5]])
        except: pass

    # Versuch 3: Globale Aktiensuche (Wenn alles andere versagt)
    if not all_titles:
        try:
            url_ex = f"https://newsapi.org/v2/everything?q=stock+market+analysis&sortBy=relevancy&pageSize=10&apiKey={NEWS_KEY}"
            res_ex = requests.get(url_ex, timeout=10).json()
            all_titles.extend([a["title"] for a in res_ex.get("articles", [])[:10]])
        except: pass

    return " | ".join(all_titles) if all_titles else "Keine aktuellen News gefunden."

def get_ai_analysis(news_context):
    """KI-Analyse mit dem 40-Jahre-Erfahrung-Prompt"""
    try:
        prompt = f"""
        Analysiere diese aktuellen Markt-Schlagzeilen: {news_context}
        
        Deine Rolle: Senior-Finanzstratege mit Fokus auf Patentstärke und Unterbewertungen.
        Aufgabe:
        1. Kurze Marktanalyse (Was passiert gerade?).
        2. Nenne exakt 3 Aktien-Ticker (z.B. AAPL, MSFT, RHM), die heute Potenzial haben.
        3. Begründe die Auswahl (Warum genau diese?).
        
        Antworte prägnant und professionell.
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener Börsenexperte. Nutze Ticker-Symbole in Großbuchstaben."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"KI-Analyse-Fehler: {str(e)}"

def get_live_data(ticker):
    """Echtzeitkurse von Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty: return None
        
        cp = hist['Close'].iloc[-1]
        pc = hist['Close'].iloc[0]
        ch = ((cp - pc) / pc) * 100
        
        return {"price": cp, "change": ch}
    except:
        return None

# --- SIDEBAR: JURISTISCHES & WATCHLIST ---
st.sidebar.title("🛡️ Investor Control")

st.sidebar.info("""
**⚖️ Patentanwalt-Check**
Dieses Tool wurde von einem Patentanwalt mitentwickelt. Logik wasserdicht, aber: Marktbewegungen sind nicht patentierbar. Keine Anlageberatung!
""")

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = pd.DataFrame(columns=['Ticker', 'Startpreis'])

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Deine Watchlist")
with st.sidebar.form("add_form"):
    t_input = st.text_input("Ticker (z.B. TSLA)").upper()
    if st.form_submit_button("Hinzufügen"):
        data = get_live_data(t_input)
        if data:
            new_row = pd.DataFrame({'Ticker': [t_input], 'Startpreis': [data['price']]})
            st.session_state.watchlist = pd.concat([st.session_state.watchlist, new_row], ignore_index=True)
            st.success(f"{t_input} hinzugefügt!")

for idx, row in st.session_state.watchlist.iterrows():
    l_data = get_live_data(row['Ticker'])
    if l_data:
        perf = ((l_data['price'] - row['Startpreis']) / row['Startpreis']) * 100
        st.sidebar.write(f"**{row['Ticker']}**: {l_data['price']:.2f}$ ({perf:+.2f}%)")

st.sidebar.markdown("---")
st.sidebar.write("🎂 **Happy Birthday!**")
st.sidebar.write("Möge dein Portfolio heute grün schließen.")

# --- HAUPTBEREICH ---
st.title("🌍 Market Intelligence Dashboard")
st.caption(f"Status: Betriebsbereit | Heute ist der {date.today().strftime('%d.%m.%Y')}")

if st.button("🚀 Heutige Chancen analysieren"):
    with st.spinner("Extrahiere globale Signale..."):
        # 1. News
        news_text = fetch_global_news()
        
        # 2. KI
        analysis = get_ai_analysis(news_text)
        
        # 3. UI
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            st.subheader("📰 Marktsignale")
            if "News-Fehler" in news_text or "Keine News" in news_text:
                st.warning(news_text)
            else:
                for n in news_text.split(" | ")[:8]:
                    st.write(f"• {n}")

        with c2:
            st.subheader("🎯 Strategie & Picks")
            st.info(analysis)
            
            # Ticker-Extraktion
            found_tickers = re.findall(r'\b[A-Z]{2,5}\b', analysis)
            filtered = [t for t in list(set(found_tickers)) if t not in ["USA", "FED", "USD", "DAX", "AI", "KI"]]
            
            if filtered:
                st.markdown("---")
                st.subheader("📈 Live-Kurse der Auswahl")
                for t in filtered[:3]:
                    data = get_live_data(t)
                    if data:
                        mc1, mc2 = st.columns(2)
                        mc1.metric(t, f"{data['price']:.2f}$")
                        mc2.metric("Heute", f"{data['change']:.2f}%")
    st.balloons()
else:
    st.write("Bereit für den nächsten Trade? Klicke auf den Button oben.")
