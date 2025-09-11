# Bu proje, birimlerin stratejik planlama etkinliğine göre başarı düzeyini sınıflandırmak için Random Forest modeli kullanır.
from sklearn.utils import resample
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import pyodbc
import os
from dotenv import load_dotenv
import warnings
from typing import Any
warnings.filterwarnings("ignore", category=UserWarning,
                        message=".*pandas only supports SQLAlchemy connectable.*")
pd.set_option("display.max_columns", None)

# Modelleme için gerekli kütüphaneler (rondom forest kullanacağız)

# Veritabanıyla bağlantı kuruluyor
load_dotenv()

conn: Any = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')}"
)

# Veriler veritabanından çekiliyor
birim = pd.read_sql("SELECT * FROM dbo.Birim", conn)
birim["Yoksis_Id"] = birim["Yoksis_Id"].astype(str).str.strip()
birim["Birim_Id"] = birim["Yoksis_Id"]
birim["Birim_Tur_Id"] = birim["Birim_Tur_Id"].astype(str).str.strip()
birim["Birim_Id"] = birim["Yoksis_Id"].astype(str)
birim["Birim_Id"] = birim["Birim_Id"].astype(str)
birim["Birim_Tur_Id"] = birim["Birim_Tur_Id"].astype(str).str.strip()

birimtur = pd.read_sql("SELECT * FROM dbo.BirimTur", conn)
birimtur["Birim_Tur_Id"] = birimtur["Birim_Tur_Id"].astype(str).str.strip()

birimrapor = pd.read_sql("SELECT * FROM dbo.BirimRaporDosya", conn)
birimrapor["Yoksis_Id"] = birimrapor["Yoksis_Id"].astype(str).str.strip()

planveri = pd.read_sql("SELECT * FROM dbo.BirimSPlanVeri", conn)
planveri["Yoksis_Id"] = planveri["Yoksis_Id"].astype(str).str.strip()
planveri["Yoksis_Id"] = planveri["Yoksis_Id"].astype(str)

print("\n=================== TABLO BOYUTLARI ===================")
print("Birim:", birim.shape)
print("BirimTur:", birimtur.shape)
print("BirimRaporDosya:", birimrapor.shape)
print("PlanVeri:", planveri.shape)
print(birim.isna().sum())

# 1. Birim bilgilerini sadeleştiri birim tablosunda birsürü column var, sadece gerekli olanları alıyoruz
birim = birim[["Yoksis_Id", "Adi", "Birim_Tur_Id"]].rename(columns={
    "Yoksis_Id": "Birim_Id",
    "Adi": "Birim_Adi"
})

# 2. Birim türünü ekle
# Birim türü tablosunu birim tablosuna ekle
birimtur = birimtur.rename(columns={"Adi": "Birim_Tur_Adi"})
birim = birim.merge(birimtur, on="Birim_Tur_Id",
                    how="left", validate="many_to_one")

print("\n" + "-"*60)
print("Eşleşmeyen Birim_Tur_Id değerleri:")
print(birim[birim["Birim_Tur_Adi"].isna()]["Birim_Tur_Id"].unique())

# 3. Rapor sayısı (Yoksis_Id üzerinden)
# ID tiplerini eşleştirmek için hepsini string'e çevir
# Rapor sayısını hesapla
rapor_sayilari = birimrapor.groupby(
    "Yoksis_Id").size().reset_index(name="Rapor_Sayisi")
rapor_sayilari["Yoksis_Id"] = rapor_sayilari["Yoksis_Id"].astype(
    str).str.strip()
birim["Birim_Id"] = birim["Birim_Id"].astype(str).str.strip()
birim = pd.merge(birim, rapor_sayilari, left_on="Birim_Id",
                 right_on="Yoksis_Id", how="left", validate="many_to_one")
birim["Rapor_Sayisi"] = birim["Rapor_Sayisi"].fillna(0).astype(int)

# 4. Stratejik plan hedef sayısı ve gerçekleşen sayısı
print("\n" + "-"*60)
print(planveri["MantiksalDeger"].value_counts())
hedef_sayisi = planveri.groupby(
    "Yoksis_Id").size().reset_index(name="Hedef_Sayisi")
hedef_sayisi["Yoksis_Id"] = hedef_sayisi["Yoksis_Id"].astype(str).str.strip()
gerceklesen = planveri[planveri["MantiksalDeger"] == True].groupby(
    "Yoksis_Id").size().reset_index(name="Gerceklesen_Hedef")
gerceklesen["Yoksis_Id"] = gerceklesen["Yoksis_Id"].astype(str).str.strip()

birim["Birim_Id"] = birim["Birim_Id"].astype(str).str.strip()
birim = birim.merge(hedef_sayisi, left_on="Birim_Id",
                    right_on="Yoksis_Id", how="left")
