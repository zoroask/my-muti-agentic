# Bring the Claude Code session window to the front.
#
# hook-wiring: external - no settings file invokes this. notify_popup.ps1 calls
# it when its panel is clicked. The window handle was recorded by
# notify_done.ps1.
#
# Windows refuses SetForegroundWindow to a process that does not own the
# foreground - measured, not assumed: calling it alone left the foreground
# unchanged. A synthetic ALT tap grants the calling thread foreground rights,
# after which the call succeeds. Minimize-then-restore is the last resort.

param([string]$Uri)  # Windows appends the URI; we do not need it.

Add-Type -Namespace ClaudeFocus -Name Win32 -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, IntPtr dwExtraInfo);
'@ -ErrorAction SilentlyContinue

$SW_MINIMIZE = 6
$SW_RESTORE = 9
$VK_MENU = 0x12
$KEYEVENTF_KEYUP = 2

function Test-IsFrontmost([IntPtr]$Handle) {
    [ClaudeFocus.Win32]::GetForegroundWindow() -eq $Handle
}

try {
    $handleFile = Join-Path $PSScriptRoot '.last-window'
    if (-not (Test-Path $handleFile)) { exit 0 }

    $handle = [IntPtr][int64](Get-Content $handleFile -Raw).Trim()
    if (-not [ClaudeFocus.Win32]::IsWindow($handle)) { exit 0 }  # session has closed

    if ([ClaudeFocus.Win32]::IsIconic($handle)) {
        [void][ClaudeFocus.Win32]::ShowWindow($handle, $SW_RESTORE)
    }

    # Tap ALT to claim foreground rights, then raise the window.
    [ClaudeFocus.Win32]::keybd_event($VK_MENU, 0, 0, [IntPtr]::Zero)
    [ClaudeFocus.Win32]::keybd_event($VK_MENU, 0, $KEYEVENTF_KEYUP, [IntPtr]::Zero)
    [void][ClaudeFocus.Win32]::SetForegroundWindow($handle)
    Start-Sleep -Milliseconds 150

    if (Test-IsFrontmost $handle) { exit 0 }

    # Last resort: a minimize/restore cycle raises a window without needing
    # foreground rights. Visually abrupt, so it is only reached on failure.
    [void][ClaudeFocus.Win32]::ShowWindow($handle, $SW_MINIMIZE)
    Start-Sleep -Milliseconds 150
    [void][ClaudeFocus.Win32]::ShowWindow($handle, $SW_RESTORE)
} catch {
    # Silent: a failed focus must never surface an error dialog.
}

exit 0
