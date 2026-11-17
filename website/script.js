// Public downloadable installer hosted on GitHub Releases.
// No GitHub account is required for downloads from public releases.
const installer = 'https://github.com/beanz129/PRNTR-TreasureTracker/releases/download/v1.1.0-rc1/TreasureTrackerSetup.exe';
const button = document.getElementById('downloadButton');
const heroButton = document.getElementById('downloadMain');
const status = document.getElementById('downloadStatus');

if (button) {
  button.href = installer;
  button.removeAttribute('aria-disabled');
  button.removeAttribute('download');
  button.textContent = '⚓ Download Desktop App for Windows ↗';
}
if (heroButton) heroButton.href = installer;
if (status) status.textContent = 'Desktop v1.1 pre-release • Windows 10/11 x64 • No Python required • Not yet tested on Windows';
