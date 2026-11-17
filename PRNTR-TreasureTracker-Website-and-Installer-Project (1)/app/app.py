import ctypes
import json
import os
import threading
import time
import webbrowser
import sys
import subprocess
import logging
from ctypes import wintypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
DATA_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'PRNTR' / 'TreasureTracker'
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = DATA_DIR / 'counter-data.json'
# Existing users can import their previous totals by copying counter-data.json here.

HOST, PORT = '127.0.0.1', 8765
LOCK = threading.RLock()
DEFAULT = {'chests': 0, 'tokens': 0, 'tokens_per_chest': 1, 'chests_per_click': 1, 'last_chest_increment': 0, 'last_treasure_increment': 0, 'hotkey': 'MIDDLE MOUSE', 'enabled': True, 'session_started': time.time(), 'last_opened': None}

def load_state():
    try:
        content = json.loads(STATE_PATH.read_text(encoding='utf-8'))
        return {**DEFAULT, **{k:v for k,v in content.items() if k in DEFAULT}}
    except (OSError, ValueError, TypeError):
        return DEFAULT.copy()

state = load_state()

def save_state():
    tmp = STATE_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2), encoding='utf-8')
    tmp.replace(STATE_PATH)

def snapshot():
    with LOCK:
        return state.copy()

def update(command, value=None):
    with LOCK:
        if command == 'open':
            amount = max(1, min(1000, int(state.get('chests_per_click', 1))))
            treasure = amount * state['tokens_per_chest']
            state['chests'] += amount
            state['tokens'] += treasure
            state['last_chest_increment'] = amount
            state['last_treasure_increment'] = treasure
            state['last_opened'] = time.time()
        elif command == 'undo':
            if state['chests'] > 0 and state.get('last_chest_increment', 0) > 0:
                state['chests'] = max(0, state['chests'] - state['last_chest_increment'])
                state['tokens'] = max(0, state['tokens'] - state.get('last_treasure_increment', 0))
                state['last_chest_increment'] = 0
                state['last_treasure_increment'] = 0
        elif command == 'set_chests':
            state['chests'] = max(0, min(999999999, int(value)))
        elif command == 'set_tokens':
            state['tokens'] = max(0, min(999999999, int(value)))
        elif command == 'chests_per_click':
            state['chests_per_click'] = max(1, min(1000, int(value)))
        elif command == 'per_chest':
            state['tokens_per_chest'] = max(0, min(100000, int(value)))
        elif command == 'hotkey':
            if value not in KEY_MAP: raise ValueError('Invalid hotkey')
            state['hotkey'] = value
        elif command == 'enabled':
            state['enabled'] = bool(value)
        elif command == 'reset':
            state['chests'] = 0
            state['tokens'] = 0
            state['session_started'] = time.time()
            state['last_opened'] = None
            state['last_chest_increment'] = 0
            state['last_treasure_increment'] = 0
        else:
            raise ValueError('Unknown action')
        save_state()
        return state.copy()

# Windows VK codes. Polling works globally, including while Minecraft is focused.
KEY_MAP = {
    'MIDDLE MOUSE': 0x04,
    'MOUSE 4 (SIDE)': 0x05,
    'MOUSE 5 (SIDE)': 0x06,
    'F6': 0x75, 'F7': 0x76, 'F8': 0x77, 'F9': 0x78,
    'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
    'NUMPAD +': 0x6B,
}

def hotkey_loop():
    if os.name != 'nt': return
    get_key = ctypes.windll.user32.GetAsyncKeyState
    get_key.argtypes = [ctypes.c_int]
    get_key.restype = ctypes.c_short
    last_key = None
    is_down = False
    last_press = 0.0
    while True:
        s = snapshot()
        key = s.get('hotkey', 'MIDDLE MOUSE')
        vk = KEY_MAP.get(key, 0x04)
        if key != last_key:
            is_down = bool(get_key(vk) & 0x8000)
            last_key = key
        down = bool(get_key(vk) & 0x8000)
        if down and not is_down and s.get('enabled', True) and time.monotonic() - last_press > 0.18:
            update('open')
            last_press = time.monotonic()
        is_down = down
        time.sleep(0.018)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if not self.path.startswith('/api/state'):
            print('[Counter]', fmt % args)

    def respond(self, content, content_type='text/html; charset=utf-8', status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/state':
            self.respond(json.dumps(snapshot()).encode(), 'application/json')
        elif path in ('/', '/dashboard'):
            self.respond((BASE / 'dashboard.html').read_bytes())
        elif path == '/overlay':
            self.respond((BASE / 'overlay.html').read_bytes())
        elif path == '/pirate-theme.png':
            self.respond((BASE / 'pirate-theme.png').read_bytes(), 'image/png')
        else:
            self.respond(b'Not found', 'text/plain', 404)

    def do_POST(self):
        if urlparse(self.path).path != '/api/action':
            return self.respond(b'Not found', 'text/plain', 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not (0 < length < 2048): raise ValueError('Invalid request size')
            payload = json.loads(self.rfile.read(length))
            result = update(payload['action'], payload.get('value'))
            self.respond(json.dumps(result).encode(), 'application/json')
        except (ValueError, KeyError, TypeError) as error:
            self.respond(json.dumps({'error': str(error)}).encode(), 'application/json', 400)

if __name__ == '__main__':
    if os.name != 'nt':
        print('Global hotkeys require Windows. Web controls can still run.')
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        print(f'Cannot start counter on port {PORT}: {exc}')
        if sys.stdin and sys.stdin.isatty(): input('Press Enter to exit...')
        raise SystemExit(1)
    threading.Thread(target=hotkey_loop, daemon=True).start()
    print('========================================')
    print('         TREASURE TRACKER')
    print('========================================')
    print(f'Dashboard: http://{HOST}:{PORT}/dashboard')
    print(f'Overlay:   http://{HOST}:{PORT}/overlay')
    print('Keep this window running during your LIVE.')
    print('Press Ctrl+C to stop. Your counters are saved.')
    print('========================================')
    webbrowser.open(f'http://{HOST}:{PORT}/dashboard')
    # Dedicated Chromium app window avoids ordinary background-tab throttling.
    browser_paths = [
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe',
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Microsoft/Edge/Application/msedge.exe',
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Google/Chrome/Application/chrome.exe',
    ]
    for browser in browser_paths:
        if browser.is_file():
            try:
                subprocess.Popen([
                    str(browser), '--user-data-dir=' + str(DATA_DIR / 'browser-profile'),
                    f'--app=http://{HOST}:{PORT}/overlay', '--window-size=650,230',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling,TabFreeze'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass
            break
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print('\nCounter stopped.')
    finally:
        server.server_close()
