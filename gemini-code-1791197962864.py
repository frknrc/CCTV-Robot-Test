import streamlit as st
import math
import pandas as pd
import requests
from datetime import datetime

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Zayıf Akım Sistem Planlama Sihirbazı",
    page_icon="🏢",
    layout="wide"
)

# --- ÜST MENÜ VE GİTHUB SİMGELERİNİ MÜŞTERİDEN GİZLEME (CSS) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- ÇEVİRİ SÖZLÜĞÜ (TR / EN / KK) ---
TEXTS = {
    "TR": {
        "page_title": "Zayıf Akım Sistem Planlama Sihirbazı",
        "caption": "Lütfen projenize ait verileri girerek donanım ve altyapı ihtiyaç raporunu oluşturun.",
        "project_name_label": "📌 Havalimanı / Proje Adı",
        "project_name_default": "Örnek Havalimanı Terminal Projesi",
        "select_systems_title": "🎯 Planlanacak Zayıf Akım Sistemlerini Seçiniz",
        "select_systems_label": "İhtiyaç duyulan sistemleri işaretleyiniz:",
        "warning_no_system": "⚠ Lütfen devam etmek için en az bir zayıf akım sistemi seçiniz.",
        "submit_btn": "🚀 Tüm Seçili Sistemlerin İhtiyaç Raporunu Oluştur",
        "report_success": "✅ **{project}** İçin Seçilen Sistem Planlama Raporu Başarıyla Hesaplandı!",
        "download_section": "📥 Rapor Çıktısı Alın",
        "cctv_title": "🎥 CCTV Kamera Güvenlik Sistemi",
        "cctv_scope": "Havalimanı Kapsamı:",
        "cctv_opt1": "Uluslararası Transit Hub (Yüksek Güvenlik / Yoğun Yolcu)",
        "cctv_opt2": "Bölgesel / Orta Ölçekli Havalimanı",
        "cctv_sqm": "Terminal Kapalı Alanı (m²)",
        "cctv_checkpoints": "Pasaport & Güvenlik Kontrol Noktası",
        "cctv_fence": "Çevre Çit Uzunluğu (Metre)",
        "cctv_anpr_chk": "Plaka Tanıma Sistemi (ANPR) İstiyorum",
        "cctv_lanes": "ANPR Giriş/Çıkış Şerit Sayısı",
        "cctv_speed": "Geçiş Hız Tipi",
        "cctv_speed_low": "Düşük Hız (Nizamiye / Otopark Bariyer)",
        "cctv_speed_high": "Yüksek Hız (Ana Yol / VIP Giriş)",
        "cctv_cr": "Ana Kontrol Odası Sayısı",
        "cctv_op": "Vardiyadaki Aktif Operatör Masa Sayısı",
        "cctv_rem": "Uzak İzleme Noktası Sayısı",
        "cctv_days": "Kayıt Saklama Süresi (Gün)",
        "cctv_res": "Kamera Kalite Standardı",
        "acs_title": "🚪 Kartlı Geçiş ve Turnike Sistemi (ACS)",
        "acs_doors_sec": "Kapı Tip ve Sayıları",
        "acs_s_doors": "Tek Kanat Kontrollü Kapı Sayısı",
        "acs_d_doors": "Çift Kanat Kontrollü Kapı Sayısı",
        "acs_turnstiles": "Geçiş Turnikesi Sayısı (Personel / Yolcu)",
        "acs_users_sec": "Kullanıcı ve Biyometrik Seçenekleri",
        "acs_users": "Sisteme Tanımlanacak Toplam Kartlı Kullanıcı Sayısı",
        "acs_face": "Yüz Tanıma Terminali Adedi",
        "acs_finger": "Parmak İzi Okuyucu Adedi",
        "fas_title": "🚨 Yangın Algılama ve İhbar Sistemi (FAS)",
        "fas_sqm": "Yangın Algılama Yapılacak Kapalı Alan (m²)",
        "fas_rf": "Asma Tavan ve Yükseltilmiş Taban İçi Dedektörler Dahil Edilsin",
        "fas_beam": "Yüksek Tavan / Hangar İçin Işın (Beam) Dedektör Çifti Sayısı",
        "pava_title": "📢 Acil Anons ve Seslendirme Sistemi (PA/VA)",
        "pava_sqm": "Anons Yapılacak Toplam Kapalı Alan (m²)",
        "pava_zones": "Bağımsız Anons Bölgesi (Zone) Sayısı",
        "pava_env": "Baskın Ortam Tipi & Gürültü Seviyesi",
        "pava_env_std": "Standart Terminal Alanı (70-75 dB)",
        "pava_env_noisy": "Gürültülü Otopark / Teknik Alan (80-85 dB)",
        "pava_env_quiet": "Sessiz Ofis / Yönetim Alanı (60 dB)",
        "system_names": {
            "CCTV": "CCTV (Kamera Güvenlik)",
            "ACS": "ACS (Kartlı Geçiş & Turnike)",
            "FAS": "FAS (Yangın Algılama)",
            "PA/VA": "PA/VA (Anons & Seslendirme)"
        }
    },
    "EN": {
        "page_title": "ELV Systems Planning Wizard",
        "caption": "Please enter your project details to generate the hardware and infrastructure requirements report.",
        "project_name_label": "📌 Airport / Project Name",
        "project_name_default": "Sample Airport Terminal Project",
        "select_systems_title": "🎯 Select ELV Systems to Plan",
        "select_systems_label": "Select the required systems:",
        "warning_no_system": "⚠ Please select at least one ELV system to proceed.",
        "submit_btn": "🚀 Generate Requirements Report for Selected Systems",
        "report_success": "✅ Planning report successfully generated for **{project}**!",
        "download_section": "📥 Download Report",
        "cctv_title": "🎥 CCTV Surveillance System",
        "cctv_scope": "Airport Scope:",
        "cctv_opt1": "International Transit Hub (High Security / High Traffic)",
        "cctv_opt2": "Regional / Medium-Sized Airport",
        "cctv_sqm": "Terminal Indoor Area (m²)",
        "cctv_checkpoints": "Passport & Security Checkpoints",
        "cctv_fence": "Perimeter Fence Length (Meters)",
        "cctv_anpr_chk": "Include Automatic Number Plate Recognition (ANPR)",
        "cctv_lanes": "ANPR Entry/Exit Lanes",
        "cctv_speed": "Vehicle Speed Type",
        "cctv_speed_low": "Low Speed (Gatehouse / Parking Barrier)",
        "cctv_speed_high": "High Speed (Main Access / VIP Entry)",
        "cctv_cr": "Main Control Rooms Count",
        "cctv_op": "Active Operator Workstations per Shift",
        "cctv_rem": "Remote Viewing Stations Count",
        "cctv_days": "Storage Retention (Days)",
        "cctv_res": "Camera Quality Standard",
        "acs_title": "🚪 Access Control & Turnstile System (ACS)",
        "acs_doors_sec": "Door Types and Quantities",
        "acs_s_doors": "Single-Leaf Controlled Doors",
        "acs_d_doors": "Double-Leaf Controlled Doors",
        "acs_turnstiles": "Turnstiles Count (Staff / Passenger)",
        "acs_users_sec": "User and Biometric Options",
        "acs_users": "Total Cardholder Users to Register",
        "acs_face": "Face Recognition Terminals Count",
        "acs_finger": "Fingerprint Readers Count",
        "fas_title": "🚨 Fire Alarm System (FAS)",
        "fas_sqm": "Covered Fire Detection Area (m²)",
        "fas_rf": "Include False Ceiling and Raised Floor Detectors",
        "fas_beam": "Beam Detector Pairs (High Ceiling / Hangar)",
        "pava_title": "📢 Public Address & Voice Alarm System (PA/VA)",
        "pava_sqm": "Public Address Covered Area (m²)",
        "pava_zones": "Independent Announcement Zones",
        "pava_env": "Dominant Environment & Noise Level",
        "pava_env_std": "Standard Terminal Area (70-75 dB)",
        "pava_env_noisy": "Noisy Parking / Technical Area (80-85 dB)",
        "pava_env_quiet": "Quiet Office / Management Area (60 dB)",
        "system_names": {
            "CCTV": "CCTV Surveillance",
            "ACS": "Access Control System (ACS)",
            "FAS": "Fire Alarm System (FAS)",
            "PA/VA": "PA/VA System"
        }
    },
    "KK": {
        "page_title": "Әлсіз тоқ жүйелерін жоспарлау шебері",
        "caption": "Жабдық пен инфрақұрылым талаптарының есебін жасау үшін жоба мәліметтерін енгізіңіз.",
        "project_name_label": "📌 Әуежай / Жоба атауы",
        "project_name_default": "Әуежай терминалының үлгілік жобасы",
        "select_systems_title": "🎯 Жоспарланатын әлсіз тоқ жүйелерін таңдаңыз",
        "select_systems_label": "Қажетті жүйелерді белгілеңіз:",
        "warning_no_system": "⚠ Жалғастыру үшін кем дегенде бір әлсіз тоқ жүйесін таңдаңыз.",
        "submit_btn": "🚀 Таңдалған жүйелер бойынша есепті қалыптастыру",
        "report_success": "✅ **{project}** жобасы үшін жоспарлау есебі сәтті есептелді!",
        "download_section": "📥 Есепті жүктеп алу",
        "cctv_title": "🎥 CCTV Бейнебақылау жүйесі",
        "cctv_scope": "Әуежай ауқымы:",
        "cctv_opt1": "Халықаралық транзиттік хаб (Жоғары қауіпсіздік / Қарқынды)",
        "cctv_opt2": "Өңірлік / Орташа әуежай",
        "cctv_sqm": "Терминалдың жабық ауданы (м²)",
        "cctv_checkpoints": "Төлқұжат және қауіпсіздік бақылау пункттері",
        "cctv_fence": "Периметрлік қоршау ұзындығы (Метр)",
        "cctv_anpr_chk": "Мемлекеттік нөмірлерді тану жүйесін (ANPR) қосу",
        "cctv_lanes": "ANPR Кіру/Шығу жолақтарының саны",
        "cctv_speed": "Қозғалыс жылдамдығының түрі",
        "cctv_speed_low": "Төмен жылдамдық (Бақылау-өткізу пункті / Шлагбаум)",
        "cctv_speed_high": "Жоғары жылдамдық (Негізгі жол / VIP кіру)",
        "cctv_cr": "Негізгі басқару бөлмелерінің саны",
        "cctv_op": "Ауысымдағы белсенді операторлар саны",
        "cctv_rem": "Қашықтан бақылау нүктелерінің саны",
        "cctv_days": "Бейнежазбаны сақтау мерзімі (Күн)",
        "cctv_res": "Камера сапасының стандарты",
        "acs_title": "🚪 Рұқсатты бақылау және турникет жүйесі (ACS)",
        "acs_doors_sec": "Есік түрлері мен саны",
        "acs_s_doors": "Бір жақтаулы бақыланатын есіктер",
        "acs_d_doors": "Екі жақтаулы бақыланатын есіктер",
        "acs_turnstiles": "Турникеттер саны (Қызметкерлер / Жолаушылар)",
        "acs_users_sec": "Пайдаланушылар мен биометрикалық параметрлер",
        "acs_users": "Тіркелетін жалпы карта пайдаланушыларының саны",
        "acs_face": "Бетті тану терминалдарының саны",
        "acs_finger": "Саусақ изін оқу құрылғыларының саны",
        "fas_title": "🚨 Өрт дабылы жүйесі (FAS)",
        "fas_sqm": "Өрт дабылы орнатылатын жабық аудан (м²)",
        "fas_rf": "Аспалы төбе мен көтерілген еден ішіндегі датчиктер қосылсын",
        "fas_beam": "Биік төбе/Ангар үшін сәулелік (Beam) датчиктер саны",
        "pava_title": "📢 Дауыстық хабарлау және эвакуация жүйесі (PA/VA)",
        "pava_sqm": "Хабарлау жасалатын жалпы жабық аудан (м²)",
        "pava_zones": "Тәуелсіз хабарлау аймақтарының (Zone) саны",
        "pava_env": "Басым орта түрі және шу деңгейі",
        "pava_env_std": "Стандартты терминал аймағы (70-75 dB)",
        "pava_env_noisy": "Шулы автотұрақ / Техникалық аймақ (80-85 dB)",
        "pava_env_quiet": "Тыныш офис / Басқару аймағы (60 dB)",
        "system_names": {
            "CCTV": "CCTV (Бейнебақылау жүйесі)",
            "ACS": "ACS (Рұқсатты бақылау жүйесі)",
            "FAS": "FAS (Өрт дабылы жүйесі)",
            "PA/VA": "PA/VA (Дауыстық хабарлау жүйесі)"
        }
    }
}

