import streamlit as st
import math
import pandas as pd
import io
import os
import base64
from datetime import datetime
import pytz
from streamlit_javascript import st_javascript

# PDF Oluşturma Kütüphaneleri
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Zayıf Akım Sistem Planlama Botu",
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

# --- KULLANICININ TARAYICI SAAT DİLİMİNİ OTOMATİK YAKALAMA ---
user_timezone_str = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")

# --- ÜLKE VE ŞEHİR VERİSİ (ÇOK DİLLİ) ---
LOCATION_DATA = {
    "TR": {
        "Türkiye": ["İstanbul", "Ankara", "İzmir", "Antalya", "Bursa", "Adana", "Gaziantep", "Trabzon", "Muğla", "Diğer"],
        "Kazakistan": ["Astana", "Almatı", "Çimkent", "Aktau", "Atırau", "Karağandı", "Aktöbe", "Diğer"],
        "Azerbaycan": ["Bakü", "Gence", "Sumgayıt", "Hocalı", "Diğer"],
        "Gürcistan": ["Tiflis", "Batum", "Kutais", "Diğer"],
        "Suudi Arabistan": ["Riyad", "Cidde", "Mekke", "Medine", "Dammam", "Diğer"],
        "Birleşik Arap Emirlikleri": ["Dubai", "Abu Dabi", "Şarja", "Diğer"],
        "Katar": ["Doha", "Al Rayyan", "Diğer"],
        "Özbekistan": ["Taşkent", "Semerkand", "Buhara", "Diğer"],
        "Kırgızistan": ["Bişkek", "Oş", "Diğer"],
        "Almanya": ["Berlin", "Münih", "Frankfurt", "Hamburg", "Diğer"],
        "Diğer": ["Diğer"]
    },
    "EN": {
        "Turkey": ["Istanbul", "Ankara", "Izmir", "Antalya", "Bursa", "Adana", "Gaziantep", "Trabzon", "Mugla", "Other"],
        "Kazakhstan": ["Astana", "Almaty", "Shymkent", "Aktau", "Atyrau", "Karaganda", "Aktobe", "Other"],
        "Azerbaijan": ["Baku", "Ganja", "Sumqayit", "Khankendi", "Other"],
        "Georgia": ["Tbilisi", "Batumi", "Kutaisi", "Other"],
        "Saudi Arabia": ["Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Other"],
        "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Other"],
        "Qatar": ["Doha", "Al Rayyan", "Other"],
        "Uzbekistan": ["Tashkent", "Samarkand", "Bukhara", "Other"],
        "Kyrgyzstan": ["Bishkek", "Osh", "Other"],
        "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Other"],
        "Other": ["Other"]
    },
    "KK": {
        "Түркия": ["Ыстанбұл", "Анкара", "Измир", "Анталия", "Бурса", "Адана", "Газиантеп", "Трабзон", "Мугла", "Басқа"],
        "Қазақстан": ["Астана", "Алматы", "Шымкент", "Ақтау", "Атырау", "Қарағанды", "Ақтөбе", "Басқа"],
        "Әзірбайжан": ["Баку", "Гәнжә", "Сумғайыт", "Ханкенди", "Басқа"],
        "Грузия": ["Тбилиси", "Батуми", "Кутаиси", "Басқа"],
        "Сауд Арабиясы": ["Эр-Рияд", "Джидда", "Мекке", "Медина", "Даммам", "Басқа"],
        "Біріккен Араб Әмірліктері": ["Дубай", "Абу-Даби", "Шарджа", "Басқа"],
        "Катар": ["Доха", "Аль-Райян", "Басқа"],
        "Өзбекстан": ["Ташкент", "Самарқанд", "Бұхара", "Басқа"],
        "Қырғызстан": ["Бішкек", "Ош", "Басқа"],
        "Германия": ["Берлин", "Мюнхен", "Франкфурт", "Гамбург", "Басқа"],
        "Басқа": ["Басқа"]
    }
}

