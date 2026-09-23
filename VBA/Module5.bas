Option Explicit

' ============================================
' Aylıq Növbətçilik Planlaşdırma Sistemi v3.0
' VBA Modul 5 - Reportlar və İxrac
' ============================================

' ============================================
' HESABATLAR
' ============================================

Public Sub GenerateMonthlyReport()
    ' Aylıq hesabat yarad
    Application.ScreenUpdating = False
    
    Dim wsReport As Worksheet
    
    ' HESABAT vərəqini yoxla
    On Error Resume Next
    Set wsReport = ThisWorkbook.Sheets("HESABAT")
    On Error GoTo 0
    
    If wsReport Is Nothing Then
        ' Vərəq yoxdursa, yarat
        Set wsReport = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        wsReport.Name = "HESABAT"
    Else
        ' Vərəqi təmizlə
        wsReport.Cells.Clear
    End If
    
    ' Başlıq
    wsReport.Range("A1").Value = "AYLIQ HESABAT"
    wsReport.Range("A1").Font.Bold = True
    wsReport.Range("A1").Font.Size = 16
    
    ' Ay məlumatları
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim year As Integer, month As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    
    wsReport.Range("A3").Value = "Ay:"
    wsReport.Range("B3").Value = wsSchedule.Range("E4").Value & " " & year
    wsReport.Range("B3").Font.Bold = True
    
    ' Ümumi məlumat
    wsReport.Range("A5").Value = "ÜMUMİ MƏLUMAT"
    wsReport.Range("A5").Font.Bold = True
    wsReport.Range("A5").Interior.Color = RGB(200, 230, 255)
    
    wsReport.Range("A6").Value = "Aktiv şəxs sayı:"
    wsReport.Range("B6").Value = "=COUNTIF('ŞƏXSLƏR'!$G$5:$G$100,\"Aktiv\")"
    
    wsReport.Range("A7").Value = "Ümumi növbə sayı:"
    wsReport.Range("B7").Value = "=COUNTIF('AYLIQ QRAFİK'!$E$8:$J$37,\"<>\")*6"
    
    wsReport.Range("A8").Value = "Dolu növbə:"
    wsReport.Range("B8").Value = "=COUNTA('AYLIQ QRAFİK'!$E$8:$E$37)+COUNTA('AYLIQ QRAFİK'!$F$8:$F$37)+COUNTA('AYLIQ QRAFİK'!$G$8:$G$37)+COUNTA('AYLIQ QRAFİK'!$H$8:$H$37)+COUNTA('AYLIQ QRAFİK'!$I$8:$I$37)+COUNTA('AYLIQ QRAFİK'!$J$8:$J$37)"
    
    wsReport.Range("A9").Value = "Boş növbə:"
    wsReport.Range("B9").Value = "=COUNTBLANK('AYLIQ QRAFİK'!$E$8:$J$37)"
    
    wsReport.Range("A10").Value = "Yoxluqda olan şəxslər:"
    wsReport.Range("B10").Value = "=COUNTIF('YOXDUR-MƏZUNİYYƏT'!$A$5:$A$100,\"<>\")"
    
    ' Yük balansı
    wsReport.Range("A12").Value = "YÜK BALANSI"
    wsReport.Range("A12").Font.Bold = True
    wsReport.Range("A12").Interior.Color = RGB(200, 230, 255)
    
    wsReport.Range("A13").Value = "Ən aşağı yük:"
    wsReport.Range("B13").Value = "=MIN('BALANS'!$C$5:$C$100)"
    wsReport.Range("B13").NumberFormat = "0.00"
    
    wsReport.Range("A14").Value = "Orta yük:"
    wsReport.Range("B14").Value = "=AVERAGE('BALANS'!$C$5:$C$100)"
    wsReport.Range("B14").NumberFormat = "0.00"
    
    wsReport.Range("A15").Value = "Ən yüksək yük:"
    wsReport.Range("B15").Value = "=MAX('BALANS'!$C$5:$C$100)"
    wsReport.Range("B15").NumberFormat = "0.00"
    
    wsReport.Range("A16").Value = "Yük fərqi:"
    wsReport.Range("B16").Value = "=MAX('BALANS'!$C$5:$C$100)-MIN('BALANS'!$C$5:$C$100)"
    wsReport.Range("B16").NumberFormat = "0.00"
    
    ' Həftəsonu balansı
    wsReport.Range("A18").Value = "HƏFTƏSONU BALANSI"
    wsReport.Range("A18").Font.Bold = True
    wsReport.Range("A18").Interior.Color = RGB(200, 230, 255)
    
    wsReport.Range("A19").Value = "Cümə say:"
    wsReport.Range("B19").Value = "=SUM('BALANS'!$F$5:$F$100)"
    
    wsReport.Range("A20").Value = "Şənbə say:"
    wsReport.Range("B20").Value = "=SUM('BALANS'!$G$5:$G$100)"
    
    wsReport.Range("A21").Value = "Bazar say:"
    wsReport.Range("B21").Value = "=SUM('BALANS'!$H$5:$H$100)"
    
    ' Formatlaşdırma
    Dim i As Integer
    For i = 1 To 21
        wsReport.Cells(i, 1).Font.Name = "Calibri"
        wsReport.Cells(i, 1).Font.Size = 11
        wsReport.Cells(i, 2).Font.Name = "Calibri"
        wsReport.Cells(i, 2).Font.Size = 11
    Next i
    
    ' Sütun genişlikləri
    wsReport.Columns("A").ColumnWidth = 25
    wsReport.Columns("B").ColumnWidth = 15
    
    MsgBox "✅ Aylıq hesabat yaradıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Public Sub GeneratePersonReport()
    ' Şəxs hesabatı yarad
    Application.ScreenUpdating = False
    
    Dim wsReport As Worksheet
    
    ' ŞƏXS_HESABATI vərəqini yoxla
    On Error Resume Next
    Set wsReport = ThisWorkbook.Sheets("ŞƏXS_HESABATI")
    On Error GoTo 0
    
    If wsReport Is Nothing Then
        Set wsReport = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        wsReport.Name = "ŞƏXS_HESABATI"
    Else
        wsReport.Cells.Clear
    End If
    
    ' Başlıq
    wsReport.Range("A1").Value = "ŞƏXS HESABATI"
    wsReport.Range("A1").Font.Bold = True
    wsReport.Range("A1").Font.Size = 16
    
    ' Ay məlumatları
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim year As Integer, month As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    
    wsReport.Range("A3").Value = "Ay:"
    wsReport.Range("B3").Value = wsSchedule.Range("E4").Value & " " & year
    wsReport.Range("B3").Font.Bold = True
    
    ' Başlıq sətri
    wsReport.Range("A5").Value = "Şəxs"
    wsReport.Range("B5").Value = "Ümumi iştirak"
    wsReport.Range("C5").Value = "Hissə növbətçisi"
    wsReport.Range("D5").Value = "Köməkçi"
    wsReport.Range("E5").Value = "NBM"
    wsReport.Range("F5").Value = "Park"
    wsReport.Range("G5").Value = "Yeməkxana"
    wsReport.Range("H5").Value = "Otaq"
    wsReport.Range("I5").Value = "Həftəsonu"
    wsReport.Range("J5").Value = "İştirak %"
    
    ' Formatlaşdırma
    Dim i As Integer
    For i = 5 To 14
        wsReport.Cells(5, i).Font.Bold = True
        wsReport.Cells(5, i).Interior.Color = RGB(200, 230, 255)
    Next i
    
    ' Şəxsləri oxu
    Dim wsPeople As Worksheet
    Set wsPeople = ThisWorkbook.Sheets("ŞƏXSLƏR")
    
    Dim lastRowPeople As Integer
    lastRowPeople = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    ' Hər şəxs üçün hesabat
    Dim reportRow As Integer
    reportRow = 6
    
    For i = 5 To lastRowPeople
        Dim person As String
        person = wsPeople.Cells(i, 5).Value
        
        If person <> "" Then
            ' Ümumi iştirak
            Dim total As Integer
            total = Application.WorksheetFunction.CountIf(wsSchedule.Range("E8:J37"), person)
            
            ' Hər növbə üçün
            Dim novbeCounts(1 To 6) As Integer
            Dim j As Integer
            For j = 5 To 10
                novbeCounts(j - 4) = Application.WorksheetFunction.CountIf(wsSchedule.Columns(j), person)
            Next j
            
            ' Həftəsonu iştirak
            Dim weekendCount As Integer
            weekendCount = CountWeekendParticipationInSchedule(person, wsSchedule)
            
            ' İştirak nisbəti
            Dim participationRate As Double
            Dim maxNovbe As Integer
            maxNovbe = Application.WorksheetFunction.Max(novbeCounts)
            If maxNovbe > 0 Then
                participationRate = (total / (30 / GetActivePeopleCount(wsPeople))) * 100
            Else
                participationRate = 0
            End If
            
            ' Məlumatları yaz
            wsReport.Cells(reportRow, 1).Value = person
            wsReport.Cells(reportRow, 2).Value = total
            
            For j = 1 To 6
                wsReport.Cells(reportRow, j + 2).Value = novbeCounts(j)
            Next j
            
            wsReport.Cells(reportRow, 9).Value = weekendCount
            wsReport.Cells(reportRow, 10).Value = participationRate / 100
            wsReport.Cells(reportRow, 10).NumberFormat = "0.00%"
            
            reportRow = reportRow + 1
        End If
    Next i
    
    ' Sütun genişlikləri
    wsReport.Columns("A").ColumnWidth = 30
    wsReport.Columns("B").ColumnWidth = 12
    For i = 3 To 9
        wsReport.Columns(i).ColumnWidth = 10
    Next i
    wsReport.Columns("J").ColumnWidth = 12
    
    MsgBox "✅ Şəxs hesabatı yaradıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Private Function CountWeekendParticipationInSchedule(person As String, wsSchedule As Worksheet) As Integer
    ' AYLIQ QRAFİK vərəqində həftəsonu iştirakını say
    Dim count As Integer
    count = 0
    
    Dim lastRow As Integer
    lastRow = wsSchedule.Cells(wsSchedule.Rows.Count, "B").End(xlUp).Row
    
    Dim i As Integer, j As Integer
    For i = 8 To lastRow
        Dim hefteGunu As String
        hefteGunu = wsSchedule.Cells(i, 3).Value
        
        If InStr("Cümə,Şənbə,Bazar", hefteGunu) > 0 Then
            For j = 5 To 10
                If wsSchedule.Cells(i, j).Value = person Then
                    count = count + 1
                    Exit For
                End If
            Next j
        End If
    Next i
    
    CountWeekendParticipationInSchedule = count
