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

# --- KULLANICININ TARAYICI SAAT DİLİMİNİ OTOMATİK YAKALAMA ---
user_timezone_str = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")

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
        "report_date_label": "Rapor Tarihi",
        "inputs_header": "📋 Girdi Parametreleri (Tasarım Kriterleri)",
        "outputs_header": "📊 Hesaplanan İhtiyaçlar (Sistem Çıktıları)",
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
        "report_date_label": "Report Date",
        "inputs_header": "📋 Input Parameters (Design Criteria)",
        "outputs_header": "📊 Calculated Requirements (System Outputs)",
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
        "report_date_label": "Есеп күні",
        "inputs_header": "📋 Енгізілген параметрлер (Жобалау критерийлері)",
        "outputs_header": "📊 Есептелген қажеттіліктер (Жүйе нәтижелері)",
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

# --- PDF OLUŞTURMA FONKSİYONU ---
def generate_pdf(project_name, results, inputs_summary, report_datetime_str, t_labels):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
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

    story.append(Paragraph(safe_str("Zayıf Akım Sistem Planlama Raporu"), title_style))
    story.append(Paragraph(safe_str(f"<b>Proje Adı:</b> {project_name}"), normal_style))
    story.append(Paragraph(safe_str(f"<b>{t_labels['report_date_label']}:</b> {report_datetime_str}"), normal_style))
    story.append(Spacer(1, 15))

    for sys_key, df_out in results.items():
        story.append(Paragraph(safe_str(f"<b>{sys_key} Metrikleri</b>"), subtitle_style))

        # Girdiler Tablosu
        if sys_key in inputs_summary:
            story.append(Paragraph(safe_str(t_labels['inputs_header']), section_style))
            df_in = inputs_summary[sys_key].copy()
            for col in df_in.columns:
                df_in[col] = df_in[col].apply(safe_str)
            df_in.columns = [safe_str(c) for c in df_in.columns]

            t_in_data = [df_in.columns.tolist()] + df_in.values.tolist()
            t_in = Table(t_in_data, colWidths=[240, 100, 100])
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
        t_out = Table(t_out_data, colWidths=[240, 100, 100])
        t_out.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), font_bold_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_out)
        story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- DİL SEÇİMİ ---
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

        for sys in selected_systems:
            # 1. CCTV HESAPLAMA
            if t["system_names"]["CCTV"] in sys:
                sqm_per_cam = 60 if inputs['cctv_airport_type'] == t["cctv_opt1"] else 90
                fence_m_per_cam = 40 if inputs['cctv_airport_type'] == t["cctv_opt1"] else 60

                indoor_cams = math.ceil(inputs['cctv_sqm'] / sqm_per_cam)
                fence_cams = math.ceil(inputs['cctv_fence_m'] / fence_m_per_cam)
                checkpoint_cams = inputs['cctv_checkpoints'] * 4
                anpr_cams = inputs['cctv_lanes'] * 2 if inputs.get('cctv_use_anpr', False) else 0

                total_cams = indoor_cams + fence_cams + checkpoint_cams + anpr_cams
                
                bitrate_map = {"2MP": 3, "4MP": 5, "8MP": 10}
                mbps_per_cam = bitrate_map.get(inputs['cctv_resolution'], 5)
                storage_tb = math.ceil((total_cams * mbps_per_cam * 3600 * 24 * inputs['cctv_storage_days']) / (8 * 1024 * 1024))

                poe_switches_24p = math.ceil(total_cams / 20)

                inputs_summary['CCTV'] = pd.DataFrame([
                    {"Girdi Parametresi": t["cctv_scope"], "Değer": inputs['cctv_airport_type'], "Birim": "-"},
                    {"Girdi Parametresi": t["cctv_sqm"], "Değer": inputs['cctv_sqm'], "Birim": "m²"},
                    {"Girdi Parametresi": t["cctv_checkpoints"], "Değer": inputs['cctv_checkpoints'], "Birim": "Nokta"},
                    {"Girdi Parametresi": t["cctv_fence"], "Değer": inputs['cctv_fence_m'], "Birim": "Metre"},
                    {"Girdi Parametresi": t["cctv_lanes"], "Değer": inputs['cctv_lanes'], "Birim": "Şerit"},
                    {"Girdi Parametresi": t["cctv_cr"], "Değer": inputs['cctv_control_rooms'], "Birim": "Adet"},
                    {"Girdi Parametresi": t["cctv_op"], "Değer": inputs['cctv_operators'], "Birim": "Masa"},
                    {"Girdi Parametresi": t["cctv_days"], "Değer": inputs['cctv_storage_days'], "Birim": "Gün"},
                    {"Girdi Parametresi": t["cctv_res"], "Değer": inputs['cctv_resolution'], "Birim": "-"}
                ])

                calculated_results['CCTV'] = pd.DataFrame([
                    {"Bileşen / Metrik": "İç Mekan Kameraları", "Miktar": indoor_cams, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Çevre Güvenlik Kameraları", "Miktar": fence_cams, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Kontrol Noktası Kameraları", "Miktar": checkpoint_cams, "Birim": "Adet"},
                    {"Bileşen / Metrik": "ANPR (Plaka Tanıma) Kameraları", "Miktar": anpr_cams, "Birim": "Adet"},
                    {"Bileşen / Metrik": "TOPLAM KAMERA SAYISI", "Miktar": total_cams, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Gerekli Depolama Alanı (Net)", "Miktar": storage_tb, "Birim": "TB"},
                    {"Bileşen / Metrik": "24-Port PoE Switch İhtiyacı", "Miktar": poe_switches_24p, "Birim": "Adet"},
                    {"Bileşen / Metrik": "VMS Lisans Sayısı", "Miktar": total_cams, "Birim": "Lisans"}
                ])

            # 2. ACS HESAPLAMA
            elif t["system_names"]["ACS"] in sys:
                total_doors = inputs['acs_single_doors'] + inputs['acs_double_doors']
                readers = (inputs['acs_single_doors'] * 2) + (inputs['acs_double_doors'] * 2) + (inputs['acs_turnstiles'] * 2)
                controllers = math.ceil((total_doors + inputs['acs_turnstiles']) / 4)

                inputs_summary['ACS'] = pd.DataFrame([
                    {"Girdi Parametresi": t["acs_s_doors"], "Değer": inputs['acs_single_doors'], "Birim": "Adet"},
                    {"Girdi Parametresi": t["acs_d_doors"], "Değer": inputs['acs_double_doors'], "Birim": "Adet"},
                    {"Girdi Parametresi": t["acs_turnstiles"], "Değer": inputs['acs_turnstiles'], "Birim": "Adet"},
                    {"Girdi Parametresi": t["acs_users"], "Değer": inputs['acs_users'], "Birim": "Kullanıcı"},
                    {"Girdi Parametresi": t["acs_face"], "Değer": inputs['acs_face_rec_qty'], "Birim": "Adet"},
                    {"Girdi Parametresi": t["acs_finger"], "Değer": inputs['acs_fingerprint_qty'], "Birim": "Adet"}
                ])

                calculated_results['ACS'] = pd.DataFrame([
                    {"Bileşen / Metrik": "Kontrollü Kapı Sayısı (Tek + Çift)", "Miktar": total_doors, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Turnikeler", "Miktar": inputs['acs_turnstiles'], "Birim": "Adet"},
                    {"Bileşen / Metrik": "Kart Okuyucular", "Miktar": readers, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Yüz Tanıma Terminalleri", "Miktar": inputs['acs_face_rec_qty'], "Birim": "Adet"},
                    {"Bileşen / Metrik": "Parmak İzi Okuyucular", "Miktar": inputs['acs_fingerprint_qty'], "Birim": "Adet"},
                    {"Bileşen / Metrik": "4-Kapılı Geçiş Kontrol Paneli", "Miktar": controllers, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Tanımlı Kullanıcı Kapasitesi", "Miktar": inputs['acs_users'], "Birim": "Kullanıcı"}
                ])

            # 3. FAS HESAPLAMA
            elif t["system_names"]["FAS"] in sys:
                sqm = inputs['fas_sqm']
                base_detectors = math.ceil(sqm / 60)
                if inputs['fas_raised_floor']:
                    base_detectors = math.ceil(base_detectors * 1.5)

                manual_call_points = math.ceil(sqm / 500)
                sounders_flashing = math.ceil(sqm / 400)
                loops = math.ceil(base_detectors / 200)
                panels = math.ceil(loops / 8)

                inputs_summary['FAS'] = pd.DataFrame([
                    {"Girdi Parametresi": t["fas_sqm"], "Değer": inputs['fas_sqm'], "Birim": "m²"},
                    {"Girdi Parametresi": t["fas_rf"], "Değer": "Evet" if inputs['fas_raised_floor'] else "Hayır", "Birim": "-"},
                    {"Girdi Parametresi": t["fas_beam"], "Değer": inputs['fas_beam_detectors'], "Birim": "Çift"}
                ])

                calculated_results['FAS'] = pd.DataFrame([
                    {"Bileşen / Metrik": "Duman / Sıcaklık Dedektörleri", "Miktar": base_detectors, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Işın (Beam) Dedektör Çifti", "Miktar": inputs['fas_beam_detectors'], "Birim": "Çift"},
                    {"Bileşen / Metrik": "Yangın İhbar Butonları", "Miktar": manual_call_points, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Flaşörlü Sirenler", "Miktar": sounders_flashing, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Toplam Çevrim (Loop) Sayısı", "Miktar": loops, "Birim": "Loop"},
                    {"Bileşen / Metrik": "Yangın Kontrol Paneli (8-Loop)", "Miktar": panels, "Birim": "Adet"}
                ])

            # 4. PA/VA HESAPLAMA
            elif t["system_names"]["PA/VA"] in sys:
                sqm = inputs['pava_sqm']
                speakers = math.ceil(sqm / 50)
                watts_per_spk = 6 if inputs['pava_environment'] == t["pava_env_noisy"] else 3
                total_power_watts = math.ceil(speakers * watts_per_spk * 1.25)
                amplifiers = math.ceil(total_power_watts / 1000)

                inputs_summary['PA/VA'] = pd.DataFrame([
                    {"Girdi Parametresi": t["pava_sqm"], "Değer": inputs['pava_sqm'], "Birim": "m²"},
                    {"Girdi Parametresi": t["pava_zones"], "Değer": inputs['pava_zones'], "Birim": "Zone"},
                    {"Girdi Parametresi": t["pava_env"], "Değer": inputs['pava_environment'], "Birim": "-"}
                ])

                calculated_results['PA/VA'] = pd.DataFrame([
                    {"Bileşen / Metrik": "Tavan / Duvar Tipi Hoparlörler", "Miktar": speakers, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Tahmini Güç İhtiyacı", "Miktar": total_power_watts, "Birim": "Watt"},
                    {"Bileşen / Metrik": "Sistem Anons Bölgesi (Zone)", "Miktar": inputs['pava_zones'], "Birim": "Zone"},
                    {"Bileşen / Metrik": "1000W Güç Anfisi İhtiyacı", "Miktar": amplifiers, "Birim": "Adet"},
                    {"Bileşen / Metrik": "Acil Anons Mikrofon İstasyonu", "Miktar": 2, "Birim": "Adet"}
                ])

        st.session_state['results'] = calculated_results
        st.session_state['inputs_summary'] = inputs_summary
        st.session_state['project_name'] = project_name
        st.session_state['selected_systems'] = selected_systems
        st.session_state['report_datetime'] = now_str

    # --- EKRANA BASMA VE İNDİRME BUTONLARI ---
    if 'results' in st.session_state and st.session_state['results']:
        st.success(t["report_success"].format(project=st.session_state['project_name']))
        st.caption(f"📅 {t['report_date_label']}: {st.session_state['report_datetime']}")

        res_tabs = st.tabs([f"📊 {s}" for s in st.session_state['selected_systems']])

        for idx, sys_name in enumerate(st.session_state['selected_systems']):
            with res_tabs[idx]:
                key_code = "CCTV" if "CCTV" in sys_name else ("ACS" if "ACS" in sys_name else ("FAS" if "FAS" in sys_name else "PA/VA"))
                
                # GİRDİLER TABLOSU
                if 'inputs_summary' in st.session_state and key_code in st.session_state['inputs_summary']:
                    st.markdown(f"#### {t['inputs_header']}")
                    st.dataframe(st.session_state['inputs_summary'][key_code], use_container_width=True, hide_index=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                # ÇIKTILAR TABLOSU
                if key_code in st.session_state['results']:
                    st.markdown(f"#### {t['outputs_header']}")
                    df_out = st.session_state['results'][key_code]
                    st.dataframe(df_out, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader(t["download_section"])

        # EXCEL OLUŞTURMA
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            info_df = pd.DataFrame([
                {"Parametre": t["project_name_label"], "Değer": st.session_state['project_name']},
                {"Parametre": t["report_date_label"], "Değer": st.session_state['report_datetime']}
            ])
            info_df.to_excel(writer, sheet_name="Genel Bilgi", index=False)

            for sys_key, df_res in st.session_state['results'].items():
                start_row = 0
                if sys_key in st.session_state['inputs_summary']:
                    st.session_state['inputs_summary'][sys_key].to_excel(writer, sheet_name=sys_key, startrow=0, index=False)
                    start_row = len(st.session_state['inputs_summary'][sys_key]) + 3
                
                df_res.to_excel(writer, sheet_name=sys_key, startrow=start_row, index=False)

        excel_data = excel_buffer.getvalue()

        # PDF OLUŞTURMA
        pdf_data = generate_pdf(
            st.session_state['project_name'], 
            st.session_state['results'], 
            st.session_state['inputs_summary'],
            st.session_state['report_datetime'],
            t
        )

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📊 Excel Raporu İndir (.xlsx)",
                data=excel_data,
                file_name=f"{st.session_state['project_name']}_Zayif_Akim_Raporu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_dl2:
            st.download_button(
                label="📄 PDF Raporu İndir (.pdf)",
                data=pdf_data,
                file_name=f"{st.session_state['project_name']}_Zayif_Akim_Raporu.pdf",
                mime="application/pdf",
                use_container_width=True
            )
