"""
Bot cuzdani — JSON kalici hafiza, islem gunlugu, gunluk deger gecmisi.
"""

import os
import json
from datetime import date

DURUM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "durum")
CUZDAN_DOSYA = os.path.join(DURUM, "cuzdan.json")
GUNLUK_DOSYA = os.path.join(DURUM, "islemler.json")
DEGER_DOSYA = os.path.join(DURUM, "gunluk_deger.json")
RAPOR_DIR = os.path.join(DURUM, "raporlar")
BASLANGIC_NAKIT = 100_000


def _hazirla():
    os.makedirs(RAPOR_DIR, exist_ok=True)


def _yukle(dosya, varsayilan):
    if os.path.exists(dosya):
        with open(dosya, encoding="utf-8") as f:
            return json.load(f)
    return varsayilan


def _yaz(dosya, veri):
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=2, ensure_ascii=False)


def cuzdan_yukle():
    return _yukle(CUZDAN_DOSYA, {"nakit": BASLANGIC_NAKIT, "pozisyonlar": {}})


def cuzdan_kaydet(c):
    _hazirla()
    _yaz(CUZDAN_DOSYA, c)


def gunluk_ekle(kayitlar):
    if not kayitlar:
        return
    _hazirla()
    log = _yukle(GUNLUK_DOSYA, [])
    log.extend(kayitlar)
    _yaz(GUNLUK_DOSYA, log)


def gunluk_oku():
    return _yukle(GUNLUK_DOSYA, [])


def deger_guncelle(toplam):
    """Bugunku degeri kaydeder, onceki gunun degerini dondurur."""
    _hazirla()
    bugun = date.today().isoformat()
    hist = _yukle(DEGER_DOSYA, [])
    onceki = None
    if hist:
        onceki = hist[-1]["deger"] if hist[-1]["tarih"] != bugun else \
            (hist[-2]["deger"] if len(hist) >= 2 else None)
    hist = [h for h in hist if h["tarih"] != bugun]
    hist.append({"tarih": bugun, "deger": round(toplam)})
    _yaz(DEGER_DOSYA, hist)
    return onceki
