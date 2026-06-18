"""
BIST Analiz — interaktif web uygulamasi (Streamlit + Plotly)
Calistir:  streamlit run app.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from veri_katmani import Sirket, usd_try
from degerleme import Degerleme, dcf, dcf_duyarlilik, carpanlar
from portfoy import Portfoy, portfoy_vs_endeks
from backtest import backtest

st.set_page_config(page_title="BIST Analiz", page_icon="📈", layout="wide")

PRIMARY = "#0F6E56"
ACCENT = "#D85A30"
MUTED = "#888780"

# ---------------- Stil ----------------
st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.2rem; max-width: 1150px;}
.hero {
  background: linear-gradient(100deg, #0F6E56 0%, #1D9E75 100%);
  color: #fff; padding: 22px 28px; border-radius: 16px; margin-bottom: 18px;
}
.hero h1 {margin: 0; font-size: 26px; font-weight: 600;}
.hero p {margin: 4px 0 0; opacity: .9; font-size: 14px;}
[data-testid="stMetric"] {
  background: #F4F6F5; border: 1px solid #E3E7E5;
  border-radius: 12px; padding: 14px 16px;
}
[data-testid="stMetricLabel"] {color: #5F5E5A;}
.stTabs [data-baseweb="tab"] {font-size: 15px; font-weight: 500;}
.note {color: #888780; font-size: 13px;}
</style>
""", unsafe_allow_html=True)


# ---------------- Cache ----------------
@st.cache_data(ttl=3600, show_spinner="Veriler getiriliyor...")
def yukle(kod):
    s = Sirket(kod)
    hist = s.fiyatlar(period="2y")
    return {
        "fiyat": s.son_fiyat(),
        "lot": s.lot_sayisi(),
        "oranlar": Degerleme(s).oranlar(),
        "fcf": s.usd_fcf(),
        "carpan": carpanlar(s, s.son_fiyat(), s.lot_sayisi()),
        "nakit": s.nakit_son(),
        "hist": hist[["Open", "High", "Low", "Close"]].copy(),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def kur_al():
    return usd_try()


def plot_stil(fig, h=380):
    fig.update_layout(
        height=h, template="plotly_white",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        font=dict(family="sans-serif", size=13),
    )
    return fig


# ---------------- Kenar cubugu ----------------
st.sidebar.markdown("### 📈 BIST Analiz")
kod = st.sidebar.text_input("Hisse kodu", value="BIMAS").upper().strip()
st.sidebar.caption("Ornek: BIMAS, ASELS, THYAO, GARAN, EREGL")
st.sidebar.divider()
st.sidebar.caption("Egitim ve kisisel arastirma amaclidir. Yatirim tavsiyesi degildir.")

# ---------------- Hero ----------------
st.markdown(
    f"<div class='hero'><h1>{kod} — Yatirim Analizi</h1>"
    f"<p>Temel analiz · DCF degerleme · portfoy · backtest</p></div>",
    unsafe_allow_html=True,
)

try:
    v = yukle(kod)
except Exception as e:
    st.error(f"Veri alinamadi: {e}")
    st.stop()

t1, t2, t3, t4 = st.tabs(["  Genel  ", "  DCF  ", "  Portfoy  ", "  Backtest  "])

# ================= GENEL =================
with t1:
    c = st.columns(4)
    c[0].metric("Son fiyat", f"{v['fiyat']:.2f} TL" if v["fiyat"] else "-")
    pd_tl = v["carpan"].get("Piyasa Degeri (mn TL)")
    c[1].metric("Piyasa degeri", f"{pd_tl/1000:.1f} mlr TL" if pd_tl else "-")
    fk = v["carpan"].get("F/K")
    c[2].metric("F/K", f"{fk:.1f}" if fk else "-")
    pddd = v["carpan"].get("PD/DD")
    c[3].metric("PD/DD", f"{pddd:.2f}" if pddd else "-")

    st.markdown("#### Fiyat ve hareketli ortalamalar")
    h = v["hist"]
    sma50 = h["Close"].rolling(50).mean()
    sma200 = h["Close"].rolling(200).mean()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=h.index, open=h["Open"], high=h["High"],
                                 low=h["Low"], close=h["Close"], name="Fiyat",
                                 increasing_line_color=PRIMARY, decreasing_line_color=ACCENT))
    fig.add_trace(go.Scatter(x=h.index, y=sma50, name="50 SMA", line=dict(color="#378ADD", width=1.4)))
    fig.add_trace(go.Scatter(x=h.index, y=sma200, name="200 SMA", line=dict(color="#BA7517", width=1.4)))
    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(plot_stil(fig, 420), use_container_width=True)

    cc = st.columns([3, 2])
    with cc[0]:
        st.markdown("#### Finansal oranlar (yil sonu)")
        st.dataframe(v["oranlar"], use_container_width=True)
    with cc[1]:
        if v["fcf"]:
            st.markdown("#### USD serbest nakit akisi")
            fcf_yil = {str(k): round(val / 1e6) for k, val in v["fcf"].items()}
            fig2 = go.Figure(go.Bar(x=list(fcf_yil.keys()), y=list(fcf_yil.values()),
                                    marker_color=PRIMARY, text=list(fcf_yil.values()),
                                    textposition="outside"))
            fig2.update_layout(yaxis_title="mn USD")
            st.plotly_chart(plot_stil(fig2, 320), use_container_width=True)