End Function

' ============================================
' İXRAC FUNKSİYALARI
' ============================================

Public Sub ExportToExcel()
    ' Mövcud faylı yeni adı ilə ixrac et
    Dim filePath As String
    filePath = Application.GetSaveAsFilename(InitialFileName:="Novbe_Sistemi_" & Format(Now(), "yyyy-mm-dd"), _
        FileFilter:="Excel Files (*.xlsx), *.xlsx", Title:="Faylı ixrac et")
    
    If filePath <> "False" Then
        ThisWorkbook.SaveAs filePath, FileFormat:=xlOpenXMLWorkbook
        MsgBox "✅ Fayl ixrac edildi: " & filePath, vbInformation, "Uğurlu!"
    End If
End Sub

Public Sub ExportReportToPDF()
    ' Hesabatı PDF olaraq ixrac et
    Dim wsReport As Worksheet
    
    On Error Resume Next
    Set wsReport = ThisWorkbook.Sheets("HESABAT")
    On Error GoTo 0
    
    If wsReport Is Nothing Then
        MsgBox "Hesabat vərəqi tapılmadı!", vbExclamation
        Exit Sub
    End If
    
    Dim filePath As String
    filePath = ThisWorkbook.Path & "\Aylıq_Novbe_Hesabat_" & Format(Now(), "yyyy-mm-dd") & ".pdf"
    
    wsReport.ExportAsFixedFormat Type:=xlTypePDF, Filename:=filePath, Quality:=xlQualityStandard, _
        IncludeDocProperties:=True, IgnorePrintAreas:=False, OpenAfterPublish:=True
    
    MsgBox "✅ Hesabat PDF olaraq ixrac edildi: " & filePath, vbInformation, "Uğurlu!"
