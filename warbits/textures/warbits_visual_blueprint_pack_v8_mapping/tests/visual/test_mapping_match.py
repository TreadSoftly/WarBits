from warbits.visual.mapping.match import best_matches


def test_best_matches_token_overlap():
    specs = [
        "F-15C",
        "AIM-9L",
        "T-80BVM",
    ]
    blueprints = [
        "mesh:f15c_formation",
        "mesh:aim9l",
        "mesh:t80bvm_lowpoly",
        "mesh:random",
    ]

    sugg = best_matches(specs, blueprints, top_k=1, min_score=0.3)
    d = {s.spec_id: s.blueprint_id for s in sugg}
    assert d["F-15C"].startswith("mesh:f15c")
    assert d["AIM-9L"].startswith("mesh:aim9l")
    assert d["T-80BVM"].startswith("mesh:t80bvm")
