import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st
import joblib

# ============================
# 🔧 STREAMLIT CONFIG
# ============================
st.set_page_config(
    page_title="Prediksi Harga Mobil Bekas DKI Jakarta",
    page_icon="🚗",
    layout="centered"
)

st.title("🚗 Prediksi Harga Mobil Bekas — DKI Jakarta")
st.write("Masukkan detail spesifikasi mobil untuk memprediksi harga pasarnya di Jakarta.")

# ============================
# 🔥 LOAD ARTIFACTS
# ============================
model = joblib.load("best_price_model.pkl")
scaler = joblib.load("scaler.pkl")
ohe = joblib.load("ohe_fuel_transmission.pkl")

merk_freq = joblib.load("merk_freq.pkl")
model_freq = joblib.load("model_short_freq.pkl")

# Load daftar fitur final
feature_names = joblib.load("feature_names.pkl")

# Ambil kelas OHE hanya untuk fuel & transmission
ohe_feature_names = ohe.get_feature_names_out(['Fuel Type', 'Transmission'])

# ============================
# 📌 FORM INPUT
# ============================
st.sidebar.header("Input Spesifikasi Mobil")

umur = st.sidebar.number_input("Umur Mobil (tahun)", 0, 30, 5)
jarak_tempuh = st.sidebar.number_input("Jarak Tempuh (km)", 0, 400000, 100000)
engine_cc = st.sidebar.number_input("Engine Capacity (CC)", 600, 5000, 1500)
seat = st.sidebar.number_input("Jumlah Kursi", 2, 12, 5)

fuel_type = st.sidebar.selectbox("Fuel Type", ohe.categories_[0])
transmission = st.sidebar.selectbox("Transmission", ohe.categories_[1])

merk_input = st.sidebar.text_input("Merk Mobil", placeholder="contoh: Toyota")
model_input = st.sidebar.text_input("Model Pendek", placeholder="contoh: Avanza")

btn = st.sidebar.button("Prediksi Harga")

# ============================
# 🛑 VALIDASI INPUT
# ============================
allow_predict = True

if btn:
    if merk_input.strip() == "":
        st.sidebar.error("❗ Merk mobil wajib diisi.")
        allow_predict = False

    if model_input.strip() == "":
        st.sidebar.error("❗ Model mobil wajib diisi.")
        allow_predict = False

# ============================
# 🔮 PREDIKSI HARGA
# ============================
if btn and allow_predict:

    # -------------------------
    # 1️⃣ OHE Fuel & Transmission
    # -------------------------
    ohe_input = ohe.transform([[fuel_type, transmission]])
    ohe_df = pd.DataFrame(ohe_input, columns=ohe_feature_names)

    # -------------------------
    # 2️⃣ Frequency Encoding
    # -------------------------
    merk_val = merk_freq.get(merk_input, 0)
    model_val = model_freq.get(model_input, 0)

    df_numeric = pd.DataFrame([{
        "Umur Mobil": umur,
        "Jarak Tempuh": jarak_tempuh,
        "Engine CC": engine_cc,
        "Seat Capacity": seat,
        "Merk_Freq": merk_val,
        "Model_Short_Freq": model_val
    }])

    # -------------------------
    # 3️⃣ Gabungkan semua feature
    # -------------------------
    input_df = pd.concat([df_numeric, ohe_df], axis=1)

    # Pastikan kolom urutannya sama dengan training
    input_df = input_df.reindex(columns=feature_names, fill_value=0)

    # -------------------------
    # 4️⃣ Scaling
    # -------------------------
    input_scaled = scaler.transform(input_df)

    # -------------------------
    # 5️⃣ Predict
    # -------------------------
    pred = model.predict(input_scaled)[0]
    low = pred * 0.9
    high = pred * 1.1

    # -------------------------
    # 6️⃣ Output UI
    # -------------------------
    st.subheader("📌 Hasil Prediksi")
    st.success(f"Estimasi Harga: **Rp {pred:,.0f}**")
    st.write(f"Rentang harga pasar: **Rp {low:,.0f} – Rp {high:,.0f}**")

    st.subheader("📋 Detail Input (Setelah Encoding & OHE)")
    st.write(input_df)

    st.subheader("📊 Visualisasi Fitur Input")
    st.bar_chart(input_df.T)

else:
    st.info("Isi spesifikasi mobil lalu klik **Prediksi Harga**.")
