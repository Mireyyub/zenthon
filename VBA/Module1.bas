Option Explicit

' ============================================
' Aylıq Növbətçilik Planlaşdırma Sistemi v2.0
' VBA Modul 1 - Əsas Funksiya
' ============================================

Public Sub GenerateSchedule()
    ' Növbələri avtomatik olaraq yaradır
    Dim startTime As Double
    startTime = Timer
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    On Error GoTo ErrorHandler
    
    ' Parametrləri oxu
    Dim params As Object
    Set params = GetParameters()
    
    ' Ay məlumatlarını oxu
    Dim year As Integer, month As Integer, numDays As Integer
    year = ThisWorkbook.Sheets("AYLIQ QRAFİK").Range("B4").Value
    month = GetMonthNumber(ThisWorkbook.Sheets("AYLIQ QRAFİK").Range("E4").Value)
    numDays = Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
    
    ' Aktiv şəxsləri oxu
    Dim people() As Variant
    people = GetActivePeople()
    
    ' Yoxluq tarixlərini oxu
    Dim absences As Object
    Set absences = GetAbsenceDates()
    
    ' Cədvəli sıfırla
    ClearSchedule numDays
    
    ' Hər növbə üçün namizədləri seç
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    Dim i As Integer, dayIdx As Integer
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    ' Hər növbə üçün
    For i = LBound(novbeTypes) To UBound(novbeTypes)
        Call GenerateScheduleForNovbeType(novbeTypes(i), year, month, numDays, people, absences, params, wsSchedule)
    Next i
    
    ' Nəticəni göstər
    MsgBox "Növbələr avtomatik olaraq yaradıldı!" & vbCrLf & _
           "Müddət: " & Format(Timer - startTime, "0.00") & " saniyə", vbInformation, "Uğurlu!"
    
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.EnableEvents = True
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Xəta baş verdi: " & Err.Description, vbCritical, "Xəta"
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.EnableEvents = True
End Sub
