from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

OY_DOSYASI = "votes.txt"

YARIS_BASLANGIC = None 

ULKE_SOZLUGU = {
    "Australian": "Avustralya", "Australia": "Avustralya",
    "British": "Birleşik Krallık", "United Kingdom": "Birleşik Krallık",
    "Italian": "İtalya", "Italy": "İtalya",
    "Dutch": "Hollanda", "Netherlands": "Hollanda",
    "Japanese": "Japonya", "Japan": "Japonya",
    "Monegasque": "Monako", "Monégasque": "Monako", "Monaco": "Monako",
    "Thai": "Tayland", "Thailand": "Tayland",
    "Spanish": "İspanya", "Spain": "İspanya",
    "New Zealander": "Yeni Zelanda", "New Zealand": "Yeni Zelanda",
    "French": "Fransa", "France": "Fransa",
    "Canadian": "Kanada", "Canada": "Kanada",
    "German": "Almanya", "Germany": "Almanya",
    "Danish": "Danimarka", "Denmark": "Danimarka",
    "Chinese": "Çin", "China": "Çin",
    "Finnish": "Finlandiya", "Finland": "Finlandiya",
    "Brazilian": "Brezilya", "Brazil": "Brezilya",
    "Mexican": "Meksika", "Mexico": "Meksika",
    "Argentine": "Arjantin", "Argentina": "Arjantin"
}

PILOTLAR_DB = [
    {"isim": "Oscar Piastri",    "takim": "McLaren",       "wiki": "Oscar_Piastri"},
    {"isim": "Lando Norris",     "takim": "McLaren",       "wiki": "Lando_Norris"},
    {"isim": "George Russell",   "takim": "Mercedes",      "wiki": "George_Russell_(racing_driver)"},
    {"isim": "Kimi Antonelli",   "takim": "Mercedes",      "wiki": "Andrea_Kimi_Antonelli"},
    {"isim": "Max Verstappen",   "takim": "Red Bull Racing","wiki": "Max_Verstappen"},
    {"isim": "Yuki Tsunoda",     "takim": "Red Bull Racing","wiki": "Yuki_Tsunoda"},
    {"isim": "Charles Leclerc",  "takim": "Ferrari",       "wiki": "Charles_Leclerc"},
    {"isim": "Lewis Hamilton",   "takim": "Ferrari",       "wiki": "Lewis_Hamilton"},
    {"isim": "Alexander Albon",  "takim": "Williams",      "wiki": "Alexander_Albon"},
    {"isim": "Carlos Sainz",     "takim": "Williams",      "wiki": "Carlos_Sainz_Jr."},
    {"isim": "Liam Lawson",      "takim": "Racing Bulls",  "wiki": "Liam_Lawson"},
    {"isim": "Isack Hadjar",     "takim": "Racing Bulls",  "wiki": "Isack_Hadjar"},
    {"isim": "Lance Stroll",     "takim": "Aston Martin",  "wiki": "Lance_Stroll"},
    {"isim": "Fernando Alonso",  "takim": "Aston Martin",  "wiki": "Fernando_Alonso"},
    {"isim": "Esteban Ocon",     "takim": "Haas F1 Team",  "wiki": "Esteban_Ocon"},
    {"isim": "Oliver Bearman",   "takim": "Haas F1 Team",  "wiki": "Oliver_Bearman"},
    {"isim": "Nico Hulkenberg",  "takim": "Kick Sauber",   "wiki": "Nico_Hülkenberg"},
    {"isim": "Gabriel Bortoleto","takim": "Kick Sauber",   "wiki": "Gabriel_Bortoleto"},
    {"isim": "Pierre Gasly",     "takim": "Alpine",        "wiki": "Pierre_Gasly"},
    {"isim": "Franco Colapinto", "takim": "Alpine",        "wiki": "Franco_Colapinto"},
]

