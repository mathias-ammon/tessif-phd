# pylint: disable=trailing-whitespace
# src/tessif/identify/calculate.py
# pylint error disabled since the dataframe doctest results require those
"""Tessif module providing calc. tools for identifying result differences."""
import numpy as np
import pandas as pd


def calc_nmae(dataframes_dict, reference_df, method="mean"):
    """Calculate the Normalized Mean Average Error along the rows.

    Parameters
    ----------
    dataframes_dict: dict
        Dictionairy of of :class:`pandas.DataFrame` objects to calculate the
        nmae error values between columns of identically indexed columns
        relative to the :paramref:`~calc_nmae.reference_df` (see
        example for less gibberish). Designed for using with timevarying (load)
        results between different softwares for the same component(s).

    reference_df: pandas.DataFrame
        Dataframe indexed like those of
        :paramref:`~calc_nmae.dataframes_dict`

    method: {"mean", "spread", "std"}, default = "mean"
        Method of normalization:

            - ``"mean"``:  MAE is divided by ``mean(reference)``
            - ``"spread"``:  MAE is divided by
              ``abs(max(reference)-min(reference))``
            - ``"std"`` MAE is divided by ``std(reference)``

    Returns
    -------
    pandas.DataFrame
        DataFrame holding the calculated NMAE. Columns and index are swapped
        in comparison to the dataframes passed as arguments.

    Examples
    --------
    Picking up on the :paramref:`Identificier Data Input Example
    <tessif.identify.core.Identificier.data>`:

    >>> import pandas as pd
    >>> software1 = pd.DataFrame(
    ...     data=[[10, 8, 2], [0, 0, 0], [20, 2, 18]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> reference_df = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original Data Frames:

    >>> print(software1)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    >>> print(reference_df)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    Normalized Mean Average Error:

    >>> nmae = calc_nmae(
    ...     dataframes_dict={"software1": software1},
    ...     reference_df=reference_df,
    ... )
    >>> print(nmae)
         software1
    A B   0.793103
    B C   0.428571
      D   1.007874

    Using "spread" instead of the default "mean" normalization:

    >>> nmae = calc_nmae(
    ...     dataframes_dict={"software1": software1},
    ...     reference_df=reference_df,
    ...     method="spread",
    ... )
    >>> print(nmae)
         software1
    A B   0.497835
    B C   0.142857
      D   0.343049
    """
    result_data = {}
    for label, dtf in dataframes_dict.items():

        result_data[label] = np.mean(
            np.abs(dtf - reference_df),
            axis="index"
        ) / _normalize(reference_df, method)

    result_df = pd.concat(result_data, axis="columns")
    return result_df


def calc_nmbe(dataframes_dict, reference_df, method="mean"):
    """Calculate the Normalized Mean Biased Error along the rows.

    Parameters
    ----------
    dataframes_dict: dict
        Dictionairy of of :class:`pandas.DataFrame` objects to calculate the
        nmbe error values between columns of identically indexed columns
        relative to the :paramref:`~calc_nmbe.reference_df` (see
        example for less gibberish). Designed for using with timevarying (load)
        results between different softwares for the same component(s).

    reference_df: pandas.DataFrame
        Dataframe indexed like those of
        :paramref:`~calc_nmbe.dataframes_dict`

    method: {"mean", "spread", "std"}, default = "mean"
        Method of normalization:

            - ``"mean"``:  MBE is divided by ``mean(reference)``
            - ``"spread"``:  MBE is divided by
              ``abs(max(reference)-min(reference))``
            - ``"std"`` MBE is divided by ``std(reference)``

    Returns
    -------
    pandas.DataFrame
        DataFrame holding the calculated NMBE. Columns and index are swapped
        in comparison to the dataframes passed as arguments.

    Examples
    --------
    Picking up on the :paramref:`Identificier Data Input Example
    <tessif.identify.core.Identificier.data>`:

    >>> import pandas as pd
    >>> software1 = pd.DataFrame(
    ...     data=[[10, 8, 2], [0, 0, 0], [20, 2, 18]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> reference_df = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original Data Frames:

    >>> print(software1)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    >>> print(reference_df)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    Normalized Mean Biased Error:

    >>> nmbe = calc_nmbe(
    ...     dataframes_dict={"software1": software1},
    ...     reference_df=reference_df,
    ... )
    >>> print(nmbe)
         software1
    A B  -0.793103
    B C   0.428571
      D  -0.990157

    Using "spread" instead of the default "mean" normalization:

    >>> nmbe = calc_nmbe(
    ...     dataframes_dict={"software1": software1},
    ...     reference_df=reference_df,
    ...     method="spread",
    ... )
    >>> print(nmbe)
         software1
    A B  -0.497835
    B C   0.142857
      D  -0.337018
    """
    result_data = {}
    for label, dtf in dataframes_dict.items():

        result_data[label] = np.mean(
            np.subtract(dtf, reference_df),
            axis="index"
        ) / _normalize(reference_df, method)

    result_df = pd.concat(result_data, axis="columns")
    return result_df


