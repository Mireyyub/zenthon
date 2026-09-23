# VBA Modulları - İstifadə Təlimatı

## 🎯 Ümumi Məqsəd

Bu sənəd **Aylıq Növbətçilik Planlaşdırma Sistemi v2.0** üçün VBA modullarının necə qurulmasını və istifadə olunanını izah edir.

---

## 📦 Təmin Edilən Fayllar

| Fayl | Məqsəd | Ölçü |
|------|--------|------|
| `Module1.bas` | Əsas funksiya (GenerateSchedule) | 2.3 KB |
| `Module2.bas` | Yoxlama və köməkçi funksiya | 5.6 KB |
| `Module3.bas` | Köməkçi funksiya (uzun) | 10 KB |
| `README.md` | Ümumi məlumat | 5 KB |

---

## 🚀 Qurulma Qılavuzu

### Tələb Olunanlar
- ✅ **Microsoft Excel 2010 və ya daha yeni**
- ✅ **Makroların icazə verilməsi**
- ✅ **Excel Macro-Enabled Workbook (*.xlsm) formatı**

---

### Adım 1: Excel Faylını Hazırla

1. **`Novbe_Sistemi.xlsx`** faylını açın
2. **File → Save As** seçin
3. **"Excel Macro-Enabled Workbook (*.xlsm)"** formatını seçin
4. Faylı **`Novbe_Sistemi_v2.xlsm`** adı ilə saxlayın

---

### Adım 2: VBA Editor-u Açın

1. **Excel pəncərəsində** `Alt + F11` düyməsinə basın
   - Və ya **Developer → Visual Basic** seçin
2. **VBA Editor** pəncərəsi açılacaq

> ⚠️ **Qeyd**: Əgər **Developer** tabı görünmürsə:
> - **File → Options → Customize Ribbon**
> - **Developer** checkbox-u işarələyin
> - OK düyməsinə basın

---

### Adım 3: Modulları Import Edin

#### Module1.bas (Əsas Funksiya)

1. VBA Editor-da **Insert → Module** seçin
2. Açılan boş modulda aşağıdakı kodu kopyalayın:

```vba
' Module1.bas faylının məzmunu
Option Explicit

Public Sub GenerateSchedule()
    ' Növbələri avtomatik olaraq yaradır
    Application.ScreenUpdating = False
    
    ' ... (qalan kod)
    
    MsgBox "Növbələr avtomatik olaraq yaradıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub
```

3. **Ctrl+S** ilə saxlayın

---

#### Module2.bas (Yoxlama Funksiya)

1. Yenə **Insert → Module** seçin
2. Açılan boş modulda `Module2.bas` faylının məzmununu kopyalayın
3. **Ctrl+S** ilə saxlayın

---

#### Module3.bas (Köməkçi Funksiya)

1. Yenə **Insert → Module** seçin
2. Açılan boş modulda `Module3.bas` faylının məzmununu kopyalayın
3. **Ctrl+S** ilə saxlayın

---

## 🎛️ Düymələrin Yaratılması

### AYLIQ QRAFİK vərəqində düymələr:

#### 1. "NÖVBƏLƏRİ YARAT" Düyməsi

1. **Developer** tabında **Insert → Button (Form Control)** seçin
2. **AYLIQ QRAFİK** vərəqində düyməni yerləşdirin (məsələn, **G4** hüceyrəsində)
3. Açılan pəncərədə **"New"** seçin
4. Aşağıdakı kodu yazın:

```vba
Private Sub CommandButton1_Click()
    Call GenerateSchedule
End Sub
```

5. Düymənin adını dəyişin:
   - Düyməyə sağ klik edin
   - **"Edit Text"** seçin
   - Adını **"NÖVBƏLƏRİ YARAT"** olaraq dəyişin

---

#### 2. "YOXLAYIN" Düyməsi

1. **Developer → Insert → Button** seçin
2. Düyməni **H4** hüceyrəsində yerləşdirin
3. **"New"** seçin
4. Aşağıdakı kodu yazın:

