import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

type Recorded = Callable[[str], Any]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def recorded() -> Recorded:
    """Loader for recorded iTunes API responses in tests/unit/fixtures."""

    def load(name: str) -> Any:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    return load
