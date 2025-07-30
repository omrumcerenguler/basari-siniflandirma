import pandas as pd
import os

# Bu dosyanın bulunduğu klasörü al
csv_folder = os.getcwd()

# Bu klasördeki tüm .csv dosyalarını listele
csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]

# Örnek CSV'lerin kaydedileceği klasör
output_folder = os.path.join(csv_folder, "ornek_csvler")
os.makedirs(output_folder, exist_ok=True)

for file in csv_files:
    try:
        df = pd.read_csv(os.path.join(csv_folder, file))
        sample_df = df.head(2)
        new_filename = os.path.join(output_folder, file.replace(".csv", "_ornek.csv"))
        sample_df.to_csv(new_filename, index=False)
        print(f"{file} → {os.path.basename(new_filename)}")
    except Exception as e:
        print(f"Hata {file} dosyasında: {e}")