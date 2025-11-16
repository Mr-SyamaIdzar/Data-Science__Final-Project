import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st
import joblib
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder

# Model Splitting & Scaling
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Model Regresi
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb  # Alternatif populer selain XGBoost

# Evaluasi Model
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Tuning
from sklearn.model_selection import RandomizedSearchCV

# (Opsional) Mengatur agar output angka tidak dalam notasi ilmiah
pd.options.display.float_format = '{:,.2f}'.format

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

le_fuel = joblib.load("fuel_type_encoder.pkl")
le_transmission = joblib.load("transmission_encoder.pkl")

# Frequency encoding maps
merk_freq = joblib.load("merk_freq.pkl")
model_freq = joblib.load("model_short_freq.pkl")

# ============================
# 📌 FORM INPUT
# ============================
st.sidebar.header("Input Spesifikasi Mobil")

umur = st.sidebar.number_input("Umur Mobil (tahun)", 0, 30, 5)
jarak_tempuh = st.sidebar.number_input("Jarak Tempuh (km)", 0, 400000, 100000)
engine_cc = st.sidebar.number_input("Engine Capacity (CC)", 600, 5000, 1500)
seat = st.sidebar.number_input("Jumlah Kursi", 2, 12, 5)

fuel_type = st.sidebar.selectbox("Fuel Type", le_fuel.classes_)
transmission = st.sidebar.selectbox("Transmission", le_transmission.classes_)

merk_input = st.sidebar.text_input("Merk Mobil", placeholder="contoh: Toyota")
model_input = st.sidebar.text_input("Model Pendek", placeholder="contoh: Avanza")

btn = st.sidebar.button("Prediksi Harga")

# ============================
# 🔮 PREDICTION
# ============================
if btn:

    # Label encoding
    fuel_encoded = le_fuel.transform([fuel_type])[0]
    trans_encoded = le_transmission.transform([transmission])[0]

    # Frequency encoding
    merk_val = merk_freq.get(merk_input, 0)
    model_val = model_freq.get(model_input, 0)

    # Dataframe input
    input_df = pd.DataFrame([{
        "Umur Mobil": umur,
        "Jarak Tempuh": jarak_tempuh,
        "Engine CC": engine_cc,
        "Seat Capacity": seat,
        "Fuel Type_encode": fuel_encoded,
        "Transmission_encode": trans_encoded,
        "Merk_Freq": merk_val,
        "Model_Short_Freq": model_val
    }])

    # Scaling
    input_scaled = scaler.transform(input_df)

    # Predict
    pred = model.predict(input_scaled)[0]

    # Range ±10%
    low = pred * 0.9
    high = pred * 1.1

    st.subheader("📌 Hasil Prediksi")
    st.success(f"**Estimasi Harga: Rp {pred:,.0f}**")
    st.write(f"Rentang harga pasar: **Rp {low:,.0f} - Rp {high:,.0f}**")

    st.subheader("📋 Detail Input")
    st.write(input_df)

    st.subheader("📊 Visualisasi Fitur")
    st.bar_chart(input_df.T)

else:
    st.info("Isi spesifikasi mobil lalu klik **Prediksi Harga**.")