End Sub

Public Sub ExportAllToPDF()
    ' Bütün vərəqləri PDF olaraq ixrac et
    Dim ws As Worksheet
    Dim filePath As String
    
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name <> "HESABAT" And ws.Name <> "ŞƏXS_HESABATI" Then
            filePath = ThisWorkbook.Path & "\" & ws.Name & "_" & Format(Now(), "yyyy-mm-dd") & ".pdf"
            ws.ExportAsFixedFormat Type:=xlTypePDF, Filename:=filePath, Quality:=xlQualityStandard, _
                IncludeDocProperties:=True, IgnorePrintAreas:=False, OpenAfterPublish:=False
        End If
    Next ws
    
    MsgBox "✅ Bütün vərəqlər PDF olaraq ixrac edildi!", vbInformation, "Uğurlu!"
End Sub

' ============================================
' EMAIL İXRACI (Outlook ilə)
' ============================================

Public Sub EmailReport()
    ' Hesabatı email ilə göndər
    Dim OutApp As Object
    Dim OutMail As Object
    
    On Error Resume Next
    Set OutApp = GetObject(",Outlook.Application")
    On Error GoTo 0
    
    If OutApp Is Nothing Then
        Set OutApp = CreateObject("Outlook.Application")
    End If
    
    Set OutMail = OutApp.CreateItem(0)
    
    With OutMail
        .To = "" ' Alıcınızı daxil edin
        .CC = ""
        .BCC = ""
        .Subject = "Aylıq Növbətçilik Hesabatı - " & Format(Now(), "mmmm yyyy")
        .Body = "Əziz istifadəçi," & vbCrLf & vbCrLf & _
                "Aylıq növbətçilik hesabatı əlavə edilmişdir." & vbCrLf & vbCrLf & _
                "Sayğılar," & vbCrLf & _
                "Növbətçilik Sistemi"
        
        ' Hesabat faylını əlavə et
        Dim tempPath As String
        tempPath = Environ("TEMP") & "\Aylıq_Novbe_Hesabat_" & Format(Now(), "yyyy-mm-dd") & ".pdf"
        
        ' Hesabatı PDF olaraq yadda saxla
        Dim wsReport As Worksheet
        On Error Resume Next
        Set wsReport = ThisWorkbook.Sheets("HESABAT")
        On Error GoTo 0
        
        If Not wsReport Is Nothing Then
            wsReport.ExportAsFixedFormat Type:=xlTypePDF, Filename:=tempPath, Quality:=xlQualityStandard
            .Attachments.Add tempPath
        End If
        
        .Display ' Emaili göstər
        ' .Send ' Dərhal göndər (test üçün commentdə)
    End With
    
    Set OutMail = Nothing
    Set OutApp = Nothing
    
    MsgBox "✅ Email hazırdır! Lütfən, alıcını daxil edin və göndərin.", vbInformation, "Uğurlu!"
