VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E78-00AA00574A4F} UserForm1
   Caption         =   "Şəxs Dəyişdirmə"
   ClientHeight    =   300
   ClientLeft      =   0
   ClientTop       =   0
   ClientWidth     =   400
   OleObjectBlob   =   "UserForm1.frx":00000000000000000000000000000000
End
Attribute VB_Name = "UserForm1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True

' UserForm1.frm - Şəxs Dəyişdirmə Interfeysi

Private Sub UserForm_Initialize()
    ' UserForm-u hazırla
    Me.Caption = "Şəxs Dəyişdirmə - Növbətçilik Sistemi v3.0"
    
    ' ComboBox-ları doldur
    Call FillPeopleComboBox
    Call FillNovbeTypeComboBox
    Call FillReasonComboBox
    
    ' Default dəyərlər
    Me.TextBoxDate.Value = Date
    Me.TextBoxDate.Format = "dd.mm.yyyy"
    
    ' Focus
    Me.ComboBoxOldPerson.SetFocus
End Sub

Private Sub FillPeopleComboBox()
    ' Şəxsləri ComboBox-a doldur
    Dim wsPeople As Worksheet
    Set wsPeople = ThisWorkbook.Sheets("ŞƏXSLƏR")
    
    Dim lastRow As Integer
    lastRow = wsPeople.Cells(wsPeople.Rows.Count, "E").End(xlUp).Row
    
    Dim i As Integer
    For i = 5 To lastRow
        Dim person As String
        person = wsPeople.Cells(i, 5).Value
        
        If person <> "" And wsPeople.Cells(i, 7).Value = "Aktiv" Then
            Me.ComboBoxOldPerson.AddItem person
            Me.ComboBoxNewPerson.AddItem person
        End If
    Next i
End Sub

Private Sub FillNovbeTypeComboBox()
    ' Növbə növlərini ComboBox-a doldur
    Dim novbeTypes() As String
    novbeTypes = Array("Hissə növbətçisi", "Hissə növbətçisinin köməkçisi", "Nəzarət-buraxılış məntəqəsi növbətçisi", "Park növbətçisi", "Yeməkxana növbətçisi", "Otaq növbətçisi")
    
    Dim i As Integer
    For i = LBound(novbeTypes) To UBound(novbeTypes)
        Me.ComboBoxNovbeType.AddItem novbeTypes(i)
    Next i
End Sub

Private Sub FillReasonComboBox()
    ' Səbəbləri ComboBox-a doldur
    Dim reasons() As String
    reasons = Array("Səhv düzəlişi", "Şəxs dəyişdirilməsi", "Məzuniyyət", "Xəstəlik", "Digər")
    
    Dim i As Integer
    For i = LBound(reasons) To UBound(reasons)
        Me.ComboBoxReason.AddItem reasons(i)
    Next i
End Sub

Private Sub ComboBoxOldPerson_Change()
    ' Köhnə şəxsi seçdikdə
    ' Avtomatik olaraq yeni şəxsi eyni et
    If Me.ComboBoxOldPerson.ListIndex >= 0 Then
        Me.ComboBoxNewPerson.Text = Me.ComboBoxOldPerson.Text
    End If
End Sub

Private Sub ComboBoxNovbeType_Change()
    ' Növbə növünü seçdikdə
    ' Tarixi avtomatik olaraq cari ayın 1-i et
    If Me.ComboBoxNovbeType.ListIndex >= 0 Then
        Dim wsSchedule As Worksheet
        Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
        
        Dim year As Integer, month As Integer
        year = wsSchedule.Range("B4").Value
        month = GetMonthNumber(wsSchedule.Range("E4").Value)
        
        Me.TextBoxDate.Value = DateSerial(year, month, 1)
    End If
End Sub

Private Sub CommandButtonApply_Click()
    ' Tətbiq et düyməsi
    
    ' Məlumatları oxu
    Dim oldPerson As String
    Dim newPerson As String
    Dim novbeDate As Date
    Dim novbeType As String
    Dim reason As String
    
    oldPerson = Me.ComboBoxOldPerson.Text
    newPerson = Me.ComboBoxNewPerson.Text
    novbeDate = Me.TextBoxDate.Value
    novbeType = Me.ComboBoxNovbeType.Text
    reason = Me.ComboBoxReason.Text
    
    ' Yoxlamalar
    If oldPerson = "" Then
        MsgBox "Köhnə şəxsi seçin!", vbExclamation
        Exit Sub
    End If
    
    If newPerson = "" Then
        MsgBox "Yeni şəxsi seçin!", vbExclamation
        Exit Sub
    End If
    
    If novbeType = "" Then
        MsgBox "Növbə növünü seçin!", vbExclamation
        Exit Sub
    End If
    
    ' Şəxsi dəyişdir
    Call ChangePerson(oldPerson, newPerson, novbeDate, novbeType, reason)
    
    ' UserForm-u bağla
    Unload Me
End Sub

Private Sub CommandButtonCancel_Click()
    ' Ləğv et düyməsi
    Unload Me
End Sub

' GetMonthNumber funksiya üçün
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