def calc_nrmse(dataframes_dict, reference_df, method="mean"):
    """Calculate the Normalized Root Mean Square Error along the rows.

    Parameters
    ----------
    dataframes_dict: dict
        Dictionairy of of :class:`pandas.DataFrame` objects to calculate the
        NRMSE error values between columns of identically indexed columns
        relative to the :paramref:`~calc_nrmse.reference_df` (see
        example for less gibberish). Designed for using with timevarying (load)
        results between different softwares for the same component(s).

    reference_df: pandas.DataFrame
        Dataframe indexed like those of
        :paramref:`~calc_nrmse.dataframes_dict`

    method: {"mean", "spread", "std"}, default = "mean"
        Method of normalization:

            - ``"mean"``:  RMSE is divided by ``mean(reference)``
            - ``"spread"``:  RMSE is divided by
              ``abs(max(reference)-min(reference))``
            - ``"std"`` NRMSE is divided by ``std(reference)``

    Returns
    -------
    pandas.DataFrame
        DataFrame holding the calculated NRMSE. Columns and index are swapped
        in comparison to the dataframes passed as arguments.

    Examples
    --------
    Picking up on the :paramref:`Identificier Data Input Example
    <tessif.identify.core.Identificier.data>`:

    >>> import pandas as pd
    >>> software1 = pd.DataFrame(
    ...     data=[[10, 8, 2], [0, 0, 0], [20, 2, 18]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> reference_df = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original Data Frames:

    >>> print(software1)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    >>> print(reference_df)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    Normalized Root Mean Square Error:

    >>> nrmse = calc_nrmse(
    ...     dataframes_dict={"software1": software1},
    ...     reference_df=reference_df,
    ... )
    >>> print(nrmse)
         software1
    A B   0.975783
    B C   0.553283
      D   1.694993

    Using "spread" instead of the default "mean" normalization:

    >>> nrmse = calc_nrmse(
    ...     dataframes_dict={"software1": software1},
    ...     reference_df=reference_df,
    ...     method="spread",
    ... )
    >>> print(nrmse)
         software1
    A B   0.612504
    B C   0.184428
      D   0.576922
    """
    result_data = {}
    for label, dtf in dataframes_dict.items():
        result_data[label] = np.sqrt(
            np.mean(
                np.square(
                    np.subtract(
                        dtf,
                        reference_df
                    ),
                ),
                axis="index",
            )
        ) / _normalize(reference_df, method)

    result_df = pd.concat(result_data, axis="columns")
    return result_df


def _calc_corr_between_two_dfs(dataframes, method="pearson", fillna=None):
    """Calculate column pairwise correlation.

    Function to calculate correlation coefficients
    to quickly sort out difference between two different software results.

    Uses :attr:`pandas.DataFrame.corrwith` under the hood.

    Note
    ----
    Its only Possible to compare two different models

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of :class:`pandas.DataFrame` objects of which identically
        indexed columns will be used for correlation.

    method : {'pearson', 'kendall', 'spearman'} or callable
        Method of correlation:

        - pearson : standard correlation coefficient
        - kendall : Kendall Tau correlation coefficient
        - spearman : Spearman rank correlation
        - callable: callable with input two 1d ndarrays
          and returning a float.

    fillna: str, ~numbers.Number, None, default=None
        String, number or None specifying what to do when pearson corrleation
        results to ``NaN``. For design case usage, this is usually the case
        when one of the correlated timeseries results is all zeros.

        If ``None``, then :attr:`pandas.DataFrame.corrwith` output is kept.

    Returns
    -------
    pandas.Series:

        Pandas Series of the pairwise pearson correlation results. Where:

            - ``1`` = perfect correlation (good)
            - ``0`` = no correlation at all (bad)
            - ``-1`` = trending in opposite directions (woops!)

    See also
    --------
    `Pearson Correlation Coefficient
    <https://en.wikipedia.org/wiki/Pearson_correlation_coefficient>`_
    """
    # hdf5 is sometimes odd
    df1 = dataframes[0].astype('float64')
    df2 = dataframes[1].astype('float64')

    # correlation coefficients
    ccfs = df1.corrwith(df2, axis="index", method=method)

    if fillna is not None:
        ccfs = ccfs.fillna(value=fillna)

    return ccfs


