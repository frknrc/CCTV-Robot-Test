import streamlit as st
import math
import pandas as pd
import io
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
        "pava_title":
