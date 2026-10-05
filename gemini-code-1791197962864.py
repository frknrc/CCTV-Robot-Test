import streamlit as st
import math

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Havalimanı CCTV Ön Tasarım Botu",
    page_icon="🎥",
    layout="wide"
)

st.title("🎥 Havalimanı CCTV & Güvenlik Ön Tasarım Botu")
st.caption("Sahalardan gerçek veriler gelene kadar sektör standartı varsayılan katsayılarla çalışan test prototipidir.")
st.markdown("---")

# --- YAN PANEL: MÜŞTERİ GİRDİLERİ ---
st.sidebar.header("📋 Proje Parametreleri")

airport_type = st.sidebar.selectbox(
    "Havalimanı Tipi",
    ["Uluslararası Transit Hub (Yüksek Güvenlik)", "Bölgesel / Orta Ölçekli Havalimanı"]
)

sqm = st.sidebar.number_input("Terminal Kapalı Alanı (m²)", min_value=1000, value=75000, step=5000)
fence_m = st.sidebar.number_input("Çevre Çit / Sınır Uzunluğu (Metre)", min_value=500, value=8000, step=500)
checkpoints = st.sidebar.slider("Pasaport & Güvenlik Noktası Sayısı", min_value=1, max_value=100, value=20)
storage_days = st.sidebar.select_slider("İstenen Kayıt Saklama Süresi (Gün)", options=[30, 60, 90, 180], value=60)

# --- VARSAYILAN KATSAYILAR (TEST VERİLERİ) ---
if "Uluslararası" in airport_type:
    sqm_per_cam = 60      # Her 60 m²'ye 1 kamera
    fence_m_per_cam = 40  # Her 40m'ye 1 çit kamerası
    cam_per_check = 3     # Banko başına 3 kamera
else:
    sqm_per_cam = 90      # Her 90 m²'ye 1 kamera
    fence_m_per_cam = 60  # Her 60m'ye 1 çit kamerası
    cam_per_check = 2     # Banko başına 2 kamera

# --- HESAPLAMA MANTIĞI ---
terminal_cams = math.ceil(sqm / sqm_per_cam)
checkpoint_cams = checkpoints * cam_per_check
fence_cams = math.ceil(fence_m / fence_m_per_cam)

fence_thermal_ptz = math.ceil(fence_cams * 0.15) # %15 Termal/PTZ
fence_fixed = fence_cams - fence_thermal_ptz

total_cams = terminal_cams + checkpoint_cams + fence_cams

# Depolama & Sunucu (4MP H.265+ için ort. 20GB/gün/kamera)
tb_per_cam_day = 0.02
total_storage_tb = math.ceil(total_cams * tb_per_cam_day * storage_days)
recording_servers = math.ceil(total_cams / 64)
failover_servers = math.ceil(recording_servers / 8)

monitors = math.ceil(total_cams / 32)
workstations = math.ceil(monitors / 4)

# --- SONUÇLARIN EKRANA BASILMASI ---
st.subheader("📊 Otomatik Tahmini İhtiyaç Raporu")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Kamera", f"{total_cams:,} Adet")
col2.metric("Gerekli Depolama", f"{total_storage_tb:,} TB")
col3.metric("Kayıt Sunucusu (64Ch)", f"{recording_servers + failover_servers} Adet", delta=f"+{failover_servers} Yedek", delta_color="normal")
col4.metric("İzleme Ekranı (55\")", f"{monitors} Adet")

st.markdown("---")

# DETAYLI TABLOLAR
tab1, tab2, tab3 = st.tabs(["📷 Kamera Dağılımı", "💾 Kayıt & Depolama", "🖥️ İzleme Odası"])

with tab1:
    st.markdown("### Ekipman Dağılım Detayı")
    st.table({
        "Bölge / Ekipman": ["Terminal İçi Sabit Dome/Bullet", "Pasaport/Güvenlik Detay (FR)", "Çevre Çit Sabit Kamera", "Çevre Çit Termal / PTZ"],
        "Tahmini Adet": [terminal_cams, checkpoint_cams, fence_fixed, fence_thermal_ptz],
        "Açıklama": ["Genel alan izleme", "Yüz tanıma & detay takibi", "Sınır hat izleme", "Gece & uzun mesafe algılama"]
    })

with tab2:
    st.markdown("### Sunucu ve Depolama Mimarisi")
    st.write(f"• **Net Depolama İhtiyacı:** `{total_storage_tb:,} TB` ({storage_days} gün saklama esasına göre)")
    st.write(f"• **Ana Kayıt Sunucusu:** `{recording_servers} Adet` (64 Kanal Kapasiteli)")
    st.write(f"• **N+1 Failover Yedek Sunucu:** `{failover_servers} Adet` (Kesintisiz çalışma için)")

with tab3:
    st.markdown("### Kontrol Merkezi İhtiyacı")
    st.write(f"• **Video Wall / İzleme Monitörü:** `{monitors} Adet` 55\" Ekran")
    st.write(f"• **Operatör İş İstasyonu (PC):** `{workstations} Adet` (Çoklu ekran destekli PC)")

st.info("💡 **Bilgi:** Sahalardan gerçek veriler geldikçe kod içerisindeki `sqm_per_cam` ve `fence_m_per_cam` katsayılarını güncelleyerek botun doğruluk oranını artırabilirsiniz.")