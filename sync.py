#!/usr/bin/env python3
"""
Dropbox â GitHub data.json sync
Scans /Projects for .ai/.pdf files per card, upgrades statuses in data.json.
Rules:
  - .pdf present  â complete
  - .ai only      â inprogress
  - neither       â pending (only if currently pending)
  - never downgrades: pendingâinprogressâcomplete
  - never touches onhold or archived
"""

import os, json, base64, time
import urllib.request, urllib.parse, urllib.error

# ââ Config ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
DBX_REFRESH  = os.environ['DROPBOX_REFRESH_TOKEN']
DBX_KEY      = os.environ['DROPBOX_APP_KEY']
DBX_SECRET   = os.environ['DROPBOX_APP_SECRET']
GH_TOKEN     = os.environ['GH_PAT']
GH_REPO      = 'ddpedersen/perception-cards-tracker'
GH_FILE      = 'data.json'
GH_BRANCH    = 'main'
DBX_ROOT     = '/Perception Cards/Projects'

STATUS_ORDER = ['pending', 'inprogress', 'complete']

# Card ID â folder path relative to /Projects (non-recursive scan)
CARD_PATHS = {
    # ââ Kobe Bryant ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'kobe-legendary':        'Artist Cards/Jared Emerson/Kobe Bryant/Legendary',
    'kobe-legendary-angel':  'Artist Cards/Jared Emerson/Kobe Bryant/Legendary - Angel of1',
    'kobe-legendary-gold':   'Artist Cards/Jared Emerson/Kobe Bryant/Legendary - Gold of2',
    'kobe-legendary-score':  'Artist Cards/Jared Emerson/Kobe Bryant/Legendary - Scoreboard',
    'kobe-legendary-silver': 'Artist Cards/Jared Emerson/Kobe Bryant/Legendary - Silver Holo',
    'kobe-chrome':           'Artist Cards/Jared Emerson/Kobe Bryant/Portrait - Chrome 1of2',
    'kobe-chrome-plate':     'Artist Cards/Jared Emerson/Kobe Bryant/Portrait - Chrome 1of2/Graded Plate',
    'kobe-plastic-holo':     'Artist Cards/Jared Emerson/Kobe Bryant/Portrait - Plastic Holo',
    'kobe-snake-print':      'Artist Cards/Jared Emerson/Kobe Bryant/Portrait - Snake Print',
    'kobe-snakeskin':        'Artist Cards/Jared Emerson/Kobe Bryant/Portrait - Snake Skin 1of1',
    'kobe-snakeskin-box':    'Artist Cards/Jared Emerson/Kobe Bryant/Portrait - Snake Skin 1of1/Custom Box',
    'kobe-court-dreams':     'Artist Cards/Jared Emerson/Kobe Bryant/Court Dreams',

    # ââ Michael Jordan âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'mj-portrait':       'Artist Cards/Jared Emerson/Michael Jordan/Jordan Portrait',
    'mj-kobe-dual':      'Artist Cards/Jared Emerson/Michael Jordan/Jordan Portrait',       # same folder
    'mj-portrait-gold':  'Artist Cards/Jared Emerson/Michael Jordan/Jordan Portrait/Portrait - of1 Gold',
    'mj-flight-angel':   'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Angel 1of1',
    'mj-flight-clear-air':'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Angel Clear Air - not sure if used',
    'mj-flight-rare-air':'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Angel w background 1of1',
    'mj-flight-clear':   'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Clear',
    'mj-flight-leather': 'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Leather Goat 1of1',
    'mj-flight-holo':    'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Plastic Holo',
    'mj-flight-stained': 'Artist Cards/Jared Emerson/Michael Jordan/MJ in Flight - Stained Glass',
    'mj-flight-space':   'Artist Cards/Jared Emerson/Michael Jordan/_Concept Designs - Move once confirmed',

    # ââ Other Jared cards ââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'lebron-legendary':  'Artist Cards/Jared Emerson/Lebron James',
    'shaq-dunk':         'Artist Cards/Jared Emerson/Shaq Dunk',
    'hardaway':          'Artist Cards/Jared Emerson/Hardaway',
    'dual-orlando':      'Artist Cards/Jared Emerson/Dual Orlando',
    'gng-dual':          'Artist Cards/Jared Emerson/GnG Dual Card - do we need these',
    'card-backs':        'Artist Cards/Jared Emerson',  # Card Back Designs.ai at root

    # ââ Athletic Art ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'neoleo': 'Artist Cards/Athletic Art SC/NeoLeo',

    # ââ Baseball âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'kerry-wood':   'Baseball/Kerry Wood',
    'roger-clemens':'Baseball',  # files at Baseball/ root

    # ââ Football âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'cam-skattebo':     'Football/Cam Skattebo',
    'josh-lego':        'Football',  # files at Football/ root
    'josh-puffs':       'Football/Josh Allen/MVP Puffs',
    'josh-playing-cards':'Football/Josh Allen/Playing Cards',
    'lee-smith':        'Football/Lee Smith',

    # ââ Graded Plates ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'plate-court-dreams': 'Graded Plates',  # both plates share this folder
    'plate-leather-goat': 'Graded Plates',

    # ââ Magical ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'magical-card': 'Magical Cards',

    # ââ Micro Wrestling ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'micro-tiger':     'Micro Wrestling/MICRO TIGER',
    'syko':            'Micro Wrestling/SYKO',
    'pinky-shortcake': 'Micro Wrestling/Pinky Shortcake',
    'unknown-wrestler':'Micro Wrestling/Unknown Wrestler',
    'baby-jesus':      'Micro Wrestling/Baby Jesus',
    'knate':           'Micro Wrestling/KNate the Knome',

    # ââ Philanthropic ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'betty-card':   'Philanthropic Projects',  # files at root
    'jake-kellehan':'Philanthropic Projects/First Order - Jake Kellehan',

    # ââ Derek Personal âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    'blades-brown':   'z_ Derek\'s Personal Projects',  # files at root
    'words-from-god': 'z_ Derek\'s Personal Projects/Derek',
    'erik-life-plan': 'z_ Derek\'s Personal Projects/Erik Life Plan Card',
    'fake-duplicates':'z_ Derek\'s Personal Projects/Fake Duplicates',
    'grandpa-deer':   'z_ Derek\'s Personal Projects/Family',
    'gym-athena':     'z_ Derek\'s Personal Projects/Gymnastics Cards/Athena',
    'gym-collins':    'z_ Derek\'s Personal Projects/Gymnastics Cards/Collins',
    'gym-julia':      'z_ Derek\'s Personal Projects/Gymnastics Cards/Julia',
    'gym-katarina':   'z_ Derek\'s Personal Projects/Gymnastics Cards/Katarina',
    'gym-mika':       'z_ Derek\'s Personal Projects/Gymnastics Cards/Mika',
    'gym-scarlett':   'z_ Derek\'s Personal Projects/Gymnastics Cards/Scarlett',
    'gym-sophie':     'z_ Derek\'s Personal Projects/Gymnastics Cards/Sophie',
    'gym-zara':       'z_ Derek\'s Personal Projects/Gymnastics Cards/Zara',
    'mika-standalone':'z_ Derek\'s Personal Projects/Mika',
    'real-motors':    'z_ Derek\'s Personal Projects/Real Motors',
    'soccer-jonah':   'z_ Derek\'s Personal Projects/Soccer Cards - Year 1',
    'soccer-william': 'z_ Derek\'s Personal Projects/Soccer Cards - Year 1',  # shares folder with jonah
    'kid-projects':   'z_ Derek\'s Personal Projects/Kid Projects',
}

