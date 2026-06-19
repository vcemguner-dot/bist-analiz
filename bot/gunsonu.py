"""
Gun sonu raporu — bot/durum/raporlar/<tarih>.md uretir.
GitHub Actions her turdan sonra calistirir (rapor hep guncel kalir).
"""

import os
from datetime import date, datetime
from strateji import faktor_tablosu, AGIRLIK, gerekce
import cuzdan as C


def rapor_uret():
    df = faktor_tablosu()
    fiyat = {k: float(df.loc[k, "fiyat"]) for k in df.index}
    c = C.cuzdan_yukle()
    log = C.gunluk_oku()
    bugun = date.today().isoformat()

    toplam = c["nakit"] + sum(p["lot"] * fiyat.get(k, p["maliyet"])
                              for k, p in c["pozisyonlar"].items())
    onceki = C.deger_guncelle(toplam)
    gunluk = ((toplam / onceki - 1) * 100) if onceki else None
    bugunku = [r for r in log if str(r.get("zaman", ""))[:10] == bugun]

    L = [f"# Bot Gun Sonu Raporu — {bugun}\n", "## Ozet",
         f"- **Portfoy degeri:** {toplam:,.0f} TL"]
    if gunluk is not None:
        L.append(f"- **Gunluk degisim:** %{gunluk:+.2f}")
    L.append(f"- **Toplam getiri:** %{(toplam/C.BASLANGIC_NAKIT-1)*100:+.2f}")
    L.append(f"- **Nakit:** {c['nakit']:,.0f} TL\n")

    L.append("## Bugunku islemler")
    if bugunku:
        for r in bugunku:
            L.append(f"- **[{r['aksiyon']}] {r['kod']}** {r.get('lot','')} lot "
                     f"@ {r.get('fiyat','')} TL — {r['sebep']}")
    else:
        L.append("- Bugun islem yapilmadi; pozisyonlar korundu.")
    L.append("")

    L.append("## Mevcut pozisyonlar — neden elimizde?")
    if c["pozisyonlar"]:
        for k, p in c["pozisyonlar"].items():
            f = fiyat.get(k, p["maliyet"])
            kz = (f / p["maliyet"] - 1) * 100
            skor = df.loc[k, "Skor"] if k in df.index else float("nan")
            L.append(f"### {k} — {p['lot']} lot, K/Z %{kz:+.1f} (skor {skor:+.2f})")
            if k in df.index:
                for g in gerekce(df, k):
                    L.append(f"- {g}")
            L.append("")
    else:
        L.append("- Pozisyon yok (nakitte).\n")

    L.append("## Piyasa fotografi")
    for k in df.index:
        L.append(f"- {k}: skor {df.loc[k,'Skor']:+.2f}")
    L.append(f"\n_Uretim: {datetime.utcnow():%Y-%m-%d %H:%M} UTC · paper-trading, "
             "yatirim tavsiyesi degildir._")

    metin = "\n".join(L)
    yol = os.path.join(C.RAPOR_DIR, f"{bugun}.md")
    with open(yol, "w", encoding="utf-8") as f:
        f.write(metin)
    # En son raporu sabit isimle de tut (panel kolay okusun)
    with open(os.path.join(C.RAPOR_DIR, "son_rapor.md"), "w", encoding="utf-8") as f:
        f.write(metin)
    return yol


if __name__ == "__main__":
    print("Rapor:", rapor_uret())
