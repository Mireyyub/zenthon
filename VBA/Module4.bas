Option Explicit

' ============================================
' Aylıq Növbətçilik Planlaşdırma Sistemi v3.0
' VBA Modul 4 - Avtomatik Yeniləmə və Şəxs Dəyişdirmə
' ============================================

' ============================================
' AVTOMATİK AY YENİLƏMƏ
' ============================================

Public Sub UpdateScheduleDates()
    ' Ay və ya il dəyişdikdə avtomatik olaraq tarixləri yeniləyir
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    
    On Error GoTo ErrorHandler
    
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim year As Integer, month As Integer, numDays As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    numDays = Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
    
    ' Tarix sütununu yenilə
    Dim day As Integer
    For day = 1 To numDays
        wsSchedule.Cells(day + 7, 1).Value = day ' №
        wsSchedule.Cells(day + 7, 2).Value = DateSerial(year, month, day) ' Tarix
        wsSchedule.Cells(day + 7, 2).NumberFormat = "dd.mm.yyyy"
        
        ' Həftə gününü yenilə
        Dim hefteGunu As String
        hefteGunu = GetHefteGunu(DateSerial(year, month, day))
        wsSchedule.Cells(day + 7, 3).Value = hefteGunu
        
        ' Ay adı
        wsSchedule.Cells(day + 7, 4).Value = wsSchedule.Range("E4").Value
    Next day
    
    ' Artıq günləri (əgər varsa) boşaldır
    If numDays < 31 Then
        For day = numDays + 1 To 31
            wsSchedule.Cells(day + 7, 1).Value = ""
            wsSchedule.Cells(day + 7, 2).Value = ""
            wsSchedule.Cells(day + 7, 3).Value = ""
            wsSchedule.Cells(day + 7, 4).Value = ""
            
            ' Növbə sütunlarını boşaldır
            Dim col As Integer
            For col = 5 To 10
                wsSchedule.Cells(day + 7, col).Value = ""
            Next col
        Next day
    End If
    
    ' Avtomatik olaraq növbələri generasiya et
    Dim answer As VbMsgBoxResult
    answer = MsgBox("Yeni ay üçün avtomatik olaraq növbələr yaradılsınmı?", vbQuestion + vbYesNo, "Avtomatik Generasiya")
    
    If answer = vbYes Then
        Call GenerateSchedule
    End If
    
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Xəta baş verdi: " & Err.Description, vbCritical, "Xəta"
    Application.EnableEvents = True
    Application.ScreenUpdating = True
End Sub

' Worksheet_Change event üçün
Private Sub Worksheet_Change(ByVal Target As Range)
    ' Bu kod AYLIQ QRAFİK vərəqində olmalıdır
    ' OnError Resume Next ' Xəta olsa da davam etsin
    
    If Not Intersect(Target, ThisWorkbook.Sheets("AYLIQ QRAFİK").Range("B4,E4")) Is Nothing Then
        Call UpdateScheduleDates
    End If
End Sub

' ============================================
' ŞƏXS DƏYİŞDİRMƏ INTERFEYSI
' ============================================

Public Sub ShowChangePersonForm()
    ' UserForm1-i göstər
    UserForm1.Show
End Sub

