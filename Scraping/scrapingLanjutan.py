import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import os

# --- Konfigurasi ---
JALUR_CSV_INPUT = 'link_carmudi.csv' 
JALUR_CSV_OUTPUT = 'dataset_scraped_carmudi.csv'
JALUR_CSV_PROGRESS = 'progress_backup.csv'  # File backup progress
NAMA_KOLOM_URL = 'Link'
JEDA_PERMINTAAN_DETIK = 3

def ekstrak_merk_dan_model_dari_url(url):
    """Mengekstrak, memformat, dan memisahkan nama kendaraan (Merk dan Model) dari URL."""
    try:
        cocok = re.search(r'/for-sale/(.*?)(-dki-jakarta)', url)
        if cocok:
            teks_nama_mentah = cocok.group(1).replace('-', ' ').title().strip()
            kata_kata = teks_nama_mentah.split()
            
            if kata_kata:
                merk = kata_kata[0]
                model = ' '.join(kata_kata[1:])
                return merk, model
            
    except Exception as e:
        print(f"  [Peringatan] Gagal mengekstrak Merk/Model dari URL: {url}. Error: {e}")
        return None, None
    
    return None, None

def ekstrak_data_spesifikasi(soup, nama_kelas_svg):
    """Fungsi bantuan untuk mencari data spesifikasi berdasarkan kelas ikon SVG."""
    try:
        ikon_svg = soup.find('svg', class_=nama_kelas_svg)
        if ikon_svg:
            data = ikon_svg.find_next_sibling('span', class_='u-text-bold').get_text(strip=True)
            return data
    except AttributeError:
        return None
    return None

def ekstrak_harga(soup):
    """Fungsi untuk mengekstrak harga dari halaman."""
    try:
        kontainer_harga = soup.find('div', class_='listing__item-price')
        if kontainer_harga:
            h3_tag = kontainer_harga.find('h3', class_='u-text-bold')
            if h3_tag:
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
        
        # Ekstrak Harga
        harga = ekstrak_harga(soup)

        # --- Ekstraksi Fitur Utama ---
        data_hasil_scrape = {
            'URL': url,
            'Merk': merk,
            'Model': model,
            'Harga': harga,
            'Tahun Produksi': ekstrak_data_spesifikasi(soup, 'svg-calendar'),
            'Jarak Tempuh': ekstrak_data_spesifikasi(soup, 'svg-mileage'),
            'Warna': ekstrak_data_spesifikasi(soup, 'svg-paint-brush')
        }
        
        # --- Scraping Spesifikasi Tambahan ---
        kontainer_data = soup.find_all('div', class_='u-border-bottom u-padding-ends-xs u-flex u-flex--justify-between')
        
        for item in kontainer_data:
            span_kunci = item.find('span', class_='u-width-1/2')
            span_nilai = item.find('span', class_='u-text-bold u-width-1/2 u-align-right')
            if span_kunci and span_nilai:
                kunci = span_kunci.get_text(strip=True)
                nilai = span_nilai.get_text(strip=True)
                if kunci not in data_hasil_scrape:
                    data_hasil_scrape[kunci] = nilai
        
        return data_hasil_scrape

    except Exception as e:
        print(f"  [ERROR] Terjadi error tak terduga saat memproses {url}: {e}")
        return {'URL': url, 'Error': str(e)}

def get_progress_terakhir():
    """Mendapatkan progress terakhir dari file backup."""
    if os.path.exists(JALUR_CSV_PROGRESS):
        try:
            df_progress = pd.read_csv(JALUR_CSV_PROGRESS)
            urls_selesai = df_progress['URL'].tolist()
            print(f"📁 Ditemukan progress sebelumnya: {len(urls_selesai)} URL sudah diproses")
            return urls_selesai
        except Exception as e:
            print(f"⚠️  Gagal membaca file progress: {e}")
            return []
    return []

def backup_progress(semua_hasil):
    """Menyimpan progress saat ini ke file backup."""
    try:
        df_backup = pd.DataFrame(semua_hasil)
        df_backup.to_csv(JALUR_CSV_PROGRESS, index=False, encoding='utf-8-sig')
        print(f"💾 Progress disimpan: {len(semua_hasil)} data tersimpan di {JALUR_CSV_PROGRESS}")
    except Exception as e:
        print(f"⚠️  Gagal menyimpan progress: {e}")