def calc_avgs(dataframes):
    """ Calculate average results on timevarying dataframes.

    Takes any number of :class:`pandas.DataFrame` objects to calculate the
    average between rows of identically indexed columns (see example for less
    gibberish). Designed to average the timevarying (load) results between
    different softwares for the same component(s).

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of :class:`pandas.DataFrame` objects of which each
        row is averaged out.

    Returns
    -------
    pandas.DataFrame
        Averaged out results

    Examples
    --------
    Picking up on the :paramref:`Identificier Data Input Example
    <tessif.identify.core.Identificier.data>`:

    >>> import pandas as pd
    >>> software1 = pd.DataFrame(
    ...     data=[[10, 8, 2], [0, 0, 0], [20, 2, 18]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> software2 = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original Data Frames:

    >>> print(software1)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    >>> print(software2)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0


    Average Results:

    >>> averaged_results = calc_avgs(
    ...     [software1, software2])
    >>> print(averaged_results)
                            A    B       
                            B    C      D
    2019-01-01 00:00:00  11.5  7.5  996.0
    2019-01-01 01:00:00  21.0  0.0   21.0
    2019-01-01 02:00:00  55.0  1.0    9.0
    """

    average_model_concat = pd.concat(dataframes, sort=False)

    average_model = average_model_concat.groupby(average_model_concat.index)
    average_model_mean = average_model.mean()

    return average_model_mean


