"""
Backtest modulu — hareketli ortalama kesisimi stratejisi.
Look-ahead, islem maliyeti ve al-tut kiyasi dahil.
"""

import yfinance as yf


def _max_dusus(kum):
    tepe = kum.cummax()
    return float(((kum / tepe) - 1).min() * 100)


def backtest(ticker, kisa=50, uzun=200, komisyon=0.002, period="5y"):
    """
    Doner: (strateji_kum, altut_kum, metrikler)
    strateji_kum / altut_kum: 1 TL baslangicli sermaye serileri.
    """
    close = yf.Ticker(ticker.upper().replace(".IS", "") + ".IS")\
        .history(period=period)["Close"].dropna()

    sma_k = close.rolling(kisa).mean()
    sma_u = close.rolling(uzun).mean()
    sinyal = (sma_k > sma_u).astype(int)

    pozisyon = sinyal.shift(1).fillna(0)        # look-ahead onleme
    gun = close.pct_change().fillna(0)
    islem = pozisyon.diff().abs().fillna(0)     # pozisyon degisimi = islem
    strat_net = pozisyon * gun - islem * komisyon

    strat_kum = (1 + strat_net).cumprod()
    altut_kum = (1 + gun).cumprod()

    metrik = {
        "Strateji getirisi %": float((strat_kum.iloc[-1] - 1) * 100),
        "Al-tut getirisi %": float((altut_kum.iloc[-1] - 1) * 100),
        "Islem sayisi": int(islem.sum()),
        "Strateji max dip %": _max_dusus(strat_kum),
        "Al-tut max dip %": _max_dusus(altut_kum),
    }
    return strat_kum, altut_kum, metrik
