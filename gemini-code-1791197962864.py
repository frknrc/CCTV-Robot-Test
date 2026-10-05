import streamlit as st
import math
import pandas as pd
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- PDF KÜTÜPHANESİ (ReportLab) ---
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
        
        # Form İçi Değişkenlerin Başlangıç Değerleri
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

                elif "FAS" in sys:
                    st.markdown("### 🚨 Yangın Algılama ve İhbar Sistemi (FAS)")
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        fas_sqm = st.number_input("Yangın Algılama Yapılacak Kapalı Alan (m²)", min_value=1000, value=75000, step=5000, key="f_sqm")
                        fas_raised_floor = st.checkbox("Asma Tavan ve Yükseltilmiş Taban İçi Dedektörler Dahil Edilsin", value=True, key="f_rf")
                    with fc2:
                        fas_beam_detectors = st.number_input("Yüksek Tavan / Hangar İçin Işın (Beam) Dedektör Çifti Sayısı", min_value=0, value=6, key="f_beam")

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
                
                # --- CCTV ---
                if "CCTV" in sys:
                    sqm_per_cam = 60 if "Uluslararası" in cctv_airport_type else 90
                    fence_m_per_cam = 40 if "Uluslararası" in cctv_airport_type else 60
                    cam_per_check = 3 if "Uluslararası" in cctv_airport_type else 2

                    terminal_cams = math.ceil(cctv_sqm / sqm_per_cam)
                    checkpoint_cams = cctv_checkpoints * cam_per_check
                    fence_cams = math.ceil(cctv_fence_m / fence_m_per_cam)
                    anpr_cams = (cctv_lanes * 2) if cctv_use_anpr else 0

                    fence_thermal = math.ceil(fence_cams * 0.15)
                    fence_fixed = fence_cams - fence_thermal
                    total_cams = terminal_cams + checkpoint_cams + fence_cams + anpr_cams

                    tb_per_cam_day = 0.02 if "4MP" in cctv_resolution else (0.015 if "2MP" in cctv_resolution else 0.035)
                    total_storage_tb = math.ceil(total_cams * tb_per_cam_day * cctv_storage_days)
                    recording_servers = math.ceil(total_cams / 64)
                    failover_servers = math.ceil(recording_servers / 8)
                    video_wall_monitors = cctv_operators * 2 + (cctv_control_rooms * 2)

                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("Toplam CCTV Kamera", f"{total_cams:,} Adet")
                    col_m2.metric("Net Depolama", f"{total_storage_tb:,} TB")
                    col_m3.metric("Kayıt Sunucusu (64Ch)", f"{recording_servers + failover_servers} Adet")
                    col_m4.metric("Video Wall (55\")", f"{video_wall_monitors} Adet")

                    st.dataframe(pd.DataFrame({
                        "Ekipman Tanımı": ["Terminal İçi Sabit Kamera", "Pasaport/Güvenlik (FR) Kamera", "Çevre Çit Sabit Kamera", "Çevre Çit Termal/PTZ", "ANPR Plaka Kamera", "64Ch Kayıt Sunucusu", "Video Wall Monitör"],
                        "Miktar": [terminal_cams, checkpoint_cams, fence_fixed, fence_thermal, anpr_cams, recording_servers + failover_servers, video_wall_monitors],
                        "Birim": ["Adet", "Adet", "Adet", "Adet", "Adet", "Adet", "Adet"]
                    }), use_container_width=True)

                    excel_rows.extend([
                        {"Sistem": "CCTV", "Bileşen / Tanım": "Terminal Sabit Kamera", "Değer / Miktar": terminal_cams, "Birim": "Adet"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "Pasaport/FR Kamera", "Değer / Miktar": checkpoint_cams, "Birim": "Adet"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "Çevre Çit Sabit Kamera", "Değer / Miktar": fence_fixed, "Birim": "Adet"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "Çevre Çit Termal/PTZ", "Değer / Miktar": fence_thermal, "Birim": "Adet"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "ANPR Plaka Kamera", "Değer / Miktar": anpr_cams, "Birim": "Adet"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "TOPLAM KAMERA", "Değer / Miktar": total_cams, "Birim": "Adet"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "Net Depolama Alanı", "Değer / Miktar": total_storage_tb, "Birim": "TB"},
                        {"Sistem": "CCTV", "Bileşen / Tanım": "Kayıt Sunucuları (N+1)", "Değer / Miktar": recording_servers + failover_servers, "Birim": "Adet"},
                    ])

                # --- ACS ---
                elif "ACS" in sys:
                    total_doors = acs_single_doors + acs_double_doors
                    total_biometric = acs_face_rec_qty + acs_fingerprint_qty

                    biometric_doors = min(total_biometric, total_doors)
                    standard_doors = max(0, total_doors - biometric_doors)

                    card_readers = standard_doors * 2
                    exit_buttons = biometric_doors
                    door_controllers = math.ceil(total_doors / 4) if total_doors > 0 else 0
                    turnstile_readers = acs_turnstiles * 2

                    locks = (acs_single_doors * 1) + (acs_double_doors * 2)
                    magnetic_contacts = (acs_single_doors * 1) + (acs_double_doors * 2)

                    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                    col_a1.metric("Toplam Kontrollü Kapı", f"{total_doors} Adet")
                    col_a2.metric("RFID Okuyucu", f"{card_readers} Adet")
                    col_a3.metric("Biyometrik Terminal", f"{total_biometric} Adet")
                    col_a4.metric("Çıkış Butonu", f"{exit_buttons} Adet")

                    st.dataframe(pd.DataFrame({
                        "Ekipman / Modül Tanımı": [
                            "Tek Kanat Kontrollü Kapı",
                            "Çift Kanat Kontrollü Kapı",
                            "Kapı Kart Okuyucu (RFID)",
                            "Yüz Tanıma Terminali",
                            "Parmak İzi Okuyucu",
                            "Kapı Çıkış Butonu (Biyometrik Kapılar İçin)",
                            "Turnike Kart Okuyucu",
                            "4 Kapılı Kapı Kontrol Paneli",
                            "Manyetik Kontak (MC)",
                            "Elektromanyetik Kilit / Kilit Karşılığı",
                            "Proximity Kullanıcı Kartı (+%20 Yedek)"
                        ],
                        "Miktar": [
                            acs_single_doors,
                            acs_double_doors,
                            card_readers,
                            acs_face_rec_qty,
                            acs_fingerprint_qty,
                            exit_buttons,
                            turnstile_readers,
                            door_controllers,
                            magnetic_contacts,
                            locks,
                            math.ceil(acs_users * 1.2)
                        ],
                        "Birim": ["Adet", "Adet", "Adet", "Adet", "Adet", "Adet", "Adet", "Adet", "Adet", "Adet", "Adet"]
                    }), use_container_width=True)

                    excel_rows.extend([
                        {"Sistem": "ACS", "Bileşen / Tanım": "Tek Kanat Kontrollü Kapı Sayısı", "Değer / Miktar": acs_single_doors, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Çift Kanat Kontrollü Kapı Sayısı", "Değer / Miktar": acs_double_doors, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Toplam Kapı Sayısı", "Değer / Miktar": total_doors, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Kapı Kart Okuyucu (RFID)", "Değer / Miktar": card_readers, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Yüz Tanıma Terminali", "Değer / Miktar": acs_face_rec_qty, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Parmak İzi Okuyucu", "Değer / Miktar": acs_fingerprint_qty, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Çıkış Butonu (Biyometrik Kapılar)", "Değer / Miktar": exit_buttons, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Turnike Kart Okuyucu", "Değer / Miktar": turnstile_readers, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "4-Kapı Kontrol Paneli", "Değer / Miktar": door_controllers, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Manyetik Kontak (MC)", "Değer / Miktar": magnetic_contacts, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Elektromanyetik Kilit", "Değer / Miktar": locks, "Birim": "Adet"},
                        {"Sistem": "ACS", "Bileşen / Tanım": "Basılacak Kart Miktarı", "Değer / Miktar": math.ceil(acs_users * 1.2), "Birim": "Adet"},
                    ])

                # --- FAS ---
                elif "FAS" in sys:
                    sqm_per_detector = 50 if fas_raised_floor else 70
                    detectors = math.ceil(fas_sqm / sqm_per_detector)
                    manual_call_points = math.ceil(fas_sqm / 500)
                    sirens = math.ceil(fas_sqm / 400)
                    loops = math.ceil(detectors / 200)
                    panels = math.ceil(loops / 8)

                    col_f1, col_f2, col_f3 = st.columns(3)
                    col_f1.metric("Optik Duman/Sıcaklık Dedektörü", f"{detectors:,} Adet")
                    col_f2.metric("Yangın İhbar Butonu & Siren", f"{manual_call_points + sirens:,} Adet")
                    col_f3.metric("8-Loop Yangın Santrali", f"{panels} Adet")

                    st.dataframe(pd.DataFrame({
                        "Ekipman Tanımı": ["Adresli Optik Duman Dedektörü", "Yangın İhbar Butonu", "Flaşörlü Siren / Flaşör", "Işın (Beam) Dedektörü", "8-Loop Yangın Algılama Santrali"],
                        "Miktar": [detectors, manual_call_points, sirens, fas_beam_detectors, panels],
                        "Birim": ["Adet", "Adet", "Adet", "Çift", "Adet"]
                    }), use_container_width=True)

                    excel_rows.extend([
                        {"Sistem": "FAS", "Bileşen / Tanım": "Adresli Optik Duman Dedektörü", "Değer / Miktar": detectors, "Birim": "Adet"},
                        {"Sistem": "FAS", "Bileşen / Tanım": "Yangın İhbar Butonu", "Değer / Miktar": manual_call_points, "Birim": "Adet"},
                        {"Sistem": "FAS", "Bileşen / Tanım": "Flaşörlü Siren", "Değer / Miktar": sirens, "Birim": "Adet"},
                        {"Sistem": "FAS", "Bileşen / Tanım": "Işın (Beam) Dedektörü", "Değer / Miktar": fas_beam_detectors, "Birim": "Çift"},
                        {"Sistem": "FAS", "Bileşen / Tanım": "8-Loop Yangın Santrali", "Değer / Miktar": panels, "Birim": "Adet"},
                    ])

                # --- PA/VA ---
                elif "PA/VA" in sys:
                    spk_sqm = 50 if "Gürültülü" in pava_environment else 80
                    ceiling_speakers = math.ceil(pava_sqm / spk_sqm)
                    horn_speakers = math.ceil(pava_sqm / 300) if "Gürültülü" in pava_environment else 0
                    total_watt = (ceiling_speakers * 6) + (horn_speakers * 15)
                    amplifiers = math.ceil(total_watt / 500)

                    col_p1, col_p2, col_p3 = st.columns(3)
                    col_p1.metric("Tavan Hoparlörü", f"{ceiling_speakers:,} Adet")
                    col_p2.metric("Toplam Güç İhtiyacı", f"{total_watt:,} Watt")
                    col_p3.metric("500W Amplifikatör Ünitesi", f"{amplifiers} Adet")

                    st.dataframe(pd.DataFrame({
                        "Ekipman Tanımı": ["Tavan Tipi Anons Hoparlörü (6W)", "Korna/Horn Hoparlör (15W)", "Sistem Bölge (Zone) Sayısı", "500W Güç Amplifikatörü", "Anons Mikrofon İstasyonu"],
                        "Miktar": [ceiling_speakers, horn_speakers, pava_zones, amplifiers, math.ceil(pava_zones / 4)],
                        "Birim": ["Adet", "Adet", "Zone", "Adet", "Adet"]
                    }), use_container_width=True)

                    excel_rows.extend([
                        {"Sistem": "PA/VA", "Bileşen / Tanım": "Tavan Hoparlörü (6W)", "Değer / Miktar": ceiling_speakers, "Birim": "Adet"},
                        {"Sistem": "PA/VA", "Bileşen / Tanım": "Korna Hoparlör (15W)", "Değer / Miktar": horn_speakers, "Birim": "Adet"},
                        {"Sistem": "PA/VA", "Bileşen / Tanım": "Anons Bölgesi (Zone)", "Değer / Miktar": pava_zones, "Birim": "Zone"},
                        {"Sistem": "PA/VA", "Bileşen / Tanım": "Anons Amplifikatörü (500W)", "Değer / Miktar": amplifiers, "Birim": "Adet"},
                    ])

        # --- RAPOR İNDİRME SEÇENEKLERİ (EXCEL & PDF) ---
        st.markdown("---")
        st.subheader("📥 Rapor Çıktısı Alın")

        file_clean_name = project_name.replace(' ', '_')

        col_ex, col_pdf = st.columns(2)

        # 1. EXCEL DOKÜMANI HAZIRLAMA
        with col_ex:
            output_excel = BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df = pd.DataFrame(excel_rows)
                df.to_excel(writer, index=False, sheet_name='Zayif_Akim_Tasarim_Raporu', startrow=4)
                
                workbook = writer.book
                worksheet = writer.sheets['Zayif_Akim_Tasarim_Raporu']

                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                font_title = Font(name="Calibri", size=16, bold=True, color="1F4E78")
                font_subtitle = Font(name="Calibri", size=10, italic=True, color="595959")
                font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                font_data = Font(name="Calibri", size=11)

                thin_border = Border(
                    left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                    top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
                )

                worksheet['A1'] = "ZAYIF AKIM SİSTEMLERİ ÖN TASARIM VE İHTİYAÇ RAPORU"
                worksheet['A1'].font = font_title
                worksheet['A2'] = "Proje: " + str(project_name) + " | Tarih: " + str(now_str)
                worksheet['A2'].font = font_subtitle

                for col_num in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=5, column=col_num)
                    cell.fill = header_fill
                    cell.font = font_header
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                for row_num in range(6, len(df) + 6):
                    for col_num in range(1, len(df.columns) + 1):
                        cell = worksheet.cell(row=row_num, column=col_num)
                        cell.font = font_data
                        cell.border = thin_border
                        cell.alignment = Alignment(horizontal="center" if col_num in [3, 4] else "left")

                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = get_column_letter(col[0].column)
                    worksheet.column_dimensions[col_letter].width = max(max_len + 5, 12)

            st.download_button(
                label="📊 Excel (.xlsx) Formatında İndir",
                data=output_excel.getvalue(),
                file_name=f"{file_clean_name}_Raporu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # 2. PDF DOKÜMANI HAZIRLAMA (ReportLab)
        with col_pdf:
            def generate_pdf(rows, proj_title, date_str):
                pdf_buffer = BytesIO()
                doc = SimpleDocTemplate(
                    pdf_buffer,
                    pagesize=A4,
                    rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
                )
                elements = []
                styles = getSampleStyleSheet()

                title_style = ParagraphStyle(
                    'DocTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    leading=20,
                    textColor=colors.HexColor('#1F4E78'),
                    spaceAfter=6
                )
                subtitle_style = ParagraphStyle(
                    'DocSubTitle',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#595959'),
                    spaceAfter=15
                )

                elements.append(Paragraph("ZAYIF AKIM SİSTEMLERİ İHTİYAÇ RAPORU", title_style))
                elements.append(Paragraph(f"Proje: {proj_title} | Tarih: {date_str}", subtitle_style))
                elements.append(Spacer(1, 10))

                # Tablo Verisi Hazırlığı
                table_data = [["Sistem", "Bilesen / Tanim", "Miktar", "Birim"]]
                for row in rows:
                    table_data.append([
                        str(row["Sistem"]),
                        str(row["Bileşen / Tanım"]),
                        str(row["Değer / Miktar"]),
                        str(row["Birim"])
                    ])

                pdf_table = Table(table_data, colWidths=[80, 260, 100, 80])
                pdf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (3, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9D9D9')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
                ]))

                elements.append(pdf_table)
                doc.build(elements)
                pdf_buffer.seek(0)
                return pdf_buffer.getvalue()

            pdf_bytes = generate_pdf(excel_rows, project_name, now_str)

            st.download_button(
                label="📄 PDF (.pdf) Formatında İndir",
                data=pdf_bytes,
                file_name=f"{file_clean_name}_Raporu.pdf",
                mime="application/pdf",
                use_container_width=True
            )
