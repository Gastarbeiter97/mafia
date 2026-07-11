import time                      #streamlit run mafia_app.py
import random
import json
import os
import streamlit as st
from pathlib import Path
from google import genai
from groq import Groq
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
#  API SETUP
# ============================================================
load_dotenv(Path(__file__).parent / ".env")

def acar(ad):
    try:
        if ad in st.secrets:
            return st.secrets[ad]
    except Exception:
        pass
    return os.getenv(ad)

gemini_client = genai.Client(api_key=acar("GEMINI_API_KEY"))
groq_client = Groq(api_key=acar("GROQ_API_KEY"))

cerebras_client = None
if acar("CEREBRAS_API_KEY"):
    cerebras_client = OpenAI(
        api_key=acar("CEREBRAS_API_KEY"),
        base_url="https://api.cerebras.ai/v1"
    )

nvidia_client = None
if acar("NVIDIA_API_KEY"):
    nvidia_client = OpenAI(
        api_key=acar("NVIDIA_API_KEY"),
        base_url="https://integrate.api.nvidia.com/v1"
    )


def groq_sorgu(prompt):
    try:
        r = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Groq: {e}")
        return None


def cerebras_sorgu(prompt):
    if cerebras_client is None:
        return None
    try:
        r = cerebras_client.chat.completions.create(
            model="gemma-4-31b",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Cerebras: {e}")
        return None


def nvidia_sorgu(prompt):
    if nvidia_client is None:
        print("❌ NVIDIA: client yoxdur (açar yüklənməyib)")
        return None
    try:
        r = nvidia_client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ NVIDIA: {e}")
        return None


def gemini_sorgu(prompt):
    try:
        r = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return r.text.strip()
    except Exception as e:
        print(f"❌ Gemini: {e}")
        return None


saglayicilar = [groq_sorgu, nvidia_sorgu, gemini_sorgu, cerebras_sorgu]
_esas = {"index": 0}


def llm_sorgu(prompt):
    say = len(saglayicilar)
    for _ in range(2):
        for i in range(say):
            index = (_esas["index"] + i) % say
            cavab = saglayicilar[index](prompt)
            if cavab is not None:
                if index != _esas["index"]:
                    print(f"🔄 Keçid: {saglayicilar[_esas['index']].__name__} → {saglayicilar[index].__name__}")
                    _esas["index"] = index
                return cavab
        time.sleep(5)
    return None


# ============================================================
#  GAME LOGIC (pure helpers - no print/input)
# ============================================================
def ad_generasiya_et():
    prompt = 'Mənə 5 ədəd fərqli Azərbaycan adı ver. YALNIZ JSON array qaytar, başqa heç nə: ["ad1", "ad2", "ad3", "ad4", "ad5"]'
    metn = llm_sorgu(prompt)
    if metn:
        metn = metn.replace("```json", "").replace("```", "").strip()
        if "[" in metn and "]" in metn:
            metn = metn[metn.index("["):metn.rindex("]") + 1]
        try:
            return json.loads(metn)
        except Exception:
            pass
    return ["Orxan", "Rəşad", "Eyvaz", "Ağa", "Nigar"]


def sag_qalanlar(oyuncular):
    return [o for o in oyuncular if o["sag"]]


def rol_tap(oyuncular, ad):
    for o in oyuncular:
        if o["ad"] == ad:
            return o["rol"]
    return "naməlum"


def oldur(oyuncular, ad):
    for o in oyuncular:
        if o["ad"] == ad:
            o["sag"] = False


def qalib_yoxla(oyuncular):
    saglar = sag_qalanlar(oyuncular)
    mafialar = [o for o in saglar if o["rol"] == "mafia"]
    vetendaslar = [o for o in saglar if o["rol"] != "mafia"]
    if len(mafialar) == 0:
        return "seher"
    elif len(mafialar) >= len(vetendaslar):
        return "mafia"
    return None


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


def ai_hekim_xilas(oyuncu, saglar):
    adlar = [o["ad"] for o in saglar]
    prompt = f"""Sən "{oyuncu['ad']}" adlı HƏKİMSƏN.
Gecədir. Mafiadan bir nəfəri xilas edə bilərsən.
Xilas edə biləcəyin oyunçular: {', '.join(adlar)}
Mafianın öldürəcəyi ən ehtimallı oyunçunu seç.
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
Gecədir. Bir nəfəri yoxlaya bilərsən.
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


def oyun_analizi(oyuncular):
    melumat = []
    for o in oyuncular:
        veziyyet = "sağ" if o["sag"] else "öldü"
        melumat.append(f"{o['ad']} - {o['rol']} ({veziyyet})")
    prompt = f"""Bir Mafia oyunu bitdi. Oyunçular və rolları:
{chr(10).join(melumat)}

Bir oyun şərhçisi kimi qısa, əyləncəli analiz yaz (3-4 cümlə):
- Kim yaxşı oynadı?
- Mafia rolunu yaxşı gizlədə bildimi?
- Maraqlı bir məqam qeyd et.
Azərbaycan dilində yaz."""
    return llm_sorgu(prompt)


# ============================================================
#  STREAMLIT UI
# ============================================================
st.set_page_config(page_title="Mafia AI", page_icon="🕵️", layout="centered")

st.markdown("""
<style>
    .stApp { background: #0f1117; }
    h1, h2, h3, p, span, label, div { color: #e8e6e3 !important; }
    .rol-karti {
        background: #1a1d29; border: 1px solid #2d3142;
        border-radius: 12px; padding: 20px; margin: 8px 0;
    }
    .olu { opacity: 0.4; text-decoration: line-through; }
    .danisiq {
        background: #1a1d29; border-left: 3px solid #d4a373;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0;
    }
    .stButton button {
        background: #d4a373; color: #0f1117 !important;
        border: none; border-radius: 8px; font-weight: 600;
    }
    .baslıq { font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; }
</style>
""", unsafe_allow_html=True)

S = st.session_state

# ---- init ----
if "faza" not in S:
    S.faza = "start"


def yeni_oyun():
    ai_adlar = ad_generasiya_et()
    adlar = ["Sən"] + ai_adlar
    rollar = ["mafia", "mafia", "hekim", "detektiv", "vetendas", "vetendas"]
    random.shuffle(rollar)
    S.oyuncular = [{"ad": adlar[i], "rol": rollar[i], "sag": True} for i in range(len(adlar))]
    S.raund = 1
    S.faza = "gece"
    S.log = []
    S.muzakire = []
    S.mesaj = ""


def senin_rol():
    for o in S.oyuncular:
        if o["ad"] == "Sən":
            return o["rol"]
    return "?"


# ---- START SCREEN ----
if S.faza == "start":
    st.markdown('<div class="baslıq">🕵️ MAFIA AI</div>', unsafe_allow_html=True)
    st.write("5 süni intellekt oyunçusu. Gizli rollar. Yalan, şübhə, səsvermə.")
    st.write("Sən şəhərin bir sakinisən — həqiqəti tapa biləcəksənmi?")
    if st.button("🎬 Yeni oyun başlat", use_container_width=True):
        with st.spinner("Oyunçular yaradılır..."):
            yeni_oyun()
        st.rerun()

# ---- ROSTER (shared) ----
def goster_roster():
    st.markdown(f"### 📅 Raund {S.raund}")
    cols = st.columns(3)
    for idx, o in enumerate(S.oyuncular):
        with cols[idx % 3]:
            klass = "rol-karti" + ("" if o["sag"] else " olu")
            etiket = o["ad"]
            if o["ad"] == "Sən":
                etiket += f" ({senin_rol()})"
            st.markdown(f'<div class="{klass}">{"🟢" if o["sag"] else "💀"} {etiket}</div>',
                        unsafe_allow_html=True)


# ---- NIGHT ----
if S.faza == "gece":
    goster_roster()
    st.markdown("## 🌙 Gecə")
    st.write("Şəhər yatır. Mafia hədəf seçir, həkim xilas edir, detektiv araşdırır.")
    if st.button("🌙 Gecəni keçir", use_container_width=True):
        oy = S.oyuncular
        saglar = sag_qalanlar(oy)
        mesajlar = []

        mafialar = [o for o in saglar if o["rol"] == "mafia"]
        hedefler = [o["ad"] for o in saglar if o["rol"] != "mafia"]
        mafia_hedef = None
        if mafialar and hedefler:
            mafia_hedef = ai_mafia_hedef(mafialar[0], saglar)

        hekimler = [o for o in saglar if o["rol"] == "hekim"]
        xilas = ai_hekim_xilas(hekimler[0], saglar) if hekimler else None

        if mafia_hedef and mafia_hedef == xilas:
            mesajlar.append("🏥 Mafia hücum etdi, amma həkim xilas etdi!")
        elif mafia_hedef:
            oldur(oy, mafia_hedef)
            r = rol_tap(oy, mafia_hedef)
            felil = "öldürüldün" if mafia_hedef == "Sən" else "öldürüldü"
            mesajlar.append(f"💀 {mafia_hedef} gecə {felil}. (Rolu: {r})")

        detektivler = [o for o in saglar if o["rol"] == "detektiv"]
        if detektivler and detektivler[0]["ad"] == "Sən":
            supheli = ai_detektiv_yoxla(detektivler[0], saglar)
            sr = rol_tap(oy, supheli)
            netice = "MAFİADIR ✅" if sr == "mafia" else "mafia deyil ❌"
            mesajlar.append(f"🔍 (Yalnız sən görürsən) {supheli}: {netice}")

        S.gece_mesaj = mesajlar
        netice = qalib_yoxla(oy)
        if netice:
            S.qalib = netice
            S.faza = "son"
        else:
            S.faza = "gunduz"
        st.rerun()

# ---- DAY ----
if S.faza == "gunduz":
    goster_roster()
    for m in S.get("gece_mesaj", []):
        st.info(m)

    st.markdown("## ☀️ Gündüz — Müzakirə")
    oy = S.oyuncular
    saglar = sag_qalanlar(oy)

    if "gunduz_hazir" not in S:
        S.muzakire = []
        with st.spinner("Oyunçular danışır..."):
            for o in saglar:
                if o["ad"] == "Sən":
                    continue
                d = ai_danis(o, S.muzakire, saglar)
                S.muzakire.append(f"{o['ad']}: {d}")
        # AI votes
        S.seslr = {}
        with st.spinner("Səsvermə..."):
            for o in saglar:
                if o["ad"] == "Sən":
                    continue
                v = ai_ses_ver(o, S.muzakire, saglar)
                S.seslr[v] = S.seslr.get(v, 0) + 1
        S.gunduz_hazir = True

    for setir in S.muzakire:
        st.markdown(f'<div class="danisiq">💬 {setir}</div>', unsafe_allow_html=True)

    st.markdown("### 🗳️ İndiyə qədər səslər")
    for ad, say in sorted(S.seslr.items(), key=lambda x: x[1], reverse=True):
        st.write(f"**{ad}**: {say} səs")

    st.markdown("### Sənin səsin")
    sag_adlar = [o["ad"] for o in saglar if o["ad"] != "Sən"]
    secim = st.radio("Kimi çıxarmaq istəyirsən?", sag_adlar, key="vote_radio")
    if st.button("✅ Səs ver", use_container_width=True):
        seslr = dict(S.seslr)
        seslr[secim] = seslr.get(secim, 0) + 1
        cixarilan = max(seslr, key=seslr.get)
        oldur(oy, cixarilan)
        r = rol_tap(oy, cixarilan)
        felil = "çıxarıldın" if cixarilan == "Sən" else "çıxarıldı"
        S.gunduz_netice = f"❌ {cixarilan} ən çox səs aldı və {felil}. (Rolu: {r})"
        S.final_seslr = seslr
        del S.gunduz_hazir
        netice = qalib_yoxla(oy)
        if netice:
            S.qalib = netice
            S.faza = "son"
        else:
            S.raund += 1
            S.faza = "gece_ara"
        st.rerun()

# ---- DAY RESULT BRIDGE ----
if S.faza == "gece_ara":
    goster_roster()
    st.success(S.gunduz_netice)
    st.markdown("### 📊 Yekun səslər")
    for ad, say in sorted(S.final_seslr.items(), key=lambda x: x[1], reverse=True):
        st.write(f"**{ad}**: {say} səs")
    if st.button("🌙 Növbəti gecəyə keç", use_container_width=True):
        S.faza = "gece"
        st.rerun()

# ---- END ----
if S.faza == "son":
    goster_roster()
    for m in S.get("gece_mesaj", []):
        st.info(m)
    if S.get("gunduz_netice"):
        st.success(S.gunduz_netice)

    if S.qalib == "seher":
        st.markdown("# 🎉 ŞƏHƏR QAZANDI!")
    else:
        st.markdown("# 🔪 MAFİA QAZANDI!")

    st.markdown("## 🎬 Oyun Analizi")
    if "analiz" not in S:
        with st.spinner("Analiz hazırlanır..."):
            S.analiz = oyun_analizi(S.oyuncular)
    st.write(S.analiz if S.analiz else "Analiz alınmadı.")

    st.markdown("### Rollar açıqlanır")
    for o in S.oyuncular:
        st.write(f"**{o['ad']}** — {o['rol']} {'(sağ)' if o['sag'] else '(öldü)'}")

    if st.button("🔄 Yenidən oyna", use_container_width=True):
        for k in list(S.keys()):
            del S[k]
        st.rerun()