Public Sub ChangePerson(OldPerson As String, NewPerson As String, NovbeDate As Date, NovbeType As String, Reason As String)
    ' Şəxsi dəyişdir
    Application.ScreenUpdating = False
    
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim year As Integer, month As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    
    Dim day As Integer
    day = Day(NovbeDate)
    
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    Dim col As Integer
    For col = LBound(novbeTypes) To UBound(novbeTypes)
        If novbeTypes(col) = NovbeType Then
            Exit For
        End If
    Next col
    
    ' Yoxla ki, köhnə şəxs orada olsun
    If wsSchedule.Cells(day + 7, col + 5).Value <> OldPerson Then
        MsgBox "Xəta: " & OldPerson & " " & Format(NovbeDate, "dd.mm.yyyy") & " tarixində " & NovbeType & " kimi qeyd edilməyib!", vbExclamation
        Exit Sub
    End If
    
    ' Yeni şəxsi təyin et
    wsSchedule.Cells(day + 7, col + 5).Value = NewPerson
    
    ' Dəyişiklikləri jurnalda qeyd et
    Call LogChange(OldPerson, NewPerson, NovbeDate, NovbeType, Reason)
    
    ' Cədvəli yoxla
    Call ValidateSchedule
    
    MsgBox "✅ Şəxs uğurla dəyişdirildi!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Private Sub LogChange(OldPerson As String, NewPerson As String, NovbeDate As Date, NovbeType As String, Reason As String)
    ' Dəyişiklikləri DƏYİŞİKLİK JURNALI vərəqinə qeyd et
    Dim wsLog As Worksheet
    Set wsLog = ThisWorkbook.Sheets("DƏYİŞİKLİK JURNALI")
    
    Dim lastRow As Integer
    lastRow = wsLog.Cells(wsLog.Rows.Count, "A").End(xlUp).Row + 1
    
    ' Tarix
    wsLog.Cells(lastRow, 1).Value = Date
    wsLog.Cells(lastRow, 1).NumberFormat = "dd.mm.yyyy"
    
    ' Saat
    wsLog.Cells(lastRow, 2).Value = Time
    wsLog.Cells(lastRow, 2).NumberFormat = "hh:mm"
    
    ' Növbə tarixi
    wsLog.Cells(lastRow, 3).Value = NovbeDate
    wsLog.Cells(lastRow, 3).NumberFormat = "dd.mm.yyyy"
    
    ' Növbə növü
    wsLog.Cells(lastRow, 4).Value = NovbeType
    
    ' Əvvəlki şəxs
    wsLog.Cells(lastRow, 5).Value = OldPerson
    
    ' Yeni şəxs
    wsLog.Cells(lastRow, 6).Value = NewPerson
    
    ' Dəyişiklik səbəbi
    wsLog.Cells(lastRow, 7).Value = Reason
    
    ' Qeyd (boş)
    wsLog.Cells(lastRow, 8).Value = ""
End Sub

' ============================================
' TARİXÇƏ VƏ STATİSTİKA
' ============================================

