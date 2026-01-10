import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Konfigurasi Halaman agar terlihat modern
st.set_page_config(page_title="SPK Supplier Makan Gratis", layout="wide")

def hitung_bobot_ahp():
    # Kriteria: Harga, Kualitas, Waktu_Kirim, Pelayanan
    kriteria = ['Harga', 'Kualitas', 'Waktu_Kirim', 'Pelayanan']
    matriks = np.array([
        [1,    0.33, 2,   3],    # Harga
        [3,    1,    4,   5],    # Kualitas (Prioritas Utama)
        [0.5,  0.25, 1,   2],    # Waktu Kirim
        [0.33, 0.2,  0.5, 1]     # Pelayanan
    ])
    
    col_sums = matriks.sum(axis=0)
    norm_matriks = matriks / col_sums
    weights = norm_matriks.mean(axis=1)
    
    # Hitung Rasio Konsistensi (CR)
    n = len(kriteria)
    ri = {1: 0, 2: 0, 3: 0.58, 4: 0.9}
    lamda_max = sum(col_sums * weights)
    ci = (lamda_max - n) / (n - 1)
    cr = ci / ri[n]
    
    return weights, cr

# --- JUDUL APLIKASI ---
st.title("🍱 Sistem Keputusan Supplier Makan Gratis")
st.markdown("### Lokasi: Setu, Tangerang Selatan")
st.info("Sistem ini menghitung secara otomatis menggunakan metode AHP berdasarkan bobot kriteria yang telah ditentukan.")

# --- INISIALISASI DATA SESSION ---
if 'data_sp' not in st.session_state:
    # Data Dummy Awal
    st.session_state.data_sp = pd.DataFrame([
        ["Supplier Setu Jaya", 15000, "Segar", 15, 8],
        ["Katering Serpong Sehat", 18000, "Segar", 25, 9],
        ["Warung Berkah", 13000, "Cukup Segar", 20, 7]
    ], columns=['Nama', 'Harga', 'Kualitas', 'Waktu_Kirim', 'Pelayanan'])

# --- SIDEBAR: INPUT DATA ---
st.sidebar.header("📝 Tambah Supplier Baru")
with st.sidebar.form("form_supplier", clear_on_submit=True):
    nama = st.text_input("Nama Supplier")
    harga = st.number_input("Harga per Porsi (Rp)", min_value=0, step=500)
    kualitas = st.selectbox("Kualitas Bahan", ["Segar", "Cukup Segar", "Tidak Segar"])
    waktu = st.number_input("Waktu Kirim (Menit)", min_value=0)
    pelayanan = st.slider("Skala Pelayanan", 1, 10, 5)
    
    submitted = st.form_submit_button("Tambah ke Tabel")
    if submitted and nama:
        new_row = pd.DataFrame([[nama, harga, kualitas, waktu, pelayanan]], 
                               columns=['Nama', 'Harga', 'Kualitas', 'Waktu_Kirim', 'Pelayanan'])
        st.session_state.data_sp = pd.concat([st.session_state.data_sp, new_row], ignore_index=True)
        st.success(f"{nama} berhasil ditambah!")

# --- HALAMAN UTAMA: TABEL & HAPUS DATA ---
st.write("### 📊 Daftar Supplier Saat Ini")
data_tabel = st.session_state.data_sp.copy()

# Tampilkan tabel dengan checkbox untuk hapus
if not data_tabel.empty:
    st.dataframe(data_tabel, use_container_width=True)
    
    # Fitur Hapus Data
    with st.expander("🗑️ Pengaturan: Hapus Data Supplier"):
        list_nama = data_tabel['Nama'].tolist()
        hapus_nama = st.multiselect("Pilih supplier yang ingin dihapus:", list_nama)
        if st.button("Hapus Supplier Terpilih"):
            st.session_state.data_sp = st.session_state.data_sp[~st.session_state.data_sp['Nama'].isin(hapus_nama)]
            st.rerun()
else:
    st.warning("Belum ada data supplier. Silakan tambah melalui sidebar.")

st.markdown("---")

# --- PROSES PERHITUNGAN ---
if st.button("🚀 Klik untuk Hitung AHP & Tampilkan Keputusan"):
    if len(st.session_state.data_sp) < 2:
        st.error("Tambahkan minimal 2 supplier untuk melakukan perbandingan!")
    else:
        df = st.session_state.data_sp.copy()
        weights, cr = hitung_bobot_ahp()
        
        # Normalisasi Internal
        df_norm = df.copy()
        kual_map = {"Segar": 3, "Cukup Segar": 2, "Tidak Segar": 1}
        df_norm['Kual_Num'] = df['Kualitas'].map(kual_map)
        
        # Hitung Normalisasi (Cost vs Benefit)
        df_norm['Harga_N'] = df['Harga'].min() / df['Harga']
        df_norm['Waktu_N'] = df['Waktu_Kirim'].min() / df['Waktu_Kirim']
        df_norm['Kual_N'] = df_norm['Kual_Num'] / 3
        df_norm['Pel_N'] = df['Pelayanan'] / 10
        
        # Hitung Skor Akhir
        df['Skor_Akhir'] = (df_norm['Harga_N'] * weights[0] + 
                            df_norm['Kual_N'] * weights[1] + 
                            df_norm['Waktu_N'] * weights[2] + 
                            df_norm['Pel_N'] * weights[3])
        
        df_final = df.sort_values(by='Skor_Akhir', ascending=False)
        
        # --- TAMPILAN HASIL ---
        st.balloons()
        st.success(f"Analisis Berhasil! (Consistency Ratio: {cr:.4f})")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("#### 🏆 Peringkat Rekomendasi")
            # Menandai yang terbaik
            st.dataframe(df_final[['Nama', 'Skor_Akhir']].style.highlight_max(axis=0, color='#d4edda'), use_container_width=True)
            
            # Download CSV
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Hasil sebagai CSV", csv, "hasil_spk_setu.csv", "text/csv")

        with col2:
            st.write("#### 📈 Visualisasi Perbandingan")
            fig, ax = plt.subplots()
            colors = ['#28a745' if x == df_final['Skor_Akhir'].max() else '#007bff' for x in df_final['Skor_Akhir']]
            ax.bar(df_final['Nama'], df_final['Skor_Akhir'], color=colors)
            ax.set_ylabel("Skor AHP")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        st.markdown(f"**Kesimpulan:** Berdasarkan perhitungan AHP, **{df_final.iloc[0]['Nama']}** adalah pilihan terbaik untuk Program Makan Gratis di wilayah Setu.")