```vba
Private Sub CommandButton2_Click()
    Call ValidateSchedule
End Sub
```

5. Adını **"YOXLAYIN"** olaraq dəyişin

---

#### 3. "SIFIRLA" Düyməsi

1. **Developer → Insert → Button** seçin
2. Düyməni **G5** hüceyrəsində yerləşdirin
3. **"New"** seçin
4. Aşağıdakı kodu yazın:

```vba
Private Sub CommandButton3_Click()
    Call ClearSchedule
End Sub
```

5. Adını **"SIFIRLA"** olaraq dəyişin

---

#### 4. "PDF" Düyməsi

1. **Developer → Insert → Button** seçin
2. Düyməni **H5** hüceyrəsində yerləşdirin
3. **"New"** seçin
4. Aşağıdakı kodu yazın:

```vba
Private Sub CommandButton4_Click()
    Call ExportToPDF
End Sub
```

5. Adını **"PDF"** olaraq dəyişin

---

## 🔧 Makroları İcazə Verin

### Üsul 1: Trust Center (Tövsiyə olunur)

1. Excel-də **File → Options** seçin
2. **Trust Center** seçin
3. **"Trust Center Settings..."** düyməsinə basın
4. **Macro Settings** seçin
5. **"Enable all macros"** seçin
6. OK düyməsinə basın

---

### Üsul 2: Fayl üçün (Müvəqqəti)

1. Faylı açarkən **"Enable Macros"** düyməsinə basın
2. Və ya **"Enable Content"** düyməsinə basın

---

## ✅ Sistemin Test Edilməsi

### Test 1: Avtomatik Növbə Generasiyası
1. **AYLIQ QRAFİK** vərəqində il və ay seçin
2. **"NÖVBƏLƏRİ YARAT"** düyməsinə basın
3. **Nəticə**: Bütün növbələr avtomatik olaraq doldurulmalıdır

---

### Test 2: Cədvəl Yoxlanması
1. **AYLIQ QRAFİK** vərəqində bəzi növbələri əl ilə dəyişin
2. **"YOXLAYIN"** düyməsinə basın
3. **Nəticə**: Qayda pozuntuları haqqında mesaj almalısınız

---

### Test 3: Cədvəl Sıfırlanması
1. **"SIFIRLA"** düyməsinə basın
2. **Nəticə**: Bütün növbə sütunları boşalmalıdır

---

### Test 4: PDF İxracı
1. **"PDF"** düyməsinə basın
2. **Nəticə**: PDF faylı avtomatik olaraq yaradılmalı və açılmalıdır

---

## 📊 Funksiya Açıqlaması

### GenerateSchedule()
**Məqsəd**: Avtomatik növbə generasiyası

**Nə edir**:
- Parametrləri oxuyur
- Aktiv şəxsləri tapır
- Yoxluq tarixlərini nəzərə alır
- Hər növbə üçün random şəxs seçir
- Cədvəli doldurur

**İstifadə**:
```vba
Call GenerateSchedule
```

---

### ValidateSchedule()
**Məqsəd**: Cədvəli yoxlamaq

**Nə edir**:
- Yoxluqda olan şəxsləri yoxlayır
- Növbə uyğunluğunu yoxlayır
- İstirahət qaydalarını yoxlayır
- Boş növbələri tapır
- Problemləri siyahı şəklində göstərir

**İstifadə**:
```vba
Call ValidateSchedule
```

---

### ClearSchedule()
**Məqsəd**: Cədvəli sıfırlamaq

**Nə edir**:
- Bütün növbə sütunlarını boşaldır
- Tarix sütunlarını yeniləyir

**İstifadə**:
```vba
Call ClearSchedule
```

---

### ExportToPDF()
**Məqsəd**: Cədvəli PDF olaraq ixrac etmək

**Nə edir**:
- AYLIQ QRAFİK vərəqini PDF olaraq ixrac edir
- Faylı avtomatik olaraq açır

**İstifadə**:
```vba
Call ExportToPDF
```

---

## 🎨 Düymələrin Formatlaşdırılması

