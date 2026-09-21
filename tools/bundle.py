#!/usr/bin/env python3
"""Read/write the assets inside the single-file bundle (index.html).

The deployed site is one self-contained file: a loading shell plus a
`__bundler/manifest` script holding every asset as
{uuid: {mime, compressed, data(base64)}} — JS/JSX sources, fonts, and photos
alike. Editing the site therefore means patching entries in that manifest,
not editing loose files (there are none; junkenpoy-ui-kits/website has only a
stale dist).

  python3 tools/bundle.py list                    # inventory
  python3 tools/bundle.py get <uuid-prefix> [out] # decode one asset
  python3 tools/bundle.py put <uuid-prefix> <file>  # replace an asset
  python3 tools/bundle.py add <file> [mime]       # add asset, prints new uuid
  python3 tools/bundle.py resource <id> <file>    # add asset AND register it as
                                                  # window.__resources[<id>], which
                                                  # is how components reference photos
"""
import base64
import gzip
import json
import re
import sys
import uuid
import zlib
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"
MANIFEST_RE = re.compile(r'(<script type="__bundler/manifest">)(.*?)(</script>)', re.S)
EXT_RES_RE = re.compile(r'(<script type="__bundler/ext_resources">)(.*?)(</script>)', re.S)


def load():
    src = INDEX.read_text(encoding="utf-8")
    m = MANIFEST_RE.search(src)
    if not m:
        sys.exit("no bundler manifest in index.html")
    return src, m, json.loads(m.group(2))


def decode(entry: dict) -> bytes:
    raw = base64.b64decode(entry["data"])
    if entry.get("compressed"):
        try:
            return gzip.decompress(raw)
        except Exception:
            return zlib.decompress(raw, -15)
    return raw


def encode(data: bytes, compressed: bool) -> str:
    payload = gzip.compress(data) if compressed else data
    return base64.b64encode(payload).decode("ascii")


def resolve(man: dict, prefix: str) -> str:
    hits = [k for k in man if k.startswith(prefix)]
    if len(hits) != 1:
        sys.exit(f"{prefix!r} matched {len(hits)} assets")
    return hits[0]


def save(src: str, m, man: dict) -> None:
    body = json.dumps(man, separators=(",", ":"))
    INDEX.write_text(src[:m.start(2)] + body + src[m.end(2):], encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    src, m, man = load()

    if cmd == "list":
        for k, v in man.items():
            size = len(decode(v))
            print(f"{k}  {v['mime']:26} {size:>9,}B  compressed={v.get('compressed')}")
    elif cmd == "get":
        key = resolve(man, sys.argv[2])
        data = decode(man[key])
        if len(sys.argv) > 3:
            Path(sys.argv[3]).write_bytes(data)
            print(f"wrote {sys.argv[3]} ({len(data):,}B)")
        else:
            sys.stdout.write(data.decode("utf-8", "replace"))
    elif cmd == "put":
        key = resolve(man, sys.argv[2])
        data = Path(sys.argv[3]).read_bytes()
        man[key]["data"] = encode(data, man[key].get("compressed", False))
        save(src, m, man)
        print(f"replaced {key} ({len(data):,}B)")
    elif cmd == "resource":
        res_id, path = sys.argv[2], Path(sys.argv[3])
        mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        m2 = EXT_RES_RE.search(src)
        if not m2:
            sys.exit("no ext_resources block")
        resources = json.loads(m2.group(2))
        existing = next((r for r in resources if r["id"] == res_id), None)
        key = existing["uuid"] if existing else str(uuid.uuid4())
        man[key] = {"mime": mime, "compressed": False,
                    "data": encode(path.read_bytes(), False)}
        if not existing:
            resources.append({"id": res_id, "uuid": key})
        # Write the resources block first, then the manifest, recomputing offsets
        # between edits (both live in the same file and the first write shifts them).
        src2 = src[:m2.start(2)] + json.dumps(resources) + src[m2.end(2):]
        m3 = MANIFEST_RE.search(src2)
        INDEX.write_text(src2[:m3.start(2)] + json.dumps(man, separators=(",", ":"))
                         + src2[m3.end(2):], encoding="utf-8")
        print(f"{res_id} -> {key} ({path.stat().st_size:,}B)")
    elif cmd == "add":
        path = Path(sys.argv[2])
        mime = sys.argv[3] if len(sys.argv) > 3 else "image/jpeg"
        key = str(uuid.uuid4())
        man[key] = {"mime": mime, "compressed": False,
                    "data": encode(path.read_bytes(), False)}
        save(src, m, man)
        print(key)
    else:
        sys.exit(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
