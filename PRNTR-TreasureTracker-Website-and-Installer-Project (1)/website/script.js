// Put the built installer into website/downloads/TreasureTrackerSetup.exe before publishing.
const installer = 'downloads/TreasureTrackerSetup.exe';
const btn = document.getElementById('downloadButton');
const main = document.getElementById('downloadMain');
const status = document.getElementById('downloadStatus');
fetch(installer, {method: 'HEAD', cache: 'no-store'}).then(response => {
  if (!response.ok || !Number(response.headers.get('content-length'))) return;
  btn.href = installer;
  btn.download = 'TreasureTrackerSetup.exe';
  btn.removeAttribute('aria-disabled');
  btn.textContent = '⚓ Download Windows Installer ↗';
  status.textContent = 'Windows 10/11 • 64-bit • No Python required • Free download';
  main.href = '#download';
}).catch(() => {});