# ââ HTTP helper âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def http_post_json(url, headers, body):
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        raise RuntimeError(f'POST {url} â {e.code}: {body.decode("utf-8", errors="replace")}')

def http_get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, 404
        body = e.read()
        raise RuntimeError(f'GET {url} â {e.code}: {body.decode("utf-8", errors="replace")}')

def http_put_json(url, headers, body):
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        raise RuntimeError(f'PUT {url} â {e.code}: {body.decode("utf-8", errors="replace")}')

def http_post_form(url, fields):
    data = urllib.parse.urlencode(fields).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# ââ Dropbox âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def get_dbx_token():
    r = http_post_form('https://api.dropboxapi.com/oauth2/token', {
        'grant_type':    'refresh_token',
        'refresh_token': DBX_REFRESH,
        'client_id':     DBX_KEY,
        'client_secret': DBX_SECRET,
    })
    return r['access_token']

def list_folder_direct(token, path):
    """Returns list of file entries for a Dropbox folder (non-recursive)."""
    headers = {
        'Authorization':  f'Bearer {token}',
        'Content-Type':   'application/json',
    }
    try:
        data = http_post_json(
            'https://api.dropboxapi.com/2/files/list_folder',
            headers,
            {'path': path, 'recursive': False, 'include_non_downloadable_files': True}
        )
    except RuntimeError as e:
        if 'path/not_found' in str(e) or '"error_summary": "path/not_found' in str(e):
            return []
        raise
    entries = list(data.get('entries', []))
    while data.get('has_more'):
        data = http_post_json(
            'https://api.dropboxapi.com/2/files/list_folder/continue',
            headers,
            {'cursor': data['cursor']}
        )
        entries.extend(data.get('entries', []))
    return entries