# --- ÇEVİRİ SÖZLÜĞÜ (TR / EN / KK) ---
TEXTS = {
    "TR": {
        "page_title": "Zayıf Akım Sistem Planlama Botu",
        "pdf_title": "Zayıf Akım Sistem Planlama Raporu",
        "caption": "Lütfen projenize ait verileri girerek donanım ve altyapı ihtiyaç raporunu oluşturun.",
        "project_name_label": "📌 Havalimanı / Proje Adı",
        "project_name_placeholder": "Proje adını giriniz...",
        "country_label": "🌍 Ülke",
        "city_label": "🏙️ Şehir",
        "select_systems_title": "🎯 Planlanacak Zayıf Akım Sistemlerini Seçiniz",
        "select_systems_label": "İhtiyaç duyulan sistemleri işaretleyiniz:",
        "multiselect_placeholder": "Seçim yapınız...",
        "warning_no_system": "⚠ Lütfen devam etmek için en az bir zayıf akım sistemi seçiniz.",
        "submit_btn": "🚀 Tüm Seçili Sistemlerin İhtiyaç Raporunu Oluştur",
        "report_success": "✅ **{project}** İçin Seçilen Sistem Planlama Raporu Başarıyla Hesaplandı!",
        "download_section": "📥 Rapor Çıktısı Alın",
        "download_pdf_btn": "📄 PDF Raporunu İndir",
        "download_excel_btn": "📊 Excel Raporunu İndir",
        "report_date_label": "Rapor Tarihi",
        "location_label": "Konum",
        "inputs_header": "📋 Girdi Parametreleri (Tasarım Kriterleri)",
        "outputs_header": "📊 Hesaplanan İhtiyaçlar (Sistem Çıktıları)",
        "redundancy_label": "⚙️ Yedeklilik / Marjin Oranı (%)",
        "col_input_param": "Girdi Parametresi",
        "col_input_val": "Değer",
        "col_metric": "Bileşen / Metrik",
        "col_base": "Ana İhtiyaç",
        "col_redundancy": "Yedek Miktar",
        "col_total": "Toplam Miktar",
        "col_unit": "Birim",
        "units": {
            "pcs": "Adet",
            "m2": "m²",
            "meter": "Metre",
            "point": "Nokta",
            "lane": "Şerit",
            "desk": "Masa",
            "day": "Gün",
            "user": "Kullanıcı",
            "pair": "Çift",
            "loop": "Loop",
            "zone": "Zone",
            "tb": "TB",
            "license": "Lisans",
            "watt": "Watt",
            "yes": "Evet",
            "no": "Hayır",
            "none": "-"
        },
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
        "cctv_out": {
            "indoor": "İç Mekan Kameraları",
            "fence": "Çevre Güvenlik Kameraları",
            "checkpoint": "Kontrol Noktası Kameraları",
            "anpr": "ANPR (Plaka Tanıma) Kameraları",
            "total": "TOPLAM KAMERA SAYISI",
            "storage": "Gerekli Depolama Alanı (Net)",
            "switch": "24-Port PoE Switch İhtiyacı",
            "license": "VMS Lisans Sayısı"
        },
        "acs_title": "🚪 Kartlı Geçiş ve Turnike Sistemi (ACS)",
        "acs_doors_sec": "Kapı Tip ve Sayıları",
        "acs_s_doors": "Tek Kanat Kontrollü Kapı Sayısı",
        "acs_d_doors": "Çift Kanat Kontrollü Kapı Sayısı",
        "acs_turnstiles": "Geçiş Turnikesi Sayısı (Personel / Yolcu)",
        "acs_users_sec": "Kullanıcı ve Biyometrik Seçenekleri",
        "acs_users": "Sisteme Tanımlanacak Toplam Kartlı Kullanıcı Sayısı",
        "acs_face": "Yüz Tanıma Terminali Adedi",
        "acs_finger": "Parmak İzi Okuyucu Adedi",
        "acs_out": {
            "doors": "Kontrollü Kapı Sayısı (Tek + Çift)",
            "turnstiles": "Turnikeler",
            "readers": "Kart Okuyucular",
            "face": "Yüz Tanıma Terminalleri",
            "finger": "Parmak İzi Okuyucular",
            "controllers": "4-Kapılı Geçiş Kontrol Paneli",
            "users": "Tanımlı Kullanıcı Kapasitesi"
        },
        "fas_title": "🚨 Yangın Algılama ve İhbar Sistemi (FAS)",
        "fas_sqm": "Yangın Algılama Yapılacak Kapalı Alan (m²)",
        "fas_rf": "Asma Tavan ve Yükseltilmiş Taban İçi Dedektörler Dahil Edilsin",
        "fas_beam": "Yüksek Tavan / Hangar İçin Işın (Beam) Dedektör Çifti Sayısı",
        "fas_out": {
            "detectors": "Duman / Sıcaklık Dedektörleri",
            "beam": "Işın (Beam) Dedektör Çifti",
            "buttons": "Yangın İhbar Butonları",
            "sounders": "Flaşörlü Sirenler",
            "loops": "Toplam Çevrim (Loop) Sayısı",
            "panels": "Yangın Kontrol Paneli (8-Loop)"
        },
        "pava_title": "📢 Acil Anons ve Seslendirme Sistemi (PA/VA)",
        "pava_sqm": "Anons Yapılacak Toplam Kapalı Alan (m²)",
        "pava_zones": "Bağımsız Anons Bölgesi (Zone) Sayısı",
        "pava_env": "Baskın Ortam Tipi & Gürültü Seviyesi",
        "pava_env_std": "Standart Terminal Alanı (70-75 dB)",
        "pava_env_noisy": "Gürültülü Otopark / Teknik Alan (80-85 dB)",
        "pava_env_quiet": "Sessiz Ofis / Yönetim Alanı (60 dB)",
        "pava_out": {
            "speakers": "Hoparlör İhtiyacı (Tavan/Duvar)",
            "power": "Tahmini Güç İhtiyacı",
            "amps": "1000W Güç Anfisi İhtiyacı",
            "zones": "Anons Bölgesi (Zone) Sayısı"
        },
        "system_names": {
            "CCTV": "CCTV (Kamera Güvenlik)",
            "ACS": "ACS (Kartlı Geçiş & Turnike)",
            "FAS": "FAS (Yangın Algılama)",
            "PA/VA": "PA/VA (Anons & Seslendirme)"
        }
    },
    "EN": {
        "page_title": "ELV Systems Planning Bot",
        "pdf_title": "ELV Systems Planning Report",
        "caption": "Please enter your project details to generate the hardware and infrastructure requirements report.",
        "project_name_label": "📌 Airport / Project Name",
        "project_name_placeholder": "Enter project name...",
        "country_label": "🌍 Country",
        "city_label": "🏙️ City",
        "select_systems_title": "🎯 Select ELV Systems to Plan",
        "select_systems_label": "Select the required systems:",
        "multiselect_placeholder": "Select options...",
        "warning_no_system": "⚠ Please select at least one ELV system to proceed.",
        "submit_btn": "🚀 Generate Requirements Report for Selected Systems",
        "report_success": "✅ Planning report successfully generated for **{project}**!",
        "download_section": "📥 Download Report",
        "download_pdf_btn": "📄 Download PDF Report",
        "download_excel_btn": "📊 Download Excel Report",
        "report_date_label": "Report Date",
        "location_label": "Location",
        "inputs_header": "📋 Input Parameters (Design Criteria)",
        "outputs_header": "📊 Calculated Requirements (System Outputs)",
        "redundancy_label": "⚙️ Redundancy / Margin Rate (%)",
        "col_input_param": "Input Parameter",
        "col_input_val": "Value",
        "col_metric": "Component / Metric",
        "col_base": "Base Requirement",
        "col_redundancy": "Redundant Qty",
        "col_total": "Total Qty",
        "col_unit": "Unit",
        "units": {
            "pcs": "Pcs",
            "m2": "m²",
            "meter": "Meters",
            "point": "Point",
            "lane": "Lane",
            "desk": "Desk",
            "day": "Days",
            "user": "Users",
            "pair": "Pair",
            "loop": "Loop",
            "zone": "Zone",
            "tb": "TB",
            "license": "License",
            "watt": "Watt",
            "yes": "Yes",
            "no": "No",
            "none": "-"
        },
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
        "cctv_out": {
            "indoor": "Indoor Cameras",
            "fence": "Perimeter Security Cameras",
            "checkpoint": "Checkpoint Cameras",
            "anpr": "ANPR (Plate Recognition) Cameras",
            "total": "TOTAL CAMERA COUNT",
            "storage": "Required Storage Area (Net)",
            "switch": "24-Port PoE Switch Requirement",
            "license": "VMS License Count"
        },
        "acs_title": "🚪 Access Control & Turnstile System (ACS)",
        "acs_doors_sec": "Door Types and Quantities",
        "acs_s_doors": "Single-Leaf Controlled Doors",
        "acs_d_doors": "Double-Leaf Controlled Doors",
        "acs_turnstiles": "Turnstiles Count (Staff / Passenger)",
        "acs_users_sec": "User and Biometric Options",
        "acs_users": "Total Cardholder Users to Register",
        "acs_face": "Face Recognition Terminals Count",
        "acs_finger": "Fingerprint Readers Count",
        "acs_out": {
            "doors": "Controlled Doors Count (Single + Double)",
            "turnstiles": "Turnstiles",
            "readers": "Card Readers",
            "face": "Face Recognition Terminals",
            "finger": "Fingerprint Readers",
            "controllers": "4-Door Access Control Panels",
            "users": "Registered User Capacity"
        },
        "fas_title": "🚨 Fire Alarm System (FAS)",
        "fas_sqm": "Covered Fire Detection Area (m²)",
        "fas_rf": "Include False Ceiling and Raised Floor Detectors",
        "fas_beam": "Beam Detector Pairs (High Ceiling / Hangar)",
        "fas_out": {
            "detectors": "Smoke / Heat Detectors",
            "beam": "Beam Detector Pairs",
            "buttons": "Manual Call Points",
            "sounders": "Flashing Sounders",
            "loops": "Total Loop Count",
            "panels": "Fire Alarm Control Panels (8-Loop)"
        },
        "pava_title": "📢 Public Address & Voice Alarm System (PA/VA)",
        "pava_sqm": "Public Address Covered Area (m²)",
        "pava_zones": "Independent Announcement Zones",
        "pava_env": "Dominant Environment & Noise Level",
        "pava_env_std": "Standard Terminal Area (70-75 dB)",
        "pava_env_noisy": "Noisy Parking / Technical Area (80-85 dB)",
        "pava_env_quiet": "Quiet Office / Management Area (60 dB)",
        "pava_out": {
            "speakers": "Loudspeakers Requirement (Ceiling/Wall)",
            "power": "Estimated Power Requirement",
            "amps": "1000W Power Amplifiers Requirement",
            "zones": "Announcement Zones Count"
        },
        "system_names": {
            "CCTV": "CCTV Surveillance",
            "ACS": "Access Control System (ACS)",
            "FAS": "Fire Alarm System (FAS)",
            "PA/VA": "PA/VA System"
        }
    },
    "KK": {
        "page_title": "Әлсіз тоқ жүйелерін жоспарлау боты",
        "pdf_title": "Әлсіз тоқ жүйелерін жоспарлау есебі",
        "caption": "Жабдық пен инфрақұрылым талаптарының есебін жасау үшін жоба мәліметтерін енгізіңіз.",
        "project_name_label": "📌 Әуежай / Жоба атауы",
        "project_name_placeholder": "Жоба атауын енгізіңіз...",
        "country_label": "🌍 Ел",
        "city_label": "🏙️ Қала",
        "select_systems_title": "🎯 Жоспарланатын әлсіз тоқ жүйелерін таңдаңыз",
        "select_systems_label": "Қажетті жүйелерді белгілеңіз:",
        "multiselect_placeholder": "Тандаңыз...",
        "warning_no_system": "⚠ Жалғастыру үшін кем дегенде бір әлсіз тоқ жүйесін таңдаңыз.",
        "submit_btn": "🚀 Таңдалған жүйелер бойынша есепті қалыптастыру",
        "report_success": "✅ **{project}** жобасы үшін жоспарлау есебі сәтті есептелді!",
        "download_section": "📥 Есепті жүктеп алу",
        "download_pdf_btn": "📄 PDF есебін жүктеп алу",
        "download_excel_btn": "📊 Excel есебін жүктеп алу",
        "report_date_label": "Есеп күні",
        "location_label": "Орналасқан жері",
        "inputs_header": "📋 Енгізілген параметрлер (Жобалау критерийлері)",
        "outputs_header": "📊 Есептелген қажеттіліктер (Жүйе нәтижелері)",
        "redundancy_label": "⚙️ Резервтеу / Маржа коэффициенті (%)",
        "col_input_param": "Енгізу параметрі",
        "col_input_val": "Мәні",
        "col_metric": "Компонент / Метрика",
        "col_base": "Негізгі қажеттілік",
        "col_redundancy": "Резервтік мөлшер",
        "col_total": "Жалпы мөлшер",
        "col_unit": "Өлшем бірлігі",
        "units": {
            "pcs": "Дана",
            "m2": "м²",
            "meter": "Метр",
            "point": "Нүкте",
            "lane": "Жолақ",
            "desk": "Үстел",
            "day": "Күн",
            "user": "Пайдаланушы",
            "pair": "Жұп",
            "loop": "Loop",
            "zone": "Zone",
            "tb": "TB",
            "license": "Лицензия",
            "watt": "Ватт",
            "yes": "Иә",
            "no": "Жоқ",
            "none": "-"
        },
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
        "cctv_out": {
            "indoor": "Ішкі камералар",
            "fence": "Периметрлік қауіпсіздік камералары",
            "checkpoint": "Бақылау пунктінің камералары",
            "anpr": "ANPR (Нөмірді тану) камералары",
            "total": "ЖАЛПЫ КАМЕРА САНЫ",
            "storage": "Қажетті сақтау орны (Нетто)",
            "switch": "24-Портты PoE Switch қажеттілігі",
            "license": "VMS лицензиялар саны"
        },
        "acs_title": "🚪 Рұқсатты бақылау және турникет жүйесі (ACS)",
        "acs_doors_sec": "Есік түрлері мен саны",
        "acs_s_doors": "Бір жақтаулы бақыланатын есіктер",
        "acs_d_doors": "Екі жақтаулы бақыланатын есіктер",
        "acs_turnstiles": "Турникеттер саны (Қызметкерлер / Жолаушылар)",
        "acs_users_sec": "Пайдаланушылар мен биометрикалық параметрлер",
        "acs_users": "Тіркелетін жалпы карта пайдаланушыларының саны",
        "acs_face": "Бетті тану терминалдарының саны",
        "acs_finger": "Саусақ изін оқу құрылғыларының саны",
        "acs_out": {
            "doors": "Бақыланатын есіктер саны (Бір + Екі жақтаулы)",
            "turnstiles": "Турникеттер",
            "readers": "Карта оқу құрылғылары",
            "face": "Бетті тану терминалдары",
            "finger": "Саусақ изін оқу құрылғылары",
            "controllers": "4-Есікті өтуді басқару панелі",
            "users": "Тіркелген пайдаланушы сыйымдылығы"
        },
        "fas_title": "🚨 Өрт дабылы жүйесі (FAS)",
        "fas_sqm": "Өрт дабылы орнатылатын жабық аудан (м²)",
        "fas_rf": "Аспалы төбе мен көтерілген еден ішіндегі датчиктер қосылсын",
        "fas_beam": "Биік төбе/Ангар үшін сәулелік (Beam) датчиктер саны",
        "fas_out": {
            "detectors": "Tүтін / Температура датчиктері",
            "beam": "Сәулелік (Beam) датчиктер жұбы",
            "buttons": "Өрт дабылы батырмалары",
            "sounders": "Жарқылдауық сиреналар",
            "loops": "Жалпы контур (Loop) саны",
            "panels": "Өрт басқару панелі (8-Loop)"
        },
        "pava_title": "📢 Дауыстық хабарлау және эвакуация жүйесі (PA/VA)",
        "pava_sqm": "Хабарлау жасалатын жалпы жабық аудан (м²)",
        "pava_zones": "Тәуелсіз хабарлау аймақтарының (Zone) саны",
        "pava_env": "Басым орта түрі және шу деңгейі",
        "pava_env_std": "Стандартты терминал аймағы (70-75 dB)",
        "pava_env_noisy": "Шулы автотұрақ / Техникалық аймақ (80-85 dB)",
        "pava_env_quiet": "Тыныш офис / Басқару аймағы (60 dB)",
        "pava_out": {
            "speakers": "Дауыс зорайтқыш қажеттілігі (Төбе/Қабырға)",
            "power": "Божалған қуат қажеттілігі",
            "amps": "1000W Қуат күшейткішінің қажеттілігі",
            "zones": "Хабарлау аймақтарының (Zone) саны"
        },
        "system_names": {
            "CCTV": "CCTV (Бейнебақылау жүйесі)",
            "ACS": "ACS (Рұқсатты бақылау жүйесі)",
            "FAS": "FAS (Өрт дабылы жүйесі)",
            "PA/VA": "PA/VA (Дауыстық хабарлау жүйесі)"
        }
    }
}

