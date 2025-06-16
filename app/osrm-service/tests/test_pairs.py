import os
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.services.logistics_service import _pairs


def test_pairs_complete():
    ids = [str(uuid4()) for _ in range(3)]
    matrix = [
        [0.0, 1.0, 2.0],
        [3.0, 0.0, 4.0],
        [5.0, 6.0, 0.0],
    ]
    result = _pairs(ids, matrix)
    assert len(result) == 6
    expected = {
        (ids[0], ids[1], 1.0),
        (ids[0], ids[2], 2.0),
        (ids[1], ids[0], 3.0),
        (ids[1], ids[2], 4.0),
        (ids[2], ids[0], 5.0),
        (ids[2], ids[1], 6.0),
    }
    assert set(result) == expected
