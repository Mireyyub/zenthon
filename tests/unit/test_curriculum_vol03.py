"""Volume 03 Logic curriculum presence and teach."""

from curriculum.volume import list_volumes, load_volume
from curriculum.loader import load_lesson, list_lessons


def test_vol03_listed():
    vols = list_volumes()
    assert any(v.startswith("03") or v == "03" for v in vols) or "03_logic" in str(vols)
    # load by id
    meta = load_volume("03")
    assert meta.get("volume") == "03" or "Logic" in str(meta.get("title"))
    lessons = meta.get("lessons") or []
    assert "000009" in lessons
    assert "000010" in lessons
    assert "000011" in lessons


def test_load_identity_lesson():
    data = load_lesson("000009", volume_id="03")
    assert data.get("name") or data.get("definition")
    assert data.get("questions") or data.get("logical_rules") or data.get("definition")


def test_list_includes_logic_lessons():
    ids = list_lessons("03")
    assert "000009" in ids