Public Sub SaveToHistory()
    ' Cari ayın məlumatlarını tarixçəyə saxla
    Application.ScreenUpdating = False
    
    Dim wsSchedule As Worksheet
    Dim wsHistory As Worksheet
    
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    ' NOVBE_TARIXÇƏSİ vərəqini yoxla
    On Error Resume Next
    Set wsHistory = ThisWorkbook.Sheets("NOVBE_TARIXÇƏSİ")
    On Error GoTo 0
    
    If wsHistory Is Nothing Then
        ' Vərəq yoxdursa, yarat
        Set wsHistory = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        wsHistory.Name = "NOVBE_TARIXÇƏSİ"
        
        ' Başlıq sətri
        wsHistory.Cells(1, 1).Value = "İl"
        wsHistory.Cells(1, 2).Value = "Ay"
        wsHistory.Cells(1, 3).Value = "Tarix"
        wsHistory.Cells(1, 4).Value = "Hissə növbətçisi"
        wsHistory.Cells(1, 5).Value = "Köməkçi"
        wsHistory.Cells(1, 6).Value = "NBM"
        wsHistory.Cells(1, 7).Value = "Park"
        wsHistory.Cells(1, 8).Value = "Yeməkxana"
        wsHistory.Cells(1, 9).Value = "Otaq"
        
        ' Formatlaşdırma
        Dim i As Integer
        For i = 1 To 9
            wsHistory.Cells(1, i).Font.Bold = True
            wsHistory.Cells(1, i).Interior.Color = RGB(200, 230, 255)
        Next i
    End If
    
    ' Cari ayın məlumatlarını saxla
    Dim year As Integer, month As Integer, numDays As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    numDays = Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
    
    Dim lastRow As Integer
    lastRow = wsHistory.Cells(wsHistory.Rows.Count, "A").End(xlUp).Row + 1
    
    Dim day As Integer, col As Integer
    For day = 1 To numDays
        wsHistory.Cells(lastRow + day - 1, 1).Value = year
        wsHistory.Cells(lastRow + day - 1, 2).Value = wsSchedule.Range("E4").Value
        wsHistory.Cells(lastRow + day - 1, 3).Value = DateSerial(year, month, day)
        wsHistory.Cells(lastRow + day - 1, 3).NumberFormat = "dd.mm.yyyy"
        
        For col = 5 To 10
            wsHistory.Cells(lastRow + day - 1, col - 1).Value = wsSchedule.Cells(day + 7, col).Value
        Next col
    Next day
    
    MsgBox "✅ Cari ay tarixçəyə saxlanıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Public Sub CalculatePersonStatistics()
    ' Şəxs statistikası hesablamaq
    Application.ScreenUpdating = False
    
    Dim wsStats As Worksheet
    
    ' ŞƏXS_STATİSTİKASI vərəqini yoxla
    On Error Resume Next
    Set wsStats = ThisWorkbook.Sheets("ŞƏXS_STATİSTİKASI")
    On Error GoTo 0
    
    If wsStats Is Nothing Then
        ' Vərəq yoxdursa, yarat
        Set wsStats = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        wsStats.Name = "ŞƏXS_STATİSTİKASI"
    End If
    
    ' Başlıq sətri
    wsStats.Cells(1, 1).Value = "Şəxs"
    wsStats.Cells(1, 2).Value = "Ümumi iştirak"
    wsStats.Cells(1, 3).Value = "Hissə növbətçisi"
    wsStats.Cells(1, 4).Value = "Köməkçi"
    wsStats.Cells(1, 5).Value = "NBM"
    wsStats.Cells(1, 6).Value = "Park"
    wsStats.Cells(1, 7).Value = "Yeməkxana"
    wsStats.Cells(1, 8).Value = "Otaq"
    wsStats.Cells(1, 9).Value = "Həftəsonu iştirak"
    wsStats.Cells(1, 10).Value = "İştirak nisbəti (%)"
    
    ' Formatlaşdırma
    Dim i As Integer
    For i = 1 To 10
        wsStats.Cells(1, i).Font.Bold = True
        wsStats.Cells(1, i).Interior.Color = RGB(200, 230, 255)
    Next i
    
    ' Şəxsləri oxu
    Dim wsPeople As Worksheet
    Set wsPeople = ThisWorkbook.Sheets("ŞƏXSLƏR")
    
    Dim lastRowPeople As Integer
    lastRowPeople = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    ' Hər şəxs üçün statistika hesabla
    Dim statsRow As Integer
    statsRow = 2
    
    For i = 5 To lastRowPeople
        Dim person As String
        person = wsPeople.Cells(i, 5).Value
        
        If person <> "" Then
            ' Ümumi iştirak
            Dim total As Integer
            total = Application.WorksheetFunction.CountIf(wsHistory.Range("D:D"), person) + _
                   Application.WorksheetFunction.CountIf(wsHistory.Range("E:E"), person) + _
                   Application.WorksheetFunction.CountIf(wsHistory.Range("F:F"), person) + _
                   Application.WorksheetFunction.CountIf(wsHistory.Range("G:G"), person) + _
                   Application.WorksheetFunction.CountIf(wsHistory.Range("H:H"), person) + _
                   Application.WorksheetFunction.CountIf(wsHistory.Range("I:I"), person)
            
            ' Hər növbə üçün
            Dim novbeTypes() As String
            novbeTypes = Array("Hissə növbətçisi", "Köməkçi", "NBM", "Park", "Yeməkxana", "Otaq")
            
            Dim novbeCounts(1 To 6) As Integer
            Dim j As Integer
            For j = LBound(novbeTypes) To UBound(novbeTypes)
                novbeCounts(j + 1) = Application.WorksheetFunction.CountIf(wsHistory.Columns(j + 3), person)
            Next j
            
            ' Həftəsonu iştirak
            Dim weekendCount As Integer
            weekendCount = CountWeekendParticipation(person, wsHistory)
            
            ' İştirak nisbəti
            Dim participationRate As Double
            If total > 0 Then
                participationRate = (total / (GetTotalDaysInHistory(wsHistory) / GetActivePeopleCount(wsPeople))) * 100
            Else
                participationRate = 0
            End If
            
            ' Məlumatları yaz
            wsStats.Cells(statsRow, 1).Value = person
            wsStats.Cells(statsRow, 2).Value = total
            
            For j = 1 To 6
                wsStats.Cells(statsRow, j + 2).Value = novbeCounts(j)
            Next j
            
            wsStats.Cells(statsRow, 9).Value = weekendCount
            wsStats.Cells(statsRow, 10).Value = participationRate
            wsStats.Cells(statsRow, 10).NumberFormat = "0.00%"
            
            statsRow = statsRow + 1
        End If
    Next i
    
    MsgBox "✅ Şəxs statistikası hesablanıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Private Function CountWeekendParticipation(person As String, wsHistory As Worksheet) As Integer
    ' Həftəsonu iştirakını say
    Dim count As Integer
    count = 0
    
    Dim lastRow As Integer
    lastRow = wsHistory.Cells(wsHistory.Rows.Count, "A").End(xlUp).Row
    
    Dim i As Integer
    For i = 2 To lastRow
        Dim dateObj As Date
        dateObj = wsHistory.Cells(i, 3).Value
        
        Dim hefteGunu As String
        hefteGunu = GetHefteGunu(dateObj)
        
        If InStr("Cümə,Şənbə,Bazar", hefteGunu) > 0 Then
            Dim j As Integer
            For j = 4 To 9
                If wsHistory.Cells(i, j).Value = person Then
                    count = count + 1
                    Exit For
                End If
            Next j
        End If
    Next i
    
    CountWeekendParticipation = count