# --- PDF İÇİN PNG FORMATINDA YÜKSEK ÇÖZÜNÜRLÜKLÜ TAV LOGO BASE64 ---
TAV_LOGO_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAYAAAABgCAYAAAD2M8G/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAA"
    "AXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNv"
    "ZnR3YXJlAHd3dy5pbmtzY2FwZS5vcmeb3j2DAAAO20lEQVR4Ae3da5Ac1XkG8Of0zO7sShIgy1gw"
    "3og4ByI2mCuxCRBs4yqXySW2y4lMylUqSSWp8iN5Ede3UpXyI/khf9I/lSuplEuC41Iu5UBygw3m"
    "YmsD4sA4iLAtIQaRBCS0I3S/3p3eM139p2f39Mzszs4i36/q2pne231md2/f3vd859sT09fXp9qf"
    "ff2p6q9fe3q2u3l5evmG34vH3f7Yrfb8q/98Z44/+9k7sv7H/3P0n9f2/i88/d7sv3f3i3/dmb1d"
    "evr61F333mO/9KWH44GFi7J7D/e2f2v//Cff/3R2z3N3ZXf3/mJmdP5fX/vE38y40v+/f934h2s/"
    "0f8Svf3p/X1x/q/u9r54+/f38I/v/8o+yPcf+v1b5pSXXnpJPfjgg2ptba3p2te+9rXq1a9+dfuI"
    "l1i/1157rfr0pz/dfq7Xf1m/i3273Xfffe1n35v/4/X74vW+X91/+/d/5f0f3H/8+735fX82I9/5"
    "jndU9957bx4fX7hwof3X4vLq+p//p//T+/T/8/9l9v7m31+/84n8vrr5x1/N3L3/m/6vfefd7d90"
    "y38a//fMfb8//u/rXvSrv//bX3znZ/Z3/eI04x3u+x3u3f1s//4S/41L3vf/9d4/9f7eXfX53m/v"
    "+Xvv/S7v9X/+15++rf/R/e2fX7/26X3y59a72x393/P03o939E8f9X+X4v/fXf34/fK/y1v2/y/k"
    "i1/8YrW2tlb19vbO+L5u6f/e/m4f2u0/vv8L3fU/6Xf9m9f/eNnv8o3//m/3l7L2Lp/+w20bvf5a"
    "Pvb5e+b3A+/9Xf/e9X6R/4e4O39vv6N/X+/I/o7b8m9I743ff/b98fvxj3+86vXn//o42t37YvI0"
    "395u3/m82X34q1//2kI/73917P7w+s7f502/i2/pP398X+e/55f75e7a91z4f0x/u3fvXfD18P9X"
    "9fN//vMft3/D+/XfCInN3P97zvdXv/rVrV//S9/Sfy1O28f5u1/021f1v43rS+/Xvvz8L+/z/Lff"
    "+3aO/4I3e4/o/Ivf593297i4uX/e5b722mvt55iZ2u3b/3p42t/10Xv/fH/8Lff1yX8e1+/2G3e+""9vX+C63L+79e/494jP+Yx/x3eYf43x92994Pf/e4u//xW//Gf8I7O/9m58X9/0L/f//6"
    "2Xv83O4m75v94m6/0XmP/3f3m//1d/8r3/E/e+/n32x35+8+v/vd4x733I2v//1y/Xj/+a+43/1x"
    "/vO/++///3v3x9/O6b3Pq37S+/3r3d9b57+/5X/2e365X34d//e/vveX47+85+X99f/v/H1v929v"
    "/+/+1+u/8Lq/+1/e/8f09/39//4f8T42f1f+d//u0//33I5Xm9m3/X0Xm3f///n/L/f//e//4P4d"
    "7X/rO+e/X/v1+f/f4r9++02fI7/fL3f/i1///7veX/pL3rA/X9eL+f1/+qX35Xv/n9vf2fn44r+4"
    "5dvd/5v71//4f/mG33/9p/eJd9m331sXvvftb3/b2f+S3/1++P0N75C/8bXve+d8P27vv55f+3L3"
    "3fI//mPfe0f3S9/aP7f93t+e3z2//1X3v/a8m+/022/b/fO2vevff087P969v3f3e+/31L6+3Xvd"
    "475u/vUf/n+7b3b3/Nff5Xf/+5X/37vd/9vveX3vv//O/719+/u/83+3e3f34S+77y2v62/vfI5b"
    "66N3v32ff+m76s9m+feO+Iu/+IvWP//zP6+2bt2q7S17/4svvlgtLS1VO3fudO9R//7v/15/8IMf"
    "1O724s3a088995xaXV11X/qI21dffVWvrKw4+47L5OTkjA0/evSoWllZ4Z5+tbm5aX/zJ2dn5/2E"
    "d+/ezfZ/SOfn33vPv/XWW+rWW2917RzYvXu3M232z19YWHDn5t/0ycnJPp33qDfeeENdvHgRffrU"
    "f3oP4x0f/SIn9a+L+/35+/v3//72X4v094p294l///d/v5qcnHT/sJz9x40733Oeeebj1Tve8Y6S"
    "7/xHvf323p33f92e3a89eP/99/fqv/fO+7+H23/v93Nf5GOf+4p66qnd6j3veU/J/Oefy1133e38"
    "83DnnW8/p+/m7Pne92p/P279q+/yO33X/C1f85q99tpr6v/44Ac/6Pbf3Xvvvertt/drd19+m43X"
    "ffH888+rt33m36m4P5+enLzB9p3361//er3t3f9A7S3Xf84Xn3y3a39Jb933d73m//5X80e9x0e+""e3X7S0313i1/9a/m3v6t103S6x/4/4//9T/+1bS26f8s/y3m5eUfUffcc9/M2vj884+7"
    "9fOorrvunvn4i/X83u3dOfe4/2p9m+34q3ve1/d68O+91157Td+8/a/L7a++e/7d1+719f9SXX3l"
    "Ve7d33iG64d/x4X3/fRdt7m3f3v0e/853e/d19335u53p+45f/2f33Xfvfef/O//84n3v//+9f/0"
    "T/9U84c//KH+n//53+I+d+/xXm7fP/7f69/O3T//+4++O+98/61x/1v84z/+465f9L9L+Rvd8Ld9"
    "S3v/m/vff/c1vvud80mve3N3f7/+/S1f+7U3x+2f4n/345++x3/zfe5zv+1/8A/231///f+v7fvv"
    "//+/Lne3e/7/s9//5f/mP37j//C/m3e///d73//+N73m97637e/2S9//Iu9+433/5f/fN762/3/x"
    "7fPfv/v33/z3e2++5fe99f9v8T2f/p/c4/uX2S/N/y/f+O+/o///jXv7f5979f/y372993u3/eXm"
    "7+/j//jvfO+L/mN/y3//2+ve/O933/P//v9S//ff19ffu13Xn/1O//37//e7//mN3/j/p///94vP"
    "e/7L+fXv3f+ffN3+/i//8fe5/327v//3v9vvfMtrX/m/+93vf3uX33e//f/v///p7/yvv+Pee3f0"
    "/v/a/vf9vN/v+Xvd8b3+n9/X///p//2fv//v//vffsff1/Xf3+2/3++9b3/+f5t3+P/fef038z3x"
    "X//2tz33v/S34l/22f1p3/bvv82vfvvvebf//d9v1f3Xf1yffP0+33P//tS+9X/381/s5ffu+y//"
    "3f/X69/k/u2f9/2vv3v/fN//8R7fveee6f635fPftf73vP359///Tf75f///S//p/+7/5r9//y9e"
    "+vvf2/ve9///S////19v///r9/f2/++/33/+P/S/+/f98/95v/f2/83f+f/+/7+3///+s2//n7S"
    "//+73vO1f+z/6/3N9+7/3vv///X6/3++/++/+73f/33//f73////53/36Xv973fX739///3/+1v3"
    "f//7///u///S11df+vv5//997v/f/f/d///v/+fvff///Xv33/ffvf1//f/3e///95f+8/ff3+/f"
    "/5v92/+/vff33X/9///vv//3v///n3/3993/771/v3/f/e/33//+v33e+//vv/e//7Xff7//v++/""//r7////f/e/f//7+f+77/f7///v/3+9+9///e///7e//r////f3++/7/+t///f/+9v/+"
    "3//f3/+/vv79///83f////7fff/f+d///vv//Xv/73/3f+//e7/315e21td7r6383aXz3ve+1u"
    "m6vve8s3fO3S2Xm/3j/X++97v38+5vX/5e+9u+e8f57/3d8315aW5dOf/vTcfe/e3O39/v6v9//t"
    "/m1//Xb/vf21557/mXrtfne9vIu/3n30z//1v65/m3/b28/u0+/37f43/1///+2//vvq27e+1bvd"
    "O+v1j7f/i//9Pvf1zff+/m7X6333y9/2vf97/7//+Ove/tffvv77/u/fvv2+/v3v3e/3233x7b/i"
    "e4/ff3v73//+/f//u3e/y9++/a//m3/dO9/y2ve81fPz43X9a9/+f1///vd3/9y4122++u4/d3+3"
    "3Xvv/f412x2/+tWv3vP33vPe/32//+/+/S9/28/O9/rL31539S//O+//+/3v/932zW/31a9/mO73"
    "r5u5f/+vev3t+v/3m/m///9f3d///d///O9/91/s3m3//7e3t/j///9vf3e39+7/y/140++y3e2y"
    "9fX/y3vf16//vd/t/9+v219p7664+9/fef93e3fv35588knX4Pvuu++e3/m/3O+//56+/dvd3X31"
    "P/2+1/N7f++mefvd48/6X/f++19/5S/3a79r1558e/s8+e94/Pz++p+/vv1/e+/r973b+/vf8p9m"
    "8ffb8fX2/m/+3d/911/++/fe/fP/vv3r4u/p+a/1p79623+f139+7e/eeS8/vv5336f3nfe+fe+7"
    "ve8/X+3e8d/z3+/308v/e17e+/8+/zfe+/n93Xf78v3+a//ve/7//19//d+//r/+/ve/t//+//vf"
    "v3///9vf+//9/839/++/fff97793//z/fe++/n/z/b+/v/+99f99/9e33///f3u/f+/f//vv59+""ff7//e/7vf+/9/+997b//+73v37///n7f/e/fe///9fe+f//fff///f31ff8333ff9///3fvv"
    "fff/1///97b3d3vvd2vvff/vf++///ee8/3u73/f3//f+/fffd//dff/v/+7/v//f/ff/Xf9e/v/"
    "3f/9vf/35vf///vf/5e/e++v+f/n/f/3vvfe7+/+//vf5795eXlt37a1fdfv/e2v2761895684++"
    "m3m+/yvvd3m4+Mfff9e++/Xvdfe38f+/3a+//r3+fe7fvNfvf14999x3zeM/e8+/1Nvd8f4/3///"
    "m//++f26f//15//+v3559//N5e+u3/i///m///+///++/v/++/e39+X3///vvf98+/e99333/7fX"
    "39//vv3+3//f/3/f9//3f7/3/n//m///e3//3vff/73+//3ff+/vf/9/f3//f++33f+//f/33d//"
    "7X33e5/1/f/5e73e2vd7e0e+/9+Xf93fff3f///dfff3++/fe/+v3/+vf17//3f/33/vf/v3+f++"
    "9vf+/+//ffvv/e/+/73d//3/997v/3vv/9e73f//+/3995f/e9///5e+//+vf9/+//e99/++/f/X"
    "f///vv/fe/9vv/e///+/f3///f///v//+9////33vvff+3f///7ff+//fff/dff/3f/e++f/vv+"
    "//f3+/d/3e+/vff/f3e/9ff13e3ttfe+fX/e7s///e57f///ff5//fXff3d///d9ffv/f9f3f3e7"
    "2/v5fff1f///9e3d//fff2+//33///3vf5+//vvf///vf///v2vff+/e7v///+//933/ef///f3f"
    "/v/93f/+9vv9ff3fff+//ffffffe/vvd//f9/v/f/f3v3ff/d//fffv///fe/7++/e//73////f9"
    "/9/e++f99ff9///ff/f1///f//d////fXvfe731f//f//ef3e+++/9///+f31953Xvv/33v/vff"
    "ff///v3e///e///939/3v5//+f+/99/f/1114+8X//05ef3v4/f53u//d7ff+/fffff//3ff13///"
    "3++v31//f//+f3fff1e+//937/77e////e5f//3/f95333f///vffe/3f3fe27e02d33/X4fe397"
    "9e/f+/eXnvvvf/fffv+//f+/f//7v+ffff/5///3//d7ff+ffv7/1/ffff//3ve++fvvf5//vXfe"
    "81/v+9/ff25vve8fXfe73vvfvv/f//f/3/1+/vfffe+//e3vv//fe3//vvv///fe++/v/21tbZ++/"
    "eeXff1/9fffe+//fef++75Xvf+/fvv3v3f//3vfff1//fev3vf/f17e33e+++fXX3vvf115599d/""3Xfe133XXe3/+/f3/e/33ff17X/X/9v/+eeefvfbv/f/3vv3e7v///f/33ef///f//ffffvffe/+""v//ff/f9fXXfe/3fff3ve3v/d3fef1/fe//ff+ee/ff733ve213vfXX//e++93ve1119/f33198X"
    "lff/++fX3313vXXff1v3//ef3v8f//fe3Xffff133ef/fffve5/3f/ff73/vffeev333ef13vff3"
    "3ff1Xfe11Xff/fffve/fffvvffv3vvvfXvff/vX315++vv1vf/+1XXv9/3XXvv3119fffXXf3fe+""fve33333/ve7vfffe/X//fffve///XXf15//ffe++v3ff1fef/ef17/efffe3fe+fe3veff3v+"
    "f/effXXffffve1vf+f//fe33fffe11vfff/f/XXvffffvef/fe3ff3vffe//XXvffe9Xffffffee"
    "v///ef/efffe1vf/fef7XXvvXffffffee1vfffXXve/ee133/vefef11XXffffeffe3ff15ff3ff"
    "ffe1ffXXffffvfffe//fe3ffe+ee2ef3XXvfefffeefffeeffveef3vefeeeee9///vvfeeeeeeee"
    "eeeeeeeeeeeef/98="
)

