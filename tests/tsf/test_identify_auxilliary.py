import pandas as pd

from tessif import identify
from tessif.identify import auxilliary


def test_flatten_multiindex_flow_data():
    """Test correct flattening."""
    import pandas as pd

    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]
    mindex_df = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )
    flat_df = pd.DataFrame(
        data=data,
        columns=["A to B", "B to C", "B to D"],
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    flattened_df = auxilliary.flatten_multiindex_flow_data(mindex_df)

    assert flattened_df.equals(flat_df)


def test_list_mutually_inclusive_columns():
    """Test correct column detecction."""
    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]

    df1 = pd.DataFrame(
        data=data,
        columns=["A", "C", "D"],
    )
    df2 = pd.DataFrame(
        data=data,
        columns=["A", "D", "E"],
    )

    mutual_cols = auxilliary.list_mutually_inclusive_columns([df1, df2])

    assert mutual_cols == ["A", "D"]


def test_list_multiindex_mutually_inclusive_columns():
    """Test correct filtering on multiindex df."""

    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]

    df1 = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )
    df2 = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "E")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    mutual_cols = auxilliary.list_mutually_inclusive_columns([df1, df2])
    assert mutual_cols == [('A', 'B'), ('B', 'C')]


def test_list_not_mutually_inclusive_columns():
    """Test correct column detecction."""
    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]

    df1 = pd.DataFrame(
        data=data,
        columns=["A", "C", "D"],
    )
    df2 = pd.DataFrame(
        data=data,
        columns=["A", "D", "E"],
    )

    no_mutual_cols = auxilliary.list_not_mutually_inclusive_columns([df1, df2])

    assert no_mutual_cols == ["C", "E"]


def test_list_multiindex_not_mutually_inclusive_columns():
    """Test correct filtering on multiindex df."""

    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]

    df1 = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )
    df2 = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "E")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    mutual_cols = auxilliary.list_not_mutually_inclusive_columns([df1, df2])
    assert mutual_cols == [('B', 'D'), ('B', 'E')]


def test_filter_mutually_inclusive_columns():
    """Test correct filtering."""

    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]

    df1 = pd.DataFrame(
        data=data,
        columns=["A", "C", "D"],
    )
    df2 = pd.DataFrame(
        data=data,
        columns=["A", "D", "E"],
    )

    df3 = pd.DataFrame(
        data=[[10, 2], [0, 0], [20, 18]],
        columns=["A", "D"],
    )
    df4 = pd.DataFrame(
        data=[[10, 8], [0, 0], [20, 2]],
        columns=["A", "D"],
    )

    filtered_dfs = auxilliary.filter_mutually_inclusive_columns([df1, df2])

    assert filtered_dfs[0].equals(df3)
    assert filtered_dfs[1].equals(df4)


def test_multiindex_filter_mutually_inclusive_columns():
    """Test correct filtering on multiindex df."""

    data = [
        [10, 8, 2, ],
        [0, 0, 0, ],
        [20, 2, 18],
    ]

    df1 = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )
    df2 = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "D"), ("B", "E")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    df3 = pd.DataFrame(
        data=[[10, 2], [0, 0], [20, 18]],
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    df4 = pd.DataFrame(
        data=[[10, 8], [0, 0], [20, 2]],
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    filtered_dfs = auxilliary.filter_mutually_inclusive_columns([df1, df2])

    assert filtered_dfs[0].equals(df3)
    assert filtered_dfs[1].equals(df4)


def test_drop_all_zero_columns():
    """Test correct column dropping."""

    data = [
        [10, 8, 0, ],
        [0, 0, 0, ],
        [20, 2, 0],
    ]

    df = pd.DataFrame(
        data=data,
        columns=["A", "C", "D"],
    )

    expected_df = pd.DataFrame(
        data=[[10, 8], [0, 0], [20, 2]],
        columns=["A", "C", ],
    )

    dropped_df = auxilliary.drop_all_zero_columns(df)

    assert dropped_df.equals(expected_df)


def test_drop_all_zero_columns_on_multiindex():
    """Test correct filtering on multiindex df."""

    data = [
        [10, 0, 2, ],
        [0, 0, 0, ],
        [20, 0, 18],
    ]

    df = pd.DataFrame(
        data=data,
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "C"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    expected_df = pd.DataFrame(
        data=[[10, 2], [0, 0], [20, 18]],
        columns=pd.MultiIndex.from_tuples(
            [("A", "B"), ("B", "D")]),
        index=pd.date_range('2019-01-01', periods=3, freq='H'),
    )

    dropped_df = auxilliary.drop_all_zero_columns(df)

    assert dropped_df.equals(expected_df)


test_flatten_multiindex_flow_data()
test_list_mutually_inclusive_columns()
test_list_not_mutually_inclusive_columns()
test_filter_mutually_inclusive_columns()
test_drop_all_zero_columns()

test_list_multiindex_mutually_inclusive_columns()
test_list_multiindex_not_mutually_inclusive_columns()
test_multiindex_filter_mutually_inclusive_columns()
test_drop_all_zero_columns_on_multiindex()
