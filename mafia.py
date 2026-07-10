import time
import random
import json
import os
from pathlib import Path
from google import genai
from groq import Groq
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env")
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
cerebras_client = OpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1"
)
nvidia_client = None
if os.getenv("NVIDIA_API_KEY"):
    nvidia_client = OpenAI(
        api_key=os.getenv("NVIDIA_API_KEY"),
        base_url="https://integrate.api.nvidia.com/v1"
    )

def cerebras_sorgu(prompt):
    try:
        response = cerebras_client.chat.completions.create(
            model="llama-3.3-70b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def nvidia_sorgu(prompt):
    try:
        response = nvidia_client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None

def ai_hekim_xilas(oyuncu, saglar):
    adlar = [o["ad"] for o in saglar]
    prompt = f"""Sən "{oyuncu['ad']}" adlı HƏKİMSƏN.
Gecədir. Mafiadan bir nəfəri xilas edə bilərsən.
Xilas edə biləcəyin oyunçular: {', '.join(adlar)}
Mafianın öldürəcəyi ən ehtimallı oyunçunu seç (özünü də xilas edə bilərsən).
YALNIZ bir ad yaz, başqa heç nə."""

    cavab = llm_sorgu(prompt)
    if cavab is None:
        return random.choice(adlar)
    cavab = cavab.strip()
    for ad in adlar:
        if ad in cavab:
            return ad
    return random.choice(adlar)

def ai_detektiv_yoxla(oyuncu, saglar):

    adlar = [o["ad"] for o in saglar if o["ad"] != oyuncu["ad"]]
    prompt = f"""Sən "{oyuncu['ad']}" adlı DETEKTİVSƏN.
Gecədir. Bir nəfəri yoxlaya bilərsən - onun mafia olub-olmadığını öyrənəcəksən.
Yoxlaya biləcəyin oyunçular: {', '.join(adlar)}
Ən şübhəli oyunçunu seç.
YALNIZ bir ad yaz, başqa heç nə."""

    cavab = llm_sorgu(prompt)
    if cavab is None:
        return random.choice(adlar)
    cavab = cavab.strip()
    for ad in adlar:
        if ad in cavab:
            return ad
    return random.choice(adlar)

def groq_sorgu(prompt):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def cerebras_sorgu(prompt):
    try:
        response = cerebras_client.chat.completions.create(
            model="llama-3.3-70b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def nvidia_sorgu(prompt):
    try:
        response = nvidia_client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def gemini_sorgu(prompt):
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return None

saglayicilar = [groq_sorgu, cerebras_sorgu, nvidia_sorgu, gemini_sorgu]
esas_index = 0


def llm_sorgu(prompt):
    global esas_index
    say = len(saglayicilar)
    for cehd in range(2):
        for i in range(say):
            index = (esas_index + i) % say
            cavab = saglayicilar[index](prompt)
            if cavab is not None:
                esas_index = index
                return cavab
        print("⚠️ Bütün provayderlər məşğuldur, 5 saniyə gözləyirəm...")
        time.sleep(5)
    return None

def ad_generasiya_et():
    prompt = 'Mənə 5 ədəd fərqli Azərbaycan adı ver. YALNIZ JSON array qaytar, başqa heç nə: ["ad1", "ad2", "ad3", "ad4", "ad5"]'
    metn = llm_sorgu(prompt)
    if metn:
        metn = metn.replace("```json", "").replace("```", "").strip()
        return json.loads(metn)
    return ["Orxan", "Rəşad", "Eyvaz", "Ağa", "Nigar"]

ai_adlar = ad_generasiya_et()
print("AI adları:", ai_adlar)

adlar = ["Sən"] + ai_adlar

rollar = ["mafia", "mafia", "hekim", "detektiv", "vetendas", "vetendas"]
random.shuffle(rollar)

oyuncular = []
for i in range(len(adlar)):
    oyuncu = {"ad": adlar[i], "rol": rollar[i], "sag": True}
    oyuncular.append(oyuncu)

for o in oyuncular:
    if o["ad"] == "Sən":
        print(f"Sənin rolun: {o['rol']}")

def rol_tap(oyuncular, ad):
    for o in oyuncular:
        if o["ad"] == ad:
            return o["rol"]
    return "naməlum"

def ai_ses_ver(oyuncu, muzakire_tarixcesi, saglar):
    sag_adlar = [o["ad"] for o in saglar if o["ad"] != oyuncu["ad"]]
    tarixce = "\n".join(muzakire_tarixcesi) if muzakire_tarixcesi else "Müzakirə olmayıb."

    prompt = f"""Sən "{oyuncu['ad']}" adlı Mafia oyunçususan. Rolun: {oyuncu['rol']}.
Müzakirə:
{tarixce}

Səs verə biləcəyin oyunçular: {', '.join(sag_adlar)}
Kimi oyundan çıxarmaq istəyirsən? YALNIZ bir ad yaz, başqa heç nə."""

    cavab = llm_sorgu(prompt)
    if cavab is None:
        return random.choice(sag_adlar)

    cavab = cavab.strip()
    for ad in sag_adlar:
        if ad in cavab:
            return ad
    return random.choice(sag_adlar)

def sag_qalanlar(oyuncular):
    return [o for o in oyuncular if o["sag"]]

def ai_mafia_hedef(oyuncu, saglar):
    hedefler = [o["ad"] for o in saglar if o["rol"] != "mafia"]
    prompt = f"""Sən "{oyuncu['ad']}" adlı MAFİASAN.
Gecədir. Şəhərdən bir nəfəri gizlicə öldürməlisən.
Öldürə biləcəyin oyunçular: {', '.join(hedefler)}
Ən təhlükəli (sənə şübhələnə biləcək) oyunçunu seç.
YALNIZ bir ad yaz, başqa heç nə."""

    cavab = llm_sorgu(prompt)
    if cavab is None:
        return random.choice(hedefler)
    cavab = cavab.strip()
    for ad in hedefler:
        if ad in cavab:
            return ad
    return random.choice(hedefler)

def qalib_yoxla(oyuncular):
    saglar = sag_qalanlar(oyuncular)
    mafialar = [o for o in saglar if o["rol"] == "mafia"]
    vetendaslar = [o for o in saglar if o["rol"] != "mafia"]

    if len(mafialar) == 0:
        return "seher"
    elif len(mafialar) >= len(vetendaslar):
        return "mafia"
    else:
        return None


def oldur(oyuncular, ad):
    for o in oyuncular:
        if o["ad"] == ad:
            o["sag"] = False

def ai_danis(oyuncu, muzakire_tarixcesi, saglar):
    sag_adlar = [o["ad"] for o in saglar if o["ad"] != oyuncu["ad"]]

    if oyuncu["rol"] == "mafia":
        rol_izahi = "Sən MAFİASAN. Rolunu MÜTLƏQ gizlə. Özünü günahsız vətəndaş kimi göstər, başqasını ittiham et."
    elif oyuncu["rol"] == "hekim":
        rol_izahi = "Sən HƏKİMSƏN (yaxşı komanda). Mafiaları tapmağa çalış, amma rolunu açıq demə."
    elif oyuncu["rol"] == "detektiv":
        rol_izahi = "Sən DETEKTİVSƏN (yaxşı komanda). Şübhəli davranışları analiz et."
    else:
        rol_izahi = "Sən sadə VƏTƏNDAŞSAN (yaxşı komanda). Mafiaları tapmağa çalış."

    tarixce_metni = "\n".join(muzakire_tarixcesi) if muzakire_tarixcesi else "Hələ heç kim danışmayıb."

    prompt = f"""Sən "{oyuncu['ad']}" adlı Mafia oyunçususan.
{rol_izahi}

Sağ qalan digər oyunçular: {', '.join(sag_adlar)}

İndiyə qədər müzakirə:
{tarixce_metni}

İndi sənin danışıq növbəndir. 1-2 cümlə danış: kimdən şübhələnirsən və niyə?
YALNIZ danışığını yaz, başqa heç nə."""

    cavab = llm_sorgu(prompt)
    if cavab is None:
        return f"{oyuncu['ad']} bu raundda susdu."
    return cavab

def gunduz_fazasi(oyuncular):
    print("\n☀️ GÜNDÜZ - Müzakirə başlayır...\n")
    saglar = sag_qalanlar(oyuncular)
    print(f"👥 Sağ qalanlar ({len(saglar)}): {', '.join(o['ad'] for o in saglar)}\n")
    muzakire_tarixcesi = []

    for o in saglar:
        if o["ad"] == "Sən":
            continue
        danisiq = ai_danis(o, muzakire_tarixcesi, saglar)
        setir = f"{o['ad']}: {danisiq}"
        print(f"💬 {setir}")
        muzakire_tarixcesi.append(setir)
        time.sleep(2)

    seslr = {}

    for o in saglar:
        if o["ad"] == "Sən":
            continue
        ses = ai_ses_ver(o, muzakire_tarixcesi, saglar)
        seslr[ses] = seslr.get(ses, 0) + 1
        print(f"🗳️ {o['ad']} → {ses}")

    print("\n📊 İndiyə qədər səslər:")
    for ad, say in sorted(seslr.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ad}: {say} səs")

    sag_adlar = [o["ad"] for o in saglar if o["ad"] != "Sən"]
    print("\nSənin səsin - kimi çıxarmaq istəyirsən?")
    for ad in sag_adlar:
        print(f"  - {ad}")
    while True:
        secim = input("Ad yaz: ").strip()
        if secim in sag_adlar:
            break
        else:
            print("⚠️ Belə bir sağ oyunçu yoxdur, yenidən yaz.")
    seslr[secim] = seslr.get(secim, 0) + 1

    cixarilan = max(seslr, key=seslr.get)
    print("\n📊 SƏSLƏR:")
    for ad, say in sorted(seslr.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ad}: {say} səs")
    oldur(oyuncular, cixarilan)
    rol = rol_tap(oyuncular, cixarilan)
    felil2 = "çıxarıldın" if cixarilan == "Sən" else "çıxarıldı"
    print(f"❌ {cixarilan} ən çox səs aldı və {felil2}. (Rolu: {rol})")

def gece_fazasi(oyuncular):
    print("\n🌙 GECƏ - Hamı yatır...")
    saglar = sag_qalanlar(oyuncular)

    mafialar_hamisi = [o["ad"] for o in saglar if o["rol"] == "mafia"]
    sen_mafiasan = any(o["ad"] == "Sən" and o["rol"] == "mafia" for o in saglar)
    if sen_mafiasan and len(mafialar_hamisi) > 1:
        yoldaslar = [ad for ad in mafialar_hamisi if ad != "Sən"]
        print(f"🤝 (Gizli) Sənin mafia yoldaşların: {', '.join(yoldaslar)}")

    mafialar = [o for o in saglar if o["rol"] == "mafia"]
    hedefler = [o["ad"] for o in saglar if o["rol"] != "mafia"]

    mafia_hedef = None
    if mafialar and hedefler:
        if sen_mafiasan:
            print("\n🔪 (Mafia) Gecə kimi öldürmək istəyirsən?")
            for ad in hedefler:
                print(f"  - {ad}")
            while True:
                secim = input("Hədəf: ").strip()
                if secim in hedefler:
                    mafia_hedef = secim
                    break
                else:
                    print("⚠️ Belə hədəf yoxdur, yenidən yaz.")
        else:
            aktiv_mafia = mafialar[0]
            mafia_hedef = ai_mafia_hedef(aktiv_mafia, saglar)

    hekimler = [o for o in saglar if o["rol"] == "hekim"]
    xilas = None
    if hekimler:
        sen_hekimsen = any(o["ad"] == "Sən" and o["rol"] == "hekim" for o in saglar)
        if sen_hekimsen:
            print("\n🩺 (Həkim) Kimi xilas etmək istəyirsən?")
            adlar = [o["ad"] for o in saglar]
            for ad in adlar:
                gorunen = "özüm" if ad == "Sən" else ad
                print(f"  - {gorunen}")
            while True:
                secim = input("Xilas: ").strip()
                if secim == "özüm":
                    secim = "Sən"
                if secim in adlar:
                    xilas = secim
                    break
                else:
                    print("⚠️ Belə oyunçu yoxdur, yenidən yaz.")
        else:
            xilas = ai_hekim_xilas(hekimler[0], saglar)

    if mafia_hedef and mafia_hedef == xilas:
        print("🏥 Mafia hücum etdi, amma həkim onu xilas etdi!")
    elif mafia_hedef:
        oldur(oyuncular, mafia_hedef)
        rol = rol_tap(oyuncular, mafia_hedef)
        felil = "öldürüldün" if mafia_hedef == "Sən" else "öldürüldü"
        print(f"💀 {mafia_hedef} gecə {felil}. (Rolu: {rol})")

    detektivler = [o for o in saglar if o["rol"] == "detektiv"]
    if detektivler:
        sen_detektivsen = any(o["ad"] == "Sən" and o["rol"] == "detektiv" for o in saglar)
        if sen_detektivsen:
            print("\n🔍 (Detektiv) Kimi yoxlamaq istəyirsən?")
            adlar = [o["ad"] for o in saglar if o["ad"] != "Sən"]
            for ad in adlar:
                print(f"  - {ad}")
            while True:
                supheli = input("Yoxla: ").strip()
                if supheli in adlar:
                    break
                else:
                    print("⚠️ Belə oyunçu yoxdur, yenidən yaz.")
        else:
            supheli = ai_detektiv_yoxla(detektivler[0], saglar)

        supheli_rol = rol_tap(oyuncular, supheli)
        netice = "MAFİADIR ✅" if supheli_rol == "mafia" else "mafia deyil ❌"

        if sen_detektivsen:
            print(f"🔍 (Detektiv məlumatı) {supheli}: {netice}")

def oyun_analizi(oyuncular):
    melumat = []
    for o in oyuncular:
        veziyyet = "sağ" if o["sag"] else "öldü"
        melumat.append(f"{o['ad']} - {o['rol']} ({veziyyet})")

    melumat_metni = "\n".join(melumat)

    prompt = f"""Bir Mafia oyunu bitdi. Oyunçular və rolları:
{melumat_metni}

Bir oyun şərhçisi kimi qısa, əyləncəli analiz yaz (3-4 cümlə):
- Kim yaxşı oynadı?
- Mafia rolunu yaxşı gizlədə bildimi?
- Maraqlı bir məqam qeyd et.
Azərbaycan dilində yaz."""

    return llm_sorgu(prompt)

print("\n🎮 OYUN BAŞLADI!\n")

raund = 1

while True:
    print(f"\n{'=' * 30}")
    print(f"📅 RAUND {raund}")
    print(f"{'=' * 30}")
    gece_fazasi(oyuncular)
    netice = qalib_yoxla(oyuncular)
    if netice == "seher":
        print("\n🎉 ŞƏHƏR QAZANDI!")
        break
    elif netice == "mafia":
        print("\n🔪 MAFİA QAZANDI!")
        break

    gunduz_fazasi(oyuncular)
    netice = qalib_yoxla(oyuncular)
    if netice == "seher":
        print("\n🎉 ŞƏHƏR QAZANDI!")
        break
    elif netice == "mafia":
        print("\n🔪 MAFİA QAZANDI!")
        break

    raund += 1

print("\n" + "="*30)
print("🎬 OYUN ANALİZİ")
print("="*30)
analiz = oyun_analizi(oyuncular)
print(analiz if analiz else "Analiz alınmadı.")