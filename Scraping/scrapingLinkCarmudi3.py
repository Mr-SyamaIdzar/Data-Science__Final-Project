import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_carmudi_links(total_pages):
    """
    Fungsi untuk melakukan scraping HANYA LINK mobil bekas 
    dari Carmudi.co.id di Yogyakarta.

    Args:
        total_pages (int): Jumlah halaman yang ingin di-scrape.

    Returns:
        pandas.DataFrame: DataFrame berisi link mobil yang berhasil di-scrape.
    """
    base_url = "https://www.carmudi.co.id/en/used-cars-for-sale/indonesia_dki-jakarta"
    all_links = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for page in range(343, total_pages + 1):
        target_url = f"{base_url}?page_number={page}&page_size=25"
        print(f"Scraping halaman ke-{page}: {target_url}")

        try:
            response = requests.get(target_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- PERUBAHAN UTAMA: Langsung mencari semua tag link yang relevan ---
            # Tag <a> dengan class 'ellipsize' berisi link yang kita butuhkan
            link_tags = soup.find_all('a', class_='ellipsize')

            if not link_tags:
                print(f"Tidak ada link ditemukan di halaman {page}. Proses berhenti.")
                break

            for tag in link_tags:
                # Mengambil nilai dari atribut 'href' saja
                link = tag.get('href')
                if link:
                    all_links.append({'Link': link})
            
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Gagal mengakses halaman {page}. Error: {e}")
            continue

    df = pd.DataFrame(all_links)
    return df

# --- EKSEKUSI SCRIPT ---
if __name__ == "__main__":
    jumlah_halaman = 542
    data_link_df = scrape_carmudi_links(jumlah_halaman)

    print("\n--- Hasil Scraping (5 Link Pertama) ---")
    print(data_link_df.head())

    print(f"\nTotal link yang berhasil di-scrape: {len(data_link_df)}.")

    try:
        data_link_df.to_csv('link_carmudi.csv', index=False)
        print("\nData berhasil disimpan ke file 'link_carmudi.csv'")
    except Exception as e:
        print(f"\nGagal menyimpan file CSV. Error: {e}")