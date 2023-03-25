# src/tessif/identify/calculate.py
"""Tessif module providing tools for identifying differing timeframes."""

import numpy as np
import pandas as pd


from tessif.identify.auxilliary import parse_reference_df
from tessif.identify.calculate import calc_ardiffs


def significant_differences(
        data,
        method="ardiffs",
        threshold=0.1,
        reference=None,
        neighs=True,
):
    """Identify significant differences between timeseries results.

    Designed to detect significant deviations between software specific
    flow results between the same components.

    Each continous sequence of detected difference is stored as a seperate
    DatFrame.

    Parameters
    ----------
    data: pandas.DataFrame, ~collections.abc.Container
        DataFrame of which each column is assumed to contain one flow result.
        Or container of flow results.

    method: {"ardiffs"}, method, default="ardiffs"
        String specifying wich precoded function to use for calculating
        differences or function that takes ``data`` as
        :class:`pandas.DataFrame` or :class:`pandas.Series` and
        :paramref:`~significant_differences.reference` (as ``reference``) to
        return a dataframe indexed like
        :paramref:`~significant_differences.data`.

    threshold: ~numbers.Number, default=0.1
        Number specifying the threshold on which relative differences are seen
        as "significant". Comparison are made based on
        :paramref:`~significant_differences.reference`

    reference: str, None, default=None
        Specifies which columns of :paramref:`~significant_differences.data`
        are to be used as reference results to calculate actual differences.

        For ``None`` (default), the dataframes' average is used as
        returned by ``numpy.mean(data, axis="columns")``

    Returns
    -------
    list
        List of DataFrames where each DataFrame represent one continues
        sequence of detected differences.

    Examples
    --------

    >>> import pandas as pd
    >>> data=[
    ...     [10, 10, 10],
    ...     [10, 12, 10],
    ...     [10, 10, 10],
    ...     [10, 10, 10],
    ...     [10, 10, 12],
    ... ]

    Simple use case of integer indexed data frames:

    >>> dtf = pd.DataFrame(
    ...     data,
    ...     columns=["software1", "software2", "software3"],
    ... )

    >>> identified_differences = significant_differences(dtf, neighs=False)
    >>> for dtf in identified_differences:
    ...     print(dtf)
    ...     print(59*'-')
       software1  software2  software3
    1  10.666667       12.0  10.666667
    -----------------------------------------------------------
       software1  software2  software3
    4  10.666667  10.666667       12.0
    -----------------------------------------------------------

    Design use case of timeindex indexed dataframes including neighbouring
    averages for creating telling stepplots:

    >>> dtf2 = pd.DataFrame(
    ...     data,
    ...     columns=["software1", "software2", "software3"],
    ...     index=pd.date_range("1990-07-13", periods=5, freq="H"),
    ... )

    >>> identified_differences = significant_differences(dtf2, neighs=True)

    >>> print(identified_differences[0])
                         software1  software2  software3
    1990-07-13 00:00:00  10.000000       10.0  10.000000
    1990-07-13 01:00:00  10.666667       12.0  10.666667
    1990-07-13 02:00:00  10.000000       10.0  10.000000

    >>> from tessif.visualize import component_loads
    >>> axes = component_loads.step(identified_differences[0])
    >>> # axes.figure.show()

    .. image:: ../../_static/images/identify_timeframes_step1.png
      :align: center
      :alt: Step plot image of the first identified timeframes

    Note how the second dataframe of identified differences does not include an
    average on the last index, despite the above's ``neighs=True``. This is due
    to a significant difference beeing detected at the last entry where a
    neighbour is not added.

    >>> print(identified_differences[1])
                         software1  software2  software3
    1990-07-13 03:00:00  10.000000  10.000000       10.0
    1990-07-13 04:00:00  10.666667  10.666667       12.0


    >>> from tessif.visualize import component_loads
    >>> axes = component_loads.step(identified_differences[1])
    >>> # axes.figure.show()

    .. image:: ../../_static/images/identify_timeframes_step2.png
      :align: center
      :alt: Step plot image of the second identified timeframes

    Using "software2" as reference and setting threshold to 30% results
    in no significant differences beeing detected:

    >>> dtf2 = pd.DataFrame(
    ...     data,
    ...     columns=["software1", "software2", "software3"],
    ...     index=pd.date_range("1990-07-13", periods=5, freq="H"),
    ... )

    >>> identified_differences = significant_differences(
    ...     dtf2, reference="software2", threshold=0.3)

    >>> print(identified_differences)
    []

    Using "software2" as reference and resetting threshold to 10%:

    >>> identified_differences = significant_differences(
    ...     dtf2, reference="software2", neighs=False)

    >>> print(identified_differences[0])
       software1  software2  software3
    1         10         12         10

    >>> print(identified_differences[1])
       software1  software2  software3
    4         10         10         12
    """
    # parse data to DataFrame
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame.from_dict(data, orient='columns')

    # temporarily change data index to int to allow clustering and neighbouring
    old_index = data.index
    data.index = range(len(data.index))

    # parse reference
    ref = parse_reference_df(data, reference)

    # calculate relative deviations
    if method == "ardiffs":
        relative_deviations = calc_ardiffs(data, ref)
    else:
        relative_deviations = method(data, ref)

    # identify only those significant
    relative_significant_differences = relative_deviations[
        relative_deviations > threshold]

    # extract integer indices using the stack().unstack() combination
    int_indices = list(
        relative_significant_differences.stack().unstack().index)

    # cluster the integer indices into continous sequences
    index_clusters = _continous_int_sequences(int_indices)

    # add neighbouring indices if requested
    if neighs:
        index_clusters = list(
            _add_integer_neighbours(idx_cl, upper_bound=max(data.index))
            for idx_cl in index_clusters
        )

    # construct an all averaged dataframe
    all_averaged = pd.DataFrame(
        data=[ref] * len(data.columns),
        columns=data.index,
        index=data.columns,
    ).transpose()

    # update the all averaged dataframe with those from the original
    # data where significant differenes were detected
    mindices = list(relative_significant_differences.stack().index)
    for idx, col in mindices:
        all_averaged.at[idx, col] = data.at[idx, col]

    # seperate the detected differences into cluster of continous indices
    # reinstating the old index
    average_and_differences = all_averaged.copy()
    average_and_differences.index = old_index
    dataframes = [
        average_and_differences.iloc[idx_cluster]
        for idx_cluster in index_clusters
    ]

    return dataframes