End Sub

' ============================================
' PRİNT FUNKSİYALARI
' ============================================

Public Sub PrintSchedule()
    ' Cədvəli çap et
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    ' Çap üçün hazırla
    With wsSchedule.PageSetup
        .Orientation = xlLandscape
        .PaperSize = xlPaperA4
        .FitToWidth = 1
        .FitToHeight = False
        .PrintArea = "$A$7:$J$37"
        .CenterHorizontally = True
        .CenterVertically = False
    End With
    
    ' Çap et
    wsSchedule.PrintOut
End Sub

Public Sub PrintAllReports()
    ' Bütün hesabatları çap et
    Dim ws As Worksheet
    
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name = "HESABAT" Or ws.Name = "ŞƏXS_HESABATI" Or ws.Name = "BALANS" Then
            ws.PrintOut
        End If
    Next ws
End Sub

' ============================================
' XƏBƏRDARLIQ SİSTEMİ
' ============================================

Public Sub CheckForIssues()
    ' Avtomatik olaraq problemləri yoxla
    Application.ScreenUpdating = False
    
    Dim issues As Collection
    Set issues = New Collection
    
    ' 1. Boş növbələri yoxla
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim year As Integer, month As Integer, numDays As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    numDays = Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
    
    Dim emptyCount As Integer
    emptyCount = 0
    
    Dim day As Integer, col As Integer
    For day = 1 To numDays
        For col = 5 To 10
            If wsSchedule.Cells(day + 7, col).Value = "" Then
                emptyCount = emptyCount + 1
            End If
        Next col
    Next day
    
    If emptyCount > 0 Then
        issues.Add "⚠️  " & emptyCount & " boş növbə var"
    End If
    
    ' 2. Yoxluqda olan şəxsləri yoxla
    Dim wsAbsence As Worksheet
    Set wsAbsence = ThisWorkbook.Sheets("YOXDUR-MƏZUNİYYƏT")
    
    Dim lastRowAbsence As Integer
    lastRowAbsence = wsAbsence.Cells(wsAbsence.Rows.Count, "A").End(xlUp).Row
    
    If lastRowAbsence > 4 Then
        Dim absenceCount As Integer
        absenceCount = Application.WorksheetFunction.CountA(wsAbsence.Range("A5:A" & lastRowAbsence))
        issues.Add "  " & absenceCount & " şəxs yoxluqdadır"
    End If
    
    ' 3. Yük balansını yoxla
    Dim wsBalance As Worksheet
    Set wsBalance = ThisWorkbook.Sheets("BALANS")
    
    Dim maxLoad As Double, minLoad As Double
    maxLoad = Application.WorksheetFunction.Max(wsBalance.Range("C5:C100"))
    minLoad = Application.WorksheetFunction.Min(wsBalance.Range("C5:C100"))
    
    Dim loadDiff As Double
    loadDiff = maxLoad - minLoad
    
    If loadDiff > 5 Then ' 5-dən çox fərq
        issues.Add "⚠️  Yük fərqi çoxdur: " & Format(loadDiff, "0.00")
    End If
    
    ' Nəticəni göstər
    If issues.Count > 0 Then
        Dim msg As String
        msg = "Xəbərdarlıqlar:" & vbCrLf & vbCrLf
        
        Dim i As Integer
        For i = 1 To issues.Count
            msg = msg & i & ". " & issues(i) & vbCrLf
        Next i
        
        MsgBox msg, vbExclamation, "Xəbərdarlıq"
    Else
        MsgBox "✅ Heç bir problem yoxdur!", vbInformation, "Uğurlu!"
    End If
    
    Application.ScreenUpdating = True
