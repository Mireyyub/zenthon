Option Explicit

' ============================================
' Aylıq Növbətçilik Planlaşdırma Sistemi v2.0
' VBA Modul 2 - Köməkçi Funksiya
' ============================================

Public Sub ValidateSchedule()
    ' Cədvəli yoxlayır və qayda pozuntularını göstərir
    Application.ScreenUpdating = False
    
    Dim issues As Collection
    Set issues = New Collection
    
    Dim wsSchedule As Worksheet
    Dim wsPeople As Worksheet
    Dim wsAbsence As Worksheet
    Dim wsParams As Worksheet
    
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    Set wsPeople = ThisWorkbook.Sheets("ŞƏXSLƏR")
    Set wsAbsence = ThisWorkbook.Sheets("YOXDUR-MƏZUNİYYƏT")
    Set wsParams = ThisWorkbook.Sheets("PARAMETRLƏR")
    
    ' Parametrləri oxu
    Dim minRestDays As Integer
    minRestDays = wsParams.Range("B13").Value
    
    Dim year As Integer, month As Integer, numDays As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    numDays = Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
    
    Dim day As Integer, col As Integer
    Dim dateObj As Date
    Dim person As String
    Dim novbeType As String
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    ' Hər tarix üçün yoxla
    For day = 1 To numDays
        dateObj = DateSerial(year, month, day)
        
        For col = 0 To UBound(novbeTypes)
            person = wsSchedule.Cells(day + 7, col + 5).Value
            novbeType = novbeTypes(col)
            
            If person <> "" Then
                ' 1. Yoxluqda olub-olmadığını yoxla
                If IsPersonAbsent(person, dateObj, wsAbsence) Then
                    issues.Add "  " & Format(dateObj, "dd.mm.yyyy") & " - " & novbeType & ": " & person & " yoxluqdadır"
                End If
                
                ' 2. Növbə uyğunluğunu yoxla
                If Not IsPersonSuitable(person, novbeType, wsPeople) Then
                    issues.Add "  " & Format(dateObj, "dd.mm.yyyy") & " - " & novbeType & ": " & person & " uyğun deyil"
                End If
                
                ' 3. İstirahət qaydasını yoxla
                Dim lastDate As Date
                lastDate = GetLastNovbeDate(person, novbeType, dateObj, wsSchedule)
                If lastDate <> 0 Then
                    If DateDiff("d", lastDate, dateObj) < minRestDays Then
                        issues.Add "  " & Format(dateObj, "dd.mm.yyyy") & " - " & novbeType & ": " & person & " - İstirahət qısa (" & DateDiff("d", lastDate, dateObj) & " gün)"
                    End If
                End If
            End If
        Next col
    Next day
    
    ' Boş növbələri tap
    For day = 1 To numDays
        For col = 0 To UBound(novbeTypes)
            person = wsSchedule.Cells(day + 7, col + 5).Value
            If person = "" Then
                issues.Add "  " & Format(DateSerial(year, month, day), "dd.mm.yyyy") & " - " & novbeTypes(col) & ": Boş"
            End If
        Next col
    Next day
    
    ' Nəticəni göstər
    If issues.Count > 0 Then
        Dim msg As String
        msg = "Aşkar edilmiş problemlər (" & issues.Count & "):" & vbCrLf & vbCrLf
        
        Dim i As Integer
        For i = 1 To issues.Count
            msg = msg & i & ". " & issues(i) & vbCrLf
            If i >= 10 Then
                msg = msg & "... (davamı görmək üçün DASHBOARD vərəqinə baxın)"
                Exit For
            End If
        Next i
        
        MsgBox msg, vbExclamation, "Qayda Pozuntuları"
    Else
        MsgBox "Heç bir problem aşkar edilmədi!", vbInformation, "Uğurlu!"
    End If
    
    Application.ScreenUpdating = True
End Sub

Public Sub ClearSchedule()
    ' Cədvəli sıfırlayır
    Application.ScreenUpdating = False
    
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim numDays As Integer
    numDays = 31
    
    ' Növbə sütunlarını sıfırla
    Dim col As Integer
    For col = 5 To 10
        wsSchedule.Range(wsSchedule.Cells(8, col), wsSchedule.Cells(38, col)).ClearContents
    Next col
    
    MsgBox "Cədvəl sıfırlandı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Public Sub ExportToPDF()
    ' Cədvəli PDF olaraq ixrac edir
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim filePath As String
    filePath = ThisWorkbook.Path & "\Novbe_Qrafik_" & Format(Now(), "yyyy-mm-dd") & ".pdf"
    
    wsSchedule.ExportAsFixedFormat Type:=xlTypePDF, Filename:=filePath, Quality:=xlQualityStandard, _
        IncludeDocProperties:=True, IgnorePrintAreas:=False, OpenAfterPublish:=True
    
    MsgBox "PDF olaraq ixrac edildi: " & filePath, vbInformation, "Uğurlu!"
End Sub

Public Sub ShowHelp()
    Dim msg As String
    msg = "Aylıq Növbətçilik Planlaşdırma Sistemi v2.0" & vbCrLf & vbCrLf
    msg = msg & "Düymələr:" & vbCrLf
    msg = msg & "- NÖVBƏLƏRİ YARAT: Avtomatik növbə generasiyası" & vbCrLf
    msg = msg & "- YOXLAYIN: Cədvəli yoxla" & vbCrLf
    msg = msg & "- SIFIRLA: Cədvəli sıfırla" & vbCrLf
    msg = msg & "- PDF: PDF olaraq ixrac et" & vbCrLf & vbCrLf
    msg = msg & "2026 - Vibe Code (Mistral AI)"
    
    MsgBox msg, vbInformation, "Kömək"
End Sub