End Function

Private Function GetTotalDaysInHistory(wsHistory As Worksheet) As Integer
    Dim lastRow As Integer
    lastRow = wsHistory.Cells(wsHistory.Rows.Count, "A").End(xlUp).Row
    
    If lastRow < 2 Then
        GetTotalDaysInHistory = 0
    Else
        GetTotalDaysInHistory = lastRow - 1
    End If
End Function

Private Function GetActivePeopleCount(wsPeople As Worksheet) As Integer
    Dim lastRow As Integer
    lastRow = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    Dim count As Integer
    count = 0
    
    Dim i As Integer
    For i = 5 To lastRow
        If wsPeople.Cells(i, 7).Value = "Aktiv" Then
            count = count + 1
        End If
    Next i
    
    GetActivePeopleCount = count
End Function

' ============================================
' QRAFİK VƏ VİZUALİZASİYA
' ============================================

Public Sub CreateWeekendLoadChart()
    ' Həftəsonu yükü qrafiki yarad
    Application.ScreenUpdating = False
    
    Dim wsBalance As Worksheet
    Set wsBalance = ThisWorkbook.Sheets("BALANS")
    
    ' Qrafik üçün yer
    Dim chartRange As Range
    Set chartRange = wsBalance.Range("F5:H12") ' Cümə, Şənbə, Bazar sütunları
    
    ' Qrafik yarat
    Dim chartObj As ChartObject
    On Error Resume Next
    Set chartObj = wsBalance.ChartObjects("Həftəsonu Yükü Qrafiki")
    On Error GoTo 0
    
    If chartObj Is Nothing Then
        Set chartObj = wsBalance.ChartObjects.Add(Left:=500, Width:=400, Top:=200, Height:=300)
        chartObj.Name = "Həftəsonu Yükü Qrafiki"
    End If
    
    With chartObj.Chart
        .ChartType = xlColumnClustered
        .SetSourceData Source:=chartRange
        .HasTitle = True
        .ChartTitle.Text = "Həftəsonu Yükü Qrafiki"
        
        ' Ox adları
        .Axes(xlCategory).HasTitle = True
        .Axes(xlCategory).AxisTitle.Text = "Şəxslər"
        
        .Axes(xlValue).HasTitle = True
        .Axes(xlValue).AxisTitle.Text = "Say"
        
        ' Seriyaların adları
        .SeriesCollection(1).Name = "Cümə"
        .SeriesCollection(2).Name = "Şənbə"
        .SeriesCollection(3).Name = "Bazar"
    End With
    
    MsgBox "✅ Həftəsonu yükü qrafiki yaradıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

Public Sub CreateLoadDistributionChart()
    ' Yük paylanması qrafiki
    Application.ScreenUpdating = False
    
    Dim wsBalance As Worksheet
    Set wsBalance = ThisWorkbook.Sheets("BALANS")
    
    ' Qrafik üçün yer
    Dim chartRange As Range
    Set chartRange = wsBalance.Range("C5:C12") ' Ümumi xidmət yükü
    
    ' Qrafik yarat
    Dim chartObj As ChartObject
    On Error Resume Next
    Set chartObj = wsBalance.ChartObjects("Yük Paylanması")
    On Error GoTo 0
    
    If chartObj Is Nothing Then
        Set chartObj = wsBalance.ChartObjects.Add(Left:=500, Width:=400, Top:=550, Height:=300)
        chartObj.Name = "Yük Paylanması"
    End If
    
    With chartObj.Chart
        .ChartType = xlPie
        .SetSourceData Source:=chartRange
        .HasTitle = True
        .ChartTitle.Text = "Xidmət Yükü Paylanması"
        
        ' Data Labels
        .ApplyDataLabels
        .SeriesCollection(1).DataLabels.ShowPercentage = True
        .SeriesCollection(1).DataLabels.ShowValue = True
    End With
    
    MsgBox "✅ Yük paylanması qrafiki yaradıldı!", vbInformation, "Uğurlu!"
    
    Application.ScreenUpdating = True