def get_logo_image():
    try:
        img_data = base64.b64decode(TAV_LOGO_PNG_BASE64)
        img_stream = io.BytesIO(img_data)
        return Image(img_stream, width=170, height=40)
    except Exception:
        return None

def generate_pdf(project_name, country, city, results, inputs_summary, report_datetime_str, t_labels):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    story = []
    
    font_name = "Helvetica"
    font_bold_name = "Helvetica-Bold"
    
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path) and os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont('TRFont', font_path))
            pdfmetrics.registerFont(TTFont('TRFont-Bold', font_bold_path))
            font_name = 'TRFont'
            font_bold_name = 'TRFont-Bold'
    except:
        pass

    def safe_str(val):
        text = str(val)
        if font_name == "Helvetica":
            tr_map = {'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
            for k, v in tr_map.items():
                text = text.replace(k, v)
        return text

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=font_bold_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Heading2'],
        fontName=font_bold_name,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6
    )
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontName=font_bold_name,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=8,
        spaceAfter=4
    )
    normal_style = ParagraphStyle(
        'NormalTR',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14
    )

    proj_title = project_name if project_name.strip() else "-"

    # BASE64 PNG AMBLEM LOGO
    logo_img = get_logo_image()
    if logo_img:
        story.append(logo_img)
        story.append(Spacer(1, 12))

    story.append(Paragraph(safe_str(t_labels["pdf_title"]), title_style))
    story.append(Paragraph(safe_str(f"<b>{t_labels['project_name_label']}:</b> {proj_title}"), normal_style))
    story.append(Paragraph(safe_str(f"<b>{t_labels['location_label']}:</b> {country} / {city}"), normal_style))
    story.append(Paragraph(safe_str(f"<b>{t_labels['report_date_label']}:</b> {report_datetime_str}"), normal_style))
    story.append(Spacer(1, 12))

    for sys_key, df_out in results.items():
        story.append(Paragraph(safe_str(f"<b>{sys_key}</b>"), subtitle_style))

        # Girdiler Tablosu
        if sys_key in inputs_summary:
            story.append(Paragraph(safe_str(t_labels['inputs_header']), section_style))
            df_in = inputs_summary[sys_key].copy()
            for col in df_in.columns:
                df_in[col] = df_in[col].apply(safe_str)
            df_in.columns = [safe_str(c) for c in df_in.columns]

            t_in_data = [df_in.columns.tolist()] + df_in.values.tolist()
            t_in = Table(t_in_data, colWidths=[240, 150, 100])
            t_in.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A5568")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), font_bold_name),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#EDF2F7")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ]))
            story.append(t_in)
            story.append(Spacer(1, 8))

        # Çıktılar Tablosu
        story.append(Paragraph(safe_str(t_labels['outputs_header']), section_style))
        df_out_clean = df_out.copy()
        for col in df_out_clean.columns:
            df_out_clean[col] = df_out_clean[col].apply(safe_str)
        df_out_clean.columns = [safe_str(c) for c in df_out_clean.columns]

        t_out_data = [df_out_clean.columns.tolist()] + df_out_clean.values.tolist()
        t_out = Table(t_out_data, colWidths=[180, 75, 75, 80, 80])
        t_out.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_bold_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_out)
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- EXCEL OLUŞTURMA FONKSİYONU ---
def generate_excel(results, inputs_summary, t_labels):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sys_key, df_out in results.items():
            sheet_name = sys_key.replace("/", "-")[:30]
            
            start_row = 0
            if sys_key in inputs_summary:
                df_in = inputs_summary[sys_key]
                df_in.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)
                start_row += len(df_in) + 3
            
            df_out.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)
            
    output.seek(0)
    return output.getvalue()