End Sub

' ============================================
' KÖMƏKÇİ FUNKSİYALAR
' ============================================

Public Sub ShowSystemInfo()
    ' Sistem haqqında məlumat göstər
    Dim msg As String
    msg = "Aylıq Növbətçilik Planlaşdırma Sistemi v3.0" & vbCrLf & vbCrLf
    msg = msg & "Versiya: 3.0" & vbCrLf
    msg = msg & "Son yeniləmə: Sentyabr 2026" & vbCrLf
    msg = msg & "Hazırlayan: Vibe Code (Mistral AI)" & vbCrLf & vbCrLf
    msg = msg & "Funksiya:" & vbCrLf
    msg = msg & "- Avtomatik növbə generasiyası" & vbCrLf
    msg = msg & "- AI optimallaşdırma" & vbCrLf
    msg = msg & "- Həftəsonu yükü qrafiki" & vbCrLf
    msg = msg & "- Şəxs statistikası" & vbCrLf
    msg = msg & "- Tarixçə" & vbCrLf
    msg = msg & "- Hesabatlar" & vbCrLf
    msg = msg & "- Email ixracı" & vbCrLf
    msg = msg & "- PDF ixracı" & vbCrLf
    
    MsgBox msg, vbInformation, "Sistem Haqqında"
End Sub

Public Sub OpenUserGuide()
    ' İstifadə təlimatını aç
    Dim filePath As String
    filePath = ThisWorkbook.Path & "\VBA\Istifade_Telimati_VBA.md"
    
    If Dir(filePath) <> "" Then
        ' Faylı aç
        Shell "cmd /c start " & filePath, vbHide
    Else
        MsgBox "İstifadə təlimatı tapılmadı!", vbExclamation
    End If
End Sub