End Sub

' ============================================
' Aİ OPTİMALLAŞDIRMA
' ============================================

Public Sub OptimizeSchedule()
    ' AI əsaslı optimallaşdırma
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    Dim startTime As Double
    startTime = Timer
    
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Dim year As Integer, month As Integer, numDays As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    numDays = Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
    
    ' Parametrləri oxu
    Dim params As Object
    Set params = GetParameters()
    
    ' Aktiv şəxsləri oxu
    Dim people() As Variant
    people = GetActivePeople()
    
    ' Yoxluq tarixlərini oxu
    Dim absences As Object
    Set absences = GetAbsenceDates()
    
    ' Cədvəli sıfırla
    ClearSchedule numDays
    
    ' Optimallaşdırılmış cədvəli yarad
    Call OptimizeScheduleForAllNovbeTypes(year, month, numDays, people, absences, params, wsSchedule)
    
    MsgBox "✅ Optimallaşdırılmış cədvəl yaradıldı!" & vbCrLf & _
           "Müddət: " & Format(Timer - startTime, "0.00") & " saniyə", vbInformation, "Uğurlu!"
    
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
End Sub

Private Sub OptimizeScheduleForAllNovbeTypes(year As Integer, month As Integer, numDays As Integer, people() As Variant, absences As Object, params As Object, wsSchedule As Worksheet)
    ' Bütün növbələr üçün optimallaşdırılmış cədvəl yarad
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    ' Hər növbə üçün
    Dim i As Integer
    For i = LBound(novbeTypes) To UBound(novbeTypes)
        Call OptimizeScheduleForNovbeType(novbeTypes(i), year, month, numDays, people, absences, params, wsSchedule)
    Next i
End Sub

Private Sub OptimizeScheduleForNovbeType(novbeType As String, year As Integer, month As Integer, numDays As Integer, people() As Variant, absences As Object, params As Object, wsSchedule As Worksheet)
    ' Optimallaşdırılmış alqoritm ilə cədvəl yarad
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    Dim col As Integer
    For col = LBound(novbeTypes) To UBound(novbeTypes)
        If novbeTypes(col) = novbeType Then
            Exit For
        End If
    Next col
    
    ' Bu növbəyə uyğun şəxsləri tap
    Dim suitablePeople() As Variant
    Dim count As Integer
    count = 0
    
    Dim i As Integer
    For i = LBound(people, 1) To UBound(people, 1)
        count = count + 1
        ReDim Preserve suitablePeople(1 To count)
        suitablePeople(count) = people(i, 1)
    Next i
    
    If count = 0 Then
        MsgBox "  " & novbeType & " üçün uyğun şəxs tapılmadı!" & vbCrLf, vbExclamation
        Exit Sub
    End If
    
    ' Hər tarix üçün ən optimal şəxsi seç
    Dim day As Integer
    For day = 1 To numDays
        Dim dateObj As Date
        dateObj = DateSerial(year, month, day)
        
        ' Mövcud namizədləri tap
        Dim candidates() As Variant
        Dim candCount As Integer
        candCount = 0
        
        For i = 1 To count
            Dim person As String
            person = suitablePeople(i)
            
            If Not IsPersonAbsent(person, dateObj, ThisWorkbook.Sheets("YOXDUR-MƏZUNİYYƏT")) Then
                candCount = candCount + 1
                ReDim Preserve candidates(1 To candCount)
                candidates(candCount) = person
            End If
        Next i
        
        If candCount = 0 Then
            wsSchedule.Cells(day + 7, col + 5).Value = ""
            Exit Sub
        End If
        
        ' Ən optimal namizədi seç
        Dim bestCandidate As String
        bestCandidate = SelectOptimalCandidate(candidates, dateObj, novbeType, wsSchedule, params, absences)
        
        wsSchedule.Cells(day + 7, col + 5).Value = bestCandidate
    Next day