# ================= DCF =================
with t2:
    st.markdown("#### USD bazli DCF degerleme")
    fcf = v["fcf"]
    if not fcf or not v["lot"]:
        st.warning("DCF icin yeterli veri yok (FCF veya hisse sayisi eksik).")
    else:
        ort = sum(fcf.values()) / len(fcf) / 1e6
        kur = kur_al()
        nakit_usd = (v["nakit"] / kur / 1e6) if v["nakit"] else 0

        c = st.columns(4)
        fcf0 = c[0].slider("Baslangic FCF (mn USD)", 100, 2000, int(round(ort)), 10)
        g = c[1].slider("Buyume g %", 0.0, 15.0, 6.0, 0.5) / 100
        wacc = c[2].slider("WACC %", 8.0, 22.0, 14.0, 0.5) / 100
        tg = c[3].slider("Terminal buyume %", 0.0, 5.0, 3.0, 0.25) / 100

        net_borc = st.number_input(
            "Net borc (mn USD) — TFRS 16 kira borcu buraya eklenebilir",
            value=float(round(-nakit_usd)), step=10.0,
            help="Pozitif = net borclu (degeri dusurur), negatif = net nakit.")

        r = dcf(fcf0, v["lot"], kur, v["fiyat"], g=g, wacc=wacc,
                terminal_g=tg, net_borc_usd=net_borc)
        prim = r["Prim/Iskonto %"]

        m = st.columns(3)
        m[0].metric("Adil deger / hisse", f"{r['Adil deger / hisse (TL)']:.0f} TL",
                    f"{prim:+.0f}% vs fiyat")
        m[1].metric("Sirket degeri (EV)", f"{r['Sirket Degeri (mn USD)']:,.0f} mn USD")
        m[2].metric("USD adil deger", f"{r['Adil deger / hisse (USD)']:.2f}")

        if prim is not None:
            if prim > 15:
                st.success(f"Iskontolu gorunuyor ({prim:+.0f}%)")
            elif prim < -15:
                st.error(f"Pahali gorunuyor ({prim:+.0f}%)")
            else:
                st.warning(f"Makul / adil deger civari ({prim:+.0f}%)")

        pe, pt = r["PV ilk donem (mn USD)"], r["PV terminal (mn USD)"]
        st.markdown(f"<span class='note'>Degerin %{round(pt/(pe+pt)*100)}'i terminal "
                    "degerden geliyor — en belirsiz kisim.</span>", unsafe_allow_html=True)

        st.markdown("#### Duyarlilik: WACC × buyume (adil deger TL)")
        wacc_list = [round(wacc + d, 4) for d in (-0.02, -0.01, 0, 0.01, 0.02)]
        g_list = [round(g + d, 4) for d in (-0.02, -0.01, 0, 0.01, 0.02)]
        grid = dcf_duyarlilik(fcf0, v["lot"], kur, v["fiyat"], wacc_list, g_list,
                              terminal_g=tg, net_borc_usd=net_borc)
        upside = (grid / v["fiyat"] - 1) * 100
        fig3 = go.Figure(go.Heatmap(
            z=upside.values, x=grid.columns, y=grid.index,
            text=grid.values, texttemplate="%{text} TL",
            colorscale="RdYlGn", zmid=0,
            colorbar=dict(title="vs fiyat %")))
        fig3.update_layout(xaxis_title="Buyume g", yaxis_title="WACC")
        st.plotly_chart(plot_stil(fig3, 360), use_container_width=True)
        st.markdown("<span class='note'>Yesil = mevcut fiyatin uzerinde (iskontolu), "
                    "kirmizi = altinda (pahali). Ortadaki hucre senin sectigin varsayim.</span>",
                    unsafe_allow_html=True)