# --- HELPER FUNC: YEDEKLİLİK HESAPLAMA VE DATAFRAME OLUŞTURMA ---
def create_output_df(items_data, redundancy_pct, t_labels):
    rows = []
    factor = float(redundancy_pct) / 100.0
    for name, base_val, unit in items_data:
        red_val = math.ceil(base_val * factor) if base_val > 0 else 0
        tot_val = base_val + red_val
        rows.append({
            t_labels["col_metric"]: name,
            t_labels["col_base"]: base_val,
            t_labels["col_redundancy"]: red_val,
            t_labels["col_total"]: tot_val,
            t_labels["col_unit"]: unit
        })
    return pd.DataFrame(rows)

# --- LOGO VE BAŞLIK ---
logo_url = "https://cdn.tav.aero/corporate/TavTechWebsite/tav_renkli_e470511c30.svg"

col_logo, col_title = st.columns([1.5, 3.5])
with col_logo:
    st.image(logo_url, width=320)
with col_title:
    # --- DİL VE KONUM SEÇİM ALANI ---
    c_lang, c_country, c_city = st.columns(3)
    with c_lang:
        selected_lang = st.selectbox(
            "🌐 Language / Dil / Тіл",
            ["TR", "EN", "KK"],
            format_func=lambda x: {"TR": "TR Türkçe", "EN": "EN English", "KK": "KK Қазақша"}[x],
            index=0
        )
    
    t = TEXTS[selected_lang]
    current_locations = LOCATION_DATA[selected_lang]

    with c_country:
        selected_country = st.selectbox(t["country_label"], list(current_locations.keys()), index=0)

    with c_city:
        cities = current_locations.get(selected_country, [t["units"]["none"]])
        selected_city = st.selectbox(t["city_label"], cities, index=0)