# --- DİL SEÇİMİ (EN ÜST SAĞ KÖŞE) ---
col_lang, col_blank = st.columns([1.5, 3.5])
with col_lang:
    selected_lang = st.selectbox(
        "🌐 Language / Dil / Тіл",
        ["TR", "EN", "KK"],
        format_func=lambda x: {"TR": "🇹🇷 Türkçe", "EN": "🇬🇧 English", "KK": "🇰🇿 Қазақша"}[x],
        index=0
    )

t = TEXTS[selected_lang]

# --- LOGO VE BAŞLIK ---
logo_url = "https://cdn.tav.aero/corporate/TavTechWebsite/tav_renkli_e470511c30.svg"

col_logo, col_title = st.columns([1.5, 3.5])
with col_logo:
    st.image(logo_url, width=320)
with col_title:
    st.title(t["page_title"])
    st.caption(t["caption"])

st.markdown("---")

# --- PROJE BİLGİSİ VE SİSTEM SEÇİMİ ---
project_name = st.text_input(t["project_name_label"], value=t["project_name_default"])

st.subheader(t["select_systems_title"])

sys_options = [
    t["system_names"]["CCTV"],
    t["system_names"]["ACS"],
    t["system_names"]["FAS"],
    t["system_names"]["PA/VA"]
]