def detect_status(token, rel_path):
    """Detect status from files in a folder."""
    full_path = f"{DBX_ROOT}/{rel_path}"
    entries = list_folder_direct(token, full_path)
    files = [e for e in entries if e.get('.tag') == 'file']
    has_pdf = any(e['name'].lower().endswith('.pdf') for e in files)
    has_ai  = any(e['name'].lower().endswith('.ai')  for e in files)
    if has_pdf:
        return 'complete'
    if has_ai:
        return 'inprogress'
    return 'pending'

# ââ Status logic ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def upgrade_status(current, detected):
    """Only upgrade, never downgrade. Protect onhold/archived."""
    if current in ('onhold', 'archived'):
        return current
    try:
        cur_idx = STATUS_ORDER.index(current)
    except ValueError:
        cur_idx = 0
    try:
        det_idx = STATUS_ORDER.index(detected)
    except ValueError:
        det_idx = 0
    return STATUS_ORDER[max(cur_idx, det_idx)]

# ââ GitHub ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
GH_HEADERS = {
    'Authorization': f'token {GH_TOKEN}',
    'Accept':        'application/vnd.github.v3+json',
    'Content-Type':  'application/json',
}

def get_data_json():
    url = f'https://api.github.com/repos/{GH_REPO}/contents/{GH_FILE}'
    data, status = http_get_json(url, GH_HEADERS)
    if status == 404 or data is None:
        return {}, None
    raw = base64.b64decode(data['content'].replace('\n', '')).decode('utf-8')
    return json.loads(raw), data['sha']

def save_data_json(payload, sha):
    url = f'https://api.github.com/repos/{GH_REPO}/contents/{GH_FILE}'
    timestamp = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    content = base64.b64encode(json.dumps(payload, indent=2).encode('utf-8')).decode('utf-8')
    body = {
        'message': f'Auto-sync from Dropbox {timestamp}',
        'content': content,
        'branch':  GH_BRANCH,
    }
    if sha:
        body['sha'] = sha
    result = http_put_json(url, GH_HEADERS, body)
    return result['content']['sha']

# ââ Main ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def main():
    print('Getting Dropbox access token...')
    dbx_token = get_dbx_token()
    print('  OK')

    print('Loading data.json from GitHub...')
    data, sha = get_data_json()
    print(f'  Loaded {len(data)} existing entries, SHA={sha}')

    changes = []
    for card_id, rel_path in CARD_PATHS.items():
        detected = detect_status(dbx_token, rel_path)
        current  = data.get(card_id, {}).get('status', 'pending')
        upgraded = upgrade_status(current, detected)

        if card_id not in data:
            data[card_id] = {}

        if upgraded != current:
            data[card_id]['status'] = upgraded
            changes.append((card_id, current, upgraded))
            print(f'  UPGRADE  {card_id}: {current} â {upgraded}')
        else:
            print(f'  no change {card_id}: {current}')

    if changes:
        print(f'\nSaving {len(changes)} change(s) to GitHub...')
        new_sha = save_data_json(data, sha)
        print(f'Saved! New SHA: {new_sha}')
        print('\nChanges:')
        for card_id, old, new in changes:
            print(f'  {card_id}: {old} â {new}')
    else:
        print('\nNo status changes â data.json unchanged.')

if __name__ == '__main__':
    main()
