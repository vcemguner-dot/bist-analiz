"""
Veri katmani — BIST sirket verileri.
Fiyat (yfinance) + mali tablo (isyatirimhisse) tek bir Sirket objesinde toplanir.
Tum modullerin (degerleme, portfoy, backtest) ortak temeli budur.
"""

import pandas as pd
import yfinance as yf


def usd_try():
    """Guncel USD/TRY kuru (1 dolar kac TL)."""
    return float(yf.Ticker("TRY=X").history(period="5d")["Close"].iloc[-1])


class Sirket:
    """Tek bir BIST sirketinin verilerini ceken ve saklayan sinif."""

    def __init__(self, kod):
        self.kod = kod.upper().replace(".IS", "").strip()
        self.yf_kod = self.kod + ".IS"
        self._fiyat = None
        self._mali = None

    # ---------- Fiyat ----------
    def fiyatlar(self, period="5y"):
        if self._fiyat is None:
            self._fiyat = yf.Ticker(self.yf_kod).history(period=period)
        return self._fiyat

    def son_fiyat(self):
        df = self.fiyatlar()
        return None if len(df) == 0 else float(df["Close"].iloc[-1])

    def lot_sayisi(self):
        try:
            return yf.Ticker(self.yf_kod).info.get("sharesOutstanding")
        except Exception:
            return None

    # ---------- Mali tablo ----------
    def mali_tablolar(self, baslangic=2021, bitis=2025):
        if self._mali is None:
            from isyatirimhisse import fetch_financials
            self._mali = fetch_financials(
                symbols=self.kod,
                start_year=str(baslangic),
                end_year=str(bitis),
                exchange="TRY",
            )
        return self._mali

    def kalem(self, kod):
        """Mali tablodan bir satiri Is Yatirim koduyla getirir (or. '3L')."""
        df = self.mali_tablolar()
        m = df["FINANCIAL_ITEM_CODE"].astype(str).str.upper() == kod.upper()
        return df[m].iloc[0] if m.any() else None

    def yil_sonu_sutunlari(self):
        df = self.mali_tablolar()
        cols = [c for c in df.columns if str(c).endswith("/12")]
        return sorted(cols, key=lambda c: int(str(c)[:4]))

    def son_donem(self):
        y = self.yil_sonu_sutunlari()
        return y[-1] if y else None

    def deger(self, kod, sutun=None):
        """Bir kalemin belirtilen donem degerini (float) getirir."""
        row = self.kalem(kod)
        if row is None:
            return None
        sutun = sutun or self.son_donem()
        try:
            v = row[sutun]
            return None if pd.isna(v) else float(v)
        except Exception:
            return None

    def nakit_son(self):
        """En son donem nakit ve nakit benzerleri (1AA), TL."""
        return self.deger("1AA")

    # ---------- USD serbest nakit akisi ----------
    def usd_fcf(self):
        """
        Yil -> USD serbest nakit akisi (FCF = Faaliyet NA - CapEx),
        her yil kendi yilinin ortalama kuruyla dolara cevrilir.
        """
        df = self.mali_tablolar()
        fx = yf.Ticker("TRY=X").history(period="10y")["Close"]
        fx_yil = fx.groupby(fx.index.year).mean()
        guncel = float(fx.iloc[-1])

        ocf = self.kalem("4C")      # Net Cash from Operations
        capex = self.kalem("4CAI")  # Capital Expenditures
        if ocf is None or capex is None:
            return {}

        out = {}
        for y in self.yil_sonu_sutunlari():
            yr = int(str(y)[:4])
            try:
                o = float(ocf[y]); c = float(capex[y])
            except Exception:
                continue
            kur = float(fx_yil.get(yr, guncel))
            out[yr] = (o - abs(c)) / kur
        return out
