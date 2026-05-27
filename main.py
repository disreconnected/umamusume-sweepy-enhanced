import os
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
except Exception:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import random
import time
import threading
import frida
from career_bot import master_data
from career_bot.presets import PresetStore
from career_bot.runner import CareerRunner
from career_bot import uma_moe_importer
from career_bot import advisor
from uma_api.client import UmaClient
from career_bot.delay import GateKeeper, dna_sleep, dna_uniform

PROCESS_NAME = "UmamusumePrettyDerby.exe"
APP_ID = "3224770"

JS_CODE = r'''
'use strict';
(function() {
    var buffers = {};
    var attached = {};
    function hex2(n) { return ('0' + (n & 255).toString(16)).slice(-2); }
    function uuidFromHex(h) {
        return h.substring(0, 8) + '-' + h.substring(8, 12) + '-' + h.substring(12, 16) + '-' + h.substring(16, 20) + '-' + h.substring(20);
    }
    function b64(s) {
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        var out = [];
        var buffer = 0;
        var bits = 0;
        for (var i = 0; i < s.length; i++) {
            var c = s.charAt(i);
            if (c === '=') break;
            var idx = chars.indexOf(c);
            if (idx < 0) continue;
            buffer = (buffer << 6) | idx;
            bits += 6;
            if (bits >= 8) {
                bits -= 8;
                out.push((buffer >> bits) & 255);
            }
        }
        return out;
    }
    function parseWire(endpoint, viewerId, body, appVer, resVer) {
        var decoded = b64(body);
        if (decoded.length < 140) return;
        var headerLen = decoded[0] | (decoded[1] << 8) | (decoded[2] << 16) | (decoded[3] << 24);
        var blob1End = 4 + headerLen;
        if (headerLen < 120 || headerLen > 2048 || decoded.length < blob1End) return;
        
        var udidHex = '';
        for (var i = blob1End - 96; i < blob1End - 80; i++) udidHex += hex2(decoded[i]);
        var authHex = '';
        for (var j = blob1End - 48; j < blob1End; j++) authHex += hex2(decoded[j]);
        
        if (!viewerId || !authHex || authHex.length < 64 || udidHex.length !== 32) return;
        
        send({
            type: 'creds',
            endpoint: endpoint,
            viewer_id: parseInt(viewerId, 10),
            udid: uuidFromHex(udidHex),
            auth_key: authHex,
            auth_key_len: authHex.length / 2,
            app_ver: appVer,
            res_ver: resVer,
            body: body
        });
    }
    function parseHttp(text) {
        if (text.indexOf('/umamusume/') < 0) return;
        var em = text.match(/POST\s+\/umamusume\/([^\s]+)\s+HTTP/i);
        var vm = text.match(/(?:^|\r\n)(?:ViewerID|ViewerId):\s*(\d+)/i);
        var appVer = text.match(/(?:^|\r\n)APP-VER:\s*([^\r\n]+)/i);
        var resVer = text.match(/(?:^|\r\n)RES-VER:\s*([^\r\n]+)/i);
        var idx = text.indexOf('\r\n\r\n');
        if (!em || !vm || idx < 0) return;
        parseWire(em[1], vm[1], text.substring(idx + 4), appVer ? appVer[1].trim() : '', resVer ? resVer[1].trim() : '');
    }
    function parseChunk(key, chunk) {
        var buf = (buffers[key] || '') + chunk;
        if (buf.length > 2097152) buf = buf.substring(buf.length - 1048576);
        var start = buf.indexOf('POST ');
        if (start < 0) {
            buffers[key] = buf.slice(-4096);
            return;
        }
        if (start > 0) buf = buf.substring(start);
        var headerEnd = buf.indexOf('\r\n\r\n');
        if (headerEnd < 0) {
            buffers[key] = buf;
            return;
        }
        var headers = buf.substring(0, headerEnd);
        var lm = headers.match(/Content-Length:\s*(\d+)/i);
        var length = lm ? parseInt(lm[1], 10) : 0;
        var total = headerEnd + 4 + length;
        if (length > 0 && buf.length < total) {
            buffers[key] = buf;
            return;
        }
        parseHttp(length > 0 ? buf.substring(0, total) : buf);
        buffers[key] = buf.length > total ? buf.substring(total) : '';
    }
    function hookTls() {
        var ga = Process.findModuleByName('GameAssembly.dll');
        if (!ga) return false;
        var installFn = ga.findExportByName('il2cpp_unity_install_unitytls_interface');
        if (!installFn) return false;
        var rb = new Uint8Array(installFn.readByteArray(16));
        var realFn = installFn;
        if (rb[0] === 0xe9) {
            var off = rb[1] | (rb[2] << 8) | (rb[3] << 16) | (rb[4] << 24);
            if (off > 0x7fffffff) off -= 0x100000000;
            realFn = installFn.add(5 + off);
            rb = new Uint8Array(realFn.readByteArray(16));
        }
        var globalPtr = null;
        if (rb[0] === 0x48 && rb[1] === 0x89 && rb[2] === 0x0d) {
            var disp = rb[3] | (rb[4] << 8) | (rb[5] << 16) | (rb[6] << 24);
            if (disp > 0x7fffffff) disp -= 0x100000000;
            globalPtr = realFn.add(7 + disp);
        }
        if (!globalPtr) return false;
        var iface = globalPtr.readPointer();
        if (!iface || iface.isNull()) return false;
        var hookedTls = 0;
        [0xd0, 0xd8, 0xe0, 0xe8].forEach(function(off) {
            var addr = iface.add(off).readPointer();
            if (!addr || addr.isNull()) return;
            var key = 'tls_' + addr.toString();
            if (attached[key]) return;
            try {
                Interceptor.attach(addr, {
                    onEnter: function(args) {
                        var len = args[2].toInt32();
                        if (len <= 0 || len > 1048576 || args[1].isNull()) return;
                        try {
                            var bytes = args[1].readByteArray(len);
                            var u8 = new Uint8Array(bytes);
                            var s = '';
                            for (var i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]);
                            parseChunk(args[0].toString(), s);
                        } catch (e) {}
                    }
                });
                attached[key] = true;
                hookedTls++;
            } catch (e) {}
        });
        return hookedTls > 0;
    }
    var tlsDone = false;
    var timer = setInterval(function() {
        try {
            if (!tlsDone) tlsDone = hookTls();
            if (tlsDone) clearInterval(timer);
        } catch (e) {}
    }, 1000);
})();
'''


DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

chara_map = {}
support_map = {}
active_client = None
active_account = None
active_dashboard_data = None
active_start_state = {}
active_parent_cards = {}
active_parent_rank_points = {}
pending_game_auth_config = {}
raw_load_index_response = None
active_selection = {
    "deck": None,
    "friend": None,
    "trainee": None,
    "veterans": []
}
turn_delay_min_sec = 2.5
turn_delay_max_sec = 5.0
turn_delay_restore_min_sec = 2.5
turn_delay_restore_max_sec = 5.0
turn_delay_disabled = False
preset_store = PresetStore(DIR)
career_runner = CareerRunner(DIR)

base_dir = Path(__file__).parent.absolute()
master_data_startup_status = master_data.status(base_dir)
if master_data_startup_status.get("exists"):
    master_data_startup_result = master_data.generate(base_dir)
    if master_data_startup_result.get("success"):
        print(f"master.mdb data generated: {master_data_startup_status.get('master_mdb_path')}")
    else:
        print(f"master.mdb data generation failed: {master_data_startup_result.get('detail')}")
elif master_data_startup_status.get("requires_user_action"):
    print(f"master.mdb requires user action: {master_data_startup_status.get('master_mdb_path')}")
chara_path = base_dir / 'data' / 'chara_list.json'
support_path = base_dir / 'data' / 'support_list.json'
images_dir = base_dir / 'data' / 'images'

if chara_path.exists():
    with open(chara_path, 'r', encoding='utf-8') as f:
        chara_map = json.load(f)
if support_path.exists():
    with open(support_path, 'r', encoding='utf-8') as f:
        support_map = json.load(f)


SESSION_CACHE_PATH = base_dir / 'data' / '.session_cache.json'
LOCAL_DECKS_PATH = base_dir / 'data' / 'decks.json'
SESSION_CACHE_WRITABLE_KEYS = ('selected_preset',)
SESSION_CACHE_ALL_KEYS = (
    'viewer_id',
    'career',
    'selected_preset',
    'last_login_at',
)


def _load_session_cache():
    try:
        if not SESSION_CACHE_PATH.exists():
            return {}
        with open(SESSION_CACHE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"session_cache: load failed: {e}")
        return {}