birim = birim.merge(gerceklesen, left_on="Birim_Id",
                    right_on="Yoksis_Id", how="left")

# Eksik değerleri 0 yap
birim["Hedef_Sayisi"] = birim["Hedef_Sayisi"].fillna(0).astype(int)
birim["Gerceklesen_Hedef"] = birim["Gerceklesen_Hedef"].fillna(0).astype(int)

birim["Planlama_Etkinligi"] = birim.apply(
    lambda row: row["Gerceklesen_Hedef"] / row["Hedef_Sayisi"] if row["Hedef_Sayisi"] > 0 else 0, axis=1)
birim["Rapor_Basina_Hedef"] = birim.apply(
    lambda row: row["Hedef_Sayisi"] / (row["Rapor_Sayisi"] + 1), axis=1)

birim = birim[birim["Hedef_Sayisi"] > 0]

birim["Ortalama_Hedef_Gerceklesme"] = birim.apply(
    lambda row: row["Gerceklesen_Hedef"] /
    row["Rapor_Sayisi"] if row["Rapor_Sayisi"] > 0 else 0,
    axis=1
)


# Eğer tüm başarı düzeyi tek sınıftan oluşuyorsa model eğitilemez


def etiketle_alternatif(row):
    if row["Planlama_Etkinligi"] >= 0.7:
        return "Başarılı"
    elif row["Planlama_Etkinligi"] >= 0.3:
        return "Orta"
    else:
        return "Başarısız"

birim["Basari_Duzeyi"] = birim.apply(etiketle_alternatif, axis=1)

if birim["Basari_Duzeyi"].nunique() == 1:
    print("UYARI: Veri setinde yalnızca '{}' sınıfı bulundu. Sınıflandırma için yeterli çeşitlilik yok.".format(
        birim["Basari_Duzeyi"].unique()[0]))
    print("Veri yetersiz olduğu için model eğitimi sonlandırıldı.")
    birim.to_csv("birim_basari_siniflandirma_sonuclari.csv", index=False)
    exit()

# Sınıfları ayır
df_basarisiz = birim[birim["Basari_Duzeyi"] == "Başarısız"]
df_basarili = birim[birim["Basari_Duzeyi"] == "Başarılı"]
df_orta = birim[birim["Basari_Duzeyi"] == "Orta"]

unique_classes = birim["Basari_Duzeyi"].unique()

if len(unique_classes) == 1:
    print(
        f"UYARI: Veri setinde yalnızca '{unique_classes[0]}' sınıfı bulundu. Sınıflandırma için yeterli çeşitlilik yok.")
    print("Veri yetersiz olduğu için model eğitimi sonlandırıldı.")
    birim.to_csv("birim_basari_siniflandirma_sonuclari.csv", index=False)
    exit()
elif len(unique_classes) == 2:
    # İki sınıf varsa, az olanı çoğalt
    class_counts = birim["Basari_Duzeyi"].value_counts()
    majority_class = class_counts.idxmax()
    minority_class = class_counts.idxmin()

    df_majority = birim[birim["Basari_Duzeyi"] == majority_class]
    df_minority = birim[birim["Basari_Duzeyi"] == minority_class]

    df_minority_up = resample(
        df_minority, replace=True, n_samples=len(df_majority), random_state=42)
    birim = pd.concat([df_majority, df_minority_up])  # type: ignore[call-overload]
else:
    # 3 sınıf varsa tüm sınıfları eşitle
    max_count = max(len(df_basarisiz), len(df_basarili), len(df_orta))
    df_basarisiz_up = resample(
        df_basarisiz, replace=True, n_samples=max_count, random_state=42)
    df_basarili_up = resample(
        df_basarili, replace=True, n_samples=max_count, random_state=42)
    df_orta_up = resample(df_orta, replace=True,
                          n_samples=max_count, random_state=42)
    birim = pd.concat([df_basarisiz_up, df_basarili_up, df_orta_up])  # type: ignore[call-overload]

# Son halini göster
print("\n" + "-"*60)
print(birim[["Birim_Adi", "Basari_Duzeyi"]].head(10))

# RANDOM FOREST MODELİ İLE SINIFLANDIRMA

# Kategorik veriyi sayısala çevir (One-Hot Encoding) çünkü modeller sayısal verilerle çalışır, yazı veriyi anlayamaz.
kategorik = pd.get_dummies(birim["Birim_Tur_Adi"], prefix="Tur")

# Ana veriyle birleştir
X = pd.concat([
    birim[[
        "Rapor_Sayisi", "Hedef_Sayisi", "Gerceklesen_Hedef",
        "Planlama_Etkinligi", "Rapor_Basina_Hedef", "Ortalama_Hedef_Gerceklesme"
    ]],
    kategorik
], axis=1)  # type: ignore[call-overload]
# X, modelin girdi verisi; y, modelin tahmin edeceği etiketlerdir.
y = birim["Basari_Duzeyi"]