RESIMLER = {
    "Oscar_Piastri": "/static/piastri.png",
    "Lando_Norris": "/static/norris.png",
    "George_Russell_(racing_driver)": "/static/russell.png",
    "Andrea_Kimi_Antonelli": "/static/antonelli.png",
    "Max_Verstappen": "/static/verstappen.png",
    "Yuki_Tsunoda": "/static/tsunoda.png",
    "Charles_Leclerc": "/static/leclerc.png",
    "Lewis_Hamilton": "/static/hamilton.png",
    "Alexander_Albon": "/static/Albon.png",
    "Carlos_Sainz_Jr.": "/static/sainz.png",
    "Liam_Lawson": "/static/lawson.png",
    "Isack_Hadjar": "/static/hadjar.png",
    "Lance_Stroll": "/static/stroll.png",
    "Fernando_Alonso": "/static/alonso.png",
    "Esteban_Ocon": "/static/ocon.png",
    "Oliver_Bearman": "/static/bearman.png",
    "Nico_Hülkenberg": "/static/hulkenberg.png",
    "Gabriel_Bortoleto": "/static/bortoleto.png",
    "Pierre_Gasly": "/static/gasly.png",
    "Franco_Colapinto": "/static/colapinto.png",
}

def veriyi_temizle(metin, veri_tipi=None):
    if not metin: return "0"
    
    # Parantezleri ve içindekileri sil (Örn: "33 (2016-)")
    temiz = re.sub(r'\[.*?\]', '', metin) # Köşeli [1]
    temiz = re.sub(r'\(.*?\)', '', temiz) # Normal (2024)
    
    temiz = temiz.strip()
    
    # Ülke Çevirisi
    if veri_tipi == "ulke":
        for ingilizce, turkce in ULKE_SOZLUGU.items():
            if ingilizce in temiz:
                return turkce
                
    return temiz

def wikipedia_kaziyici(wiki_url):
    url = f"https://en.wikipedia.org/wiki/{wiki_url}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = {"no": "??", "ulke": "-", "podyum": "0", "sampiyonluk": "0", "pol": "0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            infobox = soup.find("table", class_="infobox")
            
            if infobox:
                rows = infobox.find_all("tr")
                for row in rows:
                    header = row.find("th")
                    value = row.find("td")
                    
                    if header and value:
                        h_text = header.text.strip().lower()
                        v_text = value.text.strip()
                        
                        if any(x in h_text for x in ["car number", "car no", "number"]):
                            data["no"] = veriyi_temizle(v_text)
                        elif "nationality" in h_text:
                            data["ulke"] = veriyi_temizle(v_text, veri_tipi="ulke")
                        elif "podiums" in h_text:
                            data["podyum"] = veriyi_temizle(v_text)
                        elif "championships" in h_text:
                            data["sampiyonluk"] = veriyi_temizle(v_text)
                        elif "pole positions" in h_text:
                            data["pol"] = veriyi_temizle(v_text)
                            
    except Exception as e:
        print(f"Hata ({wiki_url}): {e}")
        
    return data

def pilotlari_yukle():
    print("\n" + "="*60)
    print("🌍 WIKIPEDIA (DÜZELTİLMİŞ) VERİ ÇEKİLİYOR...")
    print("="*60)
    
    final_liste = []
    
    for pilot in PILOTLAR_DB:
        print(f"🔍 İşleniyor: {pilot['isim']}...", end=" ")
        
        # Web'den çek
        web_verisi = wikipedia_kaziyici(pilot['wiki'])
        
        # DÜZELTMELER
        
        #  Max Verstappen "331" veya "133" gelirse "1" yap
        if pilot['isim'] == "Max Verstappen":
            if len(web_verisi['no']) > 2 or "33" in web_verisi['no']:
                web_verisi['no'] = "1"
        
        #  Ülke çevirisi çalışmadıysa manuel zorla
        if pilot['isim'] == "Charles Leclerc" and web_verisi['ulke'] == "-":
             web_verisi['ulke'] = "Monako"

        # Terminale rapor ver
        print(f"-> {web_verisi['ulke']} | No: {web_verisi['no']}")
        
        final_liste.append({
            "isim": pilot['isim'],
            "takim": pilot['takim'],
            "resim": RESIMLER.get(pilot['wiki'],""), 
            "no": web_verisi['no'],
            "ulke": web_verisi['ulke'],
            "pol": web_verisi['pol'],
            "podyum": web_verisi['podyum'],
            "sampiyonluk": web_verisi['sampiyonluk']
        })
        
    print("\n✅ TÜM VERİLER BAŞARIYLA ALINDI!\n")
    return final_liste

PILOTLAR = pilotlari_yukle()

