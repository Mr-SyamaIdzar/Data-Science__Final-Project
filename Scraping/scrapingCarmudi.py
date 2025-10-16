import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re

# --- Konfigurasi ---
# PERUBAHAN 1: Ganti nama file input
JALUR_CSV_INPUT = 'link_carmudi.csv' 
JALUR_CSV_OUTPUT = 'dataset_scraped_carmudi.csv' 
NAMA_KOLOM_URL = 'Link'
JEDA_PERMINTAAN_DETIK = 3 # Jeda antar permintaan untuk tidak membebani server

def ekstrak_merk_dan_model_dari_url(url):
    """Mengekstrak, memformat, dan memisahkan nama kendaraan (Merk dan Model) dari URL."""
    try:
        # PERUBAHAN 2: Mencari teks di antara '/for-sale/' dan '-dki-jakarta'
        cocok = re.search(r'/for-sale/(.*?)(-dki-jakarta)', url)
        if cocok:
            # Mengganti tanda hubung dengan spasi dan mengapitalisasi setiap kata
            teks_nama_mentah = cocok.group(1).replace('-', ' ').title().strip()
            
            # Pisahkan menjadi kata-kata
            kata_kata = teks_nama_mentah.split()
            
            if kata_kata:
                # Merk adalah kata pertama
                merk = kata_kata[0]
                # Model adalah kata-kata setelah kata pertama
                model = ' '.join(kata_kata[1:])
                
                # Jika tidak ada model (hanya ada merk), Model akan diisi dengan string kosong
                return merk, model
            
    except Exception as e:
        print(f"  [Peringatan] Gagal mengekstrak Merk/Model dari URL: {url}. Error: {e}")
        return None, None # Mengembalikan dua nilai
    
    return None, None

def ekstrak_data_spesifikasi(soup, nama_kelas_svg):
    """Fungsi bantuan untuk mencari data spesifikasi berdasarkan kelas ikon SVG."""
    try:
        # Cari ikon SVG berdasarkan nama kelasnya, contoh: 'svg-calendar'
        ikon_svg = soup.find('svg', class_=nama_kelas_svg)
        if ikon_svg:
            # Data yang dicari berada di tag 'span' selanjutnya yang memiliki kelas 'u-text-bold'
            data = ikon_svg.find_next_sibling('span', class_='u-text-bold').get_text(strip=True)
            return data
    except AttributeError:
        # Terjadi jika elemen tidak ditemukan (misal, data di iklan tidak lengkap)
        return None
    return None

def ekstrak_harga(soup):
    """Fungsi baru untuk mengekstrak harga dari halaman."""
    try:
        # Mencari tag <div> dengan class yang relevan
        kontainer_harga = soup.find('div', class_='listing__item-price')
        if kontainer_harga:
            # Mencari tag <h3> di dalamnya
            h3_tag = kontainer_harga.find('h3', class_='u-text-bold')
            if h3_tag:
                # Ambil teks, hilangkan spasi/baris baru, dan kembalikan
                harga = h3_tag.get_text(strip=True)
                return harga
    except Exception as e:
        print(f"  [Peringatan] Gagal mengekstrak Harga. Error: {e}")
        return None
    return None

