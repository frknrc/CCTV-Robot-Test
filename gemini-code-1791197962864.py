import streamlit as st
import math
import pandas as pd
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="CCTV Sistem Planlama Sihirbazı",
    page_icon="🎥",
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
    st.image(logo_url, width=320)  # Logo boyutu büyütüldü
with col_title:
    st.title("CCTV Sistem Planlama Sihirbazı")
    st.caption("Lütfen projenize ait verileri girerek donanım ve depolama ihtiyaç raporunu oluşturun.")

st.markdown("---")

# --- MÜŞTERİNİN KARŞISINA ÇIKACAK ADIM ADIM FORM ---
with st.form("cctv_formu"):
    
    st.subheader("📌 Proje Kimliği")
    project_name = st.text_input("Havalimanı / Proje Adı", value="Örnek Havalimanı Terminal Projesi", help="Rapor başlığında yer alacaktır.")
    
    st.markdown("---")
    st.subheader("📝 Adım 1: Havalimanı Tipi ve Sınıfı")
    airport_type = st.radio(
        "Havalimanı Kapsamını Seçiniz:",
        ["Uluslararası Transit Hub (Yüksek Güvenlik / Yoğun Yolcu)", "Bölgesel / Orta Ölçekli Havalimanı"]
    )
    
    st.markdown("---")
    st.subheader("📐 Adım 2: Saha Ölçüm Bilgileri")
    col1, col2 = st.columns(2)
    with col1:
        sqm = st.number_input("Terminal Toplam Kapalı Alanı (m²)", min_value=1000, value=75000, step=5000)
        checkpoints = st.number_input("Pasaport & Güvenlik Kontrol Noktası Sayısı", min_value=1, value=20)
    with col2:
        fence_m = st.number_input("Çevre Çit / Dış Sınır Uzunluğu (Metre)", min_value=500, value=8000, step=500)
    
    st.markdown("---")
    st.subheader("⚙️ Adım 3: Kayıt ve Detay Beklentileri")
    col3, col4 = st.columns(2)
    with col3:
        storage_days = st.selectbox("İstenen Geriye Dönük Kayıt Saklama Süresi (Gün)", [30, 60, 90, 180], index=1)
    with col4:
        resolution = st.selectbox("Tercih Edilen Kamera Kalite Standardı", ["4MP (Önerilen / Optimal)", "2MP (Full HD - Standart)", "8MP (4K - Yüksek Detay)"])

    st.markdown("---")
    submit_button = st.form_submit_button("🚀 Tasarımı ve İhtiyaç Raporunu Oluştur", use_container_width=True)

