VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E78-00AA00574A4F} UserForm2
   Caption         =   "Ay Seçimi"
   ClientHeight    =   200
   ClientLeft      =   0
   ClientTop       =   0
   ClientWidth     =   350
   OleObjectBlob   =   "UserForm2.frx":00000000000000000000000000000000
End
Attribute VB_Name = "UserForm2"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True

' UserForm2.frm - Ay Seçimi Interfeysi

Private Sub UserForm_Initialize()
    ' UserForm-u hazırla
    Me.Caption = "Ay Seçimi - Növbətçilik Sistemi v3.0"
    
    ' ComboBox-ları doldur
    Call FillYearComboBox
    Call FillMonthComboBox
    
    ' Default dəyərlər
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    Me.ComboBoxYear.Text = wsSchedule.Range("B4").Value
    Me.ComboBoxMonth.Text = wsSchedule.Range("E4").Value
    
    ' Focus
    Me.ComboBoxYear.SetFocus
End Sub

Private Sub FillYearComboBox()
    ' İlləri ComboBox-a doldur
    Dim years() As String
    years = Array("2024", "2025", "2026", "2027", "2028")
    
    Dim i As Integer
    For i = LBound(years) To UBound(years)
        Me.ComboBoxYear.AddItem years(i)
    Next i
End Sub

Private Sub FillMonthComboBox()
    ' Ayları ComboBox-a doldur
    Dim months() As String
    months = Array("Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun", "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr")
    
    Dim i As Integer
    For i = LBound(months) To UBound(months)
        Me.ComboBoxMonth.AddItem months(i)
    Next i
End Sub

Private Sub CommandButtonOK_Click()
    ' Təsdiq et düyməsi
    
    ' Məlumatları oxu
    Dim year As Integer
    Dim month As String
    
    year = Me.ComboBoxYear.Text
    month = Me.ComboBoxMonth.Text
    
    ' Yoxlamalar
    If year = "" Then
        MsgBox "İli seçin!", vbExclamation
        Exit Sub
    End If
    
    If month = "" Then
        MsgBox "Ayı seçin!", vbExclamation
        Exit Sub
    End If
    
    ' AYLIQ QRAFİK vərəqində il və ayı dəyişdir
    Dim wsSchedule As Worksheet
    Set wsSchedule = ThisWorkbook.Sheets("AYLIQ QRAFİK")
    
    wsSchedule.Range("B4").Value = year
    wsSchedule.Range("E4").Value = month
    
    ' Avtomatik olaraq tarixləri yenilə
    Call UpdateScheduleDates
    
    ' UserForm-u bağla
    Unload Me
End Sub

Private Sub CommandButtonCancel_Click()
    ' Ləğv et düyməsi
    Unload Me
End Sub
