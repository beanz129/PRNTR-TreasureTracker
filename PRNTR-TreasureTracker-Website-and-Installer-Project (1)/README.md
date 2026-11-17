# PRNTR Treasure Tracker — public website + one-click Windows installer

## What is included
- `website/`: responsive public download site.
- `app/`: current tracker with zero-treasure and squads support, packaged runtime support, and dedicated Edge/Chrome overlay window.
- `installer/TreasureTracker.iss`: Inno Setup installer script.
- `.github/workflows/windows-installer.yml`: builds and uploads `TreasureTrackerSetup.exe` from a Windows runner.
- `build-windows.bat`: local Windows build script (builders need Python 3 + Inno Setup 6; **end users do not**).

## Make the real installer
1. Upload this project to a GitHub repository with the `.github` folder intact.
2. On GitHub, go to **Actions → Build Windows installer → Run workflow**.
3. Download the `TreasureTrackerSetup` workflow artifact; it contains `TreasureTrackerSetup.exe`.
4. Put `TreasureTrackerSetup.exe` in `website/downloads/` and deploy the `website/` folder using GitHub Pages, Netlify, Cloudflare Pages or another static host.
5. The site download button automatically activates when the `.exe` exists and is served with its length metadata.
6. Alternatively, tag `v1.0.0` to generate a GitHub Release with the installer attached.

**Important:** The `.exe` has not been compiled or tested here because this runtime is Linux and cannot run Windows builds. The installer project is build-ready but please test on Windows 10 and 11 before distributing.

## User data / imports
Installer writes user settings and totals to `%LOCALAPPDATA%\PRNTR\TreasureTracker\counter-data.json`. Previous users can copy their old `counter-data.json` there. Uninstalling does not delete counts.

## Limitations
- The dedicated stream window should remain open, not minimised. Some capture configurations freeze occluded windows.
- The counter uses global hotkey polling. No Fortnite compatibility guarantee or Epic endorsement.
- This does not provide hosted public TikTok overlay links. TikTok Link sources may not accept localhost; capture the dedicated window.
- Windows installer downloads may trigger SmartScreen reputation checks until signed/reputed. No publisher signature is included.
- The public site only provides downloads; it does not collect accounts.
