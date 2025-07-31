# Başarı Sınıflandırma Projesi

Bu proje, **Çukurova Üniversitesi STRATEJİK_PLAN** veritabanı kullanılarak akademik birimlerin performanslarını analiz etmek ve başarı düzeylerine göre sınıflandırmak amacıyla geliştirilmiştir. Python programlama dili ve veri bilimi kütüphaneleri kullanılarak veri çekme, ön işleme ve analiz işlemleri gerçekleştirilmiştir.

✅ Proje tamamlanmıştır.

---

## 🔍 Proje Hakkında

Akademik birimlere ait hedef, gerçekleşen veri ve oranlar; ilgili veritabanı tablolarından çekilerek sınıflandırma mantığıyla analiz edilmiştir. Gerçek CSV verileri gizlilik nedeniyle kaldırılmış olup, yalnızca anonimleştirilmiş örnekler projede bulunmaktadır. Veri gizliliğine önem verilerek bağlantı bilgileri `.env` dosyasında tutulur ve `.gitignore` aracılığıyla gizlenir. `.env` dosyası veritabanına bağlanmak için gereklidir, örnek `.csv` dosyaları ise isteğe bağlıdır.

---

## 📁 Dosya ve Klasörler

- `basari_siniflandirmasi.py` – Ana Python script dosyası.
- `.env` – Veritabanı erişim bilgilerini içerir. (Git ile paylaşılmaz)
- `.gitignore` – İzlenmemesi gereken dosyaları belirtir.
- `requirements.txt` – Projede kullanılan kütüphaneler.
- `ornek_csvler/` – Projeye dahil edilen anonimleştirilmiş örnek CSV verileri klasörü.
- `csv_ornek_olustur.py` – Örnek CSV verisi üretmek için script.

---

## ⚙️ Kurulum

Gerekli kütüphaneleri yüklemek için:

```
pip install -r requirements.txt
```

---

## 🚀 Kullanım

Proje dosyasının bulunduğu klasörde terminal açarak aşağıdaki komutu çalıştırın:

```
python basari_siniflandirmasi.py
```

---

## 📌 Notlar

- `.env` gibi hassas dosyalar `.gitignore` tarafından dışlanmıştır.
- Bu proje yalnızca akademik ve kurum içi analiz amaçlı geliştirilmiştir.

---

# Success Classification Project

This project analyzes and classifies the performance of academic units using the **Çukurova University STRATEJIK_PLAN** database. It involves database querying, data preprocessing, and classification logic implemented in Python.

✅ The project has been completed.

---

## 🔍 Overview

Data related to unit goals and performance metrics is fetched from the database and used to perform classification-based analysis. Real CSV data has been removed for privacy reasons; only anonymized sample CSV files remain in the project. Credentials are stored in a `.env` file and excluded via `.gitignore` to ensure data security. The `.env` file is required to connect to the database, while sample `.csv` files are optional.

---

## 📁 Files & Structure

- `basari_siniflandirmasi.py` – Main Python script.
- `.env` – Database credentials (not tracked).
- `.gitignore` – Specifies ignored files.
- `requirements.txt` – Python dependencies.
- `ornek_csvler/` – Folder containing anonymized sample CSV files used in the project.
- `csv_ornek_olustur.py` – Script for generating example CSV data.

---

## ⚙️ Setup

To install dependencies:

```
pip install -r requirements.txt
```

---

## 🚀 Usage

Run the script from terminal in the project directory:

```
python basari_siniflandirmasi.py
```

---

## 📌 Notes

- Sensitive files such as `.env` are excluded via `.gitignore`.
- This project is developed for academic and internal analysis purposes only.