def _save_session_cache(updates):
    try:
        cache = _load_session_cache()
        for key, value in (updates or {}).items():
            if key not in SESSION_CACHE_ALL_KEYS:
                continue
            cache[key] = value
        SESSION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = SESSION_CACHE_PATH.with_suffix('.json.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, SESSION_CACHE_PATH)
        return cache
    except Exception as e:
        print(f"session_cache: save failed: {e}")
        return {}


def _career_snapshot_for_cache(account):
    if not account:
        return None
    career = account.get('career')
    if not career:
        return None
    return {
        'active': bool(career.get('active')),
        'name': career.get('name'),
        'card_id': career.get('card_id'),
        'scenario_id': career.get('scenario_id'),
        'turn': career.get('turn'),
    }


def display_support_type(value):
    return {
        "Friends": "Pal",
        "Wisdom": "Wit"
    }.get(value, value)


def _support_card_summary(card_id, owned_by_id=None):
    sid = str(card_id)
    info = support_map.get(sid, {})
    owned = (owned_by_id or {}).get(int(card_id or 0), {})
    return {
        'id': sid,
        'name': info.get('name', f"Unknown ({sid})"),
        'rarity': info.get('rarity', '?'),
        'type': display_support_type(info.get('type', 'Unknown')),
        'exp': owned.get('exp'),
        'limit_break_count': owned.get('limit_break_count'),
        'favorite_flag': owned.get('favorite_flag', 0),
    }


def _support_cards_from_ids(card_ids):
    cards = []
    for sid in card_ids or []:
        card = _support_card_summary(sid)
        cards.append(card)
    return cards


def _deck_meta_from_ids(card_ids):
    counts = advisor.support_type_counts(card_ids, support_map)
    return {
        "deck_support_cards": _support_cards_from_ids(card_ids),
        "deck_type_counts": counts,
        "deck_archetype": advisor.deck_archetype(counts),
    }


def _read_local_decks():
    try:
        if not LOCAL_DECKS_PATH.exists():
            return []
        data = json.loads(LOCAL_DECKS_PATH.read_text(encoding='utf-8'))
        decks = data.get('decks') if isinstance(data, dict) else data
        return decks if isinstance(decks, list) else []
    except Exception as e:
        print(f"local_decks: load failed: {e}")
        return []


def _write_local_decks(decks):
    LOCAL_DECKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = LOCAL_DECKS_PATH.with_suffix('.json.tmp')
    tmp_path.write_text(json.dumps({'decks': decks}, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp_path, LOCAL_DECKS_PATH)


def _normalise_local_deck(raw, owned_by_id=None):
    deck_id = str(raw.get('id') or '').strip()
    if not deck_id:
        deck_id = f"local_{int(time.time() * 1000)}"
    if not deck_id.startswith("local_"):
        deck_id = f"local_{deck_id}"
    ids = []
    for value in raw.get('support_card_ids') or raw.get('cards') or []:
        if isinstance(value, dict):
            value = value.get('id') or value.get('support_card_id')
        try:
            sid = int(value)
        except (TypeError, ValueError):
            continue
        if sid > 0 and sid not in ids:
            ids.append(sid)
    ids = ids[:5]
    return {
        'id': deck_id,
        'deck_id': int(raw.get('deck_id') or 1),
        'name': str(raw.get('name') or 'Sweepy Deck').strip()[:80],
        'local': True,
        'support_card_ids': ids,
        'cards': [_support_card_summary(sid, owned_by_id) for sid in ids],
    }


def _local_decks_payload(owned_by_id=None):
    return [_normalise_local_deck(deck, owned_by_id) for deck in _read_local_decks()]


def normalize_turn_delay(min_value, max_value, disabled=False):
    left = max(0.0, float(min_value or 0.0))
    right = max(0.0, float(max_value or 0.0))
    if left > right:
        right = left
    if disabled:
        left = 0.0
        right = 0.0
    return left, right, bool(disabled)

def set_turn_delay(min_value, max_value, disabled=False):
    import career_bot.delay as delay_module
    next_min, next_max, next_disabled = normalize_turn_delay(min_value, max_value, disabled)
    if not next_disabled:
        delay_module.TURN_DELAY_RESTORE_MIN = next_min
        delay_module.TURN_DELAY_RESTORE_MAX = next_max
    delay_module.TURN_DELAY_MIN = next_min
    delay_module.TURN_DELAY_MAX = next_max
    delay_module.GLOBAL_DELAYS_DISABLED = next_disabled
    return get_turn_delay()

def get_turn_delay():
    import career_bot.delay as delay_module
    return {
        "success": True,
        "min": getattr(delay_module, "TURN_DELAY_MIN", 2.5),
        "max": getattr(delay_module, "TURN_DELAY_MAX", 5.0),
        "restore_min": getattr(delay_module, "TURN_DELAY_RESTORE_MIN", 2.5),
        "restore_max": getattr(delay_module, "TURN_DELAY_RESTORE_MAX", 5.0),
        "disabled": getattr(delay_module, "GLOBAL_DELAYS_DISABLED", False)
    }


def refresh_index_state(client, max_retries=3):
    if not client:
        raise RuntimeError("Not logged in")

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            client.call("tool/start_session", {"attestation_type": 0, "device_token": None})
            return client.call("load/index", {"adid": ""})
        except Exception as exc:
            last_error = exc
            err = str(exc)
            if attempt >= max_retries:
                raise
            if "202" in err:
                dna_sleep(4.15, 4.15)
                continue
            if "394" in err:
                dna_sleep(2.5, 2.5)
                continue
            if "709" in err:
                dna_sleep(0.83, 0.83)
                continue
            raise

    raise last_error or RuntimeError("Failed to refresh load/index state")

def update_start_state(data):
    global active_start_state
    if not data:
        return
    if data.get('tp_info'):
        tp_info = dict(data.get('tp_info'))
        active_start_state['tp_info'] = tp_info
    item_list = data.get('item_list') or data.get('user_item_array')
    if isinstance(item_list, list) and item_list:
        active_start_state['current_money'] = get_item_count(item_list, 59)
        active_start_state['succession_rank_point'] = get_item_count(item_list, 75)


def normalize_friend_cards(data):
    source = 'refresh'
    friend_data = data.get('friend_support_card_data')
    if friend_data:
        source = 'initial'
        summaries = friend_data.get('summary_user_info_array', [])
        support_cards = friend_data.get('support_card_data_array', [])
    else:
        summaries = data.get('summary_user_info_array', [])
        support_cards = data.get('support_card_data_array', [])

    support_by_key = {}
    for sc in support_cards or []:
        key = (sc.get('viewer_id'), sc.get('support_card_id'))
        support_by_key[key] = sc

    friends = []
    exclude_viewer_ids = []
    seen = set()
    for info in summaries or []:
        viewer_id = info.get('viewer_id')
        support_card_id = info.get('support_card_id')
        if not viewer_id or not support_card_id:
            continue
        key = (viewer_id, support_card_id)
        if key in seen:
            continue
        seen.add(key)
        exclude_viewer_ids.append(viewer_id)
        card_data = support_by_key.get(key) or info.get('user_support_card') or {}
        support_info = support_map.get(str(support_card_id), {})
        friends.append({
            'viewer_id': viewer_id,
            'name': info.get('name', ''),
            'support_card_id': support_card_id,
            'support_name': support_info.get('name', f"Unknown ({support_card_id})"),
            'rarity': support_info.get('rarity', '?'),
            'type': display_support_type(support_info.get('type', 'Unknown')),
            'exp': card_data.get('exp', info.get('user_support_card', {}).get('exp')),
            'limit_break_count': card_data.get('limit_break_count', info.get('user_support_card', {}).get('limit_break_count')),
            'favorite_flag': card_data.get('favorite_flag', 0),
            'friend_state': info.get('friend_state', 0)
        })
    return friends, exclude_viewer_ids, source


# Confirmed shape from a live pre_single_mode/index probe:
#   data.succession_trained_chara_data.succession_trained_chara_array  -> active rentals
#   data.event_succession_trained_chara_data.succession_trained_chara_array  -> event rentals (often empty)
# Each entry includes viewer_id + trained_chara_id (the two ids needed to borrow).
FRIEND_VETERAN_KEYS = ("succession_trained_chara_array",)
FRIEND_VETERAN_CONTAINER_KEYS = (
    "succession_trained_chara_data",
    "event_succession_trained_chara_data",
)


def _extract_veteran_rows(data):
    """Collect friend-veteran entries from the confirmed pre_single_mode containers.

    Returns a list of dicts. Each dict is the raw entry from the game; we'll
    normalise downstream.
    """
    candidates = []

    def absorb(value):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    candidates.append(item)

    for container_key in FRIEND_VETERAN_CONTAINER_KEYS:
        container = data.get(container_key) or {}
        if isinstance(container, dict):
            for key in FRIEND_VETERAN_KEYS:
                absorb(container.get(key))

    # Defensive: also accept the array at top-level in case the game ever
    # restructures the response.
    for key in FRIEND_VETERAN_KEYS:
        absorb(data.get(key))

    return candidates


def normalize_friend_veterans(data):
    """Build the list of friend-borrowable veterans surfaced by pre_single_mode.

    Returns (list, source_tag). Each result entry includes stats, rank, scenario,
    decoded factors and parent lineage cards so the UI picker can show enough
    info for the user to pick the strongest veteran to borrow.
    """
    global active_parent_rank_points
    rows = _extract_veteran_rows(data)
    if not rows:
        return [], "no_data"

    summaries_by_viewer = {}
    for info in data.get('summary_user_info_array', []) or []:
        vid = info.get('viewer_id')
        if vid is not None:
            summaries_by_viewer.setdefault(vid, info)
    friend_data = data.get('friend_support_card_data') or {}
    for info in friend_data.get('summary_user_info_array', []) or []:
        vid = info.get('viewer_id')
        if vid is not None:
            summaries_by_viewer.setdefault(vid, info)
    # The succession container also carries its own summary_user_info_array
    # (one entry per veteran's owner) — fold it in too.
    for ckey in FRIEND_VETERAN_CONTAINER_KEYS:
        cinfo = data.get(ckey) or {}
        if isinstance(cinfo, dict):
            for info in cinfo.get('summary_user_info_array', []) or []:
                vid = info.get('viewer_id')
                if vid is not None:
                    summaries_by_viewer.setdefault(vid, info)

    out = []
    seen = set()
    for row in rows:
        viewer_id = row.get('viewer_id') or row.get('owner_viewer_id') or 0
        trained_chara_id = row.get('trained_chara_id') or row.get('id') or 0
        card_id = row.get('card_id') or row.get('chara_id') or 0
        if not viewer_id or not trained_chara_id:
            continue
        key = (int(viewer_id), int(trained_chara_id))
        if key in seen:
            continue
        seen.add(key)

        active_parent_rank_points[int(trained_chara_id)] = {
            'rank': int(row.get('rank') or 0),
            'rank_score': int(row.get('rank_score') or 0)
        }

        summary = summaries_by_viewer.get(viewer_id) or {}
        chara_name = chara_map.get(str(card_id), f"Unknown ({card_id})")

        factors = []
        try:
            factors = get_factors(row.get('factor_id_array') or [], card_id)
        except Exception:
            factors = []

        # Parent lineage as plain card_ids (so UI can show "Mejiro McQueen+T.M.Opera O")
        parent_card_ids = []
        for sc in row.get('succession_chara_array') or []:
            pos = sc.get('position_id')
            if pos in (10, 20):  # direct parents only, skip grandparents
                pid = int(sc.get('card_id') or 0)
                if pid:
                    parent_card_ids.append(pid)

        # The user_support_card on the summary is what they share for borrowing.
        # row.support_card_list is the deck this specific veteran was RAISED with.
        deck_support_ids = [int(item.get('support_card_id') or 0)
                            for item in (row.get('support_card_list') or [])
                            if int(item.get('support_card_id') or 0)]
        deck_meta = _deck_meta_from_ids(deck_support_ids)

        out.append({
            'viewer_id': int(viewer_id),
            'trainer_name': summary.get('name', ''),
            'trained_chara_id': int(trained_chara_id),
            'card_id': int(card_id),
            'chara_name': chara_name,
            'rank': int(row.get('rank') or 0),
            'rank_score': int(row.get('rank_score') or 0),
            'scenario_id': int(row.get('scenario_id') or 0),
            'running_style': int(row.get('running_style') or 0),
            'talent_level': int(row.get('talent_level') or 0),
            # Final stats of the veteran — what determines its inheritance value
            'speed': int(row.get('speed') or 0),
            'stamina': int(row.get('stamina') or 0),
            'power': int(row.get('power') or 0),
            'guts': int(row.get('guts') or 0),
            'wiz': int(row.get('wiz') or 0),
            'wins': len(row.get('win_saddle_id_array') or []),
            'factors': factors,
            'parent_card_ids': parent_card_ids,
            'deck_support_ids': deck_support_ids,
            'deck_support_cards': deck_meta["deck_support_cards"],
            'deck_type_counts': deck_meta["deck_type_counts"],
            'deck_archetype': deck_meta["deck_archetype"],
            # The support card the owner currently shares (separate from the deck)
            'shared_support_card_id': int(summary.get('support_card_id') or 0),
        })

    out.sort(key=lambda v: (-v['rank_score'], -v['rank']))
    return out, "ok"

    support_by_key = {}
    for sc in support_cards or []:
        key = (sc.get('viewer_id'), sc.get('support_card_id'))
        support_by_key[key] = sc

    friends = []
    exclude_viewer_ids = []
    seen = set()
    for info in summaries or []:
        viewer_id = info.get('viewer_id')
        support_card_id = info.get('support_card_id')
        if not viewer_id or not support_card_id:
            continue
        key = (viewer_id, support_card_id)
        if key in seen:
            continue
        seen.add(key)
        exclude_viewer_ids.append(viewer_id)
        card_data = support_by_key.get(key) or info.get('user_support_card') or {}
        support_info = support_map.get(str(support_card_id), {})
        friends.append({
            'viewer_id': viewer_id,
            'name': info.get('name', ''),
            'support_card_id': support_card_id,
            'support_name': support_info.get('name', f"Unknown ({support_card_id})"),
            'rarity': support_info.get('rarity', '?'),
            'type': display_support_type(support_info.get('type', 'Unknown')),
            'exp': card_data.get('exp', info.get('user_support_card', {}).get('exp')),
            'limit_break_count': card_data.get('limit_break_count', info.get('user_support_card', {}).get('limit_break_count')),
            'favorite_flag': card_data.get('favorite_flag', 0),
            'friend_state': info.get('friend_state', 0)
        })
    return friends, exclude_viewer_ids, source


def normalize_card_name(name):
    return re.sub(r'[^a-z0-9]+', '', re.sub(r'\([^)]*\)', '', str(name or '').lower()))


def validate_start_selection(req):
    support_ids = [int(card_id) for card_id in req.support_card_ids]
    friend_card_id = int(req.friend_card_id)
    if friend_card_id in support_ids:
        return "Friend support card is already in selected deck"

    friend_info = support_map.get(str(friend_card_id), {})
    friend_name = normalize_card_name(friend_info.get('name'))
    if not friend_name:
        return None

    for support_id in support_ids:
        support_name = normalize_card_name(support_map.get(str(support_id), {}).get('name'))
        if support_name and support_name == friend_name:
            return "Friend support card has same character as selected deck"

    trainee_name = normalize_card_name(chara_map.get(str(req.card_id), ''))
    if trainee_name and trainee_name == friend_name:
        return "Friend support card has same character as trainee"

    parent1_cards = active_parent_cards.get(int(req.parent_id_1), [])
    parent2_cards = active_parent_cards.get(int(req.parent_id_2), [])
    if parent1_cards and parent2_cards and int(req.card_id) in (parent1_cards[0], parent2_cards[0]):
        return "Selected direct parent is same character as trainee"

    return None


def deck_type_counts_from_ids(support_ids, friend_card_id=0):
    return advisor.support_type_counts(
        list(support_ids or []) + ([friend_card_id] if friend_card_id else []),
        support_map,
    )


def deck_type_counts_from_chara(chara_info):
    ids = []
    for card in (chara_info or {}).get('support_card_array') or []:
        sid = int(card.get('support_card_id') or 0)
        if sid:
            ids.append(sid)
    return deck_type_counts_from_ids(ids)


def apply_deck_type_counts(preset, req=None, chara_info=None):
    counts = None
    if req and (req.support_card_ids or req.friend_card_id):
        counts = deck_type_counts_from_ids(req.support_card_ids, req.friend_card_id)
    elif chara_info:
        counts = deck_type_counts_from_chara(chara_info)
    if counts is not None:
        preset["_deck_type_counts"] = counts
        preset["_deck_archetype"] = advisor.deck_archetype(counts)
        scale_table = [0.0, 0.02, 0.05, 0.09, 0.14, 0.20]
        preset["_deck_multipliers"] = [1.0 + scale_table[min(5, c)] for c in counts]


def _selected_parent_advice(req, running_style=0):
    rows = []
    selected_ids = {int(req.parent_id_1 or 0), int(req.parent_id_2 or 0)}
    rental_key = (int(req.rental_viewer_id or 0), int(req.rental_chara_id or 0))

    for parent in (active_dashboard_data or {}).get("parents", []) if active_dashboard_data else []:
        if int(parent.get("instance_id") or 0) not in selected_ids:
            continue
        rows.append({
            "source": "owned",
            "candidate_id": f"owned:{parent.get('instance_id')}",
            "name": parent.get("name"),
            "advisor": advisor.score_parent_candidate({
                "card_id": parent.get("card_id"),
                "rank": parent.get("rank"),
                "rank_score": parent.get("rank_score"),
                "wins": ((parent.get("tree") or {}).get("self") or {}).get("wins", {}).get("total", 0),
                "factors": ((parent.get("tree") or {}).get("self") or {}).get("factors", []),
                "parent_card_ids": [
                    ((parent.get("tree") or {}).get("p1") or {}).get("card_id"),
                    ((parent.get("tree") or {}).get("p2") or {}).get("card_id"),
                ],
            }, req.card_id, running_style),
        })

    for vet in (active_dashboard_data or {}).get("friendVeterans", []) if active_dashboard_data else []:
        key = (int(vet.get("viewer_id") or 0), int(vet.get("trained_chara_id") or 0))
        if key != rental_key:
            continue
        rows.append({
            "source": "rental",
            "candidate_id": f"rental:{key[0]}:{key[1]}",
            "name": vet.get("chara_name"),
            "advisor": advisor.score_parent_candidate(vet, req.card_id, running_style),
        })
    return rows


def prepare_runtime_preset_for_run(preset, req, chara_info=None):
    running_style = int((preset or {}).get("running_style") or 0)
    parent_advice = _selected_parent_advice(req, running_style)
    tuned = advisor.prepare_runtime_preset(preset, parent_advice)
    return tuned, tuned.get("_runtime_advisor") or {}


RANK_POINTS = {
    1: 2,    # G
    2: 4,    # G+
    3: 6,    # F
    4: 9,    # F+
    5: 12,   # E
    6: 16,   # E+
    7: 20,   # D
    8: 25,   # D+
    9: 30,   # C
    10: 36,  # C+
    11: 42,  # B
    12: 49,  # B+
    13: 62,  # A
    14: 73,  # A+
    15: 82,  # S
    16: 82,  # S+
    17: 92,  # SS
    18: 92,  # SS+
    19: 103, # UG
    20: 103, # UG+
    21: 113, # UF
    22: 113, # UF+
    23: 124, # UE
    24: 124, # UE+
    25: 136, # UD
    26: 136, # UD+
    27: 148, # UC
    28: 148, # UC+
    29: 160, # UB
    30: 160, # UB+
    31: 173, # UA
    32: 173, # UA+
    33: 186, # US
    34: 186, # US+
    35: 200, # USS
    36: 200, # USS+
}

def get_rank_points(rank: int) -> int:
    """Return succession rank points based on the evaluation rank ID."""
    if rank <= 0:
        return 0
    if rank in RANK_POINTS:
        return RANK_POINTS[rank]
    # Fallback extrapolation for extremely high ranks
    return 200 + (rank - 36) * 7


def parent_rank_point(parent_id):
    parent_id = int(parent_id)
    if not parent_id:
        return 0
    # Look in cache
    parent = active_parent_rank_points.get(parent_id)
    if parent:
        return get_rank_points(int(parent.get('rank') or 0))
    # Fallback to active_dashboard_data parents
    if active_dashboard_data and active_dashboard_data.get('parents'):
        for p in active_dashboard_data['parents']:
            if int(p.get('instance_id') or 0) == parent_id:
                rank = int(p.get('rank') or 0)
                active_parent_rank_points[parent_id] = {
                    'rank': rank,
                    'rank_score': int(p.get('rank_score') or 0)
                }
                return get_rank_points(rank)
    # Fallback to friendVeterans
    if active_dashboard_data and active_dashboard_data.get('friendVeterans'):
        for v in active_dashboard_data['friendVeterans']:
            if int(v.get('trained_chara_id') or 0) == parent_id:
                rank = int(v.get('rank') or 0)
                active_parent_rank_points[parent_id] = {
                    'rank': rank,
                    'rank_score': int(v.get('rank_score') or 0)
                }
                return get_rank_points(rank)
    return 0


def selected_succession_rank_point(req):
    p2 = req.rental_chara_id if req.rental_chara_id else req.parent_id_2
    selected_total = parent_rank_point(req.parent_id_1) + parent_rank_point(p2)
    if selected_total:
        return selected_total
    return active_start_state.get('succession_rank_point', 0)

skill_data = {}
skill_data_path = base_dir / 'data' / 'skill_data.json'
if skill_data_path.exists():
    with open(skill_data_path, 'r', encoding='utf-8') as f:
        skill_data = json.load(f)

factor_map = {}
factor_map_path = base_dir / 'data' / 'factor_map.json'
if factor_map_path.exists():
    with open(factor_map_path, 'r', encoding='utf-8') as f:
        factor_map = json.load(f)

race_map = {}
race_map_path = base_dir / 'data' / 'race_map.json'
if race_map_path.exists():
    with open(race_map_path, 'r', encoding='utf-8') as f:
        race_map = json.load(f)

def skill_entry_name(entry):
    if isinstance(entry, dict):
        return entry.get("name") or ""
    return entry

def get_win_summary(win_saddle_ids):
    summary = {
        "g1": 0,
        "g2": 0,
        "g3": 0
    }

    for saddle_id in win_saddle_ids or []:
        race = race_map.get(str(saddle_id))
        grade = race.get("grade") if race else None
        if grade == "G1":
            summary["g1"] += 1
        elif grade == "G2":
            summary["g2"] += 1
        elif grade == "G3":
            summary["g3"] += 1

    summary["total"] = summary["g1"] + summary["g2"] + summary["g3"]
    return summary

def clean_factor_name(name, base_id=None, category=None):
    if not isinstance(name, str):
        return name

    if category == "skill" and "?" in name and base_id is not None:
        skill_name = skill_entry_name(skill_data.get(f"{base_id}2"))
        if skill_name:
            return skill_name
    return name.replace(" ?", " ○")

def get_factors(fid_array, owner_card_id=None):
    results = []
    category_order = {
        "stat": 0,
        "aptitude": 1,
        "unique": 2,
        "race": 3,
        "skill": 4,
        "scenario": 5,
        "other": 6
    }
    stat_map = {
        1: 'Speed', 2: 'Stamina', 3: 'Power', 4: 'Guts', 5: 'Wit',
        11: 'Turf', 12: 'Dirt',
        21: 'Short', 22: 'Mile', 23: 'Medium', 24: 'Long',
        31: 'Front Runner', 32: 'Pace Chaser', 33: 'Late Surger', 34: 'End Closer'
    }
    
    owner_cid_str = str(owner_card_id) if owner_card_id else ""
    if len(owner_cid_str) > 4: owner_cid_str = owner_cid_str[:4]

    for fid in fid_array:
        if not fid or fid <= 0: continue

        fid_str = str(fid)
        factor_info = factor_map.get(fid_str)
        if factor_info:
            base_id = fid // 100
            category = factor_info.get("category", "other")
            name = clean_factor_name(factor_info.get("name", f"Unknown({fid})"), base_id, category)
            stars = factor_info.get("stars", fid % 100)
            results.append({"name": name, "stars": stars, "id": fid, "category": category})
            continue

        base_id = fid // 100
        stars = fid % 100
        bid_str = str(base_id)
        name = f"Unknown({base_id})"
        category = "other"
        
        if base_id <= 34:
            category = "stat" if base_id <= 5 else "aptitude"
            name = stat_map.get(base_id, name)
        
        elif bid_str in skill_data:
            category = "skill"
            name = skill_entry_name(skill_data[bid_str])
            
        results.append({"name": name, "stars": stars, "id": base_id, "category": category})

    return [
        factor for _, factor in sorted(
            enumerate(results),
            key=lambda item: (category_order.get(item[1]["category"], 99), item[0])
        )
    ]


def get_chara_factor_ids(chara):
    factor_ids = chara.get('factor_id_array')
    if isinstance(factor_ids, list) and factor_ids:
        return factor_ids
    return [f.get('factor_id', 0) for f in chara.get('factor_info_array', [])]


def get_item_count(item_list, item_id):
    for item in item_list or []:
        if item.get('item_id') == item_id:
            return item.get('number', 0)
    return 0


def get_account_status(data, career_data=None):
    tp_info = data.get('tp_info') or (active_client.tp_info if active_client else {})
    coin_info = data.get('coin_info') or (active_client.coin_info if active_client else {})
    item_list = data.get('item_list') or data.get('user_item_array')
    if item_list is None:
        gold = active_client.item_map.get(59, 0) if active_client else 0
    else:
        gold = get_item_count(item_list, 59)
    career = data.get('single_mode_chara_light') or None

    if career_data:
        career_payload = career_data.get('data') if career_data.get('data') else career_data
        if career_payload.get('chara_info'):
            career = career_payload.get('chara_info')

    status = {
        "tp": {
            "current": tp_info.get('current_tp', 0),
            "max": tp_info.get('max_tp', 0)
        },
        "carrots": {
            "free": coin_info.get('fcoin', 0) or 0,
            "paid": coin_info.get('coin', 0) or 0,
            "total": (coin_info.get('fcoin', 0) or 0) + (coin_info.get('coin', 0) or 0)
        },
        "gold": gold,
        "clocks": active_client.item_map.get(95, 0) if active_client else 0,
        "career": None
    }
    if career:
        card_id = str(career.get('card_id', ''))
        
        p1 = career.get('succession_trained_chara_id_1')
        p2 = career.get('succession_trained_chara_id_2')

        friend_viewer_id = None
        friend_card_id = None
        friend_support = None
        current_deck_cards = []
        current_deck_supports = []
        
        support_array = career.get('support_card_array') or []
        for sc in support_array:
            pos = sc.get('position')
            if pos == 6:
                friend_viewer_id = sc.get('owner_viewer_id')
                friend_card_id = sc.get('support_card_id')
                friend_info = support_map.get(str(friend_card_id))
                friend_support = {
                    "viewer_id": friend_viewer_id,
                    "support_card_id": friend_card_id,
                    "support_name": friend_info['name'] if friend_info else f"Unknown ({friend_card_id})",
                    "rarity": friend_info['rarity'] if friend_info else "?",
                    "type": display_support_type(friend_info['type']) if friend_info else "?",
                    "limit_break_count": sc.get('limit_break_count')
                }
            elif 1 <= pos <= 5:
                support_card_id = sc.get('support_card_id')
                current_deck_cards.append(support_card_id)
                support_info = support_map.get(str(support_card_id))
                current_deck_supports.append({
                    "id": str(support_card_id),
                    "name": support_info['name'] if support_info else f"Unknown ({support_card_id})",
                    "rarity": support_info['rarity'] if support_info else "?",
                    "type": display_support_type(support_info['type']) if support_info else "?"
                })

        matched_deck_id = None
        user_decks = data.get('support_card_deck_array') or []
        if current_deck_cards:
            current_deck_set = set(current_deck_cards)
            for deck in user_decks:
                deck_cards = deck.get('support_card_id_array') or []
                if set(deck_cards) == current_deck_set:
                    matched_deck_id = deck.get('deck_id')
                    break

        status["career"] = {
            "active": True,
            "card_id": card_id,
            "name": chara_map.get(card_id, f"Unknown ({card_id})"),
            "turn": career.get('turn', 0),
            "scenario_id": career.get('scenario_id', 0),
            "fans": career.get('fans', 0),
            "vital": career.get('vital', 0),
            "max_vital": career.get('max_vital', 0),
            "deck_id": matched_deck_id,
            "support_card_ids": current_deck_cards,
            "support_cards": current_deck_supports,
            "friend_viewer_id": friend_viewer_id,
            "friend_card_id": friend_card_id,
            "friend": friend_support,
            "parent_id_1": p1,
            "parent_id_2": p2,
        }

    return status




class LoginRequest(BaseModel):
    username: str = ""
    password: str = ""
    code: str = ""
    steam_id: str = ""
    steam_session_ticket: str = ""

class DeleteCareerRequest(BaseModel):
    current_turn: int = 0

class FinishCareerRequest(BaseModel):
    # Natural-finish (save the trained character) versus force-delete.
    # Mirrors the runner's `decision.action == "finish"` recovery branch:
    # spend leftover SP on skills, drain any residual events, then call
    # single_mode_free/finish with is_force_delete=False.
    current_turn: int = 0
    preset_name: str = ""
    buy_skills: bool = True

class StartCareerRequest(BaseModel):
    card_id: int
    support_card_ids: list[int]
    friend_viewer_id: int
    friend_card_id: int
    parent_id_1: int
    parent_id_2: int
    scenario_id: int = 4
    deck_id: int = 1
    use_tp: int = 30
    difficulty_id: int = 0
    difficulty: int = 0
    is_boost: int = 0
    boost_story_event_id: int = 0
    burn_clocks: bool = False
    # 3rd inheritance slot: borrow a friend's veteran uma as an extra parent.
    # rental_viewer_id is the friend's viewer_id (uma.moe account_id), and
    # rental_chara_id is THAT veteran's trained_chara_id on the friend's account
    # (not a card_id; an instance id like 40119368).
    rental_viewer_id: int = 0
    rental_chara_id: int = 0

class RunCareerRequest(BaseModel):
    card_id: int = 0
    support_card_ids: list[int] = []
    friend_viewer_id: int = 0
    friend_card_id: int = 0
    parent_id_1: int = 0
    parent_id_2: int = 0
    scenario_id: int = 0
    deck_id: int = 1
    use_tp: int = 30
    difficulty_id: int = 0
    difficulty: int = 0
    is_boost: int = 0
    boost_story_event_id: int = 0
    preset_name: str = ""
    rental_viewer_id: int = 0
    rental_chara_id: int = 0
    max_steps: int = 2500
    burn_clocks: bool = False
    dev_mode: bool = False

class SaveRacesRequest(BaseModel):
    preset_name: str
    races: list[int]

class SavePresetRequest(BaseModel):
    preset: dict

class DeletePresetByNameRequest(BaseModel):
    name: str

class CareerActionRequest(BaseModel):
    command_type: int
    command_id: int
    current_turn: int
    current_vital: int
    command_group_id: int = 0
    select_id: int = 0

class FriendListRequest(BaseModel):
    exclude_viewer_ids: list[int] = []
    force_refresh: bool = False

class FriendManageRequest(BaseModel):
    viewer_id: int

class AdvisorRequest(BaseModel):
    trainee_card_id: int = 0
    running_style: int = 0

class ApiDelayRequest(BaseModel):
    min: float = 1.6
    max: float = 4.0
    disabled: bool = False

class MasterDataPathRequest(BaseModel):
    master_mdb_path: str

class EventBoostSettingsRequest(BaseModel):
    # Mirrors the in-game "Event Boost (TP Usage x2)" checkbox.
    # `enabled` flips the toggle. `story_event_id` is the limited-time
    # story event id whose EP bonus applies. Both are persisted in settings.json
    # so the toggle (and event id) survive server restarts.
    enabled: bool = False
    story_event_id: int = 0

class RefillTpRequest(BaseModel):
    count: int = 0
    to_max: bool = True

class LocalDeckSaveRequest(BaseModel):
    id: str = ""
    name: str = "Sweepy Deck"
    support_card_ids: list[int] = []
    deck_id: int = 1

class UmaMoeImportRequest(BaseModel):
    trainer_id: str
    preset_name: str = ""
    create_only: bool = False
    overwrite_races: bool = True
    overwrite_skills: bool = True
    overwrite_running_style: bool = True
    overwrite_supports: bool = True
    overwrite_trainee: bool = True
    overwrite_stats: bool = False

@app.get("/api/settings/turn-delay")
async def get_turn_delay_settings():
    return get_turn_delay()

@app.post("/api/settings/turn-delay")
async def set_turn_delay_settings(req: ApiDelayRequest):
    return set_turn_delay(req.min, req.max, req.disabled)


# Event Boost (TP Usage x2) settings ------------------------------------------------
# The active limited-time story event id changes every event period, so we cache
# the user's chosen value in settings.json. The boost toggle itself is also
# persisted so the user doesn't have to re-enable it after each restart.
EVENT_BOOST_TP_MULTIPLIER = 2


def _read_event_boost_settings():
    settings = master_data.read_settings(base_dir)
    raw = settings.get("event_boost") or {}
    try:
        story_event_id = int(raw.get("story_event_id") or 0)
    except (TypeError, ValueError):
        story_event_id = 0
    return {
        "enabled": bool(raw.get("enabled")),
        "story_event_id": max(0, story_event_id),
        "tp_multiplier": EVENT_BOOST_TP_MULTIPLIER,
    }


def _write_event_boost_settings(enabled, story_event_id):
    settings = master_data.read_settings(base_dir)
    block = settings.setdefault("event_boost", {})
    block["enabled"] = bool(enabled)
    try:
        block["story_event_id"] = max(0, int(story_event_id or 0))
    except (TypeError, ValueError):
        block["story_event_id"] = 0
    master_data.write_settings(base_dir, settings)
    return _read_event_boost_settings()


@app.get("/api/settings/event-boost")
async def get_event_boost_settings():
    return {"success": True, **_read_event_boost_settings()}


@app.post("/api/settings/event-boost")
async def set_event_boost_settings(req: EventBoostSettingsRequest):
    return {"success": True, **_write_event_boost_settings(req.enabled, req.story_event_id)}

@app.get("/api/master-data/status")
async def master_data_status():
    return master_data.status(base_dir)

@app.post("/api/master-data/path")
async def set_master_data_path(req: MasterDataPathRequest):
    status = master_data.set_master_mdb_path(base_dir, req.master_mdb_path)
    if status.get("exists"):
        result = master_data.generate(base_dir)
        if result.get("success"):
            status["generated"] = result.get("generated", [])
        else:
            status["generation_error"] = result.get("detail") or "master_data generation failed"
    return status

@app.post("/api/master-data/generate")
async def generate_master_data():
    result = master_data.generate(base_dir)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("detail") or "master_data generation failed")
    return result

@app.post("/api/presets/save_races")
async def save_races(req: SaveRacesRequest):
    preset = preset_store.read_one(req.preset_name)
    if not preset:
        return {"success": False, "detail": f"{req.preset_name} preset missing"}
    preset["extra_race_list"] = req.races
    preset_store.write(preset)
    return {"success": True}

@app.get("/api/presets")
async def get_presets():
    return {"success": True, "presets": preset_store.read_all()}

@app.post("/api/presets")
async def save_preset(req: SavePresetRequest):
    return {"success": True, "preset": preset_store.write(req.preset)}

@app.post("/api/presets/delete")
async def delete_preset(req: DeletePresetByNameRequest):
    return {"success": preset_store.delete(req.name)}

@app.get("/api/skills")
async def get_skills():
    current_skill_data = {}
    path = base_dir / 'data' / 'skill_data.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            current_skill_data = json.load(f)
    return {"success": True, "skills": current_skill_data}


@app.get("/api/local-decks")
async def get_local_decks():
    return {"success": True, "decks": _local_decks_payload()}


@app.post("/api/local-decks")
async def save_local_deck(req: LocalDeckSaveRequest):
    global active_dashboard_data
    deck = _normalise_local_deck({
        'id': req.id,
        'name': req.name,
        'support_card_ids': req.support_card_ids,
        'deck_id': req.deck_id,
    })
    if len(deck['support_card_ids']) != 5:
        raise HTTPException(status_code=400, detail="A Sweepy deck needs exactly 5 owned support cards; the friend card is selected separately.")
    decks = [d for d in _read_local_decks() if str(d.get('id')) != deck['id']]
    decks.append({
        'id': deck['id'],
        'name': deck['name'],
        'deck_id': deck['deck_id'],
        'support_card_ids': deck['support_card_ids'],
    })
    _write_local_decks(decks)
    local_decks = _local_decks_payload()
    if active_dashboard_data is not None:
        active_dashboard_data["decks"] = [
            d for d in active_dashboard_data.get("decks", [])
            if not d.get("local")
        ] + local_decks
    return {"success": True, "deck": deck, "decks": local_decks}


@app.post("/api/tp/refill")
async def refill_tp(req: RefillTpRequest):
    global active_account, active_dashboard_data
    if not active_client:
        return {"success": False, "detail": "Not logged in"}
    try:
        res = active_client.read_info()
        data = res.get('data', {})
        active_client.refresh_cached_account_state(data)
        update_start_state(data)
    except Exception:
        data = {}
    tp_info = active_start_state.get('tp_info') or active_client.tp_info or {}
    current_tp = int(tp_info.get('current_tp') or 0)
    max_tp = int(tp_info.get('max_tp') or 100)
    count = int(req.count or 0)
    if req.to_max:
        count = max(0, ((max_tp - current_tp) + 29) // 30)
    if count <= 0:
        account = get_account_status(data or {})
        active_account = account
        if active_dashboard_data:
            active_dashboard_data["account"] = account
        return {"success": True, "detail": "TP already full", "account": account}
    tp = active_client.recovery_tp(count)
    if tp:
        active_start_state['tp_info'] = tp
    try:
        res = active_client.read_info()
        data = res.get('data', {})
        active_client.refresh_cached_account_state(data)
        update_start_state(data)
    except Exception:
        data = {'tp_info': active_client.tp_info, 'coin_info': active_client.coin_info}
    account = get_account_status(data)
    active_account = account
    if active_dashboard_data:
        active_dashboard_data["account"] = account
    return {"success": True, "count": count, "tp": active_client.tp_info, "account": account}


def _load_data_file(filename):
    path = base_dir / 'data' / filename
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


@app.get("/api/uma-moe/charas")
async def uma_moe_charas():
    """Return the local chara_id -> name map used to populate the search picker.

    Stable IDs already include the talent suffix (e.g. 101301 = Mejiro McQueen
    base, 101302 = alt) which is exactly what uma.moe's `main_parent_id`
    filter wants, so the front-end can pass an entry's key straight through.
    """
    return {"success": True, "charas": chara_map}


@app.get("/api/uma-moe/search")
async def uma_moe_search(chara_id: int = 0, page: int = 0, limit: int = 15):
    """Return uma.moe trainers whose trainee matches `chara_id`.

    uma.moe's /database UI affinity filter does NOT actually filter by the
    selected uma — it scores parent affinity, so results include other umas.
    This endpoint hits their /api/v3/search with `main_parent_id` instead,
    which IS the trainee-card filter, and surfaces the result in a compact
    shape the dashboard can render directly.
    """
    if chara_id <= 0:
        raise HTTPException(status_code=400, detail="chara_id must be a positive integer")
    try:
        raw = uma_moe_importer.search_trainers(chara_id, page=page, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"uma.moe search failed: {exc}")

    chara_data = _load_data_file("chara_list.json") or chara_map
    support_data = _load_data_file("support_list.json") or support_map
    items = raw.get("items") or []
    results = [
        uma_moe_importer.summarize_search_result(
            item,
            chara_data,
            support_data,
            _load_data_file("race_map.json"),
        )
        for item in items
    ]
    total_raw = raw.get("total")
    if isinstance(total_raw, str) and total_raw.startswith("over"):
        total_value = total_raw
    else:
        try:
            total_value = int(total_raw)
        except (TypeError, ValueError):
            total_value = len(results)
    return {
        "success": True,
        "chara_id": chara_id,
        "chara_name": (chara_data or {}).get(str(chara_id)) or "",
        "page": int(raw.get("page") or page or 0),
        "limit": int(raw.get("limit") or limit or 15),
        "total": total_value,
        "total_pages": int(raw.get("total_pages") or 0),
        "results": results,
    }


@app.get("/api/uma-moe/trainer/{trainer_id}")
async def uma_moe_preview(trainer_id: str):
    """Fetch a trainer from uma.moe and return the decoded preset patch (no write)."""
    try:
        record = uma_moe_importer.fetch_trainer(trainer_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"uma.moe fetch failed: {exc}")

    patch = uma_moe_importer.build_preset_patch(
        record,
        factor_map=_load_data_file("factor_map.json"),
        race_map=_load_data_file("race_map.json"),
        chara_map=_load_data_file("chara_list.json"),
        support_list=_load_data_file("support_list.json"),
    )
    return {"success": True, "trainer": record, "patch": patch}


@app.post("/api/uma-moe/import")
async def uma_moe_import(req: UmaMoeImportRequest):
    """Fetch a trainer from uma.moe and merge into a preset (create if missing)."""
    try:
        record = uma_moe_importer.fetch_trainer(req.trainer_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"uma.moe fetch failed: {exc}")

    patch = uma_moe_importer.build_preset_patch(
        record,
        factor_map=_load_data_file("factor_map.json"),
        race_map=_load_data_file("race_map.json"),
        chara_map=_load_data_file("chara_list.json"),
        support_list=_load_data_file("support_list.json"),
    )

    target_name = (req.preset_name or "").strip()
    if not target_name:
        trainer_name = patch.get("imported_trainer_name") or req.trainer_id
        target_name = f"uma.moe {trainer_name}"

    if req.create_only and preset_store.read_one(target_name):
        raise HTTPException(status_code=409, detail=f"Preset '{target_name}' already exists")

    existing = preset_store.read_one(target_name) or {"name": target_name}
    merged = uma_moe_importer.merge_into_preset(
        existing,
        patch,
        overwrite_skills=req.overwrite_skills,
        overwrite_races=req.overwrite_races,
        overwrite_stats=req.overwrite_stats,
    )
    # The merge helper covers race/skill/min/max/running_style/import metadata.
    # The flags below let the caller opt-out of overwriting supports/trainee,
    # which is useful when retargeting an existing preset to a new trainer.
    if not req.overwrite_supports:
        for key in ("friend_card_id", "friend_viewer_id"):
            if key in existing:
                merged[key] = existing[key]
    if not req.overwrite_trainee:
        if "trainee_card_id" in existing:
            merged["trainee_card_id"] = existing["trainee_card_id"]
    if not req.overwrite_running_style and "running_style" in existing:
        merged["running_style"] = existing["running_style"]
    merged["name"] = target_name

    written = preset_store.write(merged)
    return {
        "success": True,
        "preset": written,
        "patch": patch,
    }

def start_career_from_request(req):
    global active_account, active_dashboard_data
    if not active_client:
        return {"success": False, "detail": "Not logged in"}

    if active_account and active_account.get("career") and active_account["career"].get("active"):
         return {"success": False, "detail": "Cannot start a new career while another is active"}

    if not req.friend_viewer_id or not req.friend_card_id:
        return {"success": False, "detail": "Friend support card is required"}
    
    selection_error = validate_start_selection(req)
    if selection_error:
        return {"success": False, "detail": selection_error}

    try:
        res = active_client.read_info()
        data = res.get('data', {})
        active_client.refresh_cached_account_state(data)
        update_start_state(data)
        if active_account:
            active_account = get_account_status(data)
            if active_dashboard_data:
                active_dashboard_data["account"] = active_account
    except Exception:
        pass
        
    if not active_start_state.get('tp_info'):
        return {"success": False, "detail": "Missing live TP state; login again before starting career"}
    if 'current_money' not in active_start_state:
        return {"success": False, "detail": "Missing live item state; login again before starting career"}

    tp_info = active_start_state['tp_info']
    current_tp = int(tp_info.get('current_tp') or 0)
    if req.use_tp and current_tp < req.use_tp:
        for attempt in range(3):
            try:
                needed = ((req.use_tp - current_tp) + 29) // 30
                active_client.recovery_tp(needed)
                tp_info = active_client.tp_info
                active_start_state['tp_info'] = tp_info
                current_tp = int(tp_info.get('current_tp') or 0)
                if current_tp >= req.use_tp:
                    break
            except Exception as e:
                if "213" in str(e):
                    try:
                        res = refresh_index_state(active_client)
                        active_client.refresh_cached_account_state(res.get("data", {}))
                    except Exception:
                        pass
                dna_sleep(1.0, 1.0)

    if req.use_tp and current_tp < req.use_tp:
        return {"success": False, "detail": f"Not enough TP: {current_tp}/{req.use_tp}"}
    current_money = active_start_state['current_money']
    succession_rank_point = selected_succession_rank_point(req)

    try:
        active_client.pre_single_mode([req.friend_viewer_id] if req.friend_viewer_id else [])
        dna_sleep(0.5, 1.5)
    except Exception:
        pass

    result = active_client.start_career(
        card_id=req.card_id,
        support_card_ids=req.support_card_ids,
        friend_viewer_id=req.friend_viewer_id,
        friend_card_id=req.friend_card_id,
        parent_id_1=req.parent_id_1,
        parent_id_2=req.parent_id_2,
        scenario_id=req.scenario_id,
        deck_id=req.deck_id,
        use_tp=req.use_tp,
        tp_info=tp_info,
        current_money=current_money,
        succession_rank_point=succession_rank_point,
        rental_viewer_id=req.rental_viewer_id,
        rental_trained_chara_id=req.rental_chara_id,
        difficulty_id=req.difficulty_id,
        difficulty=req.difficulty,
        is_boost=req.is_boost,
        boost_story_event_id=req.boost_story_event_id
    )
    return {"success": True, "result": result}

def apply_career_result(result):
    global active_account, active_dashboard_data
    result_data = result.get('data', {})
    update_start_state(result_data)
    account = get_account_status(result_data, result)
    chara_info = result_data.get('chara_info') or {}
    if chara_info:
        account["career"] = account.get("career") or {}
        card_id = str(chara_info.get('card_id', account["career"].get("card_id", '')))
        account["career"].update({
            "active": True,
            "card_id": card_id,
            "name": chara_map.get(card_id, f"Unknown ({card_id})"),
            "turn": chara_info.get('turn', 0),
            "scenario_id": chara_info.get('scenario_id', 0),
            "fans": chara_info.get('fans', 0),
            "vital": chara_info.get('vital', 0),
            "max_vital": chara_info.get('max_vital', 0)
        })
    active_account = account
    if active_dashboard_data:
        active_dashboard_data["account"] = account
    return account, chara_info

@app.post("/api/login")
async def login(req: LoginRequest):
    from uma_api.client import UmaClient, get_ticket
    from career_bot.delay import GateKeeper
    global active_client, active_account, active_dashboard_data, active_start_state, active_parent_cards, active_parent_rank_points, pending_game_auth_config, raw_load_index_response, active_selection
    try:
        chara = None
        cfg = dict(pending_game_auth_config)
        pending_game_auth_config = {}

        active_client = None
        active_account = None
        active_dashboard_data = None
        active_start_state = {}
        active_parent_cards = {}
        active_parent_rank_points = {}
        raw_load_index_response = None
        active_selection = {
            "deck": None,
            "friend": None,
            "trainee": None,
            "veterans": []
        }

        has_form_creds = bool(req.username and req.password)
        if req.steam_id and req.steam_session_ticket:
            sid = str(req.steam_id)
            tkt = str(req.steam_session_ticket)
            print('Using provided Steam ticket')
        elif has_form_creds:
            sid, tkt = get_ticket(req.username, req.password, req.code)
        else:
            raise Exception('Steam credentials required')

        if not cfg.get('steam_id') or not cfg.get('steam_session_ticket'):
            cfg.update({
                'steam_id': sid,
                'steam_session_ticket': tkt,
            })
        cfg['steam_password_seed'] = req.password
        if not has_fresh_auth_config(cfg):
            raise Exception('Fresh in-game auth capture required; switch to the target in-game account, restart capture, then login again')

        c = UmaClient(cfg, trace_enabled=False)
        gated_client = GateKeeper(c)
        res = gated_client.login()
        if not res:
            raise HTTPException(status_code=401, detail="Game login failed")
        active_client = gated_client

        d = res.get('data', {})
        career_data = None
        if d.get('single_mode_chara_light') or d.get('single_mode_chara'):
            try:
                career_res = active_client.load_career()
                career_data = career_res.get('data')
            except Exception:
                pass
        
        account = get_account_status(d, career_data)
        active_account = account
        active_start_state = {}
        active_parent_cards = {}
        active_parent_rank_points = {}
        update_start_state(d)
        
        umas = []
        card_list = d.get('card_list', [])
        for card in card_list:
            cid = str(card.get('card_id', card.get('id', '')))
            umas.append({
                'id': cid, 
                'name': chara_map.get(cid, f"Unknown ({cid})")
            })
            
        supports = []
        support_card_list = d.get('support_card_list', [])
        owned_supports_by_id = {}
        for s in support_card_list:
            sid = str(s.get('support_card_id', s.get('id', '')))
            try:
                owned_supports_by_id[int(sid)] = s
            except (TypeError, ValueError):
                pass
            info = support_map.get(sid)
            if info:
                supports.append({
                    'id': sid, 
                    'name': info['name'], 
                    'type': display_support_type(info['type']),
                    'rarity': info['rarity'],
                    'exp': s.get('exp'),
                    'limit_break_count': s.get('limit_break_count'),
                    'favorite_flag': s.get('favorite_flag', 0),
                })
            else:
                supports.append({
                    'id': sid, 
                    'name': f"Unknown ({sid})", 
                    'type': 'Unknown', 
                    'rarity': '?',
                    'exp': s.get('exp'),
                    'limit_break_count': s.get('limit_break_count'),
                    'favorite_flag': s.get('favorite_flag', 0),
                })
                
        decks = []
        deck_array = d.get('support_card_deck_array', [])
        for deck in deck_array:
            cards = []
            for cid in deck.get('support_card_id_array', []):
                sid = str(cid)
                info = support_map.get(sid)
                if info:
                    cards.append({
                        'id': sid,
                        'name': info['name'],
                        'rarity': info['rarity'],
                        'type': display_support_type(info['type']),
                        'exp': owned_supports_by_id.get(int(cid), {}).get('exp'),
                        'limit_break_count': owned_supports_by_id.get(int(cid), {}).get('limit_break_count'),
                    })
                else:
                    cards.append({'id': sid, 'name': f'Unknown ({sid})', 'rarity': '?', 'type': '?', 'exp': owned_supports_by_id.get(int(cid), {}).get('exp'), 'limit_break_count': owned_supports_by_id.get(int(cid), {}).get('limit_break_count')})
            
            decks.append({
                'id': deck.get('deck_id'),
                'name': deck.get('name', f'Deck {deck.get("deck_id")}'),
                'cards': cards
            })
        decks.extend(_local_decks_payload(owned_supports_by_id))

        parents = []
        trained_chara_list = d.get('trained_chara', [])
        for chara in trained_chara_list:


            raw_id = str(chara.get('card_id', ''))

            if '{' in raw_id or '-' in raw_id or not raw_id.isdigit():
                found = False
                for key, val in chara.items():
                    val_str = str(val)
                    if val_str.isdigit() and len(val_str) >= 4:
                        raw_id = val_str
                        found = True
                        break
                if not found:
                    continue
            
            cid = raw_id

            tree = {
                "self": {"card_id": cid, "name": chara_map.get(cid, f"Unknown ({cid})"), "factors": [], "wins": get_win_summary(chara.get('win_saddle_id_array', []))},
                "p1": {"card_id": 0, "name": "", "factors": [], "wins": get_win_summary([])},
                "p2": {"card_id": 0, "name": "", "factors": [], "wins": get_win_summary([])},
                "gp1": {"card_id": 0, "name": "", "factors": [], "wins": get_win_summary([])},
                "gp2": {"card_id": 0, "name": "", "factors": [], "wins": get_win_summary([])},
                "gp3": {"card_id": 0, "name": "", "factors": [], "wins": get_win_summary([])},
                "gp4": {"card_id": 0, "name": "", "factors": [], "wins": get_win_summary([])}
            }
            
            tree["self"]["factors"] = get_factors(get_chara_factor_ids(chara), cid)

            for sc in chara.get('succession_chara_array', []):
                pos = sc.get('position_id')
                sc_cid = sc.get('card_id', 0)
                key = ""
                if pos == 10: key = "p1"
                elif pos == 20: key = "p2"
                elif pos == 11: key = "gp1"
                elif pos == 12: key = "gp2"
                elif pos == 21: key = "gp3"
                elif pos == 22: key = "gp4"
                
                if key:
                    tree[key]["card_id"] = sc_cid
                    tree[key]["name"] = chara_map.get(str(sc_cid), f"Unknown ({sc_cid})")
                    tree[key]["factors"] = get_factors(sc.get('factor_id_array', []), sc_cid)
                    tree[key]["wins"] = get_win_summary(sc.get('win_saddle_id_array', []))


            parents.append({
                'instance_id': chara.get('trained_chara_id'),
                'card_id': cid,
                'name': chara_map.get(cid, f"Unknown ({cid})"),
                'rank': chara.get('rank', 0),
                'rank_score': chara.get('rank_score', 0),
                'tree': tree
            })
            lineage_cards = [int(cid)]
            for sc in chara.get('succession_chara_array', []) or []:
                sc_cid = sc.get('card_id', 0)
                if sc_cid:
                    lineage_cards.append(int(sc_cid))
            active_parent_cards[int(chara.get('trained_chara_id'))] = lineage_cards
            active_parent_rank_points[int(chara.get('trained_chara_id'))] = {
                'rank': chara.get('rank', 0),
                'rank_score': chara.get('rank_score', 0)
            }

                
        active_dashboard_data = {
            "success": True,
            "account": account,
            "umas": umas,
            "supports": supports,
            "decks": decks,
            "parents": parents
        }
        _save_session_cache({
            "viewer_id": int(getattr(active_client, "viewer_id", 0) or 0),
            "career": _career_snapshot_for_cache(account),
            "last_login_at": datetime.now(timezone.utc).isoformat(),
        })
        return active_dashboard_data
    except Exception as e:
        msg = str(e)
        if "STEAM_GUARD_REQUIRED" in msg:
             pending_game_auth_config = cfg
             return {"success": False, "needs_2fa": True}
        return {"success": False, "detail": str(e)}

@app.get("/api/session")
async def session_status():
    global active_client, active_dashboard_data, active_account, active_selection
    if not active_client or not active_dashboard_data:
        return {"success": False}
    
    data = dict(active_dashboard_data)
    if active_account:
        data["account"] = active_account
    data["selection"] = active_selection
    data["success"] = True
    return data

class UISelectionRequest(BaseModel):
    selection: dict

@app.post("/api/selection")
async def update_selection(req: UISelectionRequest):
    global active_selection
    active_selection = req.selection
    return {"success": True}


class SessionCacheUpdateRequest(BaseModel):
    selected_preset: str | None = None


@app.get("/api/session-cache")
async def get_session_cache():
    """Return the persisted UI-context cache. Safe to call before login."""
    return {"success": True, "cache": _load_session_cache()}


@app.post("/api/session-cache")
async def update_session_cache(req: SessionCacheUpdateRequest):
    """Persist a small whitelist of UI hints across server restarts.

    Auth and game state are NOT touched. Only fields in
    SESSION_CACHE_WRITABLE_KEYS can be written from the client.
    """
    updates = {}
    if req.selected_preset is not None:
        updates["selected_preset"] = req.selected_preset
    cache = _save_session_cache(updates) if updates else _load_session_cache()
    return {"success": True, "cache": cache}

@app.post("/api/logout")
async def logout():
    global active_client, active_account, active_dashboard_data, active_start_state, active_parent_cards, active_parent_rank_points, raw_load_index_response, pending_game_auth_config, active_selection
    active_client = None
    active_account = None
    active_dashboard_data = None
    active_start_state = {}
    active_parent_cards = {}
    active_parent_rank_points = {}
    raw_load_index_response = None
    pending_game_auth_config = {}
    active_selection = {
        "deck": None,
        "friend": None,
        "trainee": None,
        "veterans": []
    }
    return {"success": True}

@app.post("/api/career/start")
async def start_career(req: StartCareerRequest):
    try:
        started = start_career_from_request(req)
        if not started.get("success"):
            return started
        account, chara_info = apply_career_result(started["result"])
        return {"success": True, "account": account, "chara_info": chara_info}
    except Exception as e:
        return {"success": False, "detail": str(e)}

backend_loop_thread = None
backend_loop_stop = False

def manage_career_loop(req, preset, initial_result):
    global backend_loop_stop, active_account, active_client
    max_steps = max(1, min(int(req.max_steps or 2500), 3000))
    consecutive_fails = 0
    current_result = initial_result
    
    while not backend_loop_stop:
        career_runner.start(active_client, preset, current_result, max_steps, burn_clocks=req.burn_clocks, dev_mode=req.dev_mode)
        
        while career_runner.snapshot().get("running"):
            if backend_loop_stop:
                career_runner.stop()
                return
            dna_sleep(1.0, 1.0)
            
        status = career_runner.snapshot()
        if status.get("last_error"):
            consecutive_fails += 1
            if consecutive_fails >= 3:
                break
        else:
            consecutive_fails = 0
            if active_account and "career" in active_account and active_account["career"]:
                active_account["career"]["active"] = False
            
        if not req.dev_mode:
            break
            
        for _ in range(6):
            if backend_loop_stop:
                return
            dna_sleep(1.0, 1.0)
            
        started_ok = False
        while not started_ok and not backend_loop_stop:
            try:
                started = start_career_from_request(req)
                if not started.get("success"):
                    consecutive_fails += 1
                    if consecutive_fails >= 5:
                        break
                    for _ in range(15):
                        if backend_loop_stop:
                            return
                        dna_sleep(1.0, 1.0)
                    continue
                current_result = started["result"]
                account, chara_info = apply_career_result(current_result)
                active_account = account
                started_ok = True
                consecutive_fails = 0
            except Exception as e:
                consecutive_fails += 1
                if consecutive_fails >= 5:
                    break
                for _ in range(15):
                    if backend_loop_stop:
                        return
                    dna_sleep(1.0, 1.0)

        if not started_ok:
            break

@app.post("/api/career/run")
async def run_career(req: RunCareerRequest):
    global active_account, backend_loop_thread
    if career_runner.snapshot().get("running") or (backend_loop_thread and backend_loop_thread.is_alive()):
        return {"success": False, "detail": "Career runner loop already active"}
    preset_name = req.preset_name or "xguri parent"
    preset = preset_store.read_one(preset_name)
    if not preset:
        return {"success": False, "detail": f"{preset_name} preset missing"}
    
    try:
        account = active_account or {}
        career = account.get("career") or {}
        if career.get("active"):
            index_result = refresh_index_state(active_client)
            load_data = index_result.get('data', {})
            update_start_state(load_data)

            account = get_account_status(load_data)
            active_account = account
            career = account.get("career") or {}

        if career.get("active"):
            career_result = active_client.load_career()
            career_data = career_result.get('data', {})
            
            account = get_account_status(load_data, career_result)
            active_account = account
            
            career_status = account.get("career")
            req.card_id = int(career_status.get("card_id"))
            req.support_card_ids = career_status.get("support_card_ids")
            req.friend_viewer_id = int(career_status.get("friend_viewer_id"))
            req.friend_card_id = int(career_status.get("friend_card_id"))
            req.parent_id_1 = int(career_status.get("parent_id_1"))
            req.parent_id_2 = int(career_status.get("parent_id_2"))
            req.deck_id = int(career_status.get("deck_id"))
            req.scenario_id = int(career_status.get("scenario_id") or preset.get("scenario_id", 4))
            
            chara_info = career_data.get('chara_info') or {}
            if active_dashboard_data:
                active_dashboard_data["account"] = account
            result = career_result
        else:
            if not req.scenario_id:
                req.scenario_id = int(preset.get("scenario_id", 4))
            # Auto-fill team picks from preset (e.g. when imported from uma.moe)
            # unless the UI already specified them.
            if not req.card_id and preset.get("trainee_card_id"):
                req.card_id = int(preset["trainee_card_id"])
            if not req.support_card_ids and preset.get("support_card_ids"):
                req.support_card_ids = [int(c) for c in preset["support_card_ids"]]
            if not req.friend_card_id and preset.get("friend_card_id"):
                req.friend_card_id = int(preset["friend_card_id"])
            if not req.friend_viewer_id and preset.get("friend_viewer_id"):
                req.friend_viewer_id = int(preset["friend_viewer_id"])
            if not req.parent_id_1 and preset.get("parent_id_1"):
                req.parent_id_1 = int(preset["parent_id_1"])
            if not req.parent_id_2 and preset.get("parent_id_2"):
                req.parent_id_2 = int(preset["parent_id_2"])
            if not req.rental_viewer_id and not req.rental_chara_id:
                preset_rvid = preset.get("rental_chara_viewer_id")
                preset_rcid = preset.get("rental_chara_id")
                if preset_rvid and preset_rcid:
                    req.rental_viewer_id = int(preset_rvid)
                    req.rental_chara_id = int(preset_rcid)
            started = start_career_from_request(req)
            if not started.get("success"):
                return started
            result = started["result"]
            account, chara_info = apply_career_result(result)

        preset = dict(preset)
        apply_deck_type_counts(preset, req=req, chara_info=chara_info)
        preset, runtime_advisor = prepare_runtime_preset_for_run(preset, req, chara_info)
        
        if req.dev_mode:
            backend_loop_stop = False
            backend_loop_thread = threading.Thread(target=manage_career_loop, args=(req, preset, result), daemon=True)
            backend_loop_thread.start()
            dna_sleep(0.5, 0.5)
        else:
            career_runner.start(active_client, preset, result, max(1, min(int(req.max_steps or 2500), 3000)), burn_clocks=req.burn_clocks, dev_mode=req.dev_mode)
            
        return {
            "success": True,
            "account": account,
            "chara_info": chara_info,
            "runner": career_runner.snapshot(),
            "runtime_advisor": runtime_advisor,
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}

@app.get("/api/career/runner")
async def career_runner_status():
    return {"success": True, "runner": career_runner.snapshot()}

@app.post("/api/career/runner/stop")
async def stop_career_runner():
    global backend_loop_stop
    backend_loop_stop = True
    career_runner.stop()
    return {"success": True, "runner": career_runner.snapshot()}

class BurnClocksRequest(BaseModel):
    burn_clocks: bool

@app.post("/api/career/runner/burn_clocks")
async def set_burn_clocks(req: BurnClocksRequest):
    career_runner.set_burn_clocks(req.burn_clocks)
    return {"success": True, "runner": career_runner.snapshot()}

@app.post("/api/career/friends")
async def get_friend_list(req: FriendListRequest):
    global active_client, active_dashboard_data, active_account
    if not active_client:
        return {"success": False, "detail": "Not logged in"}

    if active_account and active_account.get("career") and active_account["career"].get("active"):
        return {
            "success": True,
            "friends": [],
            "exclude_viewer_ids": [],
            "source": "Active Career (Skip)"
        }

    if (
        not req.exclude_viewer_ids
        and not req.force_refresh
        and active_dashboard_data is not None
        and "friends" in active_dashboard_data
    ):
        return {
            "success": True,
            "friends": active_dashboard_data["friends"],
            "exclude_viewer_ids": active_dashboard_data.get("friendExcludeIds", []),
            "source": "cache",
            "veterans": active_dashboard_data.get("friendVeterans", []),
            "veterans_source": active_dashboard_data.get(
                "friendVeteransSource", "cache"
            ),
        }

    try:
        result = active_client.pre_single_mode(req.exclude_viewer_ids)
        data = result.get('data', {})
        update_start_state(data)
        friends, exclude_viewer_ids, source = normalize_friend_cards(data)
        veterans, veterans_source = normalize_friend_veterans(data)

        if active_dashboard_data is not None:
            active_dashboard_data["friends"] = friends
            active_dashboard_data["friendExcludeIds"] = exclude_viewer_ids
            active_dashboard_data["friendsLoaded"] = True
            active_dashboard_data["friendVeterans"] = veterans
            active_dashboard_data["friendVeteransSource"] = veterans_source
            # Hold on to the raw response (last one) so /api/friends/raw can
            # show it to the developer for field-name discovery.
            active_dashboard_data["lastPreSingleModeRaw"] = data

        return {
            "success": True,
            "friends": friends,
            "exclude_viewer_ids": exclude_viewer_ids,
            "source": source,
            "veterans": veterans,
            "veterans_source": veterans_source,
        }
    except Exception as e:
        if active_dashboard_data is not None and active_dashboard_data.get("friends"):
            return {
                "success": True,
                "friends": active_dashboard_data.get("friends", []),
                "exclude_viewer_ids": active_dashboard_data.get("friendExcludeIds", []),
                "source": "cache-after-refresh-error",
                "warning": str(e),
                "veterans": active_dashboard_data.get("friendVeterans", []),
                "veterans_source": active_dashboard_data.get("friendVeteransSource", "cache"),
            }
        return {"success": False, "detail": str(e)}


@app.get("/api/friends/raw")
async def get_friends_raw():
    """Debug-only: return the most recently captured pre_single_mode response and
    list every top-level / nested key so we can identify the borrowable-veteran
    field shape. Trigger by calling /api/career/friends first."""
    if not active_dashboard_data:
        return {"success": False, "detail": "No active session yet"}
    raw = active_dashboard_data.get("lastPreSingleModeRaw")
    if raw is None:
        return {"success": False, "detail": "Call /api/career/friends first to populate this cache."}

    def shape(value, depth=0, max_depth=3):
        if depth > max_depth:
            return type(value).__name__
        if isinstance(value, dict):
            return {k: shape(v, depth + 1, max_depth) for k, v in value.items()}
        if isinstance(value, list):
            sample = value[0] if value else None
            return {"<list len=>": len(value), "<item shape>": shape(sample, depth + 1, max_depth)}
        return type(value).__name__

    veterans, src = normalize_friend_veterans(raw)
    return {
        "success": True,
        "top_level_keys": sorted(list(raw.keys())),
        "shape": shape(raw, max_depth=2),
        "veterans_found": len(veterans),
        "veterans_source": src,
        "veteran_field_candidates_tried": list(FRIEND_VETERAN_KEYS),
        "raw_sample": {k: raw[k] for k in list(raw.keys())[:6]},  # first 6 keys, full
    }


@app.get("/api/friends/veterans")
async def get_friend_veterans():
    """Return the cached friend-veteran list (call /api/career/friends first)."""
    if not active_dashboard_data:
        return {"success": False, "detail": "No active session yet"}
    veterans = active_dashboard_data.get("friendVeterans") or []
    return {
        "success": True,
        "veterans": veterans,
        "source": active_dashboard_data.get("friendVeteransSource", "unknown"),
    }


@app.get("/api/friends/manage")
async def get_friend_management():
    """Return the cached friend/following data the dashboard can manage."""
    if not active_dashboard_data:
        return {"success": False, "detail": "No active session yet"}
    friends = active_dashboard_data.get("friends") or []
    counts = {}
    for friend in friends:
        key = str(friend.get("friend_state", 0))
        counts[key] = counts.get(key, 0) + 1
    return {
        "success": True,
        "friends": friends,
        "counts": counts,
        "source": active_dashboard_data.get("friendsLoaded") and "cache" or "session",
    }


@app.post("/api/friends/follow")
async def follow_friend(req: FriendManageRequest):
    global active_dashboard_data
    if not active_client:
        return {"success": False, "detail": "Not logged in"}
    try:
        result = active_client.follow_user(req.viewer_id)
        if active_dashboard_data:
            for friend in active_dashboard_data.get("friends", []) or []:
                if int(friend.get("viewer_id") or 0) == int(req.viewer_id):
                    friend["friend_state"] = max(1, int(friend.get("friend_state") or 0))
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/api/friends/unfollow")
async def unfollow_friend(req: FriendManageRequest):
    global active_dashboard_data
    if not active_client:
        return {"success": False, "detail": "Not logged in"}
    try:
        result = active_client.unfollow_user(req.viewer_id)
        if active_dashboard_data:
            for friend in active_dashboard_data.get("friends", []) or []:
                if int(friend.get("viewer_id") or 0) == int(req.viewer_id):
                    friend["friend_state"] = 0
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/api/advisor/recommendations")
async def advisor_recommendations(req: AdvisorRequest):
    if not active_dashboard_data:
        return {"success": False, "detail": "No active session yet"}
    trainee_card_id = int(req.trainee_card_id or 0)
    running_style = int(req.running_style or 0)
    if not trainee_card_id:
        selection = active_selection or {}
        trainee = selection.get("trainee") or {}
        trainee_card_id = int(trainee.get("id") or trainee.get("card_id") or 0)
    if not running_style:
        preset_name = ""
        try:
            preset_name = _load_session_cache().get("selected_preset") or ""
            running_style = int((preset_store.read_one(preset_name) or {}).get("running_style") or 0)
        except Exception:
            running_style = 0
    candidates = advisor.recommend_parent_pool(
        active_dashboard_data.get("parents") or [],
        active_dashboard_data.get("friendVeterans") or [],
        trainee_card_id=trainee_card_id,
        running_style=running_style,
    )
    return {
        "success": True,
        "trainee_card_id": trainee_card_id,
        "running_style": running_style,
        "recommendations": candidates[:24],
    }


@app.post("/api/career/action")
async def career_action(req: CareerActionRequest):
    global active_client, active_account
    if not active_client:
        return {"success": False, "detail": "Not logged in"}
    
    try:
        result = active_client.exec_command(
            command_type=req.command_type,
            command_id=req.command_id,
            current_turn=req.current_turn,
            current_vital=req.current_vital,
            command_group_id=req.command_group_id,
            select_id=req.select_id
        )
        
        data = result.get('data', {})
        return {
            "success": True,
            "chara_info": data.get('chara_info', {}),
            "command_result": data.get('command_result', {})
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}

@app.post("/api/career/delete")
async def delete_career(req: DeleteCareerRequest):
    global active_client, active_account, active_dashboard_data, backend_loop_thread
    if not active_client:
        return {"success": False, "detail": "Not logged in"}
    if career_runner.snapshot().get("running") or (backend_loop_thread and backend_loop_thread.is_alive()):
        return {"success": False, "detail": "Cannot delete career while runner is active"}

    try:
        account = active_account or {}
        career = account.get("career") or {}
        if not career.get("active"):
            load_result = refresh_index_state(active_client)
            load_data = load_result.get('data', {})
            update_start_state(load_data)
            account = get_account_status(load_data)
            active_account = account
            career = account.get("career") or {}
        current_turn = req.current_turn or career.get("turn", 0) or 1
        if not career.get("active") and not req.current_turn:
            return {"success": False, "detail": "No active career"}
        active_client.finish_career(current_turn=current_turn, is_force_delete=True)
        account["career"] = None
        active_account = account
        if active_dashboard_data:
            active_dashboard_data["account"] = account
        return {"success": True, "account": account}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/api/career/finish")
async def finish_career_endpoint(req: FinishCareerRequest):
    """Natural-finish the active career: spend leftover SP on skills (per
    preset rules), drain any pending end-of-run events, then call
    single_mode_free/finish with is_force_delete=False so the trained
    character is saved.

    This mirrors `CareerRunner._run`'s `decision.action == "finish"` path
    so users can wrap up a career from the dashboard without logging into
    the game client themselves.

    Title selection is server-driven (awarded automatically based on the
    run's results) so there is no separate "pick title" API to call.
    """
    global active_client, active_account, active_dashboard_data, backend_loop_thread
    if not active_client:
        return {"success": False, "detail": "Not logged in"}
    if career_runner.snapshot().get("running") or (backend_loop_thread and backend_loop_thread.is_alive()):
        return {"success": False, "detail": "Cannot finish career while runner is active"}

    try:
        account = active_account or {}
        career = account.get("career") or {}
        if not career.get("active"):
            load_result = refresh_index_state(active_client)
            load_data = load_result.get('data', {})
            update_start_state(load_data)
            account = get_account_status(load_data)
            active_account = account
            career = account.get("career") or {}
        if not career.get("active"):
            return {"success": False, "detail": "No active career"}

        career_state = active_client.load_career()
        career_data = career_state.get("data") or {}
        chara_info = career_data.get("chara_info") or {}
        current_turn = (
            req.current_turn
            or int(chara_info.get("turn") or 0)
            or int(career.get("turn") or 0)
            or 1
        )
        sp_before = int(chara_info.get("skill_point") or 0)

        preset_name = req.preset_name or _load_session_cache().get("selected_preset") or ""
        preset = preset_store.read_one(preset_name) if preset_name else None
        if not preset:
            preset = {"scenario_id": int(career.get("scenario_id") or 4)}

        from career_bot.scenarios.mant import MantStrategy
        from career_bot.races import RacePlanner

        race_planner = RacePlanner(base_dir)
        strategy = MantStrategy(race_planner)
        skill_buyer = career_runner.skill_buyer

        skills_bought_total = 0
        if req.buy_skills:
            career_state, bought = skill_buyer.buy(active_client, career_state, preset, force=True)
            skills_bought_total += int(bought or 0)

        career_data = career_state.get("data") or {}
        if career_data.get("race_start_info"):
            try:
                career_state = active_client.race_out(current_turn=current_turn)
            except Exception as e:
                if not any(err in str(e) for err in ("102", "201", "StateRecoveryError")):
                    raise

        career_state = career_runner._drain_events(active_client, strategy, career_state, limit=50)
        career_data = career_state.get("data") or {}
        chara_info = career_data.get("chara_info") or {}

        if req.buy_skills and int(chara_info.get("skill_point") or 0) > 200:
            career_state, bought2 = skill_buyer.buy(active_client, career_state, preset, force=True)
            skills_bought_total += int(bought2 or 0)
            career_data = career_state.get("data") or {}
            chara_info = career_data.get("chara_info") or {}

        try:
            active_client.finish_career(current_turn=current_turn, is_force_delete=False)
        except Exception as e:
            if not any(err in str(e) for err in ("102", "201", "StateRecoveryError")):
                raise

        try:
            load_result = refresh_index_state(active_client)
            load_data = load_result.get("data", {})
            update_start_state(load_data)
            account = get_account_status(load_data)
            active_account = account
            if active_dashboard_data:
                active_dashboard_data["account"] = account
        except Exception:
            account["career"] = None
            active_account = account
            if active_dashboard_data:
                active_dashboard_data["account"] = account

        sp_after = int(chara_info.get("skill_point") or 0)
        return {
            "success": True,
            "account": active_account,
            "skills_bought": skills_bought_total,
            "sp_before": sp_before,
            "sp_after": sp_after,
            "preset_name": preset_name,
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.get("/api/debug/start_state")
async def get_start_state():
    return active_start_state

@app.get("/api/debug/raw_load")
async def get_raw_load():
    return {"error": "raw load/index response storage disabled"}

@app.get("/api/images/{image_name}")
async def get_image(image_name: str):
    name_no_ext = image_name.split('?')[0].replace('.png', '')
    
    exact_path = images_dir / f"{name_no_ext}.png"
    if exact_path.exists():
        return FileResponse(exact_path, media_type="image/png", headers={"Cache-Control": "no-cache"})
    
    for fallback_id in ['100101', '10010', '10000', '10001']:
        fb_path = images_dir / f"{fallback_id}.png"
        if fb_path.exists():
            return FileResponse(fb_path, media_type="image/png", headers={"Cache-Control": "no-cache"})
    
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/styles.css")
async def styles_css():
    path = base_dir / "public" / "styles.css"
    if path.exists():
        return FileResponse(path, media_type="text/css", headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="styles.css not found")

@app.get("/app.js")
async def app_js():
    path = base_dir / "public" / "app.js"
    if path.exists():
        return FileResponse(path, media_type="application/javascript", headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="app.js not found")


@app.get("/sweep.png")
async def sweep_png():
    path = base_dir / "public" / "sweep.png"
    if path.exists():
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="sweep.png not found")

@app.get("/broom.png")
async def broom_png():
    path = base_dir / "public" / "broom.png"
    if path.exists():
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="broom.png not found")

@app.get("/assets/data/{file_name}")
async def get_asset_data(file_name: str):
    path = base_dir / 'public' / 'assets' / 'data' / file_name
    if path.exists():
        return FileResponse(path, headers={"Cache-Control": "no-cache"})
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/races/{file_name}")
async def get_race_image(file_name: str):
    path = base_dir / "public" / "races" / file_name
    if path.exists():
        return FileResponse(path, headers={"Cache-Control": "max-age=31536000"})
    raise HTTPException(status_code=404, detail="Race image not found")

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = base_dir / "public" / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html", headers={"Cache-Control": "no-cache"})
    return "index.html not found"

def set_console_topmost():
    if os.name != 'nt':
        return
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
    except Exception:
        pass

def kill_process_by_name(name):
    if os.name != 'nt':
        return
    try:
        subprocess.run(['taskkill', '/IM', name, '/F'], capture_output=True, text=True, timeout=10)
    except Exception:
        pass

def kill_listeners_on_port(port):
    if os.name != 'nt':
        return
    try:
        proc = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5
        )
    except Exception:
        return

    current_pid = os.getpid()
    pids = set()
    marker = f':{port}'
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local_addr = parts[1]
        state = parts[3].upper() if len(parts) >= 5 else ''
        pid_text = parts[-1]
        if marker not in local_addr or state != 'LISTENING':
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if pid and pid != current_pid:
            pids.add(pid)

    if not pids:
        return
    print(f"Port {port} already in use; killing listener PID(s): {', '.join(map(str, sorted(pids)))}", flush=True)
    for pid in sorted(pids):
        try:
            subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True, text=True, timeout=5)
        except Exception:
            pass
    dna_sleep(0.5, 0.5)

