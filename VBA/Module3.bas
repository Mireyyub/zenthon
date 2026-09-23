Option Explicit

' ============================================
' Aylıq Növbətçilik Planlaşdırma Sistemi v2.0
' VBA Modul 3 - Köməkçi Funksiya (Uzun funksiya)
' ============================================

Private Function GetParameters() As Object
    Dim params As Object
    Set params = CreateObject("Scripting.Dictionary")
    
    Dim wsParams As Worksheet
    Set wsParams = ThisWorkbook.Sheets("PARAMETRLƏR")
    
    ' Növbə əmsalları
    params("Hissə növbətçisi") = wsParams.Range("B5").Value
    params("Hissə növbətçisinin köməkçisi") = wsParams.Range("B6").Value
    params("Nəzarət-buraxılış məntəqəsi növbətçisi") = wsParams.Range("B7").Value
    params("Park növbətçisi") = wsParams.Range("B8").Value
    params("Yeməkxana növbətçisi") = wsParams.Range("B9").Value
    params("Otaq növbətçisi") = wsParams.Range("B10").Value
    
    ' İstirahət parametrləri
    params("min_rest_days") = wsParams.Range("B13").Value
    params("consecutive_limit") = wsParams.Range("B14").Value
    params("repeat_limit") = wsParams.Range("B15").Value
    params("max_consecutive") = wsParams.Range("B16").Value
    
    ' Balans parametrləri
    params("balance_tolerance") = wsParams.Range("B19").Value
    params("previous_months_weight") = wsParams.Range("B20").Value
    params("weekend_weight") = wsParams.Range("B21").Value
    params("heavy_novbe_limit") = wsParams.Range("B22").Value
    
    Set GetParameters = params
End Function

Private Function GetActivePeople() As Variant
    Dim wsPeople As Worksheet
    Set wsPeople = ThisWorkbook.Sheets("ŞƏXSLƏR")
    
    Dim people() As Variant
    Dim row As Integer, count As Integer
    Dim lastRow As Integer
    
    lastRow = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    If lastRow < 5 Then
        ReDim people(0)
        GetActivePeople = people
        Exit Function
    End If
    
    ReDim people(1 To lastRow - 4, 1 To 2)
    count = 0
    
    For row = 5 To lastRow
        Dim fullName As String
        fullName = wsPeople.Cells(row, 5).Value
        
        If fullName <> "" And wsPeople.Cells(row, 7).Value = "Aktiv" Then
            count = count + 1
            people(count, 1) = fullName
        End If
    Next row
    
    If count = 0 Then
        ReDim people(0)
    Else
        ReDim Preserve people(1 To count, 1 To 1)
    End If
    
    GetActivePeople = people
End Function

Private Function GetAbsenceDates() As Object
    Dim absences As Object
    Set absences = CreateObject("Scripting.Dictionary")
    
    Dim wsAbsence As Worksheet
    Set wsAbsence = ThisWorkbook.Sheets("YOXDUR-MƏZUNİYYƏT")
    
    Dim row As Integer, lastRow As Integer
    lastRow = wsAbsence.Cells(wsAbsence.Rows.Count, "A").End(xlUp).Row
    
    For row = 5 To lastRow
        Dim person As String
        person = wsAbsence.Cells(row, 1).Value
        
        If person <> "" Then
            Dim startDate As Date
            startDate = wsAbsence.Cells(row, 3).Value
            
            Dim days As Integer
            days = wsAbsence.Cells(row, 4).Value
            
            If days > 0 Then
                Dim endDate As Date
                endDate = startDate + days - 1
                
                If Not absences.Exists(person) Then
                    absences.Add person, CreateObject("Scripting.Dictionary")
                End If
            End If
        End If
    Next row
    
    Set GetAbsenceDates = absences
End Function

Private Function GetMonthNumber(monthName As String) As Integer
    Dim months() As String
    months = Array("Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun", "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr")
    
    Dim i As Integer
    For i = LBound(months) To UBound(months)
        If months(i) = monthName Then
            GetMonthNumber = i + 1
            Exit Function
        End If
    Next i
    
    GetMonthNumber = 1