# Sıralama
def siralamayi_hesapla():
    skor_tablosu = {p['isim']: 0 for p in PILOTLAR}
    if os.path.exists(OY_DOSYASI):
        with open(OY_DOSYASI, "r", encoding="utf-8") as dosya:
            for satir in dosya:
                parcalar = satir.strip().split(",")
                if len(parcalar) == 2:
                    pilot = parcalar[1].strip()
                    for p_isim in skor_tablosu.keys():
                        if pilot == p_isim:
                            skor_tablosu[p_isim] += 1
    sirali = sorted(skor_tablosu.items(), key=lambda x: x[1], reverse=True)
    resimli_siralama = []
    for isim, puan in sirali:
        bilgi = next((p for p in PILOTLAR if p['isim'] == isim), None)
        if bilgi:
            resimli_siralama.append({
                "isim": isim,
                "puan": puan,
                "resim": bilgi['resim'],
                "takim": bilgi['takim']
            })
    return resimli_siralama

# ZAMANLAYICI 
def sure_hesapla():
    global YARIS_BASLANGIC
    
    # Butona basılmadıysa
    if YARIS_BASLANGIC is None:
        return "Yarış Başlamadı 🔴"
        
    simdi = datetime.now()
    gecen_sure = simdi - YARIS_BASLANGIC
    toplam_sure = timedelta(hours=1) # 1 Saatlik Yarış
    
    kalan = toplam_sure - gecen_sure
    
    if kalan.total_seconds() <= 0:
        return "Yarış Bitti! 🏁"
    
    # Süreyi hesapla
    dakika = int(kalan.total_seconds() // 60)
    saniye = int(kalan.total_seconds() % 60)
    return f"{dakika} Dk, {saniye} Sn"

@app.route('/')
def ana_sayfa():
    aranan = request.args.get('q', '').lower()
    liste_durumu = request.args.get('liste', 'kapali') 
    gonderilecek = []
    if aranan:
        liste_durumu = 'acik'
        for p in PILOTLAR:
            if aranan in p['isim'].lower() or aranan in p['takim'].lower():
                gonderilecek.append(p)
    else:
        gonderilecek = PILOTLAR
    siralama = siralamayi_hesapla()
    podyum = siralama[:3]
    return render_template('index.html', pilotlar=gonderilecek, siralama=siralama, podyum=podyum, sure=sure_hesapla(), durum=liste_durumu)

# OY EKRANI 
@app.route('/oy-ekrani/<pilot_ismi>')
def oy_ekrani(pilot_ismi):
    # KONTROL 1: Yarış Başladı mı?
    if YARIS_BASLANGIC is None:
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış henüz başlamadı! Lütfen önce 'YARIŞI BAŞLAT' butonuna basın.", durum="hata")
    
    # KONTROL 2: Yarış Bitti mi? (1 Saat = 3600 Saniye)
    simdi = datetime.now()
    gecen_sure = simdi - YARIS_BASLANGIC
    if gecen_sure.total_seconds() > 3600: 
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış süresi doldu! Artık oy kullanamazsınız.", durum="hata")

    # Her şey yolundaysa oy ekranını aç
    secilen = next((p for p in PILOTLAR if p['isim'] == pilot_ismi), None)
    return render_template('oy_ver.html', pilot=secilen)

# OY KAYDETME
@app.route('/kaydet', methods=['POST'])
def oy_kaydet():
    # Kayıt anında da kontrol (Çifte güvenlik)
    if YARIS_BASLANGIC is None:
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış başlamadığı için oyunuz geçersiz sayıldı.", durum="hata")
        
    simdi = datetime.now()
    gecen_sure = simdi - YARIS_BASLANGIC
    if gecen_sure.total_seconds() > 3600:
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış bittiği için oyunuz geçersiz sayıldı.", durum="hata")

    secilen_pilot = request.form['pilot']
    gelen_email = request.form.get('email')
    
    if not gelen_email or "@" not in gelen_email:
        return render_template('sonuc.html', mesaj="❌ Hata: Geçersiz mail adresi!", durum="hata")

    with open(OY_DOSYASI, "a", encoding="utf-8") as dosya:
        dosya.write(f"{gelen_email},{secilen_pilot}\n")
        
    return render_template('sonuc.html', mesaj=f"Teşekkürler! {secilen_pilot} için oyunuz kaydedildi.", durum="basarili")

# BAŞLAT BUTONU 
@app.route('/baslat', methods=['POST'])
def yarisi_baslat():
    global YARIS_BASLANGIC
    # Eğer yarış zaten başlamadıysa, şimdi başlat
    if YARIS_BASLANGIC is None:
        YARIS_BASLANGIC = datetime.now()
    return redirect(url_for('ana_sayfa'))

if __name__ == '__main__':
    app.run(debug=True)