# Aylıq Növbətçilik Planlaşdırma Sistemi - İstifadə Təlimatı

## 📋 Ümumi Məqsəd

Bu Excel sistemi, Azərbaycan dilində hazırlanmış peşəkar səviyyəli aylıq növbətçilik planlaşdırma və ədalət sistemi olmaq üçün nəzərdə tutulub. Sistem sadəcə növbələri cədvələ yazmaq deyil, həm də şəxslərin mövcudluğunu, növbələrin ağırlığını, həftəsonu yükünü, istirahət intervalını, əvvəlki aylardakı yükü və digər məhdudiyyətləri nəzərə alaraq mümkün qədər obyektiv və ədalətli növbə bölgüsü aparır.

---

## 📁 Faylın Quruluşu

Faylda aşağıdakı vərəqlər mövcuddur:

### 01. **DASHBOARD**
- **Məqsəd**: Ümumi vəziyyət, balans və xəbərdarlıqların izlənilməsi
- **Göstəricilər**: Cari ay və il, Ayın gün sayı, Aktiv şəxs sayı, Ümumi növbə sayı, Dolu və boş növbələr, Yoxluqda olan şəxslər, Yük göstəriciləri, Risklər

### 02. **AYLIQ QRAFİK**
- **Məqsəd**: Əsas növbətçilik cədvəlini avtomatik olaraq yaratmaq və idarə etmək
- **İstifadə**: İl və ay seçin, sistem avtomatik olaraq həmin ayın bütün tarixlərini yaradacaq
- **Sütunlar**: №, Tarix (DD.MM.YYYY), Həftənin günü, Ay adı, 6 növbə sütunu

### 03. **ŞƏXSLƏR**
- **Məqsəd**: Bütün şəxslərin məlumat bazası
- **Sütunlar**: №, Soyad, Ad, Ata adı, Tam ad, Vəzifə, Aktiv/Aktiv deyil, Qeyd, 6 növbə uyğunluğu

### 04. **YOXDUR-MƏZUNİYYƏT**
- **Məqsəd**: Şəxslərin yoxluqlarını qeyd etmək
- **Sütunlar**: Şəxs, Səbəb, Başlanğıc tarixi, Gün sayı, Bitmə tarixi (avtomatik), Qeyd

### 05. **BALANS**
- **Məqsəd**: Şəxslərin növbə və xidmət yükünün ətraflı statistikası
- **Göstəricilər**: Ümumi növbə, Ümumi xidmət yükü, Mövcud gün, Normallaşdırılmış yük, Həftəsonu sayları, Növbə növləri, Son növbə

### 06. **PARAMETRLƏR**
- **Məqsəd**: Bütün sistem parametrləri və qaydaları
- **Qruplar**: Növbə əmsalları, İstirahət və qaydalar, Balans və ədalət

### 07. **DƏYİŞİKLİK JURNALI**
- **Məqsəd**: Əl ilə edilmiş dəyişikliklərin tarixçəsini saxlayır
- **Sütunlar**: Tarix, Saat, Növbə tarixi, Növbə növü, Əvvəlki şəxs, Yeni şəxs, Səbəb, Qeyd

---

## 🚀 İstifadə Qılavuzu

### Adım 1: Hazırlıq
1. Faylı Excel-də açın
2. PARAMETRLƏR vərəqində bütün qaydaları yoxlayın

### Adım 2: Şəxsləri Daxil Etmək
1. ŞƏXSLƏR vərəqinə keçin
2. Hər şəxs üçün məlumatları daxil edin
3. Növbə uyğunluğunu müəyyən edin

### Adım 3: Yoxluqları Qeyd Etmək
1. YOXDUR-MƏZUNİYYƏT vərəqinə keçin
2. Yoxluq məlumatlarını daxil edin

### Adım 4: Növbələri Planlaşdırmaq
1. AYLIQ QRAFİK vərəqinə keçin
2. İl və ay seçin
3. Növbələri əl ilə daxil edin

### Adım 5: Balansı Yoxlamaq
1. BALANS vərəqinə keçin
2. Yük göstəricilərini yoxlayın

### Adım 6: Dashboard-da Riskləri Yoxlamaq
1. DASHBOARD vərəqinə keçin
2. Ümumi vəziyyətə baxın

