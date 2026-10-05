import streamlit as st
import math
import pandas as pd
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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

# --- ŞİRKET LOGOSU VE BAŞLIK ---
logo_url = "https://cdn.tav.aero/corporate/TavTechWebsite/tav_renkli_e470511c30.svg" 

col_logo, col_title = st.columns([1.5, 3.5])
with col_logo:
    st.image(logo_url, width=320)
with col_title:
    st.title("Zayıf Akım Sistem Planlama Sihirbazı")
    st.caption("Lütfen projenize ait verileri girerek donanım ve altyapı ihtiyaç raporunu oluşturun.")

st.markdown("---")

# --- PROJE BİLGİSİ VE SİSTEM SEÇİMİ ---
project_name = st.text_input("📌 Havalimanı / Proje Adı", value="Örnek Havalimanı Terminal Projesi")

st.subheader("🎯 Planlanacak Zayıf Akım Sistemlerini Seçiniz")
selected_systems = st.multiselect(
    "İhtiyaç duyulan sistemleri işaretleyiniz:",
    ["CCTV (Kamera Güvenlik)", "ACS (Kartlı Geçiş & Turnike)", "FAS (Yangın Algılama)", "PA/VA (Anons & Seslendirme)"],
    default=["CCTV (Kamera Güvenlik)", "ACS (Kartlı Geçiş & Turnike)"]
)

st.markdown("---")

if not selected_systems:
    st.warning("⚠️ Lütfen devam etmek için en az bir zayıf akım sistemi seçiniz.")
