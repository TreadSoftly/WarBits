from warbits.visual.mapping.normalize import canonical_key


def test_canonical_key_basic():
    a = canonical_key("F-15C")
    b = canonical_key("f15 c")
    assert a.canonical == b.canonical
    assert "f15" in a.tokens
    assert "15" in a.tokens


def test_canonical_key_vehicle_suffixes():
    a = canonical_key("T-80BVM")
    assert "t80bvm" in a.tokens
