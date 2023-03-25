# src/tessif/identify/auxilliary.py
# pylint: disable=trailing-whitespace
# pylint error disabled since the dataframe doctest results require those
"""Tessif module providing aux. resullt differences identification tools."""
from numpy import mean as numpy_mean


def flatten_multiindex_flow_data(midx_df):
    """Flatten multiindexed results to each flow beeing a singular column.

    Parameters
    ----------
    midx_df: pandas.DataFrame
        Multiindexed dataframe to be flattened.

        Design case, the top-level index represents the individual components,
        while the second-level index represent the respective outflow targets.

        Meaning for an energy system like::

            A -> B -> C
                 |
                 v
                 D

        The dataframe would look something like::

                A  B
                B  C  D
            0  10  8  2
            1   0  0  0
            2  20  2 18

        Usually returned by something like
        :attr:`tessif.analyze.ComparativeResultier.all_loads`.

    Returns
    -------
    pandas.DataFrame
        Flattened, singular indexed column data frame.

    Example
    -------
    Picking up on the example flows from above:

    >>> import pandas as pd
    >>> data = [
    ...     [10, 8, 2, ],
    ...     [0, 0, 0, ],
    ...     [20, 2, 18],
    ... ]
    >>> mindex_df = pd.DataFrame(
    ...     data=data,
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original multiindexed dataframe:

    >>> print(mindex_df)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    Flattened dataframe:

    >>> print(flatten_multiindex_flow_data(mindex_df))
                         A to B  B to C  B to D
    2019-01-01 00:00:00      10       8       2
    2019-01-01 01:00:00       0       0       0
    2019-01-01 02:00:00      20       2      18
    """

    flattened_data = midx_df.copy()

    flattened_data.columns = [
        ' to '.join(col) for col in midx_df.columns]

    return flattened_data


def list_mutually_inclusive_columns(dataframes):
    """ Identify columns present in all dataframes.

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of singular column indexed dataframes of which the
        mutually inclusive columns are identified

    Returns
    -------
    list
        List of column indices.

    Example
    -------
    >>> import pandas as pd
    >>> data = [
    ...     [10, 8, 2, ],
    ...     [0, 0, 0, ],
    ...     [20, 2, 18],
    ... ]
    >>> df1 = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "C", "D"],
    ... )
    >>> df2 = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "D", "E"],
    ... )

    >>> print(list_mutually_inclusive_columns([df1, df2]))
    ['A', 'D']
    """
    common_cols = set.intersection(
        *(set(cols) for cols in dataframes)
    )
    common_cols = list(sorted(common_cols))
    return common_cols


def list_not_mutually_inclusive_columns(dataframes):
    """ Identify columns not present in all dataframes.

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of singular column indexed dataframes of which the not
        mutually inclusive columns are identified

    Returns
    -------
    list
        List of column indices.

    Example
    -------
    >>> import pandas as pd
    >>> data = [
    ...     [10, 8, 2, ],
    ...     [0, 0, 0, ],
    ...     [20, 2, 18],
    ... ]
    >>> df1 = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "C", "D"],
    ... )
    >>> df2 = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "D", "E"],
    ... )

    >>> print(list_not_mutually_inclusive_columns([df1, df2]))
    ['C', 'E']
    """
    all_cols = set()
    for dtf in dataframes:
        for col in dtf.columns:
            all_cols.add(col)

    common_cols = set(list_mutually_inclusive_columns(dataframes))
    return list(sorted(all_cols - common_cols))


def filter_mutually_inclusive_columns(dataframes):
    """Filter a set of dataframes to only include mutually inclusive columns.

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of singular column indexed dataframes of which the
        mutually inclusive columns are identified and kept, while the
        others are dropped.

    Returns
    -------
    list
        List of dataframes only containing mutually inclusive columns.

    Example
    -------
    >>> import pandas as pd
    >>> data = [
    ...     [10, 8, 2, ],
    ...     [0, 0, 0, ],
    ...     [20, 2, 18],
    ... ]
    >>> df1 = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "C", "D"],
    ... )
    >>> df2 = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "D", "E"],
    ... )
    >>> filtered_dfs = filter_mutually_inclusive_columns([df1, df2])

    Filtered df1:

    >>> print(filtered_dfs[0])
        A   D
    0  10   2
    1   0   0
    2  20  18


    Filtered df2:

    >>> print(filtered_dfs[1])
        A  D
    0  10  8
    1   0  0
    2  20  2
    """

    common_cols = list_mutually_inclusive_columns(dataframes)
    filtered_dfs = []
    for dtf in dataframes:
        filtered_dfs.append(dtf[common_cols])

    return filtered_dfs


def drop_all_zero_columns(dataframe):
    """Drop all columns only filled with zeroes (0).

    Parameters
    ----------
    dataframe: pandas.DataFrame
        data frame of which the all zero columns are dropped.

    Returns
    -------
    pandas.DataFrame
        data frame not containing all zero columns

    Example
    -------
    >>> import pandas as pd
    >>> data = [
    ...     [10, 8, 0, ],
    ...     [0, 0, 0, ],
    ...     [20, 2, 0],
    ... ]
    >>> df = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "C", "D"],
    ... )

    >>> print(drop_all_zero_columns(df))
        A  C
    0  10  8
    1   0  0
    2  20  2
    """
    cdf = dataframe.loc[:, (dataframe != 0).any(axis="index")]
    return cdf


def drop_all_zero_rows(dataframe):
    """Drop all rows only filled with zeroes (0).

    Parameters
    ----------
    dataframe: pandas.DataFrame
        data frame of which the all-zero rows are dropped.

    Returns
    -------
    pandas.DataFrame
        data frame not containing all-zero rows

    Example
    -------
    >>> import pandas as pd
    >>> data = [
    ...     [10, 8, 0, ],
    ...     [0, 0, 0, ],
    ...     [20, 2, 0],
    ... ]
    >>> df = pd.DataFrame(
    ...     data=data,
    ...     columns=["A", "C", "D"],
    ... )

    >>> print(drop_all_zero_rows(df))
        A  C  D
    0  10  8  0
    2  20  2  0
    """
    cdf = dataframe.loc[(dataframe != 0).any(axis="columns")]
    return cdf


def parse_reference_df(dataframe, reference=None):
    """Parse dataframe averages."""
    # parse reference
    if reference is None:
        ref = numpy_mean(dataframe, axis="columns")
    else:
        ref = dataframe[reference]

    return ref