# --- Blok Eksekusi Utama ---
if __name__ == "__main__":
    print("🚀 Menginisialisasi Selenium WebDriver...")
    opsi_chrome = Options()
    opsi_chrome.add_argument("--headless")
    opsi_chrome.add_argument("--log-level=3")
    opsi_chrome.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opsi_chrome)
        print("✅ WebDriver siap digunakan.")
        
        # Memuat URL dari file CSV sumber
        df_urls = pd.read_csv(JALUR_CSV_INPUT)
        semua_url = df_urls[NAMA_KOLOM_URL].dropna().tolist()
        
        # Mendapatkan progress terakhir
        urls_selesai = get_progress_terakhir()
        urls_belum_diproses = [url for url in semua_url if url not in urls_selesai]
        
        print(f"📊 Statistik:")
        print(f"   - Total URL: {len(semua_url)}")
        print(f"   - Sudah diproses: {len(urls_selesai)}")
        print(f"   - Belum diproses: {len(urls_belum_diproses)}")
        
        if not urls_belum_diproses:
            print("✅ Semua URL sudah diproses sebelumnya!")
            # Load hasil sebelumnya dan simpan ke file final
            if os.path.exists(JALUR_CSV_PROGRESS):
                df_hasil_final = pd.read_csv(JALUR_CSV_PROGRESS)
                df_hasil_final.to_csv(JALUR_CSV_OUTPUT, index=False, encoding='utf-8-sig')
                print(f"📁 Hasil final disimpan di: {JALUR_CSV_OUTPUT}")
                os.remove(JALUR_CSV_PROGRESS)  # Hapus file progress
            driver.quit()
            exit()

        # Memuat hasil yang sudah ada
        if os.path.exists(JALUR_CSV_PROGRESS):
            semua_hasil = pd.read_csv(JALUR_CSV_PROGRESS).to_dict('records')
        else:
            semua_hasil = []

        # Memproses URL yang belum diproses
        print(f"\n🔄 Memulai proses scraping dari URL yang belum diproses...")
        for i, url in enumerate(urls_belum_diproses):
            print(f"📝 Memproses ({len(semua_hasil) + 1}/{len(semua_url)}): {url}")
            
            try:
                data = scrape_data_kendaraan(url, driver)
                if data:
                    semua_hasil.append(data)
                    
                    # Backup progress setiap 5 URL
                    if (i + 1) % 5 == 0:
                        backup_progress(semua_hasil)
                        print(f"💾 Auto-save progress...")
                        
            except Exception as e:
                print(f"❌ ERROR pada URL {url}: {e}")
                print("💾 Menyimpan progress sebelum berhenti...")
                backup_progress(semua_hasil)
                print("🔄 Script dapat dijalankan kembali untuk melanjutkan dari titik ini")
                break

        # Mengonversi list hasil ke DataFrame pandas
        df_hasil = pd.DataFrame(semua_hasil)
        
        # --- Penataan Struktur Data Final ---
        kolom_utama = ['URL', 'Merk', 'Model', 'Harga', 'Tahun Produksi', 'Jarak Tempuh', 'Warna']
        kolom_spesifikasi = [kol for kol in df_hasil.columns if kol not in kolom_utama and kol != 'Error']
        urutan_kolom_final = kolom_utama + sorted(kolom_spesifikasi)
        
        if 'Error' in df_hasil.columns:
            urutan_kolom_final.append('Error')

        # Memastikan hanya kolom yang ada yang digunakan untuk reindex
        kolom_untuk_reindex = [kol for kol in urutan_kolom_final if kol in df_hasil.columns]
        df_hasil = df_hasil.reindex(columns=kolom_untuk_reindex)

        # Menyimpan dataset final ke file CSV baru
        df_hasil.to_csv(JALUR_CSV_OUTPUT, index=False, encoding='utf-8-sig')
        
        # Hapus file progress jika sudah selesai semua
        if len(semua_hasil) == len(semua_url):
            if os.path.exists(JALUR_CSV_PROGRESS):
                os.remove(JALUR_CSV_PROGRESS)
            print(f"\n✅ Proses scraping BERHASIL DISELESAIKAN!")
        else:
            print(f"\n⏸️  Proses scraping PAUSED. {len(semua_hasil)} dari {len(semua_url)} URL berhasil diproses.")
            
        print(f"📁 Hasil disimpan di: {JALUR_CSV_OUTPUT}")

    except FileNotFoundError:
        print(f"❌ [ERROR KRITIS] File input tidak ditemukan di '{JALUR_CSV_INPUT}'. Mohon periksa kembali lokasi file.")
    except Exception as e:
        print(f"❌ [ERROR KRITIS] Skrip berhenti karena error tak terduga: {e}")
        # Backup progress sebelum keluar
        if 'semua_hasil' in locals():
            backup_progress(semua_hasil)
    finally:
        if 'driver' in locals() and driver:
            driver.quit()
            print("🔴 WebDriver telah ditutup.")