End Sub

Private Function SelectOptimalCandidate(candidates() As Variant, dateObj As Date, novbeType As String, wsSchedule As Worksheet, params As Object, absences As Object) As String
    ' Namizədləri qiymətləndir və ən optimanı seç
    Dim scores() As Double
    ReDim scores(1 To UBound(candidates, 1))
    
    Dim i As Integer
    For i = 1 To UBound(candidates, 1)
        scores(i) = CalculateOptimalScore(candidates(i), dateObj, novbeType, wsSchedule, params, absences)
    Next i
    
    ' Ən yüksək xalı toplayan namizədi seç
    Dim bestIndex As Integer
    Dim bestScore As Double
    bestScore = -1000000
    bestIndex = 1
    
    For i = 1 To UBound(scores, 1)
        If scores(i) > bestScore Then
            bestScore = scores(i)
            bestIndex = i
        End If
    Next i
    
    SelectOptimalCandidate = candidates(bestIndex)
End Function

Private Function CalculateOptimalScore(person As String, dateObj As Date, novbeType As String, wsSchedule As Worksheet, params As Object, absences As Object) As Double
    ' Optimallaşdırma üçün xal hesablama
    Dim score As Double
    score = 0
    
    ' 1. Cari yük (çox yükü olan prioriteti aşağı - 40%)
    Dim currentLoad As Double
    currentLoad = CalculatePersonLoad(person, wsSchedule, params)
    score = score - currentLoad * 40
    
    ' 2. Həftəsonu yükü (25%)
    Dim hefteGunu As String
    hefteGunu = GetHefteGunu(dateObj)
    If InStr("Cümə,Şənbə,Bazar", hefteGunu) > 0 Then
        Dim weekendLoad As Integer
        weekendLoad = CountWeekendNovbe(person, wsSchedule)
        score = score - weekendLoad * params("weekend_weight") * 25
    End If
    
    ' 3. İstirahət qaydası (20%)
    Dim lastDate As Date
    lastDate = GetLastNovbeDate(person, novbeType, dateObj, wsSchedule)
    If lastDate <> 0 Then
        Dim daysDiff As Integer
        daysDiff = DateDiff("d", lastDate, dateObj)
        If daysDiff < params("min_rest_days") Then
            score = score - 1000 * 20 ' Çox böyük cəza
        End If
    End If
    
    ' 4. Eyni növbənin ardıcıl sayını (10%)
    Dim consecutiveCount As Integer
    consecutiveCount = CountConsecutive(person, novbeType, dateObj, wsSchedule)
    If consecutiveCount >= params("max_consecutive") Then
        score = score - 500 * 10
    End If
    
    ' 5. Yük bərabərliyi (5%)
    Dim avgLoad As Double
    avgLoad = CalculateAverageLoad(wsSchedule, params)
    Dim loadDiff As Double
    loadDiff = currentLoad - avgLoad
    If loadDiff > 0 Then
        score = score - loadDiff * 5
    Else
        score = score + Abs(loadDiff) * 5
    End If
    
    ' 6. Random faktor (0.1%)
    score = score + Rnd() * 0.1
    
    CalculateOptimalScore = score
End Function

Private Function CalculateAverageLoad(wsSchedule As Worksheet, params As Object) As Double
    ' Orta yükü hesabla
    Dim totalLoad As Double
    totalLoad = 0
    
    Dim wsPeople As Worksheet
    Set wsPeople = ThisWorkbook.Sheets("ŞƏXSLƏR")
    
    Dim lastRow As Integer
    lastRow = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    Dim i As Integer
    For i = 5 To lastRow
        Dim person As String
        person = wsPeople.Cells(i, 5).Value
        If person <> "" And wsPeople.Cells(i, 7).Value = "Aktiv" Then
            totalLoad = totalLoad + CalculatePersonLoad(person, wsSchedule, params)
        End If
    Next i
    
    Dim activeCount As Integer
    activeCount = GetActivePeopleCount(wsPeople)
    
    If activeCount > 0 Then
        CalculateAverageLoad = totalLoad / activeCount
    Else
        CalculateAverageLoad = 0
    End If
End Function