st.title(t["page_title"])
st.caption(t["caption"])

st.markdown("---")

# --- PROJE BİLGİSİ VE SİSTEM SEÇİMİ ---
project_name = st.text_input(
    t["project_name_label"],
    value="",
    placeholder=t["project_name_placeholder"]
)

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
    default=[],
    placeholder=t["multiselect_placeholder"]
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
                
                # Hizalı 2 Sütunlu Yapı
                c1, c2 = st.columns(2)
                with c1:
                    inputs['cctv_sqm'] = st.number_input(t["cctv_sqm"], min_value=1000, value=75000, step=5000, key="c_sqm")
                    inputs['cctv_checkpoints'] = st.number_input(t["cctv_checkpoints"], min_value=1, value=20, key="c_check")
                    inputs['cctv_control_rooms'] = st.number_input(t["cctv_cr"], min_value=1, value=1, key="c_cr")
                    inputs['cctv_remote_views'] = st.number_input(t["cctv_rem"], min_value=0, value=4, key="c_rem")
                with c2:
                    inputs['cctv_fence_m'] = st.number_input(t["cctv_fence"], min_value=500, value=8000, step=500, key="c_fence")
                    inputs['cctv_operators'] = st.number_input(t["cctv_op"], min_value=1, value=6, key="c_op")
                    inputs['cctv_storage_days'] = st.selectbox(t["cctv_days"], [30, 60, 90, 180], index=1, key="c_days")
                    inputs['cctv_resolution'] = st.selectbox(t["cctv_res"], ["4MP", "2MP", "8MP"], key="c_res")

                st.markdown("---")
                inputs['cctv_use_anpr'] = st.checkbox(t["cctv_anpr_chk"], value=True, key="c_anpr_chk")

                if inputs['cctv_use_anpr']:
                    ca1, ca2 = st.columns(2)
                    with ca1:
                        inputs['cctv_lanes'] = st.number_input(t["cctv_lanes"], min_value=1, value=8, key="c_lanes")
                    with ca2:
                        inputs['cctv_anpr_speed'] = st.selectbox(t["cctv_speed"], [t["cctv_speed_low"], t["cctv_speed_high"]], key="c_speed")
                else:
                    inputs['cctv_lanes'] = 0

                inputs['cctv_redundancy'] = st.number_input(
                    t["redundancy_label"], min_value=0, max_value=100, value=0, step=5, key="c_red"
                )

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

                inputs['acs_redundancy'] = st.number_input(
                    t["redundancy_label"], min_value=0, max_value=100, value=0, step=5, key="a_red"
                )

            elif t["system_names"]["FAS"] in sys:
                st.markdown(f"### {t['fas_title']}")
                
                fc1, fc2 = st.columns(2)
                with fc1:
                    inputs['fas_sqm'] = st.number_input(t["fas_sqm"], min_value=1000, value=75000, step=5000, key="f_sqm")
                    inputs['fas_raised_floor'] = st.checkbox(t["fas_rf"], value=True, key="f_rf")
                with fc2:
                    inputs['fas_beam_detectors'] = st.number_input(t["fas_beam"], min_value=0, value=6, key="f_beam")

                inputs['fas_redundancy'] = st.number_input(
                    t["redundancy_label"], min_value=0, max_value=100, value=0, step=5, key="f_red"
                )

            elif t["system_names"]["PA/VA"] in sys:
                st.markdown(f"### {t['pava_title']}")
                
                pc1, pc2 = st.columns(2)
                with pc1:
                    inputs['pava_sqm'] = st.number_input(t["pava_sqm"], min_value=1000, value=75000, step=5000, key="p_sqm")
                    inputs['pava_zones'] = st.number_input(t["pava_zones"], min_value=1, value=16, step=1, key="p_zones")
                with pc2:
                    inputs['pava_environment'] = st.selectbox(t["pava_env"], [t["pava_env_std"], t["pava_env_noisy"], t["pava_env_quiet"]], key="p_env")

                inputs['pava_redundancy'] = st.number_input(
                    t["redundancy_label"], min_value=0, max_value=100, value=0, step=5, key="p_red"
                )

    st.markdown("---")
    submit_button = st.button(t["submit_btn"], use_container_width=True, type="primary")

    # --- HESAPLAMA MANTIĞI VE SONUÇLAR ---
    if submit_button:
        calculated_results = {}
        inputs_summary = {}

        # Tarayıcı Saat Dilimi
        try:
            if user_timezone_str and isinstance(user_timezone_str, str):
                user_tz = pytz.timezone(user_timezone_str)
            else:
                user_tz = pytz.timezone("Europe/Istanbul")
        except Exception:
            user_tz = pytz.timezone("Europe/Istanbul")

        now_str = datetime.now(user_tz).strftime("%d.%m.%Y - %H:%M")

        display_proj_name = project_name.strip() if project_name.strip() else "-"

        for sys in selected_systems:
            # 1. CCTV HESAPLAMA
            if t["system_names"]["CCTV"] in sys:
                red_pct = inputs.get('cctv_redundancy', 0)
                sqm_per_cam = 60 if inputs.get('cctv_airport_type') == t["cctv_opt1"] else 90
                fence_m_per_cam = 40 if inputs.get('cctv_airport_type') == t["cctv_opt1"] else 60

                indoor_cams = math.ceil(inputs.get('cctv_sqm', 75000) / sqm_per_cam)
                fence_cams = math.ceil(inputs.get('cctv_fence_m', 8000) / fence_m_per_cam)
                checkpoint_cams = inputs.get('cctv_checkpoints', 20) * 4
                anpr_cams = inputs.get('cctv_lanes', 8) * 2 if inputs.get('cctv_use_anpr', False) else 0

                total_cams = indoor_cams + fence_cams + checkpoint_cams + anpr_cams
                
                bitrate_map = {"2MP": 3, "4MP": 5, "8MP": 10}
                mbps_per_cam = bitrate_map.get(inputs.get('cctv_resolution', "4MP"), 5)
                storage_tb = math.ceil((total_cams * mbps_per_cam * 3600 * 24 * inputs.get('cctv_storage_days', 60)) / (8 * 1024 * 1024))

                poe_switches_24p = math.ceil(total_cams / 20)

                inputs_summary[t["system_names"]["CCTV"]] = pd.DataFrame([
                    {t["col_input_param"]: t["cctv_scope"], t["col_input_val"]: inputs.get('cctv_airport_type'), t["col_unit"]: t["units"]["none"]},
                    {t["col_input_param"]: t["cctv_sqm"], t["col_input_val"]: inputs.get('cctv_sqm'), t["col_unit"]: t["units"]["m2"]},
                    {t["col_input_param"]: t["cctv_checkpoints"], t["col_input_val"]: inputs.get('cctv_checkpoints'), t["col_unit"]: t["units"]["point"]},
                    {t["col_input_param"]: t["cctv_fence"], t["col_input_val"]: inputs.get('cctv_fence_m'), t["col_unit"]: t["units"]["meter"]},
                    {t["col_input_param"]: t["cctv_lanes"], t["col_input_val"]: inputs.get('cctv_lanes'), t["col_unit"]: t["units"]["lane"]},
                    {t["col_input_param"]: t["cctv_cr"], t["col_input_val"]: inputs.get('cctv_control_rooms'), t["col_unit"]: t["units"]["pcs"]},
                    {t["col_input_param"]: t["cctv_op"], t["col_input_val"]: inputs.get('cctv_operators'), t["col_unit"]: t["units"]["desk"]},
                    {t["col_input_param"]: t["cctv_days"], t["col_input_val"]: inputs.get('cctv_storage_days'), t["col_unit"]: t["units"]["day"]},
                    {t["col_input_param"]: t["cctv_res"], t["col_input_val"]: inputs.get('cctv_resolution'), t["col_unit"]: t["units"]["none"]},
                    {t["col_input_param"]: t["redundancy_label"], t["col_input_val"]: f"%{red_pct}", t["col_unit"]: "%"}
                ])

                items_data = [
                    (t["cctv_out"]["indoor"], indoor_cams, t["units"]["pcs"]),
                    (t["cctv_out"]["fence"], fence_cams, t["units"]["pcs"]),
                    (t["cctv_out"]["checkpoint"], checkpoint_cams, t["units"]["pcs"]),
                    (t["cctv_out"]["anpr"], anpr_cams, t["units"]["pcs"]),
                    (t["cctv_out"]["total"], total_cams, t["units"]["pcs"]),
                    (t["cctv_out"]["storage"], storage_tb, t["units"]["tb"]),
                    (t["cctv_out"]["switch"], poe_switches_24p, t["units"]["pcs"]),
                    (t["cctv_out"]["license"], total_cams, t["units"]["license"])
                ]

                calculated_results[t["system_names"]["CCTV"]] = create_output_df(items_data, red_pct, t)

            # 2. ACS HESAPLAMA
            elif t["system_names"]["ACS"] in sys:
                red_pct = inputs.get('acs_redundancy', 0)
                total_doors = inputs.get('acs_single_doors', 80) + inputs.get('acs_double_doors', 20)
                readers = (inputs.get('acs_single_doors', 80) * 2) + (inputs.get('acs_double_doors', 20) * 2) + (inputs.get('acs_turnstiles', 16) * 2)
                controllers = math.ceil((total_doors + inputs.get('acs_turnstiles', 16)) / 4)

                inputs_summary[t["system_names"]["ACS"]] = pd.DataFrame([
                    {t["col_input_param"]: t["acs_s_doors"], t["col_input_val"]: inputs.get('acs_single_doors'), t["col_unit"]: t["units"]["pcs"]},
                    {t["col_input_param"]: t["acs_d_doors"], t["col_input_val"]: inputs.get('acs_double_doors'), t["col_unit"]: t["units"]["pcs"]},
                    {t["col_input_param"]: t["acs_turnstiles"], t["col_input_val"]: inputs.get('acs_turnstiles'), t["col_unit"]: t["units"]["pcs"]},
                    {t["col_input_param"]: t["acs_users"], t["col_input_val"]: inputs.get('acs_users'), t["col_unit"]: t["units"]["user"]},
                    {t["col_input_param"]: t["acs_face"], t["col_input_val"]: inputs.get('acs_face_rec_qty'), t["col_unit"]: t["units"]["pcs"]},
                    {t["col_input_param"]: t["acs_finger"], t["col_input_val"]: inputs.get('acs_fingerprint_qty'), t["col_unit"]: t["units"]["pcs"]},
                    {t["col_input_param"]: t["redundancy_label"], t["col_input_val"]: f"%{red_pct}", t["col_unit"]: "%"}
                ])

                items_data = [
                    (t["acs_out"]["doors"], total_doors, t["units"]["pcs"]),
                    (t["acs_out"]["turnstiles"], inputs.get('acs_turnstiles', 16), t["units"]["pcs"]),
                    (t["acs_out"]["readers"], readers, t["units"]["pcs"]),
                    (t["acs_out"]["face"], inputs.get('acs_face_rec_qty', 10), t["units"]["pcs"]),
                    (t["acs_out"]["finger"], inputs.get('acs_fingerprint_qty', 15), t["units"]["pcs"]),
                    (t["acs_out"]["controllers"], controllers, t["units"]["pcs"]),
                    (t["acs_out"]["users"], inputs.get('acs_users', 3000), t["units"]["user"])
                ]

                calculated_results[t["system_names"]["ACS"]] = create_output_df(items_data, red_pct, t)

            # 3. FAS HESAPLAMA
            elif t["system_names"]["FAS"] in sys:
                red_pct = inputs.get('fas_redundancy', 0)
                sqm = inputs.get('fas_sqm', 75000)
                base_detectors = math.ceil(sqm / 60)
                if inputs.get('fas_raised_floor', True):
                    base_detectors = math.ceil(base_detectors * 1.5)

                manual_call_points = math.ceil(sqm / 500)
                sounders_flashing = math.ceil(sqm / 400)
                loops = math.ceil(base_detectors / 200)
                panels = math.ceil(loops / 8)

                inputs_summary[t["system_names"]["FAS"]] = pd.DataFrame([
                    {t["col_input_param"]: t["fas_sqm"], t["col_input_val"]: inputs.get('fas_sqm'), t["col_unit"]: t["units"]["m2"]},
                    {t["col_input_param"]: t["fas_rf"], t["col_input_val"]: t["units"]["yes"] if inputs.get('fas_raised_floor') else t["units"]["no"], t["col_unit"]: t["units"]["none"]},
                    {t["col_input_param"]: t["fas_beam"], t["col_input_val"]: inputs.get('fas_beam_detectors'), t["col_unit"]: t["units"]["pair"]},
                    {t["col_input_param"]: t["redundancy_label"], t["col_input_val"]: f"%{red_pct}", t["col_unit"]: "%"}
                ])

                items_data = [
                    (t["fas_out"]["detectors"], base_detectors, t["units"]["pcs"]),
                    (t["fas_out"]["beam"], inputs.get('fas_beam_detectors', 6), t["units"]["pair"]),
                    (t["fas_out"]["buttons"], manual_call_points, t["units"]["pcs"]),
                    (t["fas_out"]["sounders"], sounders_flashing, t["units"]["pcs"]),
                    (t["fas_out"]["loops"], loops, t["units"]["loop"]),
                    (t["fas_out"]["panels"], panels, t["units"]["pcs"])
                ]

                calculated_results[t["system_names"]["FAS"]] = create_output_df(items_data, red_pct, t)

            # 4. PA/VA HESAPLAMA
            elif t["system_names"]["PA/VA"] in sys:
                red_pct = inputs.get('pava_redundancy', 0)
                sqm = inputs.get('pava_sqm', 75000)
                speakers = math.ceil(sqm / 50)
                watts_per_spk = 6 if inputs.get('pava_environment') == t["pava_env_noisy"] else 3
                total_power_watts = math.ceil(speakers * watts_per_spk * 1.25)
                amplifiers = math.ceil(total_power_watts / 1000)

                inputs_summary[t["system_names"]["PA/VA"]] = pd.DataFrame([
                    {t["col_input_param"]: t["pava_sqm"], t["col_input_val"]: inputs.get('pava_sqm'), t["col_unit"]: t["units"]["m2"]},
                    {t["col_input_param"]: t["pava_zones"], t["col_input_val"]: inputs.get('pava_zones'), t["col_unit"]: t["units"]["zone"]},
                    {t["col_input_param"]: t["pava_env"], t["col_input_val"]: inputs.get('pava_environment'), t["col_unit"]: t["units"]["none"]},
                    {t["col_input_param"]: t["redundancy_label"], t["col_input_val"]: f"%{red_pct}", t["col_unit"]: "%"}
                ])

                items_data = [
                    (t["pava_out"]["speakers"], speakers, t["units"]["pcs"]),
                    (t["pava_out"]["power"], total_power_watts, t["units"]["watt"]),
                    (t["pava_out"]["amps"], amplifiers, t["units"]["pcs"]),
                    (t["pava_out"]["zones"], inputs.get('pava_zones', 16), t["units"]["zone"])
                ]

                calculated_results[t["system_names"]["PA/VA"]] = create_output_df(items_data, red_pct, t)

        # --- EKRANDA SONUÇLARI GÖSTERME ---
        st.success(t["report_success"].format(project=display_proj_name))

        res_tabs = st.tabs(list(calculated_results.keys()))
        for idx, sys_key in enumerate(calculated_results.keys()):
            with res_tabs[idx]:
                col_in, col_out = st.columns([1, 1.5])
                with col_in:
                    st.markdown(f"#### {t['inputs_header']}")
                    st.dataframe(inputs_summary[sys_key], use_container_width=True, hide_index=True)
                with col_out:
                    st.markdown(f"#### {t['outputs_header']}")
                    st.dataframe(calculated_results[sys_key], use_container_width=True, hide_index=True)

        # --- İNDİRME ALANI (PDF & EXCEL) ---
        st.markdown("---")
        st.subheader(t["download_section"])

        pdf_bytes = generate_pdf(
            project_name=display_proj_name,
            country=selected_country,
            city=selected_city,
            results=calculated_results,
            inputs_summary=inputs_summary,
            report_datetime_str=now_str,
            t_labels=t
        )

        excel_bytes = generate_excel(
            results=calculated_results,
            inputs_summary=inputs_summary,
            t_labels=t
        )

        file_prefix = display_proj_name.replace(' ', '_')
        pdf_filename = f"{file_prefix}_Report.pdf"
        excel_filename = f"{file_prefix}_Report.xlsx"

        col_pdf, col_excel = st.columns(2)
        with col_pdf:
            st.download_button(
                label=t["download_pdf_btn"],
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        with col_excel:
            st.download_button(
                label=t["download_excel_btn"],
                data=excel_bytes,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
