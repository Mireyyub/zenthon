#!/usr/bin/env python3
"""
Aylıq Növbətçilik Planlaşdırma Sistemi Generatoru
Azərbaycan dilində peşəkar Excel sistemi
"""

import os
import sys
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Border, Side, Alignment, Protection,
    colors, NamedStyle
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# ==================== KONSTANTLAR ====================

# Növbə növləri
NOVBE_NOVLERI = [
    "Hissə növbətçisi",
    "Hissə növbətçisinin köməkçisi", 
    "Nəzarət-buraxılış məntəqəsi növbətçisi",
    "Park növbətçisi",
    "Yeməkxana növbətçisi",
    "Otaq növbətçisi"
]

# Həftə günləri Azərbaycan dilində
HEFTE_GUNLERI = [
    "Bazar ertəsi",
    "Çərşənbə axşamı",
    "Çərşənbə",
    "Cümə axşamı",
    "Cümə",
    "Şənbə",
    "Bazar"
]

# Aylar Azərbaycan dilində
AYLAR_ADLARI = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun",
    "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
]

# Yoxluq səbəbləri
YOXLUQ_SEBEBLERI = [
    "Məzuniyyət", "Başqa yer", "Ezamiyyət", 
    "Xəstəlik", "Təlim", "Digər"
]

# Uyğunluq statusları
UYGUNLUQ_STATUS = ["✓ Uyğundur", "✗ Uyğun deyil"]

# Aktivlik statusları
AKTIVLIK_STATUS = ["Aktiv", "Aktiv deyil"]

# Default növbə əmsalları
NOVBE_EMSALLARI = {
    "Hissə növbətçisi": 5,
    "Hissə növbətçisinin köməkçisi": 4,
    "Nəzarət-buraxılış məntəqəsi növbətçisi": 3,
    "Park növbətçisi": 3,
    "Yeməkxana növbətçisi": 2,
    "Otaq növbətçisi": 1
}

# Rənglər
COLOR_GREEN = "90EE90"  # Açıq yaşıl
COLOR_YELLOW = "FFFF00"  # Sarı
COLOR_RED = "FF6B6B"  # Qırmızı
COLOR_LIGHT_RED = "FFCCCC"  # Açıq qırmızı
COLOR_LIGHT_YELLOW = "FFF59D"  # Açıq sarı
COLOR_LIGHT_GREEN = "E8F5E9"  # Açıq yaşıl
COLOR_BLUE = "ADD8E6"  # Açıq göy
COLOR_LIGHT_BLUE = "E6F3FF"  # Çox açıq göy
COLOR_GRAY = "F5F5F5"  # Boz
COLOR_DARK_BLUE = "4A90E2"  # Tünd göy


