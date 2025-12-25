from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

OY_DOSYASI = "votes.txt"
YARIS_BASLANGIC = None 
YARIS_SURESI_SANIYE = 300 

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
    
    # Parantezleri ve içindekileri sil (Örn: "(2016-), 33[not 1]")
    temiz = re.sub(r'\[.*?\]', '', metin) 
    temiz = re.sub(r'\(.*?\)', '', temiz) 
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
    print(" VERİLER ÇEKİLİYOR)")
    print("="*60)
    
    final_liste = []
    
    for pilot in PILOTLAR_DB:
        print(f" İşleniyor: {pilot['isim']}...", end=" ")
        
        web_verisi = wikipedia_kaziyici(pilot['wiki'])
        
        # Sadece Verstappen için düzeltme (Numarası 1 olsun diye)
        if pilot['isim'] == "Max Verstappen":
            if len(web_verisi['no']) > 2 or "33" in web_verisi['no']:
                web_verisi['no'] = "1"
    
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
        bulunan_bilgi = None 
        for p in PILOTLAR:           
            if p['isim'] == isim:   
                bulunan_bilgi = p    
                break
        if bulunan_bilgi:
            resimli_siralama.append({
                "isim": isim,
                "puan": puan,
                "resim": bulunan_bilgi['resim'],
                "takim": bulunan_bilgi['takim']
            })

    return resimli_siralama

# ZAMANLAYICI
def sure_hesapla():
    global YARIS_BASLANGIC
    
    if YARIS_BASLANGIC is None:
        return "Yarış Başlamadı 🔴"
        
    simdi = datetime.now()
    gecen_sure = simdi - YARIS_BASLANGIC
    toplam_sure = timedelta(seconds=YARIS_SURESI_SANIYE) 
    
    kalan = toplam_sure - gecen_sure
    
    if kalan.total_seconds() <= 0:
        return "Yarış Bitti! 🏁"
    
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
            if (aranan in p['isim'].lower() or 
                aranan in p['takim'].lower() or 
                aranan in str(p.get('no', '')).lower() or 
                aranan in p.get('ulke', '').lower()):
                
                gonderilecek.append(p)
    else:
        gonderilecek = PILOTLAR
        
    siralama = siralamayi_hesapla()
    podyum = siralama[:3]
    return render_template('index.html', pilotlar=gonderilecek, siralama=siralama, podyum=podyum, sure=sure_hesapla(), durum=liste_durumu)

@app.route('/oy-ekrani/<pilot_ismi>')
def oy_ekrani(pilot_ismi):
    if YARIS_BASLANGIC is None:
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış henüz başlamadı! Lütfen önce 'YARIŞI BAŞLAT' butonuna basın.", durum="hata")
    
    simdi = datetime.now()
    gecen_sure = simdi - YARIS_BASLANGIC
    if gecen_sure.total_seconds() > YARIS_SURESI_SANIYE: 
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış süresi doldu! Artık oy kullanamazsınız.", durum="hata")

    secilen = None          
    for p in PILOTLAR:      
        if p['isim'] == pilot_ismi: 
            secilen = p    
            break
    return render_template('oy_ver.html', pilot=secilen)

# OY KAYDETME 
@app.route('/kaydet', methods=['POST'])
def oy_kaydet():
    if YARIS_BASLANGIC is None:
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış başlamadığı için oyunuz geçersiz sayıldı.", durum="hata")
        
    simdi = datetime.now()
    gecen_sure = simdi - YARIS_BASLANGIC
    
    if gecen_sure.total_seconds() > YARIS_SURESI_SANIYE:
        return render_template('sonuc.html', mesaj="⚠️ HATA: Yarış bittiği için oyunuz geçersiz sayıldı.", durum="hata")

    secilen_pilot = request.form['pilot']
    gelen_email = request.form.get('email', '').strip()
    
    if not gelen_email or "@" not in gelen_email:
        return render_template('sonuc.html', mesaj="❌ Hata: Geçersiz mail adresi!", durum="hata")

    with open(OY_DOSYASI, "a", encoding="utf-8") as dosya:
        dosya.write(f"{gelen_email},{secilen_pilot}\n")
        
    return render_template('sonuc.html', mesaj=f"Teşekkürler! {secilen_pilot} için oyunuz kaydedildi.", durum="basarili")

@app.route('/baslat', methods=['POST'])
def yarisi_baslat():
    global YARIS_BASLANGIC
    
    if os.path.exists(OY_DOSYASI):
        eski_siralama = siralamayi_hesapla() # Şu anki puan durumunu al
        
        if eski_siralama:
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n" + "="*50)
            print(f"🏁 TAMAMLANAN YARIŞ RAPORU - {tarih}")
            print("="*50)
            for i, p in enumerate(eski_siralama, 1):
                print(f"{i}. {p['isim']} \t-> {p['puan']} Oy")
            print("="*50 + "\n")

            sampiyon = eski_siralama[0]['isim'] 
            
            fan_sayaci = {} 

            with open(OY_DOSYASI, "r", encoding="utf-8") as dosya:
                for satir in dosya:
                    parcalar = satir.strip().split(",")
                    if len(parcalar) == 2:
                        mail = parcalar[0]
                        oy_verilen = parcalar[1]
                        
                        # Eğer bu oy şampiyona verildiyse sayaca ekle
                        if oy_verilen == sampiyon:
                            if mail in fan_sayaci:
                                fan_sayaci[mail] += 1 # Varsa 1 artır
                            else:
                                fan_sayaci[mail] = 1  # Yoksa 1 ile başlat

            print(f"\n🏆 ŞAMPİYON: {sampiyon}")
            
            if fan_sayaci:
                
                en_sadik_fan = max(fan_sayaci, key=fan_sayaci.get)
                atilan_oy_sayisi = fan_sayaci[en_sadik_fan]
                
                print(f"🎁 ÖDÜL KAZANAN TARAFTAR (En çok oy veren):")
                print("-" * 50)
                print(f"   👤 Mail Adresi : {en_sadik_fan}")
                print(f"   🗳️  Attığı Oy   : {atilan_oy_sayisi} Adet")
                print("-" * 50)
            else:
                print("   (Şampiyona henüz kimse oy vermemiş)")  

            print("✅ Rapor terminale yazıldı. Dosya temizleniyor...\n")

    if os.path.exists(OY_DOSYASI):
        open(OY_DOSYASI, 'w').close()
        
    YARIS_BASLANGIC = datetime.now()
    return redirect(url_for('ana_sayfa'))

@app.route('/api/guncel-veriler')
def guncel_veriler_api():
    siralama = siralamayi_hesapla()
    podyum = siralama[:3]
    sure = sure_hesapla()
    return jsonify(siralama=siralama, podyum=podyum, sure=sure)

if __name__ == '__main__':
    app.run(debug=False)