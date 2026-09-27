# Notify when Claude Code finishes a turn.
#
# Records the session's window handle, launches a detached clickable panel
# (notify_popup.ps1), and flashes the taskbar button. Returns immediately - the
# panel outlives this process, so the hook never waits on it.
#
# Runs as a Stop hook. Every failure is swallowed and the exit code is always 0:
# a broken notifier must never break a session.

function Get-OwningWindow {
    # The nearest ancestor process that owns a window. Walking the tree rather
    # than looking for a named terminal keeps this working in any host.
    $current = $PID
    for ($depth = 0; $depth -lt 10; $depth++) {
        $info = Get-CimInstance Win32_Process -Filter "ProcessId = $current" -ErrorAction SilentlyContinue
        if (-not $info) { return $null }
        $proc = Get-Process -Id $info.ProcessId -ErrorAction SilentlyContinue
        if ($proc -and $proc.MainWindowHandle -ne 0) { return $proc }
        $current = $info.ParentProcessId
    }
    return $null
}

function Set-TaskbarFlash([IntPtr]$Handle) {
    Add-Type -Namespace ClaudeNotify -Name Win32 -MemberDefinition @'
[StructLayout(LayoutKind.Sequential)]
public struct FLASHWINFO { public uint cbSize; public IntPtr hwnd; public uint dwFlags; public uint uCount; public uint dwTimeout; }
[DllImport("user32.dll")] public static extern bool FlashWindowEx(ref FLASHWINFO pwfi);
'@ -ErrorAction SilentlyContinue

    $info = New-Object ClaudeNotify.Win32+FLASHWINFO
    $info.cbSize    = [System.Runtime.InteropServices.Marshal]::SizeOf($info)
    $info.hwnd      = $Handle
    $info.dwFlags   = 0x0000000C  # FLASHW_TRAY | FLASHW_TIMERNOFG
    $info.uCount    = 0           # keep flashing until the window is focused
    $info.dwTimeout = 0
    [void][ClaudeNotify.Win32]::FlashWindowEx([ref]$info)
}

try {
    $window = Get-OwningWindow
    if (-not $window) { exit 0 }

    # focus_session.ps1 reads this when the panel is clicked.
    Set-Content -Path (Join-Path $PSScriptRoot '.last-window') `
                -Value $window.MainWindowHandle -Encoding ascii

    $label = if ($window.MainWindowTitle) { $window.MainWindowTitle } else { 'Claude Code session' }
    $label = $label -replace '"', ''   # keep the argument list well formed

    # Detached, so this hook returns at once and the panel stays up on its own.
    Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', "`"$(Join-Path $PSScriptRoot 'notify_popup.ps1')`"",
        '-Label', "`"$label`""
    )

    Set-TaskbarFlash $window.MainWindowHandle
} catch {
    # Deliberately silent - see the header.
}

exit 0
