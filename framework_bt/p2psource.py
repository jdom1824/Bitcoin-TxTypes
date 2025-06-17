"""
P2PSource  –  Bitcoin Core-style block retrieval
────────────────────────────────────────────────
• Gets block hash by height via mempool.space
• Tries up to N P2P peers **in parallel** (8 workers)
• Saves responding peers to GOOD_FILE
• If none work → fallback to /block/<hash>/raw HTTP download
"""

from __future__ import annotations
import concurrent.futures as cf
import ipaddress, itertools, json, os, random, socket, struct, time
from hashlib import sha256
from pathlib import Path
from typing import Iterator, Optional

import requests
from tqdm import tqdm

# ── Constants ───────────────────────────────────────────────────
MAGIC      = b"\xf9\xbe\xb4\xd9"
PORT       = 8333
UA         = b"/framework-bt-p2p:0.1/"
SOCK_TO    = 20
WORKERS    = 8  # simultaneous connections
FALLBACK   = "https://mempool.space/api/block/{}/raw"
GOOD_FILE  = Path.home() / ".framework_bt_goodpeers.json"
DNS_SEEDS  = [
    "seed.bitcoin.sipa.be", "dnsseed.bluematt.me",
    "dnsseed.bitcoin.dashjr.org", "seed.bitcoinstats.com",
    "seed.bitcoin.jonasschnelli.ch", "seed.btc.petertodd.org",
    "seed.bitcoin.sprovoost.nl", "dnsseed.emzy.de",
]

# ── Quick utilities ─────────────────────────────────────────────
dsha256 = lambda b: sha256(sha256(b).digest()).digest()
be2le   = lambda h: bytes.fromhex(h)[::-1]

def _var_str(b: bytes) -> bytes:
    return struct.pack("<B", len(b)) + b

def _pack(cmd: bytes, payload=b""):
    return MAGIC + cmd.ljust(12, b"\0") + struct.pack("<I", len(payload)) + dsha256(payload)[:4] + payload

def _read(sock, n):
    d = b""
    while len(d) < n:
        p = sock.recv(n - len(d))
        if not p:
            raise ConnectionError("EOF")
        d += p
    return d

def _read_msg(sock):
    h = _read(sock, 24)
    if h[:4] != MAGIC:
        raise ValueError("Bad magic bytes")
    ln = struct.unpack("<I", h[16:20])[0]
    _read(sock, 4)
    return h[4:16].rstrip(b"\0"), _read(sock, ln)

def _handshake(sock):
    v = struct.pack("<iQQ", 70016, 0, int(time.time()))
    v += b"\0" * 26 + b"\0" * 26 + os.urandom(8) + _var_str(UA) + struct.pack("<i?", 0, False)
    sock.sendall(_pack(b"version", v))
    got_v = got_a = False
    while not (got_v and got_a):
        cmd, _ = _read_msg(sock)
        if cmd == b"version":
            got_v = True
            sock.sendall(_pack(b"verack"))
        elif cmd == b"verack":
            got_a = True

# ── Peer management ─────────────────────────────────────────────
def _good_load() -> list[str]:
    try:
        return json.loads(GOOD_FILE.read_text()) if GOOD_FILE.exists() else []
    except:
        return []

def _good_save(ip: str):
    good = _good_load()
    if ip not in good:
        good.append(ip)
        try:
            GOOD_FILE.write_text(json.dumps(good[-500:]))
        except:
            pass

def _ips_dns(max_ips=300) -> list[str]:
    out = []
    for host in random.sample(DNS_SEEDS, len(DNS_SEEDS)):
        try:
            for res in socket.getaddrinfo(host, 8333, socket.AF_INET):
                ip = res[4][0]
                if ip not in out:
                    out.append(ip)
                    if len(out) >= max_ips:
                        return out
        except socket.gaierror:
            pass
    return out

def _ips_bitnodes(max_ips=150) -> list[str]:
    try:
        j = requests.get("https://bitnodes.io/api/v1/snapshots/latest/", timeout=10).json()
    except:
        return []
    ips = [ip.split(":")[0] for ip in j["nodes"] if "." in ip]
    random.shuffle(ips)
    good = []
    for ip in ips:
        try:
            ipaddress.IPv4Address(ip)
            good.append(ip)
            if len(good) >= max_ips:
                break
        except ipaddress.AddressValueError:
            pass
    return good

def _peer_pool() -> list[str]:
    pool = _good_load() + _ips_dns() + _ips_bitnodes()
    random.shuffle(pool)
    return list(dict.fromkeys(pool))

# ── P2P download (concurrent) ───────────────────────────────────
def _fetch_from_peer(peer: str, block_hash: str, timeout: int = SOCK_TO) -> bytes | None:
    try:
        with socket.create_connection((peer, PORT), timeout=timeout) as s:
            _handshake(s)
            inv = struct.pack("<I", 1) + b"\x02\x00\x00\x00" + be2le(block_hash)
            s.sendall(_pack(b"getdata", inv))
            cmd, payload = _read_msg(s)
            if cmd == b"block":
                _good_save(peer)
                return payload
    except Exception:
        return None

def _download_p2p(block_hash: str, peers: list[str], max_peers: int) -> bytes:
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        fut_to_ip = {
            ex.submit(_fetch_from_peer, ip, block_hash): ip
            for ip in peers[:max_peers]
        }
        for fut in cf.as_completed(fut_to_ip):
            data = fut.result()
            if data:
                return data
    raise RuntimeError("All peers failed.")

# ── HTTP fallback ───────────────────────────────────────────────
def _download_http(block_hash: str) -> bytes:
    print(f"[•] Fallback HTTP {block_hash}")
    r = requests.get(FALLBACK.format(block_hash), timeout=30)
    r.raise_for_status()
    return r.content

# ── Get block hash by height ────────────────────────────────────
def _hash_by_height(h: int) -> str:
    r = requests.get(f"https://mempool.space/api/block-height/{h}", timeout=10)
    r.raise_for_status()
    return r.text.strip()

# ── Iterable block source ───────────────────────────────────────
class P2PSource:
    def __init__(self, start_height: int, end_height: int,
                 peer_ip: Optional[str] = None, max_peers: int = 40):
        self.start, self.end = start_height, end_height
        self.max_peers = max(20, max_peers)
        self.fixed = peer_ip

    def __iter__(self) -> Iterator[dict]:
        pool = _peer_pool()
        if self.fixed:
            pool.insert(0, self.fixed)

        for h in range(self.start, self.end + 1):
            block_hash = _hash_by_height(h)
            print(f"[•] Height {h} → {block_hash[:12]}…  (trying peers)")
            try:
                raw = _download_p2p(block_hash, pool, self.max_peers)
            except Exception:
                raw = _download_http(block_hash)
            yield {"height": h, "hash": block_hash, "raw": raw}