def calc_evs(
        dataframes,
        labels=None,
        reference=None,
        error="NMAE",
        normalization="mean",
):
    """Calculate Error Value between timevarying dataframes.

    Takes any number of :class:`pandas.DataFrame` objects to calculate chosen
    error values between rows of identically indexed columns (see example for
    less gibberish). Designed for using with timevarying (load) results between
    different softwares for the same component(s).

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of :class:`pandas.DataFrame` objects of which each
        row is averaged out.

    labels: ~collections.abc.Container, None, default=None
        Container of strings specifying the respective dataframe labels.
        Equals software names in the design case.

    reference: int, str, None, default=None
        Defines the reference results to be used for calculating the
        statistical error values. Integer denotes the 0-indexed container
        position of :paramref:`~calc_timevarrying_error_value.dataframes`.
        String the respective label. String parameter only works if
        :paramref:`~calc_timevarrying_error_value.labels` are stated as
        container of strings.

        In case ``None`` is used (default), the dataframes average is used as
        returned by :func:`average_timevarying_dataframe_results`.

    error: str
        String abbrevating the error value calculated. Currently supported are:

            - ``nmae`` for ``Normalized Mean Average Error`` (default)
            - ``nmbe`` for ``Normalized Mean Biased Error``
            - ``nrmse`` for ``Normalized Root Mean Square Error``

    normalization: {"mean", "spread"}, default = "mean"
        Method of error value normalization:

            - ``"mean"``:  NMBE is divided by ``mean(reference)``
            - ``"spread"``:  NMBE is divided by
              ``abs(max(reference)-min(reference))``

    Returns
    -------
    pandas.DataFrame
        DataFrame holding the calculated error values. Columns and index are
        swapped in comparison to the dataframes passed as arguments.

    Examples
    --------
    Picking up on the :paramref:`Identificier Data Input Example
    <tessif.identify.core.Identificier.data>`:

    >>> import pandas as pd
    >>> software1 = pd.DataFrame(
    ...     data=[[10, 8, 2], [0, 0, 0], [20, 2, 18]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> software2 = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> software3 = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original Data Frames:

    >>> print(software1)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    >>> print(software2)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    >>> print(software3)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    Normalized Mean Average Error:

    >>> nmae = calc_evs(
    ...     dataframes=[software1, software2, software3],
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ...     error="nmae",
    ... )
    >>> print(nmae)
         software1  software2  software3
    A B   0.793103        0.0        0.0
    B C   0.428571        0.0        0.0
      D   1.007874        0.0        0.0

    Using "spread" normalization:

    >>> nmae = calc_evs(
    ...     dataframes=[software1, software2, software3],
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ...     error="nmae",
    ...     normalization="spread",
    ... )
    >>> print(nmae)
         software1  software2  software3
    A B   0.497835        0.0        0.0
    B C   0.142857        0.0        0.0
      D   0.343049        0.0        0.0

    Normalized Mean Biased Error:

    >>> nmbe = calc_evs(
    ...     dataframes=[software1, software2, software3],
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ...     error="nmbe",
    ... )
    >>> print(nmbe)
         software1  software2  software3
    A B  -0.793103        0.0        0.0
    B C   0.428571        0.0        0.0
      D  -0.990157        0.0        0.0

    Using "spread" normalization:

    >>> nmbe = calc_evs(
    ...     dataframes=[software1, software2, software3],
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ...     error="nmbe",
    ...     normalization="spread",
    ... )
    >>> print(nmbe)
         software1  software2  software3
    A B  -0.497835        0.0        0.0
    B C   0.142857        0.0        0.0
      D  -0.337018        0.0        0.0


    Normalized Root Mean Square Error:

    >>> nrmse = calc_evs(
    ...     dataframes=[software1, software2, software3],
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ...     error="nrmse",
    ... )
    >>> print(nrmse)
         software1  software2  software3
    A B   0.975783        0.0        0.0
    B C   0.553283        0.0        0.0
      D   1.694993        0.0        0.0

    Using "spread" normalization:

    >>> nrmse = calc_evs(
    ...     dataframes=[software1, software2, software3],
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ...     error="nrmse",
    ...     normalization="spread",
    ... )
    >>> print(nrmse)
         software1  software2  software3
    A B   0.612504        0.0        0.0
    B C   0.184428        0.0        0.0
      D   0.576922        0.0        0.0
    """
    if labels is None:
        labels = range(len(dataframes))

    dataframe_dict = dict(zip(labels, dataframes))

    if reference is None:
        reference_results = calc_avgs(dataframes)
    else:
        if isinstance(reference, int):
            reference_results = tuple(dataframes)[reference]
        else:
            reference_results = dataframe_dict[reference]

    ev_mapping = {
        "nmae": calc_nmae,
        "nmbe": calc_nmbe,
        "nrmse": calc_nrmse,
    }

    result_df = ev_mapping[error](
        dataframe_dict, reference_results, method=normalization)
    return result_df