def scrape_data_kendaraan(url, driver):
    """
    Fungsi utama untuk scraping satu URL.
    Mengatur proses ekstraksi dan mengembalikan hasilnya dalam bentuk dictionary.
    """
    try:
        driver.get(url)
        time.sleep(JEDA_PERMINTAAN_DETIK)

        sumber_halaman = driver.page_source
        soup = BeautifulSoup(sumber_halaman, 'html.parser')

        # Ekstrak Merk dan Model
        merk, model = ekstrak_merk_dan_model_dari_url(url)
        
        # Ekstrak Harga (PERUBAHAN 3)
        harga = ekstrak_harga(soup)

        # --- Ekstraksi Fitur Utama ---
        # Menentukan struktur data utama dan urutan kolom
        data_hasil_scrape = {
            'URL': url,
            'Merk': merk,        # Kolom baru
            'Model': model,      # Kolom baru
            'Harga': harga,      # Kolom baru
            'Tahun Produksi': ekstrak_data_spesifikasi(soup, 'svg-calendar'),
            'Jarak Tempuh': ekstrak_data_spesifikasi(soup, 'svg-mileage'),
            'Warna': ekstrak_data_spesifikasi(soup, 'svg-paint-brush')
        }
        
        # --- Scraping Spesifikasi Tambahan ---
        # Mencari semua pasangan kunci-nilai untuk spesifikasi kendaraan
        kontainer_data = soup.find_all('div', class_='u-border-bottom u-padding-ends-xs u-flex u-flex--justify-between')
        
        for item in kontainer_data:
            span_kunci = item.find('span', class_='u-width-1/2')
            span_nilai = item.find('span', class_='u-text-bold u-width-1/2 u-align-right')
            if span_kunci and span_nilai:
                kunci = span_kunci.get_text(strip=True)
                nilai = span_nilai.get_text(strip=True)
                # Tambahkan hanya jika belum ada di fitur utama (dan bukan Merk/Model/Harga)
                if kunci not in data_hasil_scrape:
                    data_hasil_scrape[kunci] = nilai
        
        return data_hasil_scrape

    except Exception as e:
        print(f"  [ERROR] Terjadi error tak terduga saat memproses {url}: {e}")
        return {'URL': url, 'Error': str(e)}

# --- Blok Eksekusi Utama ---
if __name__ == "__main__":
    print("Menginisialisasi Selenium WebDriver...")
    opsi_chrome = Options()
    opsi_chrome.add_argument("--headless")  # Menjalankan browser di latar belakang
    opsi_chrome.add_argument("--log-level=3") # Menyembunyikan pesan konsol yang tidak penting
    opsi_chrome.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opsi_chrome)
        print("WebDriver siap digunakan.")
        
        # Memuat URL dari file CSV sumber
        df_urls = pd.read_csv(JALUR_CSV_INPUT)
        urls_untuk_diproses = df_urls[NAMA_KOLOM_URL].dropna().tolist() 
        print(f"Ditemukan {len(urls_untuk_diproses)} URL untuk diproses.")

        # Memproses setiap URL dan menyimpan hasilnya
        semua_hasil = []
        for i, url in enumerate(urls_untuk_diproses):
            print(f"Memproses ({i+1}/{len(urls_untuk_diproses)}): {url}")
            data = scrape_data_kendaraan(url, driver)
            if data:
                semua_hasil.append(data)

        # Mengonversi list hasil ke DataFrame pandas
        df_hasil = pd.DataFrame(semua_hasil)
        
        # --- Penataan Struktur Data Final ---
        # Menentukan dan menerapkan urutan kolom akhir untuk file CSV
        kolom_utama = ['URL', 'Merk', 'Model', 'Harga', 'Tahun Produksi', 'Jarak Tempuh', 'Warna'] # 'Harga' ditambahkan
        kolom_spesifikasi = [kol for kol in df_hasil.columns if kol not in kolom_utama and kol != 'Error']
        urutan_kolom_final = kolom_utama + sorted(kolom_spesifikasi)
        
        if 'Error' in df_hasil.columns:
            urutan_kolom_final.append('Error')

        # Memastikan hanya kolom yang ada yang digunakan untuk reindex
        kolom_untuk_reindex = [kol for kol in urutan_kolom_final if kol in df_hasil.columns]
        df_hasil = df_hasil.reindex(columns=kolom_untuk_reindex)

        # Menyimpan dataset final ke file CSV baru
        df_hasil.to_csv(JALUR_CSV_OUTPUT, index=False, encoding='utf-8-sig')
        print(f"\n✔ Proses scraping berhasil diselesaikan.")
        print(f"Hasil disimpan di: {JALUR_CSV_OUTPUT}")

    except FileNotFoundError:
        print(f"❌ [ERROR KRITIS] File input tidak ditemukan di '{JALUR_CSV_INPUT}'. Mohon periksa kembali lokasi file.")
    except Exception as e:
        print(f"❌ [ERROR KRITIS] Skrip berhenti karena error tak terduga: {e}")
    finally:
        if 'driver' in locals() and driver:
            driver.quit()
            print("WebDriver telah ditutup.")