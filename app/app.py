import ctypes
import json
import os
import threading
import time
import webbrowser
import sys
import subprocess
import logging
import re
from ctypes import wintypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
DATA_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'PRNTR' / 'TreasureTracker'
DATA_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_STATE_PATH = DATA_DIR / 'counter-data.json'
PROFILE_DIR = DATA_DIR / 'profiles'
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_PROFILE_PATH = DATA_DIR / 'active-profile.json'
# Usernames are LOCAL profiles, not cloud accounts.
def normalize_username(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,24}', value):
        raise ValueError('Username must be 1-24 characters (letters, numbers, _ or -)')
    return value.lower()

def profile_path(username):
    return PROFILE_DIR / (normalize_username(username) + '.json')

def get_current_username():
    try:
        obj = json.loads(ACTIVE_PROFILE_PATH.read_text(encoding='utf-8'))
        return normalize_username(obj.get('username', 'default'))
    except (OSError, ValueError, TypeError):
        return 'default'

def available_profiles():
    return sorted(p.stem for p in PROFILE_DIR.glob('*.json') if re.fullmatch(r'[a-z0-9_-]{1,24}', p.stem))

HOST, PORT = '127.0.0.1', 8765
LOCK = threading.RLock()
DEFAULT = {'chests': 0, 'tokens': 0, 'tokens_per_chest': 1, 'chests_per_click': 1, 'last_chest_increment': 0, 'last_treasure_increment': 0, 'hotkey': 'MIDDLE MOUSE', 'enabled': True, 'session_started': time.time(), 'last_opened': None, 'last_hotkey_seen': None}

def load_profile(username):
    path = profile_path(username)
    try:
        content = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        # Preserve existing users' counts by migrating their original state to Default.
        if username == 'default' and LEGACY_STATE_PATH.is_file() and not path.exists():
            try:
                content = json.loads(LEGACY_STATE_PATH.read_text(encoding='utf-8'))
            except (OSError, ValueError, TypeError):
                content = {}
        else:
            content = {}
    cleaned = {k: v for k, v in content.items() if k in DEFAULT}
    return {**DEFAULT, **cleaned}

current_profile = get_current_username()
state = load_profile(current_profile)

def save_state():
    path = profile_path(current_profile)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2), encoding='utf-8')
    tmp.replace(path)

def save_active_profile():
    tmp = ACTIVE_PROFILE_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps({'username': current_profile}), encoding='utf-8')
    tmp.replace(ACTIVE_PROFILE_PATH)

# Create the initial default profile on first launch, migrating existing totals.
save_state()
save_active_profile()

def snapshot():
    with LOCK:
        return {**state, 'username': current_profile, 'profiles': available_profiles()}

def update(command, value=None):
    global current_profile, state
    with LOCK:
        if command in ('profile_create', 'profile_select'):
            username = normalize_username(value)
            path = profile_path(username)
            if command == 'profile_create' and path.exists():
                raise ValueError('That profile already exists on this PC')
            if command == 'profile_select' and not path.exists():
                raise ValueError('Profile not found on this PC')
            if command == 'profile_create':
                fresh = {**DEFAULT, 'session_started': time.time()}
                path.write_text(json.dumps(fresh, indent=2), encoding='utf-8')
            current_profile = username
            state = load_profile(username)
            save_active_profile()
            return snapshot()
        if command == 'open':
            amount = max(1, min(1000, int(state.get('chests_per_click', 1))))
            treasure = amount * state['tokens_per_chest']
            state['chests'] += amount
            state['tokens'] += treasure
            state['last_chest_increment'] = amount
            state['last_treasure_increment'] = treasure
            state['last_opened'] = time.time()
            if value == 'hotkey':
                state['last_hotkey_seen'] = state['last_opened']
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
            if value not in KEY_MAP:
                raise ValueError('Invalid hotkey')
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
        return snapshot()

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
            update('open', 'hotkey')
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
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        # On windowed builds print messages are invisible: show a Windows dialog.
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(0, f"Could not start Treasure Tracker on port {PORT}.\\n\\nClose the other tracker first.\\n{exc}", "Treasure Tracker", 0x10)
        else:
            print(f"Cannot start Treasure Tracker: {exc}")
        raise SystemExit(1)
    threading.Thread(target=hotkey_loop, daemon=True).start()
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        from desktop_gui import launch
        launch(snapshot, update, DATA_DIR, server.shutdown)
    finally:
        server.shutdown()
        server.server_close()
