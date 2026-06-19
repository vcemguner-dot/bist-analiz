"""
Bot stratejisi — cok faktorlu skorlama.
veri_katmani.Sirket'i temel veriler icin yeniden kullanir.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
import yfinance as yf

# Ust klasordeki veri_katmani'ni kullanabilmek icin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from veri_katmani import Sirket  # noqa: E402

# Bankalar/holdingler standart mali tablo vermedigi icin haric tutuldu
TAKIP = ["BIMAS", "ASELS", "THYAO", "EREGL", "TUPRS",
         "SISE", "FROTO", "TOASO", "TCELL", "MGROS"]
TUT = 3

AGIRLIK = {
    "Momentum": 0.25, "Trend": 0.15, "Deger": 0.20,
    "Kalite": 0.20, "DusukVol": 0.10, "RSI": 0.05, "Saglik": 0.05,
}

RAW = {
    "Momentum": ("%{:.0f}", "Momentum_raw"), "Trend": ("200g'ye gore %{:.0f}", "Trend_raw"),
    "Deger": ("F/K {:.1f}", "PE_raw"), "Kalite": ("ROE %{:.0f}", "ROE_raw"),
    "DusukVol": ("volatilite %{:.0f}", "Vol_raw"), "RSI": ("RSI {:.0f}", "RSI_raw"),
    "Saglik": ("Borc/Ozk {:.2f}", "DE_raw"),
}


def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _mcap(tk):
    try:
        return float(yf.Ticker(tk).fast_info["market_cap"])
    except Exception:
        try:
            return float(yf.Ticker(tk).info.get("marketCap"))
        except Exception:
            return None


def temel_veri(kod):
    """(pe, roe, de) — veri_katmani uzerinden. Eksikse None."""
    try:
        s = Sirket(kod)
        net = s.deger("3L")          # net kar
        oz = s.deger("2N")           # ozkaynak
        kb = s.deger("2A") or 0      # kisa vadeli borc
        ub = s.deger("2B") or 0      # uzun vadeli borc
        mcap = _mcap(kod + ".IS")
        pe = (mcap / net) if (mcap and net and net > 0) else None
        roe = (net / oz * 100) if (net and oz) else None
        de = ((kb + ub) / oz) if oz else None
        return pe, roe, de
    except Exception:
        return None, None, None


def faktor_tablosu(takip=TAKIP):
    data = yf.download([k + ".IS" for k in takip], period="2y",
                       auto_adjust=True)["Close"].ffill()
    satir = {}
    for k in takip:
        s = data[k + ".IS"].dropna()
        if len(s) < 210:
            continue
        sma200 = s.rolling(200).mean().iloc[-1]
        pe, roe, de = temel_veri(k)
        satir[k] = {
            "fiyat": float(s.iloc[-1]),
            "Momentum_raw": (s.iloc[-1] / s.iloc[-61] - 1) * 100,
            "Trend_raw": (s.iloc[-1] / sma200 - 1) * 100,
            "Vol_raw": s.pct_change().tail(30).std() * math.sqrt(252) * 100,
            "RSI_raw": float(rsi(s).iloc[-1]),
            "PE_raw": pe, "ROE_raw": roe, "DE_raw": de,
        }
    df = pd.DataFrame(satir).T

    df["Momentum"] = df["Momentum_raw"]
    df["Trend"] = df["Trend_raw"]
    df["DusukVol"] = -df["Vol_raw"]
    df["RSI"] = -df["RSI_raw"]
    df["Deger"] = df["PE_raw"].rdiv(1.0)
    df["Kalite"] = df["ROE_raw"]
    df["Saglik"] = -df["DE_raw"]

    for f in AGIRLIK:
        z = (df[f] - df[f].mean()) / df[f].std()
        df["z_" + f] = z.fillna(0)
    df["Skor"] = sum(AGIRLIK[f] * df["z_" + f] for f in AGIRLIK)
    return df.sort_values("Skor", ascending=False)


def tag(z):
    if z >= 1.0:  return "cok guclu"
    if z >= 0.4:  return "guclu"
    if z > -0.4:  return "ortalama"
    if z > -1.0:  return "zayif"
    return "cok zayif"


def ham(df, k, f):
    fmt, sut = RAW[f]
    v = df.loc[k, sut]
    return "veri yok" if pd.isna(v) else fmt.format(v)


def gerekce(df, k, n=2):
    zs = {f: df.loc[k, "z_" + f] for f in AGIRLIK}
    en = sorted(zs, key=zs.get, reverse=True)[:n]
    return [f"{f} {tag(zs[f])} ({ham(df,k,f)}, z{zs[f]:+.1f})" for f in en]
