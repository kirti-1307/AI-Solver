# Optional check: open the built report in Microsoft Word (read-only) and
# report how many pages it has. The .docx itself is produced by build_report.py.
#   powershell -ExecutionPolicy Bypass -File report\build_report.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$docx = Join-Path $here "Assignment2_Report.docx"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($docx, $false, $true)     # read-only
    $pages = $doc.ComputeStatistics(2)                    # wdStatisticPages
    $words = $doc.ComputeStatistics(0)                    # wdStatisticWords
    $doc.Close($false)
    Write-Output "pages=$pages words=$words"
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