else:
    with st.form("main_system_form"):
        system_tabs = st.tabs(selected_systems)
        
        # Soru Değişkenleri Tanımları
        cctv_airport_type = "Uluslararası Transit Hub (Yüksek Güvenlik / Yoğun Yolcu)"
        cctv_sqm = 75000
        cctv_checkpoints = 20
        cctv_fence_m = 8000
        cctv_use_anpr = False
        cctv_lanes = 0
        cctv_anpr_speed = "Düşük Hız (Nizamiye / Otopark Bariyer)"
        cctv_control_rooms = 1
        cctv_operators = 6
        cctv_remote_views = 4
        cctv_storage_days = 60
        cctv_resolution = "4MP (Önerilen / Optimal)"

        acs_single_doors = 80
        acs_double_doors = 20
        acs_turnstiles = 12
        acs_users = 2500
        acs_face_rec_qty = 10
        acs_fingerprint_qty = 15

        fas_sqm = 75000
        fas_raised_floor = True
        fas_beam_detectors = 4

        pava_zones = 16
        pava_sqm = 75000
        pava_environment = "Standart Terminal Alanı (70-75 dB)"

        for i, sys in enumerate(selected_systems):
            with system_tabs[i]:
                # --- 1. CCTV SİSTEMİ ---
                if "CCTV" in sys:
                    st.markdown("### 🎥 CCTV Kamera Güvenlik Sistemi")
                    cctv_airport_type = st.radio(
                        "Havalimanı Kapsamı:",
                        ["Uluslararası Transit Hub (Yüksek Güvenlik / Yoğun Yolcu)", "Bölgesel / Orta Ölçekli Havalimanı"],
                        key="cctv_type"
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        cctv_sqm = st.number_input("Terminal Kapalı Alanı (m²)", min_value=1000, value=75000, step=5000, key="c_sqm")
                        cctv_checkpoints = st.number_input("Pasaport & Güvenlik Kontrol Noktası", min_value=1, value=20, key="c_check")
                    with c2:
                        cctv_fence_m = st.number_input("Çevre Çit Uzunluğu (Metre)", min_value=500, value=8000, step=500, key="c_fence")
                        cctv_use_anpr = st.checkbox("Plaka Tanıma Sistemi (ANPR) İstiyorum", value=True, key="c_anpr_chk")

                    if cctv_use_anpr:
                        ca1, ca2 = st.columns(2)
                        with ca1:
                            cctv_lanes = st.number_input("ANPR Giriş/Çıkış Şerit Sayısı", min_value=1, value=8, key="c_lanes")
                        with ca2:
                            cctv_anpr_speed = st.selectbox("Geçiş Hız Tipi", ["Düşük Hız (Nizamiye / Otopark Bariyer)", "Yüksek Hız (Ana Yol / VIP Giriş)"], key="c_speed")

                    c3, c4 = st.columns(2)
                    with c3:
                        cctv_control_rooms = st.number_input("Ana Kontrol Odası Sayısı", min_value=1, value=1, key="c_cr")
                        cctv_operators = st.number_input("Vardiyadaki Aktif Operatör Masa Sayısı", min_value=1, value=6, key="c_op")
                    with c4:
                        cctv_remote_views = st.number_input("Uzak İzleme Noktası Sayısı", min_value=0, value=4, key="c_rem")
                        cctv_storage_days = st.selectbox("Kayıt Saklama Süresi (Gün)", [30, 60, 90, 180], index=1, key="c_days")
                        cctv_resolution = st.selectbox("Kamera Kalite Standardı", ["4MP (Önerilen / Optimal)", "2MP (Full HD - Standart)", "8MP (4K - Yüksek Detay)"], key="c_res")

                # --- 2. ACS SİSTEMİ ---
                elif "ACS" in sys:
                    st.markdown("### 🚪 Kartlı Geçiş ve Turnike Sistemi (ACS)")
                    ac1, ac2 = st.columns(2)
                    with ac1:
                        st.markdown("**Kapı Tip ve Sayıları**")
                        acs_single_doors = st.number_input("Tek Kanat Kontrollü Kapı Sayısı", min_value=0, value=80, step=5, key="a_s_doors")
                        acs_double_doors = st.number_input("Çift Kanat Kontrollü Kapı Sayısı", min_value=0, value=20, step=2, key="a_d_doors")
                        acs_turnstiles = st.number_input("Geçiş Turnikesi Sayısı (Personel / Yolcu)", min_value=0, value=16, step=2, key="a_turn")
                    with ac2:
                        st.markdown("**Kullanıcı ve Biyometrik Seçenekleri**")
                        acs_users = st.number_input("Sisteme Tanımlanacak Toplam Kartlı Kullanıcı Sayısı", min_value=100, value=3000, step=500, key="a_users")
                        acs_face_rec_qty = st.number_input("Yüz Tanıma Terminali Adedi", min_value=0, value=10, step=1, key="a_face_qty")
                        acs_fingerprint_qty = st.number_input("Parmak İzi Okuyucu Adedi", min_value=0, value=15, step=1, key="a_finger_qty")

                # --- 3. FAS SİSTEMİ ---
                elif "FAS" in sys:
                    st.markdown("### 🚨 Yangın Algılama ve İhbar Sistemi (FAS)")
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        fas_sqm = st.number_input("Yangın Algılama Yapılacak Kapalı Alan (m²)", min_value=1000, value=75000, step=5000, key="f_sqm")
                        fas_raised_floor = st.checkbox("Asma Tavan ve Yükseltilmiş Taban İçi Dedektörler Dahil Edilsin", value=True, key="f_rf")
                    with fc2:
                        fas_beam_detectors = st.number_input("Yüksek Tavan / Hangar İçin Işın (Beam) Dedektör Çifti Sayısı", min_value=0, value=6, key="f_beam")

                # --- 4. PA/VA SİSTEMİ ---
                elif "PA/VA" in sys:
                    st.markdown("### 📢 Acil Anons ve Seslendirme Sistemi (PA/VA)")
                    pc1, pc2 = st.columns(2)
                    with pc1:
                        pava_sqm = st.number_input("Anons Yapılacak Toplam Kapalı Alan (m²)", min_value=1000, value=75000, step=5000, key="p_sqm")
                        pava_zones = st.number_input("Bağımsız Anons Bölgesi (Zone) Sayısı", min_value=1, value=16, step=1, key="p_zones")
                    with pc2:
                        pava_environment = st.selectbox("Baskın Ortam Tipi & Gürültü Seviyesi", ["Standart Terminal Alanı (70-75 dB)", "Gürültülü Otopark / Teknik Alan (80-85 dB)", "Sessiz Ofis / Yönetim Alanı (60 dB)"], key="p_env")

        st.markdown("---")
        submit_button = st.form_submit_button("🚀 Tüm Seçili Sistemlerin İhtiyaç Raporunu Oluştur", use_container_width=True)

    # --- HESAPLAMA VE SONUÇ EKRANI ---
    if submit_button:
        st.success(f"✅ **{project_name}** İçin Seçilen Sistem Planlama Raporu Başarıyla Hesaplandı!")
        
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        excel_rows = [
            {"Sistem": "GENEL BİLGİ", "Bileşen / Tanım": "Proje Adı", "Değer / Miktar": project_name, "Birim": "-"},
            {"Sistem": "GENEL BİLGİ", "Bileşen / Tanım": "Oluşturulma Tarihi", "Değer / Miktar": now_str, "Birim": "-"}
        ]

        res_tabs = st.tabs([f"📊 {s}" for s in selected_systems])

        for idx, sys in enumerate(selected_systems):
            with res_tabs[idx]:
                
                # --- 1. CCTV HESAPLAR ---
                if "CCTV" in sys:
                    sqm_per_cam = 60 if "Uluslararası" in cctv_airport_type else 90
                    fence_m_per_cam = 40 if "Uluslararası" in cctv_airport_type else 60
                    cam_per_check = 3 if "Uluslararası" in cctv_airport_type else 2

                    terminal_cams = math.ceil(cctv_sqm / sqm_per_cam)
                    checkpoint_cams = cctv_checkpoints * cam_