---

## ⚙️ Sistem Parametrləri

### Növbə Əmsalları
- Hissə növbətçisi: 5
- Köməkçi: 4
- NBM: 3
- Park: 3
- Yeməkxana: 2
- Otaq: 1

### İstirahət və Qaydalar
- Minimum istirahət intervalı: 1 gün
- Ardıcıl növbə limiti: 2
- Eyni növbə təkrar limiti: 3

### Balans və Ədalət
- Balans toleransı: 10%
- Əvvəlki ayların təsir əmsalı: 0.3
- Həftəsonu əmsalı: 1.5

---

## 📊 Hesablama Formulları

### Xidmət Yükü
```
Xidmət Yükü = Σ (Növbə sayı × Növbə əmsalı)
```

### Normallaşdırılmış Yük
```
Normallaşdırılmış Yük = Xidmət Yükü / Mövcud Gün Sayı
```

---

## 🎯 Ədalət Prinsipləri

1. Ümumi yük fərqini minimuma endir
2. Həftəsonu yük fərqini minimuma endir
3. Son aylardakı yük fərqini minimuma endir
4. Ardıcıl növbələri minimuma endir
5. Eyni növbənin təkrarını minimuma endir
6. İstirahət intervalını qoru

---

## ⚠️ Xəbərdarlıqlar

- 🔴 Yoxluqda olan şəxsə növbə
- 🔴 Uyğun olmayan şəxs
- ⚠️ İstirahət qaydasının pozulması
- ⚠️ Ardıcıl növbə
- ⚠️ Həddindən artıq həftəsonu yükü
- 🟡 Boş növbə

---

## 🔧 Data Validation

- ŞƏXSLƏR: Aktivlik, Növbə uyğunluğu
- YOXDUR-MƏZUNİYYƏT: Şəxs, Səbəb
- AYLIQ QRAFİK: İl, Ay, Növbə sütunları
- DƏYİŞİKLİK JURNALI: Növbə növü, Səbəb

---

## 🎨 Şərti Formatlaşdırma

| Rəng | Məna |
|------|------|
| 🟢 Yaşıl | Qaydalara uyğundur |
| 🟡 Sarı | Diqqət tələb edir |
| 🔴 Qırmızı | Qayda pozuntusu |
| ⛔ | Təyin etmək olmaz |

---

## 📄 Çap Quraşdırması

- Format: A4/A3 (Landscape)
- Başlıqlar: Hər səhifədə təkrarlanır

---

## 🔐 Qoruma

- Qoruma parolu: `novbe123`
- Açıq hüceyrələr: PARAMETRLƏR (B sütunu), ŞƏXSLƏR, YOXDUR-MƏZUNİYYƏT, AYLIQ QRAFİK, DƏYİŞİKLİK JURNALI

---

## 🛠️ Texniki Xüsusiyyətlər

- Format: Excel (.xlsx)
- Kitabxana: openpyxl (Python)
- Dilə: Azərbaycan dili (UTF-8)
- Sistemin tələbləri: Microsoft Excel 2010+, LibreOffice Calc
- Makrolar: Tələb edilmir

---

## 🆘 Tez-Tez Verilən Suallar

### Sual: Faylı açarkən "Qoruma" xəbərdarlığı alıram. Nə etmək lazımdır?
**Cavab**: "Düzəliş et" (Edit) seçin və parol olaraq `novbe123` daxil edin.

### Sual: Niyə bəzi şəxslər növbəyə təyin edilmir?
**Cavab**: Şəxs aktiv deyil, yoxluqdadır və ya həmin növbəyə uyğun deyil.

### Sual: Bitmə tarixi niyə avtomatik hesablanmır?
**Cavab**: YOXDUR-MƏZUNİYYƏT vərəqində avtomatik hesablanır (Başlanğıc + Gün sayı - 1).

---

## 📝 Versiya Tarixçəsi

- **v1.0** (Sentyabr 2026): İlk buraxılış

---

**Son yeniləmə**: Sentyabr 2026
**Hazırlayan**: Vibe Code (Mistral AI)
**Lisenziya**: Açıq mənbə (Open Source)
