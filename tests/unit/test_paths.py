from pathlib import Path

import pytest

from majordomus.core.util.paths import safe_join


def test_safe_join_allows_path_inside_base(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()

    result = safe_join(base, "child", "file.txt")

    assert str(result).startswith(str(base.resolve()))


def test_safe_join_prevents_escape(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()

    with pytest.raises(ValueError):
        safe_join(base, "..", "escape.txt")
