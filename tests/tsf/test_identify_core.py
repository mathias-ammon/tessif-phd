from tessif import identify


def test_cluster_design_condition():
    """Test successful clustering on design condition."""
    cases = [
        ([0, 1], "high"),
        ([1, 1],  "medium1"),
        ([0, 0],  "medium2"),
        ([1, 0],  "low"),
    ]

    # first condition = pcc, second condition = nmae
    conditions = {
        "high": ({"oprt": "lt", "thres": 0.7}, {"oprt": "ge", "thres": 0.1}),
        "medium1": ({"oprt": "ge", "thres": 0.7}, {"oprt": "ge", "thres": 0.1}),
        "medium2": ({"oprt": "lt", "thres": 0.7}, {"oprt": "lt", "thres": 0.1}),
        "low": ({"oprt": "ge", "thres": 0.7}, {"oprt": "lt", "thres": 0.1}),
    }
    for case in cases:
        assert identify.cluster(case[0], conditions) == case[1]


def test_cluster_singular_condition():
    """Test successful clustering on singular condition."""
    cases = [
        ((9000,), "Nope",),
        ((9001,), "Its over 9000!"),
        ((42,), "Nope",),
    ]

    conditions = {
        "Its over 9000!": ({"oprt": "gt", "thres": 9000},),
        "Nope": ({"oprt": "le", "thres": 9000},),
    }

    for value, cluster_name in cases:
        assert identify.cluster(value, conditions) == cluster_name


test_cluster_design_condition()
test_cluster_singular_condition()