def calc_corrs(
        dataframes,
        method="pearson",
        labels=None,
        reference=None,
        fillna=None,
):
    """Calc Pearson Correlation Coefficient between timevarying dataframes.

    Takes any number of :class:`pandas.DataFrame` objects to calculate the
    pearson correlation coefficients between rows of identically indexed
    columns (see example for less gibberish). Designed for using with
    timevarying (load) results between different softwares for the same
    component(s).

    Uses :attr:`pandas.DataFrame.corrwith` under the hood.

    Parameters
    ----------
    dataframes: ~collections.abc.Container
        Container of :class:`pandas.DataFrame` objects of which each
        row is averaged out.

    method : {'pearson', 'kendall', 'spearman'} or callable
        Method of correlation:

        - pearson : standard correlation coefficient
        - kendall : Kendall Tau correlation coefficient
        - spearman : Spearman rank correlation
        - callable: callable with input two 1d ndarrays
          and returning a float.

    labels: ~collections.abc.Container, None, default=None
        Container of strings specifying the respective dataframe labels.
        Equals software names in the design case.

    reference: int, str, None, default=None
        Defines the reference results to be used for calculating the
        statistical error values. Integer denotes the 0-indexed container
        position of :paramref:`~calc_timevarrying_error_value.dataframes`.
        String the respective label. String parameter only works if
        :paramref:`~calc_timevarrying_error_value.labels` are stated as
        container of strings.

        In case ``None`` is used (default), the dataframes average is used as
        returned by :func:`average_timevarying_dataframe_results`.

    fillna: str, ~numbers.Number, None, default=None
        String, number or None specifying what to do when pearson corrleation
        results to ``NaN``. For design case usage, this is usually the case
        when one of the correlated timeseries results is all zeros.

        If ``None``, then :attr:`pandas.DataFrame.corrwith` output is kept.

    Returns
    -------
    pandas.DataFrame
        DataFrame holding the calculated PCC values. Columns and index are
        swapped in comparison to the dataframes passed as arguments.

    Examples
    --------
    Picking up on the :paramref:`Identificier Data Input Example
    <tessif.identify.core.Identificier.data>`:


    >>> import pandas as pd
    >>> software1 = pd.DataFrame(
    ...     data=[[10, 8, 2], [0, 0, 0], [20, 2, 18]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> software2 = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )
    >>> software3 = pd.DataFrame(
    ...     data=[[13, 7, 1990], [42, 0, 42], [90, 0, 0]],
    ...     columns=pd.MultiIndex.from_tuples(
    ...         [("A", "B"), ("B", "C"), ("B", "D")]),
    ...     index=pd.date_range('2019-01-01', periods=3, freq='H'),
    ... )

    Original Data Frames:

    >>> print(software1)
                          A  B    
                          B  C   D
    2019-01-01 00:00:00  10  8   2
    2019-01-01 01:00:00   0  0   0
    2019-01-01 02:00:00  20  2  18

    >>> print(software2)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    >>> print(software3)
                          A  B      
                          B  C     D
    2019-01-01 00:00:00  13  7  1990
    2019-01-01 01:00:00  42  0    42
    2019-01-01 02:00:00  90  0     0

    Pearson Correlation Coefficients:

    >>> pcc = calc_corrs(
    ...     dataframes=[software1, software2, software3],
    ...     method="pearson",
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ... )
    >>> print(pcc)
         software1  software2  software3
    A B   0.617145        1.0        1.0
    B C   0.970725        1.0        1.0
      D  -0.426423        1.0        1.0

    Spearman Correlation Coefficients:

    >>> spear = calc_corrs(
    ...     dataframes=[software1, software2, software3],
    ...     method="spearman",
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ... )
    >>> print(spear)
         software1  software2  software3
    A B   0.500000        1.0        1.0
    B C   0.866025        1.0        1.0
      D  -0.500000        1.0        1.0

    Kendall Correlation Coefficients:

    >>> kend = calc_corrs(
    ...     dataframes=[software1, software2, software3],
    ...     method="kendall",
    ...     labels=["software1", "software2", "software3"],
    ...     reference="software2",
    ... )
    >>> print(kend)
         software1  software2  software3
    A B   0.333333        1.0        1.0
    B C   0.816497        1.0        1.0
      D  -0.333333        1.0        1.0

    """
    if labels is None:
        labels = range(len(dataframes))

    dataframe_dict = dict(zip(labels, dataframes))

    if reference is None:
        reference_results = calc_avgs(dataframes)
    else:
        if isinstance(reference, int):
            reference_results = tuple(dataframes)[reference]
        else:
            reference_results = dataframe_dict[reference]

    pearson_results = pd.DataFrame()

    for label, dtf in dataframe_dict.items():
        pearson_results[label] = _calc_corr_between_two_dfs(
            dataframes=[reference_results, dtf],
            method=method,
            fillna=fillna,
        )

    return pearson_results


def _normalize(reference, method):
    norms = {
        "mean": np.mean(reference, axis="index"),
        "spread": abs(reference.max() - reference.min()),
        "std": np.std(reference, axis="index"),
    }

    return norms[method]


def calc_reldiffs(data, reference):
    """Calculate absolute relative difference between data frames."""
    biased_differences = data.subtract(reference, axis="index")
    relative_biased_differences = biased_differences.divide(
        reference, axis="index")
    absolute_relative_differences = relative_biased_differences

    return absolute_relative_differences


def calc_ardiffs(data, reference):
    """Calculate absolute relative difference between data frames."""
    biased_differences = data.subtract(reference, axis="index")
    relative_biased_differences = biased_differences.divide(
        reference, axis="index")
    absolute_relative_differences = relative_biased_differences.abs()

    return absolute_relative_differences