selected_systems = st.multiselect(
    t["select_systems_label"],
    sys_options,
    default=[sys_options[0], sys_options[1]]
)

st.markdown("---")

if not selected_systems:
    st.warning(t["warning_no_system"])
else:
    system_tabs = st.tabs(selected_systems)
    inputs = {}

    for i, sys in enumerate(selected_systems):
        with system_tabs[i]:
            if t["system_names"]["CCTV"] in sys:
                st.markdown(f"### {t['cctv_title']}")
                inputs['cctv_airport_type'] = st.radio(
                    t["cctv_scope"],
                    [t["cctv_opt1"], t["cctv_opt2"]],
                    key="cctv_type"
                )
                c1, c2 = st.columns(2)
                with c1:
                    inputs['cctv_sqm'] = st.number_input(t["cctv_sqm"], min_value=1000, value=75000, step=5000, key="c_sqm")
                    inputs['cctv_checkpoints'] = st.number_input(t["cctv_checkpoints"], min_value=1, value=20, key="c_check")
                with c2:
                    inputs['cctv_fence_m'] = st.number_input(t["cctv_fence"], min_value=500, value=8000, step=500, key="c_fence")
                    inputs['cctv_use_anpr'] = st.checkbox(t["cctv_anpr_chk"], value=True, key="c_anpr_chk")

                if inputs['cctv_use_anpr']:
                    ca1, ca2 = st.columns(2)
                    with ca1:
                        inputs['cctv_lanes'] = st.number_input(t["cctv_lanes"], min_value=1, value=8, key="c_lanes")
                    with ca2:
                        inputs['cctv_anpr_speed'] = st.selectbox(t["cctv_speed"], [t["cctv_speed_low"], t["cctv_speed_high"]], key="c_speed")
                else:
                    inputs['cctv_lanes'] = 0

                c3, c4 = st.columns(2)
                with c3:
                    inputs['cctv_control_rooms'] = st.number_input(t["cctv_cr"], min_value=1, value=1, key="c_cr")
                    inputs['cctv_operators'] = st.number_input(t["cctv_op"], min_value=1, value=6, key="c_op")
                with c4:
                    inputs['cctv_remote_views'] = st.number_input(t["cctv_rem"], min_value=0, value=4, key="c_rem")
                    inputs['cctv_storage_days'] = st.selectbox(t["cctv_days"], [30, 60, 90, 180], index=1, key="c_days")
                    inputs['cctv_resolution'] = st.selectbox(t["cctv_res"], ["4MP", "2MP", "8MP"], key="c_res")

            elif t["system_names"]["ACS"] in sys:
                st.markdown(f"### {t['acs_title']}")
                ac1, ac2 = st.columns(2)
                with ac1:
                    st.markdown(f"**{t['acs_doors_sec']}**")
                    inputs['acs_single_doors'] = st.number_input(t["acs_s_doors"], min_value=0, value=80, step=5, key="a_s_doors")
                    inputs['acs_double_doors'] = st.number_input(t["acs_d_doors"], min_value=0, value=20, step=2, key="a_d_doors")
                    inputs['acs_turnstiles'] = st.number_input(t["acs_turnstiles"], min_value=0, value=16, step=2, key="a_turn")
                with ac2:
                    st.markdown(f"**{t['acs_users_sec']}**")
                    inputs['acs_users'] = st.number_input(t["acs_users"], min_value=100, value=3000, step=500, key="a_users")
                    inputs['acs_face_rec_qty'] = st.number_input(t["acs_face"], min_value=0, value=10, step=1, key="a_face_qty")
                    inputs['acs_fingerprint_qty'] = st.number_input(t["acs_finger"], min_value=0, value=15, step=1, key="a_finger_qty")

            elif t["system_names"]["FAS"] in sys:
                st.markdown(f"### {t['fas_title']}")
                fc1, fc2 = st.columns(2)
                with fc1:
                    inputs['fas_sqm'] = st.number_input(t["fas_sqm"], min_value=1000, value=75000, step=5000, key="f_sqm")
                    inputs['fas_raised_floor'] = st.checkbox(t["fas_rf"], value=True, key="f_rf")
                with fc2:
                    inputs['fas_beam_detectors'] = st.number_input(t["fas_beam"], min_value=0, value=6, key="f_beam")

            elif t["system_names"]["PA/VA"] in sys:
                st.markdown(f"### {t['pava_title']}")
                pc1, pc2 = st.columns(2)
                with pc1:
                    inputs['pava_sqm'] = st.number_input(t["pava_sqm"], min_value=1000, value=75000, step=5000, key="p_sqm")
                    inputs['pava_zones'] = st.number_input(t["pava_zones"], min_value=1, value=16, step=1, key="p_zones")
                with pc2:
                    inputs['pava_environment'] = st.selectbox(t["pava_env"], [t["pava_env_std"], t["pava_env_noisy"], t["pava_env_quiet"]], key="p_env")

    st.markdown("---")
    submit_button = st.button(t["submit_btn"], use_container_width=True, type="primary")

    # --- HESAPLAMA VE SONUÇ EKRANI ---
    if submit_button:
        st.success(t["report_success"].format(project=project_name))
        
        res_tabs = st.tabs([f"📊 {s}" for s in selected_systems])

        for idx, sys in enumerate(selected_systems):
            with res_tabs[idx]:
                
                # --- CCTV HESAPLAMA ---
                if t["system_names"]["CCTV"] in sys:
                    sqm_per_cam = 60 if inputs['cctv_airport_type'] == t["cctv_opt1"] else 90
                    fence_m_per_cam = 40 if inputs['cctv_airport_type'] == t["cctv_opt1"] else 60
                    cam_per
