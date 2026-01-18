import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPK Makan Gratis - Setu", layout="wide")

# --- STYLE CSS CUSTOM ---
st.markdown("""
    <style>
    .stApp { background-color: #fdfdfd; }
    .main-header {
        text-align: center; padding: 20px; background: #e8f5e9;
        border-radius: 15px; border-bottom: 5px solid #2E7D32; margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #f1f1f1; border-radius: 10px 10px 0 0;
        padding: 0 20px; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #2E7D32; color: white; }
    .step-box {
        background-color: #ffffff; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #2E7D32;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA AHP ---
def hitung_ahp(matrix):
    n = len(matrix)
    col_sums = matrix.sum(axis=0)
    norm_matriks = matrix / col_sums
    weights = norm_matriks.mean(axis=1)
    lamda_max = sum(col_sums * weights)
    ci = (lamda_max - n) / (n - 1) if n > 1 else 0
    ri = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24}
    cr = ci / ri[n] if n in ri and ri[n] != 0 else 0
    return weights, cr

# --- SESSION STATE INITIALIZATION ---
if 'weights' not in st.session_state: st.session_state.weights = None
if 'list_kriteria' not in st.session_state: st.session_state.list_kriteria = ["Harga", "Kualitas Bahan", "Waktu Kirim", "Pelayanan"]
if 'list_alternatif' not in st.session_state: st.session_state.list_alternatif = ["Supplier A", "Supplier B", "Supplier C"]

# --- NAVIGASI ATAS ---
tab_home, tab_kriteria, tab_alternatif, tab_hasil = st.tabs([
    "Beranda", "Tahap 1: Kriteria & Bobot", "Tahap 2: Input Data", "Tahap 3: Hasil"
])

# --- HALAMAN 1: BERANDA ---
with tab_home:
    st.markdown("<div class='main-header'><h1>Program Makan Siang Gratis <br>Sekolah Kec. Setu, Tangsel</h1></div>", unsafe_allow_html=True)
    col_img, col_txt = st.columns([1, 1])
    with col_img:
        st.image("https://img.freepik.com/free-vector/healthy-food-concept-illustration_114360-1498.jpg", use_container_width=True)
    with col_txt:
        st.markdown("""
        ### Selamat Datang di Sistem Keputusan Supplier
        Gunakan aplikasi ini untuk menentukan vendor terbaik berdasarkan metode **AHP**.
        
        **Langkah Penggunaan:**
        1. Isi Kriteria & Alternatif, lalu tentukan tingkat kepentingan.
        2. Masukkan data real masing-masing supplier.
        3. Lihat hasil perangkingan otomatis.
        """)

# --- HALAMAN 2: TAHAP 1 (KRITERIA & BOBOT) ---
with tab_kriteria:
    st.header("Tahap 1: Konfigurasi Kriteria & Bobot")
    
    # Visual Box untuk Input Dasar
    st.markdown("<div class='step-box'>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        k_input = st.text_area("Daftar Kriteria (Pisahkan dengan koma)", ", ".join(st.session_state.list_kriteria))
    with col_b:
        a_input = st.text_area("Daftar Alternatif/Supplier (Pisahkan dengan koma)", ", ".join(st.session_state.list_alternatif))
    
    if st.button("Simpan Daftar Dasar"):
        st.session_state.list_kriteria = [x.strip() for x in k_input.split(",")]
        st.session_state.list_alternatif = [x.strip() for x in a_input.split(",")]
        st.success("Daftar berhasil diperbarui!")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🔄 Perbandingan Tingkat Kepentingan")
    st.info("Bandingkan setiap kriteria. Semakin tinggi nilai, semakin penting kriteria tersebut.")
    
    list_k = st.session_state.list_kriteria
    n = len(list_k)
    matriks_k = np.eye(n)
    
    # Form Perbandingan Visual
    for i in range(n):
        for j in range(i + 1, n):
            val = st.slider(
                f"Tingkat Kepentingan: **{list_k[i]}** dibanding **{list_k[j]}**", 
                0.1, 9.0, 1.0, 0.5, key=f"k_{i}_{j}"
            )
            matriks_k[i, j] = val
            matriks_k[j, i] = 1 / val
            
    if st.button("Hitung Bobot Kriteria"):
        w, cr = hitung_ahp(matriks_k)
        st.session_state.weights = w
        st.session_state.cr = cr
        st.success(f"Bobot Berhasil Dihitung! Konsistensi (CR): {cr:.4f}")
        st.table(pd.DataFrame({'Kriteria': list_k, 'Bobot': w}))

# --- HALAMAN 3: TAHAP 2 (INPUT DATA ALTERNATIF) ---
with tab_alternatif:
    st.header("Tahap 2: Input Nilai Alternatif")
    if st.session_state.weights is None:
        st.warning("⚠️ Harap selesaikan Tahap 1 (Hitung Bobot Kriteria) terlebih dahulu!")
    else:
        temp_data = []
        for i, alt in enumerate(st.session_state.list_alternatif):
            with st.expander(f"Input Data untuk: {alt}", expanded=True):
                cols = st.columns(len(st.session_state.list_kriteria))
                row_val = []
                for j, k in enumerate(st.session_state.list_kriteria):
                    # Deteksi kriteria untuk label input khusus
                    if "Harga" in k:
                        val = cols[j].number_input(f"Harga (Rp)", min_value=0, key=f"v_{i}_{j}")
                    elif "Kualitas" in k:
                        kual_txt = cols[j].selectbox(f"Kualitas", ["Segar", "Cukup Segar", "Tidak Segar"], key=f"v_{i}_{j}")
                        val = 3 if kual_txt == "Segar" else (2 if kual_txt == "Cukup Segar" else 1)
                    elif "Waktu" in k:
                        val = cols[j].number_input(f"Waktu (Menit)", min_value=0, key=f"v_{i}_{j}")
                    elif "Pelayanan" in k:
                        val = cols[j].number_input(f"Pelayanan (Skala 1-10)", min_value=1, max_value=10, value=5, key=f"v_{i}_{j}")
                    else:
                        val = cols[j].number_input(f"{k}", min_value=0, key=f"v_{i}_{j}")
                    row_val.append(val)
                temp_data.append([alt] + row_val)
        
        if st.button("Simpan & Proses Hasil"):
            st.session_state.raw_matrix = temp_data
            st.success("Data Tersimpan! Buka Tab Hasil untuk melihat ranking.")

# --- HALAMAN 4: TAHAP 3 (HASIL) ---
with tab_hasil:
    st.header("Tahap 3: Hasil Analisis Keputusan")
    if 'raw_matrix' not in st.session_state:
        st.error("Data belum lengkap. Selesaikan tahap sebelumnya.")
    else:
        data = st.session_state.raw_matrix
        names = [r[0] for r in data]
        matrix_x = np.array([r[1:] for r in data], dtype=float)
        
        # 1. MATRIKS KEPUTUSAN AWAL (X)
        st.subheader("1. Matriks Keputusan Awal (X)")
        df_x = pd.DataFrame(matrix_x, columns=st.session_state.list_kriteria, index=names)
        
        # Formating: Harga tetap Rp, sisanya angka bulat
        format_dict = {col: "{:.0f}" for col in df_x.columns}
        if "Harga" in format_dict: format_dict["Harga"] = "Rp {:,.0f}"
        
        st.dataframe(df_x.style.format(format_dict), use_container_width=True)

        # 2. NORMALISASI (R)
        norm_r = np.zeros_like(matrix_x)
        for j, k in enumerate(st.session_state.list_kriteria):
            if "Harga" in k or "Waktu" in k: # Cost
                norm_r[:, j] = matrix_x[:, j].min() / matrix_x[:, j]
            else: # Benefit
                norm_r[:, j] = matrix_x[:, j] / matrix_x[:, j].max()
        
        st.subheader("2. Matriks Ternormalisasi (R)")
        st.dataframe(pd.DataFrame(norm_r, columns=st.session_state.list_kriteria, index=names).style.format("{:.4f}"), use_container_width=True)
        
        # 3. RANKING
        scores = norm_r @ st.session_state.weights
        df_rank = pd.DataFrame({"Supplier": names, "Skor Akhir": scores}).sort_values(by="Skor Akhir", ascending=False)
        df_rank["Ranking"] = range(1, len(df_rank) + 1)
        
        st.subheader("3. Hasil Perangkingan")
        st.success(f"Supplier Rekomendasi: **{df_rank.iloc[0]['Supplier']}**")
        st.dataframe(df_rank[["Ranking", "Supplier", "Skor Akhir"]].style.format({"Skor Akhir": "{:.4f}"}), use_container_width=True)
        
        fig, ax = plt.subplots()
        ax.bar(df_rank['Supplier'], df_rank['Skor Akhir'], color="#648A66")
        st.pyplot(fig)
