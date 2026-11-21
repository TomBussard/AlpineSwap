Attribute VB_Name = "ScenarioAnalysis"
Option Explicit

Public Sub RunScenarios()
    Dim inputs As Worksheet, scenario As Worksheet, runs As Worksheet
    Set inputs = ThisWorkbook.Worksheets("Inputs")
    Set scenario = ThisWorkbook.Worksheets("Scenario")
    Set runs = ThisWorkbook.Worksheets("Runs")

    Dim requested As Double
    requested = inputs.Range("B16").Value2
    If requested < 1 Or requested > runs.Rows.Count - 1 Or requested <> Fix(requested) Then
        Err.Raise vbObjectError + 1, , "Enter a whole number of scenarios that will fit in the Runs sheet."
    End If

    Dim results() As Variant, count As Long, i As Long
    count = CLng(requested)
    ReDim results(1 To count, 1 To 4)

    Dim savedMode As Variant, savedScreen As Boolean, failure As String
    savedMode = inputs.Range("B15").Value2
    savedScreen = Application.ScreenUpdating
    On Error GoTo Failed
    Application.ScreenUpdating = False
    inputs.Range("B15").Value2 = "Random"
    For i = 1 To count
        ' One recalculation gives the full swap and both annual payments the same FX path.
        scenario.Calculate
        results(i, 1) = i
        results(i, 2) = scenario.Range("L18").Value2
        results(i, 3) = scenario.Range("L7").Value2
        results(i, 4) = scenario.Range("L13").Value2
    Next i

    Dim lastRow As Long
    lastRow = runs.Cells(runs.Rows.Count, 1).End(xlUp).Row
    runs.Range("A2").Resize(count, 4).Value2 = results
    If lastRow > count + 1 Then runs.Range("A" & count + 2 & ":D" & lastRow).ClearContents
    GoTo RestoreSettings

Failed:
    failure = Err.Description
RestoreSettings:
    On Error Resume Next
    inputs.Range("B15").Value2 = savedMode
    scenario.Calculate
    Application.ScreenUpdating = savedScreen
    On Error GoTo 0
    If Len(failure) > 0 Then Err.Raise vbObjectError + 2, , failure
End Sub

