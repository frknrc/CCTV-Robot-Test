import streamlit as st
import math

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="CCTV Ön Tasarım Asistanı",
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
# Aşağıdaki tırnak içine kendi logonuzun internet linkini yapıştırabilirsiniz.
logo_url = "https://via.placeholder.com/200x60.png?text=SIRKET+LOGOSU" 

col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image(logo_url, width=180)
with col_title:
    st.title("Havalimanı CCTV & Güvenlik Ön Tasarım Sihirbazı")
    st.caption("Lütfen projenize ait verileri sırasıyla doldurarak ön tasarım raporunu oluşturun.")

st.markdown("---")

# --- MÜŞTERİNİN KARŞISINA ÇIKACAK ADIM ADIM FORM ---
with st.form("cctv_formu"):
    
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
    # Form Gönderme Butonu
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
    st.success("✅ Projenize Özel Ön Tasarım Başarıyla Oluşturuldu!")
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
