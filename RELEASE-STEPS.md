# PRNTR Treasure Tracker — installer staging

This branch contains the GitHub Actions setup for the Windows installer. **The application source files and pirate background image must be uploaded from the full release ZIP before the build can run.** No installer has been compiled or published yet.

## Finish supplying the project

1. Download the [complete project ZIP](https://chatgpt.com/) from the chat and extract it on your PC.
2. Open this repository's `treasure-tracker-release` branch in GitHub.
3. Select **Add file → Upload files**, and drag the contents of the *extracted* project (folders included). Keep the directory structure: `app/`, `installer/`, `website/`, `.github/workflows/`. Do not upload the ZIP as a single file.
4. Commit the files to the staging branch. If GitHub's web uploader doesn't retain a folder, upload its contents inside that folder.
5. Select **Actions → Build Windows installer → Run workflow**, choose `treasure-tracker-release`.
6. On success, download the `TreasureTrackerSetup` artifact. It contains the Windows setup executable.

The app is not endorsed by Epic Games; its global hotkey polling may be subject to game and anti-cheat restrictions. Test on Windows and verify the installer before making a public release.
