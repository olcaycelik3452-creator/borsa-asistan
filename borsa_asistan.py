import streamlit as st
import os
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
import requests
import json
import time
import datetime
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title="Borsa AI Asistanı", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

API_KEY = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
PORTFOY_DOSYA = Path.home() / "borsa_portfoy.json"
ALARM_DOSYA = Path.home() / "borsa_alarmlar.json"
HAFIZA_DOSYA = Path.home() / "borsa_hafiza.json"
TAKIP_DOSYA = Path.home() / "borsa_takip.json"

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: #0a0a0f; color: #e2e8f0; }
  section[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e2030; }
  .stTextInput input, .stSelectbox select, .stNumberInput input { background: #1a1a2e !important; color: #e2e8f0 !important; border: 1px solid #2d2d4e !important; border-radius: 8px !important; }
  div[data-testid="metric-container"] { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #2d2d4e; border-radius: 12px; padding: 16px !important; }
  div[data-testid="metric-container"] label { color: #8892b0 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 1px; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ccd6f6 !important; font-size: 22px !important; font-weight: 700; }
  .stTabs [data-baseweb="tab-list"] { background: #0f0f1a; border-bottom: 1px solid #1e2030; gap: 4px; }
  .stTabs [data-baseweb="tab"] { background: transparent; color: #8892b0; border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: 500; }
  .stTabs [aria-selected="true"] { background: #1a1a2e !important; color: #64ffda !important; border-bottom: 2px solid #64ffda !important; }
  .stChatMessage { background: #1a1a2e !important; border: 1px solid #2d2d4e; border-radius: 12px; margin: 8px 0; }
  .stChatInput textarea { background: #1a1a2e !important; color: #e2e8f0 !important; border: 1px solid #2d2d4e !important; border-radius: 12px !important; }
  .kart { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #2d2d4e; border-left: 3px solid #64ffda; border-radius: 10px; padding: 14px 18px; margin: 8px 0; }
  .kart-yesil { border-left-color: #00ff88 !important; }
  .kart-kirmizi { border-left-color: #ff4444 !important; }
  .kart-sari { border-left-color: #ffaa00 !important; }
  .kart-mor { border-left-color: #7c4dff !important; }
  .baslik { color: #ccd6f6; font-weight: 600; font-size: 14px; margin-bottom: 4px; }
  .meta { color: #8892b0; font-size: 11px; }
  .rasyo-kart { background: #1a1a2e; border: 1px solid #2d2d4e; border-radius: 10px; padding: 12px 16px; text-align: center; margin-bottom: 8px; }
  .rasyo-deger { color: #64ffda; font-size: 20px; font-weight: 700; }
  .rasyo-isim { color: #8892b0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
  .sinyal-al { background: linear-gradient(135deg,#0d2137,#0a3d2b); border:1px solid #00ff88; border-radius:8px; padding:8px 16px; color:#00ff88; font-weight:700; display:inline-block; }
  .sinyal-sat { background: linear-gradient(135deg,#2d1a1a,#3d0a0a); border:1px solid #ff4444; border-radius:8px; padding:8px 16px; color:#ff4444; font-weight:700; display:inline-block; }
  .sinyal-bekle { background: linear-gradient(135deg,#2d2a1a,#3d320a); border:1px solid #ffaa00; border-radius:8px; padding:8px 16px; color:#ffaa00; font-weight:700; display:inline-block; }
  h1 { background: linear-gradient(90deg,#64ffda,#00bcd4,#7c4dff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-weight:800 !important; font-size:2.2rem !important; }
  .alarm-aktif { color: #00ff88; font-size: 11px; }
  .alarm-pasif { color: #8892b0; font-size: 11px; }
  ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: #0a0a0f; } ::-webkit-scrollbar-thumb { background: #2d2d4e; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Yardımcı Fonksiyonlar ──────────────────────────────────────
def portfoy_yukle():
    try:
        if PORTFOY_DOSYA.exists():
            return json.loads(PORTFOY_DOSYA.read_text())
    except: pass
    return {}

def portfoy_kaydet(p):
    PORTFOY_DOSYA.write_text(json.dumps(p, ensure_ascii=False))

def alarm_yukle():
    try:
        if ALARM_DOSYA.exists():
            return json.loads(ALARM_DOSYA.read_text())
    except: pass
    return []

def alarm_kaydet(a):
    ALARM_DOSYA.write_text(json.dumps(a, ensure_ascii=False))

def hafiza_yukle():
    try:
        if HAFIZA_DOSYA.exists():
            return json.loads(HAFIZA_DOSYA.read_text())
    except: pass
    return []

def hafiza_kaydet(h):
    HAFIZA_DOSYA.write_text(json.dumps(h[-50:], ensure_ascii=False))

def takip_yukle():
    try:
        if TAKIP_DOSYA.exists():
            return json.loads(TAKIP_DOSYA.read_text())
    except: pass
    return []

def takip_kaydet(t):
    TAKIP_DOSYA.write_text(json.dumps(t, ensure_ascii=False))

@st.cache_data(ttl=180)
def veri_cek(sembol, periyot, aralik):
    obj = yf.Ticker(sembol)
    df = obj.history(period=periyot, interval=aralik)
    bilgi = obj.info
    return df, bilgi

@st.cache_data(ttl=60)
def son_fiyat_cek(sembol):
    try:
        return yf.Ticker(sembol).history(period="1d")['Close'].iloc[-1]
    except: return None

def turkce_haberler_cek(sembol):
    kod = sembol.replace('.IS','').upper()
    sirket_map = {
        'THYAO':'THY|Türk Hava','GARAN':'Garanti|GARAN','AKBNK':'Akbank|AKBNK',
        'ASELS':'Aselsan|ASELS','EREGL':'Ereğli|EREGL','KCHOL':'Koç Holding|KCHOL',
        'SASA':'Sasa|SASA','BIMAS':'BİM|Bim|BIMAS','TUPRS':'Tüpraş|TUPRS',
        'SAHOL':'Sabancı|SAHOL','YKBNK':'Yapı Kredi|YKBNK','ISCTR':'İş Bankası|ISCTR',
        'TOASO':'Tofaş|TOASO','FROTO':'Ford Otosan|FROTO','ARCLK':'Arçelik|ARCLK',
        'PETKM':'Petkim|PETKM','KOZAL':'Koza Altın|KOZAL','EKGYO':'Emlak Konut|EKGYO',
    }
    anahtar = sirket_map.get(kod, kod)
    kelimeler = [k.strip() for k in anahtar.split('|')]
    rss_kaynaklar = [
        ('https://www.foreks.com/rss/', 'Foreks'),
        ('https://www.bloomberght.com/rss', 'BloombergHT'),
        ('https://bigpara.hurriyet.com.tr/rss/', 'Bigpara'),
        ('https://tr.investing.com/rss/stock.rss', 'Investing TR'),
    ]
    haberler = []
    import xml.etree.ElementTree as ET
    for url, kaynak in rss_kaynaklar:
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent':'Mozilla/5.0'})
            root = ET.fromstring(r.content)
            for item in root.findall('.//item'):
                t_el = item.find('title')
                if t_el is None or not t_el.text: continue
                t = t_el.text.strip()
                eslesme = any(k.lower() in t.lower() for k in kelimeler)
                onemli_kw = ['SERMAYE','TEMETTÜ','KAR PAYI','BİRLEŞME','SATIN AL','FAİZ','ENFLASYON','TRUMP','FED','DOLAR']
                genel = any(w in t.upper() for w in onemli_kw)
                if eslesme or genel:
                    l_el = item.find('link')
                    d_el = item.find('pubDate')
                    desc_el = item.find('description')
                    import re
                    desc = re.sub('<.*?>','', desc_el.text)[:120] if desc_el is not None and desc_el.text else ''
                    haberler.append({
                        'title': t, 'link': l_el.text if l_el is not None else '#',
                        'pubDate': d_el.text[:16] if d_el is not None and d_el.text else '',
                        'desc': desc, 'kaynak': kaynak, 'onemli': eslesme
                    })
        except: continue
    haberler.sort(key=lambda x: (not x['onemli'], x.get('pubDate','')))
    return haberler[:12]

def hesapla(df):
    df = df.copy()
    c = df['Close']
    delta = c.diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    df['RSI'] = 100-(100/(1+gain/loss))
    df['MA20'] = c.rolling(20).mean()
    df['MA50'] = c.rolling(50).mean()
    df['MA200'] = c.rolling(200).mean()
    std20 = c.rolling(20).std()
    df['BB_UST'] = df['MA20']+2*std20
    df['BB_ALT'] = df['MA20']-2*std20
    ema12 = c.ewm(span=12).mean()
    ema26 = c.ewm(span=26).mean()
    df['MACD'] = ema12-ema26
    df['MACD_SIG'] = df['MACD'].ewm(span=9).mean()
    df['MACD_HIST'] = df['MACD']-df['MACD_SIG']
    high = df['High'].rolling(50).max()
    low = df['Low'].rolling(50).min()
    diff = high-low
    df['FIB_382'] = high-0.382*diff
    df['FIB_618'] = high-0.618*diff
    df['Sinyal'] = 0
    df.loc[(df['RSI']<35)&(c>df['MA20']),'Sinyal'] = 1
    df.loc[(df['RSI']>65)&(c<df['MA20']),'Sinyal'] = -1
    df['Poz'] = df['Sinyal'].replace(0,pd.NA).ffill().fillna(0)
    ret = c.pct_change()
    df['BH'] = (1+ret).cumprod()
    df['Strateji'] = (1+ret*df['Poz'].shift(1)).cumprod()
    return df

def sinyal_hesapla(df):
    r = df['RSI'].iloc[-1]
    f = df['Close'].iloc[-1]
    puan = 0
    if r<35: puan+=2
    elif r>70: puan-=2
    if f>df['MA20'].iloc[-1]: puan+=1
    else: puan-=1
    if f>df['MA50'].iloc[-1]: puan+=1
    else: puan-=1
    if df['MACD'].iloc[-1]>df['MACD_SIG'].iloc[-1]: puan+=1
    else: puan-=1
    if puan>=2: return "AL", puan
    elif puan<=-2: return "SAT", puan
    else: return "BEKLE", puan

# ── SIDEBAR ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h3 style='color:#64ffda;'>⚙️ Ayarlar</h3>", unsafe_allow_html=True)
    hisse = st.text_input("🔍 Hisse Kodu", value="THYAO.IS")
    period_label = st.selectbox("📅 Zaman Aralığı",
        ["Son 5 Gün (Saatlik)","1 Ay","3 Ay","6 Ay","1 Yıl","2 Yıl"], index=3)
    period_map = {
        "Son 5 Gün (Saatlik)":("5d","1h"), "1 Ay":("1mo","1d"),
        "3 Ay":("3mo","1d"), "6 Ay":("6mo","1d"),
        "1 Yıl":("1y","1wk"), "2 Yıl":("2y","1wk")
    }
    period, interval = period_map[period_label]

    st.markdown("---")
    st.markdown("<p style='color:#8892b0;font-size:12px;'>🎯 <b style='color:#ccd6f6;'>Risk Profilin</b></p>", unsafe_allow_html=True)
    risk_profil = st.selectbox("", ["Muhafazakar","Dengeli","Agresif"], label_visibility="collapsed")
    risk_aciklama = {"Muhafazakar":"Düşük risk, temettü odaklı","Dengeli":"Orta risk, büyüme+temettü","Agresif":"Yüksek risk, büyüme odaklı"}
    st.caption(risk_aciklama[risk_profil])

    st.markdown("---")
    st.markdown("<p style='color:#8892b0;font-size:12px;'>⭐ <b style='color:#ccd6f6;'>Takip Listesi</b></p>", unsafe_allow_html=True)
    takip = takip_yukle()
    t_ekle_col, t_btn_col = st.columns([3,1])
    t_yeni = t_ekle_col.text_input("", placeholder="GARAN.IS", key="t_yeni", label_visibility="collapsed")
    if t_btn_col.button("➕", key="t_ekle_btn"):
        if t_yeni and t_yeni.upper() not in takip:
            takip.append(t_yeni.upper())
            takip_kaydet(takip)
            st.rerun()
    for t_hisse in takip:
        try:
            t_fiyat = son_fiyat_cek(t_hisse)
            t_col1, t_col2, t_col3 = st.columns([3,2,1])
            if t_col1.button(t_hisse, key=f"t_{t_hisse}"):
                hisse = t_hisse
            t_col2.markdown(f"<p style='color:#64ffda;font-size:12px;margin-top:8px;'>{t_fiyat:.2f}₺</p>" if t_fiyat else "<p style='color:#8892b0;font-size:12px;margin-top:8px;'>—</p>", unsafe_allow_html=True)
            if t_col3.button("✕", key=f"t_sil_{t_hisse}"):
                takip.remove(t_hisse)
                takip_kaydet(takip)
                st.rerun()
        except:
            pass

    st.markdown("---")
    st.markdown("<p style='color:#8892b0;font-size:12px;'>🇹🇷 <b style='color:#ccd6f6;'>BIST Hisseleri</b></p>", unsafe_allow_html=True)
    for b in ["THYAO.IS","GARAN.IS","ASELS.IS","EREGL.IS","KCHOL.IS","SASA.IS","BIMAS.IS","AKBNK.IS","TUPRS.IS","SAHOL.IS"]:
        if st.button(b, key=b): hisse = b
    st.markdown("---")
    st.markdown("<p style='color:#8892b0;font-size:12px;'>🌍 <b style='color:#ccd6f6;'>Global</b></p>", unsafe_allow_html=True)
    for g in ["SPY","AAPL","TSLA","NVDA","BTC-USD","GC=F"]:
        if st.button(g, key=g): hisse = g

# ── BAŞLIK ─────────────────────────────────────────────────────
st.markdown("# 📈 Borsa AI Asistanı")
st.markdown("<p style='color:#8892b0;margin-top:-10px;'>Gerçek zamanlı analiz · Portföy takibi · Fiyat alarmları · AI yorumlama</p>", unsafe_allow_html=True)
st.markdown("---")

# ── ALARM KONTROLÜ ─────────────────────────────────────────────
alarmlar = alarm_yukle()
tetiklenen = []
for alarm in alarmlar:
    try:
        fp = son_fiyat_cek(alarm['sembol'])
        if fp:
            if alarm['yon'] == 'üstüne' and fp >= alarm['hedef']:
                tetiklenen.append(alarm)
            elif alarm['yon'] == 'altına' and fp <= alarm['hedef']:
                tetiklenen.append(alarm)
    except: pass

if tetiklenen:
    for t in tetiklenen:
        st.warning(f"🔔 ALARM: **{t['sembol']}** {t['hedef']} TL {t['yon']} çıktı! Şu an: {son_fiyat_cek(t['sembol']):.2f} TL")

# ── VERİ ÇEK ───────────────────────────────────────────────────
try:
    with st.spinner("🔄 Veriler yükleniyor..."):
        df, bilgi = veri_cek(hisse, period, interval)

    if df.empty:
        st.error("❌ Hisse bulunamadı.")
        st.stop()

    df = hesapla(df)
    sinyal, puan = sinyal_hesapla(df)
    son = df['Close'].iloc[-1]
    ilk = df['Close'].iloc[0]
    degisim = ((son-ilk)/ilk)*100
    rsi = df['RSI'].iloc[-1]
    st_getiri = (df['Strateji'].iloc[-1]-1)*100
    bh_getiri = (df['BH'].iloc[-1]-1)*100

    # ── METRİKLER ──────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("💰 Son Fiyat", f"{son:.2f}", f"{degisim:+.1f}%")
    c2.metric("📊 RSI", f"{rsi:.1f}", "Aşırı Alım" if rsi>70 else ("Aşırı Satım" if rsi<30 else "Normal"))
    c3.metric("📈 Dönem Getiri", f"{degisim:+.1f}%")
    c4.metric("🤖 Strateji", f"{st_getiri:+.1f}%", f"BH: {bh_getiri:+.1f}%")
    sinyal_cls = "al" if sinyal=="AL" else "sat" if sinyal=="SAT" else "bekle"
    c5.markdown(f'<div class="sinyal-{sinyal_cls}">⚡ {sinyal} ({puan:+d})</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── SEKMELER ───────────────────────────────────────────────
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = st.tabs([
        "📊 Grafik","📉 MACD & RSI","🔬 Backtest",
        "💼 Portföy","🔔 Alarmlar","🌅 Sabah Raporu",
        "📰 Haberler","📋 Rasyolar","🤖 AI Asistan"
    ])

    # ─ TAB 1: TradingView ─────────────────────────────────────
    with tab1:
        tv_sembol = hisse.replace('.IS','')
        tv_exchange = 'BIST' if '.IS' in hisse else ('BINANCE' if 'BTC' in hisse else 'NASDAQ')
        if hisse == 'BTC-USD': tv_sembol = 'BTCUSDT'
        if hisse == 'GC=F': tv_sembol = 'XAUUSD'; tv_exchange = 'OANDA'
        tv_interval_map = {"Son 5 Gün (Saatlik)":"60","1 Ay":"D","3 Ay":"D","6 Ay":"D","1 Yıl":"W","2 Yıl":"W"}
        tv_interval = tv_interval_map.get(period_label, "D")
        tv_html = f"""
        <div style="height:580px;border-radius:12px;overflow:hidden;border:1px solid #1e2030;">
        <div class="tradingview-widget-container" style="height:100%;">
          <div id="tv_chart" style="height:100%;"></div>
          <script src="https://s3.tradingview.com/tv.js"></script>
          <script>
          new TradingView.widget({{
            autosize:true, symbol:"{tv_exchange}:{tv_sembol}", interval:"{tv_interval}",
            timezone:"Europe/Istanbul", theme:"dark", style:"1", locale:"tr",
            toolbar_bg:"#0f0f1a", enable_publishing:false, container_id:"tv_chart",
            studies:["MASimple@tv-basicstudies","BB@tv-basicstudies","MACD@tv-basicstudies","RSI@tv-basicstudies"],
            overrides:{{"paneProperties.background":"#0a0a0f","paneProperties.backgroundType":"solid",
              "paneProperties.vertGridProperties.color":"#1e2030","paneProperties.horzGridProperties.color":"#1e2030"}}
          }});
          </script>
        </div></div>"""
        components.html(tv_html, height=590)

    # ─ TAB 2: MACD & RSI ──────────────────────────────────────
    with tab2:
        fig2 = make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.5,0.5],vertical_spacing=0.06,
                             subplot_titles=["RSI (14)","MACD"])
        fig2.add_trace(go.Scatter(x=df.index,y=df['RSI'],name="RSI",line=dict(color='#7c4dff',width=2)),row=1,col=1)
        fig2.add_hrect(y0=70,y1=100,fillcolor="rgba(255,68,68,0.08)",line_width=0,row=1,col=1)
        fig2.add_hrect(y0=0,y1=30,fillcolor="rgba(0,255,136,0.08)",line_width=0,row=1,col=1)
        fig2.add_hline(y=70,line_dash="dash",line_color="#ff4444",line_width=1,row=1,col=1)
        fig2.add_hline(y=30,line_dash="dash",line_color="#00ff88",line_width=1,row=1,col=1)
        fig2.add_trace(go.Scatter(x=df.index,y=df['MACD'],name="MACD",line=dict(color='#64ffda',width=2)),row=2,col=1)
        fig2.add_trace(go.Scatter(x=df.index,y=df['MACD_SIG'],name="Sinyal",line=dict(color='#ff6b6b',width=1.5,dash='dot')),row=2,col=1)
        renkler=['#00ff88' if v>=0 else '#ff4444' for v in df['MACD_HIST']]
        fig2.add_trace(go.Bar(x=df.index,y=df['MACD_HIST'],name="Histogram",marker_color=renkler,opacity=0.7),row=2,col=1)
        fig2.update_layout(height=500,template="plotly_dark",paper_bgcolor='#0a0a0f',plot_bgcolor='#0f0f1a',
                           legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color='#8892b0')))
        st.plotly_chart(fig2,use_container_width=True)

    # ─ TAB 3: Backtest ────────────────────────────────────────
    with tab3:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df.index,y=df['BH'],name="Al & Tut",line=dict(color='#8892b0',width=2)))
        fig3.add_trace(go.Scatter(x=df.index,y=df['Strateji'],name="RSI Stratejisi",line=dict(color='#64ffda',width=2.5)))
        al=df[df['Sinyal']==1]; sat=df[df['Sinyal']==-1]
        fig3.add_trace(go.Scatter(x=al.index,y=al['Strateji'],mode='markers',name="Al",marker=dict(color='#00ff88',size=10,symbol='triangle-up')))
        fig3.add_trace(go.Scatter(x=sat.index,y=sat['Strateji'],mode='markers',name="Sat",marker=dict(color='#ff4444',size=10,symbol='triangle-down')))
        fig3.update_layout(height=400,template="plotly_dark",paper_bgcolor='#0a0a0f',plot_bgcolor='#0f0f1a',
                           title="Strateji Performansı",legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color='#8892b0')))
        st.plotly_chart(fig3,use_container_width=True)
        cc1,cc2,cc3=st.columns(3)
        cc1.metric("Al & Tut",f"{bh_getiri:+.1f}%")
        cc2.metric("RSI Stratejisi",f"{st_getiri:+.1f}%")
        cc3.metric("Fark",f"{st_getiri-bh_getiri:+.1f}%","Strateji daha iyi" if st_getiri>bh_getiri else "Al & Tut daha iyi")

    # ─ TAB 4: Portföy ─────────────────────────────────────────
    with tab4:
        st.markdown("<h4 style='color:#64ffda;'>💼 Portföy Takibi</h4>", unsafe_allow_html=True)
        portfoy = portfoy_yukle()

        col_p1, col_p2 = st.columns([1,2])
        with col_p1:
            st.markdown("<p style='color:#8892b0;font-size:13px;'>Hisse Ekle</p>", unsafe_allow_html=True)
            p_sembol = st.text_input("Sembol", placeholder="THYAO.IS", key="p_sembol")
            p_adet = st.number_input("Adet", min_value=1, value=100, key="p_adet")
            p_maliyet = st.number_input("Alış Fiyatı (₺)", min_value=0.01, value=100.0, key="p_maliyet")
            if st.button("➕ Portföye Ekle", key="ekle_btn"):
                if p_sembol:
                    portfoy[p_sembol.upper()] = {"adet": p_adet, "maliyet": p_maliyet}
                    portfoy_kaydet(portfoy)
                    st.success(f"✅ {p_sembol.upper()} eklendi!")
                    st.rerun()

        with col_p2:
            if portfoy:
                toplam_maliyet = 0
                toplam_deger = 0
                tablo = []
                for sembol, bilgi_p in portfoy.items():
                    try:
                        guncel = son_fiyat_cek(sembol) or bilgi_p['maliyet']
                        maliyet_toplam = bilgi_p['adet'] * bilgi_p['maliyet']
                        deger_toplam = bilgi_p['adet'] * guncel
                        kar_zarar = deger_toplam - maliyet_toplam
                        kar_yuzde = ((guncel - bilgi_p['maliyet']) / bilgi_p['maliyet']) * 100
                        toplam_maliyet += maliyet_toplam
                        toplam_deger += deger_toplam
                        tablo.append({
                            "Hisse": sembol, "Adet": bilgi_p['adet'],
                            "Alış": f"{bilgi_p['maliyet']:.2f}₺",
                            "Güncel": f"{guncel:.2f}₺",
                            "Değer": f"{deger_toplam:,.0f}₺",
                            "K/Z": f"{kar_zarar:+,.0f}₺",
                            "%": f"{kar_yuzde:+.1f}%"
                        })
                    except: pass

                df_p = pd.DataFrame(tablo)
                st.dataframe(df_p.style.set_properties(**{'background-color':'#1a1a2e','color':'#e2e8f0','border':'1px solid #2d2d4e'}), use_container_width=True)

                toplam_kz = toplam_deger - toplam_maliyet
                toplam_yuzde = ((toplam_deger - toplam_maliyet) / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
                m1,m2,m3 = st.columns(3)
                m1.metric("💰 Toplam Değer", f"{toplam_deger:,.0f}₺")
                m2.metric("📊 Toplam Maliyet", f"{toplam_maliyet:,.0f}₺")
                m3.metric("📈 Toplam K/Z", f"{toplam_kz:+,.0f}₺", f"{toplam_yuzde:+.1f}%")

                # Pasta grafik
                if len(tablo) > 1:
                    fig_p = go.Figure(go.Pie(
                        labels=[t['Hisse'] for t in tablo],
                        values=[float(t['Değer'].replace('₺','').replace(',','')) for t in tablo],
                        hole=0.4, marker=dict(colors=['#64ffda','#7c4dff','#ff6b6b','#ffaa00','#00bcd4','#ff4488'])
                    ))
                    fig_p.update_layout(height=300,template="plotly_dark",paper_bgcolor='#0a0a0f',
                                        showlegend=True,legend=dict(font=dict(color='#8892b0')))
                    st.plotly_chart(fig_p, use_container_width=True)

                # Silme
                sil_sembol = st.selectbox("Hisse Sil", [""] + list(portfoy.keys()), key="sil_sec")
                if sil_sembol and st.button("🗑️ Sil", key="sil_btn"):
                    del portfoy[sil_sembol]
                    portfoy_kaydet(portfoy)
                    st.rerun()
            else:
                st.info("Henüz portföy eklenmemiş. Sol taraftan hisse ekleyin.")

    # ─ TAB 5: Alarmlar ────────────────────────────────────────
    with tab5:
        st.markdown("<h4 style='color:#64ffda;'>🔔 Fiyat Alarmları</h4>", unsafe_allow_html=True)
        alarmlar = alarm_yukle()

        col_a1, col_a2 = st.columns([1,2])
        with col_a1:
            st.markdown("<p style='color:#8892b0;font-size:13px;'>Alarm Ekle</p>", unsafe_allow_html=True)
            a_sembol = st.text_input("Sembol", value=hisse, key="a_sembol")
            a_yon = st.selectbox("Yön", ["üstüne","altına"], key="a_yon")
            a_hedef = st.number_input("Hedef Fiyat (₺)", min_value=0.01, value=float(f"{son:.2f}"), key="a_hedef")
            a_not = st.text_input("Not (opsiyonel)", placeholder="Örn: Destek kırılırsa sat", key="a_not")
            if st.button("🔔 Alarm Ekle", key="alarm_ekle"):
                alarmlar.append({"sembol":a_sembol.upper(),"yon":a_yon,"hedef":a_hedef,"not":a_not,"tarih":str(datetime.date.today())})
                alarm_kaydet(alarmlar)
                st.success(f"✅ {a_sembol.upper()} {a_hedef}₺ {a_yon} alarmı eklendi!")
                st.rerun()

        with col_a2:
            if alarmlar:
                st.markdown("<p style='color:#8892b0;font-size:13px;'>Aktif Alarmlar</p>", unsafe_allow_html=True)
                for i, alarm in enumerate(alarmlar):
                    try:
                        guncel_f = son_fiyat_cek(alarm['sembol'])
                        guncel_str = f"{guncel_f:.2f}₺" if guncel_f else "?"
                        tetik = (alarm['yon']=='üstüne' and guncel_f and guncel_f>=alarm['hedef']) or \
                                (alarm['yon']=='altına' and guncel_f and guncel_f<=alarm['hedef'])
                        renk = "kart-yesil" if tetik else "kart"
                        st.markdown(f"""
                        <div class="kart {renk}">
                            <div class="baslik">{'🔴 TETİKLENDİ! ' if tetik else '⏳ '}{alarm['sembol']} — {alarm['hedef']}₺ {alarm['yon']}</div>
                            <div class="meta">Güncel: {guncel_str} | {alarm.get('not','')} | {alarm.get('tarih','')}</div>
                        </div>""", unsafe_allow_html=True)
                    except: pass
                if st.button("🗑️ Tüm Alarmları Temizle", key="alarm_temizle"):
                    alarm_kaydet([])
                    st.rerun()
            else:
                st.info("Henüz alarm eklenmemiş.")

    # ─ TAB 6: Sabah Raporu ────────────────────────────────────
    with tab6:
        st.markdown("<h4 style='color:#64ffda;'>🌅 Sabah Raporu</h4>", unsafe_allow_html=True)
        portfoy = portfoy_yukle()

        if st.button("📊 Raporu Oluştur", key="rapor_btn"):
            with st.spinner("🤖 AI rapor hazırlıyor..."):
                portfoy_ozet = ""
                if portfoy:
                    portfoy_ozet = "\n📦 PORTFÖY:\n"
                    for sem, bp in portfoy.items():
                        try:
                            gf = son_fiyat_cek(sem) or bp['maliyet']
                            kz = ((gf - bp['maliyet']) / bp['maliyet']) * 100
                            portfoy_ozet += f"- {sem}: {bp['adet']} adet, alış {bp['maliyet']:.2f}₺, güncel {gf:.2f}₺, K/Z: {kz:+.1f}%\n"
                        except: pass

                haberler_ozet = ""
                try:
                    haberler = turkce_haberler_cek(hisse)
                    if haberler:
                        haberler_ozet = "\n📰 GÜNCEL HABERLER:\n"
                        for h in haberler[:5]:
                            haberler_ozet += f"- {h['title']} ({h['kaynak']})\n"
                except: pass

                try:
                    client = anthropic.Anthropic(api_key=API_KEY)
                    yanit = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1500,
                        system=f"""Sen bir portföy yöneticisisin. Bugünün tarihi: {datetime.date.today()}
Risk profili: {risk_profil}
{portfoy_ozet}
{haberler_ozet}

Güncel hisse: {hisse}, Fiyat: {son:.2f}₺, RSI: {rsi:.1f}, Sinyal: {sinyal}
F/K: {bilgi.get('trailingPE','?')}, Beta: {bilgi.get('beta','?')}

Kısa, madde madde sabah raporu hazırla:
1) Piyasa özeti
2) Portföy durumu (varsa)
3) Dikkat edilmesi gereken haberler
4) Bugün için öneri (risk profiline göre)
Türkçe yaz, emoji kullan.""",
                        messages=[{"role":"user","content":"Bugünün sabah raporunu hazırla."}]
                    )
                    rapor = yanit.content[0].text
                    st.markdown(f"<div style='color:#e2e8f0;line-height:1.8;background:#1a1a2e;padding:20px;border-radius:12px;border:1px solid #2d2d4e;'>{rapor}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Rapor oluşturulamadı: {e}")
        else:
            st.info("'Raporu Oluştur' butonuna basarak AI destekli günlük sabah raporunuzu alın.")
            st.markdown("""
            <div class="kart">
                <div class="baslik">📋 Rapor İçeriği</div>
                <div class="meta" style="line-height:2;">
                ✅ Piyasa özeti<br>
                ✅ Portföyün güncel durumu<br>
                ✅ Önemli haberler<br>
                ✅ Risk profiline göre öneri
                </div>
            </div>""", unsafe_allow_html=True)

    # ─ TAB 7: Haberler ────────────────────────────────────────
    with tab7:
        st.markdown(f"<h4 style='color:#64ffda;'>📰 Haberler</h4>", unsafe_allow_html=True)
        kod = hisse.replace('.IS','').upper()
        kap_url = f"https://www.kap.org.tr/tr/Bildirim/Liste?hisse={kod}"
        st.markdown(f"<a href='{kap_url}' target='_blank' style='color:#64ffda;font-size:12px;'>📋 KAP Özel Durum Açıklamaları →</a>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown(f"<p style='color:#64ffda;font-size:13px;font-weight:600;'>🎯 {hisse} Haberleri</p>", unsafe_allow_html=True)
            tum_h = turkce_haberler_cek(hisse)
            hisse_h = [h for h in tum_h if h.get('onemli')]
            genel_h = [h for h in tum_h if not h.get('onemli')]
            if hisse_h:
                for h in hisse_h:
                    st.markdown(f"""<div class="kart kart-yesil">
                        <div class="baslik">{h['title']}</div>
                        <div class="meta">🕐 {h.get('pubDate','') or 'Yakın zamanda'} | <span style="color:#7c4dff;">{h.get('kaynak','')}</span> | <a href="{h.get('link','#')}" target="_blank" style="color:#64ffda;">Oku →</a></div>
                        {f"<div style='color:#8892b0;font-size:11px;margin-top:4px;'>{h['desc']}</div>" if h.get('desc') else ''}
                    </div>""", unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ {hisse} adına özel haber bulunamadı. KAP'a bakın.")

        with col_h2:
            st.markdown("<p style='color:#64ffda;font-size:13px;font-weight:600;'>🌍 Piyasa Haberleri</p>", unsafe_allow_html=True)
            for h in genel_h[:6]:
                st.markdown(f"""<div class="kart">
                    <div class="baslik">{h['title']}</div>
                    <div class="meta">🕐 {h.get('pubDate','') or ''} | <span style="color:#7c4dff;">{h.get('kaynak','')}</span> | <a href="{h.get('link','#')}" target="_blank" style="color:#64ffda;">Oku →</a></div>
                    {f"<div style='color:#8892b0;font-size:11px;margin-top:4px;'>{h['desc']}</div>" if h.get('desc') else ''}
                </div>""", unsafe_allow_html=True)

    # ─ TAB 8: Rasyolar ────────────────────────────────────────
    with tab8:
        st.markdown(f"<h4 style='color:#64ffda;'>📋 {hisse} Rasyolar & Sektör Karşılaştırması</h4>", unsafe_allow_html=True)
        rasyo_map = {
            'F/K':('trailingPE',''),'PD/DD':('priceToBook',''),'F/S':('priceToSalesTrailing12Months',''),
            'EV/FAVÖK':('enterpriseToEbitda',''),'Piyasa Değeri':('marketCap','B'),
            'Temettü %':('dividendYield','%'),'Beta':('beta',''),
            'Brüt Kar Marjı':('grossMargins','%'),'Net Kar Marjı':('profitMargins','%'),
            'ROE':('returnOnEquity','%'),'ROA':('returnOnAssets','%'),'Borç/Öz':('debtToEquity',''),
        }
        r_cols = st.columns(4)
        for i,(isim,(key,birim)) in enumerate(rasyo_map.items()):
            val = bilgi.get(key)
            if val is not None:
                if birim=='%': goster=f"{val*100:.1f}%"
                elif birim=='B': goster=f"${val/1e9:.1f}B" if val>1e9 else f"${val/1e6:.0f}M"
                else: goster=f"{val:.2f}"
            else: goster="—"
            with r_cols[i%4]:
                st.markdown(f'<div class="rasyo-kart"><div class="rasyo-deger">{goster}</div><div class="rasyo-isim">{isim}</div></div><br>', unsafe_allow_html=True)

        st.markdown("---")
        sektor = bilgi.get('sector',''); sanayi = bilgi.get('industry','')
        st.markdown(f"<p style='color:#8892b0;'>Sektör: <b style='color:#ccd6f6;'>{sektor}</b> | Sanayi: <b style='color:#ccd6f6;'>{sanayi}</b></p>", unsafe_allow_html=True)
        rakip_map = {'Airlines':['THYAO.IS','PEGYO.IS','UAL','DAL'],'Banks':['GARAN.IS','AKBNK.IS','YKBNK.IS','ISCTR.IS'],'Technology':['ASELS.IS','LOGO.IS','AAPL','MSFT'],'Energy':['TUPRS.IS','AYGAZ.IS','XOM','CVX']}
        rakipler = []
        for k,v in rakip_map.items():
            if k.lower() in sektor.lower() or k.lower() in sanayi.lower():
                rakipler = [r for r in v if r!=hisse][:4]; break
        if not rakipler: rakipler = ['GARAN.IS','AKBNK.IS','YKBNK.IS']
        karsilastirma = [{'Hisse':hisse+' ★','F/K':round(bilgi.get('trailingPE',0) or 0,2),'PD/DD':round(bilgi.get('priceToBook',0) or 0,2),'Beta':round(bilgi.get('beta',0) or 0,2),'Temettü%':round((bilgi.get('dividendYield',0) or 0)*100,2),'NetKar%':round((bilgi.get('profitMargins',0) or 0)*100,2)}]
        for r in rakipler:
            try:
                ri = yf.Ticker(r).info
                karsilastirma.append({'Hisse':r,'F/K':round(ri.get('trailingPE',0) or 0,2),'PD/DD':round(ri.get('priceToBook',0) or 0,2),'Beta':round(ri.get('beta',0) or 0,2),'Temettü%':round((ri.get('dividendYield',0) or 0)*100,2),'NetKar%':round((ri.get('profitMargins',0) or 0)*100,2)})
            except: pass
        st.dataframe(pd.DataFrame(karsilastirma).style.set_properties(**{'background-color':'#1a1a2e','color':'#e2e8f0','border':'1px solid #2d2d4e'}), use_container_width=True)

    # ─ TAB 9: AI Asistan ──────────────────────────────────────
    with tab9:
        st.markdown(f"<h4 style='color:#64ffda;'>🤖 AI Asistan — {hisse}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#8892b0;'>Risk profili: <b style='color:#64ffda;'>{risk_profil}</b> | Teknik + Temel + Haber analizi</p>", unsafe_allow_html=True)

        if "son_hisse" not in st.session_state: st.session_state.son_hisse = hisse
        if st.session_state.son_hisse != hisse:
            st.session_state.mesajlar = []; st.session_state.son_hisse = hisse
        if "mesajlar" not in st.session_state: st.session_state.mesajlar = []

        hafiza = hafiza_yukle()

        # Hızlı soru butonları
        st.markdown("<p style='color:#8892b0;font-size:12px;'>Hızlı sorular:</p>", unsafe_allow_html=True)
        hq1,hq2,hq3,hq4 = st.columns(4)
        if hq1.button("📊 Teknik analiz", key="hq1"): st.session_state.hizli_soru = f"{hisse} için detaylı teknik analiz yap"
        if hq2.button("💰 Al malı mıyım?", key="hq2"): st.session_state.hizli_soru = f"{hisse} şu an alınır mı? Risk profili: {risk_profil}"
        if hq3.button("📰 Haber yorumu", key="hq3"): st.session_state.hizli_soru = f"{hisse} ile ilgili son haberleri yorumla"
        if hq4.button("🎯 Hedef fiyat", key="hq4"): st.session_state.hizli_soru = f"{hisse} için 3-6 aylık hedef fiyat tahmini"

        for msg in st.session_state.mesajlar:
            with st.chat_message(msg["role"]):
                st.markdown(f"<div style='color:#e2e8f0;line-height:1.7;'>{msg['content']}</div>", unsafe_allow_html=True)

        hizli = st.session_state.pop("hizli_soru", None) if "hizli_soru" in st.session_state else None
        soru = st.chat_input(f"{hisse} hakkında sorun...") or hizli

        if soru:
            st.session_state.mesajlar.append({"role":"user","content":soru})
            with st.chat_message("user"):
                st.markdown(f"<div style='color:#e2e8f0;'>{soru}</div>", unsafe_allow_html=True)

            haberler_ozet = ""
            try:
                son_haberler = turkce_haberler_cek(hisse)
                if son_haberler:
                    haberler_ozet = "\n📰 SON HABERLER:\n"
                    for h in son_haberler[:5]:
                        haberler_ozet += f"- {h['title']} ({h.get('kaynak','')})\n"
            except: pass

            hafiza_ozet = ""
            if hafiza:
                hafiza_ozet = "\n🧠 ÖNCEKİ ANALİZLER:\n"
                for h in hafiza[-3:]:
                    hafiza_ozet += f"- [{h['tarih']}] {h['hisse']}: {h['ozet']}\n"

            temel_ozet = f"""
📋 TEMEL VERİLER: F/K:{bilgi.get('trailingPE','?')} | PD/DD:{bilgi.get('priceToBook','?')} | Beta:{bilgi.get('beta','?')} | NetKar:{round((bilgi.get('profitMargins',0) or 0)*100,1)}% | ROE:{round((bilgi.get('returnOnEquity',0) or 0)*100,1)}% | Temettü:{round((bilgi.get('dividendYield',0) or 0)*100,2)}%"""

            teknik_ozet = f"""
📊 TEKNİK VERİLER: Fiyat:{son:.2f}₺ ({degisim:+.1f}%) | RSI:{rsi:.1f} | MACD:{df['MACD'].iloc[-1]:.3f} | MA20:{df['MA20'].iloc[-1]:.2f} | MA50:{df['MA50'].iloc[-1]:.2f} | BB Üst:{df['BB_UST'].iloc[-1]:.2f} | Sinyal:{sinyal}({puan:+d})"""

            with st.chat_message("assistant"):
                with st.spinner("🧠 Analiz ediliyor..."):
                    try:
                        client = anthropic.Anthropic(api_key=API_KEY)
                        cevap = None
                        for deneme in range(3):
                            try:
                                yanit = client.messages.create(
                                    model="claude-haiku-4-5-20251001",
                                    max_tokens=1200,
                                    system=f"""Sen deneyimli bir borsa analistisisin. Analiz ettiğin hisse: {hisse}
Yatırımcının risk profili: {risk_profil}
{teknik_ozet}
{temel_ozet}
{haberler_ozet}
{hafiza_ozet}
Kurallar: 1) Teknik+temel+haber analizini birleştir 2) Risk profiline göre yorum yap 3) Kesin tavsiye değil olasılık sun 4) Türkçe, emoji kullan 5) Madde madde yaz""",
                                    messages=[{"role":"user","content":soru}]
                                )
                                cevap = yanit.content[0].text
                                break
                            except Exception as e:
                                if "overloaded" in str(e).lower() and deneme<2:
                                    st.toast(f"⏳ Sunucu yoğun, bekleniyor...")
                                    time.sleep(3*(deneme+1))
                                else: raise e

                        if cevap:
                            st.markdown(f"<div style='color:#e2e8f0;line-height:1.7;'>{cevap}</div>", unsafe_allow_html=True)
                            st.session_state.mesajlar.append({"role":"assistant","content":cevap})
                            # Hafızaya kaydet
                            hafiza.append({"tarih":str(datetime.date.today()),"hisse":hisse,"soru":soru[:80],"ozet":cevap[:150]})
                            hafiza_kaydet(hafiza)
                    except Exception as e:
                        st.error(f"AI hatası: {e}")

except Exception as e:
    st.error(f"Hata: {e}")
    st.info("Hisse kodunu kontrol edin. BIST için .IS ekleyin (örn: THYAO.IS)")
