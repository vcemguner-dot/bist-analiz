"""
Degerleme modulu — finansal oranlar + USD bazli DCF + carpanlar + duyarlilik.
Is Yatirim kalem kodlari ekran goruntulerinden dogrulanmistir (kesin).
"""

import pandas as pd
from veri_katmani import Sirket


def _bol(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def _yuzde(a, b):
    r = _bol(a, b)
    return None if r is None else r * 100


class Degerleme:
    """Bir Sirket'in mali tablolarindan finansal oran hesaplar."""

    KODLAR = {
        "Donen Varliklar":  "1A",
        "Toplam Varliklar": "1BL",
        "Kisa Vadeli Borc": "2A",
        "Uzun Vadeli Borc": "2B",
        "Ozkaynak":         "2N",
        "Satis Gelirleri":  "3C",
        "Brut Kar":         "3D",
        "Faaliyet Kari":    "3DF",
        "Net Kar":          "3L",
    }

    def __init__(self, sirket):
        self.s = sirket
        self.satirlar = {ad: sirket.kalem(kod) for ad, kod in self.KODLAR.items()}

    @staticmethod
    def _deger(row, sutun):
        if row is None:
            return None
        try:
            v = row[sutun]
            return None if pd.isna(v) else float(v)
        except Exception:
            return None

    def oranlar(self, yil_sayisi=4):
        yillar = self.s.yil_sonu_sutunlari()[-yil_sayisi:]
        tablo = {}
        for y in yillar:
            g = {ad: self._deger(r, y) for ad, r in self.satirlar.items()}
            satis, net, oz = g["Satis Gelirleri"], g["Net Kar"], g["Ozkaynak"]
            ta, kb, ub = g["Toplam Varliklar"], g["Kisa Vadeli Borc"], g["Uzun Vadeli Borc"]
            borc = None if (kb is None and ub is None) else (kb or 0) + (ub or 0)
            tablo[str(y)[:4]] = {
                "Net Marj %":      _yuzde(net, satis),
                "Brut Marj %":     _yuzde(g["Brut Kar"], satis),
                "Faaliyet Marj %": _yuzde(g["Faaliyet Kari"], satis),
                "ROE %":           _yuzde(net, oz),
                "ROA %":           _yuzde(net, ta),
                "Cari Oran":       _bol(g["Donen Varliklar"], kb),
                "Borc/Ozkaynak":   _bol(borc, oz),
            }
        return pd.DataFrame(tablo).round(2)


def carpanlar(sirket, fiyat_tl, lot):
    """Piyasa carpanlari: F/K, PD/DD, piyasa degeri."""
    d = Degerleme(sirket)
    son = sirket.son_donem()
    net = Degerleme._deger(d.satirlar["Net Kar"], son)
    oz = Degerleme._deger(d.satirlar["Ozkaynak"], son)
    mcap = (fiyat_tl or 0) * (lot or 0)
    return {
        "Piyasa Degeri (mn TL)": mcap / 1e6 if mcap else None,
        "F/K": _bol(mcap, net),
        "PD/DD": _bol(mcap, oz),
    }


def dcf(fcf0_usd, shares, kur, fiyat_tl,
        g=0.06, wacc=0.14, terminal_g=0.03, yil=10, net_borc_usd=0.0):
    """USD bazli DCF. Doner: adil deger, primler, PV bilesenleri."""
    pv_explicit = 0.0
    fcf_t = fcf0_usd
    for t in range(1, yil + 1):
        fcf_t = fcf0_usd * (1 + g) ** t
        pv_explicit += fcf_t / (1 + wacc) ** t

    tv = fcf_t * (1 + terminal_g) / (wacc - terminal_g)
    pv_tv = tv / (1 + wacc) ** yil

    ev = pv_explicit + pv_tv
    ozkaynak_deger = ev - net_borc_usd
    hisse_usd = ozkaynak_deger * 1e6 / shares
    hisse_tl = hisse_usd * kur
    prim = (hisse_tl / fiyat_tl - 1) * 100 if fiyat_tl else None

    return {
        "Sirket Degeri (mn USD)": ev,
        "PV ilk donem (mn USD)": pv_explicit,
        "PV terminal (mn USD)": pv_tv,
        "Adil deger / hisse (USD)": hisse_usd,
        "Adil deger / hisse (TL)": hisse_tl,
        "Mevcut fiyat (TL)": fiyat_tl,
        "Prim/Iskonto %": prim,
    }


def dcf_duyarlilik(fcf0_usd, shares, kur, fiyat_tl,
                   wacc_list, g_list, terminal_g=0.03, net_borc_usd=0.0, yil=10):
    """
    WACC (satir) x buyume (sutun) icin adil deger (TL) tablosu.
    Doner: DataFrame (index=WACC, columns=buyume).
    """
    grid = {}
    for g in g_list:
        col = {}
        for w in wacc_list:
            r = dcf(fcf0_usd, shares, kur, fiyat_tl, g=g, wacc=w,
                    terminal_g=terminal_g, net_borc_usd=net_borc_usd, yil=yil)
            col[f"{w*100:.0f}%"] = round(r["Adil deger / hisse (TL)"])
        grid[f"{g*100:.0f}%"] = col
    return pd.DataFrame(grid)