def has_fresh_auth_config(cfg):
    app_ver = str(cfg.get('app_ver') or '').strip()
    res_ver = str(cfg.get('res_ver') or '').strip()
    if not app_ver or not res_ver:
        return False
    if int(cfg.get('auth_key_len') or 0) != 48:
        return False
    viewer_id = cfg.get('viewer_id')
    udid = str(cfg.get('udid') or '').strip()
    auth_key = str(cfg.get('auth_key') or '').strip().lower()
    if not viewer_id or not udid or not auth_key:
        return False
    if not re.fullmatch(r'[0-9a-f]+', auth_key):
        return False
    if len(auth_key) < 32 or len(auth_key) % 2:
        return False
    if len(udid) != 36 or udid.count('-') != 4:
        return False
    return True

def launch_game():
    if os.name != 'nt':
        print('Auth refresh needs Windows Steam launch.')
        return False
    try:
        os.startfile(f'steam://rungameid/{APP_ID}')
        return True
    except Exception as e:
        print(f'Failed to launch Umamusume through Steam: {e}')
        return False

def refresh_auth_before_serving(timeout_sec=None):
    global pending_game_auth_config
    timeout_sec = timeout_sec or int(os.environ.get('SWEEPY_AUTH_CAPTURE_TIMEOUT_SEC', '180'))
    started_at = time.time()
    deadline = started_at + timeout_sec

    print('[NEED TO CAPTURE AUTH]', flush=True)
    if not launch_game():
        return False
    
    print(f'Waiting up to {timeout_sec}s for user to enter game menu', flush=True)

    session = None
    captured_data = {}
    done = {'ok': False}

    def on_message(message, data):
        if message.get('type') == 'error':
            print(f"Frida Error: {message.get('description')}", flush=True)
            return
        payload = message.get('payload') or {}
        if payload.get('type') == 'creds':
            if payload.get('app_ver') and payload.get('res_ver'):
                try:
                    from uma_api.client import unpack
                    wire = unpack(payload.get('body') or '', payload.get('udid') or '')
                    for key in (
                        'viewer_id',
                        'device_id',
                        'device_name',
                        'graphics_device_name',
                        'ip_address',
                        'platform_os_version',
                        'locale',
                        'steam_id',
                        'steam_session_ticket',
                    ):
                        if wire.get(key) is not None:
                            payload[key] = wire.get(key)
                except Exception:
                    pass
                captured_data.update(payload)
                done['ok'] = True

    while time.time() < deadline:
        try:
            session = frida.attach(PROCESS_NAME)
            break
        except Exception:
            dna_sleep(1.0, 1.0)
    
    if not session:
        print(f'Error: {PROCESS_NAME} not found within timeout.', flush=True)
        return False

    try:
        script = session.create_script(JS_CODE)
        script.on('message', on_message)
        script.load()

        while time.time() < deadline:
            if done['ok']:
                if has_fresh_auth_config(captured_data):
                    pending_game_auth_config = dict(captured_data)
                    dna_sleep(2.0, 4.0)
                    kill_process_by_name(PROCESS_NAME)
                    return True
            dna_sleep(0.5, 0.5)
    except Exception as e:
        print(f'Frida injection failed: {e}', flush=True)
    finally:
        if session:
            try:
                session.detach()
            except Exception:
                pass

    print('Auth refresh failed: no fresh credentials captured before timeout.', flush=True)
    return False


if __name__ == "__main__":
    import uvicorn

    try:
        subprocess.run(["git", "pull"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    set_console_topmost()
    kill_listeners_on_port(1616)
    if not refresh_auth_before_serving():
        raise SystemExit(1)
    print("Access the Web UI at: http://127.0.0.1:1616", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=1616, log_level="error")