### Düymələrin Ölçüləri
| Düymə | Yeri | Ölçü |
|-------|------|------|
| NÖVBƏLƏRİ YARAT | G4 | 100x30 |
| YOXLAYIN | H4 | 100x30 |
| SIFIRLA | G5 | 100x30 |
| PDF | H5 | 100x30 |

### Düymələrin Rəngləri
- **NÖVBƏLƏRİ YARAT**: Yaşıl (4472C4)
- **YOXLAYIN**: Sarı (FFC000)
- **SIFIRLA**: Qırmızı (FF0000)
- **PDF**: Gøy (00B0F0)

---

## ⚠️ Mümkün Problemler və Həlləri

### Problem 1: "Macros are disabled" xəbərdarlığı
**Səbəb**: Makrolar icazə verilməyib
**Həll**: Trust Center-dən makroları icazə verin

---

### Problem 2: Düymələr işləmir
**Səbəb**: Düymə **"Form Control"** deyil, **"ActiveX Control"**
**Həll**: Düyməni silin və yenidən **Form Control** olaraq yaratın

---

### Problem 3: VBA Editor-da "Compile Error"
**Səbəb**: Modulların birində sintaksis xətası
**Həll**: Xəta mesajında göstərilən sətirə baxın və düzelin

---

### Problem 4: Fayl açılanda "Security Warning"
**Səbəb**: Fayl ***.xlsx*** formatındadır
**Həll**: Faylı ***.xlsm*** formatında saxlayın

---

### Problem 5: Random alqoritm ədalətsizdir
**Səbəb**: Sadə random seçim istifadə olunur
**Həll**: Module3.bas-dakı `GenerateScheduleForNovbeType` funksiyasını təkmilləşdirin

---

## 🔧 Təkmilləşdirmə İmkānları

### 1. Ağıllı Alqoritm
Module3.bas-dakı `GenerateScheduleForNovbeType` funksiyasını aşağıdakı kimi dəyişin:

```vba
Private Sub GenerateScheduleForNovbeType(...)
    ' Yük balansını nəzərə al
    ' Həftəsonu yükünü nəzərə al
    ' İstirahət qaydalarını nəzərə al
    ' ...
End Sub
```

### 2. Progress Bar
**UserForm** ilə progress bar əlavə edin:

```vba
' UserForm-da
Private Sub UserForm_Initialize()
    ProgressBar1.Min = 0
    ProgressBar1.Max = 100
    Label1.Caption = "Növbələr yaradılır..."
End Sub

' GenerateSchedule-də
ProgressBar1.Value = (day / numDays) * 100
DoEvents
```

### 3. Avtomatik Yeniləmə
Workspace_Change eventindən istifadə edin:

```vba
Private Sub Worksheet_Change(ByVal Target As Range)
    ' Növbə sütunlarında dəyişiklik olarsa
    If Not Intersect(Target, Range("E8:J37")) Is Nothing Then
        Call ValidateSchedule
    End If
End Sub
```

---

## 📝 Xatırlatmalar

1. **Faylı daim *.xlsm formatında saxlayın**
2. **Makroları icazə verin**
3. **VBA Editor-da bütün modulların düzgün import edildiyini yoxlayın**
4. **Düymələrin "Form Control" tipində olduğuna əmin olun**
5. **Test edərək yoxlayın**

---

## 🎉 Nəticə

✅ **Təkmilləşdirilmiş Aylıq Növbətçilik Sistemi** hazırdır!

**Nə əldə etdik:**
- Avtomatik növbə generasiyası
- Cədvəl yoxlanması
- Cədvəl sıfırlanması
- PDF ixracı
- Interaktiv düymələr

---

## 📞 Əlaqə

Əgər sualınız varsa:
- VBA kodlarını yoxlayın
- Excel versiyasını yoxlayın
- Makroların icazə verildiyini yoxlayın
- Bu sənədə baxın

---

**Son yeniləmə**: Sentyabr 2026
**Hazırlayan**: Vibe Code (Mistral AI)
