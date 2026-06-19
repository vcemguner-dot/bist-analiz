"""
Bir islem turu — GitHub Actions bunu calistirir.
Skorla -> hedefi belirle -> AL/SAT/TUT uygula -> kaydet + logla.
"""

from datetime import datetime
from strateji import faktor_tablosu, TUT, gerekce
import cuzdan as C


def tur_calistir():
    df = faktor_tablosu()
    fiyat = {k: float(df.loc[k, "fiyat"]) for k in df.index}
    hedef = df.head(TUT).index.tolist()
    c = C.cuzdan_yukle()
    zaman = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    kararlar, log = [], []

    # SAT
    for k in list(c["pozisyonlar"]):
        if k not in hedef:
            poz = c["pozisyonlar"][k]
            f = fiyat.get(k, poz["maliyet"])
            kz = (f / poz["maliyet"] - 1) * 100
            c["nakit"] += poz["lot"] * f
            sebep = f"ilk {TUT} disina dustu; gerceklesen K/Z %{kz:+.1f}"
            kararlar.append(("SAT", k, sebep))
            log.append({"zaman": zaman, "kod": k, "aksiyon": "SAT",
                        "lot": poz["lot"], "fiyat": round(f, 2), "sebep": sebep})
            del c["pozisyonlar"][k]

    # AL
    alinacak = [k for k in hedef if k not in c["pozisyonlar"]]
    if alinacak:
        pay = c["nakit"] / len(alinacak)
        for k in alinacak:
            f = fiyat[k]
            lot = int(pay // f)
            if lot > 0:
                c["nakit"] -= lot * f
                c["pozisyonlar"][k] = {"lot": lot, "maliyet": round(f, 2)}
                sebep = "ilk %d'e girdi — %s; skor %+.2f" % (
                    TUT, ", ".join(gerekce(df, k)), df.loc[k, "Skor"])
                kararlar.append(("AL", k, sebep))
                log.append({"zaman": zaman, "kod": k, "aksiyon": "AL",
                            "lot": lot, "fiyat": round(f, 2), "sebep": sebep})

    # TUT
    for k in hedef:
        if k in c["pozisyonlar"] and k not in alinacak:
            kararlar.append(("TUT", k, f"hala ilk {TUT}'te (skor {df.loc[k,'Skor']:+.2f})"))

    C.cuzdan_kaydet(c)
    C.gunluk_ekle(log)

    toplam = c["nakit"] + sum(p["lot"] * fiyat.get(k, p["maliyet"])
                              for k, p in c["pozisyonlar"].items())
    return c, kararlar, toplam


if __name__ == "__main__":
    c, kararlar, toplam = tur_calistir()
    print(f"[{datetime.utcnow():%Y-%m-%d %H:%M} UTC] Tur tamamlandi.")
    for a, k, s in kararlar:
        print(f"  [{a}] {k}: {s}")
    print(f"  Toplam deger: {toplam:,.0f} TL")