# Eğitim/test bölmesi
X_train, X_test, y_train, y_test = train_test_split(
    # %30 test verisi, %70 eğitim verisi. stratify=y → Etiket sınıflarının oransal dağılımını koruyarak bölme yapar
    X, y, test_size=0.3, random_state=42, stratify=y
)  # (örnek: %60 başarılı, %30 orta, %10 başarısız → hem train hem test setinde bu oran korunur)


# Model oluştur
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Tahmin yap
# y_pred, test verisi için modelin tahmin ettiği etiketler
y_pred = model.predict(X_test)

# Değerlendirme
print("\n" + "-"*60)
print("Classification Report:\n", classification_report(
    y_test, y_pred))  # modelin başarısını gösterir
print("\n" + "-"*60)
# modelin tahminlerinin doğruluğunu gösterir
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# Karışıklık matrisi görselleştirme (confusion matrix)
labels = ["Başarılı", "Orta", "Başarısız"]  # Sıralı ve tam etiket listesi

plt.figure(figsize=(6, 4))
sns.heatmap(
    confusion_matrix(y_test, y_pred, labels=labels),
    annot=True, fmt="d", cmap="Blues",
    xticklabels=labels, yticklabels=labels
)
plt.xlabel("Tahmin Edilen")
plt.ylabel("Gerçek Değer")
plt.title("Başarı Sınıflandırması - Karışıklık Matrisi")
print("\n" + "-"*60)
plt.tight_layout()
plt.show()
# Bu grafik sana şunu gösterir:
# Model “Başarılı” etiketini kaç kez doğru tahmin etmiş?
# “Orta” ya da “Başarısız” olanları karıştırmış mı?
# En çok hangi sınıfta zorlanmış?

# Tüm veriyi dışa aktar (etiketli haliyle)
birim.to_csv("birim_basari_siniflandirma_sonuclari.csv", index=False)

# Sadece test sonuçlarını ayrı olarak kaydetmek istersen:
test_sonuclari = X_test.copy()
test_sonuclari["Gercek"] = y_test.values
test_sonuclari["Tahmin"] = y_pred
test_sonuclari.to_csv("model_tahmin_sonuclari.csv", index=False)

# Sayısal sütunlar için genel istatistik
print("\n" + "-"*60)
print(birim[["Rapor_Sayisi", "Hedef_Sayisi", "Gerceklesen_Hedef"]].describe())

print("\n" + "-"*60)
print(kategorik.head())

print("\n" + "-"*60)
print(birim["Birim_Tur_Adi"].value_counts())

# === ÖZELLİK ÖNEMİ ANALİZİ ===
importances = model.feature_importances_
feature_names = X.columns
feature_imp_series = pd.Series(
    importances, index=feature_names).sort_values(ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x=feature_imp_series.values, y=feature_imp_series.index,
            hue=None, palette="viridis", legend=False)
plt.title("Random Forest - Özellik Önem Düzeyleri")
plt.xlabel("Önem Skoru")
plt.ylabel("Özellikler")
print("\n" + "-"*60)
plt.tight_layout()
plt.show()

print("\n" + "-"*60)
print("Özellik önemleri:", model.feature_importances_)

print("\n" + "-"*60)
print(birim[["Rapor_Sayisi", "Hedef_Sayisi",
      "Gerceklesen_Hedef", "Basari_Duzeyi"]].head(20))

print("\n" + "-"*60)
print("Veri setindeki sınıf dağılımı:")
print(birim["Basari_Duzeyi"].value_counts())
print("\n" + "-"*60)
print("\nSınıf dağılımı (oran olarak):")
print(birim["Basari_Duzeyi"].value_counts(normalize=True))
if birim["Basari_Duzeyi"].nunique() == 1:
    print("UYARI: Veri setinde yalnızca '{}' sınıfı bulundu. Sınıflandırma için yeterli çeşitlilik yok.".format(
        birim["Basari_Duzeyi"].unique()[0]))

print(birim["Basari_Duzeyi"].value_counts())
birim.to_csv("birim_basari_siniflandirma_sonuclari.csv", index=False)
print("Birim:", birim.shape)
print("BirimRapor:", birimrapor.shape)
print("PlanVeri:", planveri.shape)
print("Birleşmiş tablo:", birim.head())

print("\n" + "-"*60)
print("Birim tablosu (ilk 5 satır):")
print(birim.head())

print("\n" + "-"*60)
print("BirimRapor tablosu (ilk 5 satır):")
print(birimrapor.head())

print("\n" + "-"*60)
print("PlanVeri tablosu (ilk 5 satır):")
print(planveri.head())

print("İşlem tamamlandı. Model başarıyla eğitildi ve sonuçlar kaydedildi.")
