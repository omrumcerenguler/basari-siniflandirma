from dotenv import load_dotenv
import os
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# Modelleme için gerekli kütüphaneler (rondom forest kullanacağız)
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils import resample

# Veritabanıyla bağlantı kuruluyor
load_dotenv()

conn = pyodbc.connect(
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

# 1. Birim bilgilerini sadeleştiri birim tablosunda birsürü column var, sadece gerekli olanları alıyoruz
birim = birim[["Yoksis_Id", "Adi", "Birim_Tur_Id"]].rename(columns={
    "Yoksis_Id": "Birim_Id",
    "Adi": "Birim_Adi"
})

# 2. Birim türünü ekle
# Birim türü tablosunu birim tablosuna ekle
birimtur = birimtur.rename(columns={"Adi": "Birim_Tur_Adi"}) 
birim = birim.merge(birimtur, on="Birim_Tur_Id", how="left", validate="many_to_one")

print("Eşleşmeyen Birim_Tur_Id değerleri:")
print(birim[birim["Birim_Tur_Adi"].isna()]["Birim_Tur_Id"].unique())

# 3. Rapor sayısı (Yoksis_Id üzerinden)
# ID tiplerini eşleştirmek için hepsini string'e çevir
# Rapor sayısını hesapla
rapor_sayilari = birimrapor.groupby("Yoksis_Id").size().reset_index(name="Rapor_Sayisi")
rapor_sayilari["Yoksis_Id"] = rapor_sayilari["Yoksis_Id"].astype(str).str.strip()
birim["Birim_Id"] = birim["Birim_Id"].astype(str).str.strip()
birim = pd.merge(birim, rapor_sayilari, left_on="Birim_Id", right_on="Yoksis_Id", how="left", validate="many_to_one")
birim["Rapor_Sayisi"] = birim["Rapor_Sayisi"].fillna(0).astype(int)

# 4. Stratejik plan hedef sayısı ve gerçekleşen sayısı
hedef_sayisi = planveri.groupby("Yoksis_Id").size().reset_index(name="Hedef_Sayisi")
hedef_sayisi["Yoksis_Id"] = hedef_sayisi["Yoksis_Id"].astype(str).str.strip()
gerceklesen = planveri[planveri["MantiksalDeger"] == True].groupby("Yoksis_Id").size().reset_index(name="Gerceklesen_Hedef")
gerceklesen["Yoksis_Id"] = gerceklesen["Yoksis_Id"].astype(str).str.strip()

birim["Birim_Id"] = birim["Birim_Id"].astype(str).str.strip()
birim = birim.merge(hedef_sayisi, left_on="Birim_Id", right_on="Yoksis_Id", how="left")
birim = birim.merge(gerceklesen, left_on="Birim_Id", right_on="Yoksis_Id", how="left")

# Eksik değerleri 0 yap
birim["Hedef_Sayisi"] = birim["Hedef_Sayisi"].fillna(0).astype(int)
birim["Gerceklesen_Hedef"] = birim["Gerceklesen_Hedef"].fillna(0).astype(int)

# Gerçekleşme oranı
birim["Gerceklesme_Orani"] = (
    birim["Gerceklesen_Hedef"] / birim["Hedef_Sayisi"].replace(0, pd.NA)
) * 100
birim["Gerceklesme_Orani"] = birim["Gerceklesme_Orani"].fillna(0)

# Sonuçlardan örnek göster
#print(birim[["Birim_Adi", "Birim_Tur_Adi", "Rapor_Sayisi", "Hedef_Sayisi", "Gerceklesen_Hedef", "Gerceklesme_Orani"]].head(10))

# 5. Etiket oluştur: Başarılı, Orta, Başarısız
def etiketle(orani):
    if orani >= 80:
        return "Başarılı"
    elif orani >= 50:
        return "Orta"
    else:
        return "Başarısız"

birim["Basari_Duzeyi"] = birim["Gerceklesme_Orani"].apply(etiketle)

# Sınıfları ayır
df_basarisiz = birim[birim["Basari_Duzeyi"] == "Başarısız"]
df_basarili = birim[birim["Basari_Duzeyi"] == "Başarılı"]
df_orta = birim[birim["Basari_Duzeyi"] == "Orta"]

# Azınlık sınıfları çoğalt (upsampling)
df_basarili_up = pd.DataFrame()
df_orta_up = pd.DataFrame()

if not df_basarili.empty:
    df_basarili_up = resample(df_basarili, replace=True, n_samples=len(df_basarisiz), random_state=42)

if not df_orta.empty:
    df_orta_up = resample(df_orta, replace=True, n_samples=len(df_basarisiz), random_state=42) 
    
# Yeni dengelenmiş veri seti
birim = pd.concat([df_basarisiz, df_basarili_up, df_orta_up])

# Son halini göster
#print(birim[["Birim_Adi", "Gerceklesme_Orani", "Basari_Duzeyi"]].head(10))

# RANDOM FOREST MODELİ İLE SINIFLANDIRMA

# Kategorik veriyi sayısala çevir (One-Hot Encoding) çünkü modeller sayısal verilerle çalışır, yazı veriyi anlayamaz.
kategorik = pd.get_dummies(birim["Birim_Tur_Adi"], prefix="Tur")

# Ana veriyle birleştir
X = pd.concat([birim[["Rapor_Sayisi", "Hedef_Sayisi", "Gerceklesen_Hedef"]], kategorik], axis=1) 
y = birim["Basari_Duzeyi"] # X, modelin girdi verisi; y, modelin tahmin edeceği etiketlerdir.

# Eğitim/test bölmesi
X_train, X_test, y_train, y_test = train_test_split( 
    X, y, test_size=0.3, random_state=42, stratify=y # %30 test verisi, %70 eğitim verisi. stratify=y → Etiket sınıflarının oransal dağılımını koruyarak bölme yapar
)                                                   #(örnek: %60 başarılı, %30 orta, %10 başarısız → hem train hem test setinde bu oran korunur)


# Model oluştur
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Tahmin yap
y_pred = model.predict(X_test) #y_pred, test verisi için modelin tahmin ettiği etiketler

# Değerlendirme
#print("Classification Report:\n", classification_report(y_test, y_pred)) # modelin başarısını gösterir
#print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred)) # modelin tahminlerinin doğruluğunu gösterir

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
plt.tight_layout()
#plt.show()
#Bu grafik sana şunu gösterir:
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
#print(birim[["Rapor_Sayisi", "Hedef_Sayisi", "Gerceklesen_Hedef", "Gerceklesme_Orani"]].describe())

# Korelasyon matrisi oluştur
corr = birim[["Rapor_Sayisi", "Hedef_Sayisi", "Gerceklesen_Hedef", "Gerceklesme_Orani"]].corr() # Korelasyon, değişkenler arasındaki ilişkiyi gösterir. 1'e yakınsa pozitif ilişki, -1'e yakınsa negatif ilişki vardır. 0 ise ilişkisizlik anlamına gelir.
                                                                                           #pozitif ilişki= biri artarsa diğeri de artar; negatif ilişki= biri artarsa diğeri azalır.
# Korelasyon heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", linewidths=0.5)
plt.title("Sayısal Değişkenler Arası Korelasyon Matrisi")
plt.tight_layout()
#plt.show()

print(kategorik.head())

print(birimtur["Birim_Tur_Adi"].unique())

print(birimtur.columns)
print(birim["Birim_Tur_Id"].unique())
print(birimtur["Birim_Tur_Id"].unique())
print(birim["Birim_Tur_Adi"].value_counts())