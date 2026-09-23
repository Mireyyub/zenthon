# VBA Modulları - Aylıq Növbətçilik Sistemi v2.0

## 📋 Ümumi Məqsəd

Bu folderdə **Excel VBA** kodları yerləşir ki, **Aylıq Növbətçilik Planlaşdırma Sistemi**ni interaktiv və avtomatik şəkildə işlətmək üçün nəzərdə tutulub.

---

## 📁 Fayllar

| Fayl | Məqsəd | Status |
|------|--------|--------|
| **Module1.bas** | Əsas funksiya (GenerateSchedule) | ✅ Hazır |
| **Module2.bas** | Yoxlama və köməkçi funksiya | ✅ Hazır |
| **Module3.bas** | Köməkçi funksiya (uzun) | ✅ Hazır |

---

## 🚀 İstifadə Qılavuzu

### Adım 1: Excel Faylını Açın
1. `Novbe_Sistemi.xlsx` faylını **Microsoft Excel 2010+**-də açın
2. **Alt+F11** düyməsinə basın (VBA Editor açılacaq)

### Adım 2: Modulları Import Edin

#### Module1.bas
1. VBA Editor-da **Insert → Module** seçin
2. Açılan boş modulda `Module1.bas` faylının məzmununu kopyalayın və yapışdırın

#### Module2.bas
1. Yenə **Insert → Module** seçin
2. Açılan boş modulda `Module2.bas` faylının məzmununu kopyalayın və yapışdırın

#### Module3.bas
1. Yenə **Insert → Module** seçin
2. Açılan boş modulda `Module3.bas` faylının məzmununu kopyalayın və yapışdırın

---

## 🎯 Funksiya Açıqlaması

### Module1.bas
- **`GenerateSchedule()`** - Növbələri avtomatik olaraq yaradır
  - Parametrləri oxuyur
  - Aktiv şəxsləri tapır
  - Yoxluq tarixlərini nəzərə alır
  - Hər növbə üçün ən uyğun şəxsi seçir
  - Cədvəli doldurur

### Module2.bas
- **`ValidateSchedule()`** - Cədvəli yoxlayır və qayda pozuntularını göstərir
  - Yoxluqda olan şəxsləri yoxlayır
  - Növbə uyğunluğunu yoxlayır
  - İstirahət qaydalarını yoxlayır
  - Boş növbələri tapır

- **`ClearSchedule()`** - Cədvəli sıfırlayır

- **`ExportToPDF()`** - Cədvəli PDF olaraq ixrac edir

- **`ShowHelp()`** - Kömək mesajını göstərir

### Module3.bas
- **`GetParameters()`** - Parametrləri oxuyur
- **`GetActivePeople()`** - Aktiv şəxsləri tapır
- **`GetAbsenceDates()`** - Yoxluq tarixlərini oxuyur
- **`GetMonthNumber()`** - Ay adını nömrəyə çevirir
- **`IsPersonAbsent()`** - Şəxsin yoxluqda olub-olmadığını yoxlayır
- **`IsPersonSuitable()`** - Şəxsin növbəyə uyğun olub-olmadığını yoxlayır
- **`GetLastNovbeDate()`** - Şəxsin son növbə tarixini tapır
- **`GenerateScheduleForNovbeType()`** - Mühüm növbə üçün cədvəli yaradır
- **`GetHefteGunu()`** - Tarixə əsasən həftə gününü tapır

---

## 🔧 Düymələrin Yaratılması

### AYLIQ QRAFİK vərəqində düymələr:

#### 1. NÖVBƏLƏRİ YARAT düyməsi
```vba
Private Sub CommandButton1_Click()
    Call GenerateSchedule
End Sub
```

#### 2. YOXLAYIN düyməsi
```vba
Private Sub CommandButton2_Click()
    Call ValidateSchedule
End Sub
```

#### 3. SIFIRLA düyməsi
```vba
Private Sub CommandButton3_Click()
    Call ClearSchedule
End Sub
```

#### 4. PDF düyməsi
```vba
Private Sub CommandButton4_Click()
    Call ExportToPDF
End Sub
```

---

## ⚙️ Təhlükəsizlik

### Makroları İcazə Verin
1. Excel-də **File → Options → Trust Center → Trust Center Settings**
2. **Macro Settings** seçin
3. **"Enable all macros"** seçin (və ya **"Disable all macros with notification"**)
4. OK düyməsinə basın

### Faylı Saxlayın
1. **File → Save As**
2. **Excel Macro-Enabled Workbook (*.xlsm)** seçin
3. Faylı `Novbe_Sistemi_v2.xlsm` adı ilə saxlayın

---

## 📝 Qeydlər

1. **VBA kodları** sadəcə **Excel 2010 və ya daha yeni versiyalarda** işləyir
2. **Makrolar tələb edir**
3. **Fayl artıq `.xlsm` formatında olmalıdır**
4. **Random alqoritm** istifadə olunur (sadə versiya)
5. **Daha mürəkkəb alqoritm** üçün Module3.bas-dakı `GenerateScheduleForNovbeType` funksiyasını təkmilləşdirin

---

## 🎯 Növbəti Addımlar

### 1. Düzəlişlər
- [ ] **Random alqoritm** → **Ağıllı alqoritm** (Module3.bas)
- [ ] **Həftəsonu balansı** nəzərə almaq
- [ ] **Yük bərabərliyi** nəzərə almaq

### 2. Əlavə Funksiya
- [ ] **Avtomatik yeniləmə** (Workspace_Change event)
- [ ] **Şəxs dəyişdirmə** interfeysi
- [ ] **Statistika hesablama**

### 3. Təkmilləşdirmə
- [ ] **UserForm** ilə interaktiv interfeys
- [ ] **Progress bar** göstərilməsi
- [ ] **Xəta mesajları** təkmilləşdirmə

---

## 💡 Məsələlər və Həlləri

### Sual: "Macros are disabled" xəbərdarlığı alıram
**Cavab**: Makroları icazə verin (Trust Center Settings)

### Sual: Düymələr işləmir
**Cavab**: Düymələrin **Macro** tipində olduğuna əmin olun

### Sual: VBA Editor-da xəta alıram
**Cavab**: Bütün modulların düzgün import edildiyini yoxlayın

### Sual: Fayl açılanda xəta alıram
**Cavab**: Faylı `.xlsm` formatında saxlayın

---

## 📞 Əlaqə

Əgər sualınız varsa:
- VBA kodlarını yoxlayın
- Excel versiyasını yoxlayın
- Makroların icazə verildiyini yoxlayın

---

**Son yeniləmə**: Sentyabr 2026
**Hazırlayan**: Vibe Code (Mistral AI)
