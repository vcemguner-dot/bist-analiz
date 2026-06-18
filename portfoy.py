"""
Portfoy modulu — pozisyon takibi, kar/zarar, dagilim ve endeks kiyasi.
"""

import pandas as pd
import yfinance as yf


class Portfoy:
    def __init__(self):
        self.pozisyonlar = []

    def ekle(self, kod, lot, maliyet):
        self.pozisyonlar.append({
            "kod": kod.upper().replace(".IS", "").strip(),
            "lot": lot, "maliyet": maliyet,
        })
        return self

    @staticmethod
    def _fiyat(kod):
        try:
            h = yf.Ticker(kod + ".IS").history(period="5d")
            return float(h["Close"].iloc[-1]) if len(h) else None
        except Exception:
            return None

    def ozet(self):
        rows = []
        for p in self.pozisyonlar:
            f = self._fiyat(p["kod"])
            alis = p["lot"] * p["maliyet"]
            if f is None:
                rows.append({"Kod": p["kod"], "Lot": p["lot"], "Maliyet": p["maliyet"],
                             "Alis Tutari": alis, "Guncel Fiyat": None, "Guncel Deger": None,
                             "K/Z (TL)": None, "Getiri %": None, "Agirlik %": None})
                continue
            deger = p["lot"] * f
            rows.append({"Kod": p["kod"], "Lot": p["lot"], "Maliyet": p["maliyet"],
                         "Alis Tutari": alis, "Guncel Fiyat": f, "Guncel Deger": deger,
                         "K/Z (TL)": deger - alis, "Getiri %": (f / p["maliyet"] - 1) * 100,
                         "Agirlik %": None})
        df = pd.DataFrame(rows)
        toplam = df["Guncel Deger"].sum(skipna=True)
        if toplam and toplam > 0:
            df["Agirlik %"] = df["Guncel Deger"] / toplam * 100
        return df.round(2)


def portfoy_vs_endeks(pozisyonlar, period="1y"):
    """
    Pozisyonlari period basinda almis varsayar; portfoy degerini gun gun
    hesaplar ve BIST 100 (XU100) ile karsilastirir.
    Doner: (port_idx, xu_idx, metrikler) -- ikisi de basta 100.
    """
    kodlar = [x["kod"] for x in pozisyonlar]
    lotlar = {x["kod"]: x["lot"] for x in pozisyonlar}
    tickers = [k + ".IS" for k in kodlar] + ["XU100.IS"]

    data = yf.download(tickers, period=period, auto_adjust=True)["Close"].ffill().dropna()
    port = sum(data[k + ".IS"] * lotlar[k] for k in kodlar)

    port_idx = port / port.iloc[0] * 100
    xu_idx = data["XU100.IS"] / data["XU100.IS"].iloc[0] * 100

    metrik = {
        "Portfoy getirisi %": float(port_idx.iloc[-1] - 100),
        "BIST 100 getirisi %": float(xu_idx.iloc[-1] - 100),
    }
    metrik["Alfa %"] = metrik["Portfoy getirisi %"] - metrik["BIST 100 getirisi %"]
    return port_idx, xu_idx, metrik
