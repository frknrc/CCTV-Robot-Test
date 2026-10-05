import streamlit as st
import math
import pandas as pd
import requests
from datetime import datetime

# --- DİL SEÇİMİ VE ÇEVİRİ SÖZLÜĞÜ (TR / EN / KK) ---
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
        "warning_no_system": "⚠ Жалғастыру үшін set кем дегенде бір әлсіз тоқ жүйесін таңдаңыз.",
        "submit_btn": "🚀 Таңдалған жүйелер бойынша есепті қалыптастыру",
        "report_success": "✅ **{project}** жобасы үшін жоспарлау есебі сәтті есептелді!",
        "download_section": "📥 Есепті жүктеп алу",
        "system_names": {
            "CCTV": "CCTV (Бейнебақылау жүйесі)",
            "ACS": "ACS (Рұқсатты бақылау жүйесі)",
            "FAS": "FAS (Өрт дабылы жүйесі)",
            "PA/VA": "PA/VA (Дауыстық хабарлау жүйесі)"
        }
    }
}

# --- EN ÜSTTE DİL SEÇİM KUTUSU ---
col_lang, col_blank = st.columns([1.5, 3.5])
with col_lang:
    selected_lang = st.selectbox(
        "🌐 Language / Dil / Тіл",
        ["TR", "EN", "KK"],
        format_func=lambda x: {"TR": "🇹🇷 Türkçe", "EN": "🇬🇧 English", "KK": "🇰🇿 Қазақша"}[x],
        index=0
    )

# Seçilen dile göre metinleri getiren nesne
t = TEXTS[selected_lang]

# --- KULLANIM ÖRNEĞİ ---
st.title(t["page_title"])
st.caption(t["caption"])

project_name = st.text_input(t["project_name_label"], value=t["project_name_default"])
