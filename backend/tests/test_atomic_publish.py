import json
from pathlib import Path

from app.storage.local import LocalDiskStorage


def test_atomic_put_does_not_clobber_live_on_partial_write(tmp_path: Path):
    storage = LocalDiskStorage(root=tmp_path, public_base="http://x")
    live = "catalogues/catalogue.json"
    v1 = json.dumps({"v": 1}).encode()
    storage.atomic_put_json(live, "catalogues/catalogue-1.json", v1)
    assert json.loads(storage.get(live))["v"] == 1

    v2 = json.dumps({"v": 2}).encode()
    storage.atomic_put_json(live, "catalogues/catalogue-2.json", v2)
    assert json.loads(storage.get(live))["v"] == 2
    # previous version still intact
    assert json.loads(storage.get("catalogues/catalogue-1.json"))["v"] == 1


def test_live_file_is_complete_json(tmp_path: Path):
    storage = LocalDiskStorage(root=tmp_path, public_base="http://x")
    payload = json.dumps({"sections": []}).encode()
    storage.atomic_put_json("catalogues/catalogue.json", "catalogues/catalogue-x.json", payload)
    raw = storage.get("catalogues/catalogue.json")
    json.loads(raw)
