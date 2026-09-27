# A clickable "finished" notification that needs no registry and no install.
#
# hook-wiring: external - launched detached by notify_done.ps1, not by a
# settings file.
#
# Windows will not let a toast from a borrowed app identity activate our own
# handler, and registering a protocol needs a change outside this project. So
# this draws its own notification panel instead: an ordinary always-on-top
# window. Clicking anywhere on it raises the session, because the click lands
# on a window we own - no protocol, no AUMID, nothing to register.

param(
    [string]$Label = 'Claude Code session',
    [int]$DismissAfterSeconds = 12
)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing

# Palette borrowed from docs/agent-library-schematics.html so it looks native
# to this project rather than like a stray dialog.
$paper = [System.Drawing.ColorTranslator]::FromHtml('#121B2E')
$ink = [System.Drawing.ColorTranslator]::FromHtml('#E4E9F2')
$muted = [System.Drawing.ColorTranslator]::FromHtml('#8B97AC')
$accent = [System.Drawing.ColorTranslator]::FromHtml('#4C8DFF')

$form = New-Object System.Windows.Forms.Form
$form.FormBorderStyle = 'None'
$form.StartPosition = 'Manual'
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.BackColor = $paper
$form.Size = New-Object System.Drawing.Size(390, 98)
$form.Cursor = [System.Windows.Forms.Cursors]::Hand

$area = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$form.Location = New-Object System.Drawing.Point(
    ($area.Right - $form.Width - 16),
    ($area.Bottom - $form.Height - 16)
)

$stripe = New-Object System.Windows.Forms.Panel
$stripe.BackColor = $accent
$stripe.Size = New-Object System.Drawing.Size(4, $form.Height)
$stripe.Location = New-Object System.Drawing.Point(0, 0)

$title = New-Object System.Windows.Forms.Label
$title.Text = 'Claude Code finished'
$title.ForeColor = $ink
$title.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
$title.Location = New-Object System.Drawing.Point(20, 16)
$title.AutoSize = $true

$body = New-Object System.Windows.Forms.Label
$body.Text = $Label
$body.ForeColor = $muted
$body.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$body.Location = New-Object System.Drawing.Point(20, 42)
$body.Size = New-Object System.Drawing.Size(354, 18)
$body.AutoEllipsis = $true

$hint = New-Object System.Windows.Forms.Label
$hint.Text = 'Click to return to this session'
$hint.ForeColor = $accent
$hint.Font = New-Object System.Drawing.Font('Segoe UI', 8)
$hint.Location = New-Object System.Drawing.Point(20, 66)
$hint.AutoSize = $true

$form.Controls.AddRange(@($stripe, $title, $body, $hint))

function Invoke-Focus {
    try {
        # Reuse the proven focus logic rather than duplicating the P/Invoke.
        & (Join-Path $PSScriptRoot 'focus_session.ps1')
    } catch {
        # A failed focus must not leave the panel stuck on screen.
    }
    $form.Close()
}

# Any click anywhere on the panel counts, including on the labels.
$onClick = { Invoke-Focus }
$form.Add_Click($onClick)
foreach ($control in $form.Controls) { $control.Add_Click($onClick) }

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = [Math]::Max(1, $DismissAfterSeconds) * 1000
$timer.Add_Tick({ $timer.Stop(); $form.Close() })
$timer.Start()

[void]$form.ShowDialog()
exit 0