def _continous_int_sequences(integers):
    """Identify continous sequences of integers.

    Parameters
    ----------
    integers: ~collections.abc.Container
        Container of sequence of integers

    Returns
    -------
    list
        Nested list of identified continous integer sequences.

    Examples
    --------
    Default Use Case:

    >>> sequences = [
    ...     (0, 1, 3, 5, 6, 10),
    ...     (1, 4, 5, 6, 12),
    ...     [3, 4, 5],
    ...     (1, 3, 7,),
    ... ]

    >>> for seq in sequences:
    ...     cnt_seq = _continous_int_sequences(seq)
    ...     print(seq)
    ...     print(cnt_seq)
    ...     print(59*'-')
    (0, 1, 3, 5, 6, 10)
    [[0, 1], [3], [5, 6], [10]]
    -----------------------------------------------------------
    (1, 4, 5, 6, 12)
    [[1], [4, 5, 6], [12]]
    -----------------------------------------------------------
    [3, 4, 5]
    [[3, 4, 5]]
    -----------------------------------------------------------
    (1, 3, 7)
    [[1], [3], [7]]
    -----------------------------------------------------------
    """
    integers = tuple(sorted(integers))
    sequences = []
    sequence = []

    for number in integers:
        sequence.append(number)
        if number+1 not in integers:
            sequences.append(sequence)
            sequence = []

    return sequences


def _add_integer_neighbours(sequence, lower_bound=0, upper_bound=None):
    """
    Add lower and upper integers to given sequence.

    Parameters
    ----------
    sequence: int
        Sequence of integers of which neighbours are to be added at lower and
        upper bounds

    Examples
    --------
    Default Use Case:

    >>> sequences = [
    ...     (0, 1, 3, 5, 6, 10),
    ...     (1, 4, 5, 6, 12),
    ...     [3, 4, 5],
    ...     (1, 3, 7,),
    ... ]

    >>> for seq in sequences:
    ...     neighboured_seq = _add_integer_neighbours(seq)
    ...     print(seq)
    ...     print(neighboured_seq)
    ...     print(59*'-')
    (0, 1, 3, 5, 6, 10)
    [0, 1, 3, 5, 6, 10, 11]
    -----------------------------------------------------------
    (1, 4, 5, 6, 12)
    [0, 1, 4, 5, 6, 12, 13]
    -----------------------------------------------------------
    [3, 4, 5]
    [2, 3, 4, 5, 6]
    -----------------------------------------------------------
    (1, 3, 7)
    [0, 1, 3, 7, 8]
    -----------------------------------------------------------
    """
    if sequence[0] != lower_bound:
        sequence = [sequence[0] - 1, *sequence]

    if upper_bound is None:
        upper_bound = float("+inf")

    if sequence[-1] != upper_bound:
        sequence = [*sequence, sequence[-1] + 1]

    return sequence
