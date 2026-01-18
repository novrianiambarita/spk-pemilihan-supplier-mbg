import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import json

# --- 1. INISIALISASI DATABASE (SQLite) ---
def init_db():
    conn = sqlite3.connect('spk_ahp.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_keputusan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pemenang TEXT,
            skor REAL,
            kriteria TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def simpan_hasil(pemenang, skor, kriteria):
    conn = sqlite3.connect('spk_ahp.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO riwayat_keputusan (pemenang, skor, kriteria)
        VALUES (?, ?, ?)
    ''', (pemenang, skor, ", ".join(kriteria)))
    conn.commit()
    conn.close()

# --- 2. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(page_title="SPK Makan Gratis - Setu", layout="wide")

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

# --- 3. FUNGSI LOGIKA AHP ---
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

# --- 4. SESSION STATE ---
if 'weights' not in st.session_state: st.session_state.weights = None
if 'list_kriteria' not in st.session_state: st.session_state.list_kriteria = ["Harga", "Kualitas Bahan", "Waktu Kirim", "Pelayanan"]
if 'list_alternatif' not in st.session_state: st.session_state.list_alternatif = ["Supplier A", "Supplier B", "Supplier C"]

# --- 5. NAVIGASI ATAS ---
tab_home, tab_kriteria, tab_alternatif, tab_hasil, tab_riwayat = st.tabs([
    "BERANDA", "TAHAP 1 : KRITERIA", "TAHAP 2 : INPUT DATA", "TAHAP 3 : HASIL", "RIWAYAT"
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
        1. **Tahap 1:** Isi Kriteria & Alternatif, lalu tentukan tingkat kepentingan.
        2. **Tahap 2:** Masukkan data real masing-masing supplier.
        3. **Tahap 3:** Lihat hasil perangkingan dan simpan ke riwayat.
        """)

# --- HALAMAN 2: KRITERIA ---
with tab_kriteria:
    st.header("TAHAP 1: PENENTUAN KRITERIA & BOBOT")
    st.markdown("<div class='step-box'>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        k_input = st.text_area("Daftar Kriteria (Pisahkan dengan koma)", ", ".join(st.session_state.list_kriteria))
    with col_b:
        a_input = st.text_area("Daftar Alternatif (Pisahkan dengan koma)", ", ".join(st.session_state.list_alternatif))
    
    if st.button("SIMPAN DAFTAR KRITERIA & ALTERNATIF"):
        st.session_state.list_kriteria = [x.strip() for x in k_input.split(",")]
        st.session_state.list_alternatif = [x.strip() for x in a_input.split(",")]
        st.success("Daftar diperbarui!")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Perbandingan Kriteria")
    list_k = st.session_state.list_kriteria
    n = len(list_k)
    matriks_k = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            val = st.slider(f"Kepentingan: **{list_k[i]}** vs **{list_k[j]}**", 0.1, 9.0, 1.0, 0.5, key=f"k_{i}_{j}")
            matriks_k[i, j] = val
            matriks_k[j, i] = 1 / val
            
    if st.button("HITUNG BOBOT KRITERIA"):
        w, cr = hitung_ahp(matriks_k)
        st.session_state.weights = w
        st.session_state.cr = cr
        st.success(f"Bobot Dihitung! Konsistensi (CR): {cr:.4f}")
        st.table(pd.DataFrame({'Kriteria': list_k, 'Bobot': w}))

# --- HALAMAN 3: INPUT DATA ---
with tab_alternatif:
    st.header("TAHAP 2: INPUT DATA SUPPLIER")
    if st.session_state.weights is None:
        st.warning("Selesaikan Tahap 1 terlebih dahulu!")
    else:
        temp_data = []
        for i, alt in enumerate(st.session_state.list_alternatif):
            with st.expander(f"Data untuk: {alt}", expanded=True):
                cols = st.columns(len(st.session_state.list_kriteria))
                row_val = []
                for j, k in enumerate(st.session_state.list_kriteria):
                    if "Harga" in k:
                        val = cols[j].number_input(f"Harga (Rp)", min_value=0, key=f"v_{i}_{j}")
                    elif "Kualitas" in k:
                        k_txt = cols[j].selectbox(f"Kualitas", ["Segar", "Cukup Segar", "Tidak Segar"], key=f"v_{i}_{j}")
                        val = 3 if k_txt == "Segar" else (2 if k_txt == "Cukup Segar" else 1)
                    elif "Waktu" in k:
                        val = cols[j].number_input(f"Waktu (Menit)", min_value=0, key=f"v_{i}_{j}")
                    elif "Pelayanan" in k:
                        val = cols[j].number_input(f"Pelayanan (Skala 1-10)", 1, 10, 5, key=f"v_{i}_{j}")
                    else:
                        val = cols[j].number_input(f"{k}", min_value=0, key=f"v_{i}_{j}")
                    row_val.append(val)
                temp_data.append([alt] + row_val)
        
        if st.button("SIMPAN DATA SUPPLIER"):
            st.session_state.raw_matrix = temp_data
            st.success("Data disimpan! Silakan buka Tab Hasil.")

# --- HALAMAN 4: HASIL ---
with tab_hasil:
    st.header("TAHAP 3: ANALISIS HASIL SUPPLIER")
    if 'raw_matrix' not in st.session_state:
        st.error("Data belum lengkap.")
    else:
        data = st.session_state.raw_matrix
        names = [r[0] for r in data]
        matrix_x = np.array([r[1:] for r in data], dtype=float)
        
        # 1. Matriks X
        st.subheader("1. Matriks Keputusan Awal (X)")
        df_x = pd.DataFrame(matrix_x, columns=st.session_state.list_kriteria, index=names)
        fmt = {c: "{:.0f}" for c in df_x.columns}; 
        if "Harga" in fmt: fmt["Harga"] = "Rp {:,.0f}"
        st.dataframe(df_x.style.format(fmt), use_container_width=True)

        # 2. Matriks R
        norm_r = np.zeros_like(matrix_x)
        for j, k in enumerate(st.session_state.list_kriteria):
            if "Harga" in k or "Waktu" in k: norm_r[:, j] = matrix_x[:, j].min() / matrix_x[:, j]
            else: norm_r[:, j] = matrix_x[:, j] / matrix_x[:, j].max()
        st.subheader("2. Matriks Ternormalisasi (R)")
        st.dataframe(pd.DataFrame(norm_r, columns=st.session_state.list_kriteria, index=names).style.format("{:.4f}"), use_container_width=True)
        
        # 3. Skor & Simpan
        scores = norm_r @ st.session_state.weights
        df_rank = pd.DataFrame({"Supplier": names, "Skor": scores}).sort_values(by="Skor", ascending=False)
        df_rank["Ranking"] = range(1, len(df_rank) + 1)
        
        st.subheader("3. Perangkingan")
        st.success(f"Pemenang: **{df_rank.iloc[0]['Supplier']}**")
        st.dataframe(df_rank[["Ranking", "Supplier", "Skor"]].style.format({"Skor": "{:.4f}"}), use_container_width=True)
        
        if st.button("SIMPAN HASIL KE RIWAYAT"):
            simpan_hasil(df_rank.iloc[0]['Supplier'], float(df_rank.iloc[0]['Skor']), st.session_state.list_kriteria)
            st.balloons()
            st.success("Hasil berhasil diarsipkan!")

# --- HALAMAN 5: RIWAYAT ---
with tab_riwayat:
    st.header("RIWAYAT KEPUTUSAN SUPPLIER")
    conn = sqlite3.connect('spk_ahp.db')
    df_h = pd.read_sql_query("SELECT tanggal, pemenang, skor, kriteria FROM riwayat_keputusan ORDER BY tanggal DESC", conn)
    conn.close()
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True)
    else:
        st.info("Riwayat masih kosong.")