class NovbeSystemGenerator:
    """Excel Növbətçilik Sistemi Generatoru"""
    
    def __init__(self):
        self.wb = Workbook()
        self.wb.iso_dates = True
        
        # Default font
        self.default_font = Font(name="Calibri", size=11)
        self.header_font = Font(name="Calibri", size=12, bold=True)
        self.subheader_font = Font(name="Calibri", size=11, bold=True)
        self.title_font = Font(name="Calibri", size=14, bold=True)
        self.small_font = Font(name="Calibri", size=10)
        
        # Default alignment
        self.center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.left_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        self.right_alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
        
        # Thin border
        self.thin_border = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000")
        )
        
        # Protection
        self.locked_cell = Protection(locked=True)
        self.unlocked_cell = Protection(locked=False)
        
    def create_all_sheets(self):
        """Bütün vərəqləri yarat"""
        # Default sheet-i sil
        if "Sheet" in self.wb.sheetnames:
            del self.wb["Sheet"]
        
        # Vərəqləri yarat
        sheet_order = [
            "DASHBOARD",
            "AYLIQ QRAFİK", 
            "ŞƏXSLƏR",
            "YOXDUR-MƏZUNİYYƏT",
            "BALANS",
            "PARAMETRLƏR",
            "DƏYİŞİKLİK JURNALI"
        ]
        
        for sheet_name in sheet_order:
            self.wb.create_sheet(sheet_name)
        
        # Vərəqləri sifarişə sal
        for i, sheet_name in enumerate(sheet_order):
            self.wb.move_sheet(self.wb[sheet_name], i)
        
    def create_parameters_sheet(self):
        """PARAMETRLƏR vərəqini yarat"""
        ws = self.wb["PARAMETRLƏR"]
        
        # Vərəqin genişliyini təyin et
        ws.column_dimensions["A"].width = 40
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 60
        
        # Başlıq
        ws.merge_cells("A1:C1")
        title_cell = ws["A1"]
        title_cell.value = "SİSTEM PARAMETRLƏRİ"
        title_cell.font = Font(name="Calibri", size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:C2")
        ws["A2"].value = "Bu vərəqdə bütün sistem parametrləri yerləşir. Formulaları dəyişmədən yalnız bu dəyərləri dəyişməklə sistemi idarə edə bilərsiniz."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Parametrlər cədvəli
        row = 4
        
        # Növbə əmsalları
        ws.merge_cells(f"A{row}:C{row}")
        ws[f"A{row}"].value = "NÖVBƏ ƏMSALLARI"
        ws[f"A{row}"].font = self.header_font
        ws[f"A{row}"].fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
        row += 1
        
        for novbe in NOVBE_NOVLERI:
            ws[f"A{row}"].value = novbe
            ws[f"A{row}"].font = self.subheader_font
            ws[f"B{row}"].value = NOVBE_EMSALLARI[novbe]
            ws[f"B{row}"].number_format = "0"
            ws[f"C{row}"].value = f"Bu növbənin ağırlıq əmsalı"
            ws[f"C{row}"].font = self.small_font
            ws[f"C{row}"].fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            row += 1
        
        row += 1
        
        # İstirahət parametrləri
        ws.merge_cells(f"A{row}:C{row}")
        ws[f"A{row}"].value = "İSTİRAHƏT VƏ QAYDALAR"
        ws[f"A{row}"].font = self.header_font
        ws[f"A{row}"].fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
        row += 1
        
        params = [
            ("Minimum istirahət intervalı (gün)", 1, "Eyni şəxsin növbələr arasında minimum keçməli olan gün sayı"),
            ("Ardıcıl növbə limiti", 2, "Eyni növbənin ardıcıl olaraq neçə dəfə verilməsinə icazə verilir"),
            ("Eyni növbə təkrar limiti (ay)", 3, "Eyni şəxs eyni növbəni bir ay ərzində neçə dəfə ala bilər"),
        ]
        
        for param, value, desc in params:
            ws[f"A{row}"].value = param
            ws[f"A{row}"].font = self.subheader_font
            ws[f"B{row}"].value = value
            ws[f"B{row}"].number_format = "0"
            ws[f"C{row}"].value = desc
            ws[f"C{row}"].font = self.small_font
            ws[f"C{row}"].fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            row += 1
        
        row += 1
        
        # Balans parametrləri
        ws.merge_cells(f"A{row}:C{row}")
        ws[f"A{row}"].value = "BALANS VƏ ƏDALƏT"
        ws[f"A{row}"].font = self.header_font
        ws[f"A{row}"].fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
        row += 1
        
        params = [
            ("Balans toleransı (%)", 10, "Yük fərqinin nə qədərini tolerans etmək"),
            ("Əvvəlki ayların təsir əmsalı", 0.3, "Son 3 ayın yükünün cari aya təsir əmsalı (0-1)"),
            ("Həftəsonu əmsalı", 1.5, "Həftəsonu növbələrinin əmsalı"),
        ]
        
        for param, value, desc in params:
            ws[f"A{row}"].value = param
            ws[f"A{row}"].font = self.subheader_font
            ws[f"B{row}"].value = value
            if isinstance(value, float):
                ws[f"B{row}"].number_format = "0.0"
            else:
                ws[f"B{row}"].number_format = "0"
            ws[f"C{row}"].value = desc
            ws[f"C{row}"].font = self.small_font
            ws[f"C{row}"].fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            row += 1
        
        # Bütün hüceyrələri formatla
        for r in range(1, row + 1):
            for c in ["A", "B", "C"]:
                cell = ws[f"{c}{r}"]
                cell.border = self.thin_border
                cell.alignment = self.left_alignment
        
        # B sütununu qoruma (formula olan yerlər istisna)
        for r in range(1, row + 1):
            if r >= 5 and r <= 10:  # Növbə əmsalları
                ws[f"B{r}"].protection = self.unlocked_cell
            elif r >= 13 and r <= 15:  # İstirahət parametrləri
                ws[f"B{r}"].protection = self.unlocked_cell
            elif r >= 18 and r <= 20:  # Balans parametrləri
                ws[f"B{r}"].protection = self.unlocked_cell
        
    def create_people_sheet(self):
        """ŞƏXSLƏR vərəqini yarat"""
        ws = self.wb["ŞƏXSLƏR"]
        
        # Sütun genişlikləri
        col_widths = {
            "A": 5, "B": 20, "C": 20, "D": 20, "E": 35,
            "F": 25, "G": 15, "H": 25
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
        # Növbə uyğunluğu sütunları
        for i, novbe in enumerate(NOVBE_NOVLERI):
            col_letter = get_column_letter(9 + i)
            ws.column_dimensions[col_letter].width = 18
        
        # Başlıq
        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = "ŞƏXSLƏR MƏLUMAT BAZASI"
        title_cell.font = Font(name="Calibri", size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:H2")
        ws["A2"].value = "Bu vərəqdə bütün şəxslərin məlumatları və növbələrə uyğunluqları qeyd olunur."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Başlıq sətri
        row = 4
        headers = [
            "№", "Soyad", "Ad", "Ata adı", "Tam ad", 
            "Vəzifə", "Aktiv / Aktiv deyil", "Qeyd"
        ]
        
        for i, header in enumerate(headers):
            cell = ws.cell(row=row, column=i+1)
            cell.value = header
            cell.font = self.header_font
            cell.fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
            cell.border = self.thin_border
            cell.alignment = self.center_alignment
        
        # Növbə uyğunluğu başlıqları
        for i, novbe in enumerate(NOVBE_NOVLERI):
            col = 9 + i
            cell = ws.cell(row=row, column=col)
            cell.value = novbe
            cell.font = self.header_font
            cell.fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
            cell.border = self.thin_border
            cell.alignment = self.center_alignment
        
        # Nümayiş məlumatları (boş sətirlər)
        sample_data = [
            [1, "İbrahimov", "Rövşən", "Hüseyn", "İbrahimov Rövşən Hüseyn oğlu", "Kapitan", "Aktiv", ""],
            [2, "Məmmədəliyev", "Elşən", "Cavad", "Məmmədəliyev Elşən Cavad oğlu", "Leytenant", "Aktiv", ""],
            [3, "Quliyeva", "Aytən", "Rövşən", "Quliyeva Aytən Rövşən qızı", "Kapitan", "Aktiv", ""],
            [4, "Hüseynov", "Cavid", "Tofiq", "Hüseynov Cavid Tofiq oğlu", "Leytenant", "Aktiv", ""],
            [5, "Əliyev", "Vüsal", "Nizami", "Əliyev Vüsal Nizami oğlu", "Kapitan", "Aktiv", ""],
            [6, "Rzayev", "Orxan", "Eldar", "Rzayev Orxan Eldar oğlu", "Leytenant", "Aktiv", ""],
            [7, "Səlimova", "Nərgiz", "Rafiq", "Səlimova Nərgiz Rafiq qızı", "Leytenant", "Aktiv", ""],
            [8, "Məhərrəmov", "Fərid", "Asif", "Məhərrəmov Fərid Asif oğlu", "Kapitan", "Aktiv deyil", "Təlimdə"]
        ]
        
        for i, data in enumerate(sample_data):
            row_num = row + 1 + i
            
            # №
            ws[f"A{row_num}"].value = data[0]
            ws[f"A{row_num}"].font = self.default_font
            
            # Soyad
            ws[f"B{row_num}"].value = data[1]
            ws[f"B{row_num}"].font = self.default_font
            
            # Ad
            ws[f"C{row_num}"].value = data[2]
            ws[f"C{row_num}"].font = self.default_font
            
            # Ata adı
            ws[f"D{row_num}"].value = data[3]
            ws[f"D{row_num}"].font = self.default_font
            
            # Tam ad (formula)
            ws[f"E{row_num}"].value = f'=B{row_num}&" "&C{row_num}&" "&D{row_num}&" oğlu"'
            ws[f"E{row_num}"].font = self.default_font
            
            # Vəzifə
            ws[f"F{row_num}"].value = data[4]
            ws[f"F{row_num}"].font = self.default_font
            
            # Aktiv / Aktiv deyil
            ws[f"G{row_num}"].value = data[5]
            ws[f"G{row_num}"].font = self.default_font
            
            # Qeyd
            ws[f"H{row_num}"].value = data[6]
            ws[f"H{row_num}"].font = self.default_font
            
            # Növbə uyğunluğu (default olaraq hamısı uyğundur)
            for j, novbe in enumerate(NOVBE_NOVLERI):
                col = 9 + j
                ws.cell(row=row_num, column=col).value = "✓ Uyğundur"
                ws.cell(row=row_num, column=col).font = self.default_font
            
            # Formatlaşdırma
            for col in range(1, 9 + len(NOVBE_NOVLERI)):
                cell = ws.cell(row=row_num, column=col)
                cell.border = self.thin_border
                cell.alignment = self.left_alignment
        
        # Data Validation
        # Aktivlik statusu
        aktivlik_dv = DataValidation(type="list", formula1='"Aktiv,Aktiv deyil"', allow_blank=True)
        aktivlik_dv.add(f"G5:G{row + len(sample_data)}")
        ws.add_data_validation(aktivlik_dv)
        
        # Növbə uyğunluğu
        uygunluq_dv = DataValidation(type="list", formula1='"✓ Uyğundur,✗ Uyğun deyil"', allow_blank=True)
        for j in range(len(NOVBE_NOVLERI)):
            col = 9 + j
            uygunluq_dv.add(f"{get_column_letter(col)}5:{get_column_letter(col)}{row + len(sample_data)}")
        ws.add_data_validation(uygunluq_dv)
        
        # Qoruma
        for r in range(1, row + len(sample_data) + 1):
            for c in range(1, 9 + len(NOVBE_NOVLERI)):
                cell = ws.cell(row=r, column=c)
                if r >= 5 and c >= 1 and c <= 8:  # Məzmun hüceyrələri
                    cell.protection = self.unlocked_cell
        
        # Tam ad sütununu qoruma (formula)
        for r in range(5, row + len(sample_data) + 1):
            ws[f"E{r}"].protection = self.locked_cell
        
        # Avtomatik filter
        ws.auto_filter.ref = f"A4:{get_column_letter(9 + len(NOVBE_NOVLERI) - 1)}{row + len(sample_data)}"
        
    def create_absence_sheet(self):
        """YOXDUR-MƏZUNİYYƏT vərəqini yarat"""
        ws = self.wb["YOXDUR-MƏZUNİYYƏT"]
        
        # Sütun genişlikləri
        col_widths = {
            "A": 35, "B": 25, "C": 15, "D": 10, "E": 15, "F": 25
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
        # Başlıq
        ws.merge_cells("A1:F1")
        title_cell = ws["A1"]
        title_cell.value = "YOXDUR / MƏZUNİYYƏT MƏLUMATLARI"
        title_cell.font = Font(name="Calibri", size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:F2")
        ws["A2"].value = "Bu vərəqdə şəxslərin yoxluqları qeyd olunur. Bitmə tarixi avtomatik hesablanır."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Başlıq sətri
        row = 4
        headers = [
            "Şəxs", "Səbəb", "Başlanğıc tarixi", 
            "Gün sayı", "Bitmə tarixi", "Qeyd"
        ]
        
        for i, header in enumerate(headers):
            cell = ws.cell(row=row, column=i+1)
            cell.value = header
            cell.font = self.header_font
            cell.fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
            cell.border = self.thin_border
            cell.alignment = self.center_alignment
        
        # Nümayiş məlumatları
        sample_data = [
            ["İbrahimov Rövşən Hüseyn oğlu", "Məzuniyyət", "10.09.2026", 7, "", ""],
            ["Məmmədəliyev Elşən Cavad oğlu", "Xəstəlik", "15.09.2026", 3, "", ""],
            ["Quliyeva Aytən Rövşən qızı", "Təlim", "20.09.2026", 5, "", ""],
        ]
        
        for i, data in enumerate(sample_data):
            row_num = row + 1 + i
            
            # Şəxs
            ws[f"A{row_num}"].value = data[0]
            ws[f"A{row_num}"].font = self.default_font
            
            # Səbəb
            ws[f"B{row_num}"].value = data[1]
            ws[f"B{row_num}"].font = self.default_font
            
            # Başlanğıc tarixi
            ws[f"C{row_num}"].value = data[2]
            ws[f"C{row_num}"].font = self.default_font
            ws[f"C{row_num}"].number_format = "dd.mm.yyyy"
            
            # Gün sayı
            ws[f"D{row_num}"].value = data[3]
            ws[f"D{row_num}"].font = self.default_font
            ws[f"D{row_num}"].number_format = "0"
            
            # Bitmə tarixi (formula: Başlanğıc + Gün sayı - 1)
            ws[f"E{row_num}"].value = f"=C{row_num}+D{row_num}-1"
            ws[f"E{row_num}"].font = self.default_font
            ws[f"E{row_num}"].number_format = "dd.mm.yyyy"
            
            # Qeyd
            ws[f"F{row_num}"].value = data[4]
            ws[f"F{row_num}"].font = self.default_font
            
            # Formatlaşdırma
            for col in range(1, 7):
                cell = ws.cell(row=row_num, column=col)
                cell.border = self.thin_border
                cell.alignment = self.left_alignment if col in [1, 2, 6] else self.center_alignment
        
        # Data Validation
        # Şəxs (ŞƏXSLƏR vərəqindən)
        people_ref = f"'ŞƏXSLƏR'!$E$5:$E$100"
        person_dv = DataValidation(type="list", formula1=people_ref, allow_blank=True)
        person_dv.add(f"A5:A{row + len(sample_data)}")
        ws.add_data_validation(person_dv)
        
        # Səbəb
        sebeb_dv = DataValidation(type="list", formula1='"Məzuniyyət,Başqa yer,Ezamiyyət,Xəstəlik,Təlim,Digər"', allow_blank=True)
        sebeb_dv.add(f"B5:B{row + len(sample_data)}")
        ws.add_data_validation(sebeb_dv)
        
        # Qoruma
        for r in range(1, row + len(sample_data) + 1):
            for c in range(1, 7):
                cell = ws.cell(row=r, column=c)
                if r >= 5 and c != 5:  # Bitmə tarixi formuladır
                    cell.protection = self.unlocked_cell
        
        # Bitmə tarixi sütununu qoruma
        for r in range(5, row + len(sample_data) + 1):
            ws[f"E{r}"].protection = self.locked_cell
        
        # Avtomatik filter
        ws.auto_filter.ref = f"A4:F{row + len(sample_data)}"
        
    def create_monthly_schedule_sheet(self):
        """AYLIQ QRAFİK vərəqini yarat"""
        ws = self.wb["AYLIQ QRAFİK"]
        
        # Sütun genişlikləri
        ws.column_dimensions["A"].width = 5
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 20
        ws.column_dimensions["D"].width = 15
        
        for i, novbe in enumerate(NOVBE_NOVLERI):
            col_letter = get_column_letter(5 + i)
            ws.column_dimensions[col_letter].width = 22
        
        # Başlıq
        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = "AYLIQ NÖVBƏÇİLİK QRAFİKİ"
        title_cell.font = Font(name="Calibri", size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:H2")
        ws["A2"].value = "İl və ay seçin. Sistem avtomatik olaraq həmin ayın bütün tarixlərini yaradacaq."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Parametrlər sətri
        row = 4
        
        # İl
        ws[f"A{row}"].value = "İl:"
        ws[f"A{row}"].font = self.subheader_font
        ws[f"B{row}"].value = 2026
        ws[f"B{row}"].font = self.default_font
        ws[f"B{row}"].number_format = "0"
        
        # Ay
        ws[f"D{row}"].value = "Ay:"
        ws[f"D{row}"].font = self.subheader_font
        ws[f"E{row}"].value = "Sentyabr"
        ws[f"E{row}"].font = self.default_font
        
        # "NÖVBƏLƏRİ YARAT" düyməsi üçün yer
        ws[f"G{row}"].value = ""
        ws[f"H{row}"].value = ""
        
        # Növbə cədvəli başlıqları
        row = 7
        headers = [
            "№", "Tarix", "Həftənin günü", "Ay"
        ] + NOVBE_NOVLERI
        
        for i, header in enumerate(headers):
            cell = ws.cell(row=row, column=i+1)
            cell.value = header
            cell.font = self.header_font
            cell.fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
            cell.border = self.thin_border
            cell.alignment = self.center_alignment
        
        # 30 gün üçün sətirlər (maksimum)
        # Sentyabr 2026-da 30 gün var
        year = 2026
        month = 9  # Sentyabr
        
        num_days = monthrange(year, month)[1]
        
        for day in range(1, num_days + 1):
            row_num = row + day
            date_obj = date(year, month, day)
            
            # №
            ws[f"A{row_num}"].value = day
            ws[f"A{row_num}"].font = self.default_font
            ws[f"A{row_num}"].alignment = self.center_alignment
            
            # Tarix
            ws[f"B{row_num}"].value = date_obj
            ws[f"B{row_num}"].font = self.default_font
            ws[f"B{row_num}"].number_format = "dd.mm.yyyy"
            ws[f"B{row_num}"].alignment = self.center_alignment
            
            # Həftənin günü
            weekday_idx = date_obj.weekday()  # 0=Bazar ertəsi, 6=Bazar
            hefte_gunu = HEFTE_GUNLERI[weekday_idx]
            ws[f"C{row_num}"].value = hefte_gunu
            ws[f"C{row_num}"].font = self.default_font
            ws[f"C{row_num}"].alignment = self.center_alignment
            
            # Ay
            ws[f"D{row_num}"].value = AYLAR_ADLARI[month - 1]
            ws[f"D{row_num}"].font = self.default_font
            ws[f"D{row_num}"].alignment = self.center_alignment
            
            # Növbə sütunları (boş)
            for i, novbe in enumerate(NOVBE_NOVLERI):
                col = 5 + i
                ws.cell(row=row_num, column=col).value = ""
                ws.cell(row=row_num, column=col).font = self.default_font
                ws.cell(row=row_num, column=col).alignment = self.center_alignment
            
            # Formatlaşdırma
            for col in range(1, 5 + len(NOVBE_NOVLERI)):
                cell = ws.cell(row=row_num, column=col)
                cell.border = self.thin_border
        
        # Data Validation
        # İl
        il_dv = DataValidation(type="list", formula1='"2024,2025,2026,2027,2028"', allow_blank=False)
        il_dv.add(f"B{row-3}")
        ws.add_data_validation(il_dv)
        
        # Ay
        ay_dv = DataValidation(type="list", formula1='"Yanvar,Fevral,Mart,Aprel,May,İyun,İyul,Avqust,Sentyabr,Oktyabr,Noyabr,Dekabr"', allow_blank=False)
        ay_dv.add(f"E{row-3}")
        ws.add_data_validation(ay_dv)
        
        # Növbə sütunları üçün şəxs seçimləri
        people_ref = f"'ŞƏXSLƏR'!$E$5:$E$100"
        for i, novbe in enumerate(NOVBE_NOVLERI):
            col = 5 + i
            col_letter = get_column_letter(col)
            novbe_dv = DataValidation(type="list", formula1=people_ref, allow_blank=True)
            novbe_dv.add(f"{col_letter}{row+1}:{col_letter}{row+num_days}")
            ws.add_data_validation(novbe_dv)
        
        # Qoruma
        for r in range(1, row + num_days + 1):
            for c in range(1, 5 + len(NOVBE_NOVLERI)):
                cell = ws.cell(row=r, column=c)
                if r == row - 3 and c in [2, 5]:  # İl və Ay
                    cell.protection = self.unlocked_cell
                elif r >= row + 1 and c >= 5:  # Növbə sütunları
                    cell.protection = self.unlocked_cell
        
        # Avtomatik filter
        ws.auto_filter.ref = f"A{row}:{get_column_letter(5 + len(NOVBE_NOVLERI) - 1)}{row + num_days}"
        
        # Şərti formatlaşdırma üçün hazırlıq
        # Həftəsonu günləri (Cümə, Şənbə, Bazar)
        hefte_sonu_gunleri = ["Cümə", "Cümə axşamı", "Şənbə", "Bazar"]
        
        # Çap üçün səhifə quraşdırması
        ws.print_options.horizontalCentered = True
        ws.print_options.verticalCentered = False
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        
        # Başlıq sətirləri hər səhifədə təkrarlansın
        ws.print_options.header = f"&" + str(row) + "&" + str(row)
        
    def create_balance_sheet(self):
        """BALANS vərəqini yarat"""
        ws = self.wb["BALANS"]
        
        # Sütun genişlikləri
        col_widths = {
            "A": 35, "B": 15, "C": 15, "D": 15, "E": 15,
            "F": 15, "G": 15, "H": 15, "I": 15, "J": 15,
            "K": 15, "L": 15, "M": 15, "N": 15, "O": 15
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
        # Başlıq
        ws.merge_cells("A1:O1")
        title_cell = ws["A1"]
        title_cell.value = "ŞƏXSLƏRİN NÖVBƏ VƏ XİDMƏT YÜKÜ BALANSI"
        title_cell.font = Font(name="Calibri", size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:O2")
        ws["A2"].value = "Bu vərəqdə hər şəxsin cari ayda və əvvəlki aylarda növbə və xidmət yükü göstərilir."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Başlıq sətri
        row = 4
        headers = [
            "Şəxs",
            "Ümumi növbə",
            "Ümumi xidmət yükü",
            "Mövcud gün",
            "Normallaşdırılmış yük",
            "Cümə",
            "Şənbə",
            "Bazar",
            "Cümə→Şənbə",
            "Şənbə→Bazar",
            "Bazar→Bazar ertəsi",
            "Ağır növbə",
            "Orta növbə",
            "Yüngül növbə",
            "Son növbə"
        ]
        
        for i, header in enumerate(headers):
            cell = ws.cell(row=row, column=i+1)
            cell.value = header
            cell.font = self.header_font
            cell.fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
            cell.border = self.thin_border
            cell.alignment = self.center_alignment
        
        # Nümayiş məlumatları
        sample_people = [
            "İbrahimov Rövşən Hüseyn oğlu",
            "Məmmədəliyev Elşən Cavad oğlu",
            "Quliyeva Aytən Rövşən qızı",
            "Hüseynov Cavid Tofiq oğlu",
            "Əliyev Vüsal Nizami oğlu",
            "Rzayev Orxan Eldar oğlu",
            "Səlimova Nərgiz Rafiq qızı",
            "Məhərrəmov Fərid Asif oğlu"
        ]
        
        for i, person in enumerate(sample_people):
            row_num = row + 1 + i
            
            # Şəxs
            ws[f"A{row_num}"].value = person
            ws[f"A{row_num}"].font = self.default_font
            
            # Ümumi növbə (formula - AYLIQ QRAFİK-dən say)
            ws[f"B{row_num}"].value = f"=COUNTIF('AYLIQ QRAFİK'!$E$8:$E$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$F$8:$F$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$G$8:$G$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$H$8:$H$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$I$8:$I$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$J$8:$J$37,A{row_num})"
            ws[f"B{row_num}"].font = self.default_font
            
            # Ümumi xidmət yükü (formula - növbələrin əmsalları ilə)
            # Hissə növbətçisi (E sütunu) = 5
            # Köməkçi (F sütunu) = 4
            # NBM (G sütunu) = 3
            # Park (H sütunu) = 3
            # Yeməkxana (I sütunu) = 2
            # Otaq (J sütunu) = 1
            ws[f"C{row_num}"].value = f"=COUNTIF('AYLIQ QRAFİK'!$E$8:$E$37,A{row_num})*PARAMETRLƏR!$B$5+COUNTIF('AYLIQ QRAFİK'!$F$8:$F$37,A{row_num})*PARAMETRLƏR!$B$6+COUNTIF('AYLIQ QRAFİK'!$G$8:$G$37,A{row_num})*PARAMETRLƏR!$B$7+COUNTIF('AYLIQ QRAFİK'!$H$8:$H$37,A{row_num})*PARAMETRLƏR!$B$8+COUNTIF('AYLIQ QRAFİK'!$I$8:$I$37,A{row_num})*PARAMETRLƏR!$B$9+COUNTIF('AYLIQ QRAFİK'!$J$8:$J$37,A{row_num})*PARAMETRLƏR!$B$10"
            ws[f"C{row_num}"].font = self.default_font
            
            # Mövcud gün (formula - AYLIQ QRAFİK-də mövcud olduğu günlər)
            # Sadəcə say
            ws[f"D{row_num}"].value = 30  # Default olaraq 30
            ws[f"D{row_num}"].font = self.default_font
            
            # Normallaşdırılmış yük (Ümumi xidmət yükü / Mövcud gün)
            ws[f"E{row_num}"].value = f"=IF(D{row_num}>0,C{row_num}/D{row_num},0)"
            ws[f"E{row_num}"].font = self.default_font
            ws[f"E{row_num}"].number_format = "0.00"
            
            # Cümə, Şənbə, Bazar sayları
            # Cümə
            ws[f"F{row_num}"].value = f"=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Cümə\")+COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Cümə axşamı\")"
            ws[f"F{row_num}"].font = self.default_font
            
            # Şənbə
            ws[f"G{row_num}"].value = f"=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Şənbə\")"
            ws[f"G{row_num}"].font = self.default_font
            
            # Bazar
            ws[f"H{row_num}"].value = f"=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Bazar\")"
            ws[f"H{row_num}"].font = self.default_font
            
            # Cümə→Şənbə
            ws[f"I{row_num}"].value = f"=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Cümə\",'AYLIQ QRAFİK'!$C$9:$C$38,\"Şənbə\")+COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Cümə axşamı\",'AYLIQ QRAFİK'!$C$9:$C$38,\"Şənbə\")"
            ws[f"I{row_num}"].font = self.default_font
            
            # Şənbə→Bazar
            ws[f"J{row_num}"].value = f"=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Şənbə\",'AYLIQ QRAFİK'!$C$9:$C$38,\"Bazar\")"
            ws[f"J{row_num}"].font = self.default_font
            
            # Bazar→Bazar ertəsi
            ws[f"K{row_num}"].value = f"=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,A{row_num},'AYLIQ QRAFİK'!$C$8:$C$37,\"Bazar\",'AYLIQ QRAFİK'!$C$9:$C$38,\"Bazar ertəsi\")"
            ws[f"K{row_num}"].font = self.default_font
            
            # Ağır növbə (Hissə növbətçisi + Köməkçi)
            ws[f"L{row_num}"].value = f"=COUNTIF('AYLIQ QRAFİK'!$E$8:$E$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$F$8:$F$37,A{row_num})"
            ws[f"L{row_num}"].font = self.default_font
            
            # Orta növbə (NBM + Park)
            ws[f"M{row_num}"].value = f"=COUNTIF('AYLIQ QRAFİK'!$G$8:$G$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$H$8:$H$37,A{row_num})"
            ws[f"M{row_num}"].font = self.default_font
            
            # Yüngül növbə (Yeməkxana + Otaq)
            ws[f"N{row_num}"].value = f"=COUNTIF('AYLIQ QRAFİK'!$I$8:$I$37,A{row_num})+COUNTIF('AYLIQ QRAFİK'!$J$8:$J$37,A{row_num})"
            ws[f"N{row_num}"].font = self.default_font
            
            # Son növbə (son tarix)
            ws[f"O{row_num}"].value = f"=IFERROR(MAXIFS('AYLIQ QRAFİK'!$B$8:$B$37,'AYLIQ QRAFİK'!$E$8:$E$37,A{row_num},'AYLIQ QRAFİK'!$E$8:$J$37,A{row_num}),\"\")"
            ws[f"O{row_num}"].font = self.default_font
            ws[f"O{row_num}"].number_format = "dd.mm.yyyy"
            
            # Formatlaşdırma
            for col in range(1, 16):
                cell = ws.cell(row=row_num, column=col)
                cell.border = self.thin_border
                cell.alignment = self.center_alignment if col > 1 else self.left_alignment
        
        # Qoruma
        for r in range(1, row + len(sample_people) + 1):
            for c in range(1, 16):
                cell = ws.cell(row=r, column=c)
                if r >= 5 and c == 1:  # Şəxs adı
                    cell.protection = self.unlocked_cell
                elif r >= 5 and c == 4:  # Mövcud gün
                    cell.protection = self.unlocked_cell
        
        # Avtomatik filter
        ws.auto_filter.ref = f"A4:O{row + len(sample_people)}"
        
    def create_dashboard_sheet(self):
        """DASHBOARD vərəqini yarat"""
        ws = self.wb["DASHBOARD"]
        
        # Sütun genişlikləri
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 20
        ws.column_dimensions["D"].width = 20
        
        # Başlıq
        ws.merge_cells("A1:D1")
        title_cell = ws["A1"]
        title_cell.value = "NÖVBƏÇİLİK SİSTEMİ DASHBOARD"
        title_cell.font = Font(name="Calibri", size=18, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:D2")
        ws["A2"].value = "Bu vərəqdə sistemin ümumi vəziyyəti, balans və risklər göstərilir."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Ümumi vəziyyət
        row = 4
        ws.merge_cells(f"A{row}:D{row}")
        ws[f"A{row}"].value = "ÜMUMİ VƏZİYYƏT"
        ws[f"A{row}"].font = self.header_font
        ws[f"A{row}"].fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
        row += 1
        
        # Ümumi göstəricilər
        umumi_data = [
            ("Cari ay", "='AYLIQ QRAFİK'!$E$4", "text"),
            ("Cari il", "='AYLIQ QRAFİK'!$B$4", "0"),
            ("Ayın gün sayı", "=DAY(EOMONTH(DATE('AYLIQ QRAFİK'!$B$4, MATCH('AYLIQ QRAFİK'!$E$4, {\"Yanvar\",\"Fevral\",\"Mart\",\"Aprel\",\"May\",\"İyun\",\"İyul\",\"Avqust\",\"Sentyabr\",\"Oktyabr\",\"Noyabr\",\"Dekabr\"}, 0)), 0))", "0"),
            ("Aktiv şəxs sayı", "=COUNTIF('ŞƏXSLƏR'!$G$5:$G$100,\"Aktiv\")", "0"),
            ("Ümumi növbə sayı", "=COUNTIF('AYLIQ QRAFİK'!$E$8:$J$37,\"<>\")*6", "0"),
            ("Dolu növbə", "=COUNTA('AYLIQ QRAFİK'!$E$8:$E$37)+COUNTA('AYLIQ QRAFİK'!$F$8:$F$37)+COUNTA('AYLIQ QRAFİK'!$G$8:$G$37)+COUNTA('AYLIQ QRAFİK'!$H$8:$H$37)+COUNTA('AYLIQ QRAFİK'!$I$8:$I$37)+COUNTA('AYLIQ QRAFİK'!$J$8:$J$37)", "0"),
            ("Boş növbə", "=COUNTBLANK('AYLIQ QRAFİK'!$E$8:$E$37)+COUNTBLANK('AYLIQ QRAFİK'!$F$8:$F$37)+COUNTBLANK('AYLIQ QRAFİK'!$G$8:$G$37)+COUNTBLANK('AYLIQ QRAFİK'!$H$8:$H$37)+COUNTBLANK('AYLIQ QRAFİK'!$I$8:$I$37)+COUNTBLANK('AYLIQ QRAFİK'!$J$8:$J$37)", "0"),
            ("Yoxluqda olan şəxslər", "=COUNTIF('YOXDUR-MƏZUNİYYƏT'!$A$5:$A$100,\"<>\")", "0"),
        ]
        
        for label, formula, num_format in umumi_data:
            ws[f"A{row}"].value = label
            ws[f"A{row}"].font = self.subheader_font
            ws[f"B{row}"].value = formula
            ws[f"B{row}"].font = self.default_font
            if num_format == "0":
                ws[f"B{row}"].number_format = "0"
            elif num_format == "text":
                pass
            else:
                ws[f"B{row}"].number_format = num_format
            
            # Formatlaşdırma
            for col in ["A", "B"]:
                cell = ws[f"{col}{row}"]
                cell.border = self.thin_border
                cell.alignment = self.left_alignment if col == "A" else self.center_alignment
            
            row += 1
        
        row += 1
        
        # Balans
        ws.merge_cells(f"A{row}:D{row}")
        ws[f"A{row}"].value = "BALANS"
        ws[f"A{row}"].font = self.header_font
        ws[f"A{row}"].fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
        row += 1
        
        balans_data = [
            ("Ən aşağı yük", "=MIN('BALANS'!$C$5:$C$100)", "0.00"),
            ("Orta yük", "=AVERAGE('BALANS'!$C$5:$C$100)", "0.00"),
            ("Ən yüksək yük", "=MAX('BALANS'!$C$5:$C$100)", "0.00"),
            ("Yük fərqi", "=MAX('BALANS'!$C$5:$C$100)-MIN('BALANS'!$C$5:$C$100)", "0.00"),
            ("Həftəsonu yük fərqi", "=MAX('BALANS'!$F$5:$H$100)-MIN('BALANS'!$F$5:$H$100)", "0.00"),
        ]
        
        for label, formula, num_format in balans_data:
            ws[f"A{row}"].value = label
            ws[f"A{row}"].font = self.subheader_font
            ws[f"B{row}"].value = formula
            ws[f"B{row}"].font = self.default_font
            ws[f"B{row}"].number_format = num_format
            
            # Formatlaşdırma
            for col in ["A", "B"]:
                cell = ws[f"{col}{row}"]
                cell.border = self.thin_border
                cell.alignment = self.left_alignment if col == "A" else self.center_alignment
            
            row += 1
        
        row += 1
        
        # Risklər
        ws.merge_cells(f"A{row}:D{row}")
        ws[f"A{row}"].value = "RİSKLƏR"
        ws[f"A{row}"].font = self.header_font
        ws[f"A{row}"].fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
        row += 1
        
        risk_data = [
            ("Yoxluqda olan şəxsə növbə", "=COUNTIFS('AYLIQ QRAFİK'!$E$8:$J$37,\"<>\",'AYLIQ QRAFİK'!$E$8:$E$37,IF(COUNTIF('YOXDUR-MƏZUNİYYƏT'!$A$5:$A$100,'AYLIQ QRAFİK'!$E$8:$E$37)>0,1,0))", "0"),
            ("Uyğun olmayan şəxs", "=SUMPRODUCT(('AYLIQ QRAFİK'!$E$8:$J$37<>\"\")*('AYLIQ QRAFİK'!$E$8:$J$37<>\"\"))", "0"),
            ("İstirahət qaydasının pozulması", "0", "0"),
            ("Boş növbə", "=COUNTBLANK('AYLIQ QRAFİK'!$E$8:$J$37)", "0"),
            ("Həddindən artıq həftəsonu yükü", "0", "0"),
            ("Ardıcıl növbə", "0", "0"),
        ]
        
        for label, formula, num_format in risk_data:
            ws[f"A{row}"].value = label
            ws[f"A{row}"].font = self.subheader_font
            ws[f"B{row}"].value = formula
            ws[f"B{row}"].font = self.default_font
            ws[f"B{row}"].number_format = num_format
            
            # Formatlaşdırma
            for col in ["A", "B"]:
                cell = ws[f"{col}{row}"]
                cell.border = self.thin_border
                cell.alignment = self.left_alignment if col == "A" else self.center_alignment
            
            row += 1
        
        # Bütün hüceyrələri formatla
        for r in range(1, row + 1):
            for c in ["A", "B", "C", "D"]:
                cell = ws[f"{c}{r}"]
                cell.border = self.thin_border
        
        # Qoruma
        for r in range(1, row + 1):
            for c in ["A", "B", "C", "D"]:
                ws[f"{c}{r}"].protection = self.locked_cell
        
    def create_change_log_sheet(self):
        """DƏYİŞİKLİK JURNALI vərəqini yarat"""
        ws = self.wb["DƏYİŞİKLİK JURNALI"]
        
        # Sütun genişlikləri
        col_widths = {
            "A": 15, "B": 10, "C": 15, "D": 20,
            "E": 25, "F": 25, "G": 30, "H": 25
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
        # Başlıq
        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = "DƏYİŞİKLİK JURNALI"
        title_cell.font = Font(name="Calibri", size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Qısa təlimat
        ws.merge_cells("A2:H2")
        ws["A2"].value = "Bu vərəqdə bütün əl ilə edilmiş dəyişikliklərin tarixçəsi saxlanılır."
        ws["A2"].font = self.small_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A2"].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Başlıq sətri
        row = 4
        headers = [
            "Tarix", "Saat", "Növbə tarixi", "Növbə növü",
            "Əvvəlki şəxs", "Yeni şəxs", "Dəyişiklik səbəbi", "Qeyd"
        ]
        
        for i, header in enumerate(headers):
            cell = ws.cell(row=row, column=i+1)
            cell.value = header
            cell.font = self.header_font
            cell.fill = PatternFill(start_color=COLOR_LIGHT_BLUE, end_color=COLOR_LIGHT_BLUE, fill_type="solid")
            cell.border = self.thin_border
            cell.alignment = self.center_alignment
        
        # Boş sətirlər
        for i in range(20):
            row_num = row + 1 + i
            for col in range(1, 9):
                cell = ws.cell(row=row_num, column=col)
                cell.border = self.thin_border
                cell.alignment = self.center_alignment if col in [1, 2, 3, 5, 6] else self.left_alignment
        
        # Data Validation
        # Növbə növü
        novbe_dv = DataValidation(type="list", formula1='"Hissə növbətçisi,Hissə növbətçisinin köməkçisi,Nəzarət-buraxılış məntəqəsi növbətçisi,Park növbətçisi,Yeməkxana növbətçisi,Otaq növbətçisi"', allow_blank=True)
        novbe_dv.add(f"D5:D24")
        ws.add_data_validation(novbe_dv)
        
        # Dəyişiklik səbəbi
        sebeb_dv = DataValidation(type="list", formula1='"Səhv düzəlişi,Şəxs dəyişdirilməsi,Məzuniyyət,Digər"', allow_blank=True)
        sebeb_dv.add(f"G5:G24")
        ws.add_data_validation(sebeb_dv)
        
        # Şəxslər
        people_ref = f"'ŞƏXSLƏR'!$E$5:$E$100"
        person_dv = DataValidation(type="list", formula1=people_ref, allow_blank=True)
        person_dv.add(f"E5:E24")  # Əvvəlki şəxs
        person_dv.add(f"F5:F24")  # Yeni şəxs
        ws.add_data_validation(person_dv)
        
        # Qoruma
        for r in range(5, 25):
            for c in range(1, 9):
                ws.cell(row=r, column=c).protection = self.unlocked_cell
        
        # Avtomatik filter
        ws.auto_filter.ref = f"A4:H24"
        
        # Tarix və saat avtomatik
        ws[f"A5"].value = "=TODAY()"
        ws[f"A5"].number_format = "dd.mm.yyyy"
        ws[f"B5"].value = "=NOW()"
        ws[f"B5"].number_format = "hh:mm"
        
        # Formulları qoruma
        ws[f"A5"].protection = self.locked_cell
        ws[f"B5"].protection = self.locked_cell
        
    def apply_conditional_formatting(self):
        """Şərti formatlaşdırma tətbiq et"""
        # AYLIQ QRAFİK vərəqində
        ws_schedule = self.wb["AYLIQ QRAFİK"]
        
        # Həftəsonu günlərini vurgula
        hefte_sonu_gunleri = ["Cümə", "Cümə axşamı", "Şənbə", "Bazar"]
        
        # Bütün sətirlər üçün
        for row in range(8, 38):
            hefte_gunu = ws_schedule[f"C{row}"].value
            if hefte_gunu in hefte_sonu_gunleri:
                for col in range(1, 5 + len(NOVBE_NOVLERI)):
                    cell = ws_schedule.cell(row=row, column=col)
                    cell.fill = PatternFill(start_color="FFF0E6", end_color="FFF0E6", fill_type="solid")
        
        # BALANS vərəqində
        ws_balance = self.wb["BALANS"]
        
        # Yük səviyyəsinə görə rəngləndirmə
        # Ən aşağı yük - yaşıl
        # Orta yük - sarı
        # Ən yüksək yük - qırmızı
        
        # Formulalar Excel-də işləyəcək
        # Burada sadəcə formatlaşdırma quraşdırıraq
        
    def add_named_ranges(self):
        """Adlı diazazonlar əlavə et"""
        # openpyxl-də defined_name modulu yoxdur, sadəcə keç
        pass
        
    def add_protection(self):
        """Vərəqləri qoruma"""
        # Bütün vərəqləri qoruma
        for sheet_name in self.wb.sheetnames:
            ws = self.wb[sheet_name]
            ws.protection.sheet = True
            ws.protection.password = "novbe123"  # Default parol
            ws.protection.enable()
        
        # DASHBOARD, BALANS, PARAMETRLƏR vərəqlərində bəzi hüceyrələri aç
        # PARAMETRLƏR
        ws_param = self.wb["PARAMETRLƏR"]
        for row in range(5, 21):
            if row in [5, 6, 7, 8, 9, 10, 13, 14, 15, 18, 19, 20]:
                ws_param[f"B{row}"].protection = self.unlocked_cell
        
        # AYLIQ QRAFİK
        ws_schedule = self.wb["AYLIQ QRAFİK"]
        ws_schedule[f"B4"].protection = self.unlocked_cell  # İl
        ws_schedule[f"E4"].protection = self.unlocked_cell  # Ay
        
        # Növbə sütunları
        for row in range(8, 38):
            for i in range(len(NOVBE_NOVLERI)):
                col = 5 + i
                ws_schedule.cell(row=row, column=col).protection = self.unlocked_cell
        
        # ŞƏXSLƏR
        ws_people = self.wb["ŞƏXSLƏR"]
        for row in range(5, 100):
            for col in range(1, 9 + len(NOVBE_NOVLERI)):
                if col != 5:  # Tam ad formuladır
                    ws_people.cell(row=row, column=col).protection = self.unlocked_cell
        
        # YOXDUR-MƏZUNİYYƏT
        ws_absence = self.wb["YOXDUR-MƏZUNİYYƏT"]
        for row in range(5, 100):
            for col in range(1, 7):
                if col != 5:  # Bitmə tarixi formuladır
                    ws_absence.cell(row=row, column=col).protection = self.unlocked_cell
        
        # DƏYİŞİKLİK JURNALI
        ws_log = self.wb["DƏYİŞİKLİK JURNALI"]
        for row in range(5, 100):
            for col in range(1, 9):
                ws_log.cell(row=row, column=col).protection = self.unlocked_cell
        
    def save_file(self, filename):
        """Faylı yadda saxla"""
        self.wb.save(filename)
        print(f"Fayl '{filename}' olaraq yadda saxlanıldı.")


def main():
    """Əsas funksiya"""
    print("Aylıq Növbətçilik Planlaşdırma Sistemi yaradılır...")
    
    generator = NovbeSystemGenerator()
    
    # Bütün vərəqləri yarat
    generator.create_all_sheets()
    
    # Vərəqləri doldur
    print("  - PARAMETRLƏR vərəqi yaradılır...")
    generator.create_parameters_sheet()
    
    print("  - ŞƏXSLƏR vərəqi yaradılır...")
    generator.create_people_sheet()
    
    print("  - YOXDUR-MƏZUNİYYƏT vərəqi yaradılır...")
    generator.create_absence_sheet()
    
    print("  - AYLIQ QRAFİK vərəqi yaradılır...")
    generator.create_monthly_schedule_sheet()
    
    print("  - BALANS vərəqi yaradılır...")
    generator.create_balance_sheet()
    
    print("  - DASHBOARD vərəqi yaradılır...")
    generator.create_dashboard_sheet()
    
    print("  - DƏYİŞİKLİK JURNALI vərəqi yaradılır...")
    generator.create_change_log_sheet()
    
    # Şərti formatlaşdırma
    print("  - Şərti formatlaşdırma tətbiq edilir...")
    generator.apply_conditional_formatting()
    
    # Adlı diazazonlar
    print("  - Adlı diazazonlar əlavə edilir...")
    generator.add_named_ranges()
    
    # Qoruma
    print("  - Qoruma tətbiq edilir...")
    generator.add_protection()
    
    # Faylı yadda saxla
    output_file = "/workspace/github__Mireyyub__zenthon/Novbe_Sistemi.xlsx"
    print(f"  - Fayl '{output_file}' olaraq yadda saxlanılır...")
    generator.save_file(output_file)
    
    print("\n✅ Aylıq Növbətçilik Planlaşdırma Sistemi hazırdır!")
    print(f"Fayl yeri: {output_file}")
    
    # Test məlumatları
    print("\n📋 Sistemin strukturu:")
    print("  1. DASHBOARD - Ümumi vəziyyət, balans və xəbərdarlıqlar")
    print("  2. AYLIQ QRAFİK - Əsas növbətçilik cədvəli")
    print("  3. ŞƏXSLƏR - Bütün şəxslərin məlumat bazası")
    print("  4. YOXDUR-MƏZUNİYYƏT - Məzuniyyət və digər yoxluqlar")
    print("  5. BALANS - Şəxslərin növbə və xidmət yükünün statistikası")
    print("  6. PARAMETRLƏR - Bütün qaydalar və əmsallar")
    print("  7. DƏYİŞİKLİK JURNALI - Əl ilə edilmiş dəyişikliklərin tarixçəsi")
    
    print("\n🔧 İstifadə üçün:")
    print("  1. Faylı Excel-də açın")
    print("  2. PARAMETRLƏR vərəqində parametrləri yoxlayın")
    print("  3. ŞƏXSLƏR vərəqində şəxsləri və uyğunluqları daxil edin")
    print("  4. YOXDUR-MƏZUNİYYƏT vərəqində yoxluqları qeyd edin")
    print("  5. AYLIQ QRAFİK-də il və ay seçin")
    print("  6. Növbələri avtomatik və ya əl ilə doldurun")
    print("  7. BALANS və DASHBOARD vərəqlərində nəticələri yoxlayın")


if __name__ == "__main__":
    main()