End Function

Private Function IsPersonAbsent(person As String, dateObj As Date, wsAbsence As Worksheet) As Boolean
    Dim lastRow As Integer
    lastRow = wsAbsence.Cells(wsAbsence.Rows.Count, "A").End(xlUp).Row
    
    Dim row As Integer
    For row = 5 To lastRow
        Dim p As String
        p = wsAbsence.Cells(row, 1).Value
        
        If p = person Then
            Dim startDate As Date
            startDate = wsAbsence.Cells(row, 3).Value
            
            Dim days As Integer
            days = wsAbsence.Cells(row, 4).Value
            
            If days > 0 Then
                Dim endDate As Date
                endDate = startDate + days - 1
                
                If dateObj >= startDate And dateObj <= endDate Then
                    IsPersonAbsent = True
                    Exit Function
                End If
            End If
        End If
    Next row
    
    IsPersonAbsent = False
End Function

Private Function IsPersonSuitable(person As String, novbeType As String, wsPeople As Worksheet) As Boolean
    Dim lastRow As Integer
    lastRow = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    Dim row As Integer
    For row = 5 To lastRow
        Dim fullName As String
        fullName = wsPeople.Cells(row, 5).Value
        
        If fullName = person Then
            Dim novbeTypes() As String
            novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
            
            Dim i As Integer, found As Boolean
            found = False
            
            For i = LBound(novbeTypes) To UBound(novbeTypes)
                If novbeTypes(i) = novbeType Then
                    Dim uygun As String
                    uygun = wsPeople.Cells(row, 9 + i).Value
                    IsPersonSuitable = (uygun = " Uyğundur")
                    found = True
                    Exit For
                End If
            Next i
            
            If Not found Then
                IsPersonSuitable = True
            End If
            
            Exit Function
        End If
    Next row
    
    IsPersonSuitable = True
End Function

Private Function GetLastNovbeDate(person As String, novbeType As String, currentDate As Date, wsSchedule As Worksheet) As Date
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    Dim col As Integer
    For col = LBound(novbeTypes) To UBound(novbeTypes)
        If novbeTypes(col) = novbeType Then
            Exit For
        End If
    Next col
    
    Dim year As Integer, month As Integer
    year = wsSchedule.Range("B4").Value
    month = GetMonthNumber(wsSchedule.Range("E4").Value)
    
    Dim lastDate As Date
    lastDate = 0
    
    Dim day As Integer
    For day = 1 To Day(DateSerial(year, month + 1, 1) - DateSerial(year, month, 1))
        If day >= currentDate - Day(currentDate) + 1 Then Exit For
        
        Dim p As String
        p = wsSchedule.Cells(day + 7, col + 5).Value
        
        If p = person Then
            lastDate = DateSerial(year, month, day)
        End If
    Next day
    
    GetLastNovbeDate = lastDate
End Function

Private Sub GenerateScheduleForNovbeType(novbeType As String, year As Integer, month As Integer, numDays As Integer, people() As Variant, absences As Object, params As Object, wsSchedule As Worksheet)
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
    
    ' Hər tarix üçün şəxs təyin et
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
        
        ' Random şəxs seç (sadə alqoritm)
        Dim randomIndex As Integer
        Randomize
        randomIndex = Int((candCount * Rnd) + 1)
        
        wsSchedule.Cells(day + 7, col + 5).Value = candidates(randomIndex)
    Next day
End Sub

Private Function GetHefteGunu(dateObj As Date) As String
    Dim days() As String
    days = Array("Bazar ertəsi", "Çərşənbə axşamı", "Çərşənbə", "Cümə axşamı", "Cümə", "Şənbə", "Bazar")
    
    Dim weekday As Integer
    weekday = Weekday(dateObj, vbMonday)
    
    If weekday >= 1 And weekday <= 7 Then
        GetHefteGunu = days(weekday - 1)
    Else
        GetHefteGunu = ""
    End If
End Function