# --- MÜŞTERİ BUTONA BASTIĞINDA ÇIKACAK SONUÇ EKRANI ---
if submit_button:
    # Katsayı Hesaplamaları
    if "Uluslararası" in airport_type:
        sqm_per_cam, fence_m_per_cam, cam_per_check = 60, 40, 3
    else:
        sqm_per_cam, fence_m_per_cam, cam_per_check = 90, 60, 2

    terminal_cams = math.ceil(sqm / sqm_per_cam)
    checkpoint_cams = checkpoints * cam_per_check
    fence_cams = math.ceil(fence_m / fence_m_per_cam)

    fence_thermal_ptz = math.ceil(fence_cams * 0.15)
    fence_fixed = fence_cams - fence_thermal_ptz

    total_cams = terminal_cams + checkpoint_cams + fence_cams

    # Depolama & Sunucu Hesaplama
    tb_per_cam_day = 0.02 if "4MP" in resolution else (0.015 if "2MP" in resolution else 0.035)
    total_storage_tb = math.ceil(total_cams * tb_per_cam_day * storage_days)
    recording_servers = math.ceil(total_cams / 64)
    failover_servers = math.ceil(recording_servers / 8)

    monitors = math.ceil(total_cams / 32)
    workstations = math.ceil(monitors / 4)

    # Sonuçların Gösterilmesi
    st.success(f"✅ **{project_name}** İçin Ön Tasarım Başarıyla Oluşturuldu!")
    st.subheader("📊 Tahmini Donanım & Altyapı İhtiyaç Raporu")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Kamera", f"{total_cams:,} Adet")
    m2.metric("Gerekli Depolama", f"{total_storage_tb:,} TB")
    m3.metric("Kayıt Sunucusu (64Ch)", f"{recording_servers + failover_servers} Adet", delta=f"+{failover_servers} Yedek", delta_color="normal")
    m4.metric("İzleme Ekranı (55\")", f"{monitors} Adet")

    st.markdown("---")

    # Detay Tabloları
    tab1, tab2, tab3 = st.tabs(["📷 Kamera Dağılımı", "💾 Kayıt & Depolama", "🖥️ İzleme Odası"])

    with tab1:
        st.table({
            "Bölge / Ekipman": ["Terminal İçi Sabit Dome/Bullet", "Pasaport/Güvenlik Detay (FR)", "Çevre Çit Sabit Kamera", "Çevre Çit Termal / PTZ"],
            "Tahmini Adet": [terminal_cams, checkpoint_cams, fence_fixed, fence_thermal_ptz],
            "Açıklama": ["Genel alan izleme", "Yüz tanıma & detay takibi", "Sınır hat izleme", "Gece & uzun mesafe algılama"]
        })

    with tab2:
        st.write(f"• **Net Depolama İhtiyacı:** `{total_storage_tb:,} TB` ({storage_days} gün saklama esasına göre)")
        st.write(f"• **Ana Kayıt Sunucusu:** `{recording_servers} Adet` (64 Kanal Kapasiteli)")
        st.write(f"• **Yedek Sunucu (N+1 Failover):** `{failover_servers} Adet` (Kesintisiz çalışma için)")

    with tab3:
        st.write(f"• **Video Wall / İzleme Monitörü:** `{monitors} Adet` 55\" Ekran")
        st.write(f"• **Operatör İş İstasyonu (PC):** `{workstations} Adet` (Çoklu ekran destekli PC)")

    # --- PROFESYONEL EXCEL OLUŞTURMA İŞLEMLERİ ---
    st.markdown("---")
    st.subheader("📥 Kurumsal Rapor İndirme")

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Excel Veri Yapısı
        excel_data = [
            {"Kategori": "PROJE BİLGİSİ", "Bileşen / Tanım": "Proje Adı", "Değer / Miktar": project_name, "Birim": "-"},
            {"Kategori": "PROJE BİLGİSİ", "Bileşen / Tanım": "Havalimanı Tipi", "Değer / Miktar": airport_type, "Birim": "-"},
            {"Kategori": "GİRDİ PARAMETRELERİ", "Bileşen / Tanım": "Terminal Kapalı Alanı", "Değer / Miktar": sqm, "Birim": "m²"},
            {"Kategori": "GİRDİ PARAMETRELERİ", "Bileşen / Tanım": "Çevre Çit Uzunluğu", "Değer / Miktar": fence_m, "Birim": "Metre"},
            {"Kategori": "GİRDİ PARAMETRELERİ", "Bileşen / Tanım": "Güvenlik Kontrol Noktası", "Değer / Miktar": checkpoints, "Birim": "Nokta"},
            {"Kategori": "GİRDİ PARAMETRELERİ", "Bileşen / Tanım": "Kayıt Saklama Süresi", "Değer / Miktar": storage_days, "Birim": "Gün"},
            {"Kategori": "GİRDİ PARAMETRELERİ", "Bileşen / Tanım": "Çözünürlük Standardı", "Değer / Miktar": resolution, "Birim": "-"},
            {"Kategori": "KAMERA DAĞILIMI", "Bileşen / Tanım": "Terminal İçi Sabit Kamera", "Değer / Miktar": terminal_cams, "Birim": "Adet"},
            {"Kategori": "KAMERA DAĞILIMI", "Bileşen / Tanım": "Pasaport / Güvenlik (FR) Kamera", "Değer / Miktar": checkpoint_cams, "Birim": "Adet"},
            {"Kategori": "KAMERA DAĞILIMI", "Bileşen / Tanım": "Çevre Çit Sabit Kamera", "Değer / Miktar": fence_fixed, "Birim": "Adet"},
            {"Kategori": "KAMERA DAĞILIMI", "Bileşen / Tanım": "Çevre Çit Termal / PTZ Kamera", "Değer / Miktar": fence_thermal_ptz, "Birim": "Adet"},
            {"Kategori": "KAMERA DAĞILIMI", "Bileşen / Tanım": "TOPLAM KAMERA İHTİYACI", "Değer / Miktar": total_cams, "Birim": "Adet"},
            {"Kategori": "DEPOLAMA & SUNUCU", "Bileşen / Tanım": "Net Depolama Alanı", "Değer / Miktar": total_storage_tb, "Birim": "TB"},
            {"Kategori": "DEPOLAMA & SUNUCU", "Bileşen / Tanım": "64Ch Kayıt Sunucusu", "Değer / Miktar": recording_servers, "Birim": "Adet"},
            {"Kategori": "DEPOLAMA & SUNUCU", "Bileşen / Tanım": "N+1 Failover Yedek Sunucu", "Değer / Miktar": failover_servers, "Birim": "Adet"},
            {"Kategori": "KONTROL MERKEZİ", "Bileşen / Tanım": "55\" Video Wall Monitör", "Değer / Miktar": monitors, "Birim": "Adet"},
            {"Kategori": "KONTROL MERKEZİ", "Bileşen / Tanım": "Operatör İş İstasyonu (PC)", "Değer / Miktar": workstations, "Birim": "Adet"},
        ]

        df = pd.DataFrame(excel_data)
        df.to_excel(writer, index=False, sheet_name='CCTV_Tasarim_Raporu', startrow=4)
        
        workbook = writer.book
        worksheet = writer.sheets['CCTV_Tasarim_Raporu']

        # STİL VE BİÇİMLENDİRME (OPENPYXL)
        # Renk Paleti (Kurumsal Lacivert & Gri)
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        title_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        
        font_title = Font(name="Calibri", size=16, bold=True, color="1F4E78")
        font_subtitle = Font(name="Calibri", size=10, italic=True, color="595959")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_data = Font(name="Calibri", size=11)
        font_total = Font(name="Calibri", size=11, bold=True, color="1F4E78")

        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        # Başlık Bilgilerini Excel'in En Üstüne Ekleme
        worksheet['A1'] = "CCTV SİSTEMİ ÖN TASARIM VE İHTİYAÇ RAPORU"
        worksheet['A1'].font = font_title
        worksheet['A2'] = f"Proje: {project_name} | Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        worksheet['A2'].font = font_subtitle

        # Tablo Başlıklarını Biçimlendirme (5. Satır)
        for col_num in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=5, column=col_num)
            cell.fill = header_fill
            cell.font = font_header
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Veri Hücrelerini Biçimlendirme
        for row_num in range(6, len(df) + 6):
            for col_num in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=row_num, column=col_num)
                cell.font = font_data
                cell.border = thin_border
                
                # Ortala veya Sağa Hizala
                if col_num in [3, 4]:
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

                # Toplam Kamera satırını koyu yap
                if worksheet.cell(row=row_num, column=2).value == "TOPLAM KAMERA İHTİYACI":
                    cell.font = font_total

        # Otomatik Sütun Genişliği Ayarlama
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            worksheet.column_dimensions[col_letter].width = max(max_len + 5, 12)

    processed_data = output.getvalue()

    # İndirme Butonu
    st.download_button(
        label="📊 Profesyonel İhtiyaç Raporunu Excel (.xlsx) Olarak İndir",
        data=processed_data,
        file_name=f"{project_name.replace(' ', '_')}_CCTV_Raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
