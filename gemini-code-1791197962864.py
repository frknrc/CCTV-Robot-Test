import streamlit as st
import math
import pandas as pd
import io
import os
from datetime import datetime
import pytz
from streamlit_javascript import st_javascript

# PDF Oluşturma Kütüphaneleri
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
        "project_name_label": "📌 Havalimanı / Proje Adı (Zorunlu)",
        "project_name_placeholder": "Lütfen proje adını yazınız...",
        "warning_no_project": "🚨 Rapor oluşturabilmek için 'Havalimanı / Proje Adı' alanını doldurmanız zorunludur!",
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
        "project_name_label": "📌 Airport / Project Name (Required)",
        "project_name_placeholder": "Please enter project name...",
        "warning_no_project": "🚨 'Airport / Project Name' is required to generate a report!",
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
        "project_name_label": "📌 Әуежай / Жоба атауы (Міндетті)",
        "project_name_placeholder": "Жоба атауын енгізіңіз...",
        "warning_no_project": "🚨 Есепті қалыптастыру үшін 'Әуежай / Жоба атауы' өрісін толтыру міндетті!",
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

def generate_pdf(project_name, country, city, results, inputs_summary, report_datetime_str, t_labels):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
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

    logo_tav_style = ParagraphStyle(
        'LogoTAV',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=22,
        textColor=colors.white
    )
    logo_sub_style = ParagraphStyle(
        'LogoSub',
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#E2E8F0")
    )

    logo_table_data = [
        [
            Paragraph("<b>TAV</b>", logo_tav_style),
            Paragraph("<b>TECHNOLOGIES</b><br/><font size=5 color='#CBD5E0'>AIRPORTS</font>", logo_sub_style)
        ]
    ]
    logo_table = Table(logo_table_data, colWidths=[55, 90])
    logo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1A365D")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEAFTER', (0, 0), (0, 0), 2, colors.HexColor("#E53E3E")),
    ]))

    story.append(logo_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph(safe_str(t_labels["pdf_title"]), title_style))
    story.append(Paragraph(safe_str(f"<b>Havalimani / Proje Adi:</b> {project_name}"), normal_style))
    story.append(Paragraph(safe_str(f"<b>{t_labels['location_label']}:</b> {country} / {city}"), normal_style))
    story.append(Paragraph(safe_str(f"<b>{t_labels['report_date_label']}:</b> {report_datetime_str}"), normal_style))
    story.append(Spacer(1, 12))

    for sys_key, df_out in results.items():
        story.append(Paragraph(safe_str(f"<b>{sys_key}</b>"), subtitle_style))

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
        # KESİN ZORUNLU KONTROL: Proje adı yazılmadıysa hiçbir şey hesaplama ve indirme butonu koyma
        if not project_name or not project_name.strip():
            st.error(t["warning_no_project"])
        else:
            calculated_results = {}
            inputs_summary = {}

            try:
                if user_timezone_str and isinstance(user_timezone_str, str):
                    user_tz = pytz.timezone(user_timezone_str)
                else:
                    user_tz = pytz.timezone("Europe/Istanbul")
            except Exception:
                user_tz = pytz.timezone("Europe/Istanbul")

            now_str = datetime.now(user_tz).strftime("%d.%m.%Y - %H:%M")

            display_proj_name = project_name.strip()

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
