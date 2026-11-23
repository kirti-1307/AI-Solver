# Writes report/Assignment2_Report.pdf from report/Assignment2_Report.docx with Microsoft Word's own
# PDF export, so the PDF has the same pages as the Word file and real, selectable text.
# Run after `python report/build_report.py`:   powershell -File report/make_pdf.ps1
# Word runs hidden inside a job with a time limit, because a hidden Word can hang on a dialog.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$doc = Join-Path $here 'Assignment2_Report.docx'
$pdf = Join-Path $here 'Assignment2_Report.pdf'
$job = Start-Job -ScriptBlock {
    param($p, $out)
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false
    $w.DisplayAlerts = 0
    try {
        $d = $w.Documents.Open($p, $false, $true)            # read-only
        $d.ExportAsFixedFormat($out, 17, $false, 0)           # 17 = PDF, no viewer, optimised for print
        "pages: " + $d.ComputeStatistics(2)
        $d.Close($false)
    } catch {
        "error: $($_.Exception.Message)"
    } finally {
        $w.Quit()
    }
} -ArgumentList $doc, $pdf
if (Wait-Job $job -Timeout 90) { Receive-Job $job } else { 'Word did not finish within 90 s'; Stop-Job $job }
Remove-Job $job -Force
Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq '' } | Stop-Process -Force -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $pdf) { "wrote $pdf (" + (Get-Item -LiteralPath $pdf).Length + " bytes)" }
