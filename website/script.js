// Installer is delivered directly from the website's /downloads/ folder.
const installer = './downloads/TreasureTrackerSetup.exe';
const btn = document.getElementById('downloadButton');
const main = document.getElementById('downloadMain');
const status = document.getElementById('downloadStatus');
for (const element of [btn, main]) {
  if (!element) continue;
  element.href = installer;
  element.setAttribute('download', 'TreasureTrackerSetup.exe');
  element.removeAttribute('aria-disabled');
}
if (btn) btn.textContent = '⚓ Download Desktop App for Windows';
if (status) status.textContent = 'Direct website download • Desktop v1.1 pre-release • Windows 10/11 (64-bit) • No Python required • Not yet manually tested';