# ================= PORTFOY =================
with t3:
    st.markdown("#### Portfoy")
    st.caption("Pozisyonlarini duzenle (lot = adet, maliyet = alis fiyati TL), sonra Hesapla.")
    varsayilan = pd.DataFrame([
        {"kod": "BIMAS", "lot": 50, "maliyet": 300.0},
        {"kod": "ASELS", "lot": 100, "maliyet": 80.0},
        {"kod": "THYAO", "lot": 30, "maliyet": 250.0},
        {"kod": "GARAN", "lot": 200, "maliyet": 90.0},
    ])
    duzen = st.data_editor(varsayilan, num_rows="dynamic", use_container_width=True,
                           key="portfoy_editor")

    if st.button("Hesapla", type="primary"):
        pozlar = [{"kod": str(rw["kod"]).upper().strip(), "lot": int(rw["lot"]),
                   "maliyet": float(rw["maliyet"])}
                  for _, rw in duzen.iterrows() if str(rw["kod"]).strip()]
        p = Portfoy()
        for x in pozlar:
            p.ekle(x["kod"], x["lot"], x["maliyet"])
        df = p.ozet()

        t_alis = df["Alis Tutari"].sum(skipna=True)
        t_deger = df["Guncel Deger"].sum(skipna=True)
        mc = st.columns(2)
        mc[0].metric("Toplam deger", f"{t_deger:,.0f} TL",
                     f"{(t_deger/t_alis-1)*100:+.1f}%")
        mc[1].metric("Toplam maliyet", f"{t_alis:,.0f} TL")

        st.dataframe(df, use_container_width=True)

        cc = st.columns(2)
        with cc[0]:
            gg = df.dropna(subset=["Guncel Deger"])
            fig = go.Figure(go.Pie(labels=gg["Kod"], values=gg["Guncel Deger"], hole=0.5))
            fig.update_layout(title="Dagilim")
            st.plotly_chart(plot_stil(fig, 340), use_container_width=True)
        with cc[1]:
            try:
                pidx, xidx, met = portfoy_vs_endeks(pozlar)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=pidx.index, y=pidx.values, name="Portfoy",
                                         line=dict(color=PRIMARY, width=2)))
                fig.add_trace(go.Scatter(x=xidx.index, y=xidx.values, name="BIST 100",
                                         line=dict(color=MUTED, width=2, dash="dash")))
                fig.update_layout(title="Portfoy vs BIST 100 (1 yil, baslangic=100)")
                st.plotly_chart(plot_stil(fig, 340), use_container_width=True)
                st.metric("Alfa (endekse gore)", f"{met['Alfa %']:+.1f}%",
                          "endeksi yendin" if met["Alfa %"] > 0 else "altinda")
            except Exception as e:
                st.info(f"Endeks kiyasi yapilamadi: {e}")

# ================= BACKTEST =================
with t4:
    st.markdown("#### Backtest — hareketli ortalama kesisimi")
    c = st.columns(4)
    kisa = c[0].slider("Kisa SMA", 5, 100, 50, 5)
    uzun = c[1].slider("Uzun SMA", 50, 300, 200, 10)
    komp = c[2].slider("Komisyon %", 0.0, 1.0, 0.2, 0.05) / 100
    donem = c[3].selectbox("Donem", ["2y", "5y", "10y"], index=1)

    if st.button("Backtest calistir", type="primary"):
        try:
            strat, altut, met = backtest(kod, kisa, uzun, komp, donem)
            mc = st.columns(3)
            mc[0].metric("Strateji", f"{met['Strateji getirisi %']:+.0f}%")
            mc[1].metric("Al-tut", f"{met['Al-tut getirisi %']:+.0f}%")
            fark = met["Strateji getirisi %"] - met["Al-tut getirisi %"]
            mc[2].metric("Fark", f"{fark:+.0f}%",
                         "strateji onde" if fark > 0 else "al-tut onde")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=strat.index, y=strat.values, name="Strateji",
                                     line=dict(color=PRIMARY, width=2)))
            fig.add_trace(go.Scatter(x=altut.index, y=altut.values, name="Al-tut",
                                     line=dict(color=ACCENT, width=2, dash="dash")))
            fig.update_layout(title="Sermaye egrisi (1 TL baslangic)", yaxis_title="kat")
            st.plotly_chart(plot_stil(fig, 420), use_container_width=True)
            st.markdown(f"<span class='note'>Islem sayisi: {met['Islem sayisi']} · "
                        f"Strateji max dip: {met['Strateji max dip %']:.0f}% · "
                        f"Al-tut max dip: {met['Al-tut max dip %']:.0f}%</span>",
                        unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Backtest hatasi: {e}")
