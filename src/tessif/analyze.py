# tessif/analyze
"""
:mod:`~tessif.analyze` is a :mod:`tessif` module aggregating functionalities
for inspecting :ref:`energy system simulation models <SupportedModels>`
to evaluate and compare them.

It serves as main reference point for tessif's scientific evaluation process.
"""

import collections
import copy
from datetime import datetime
import importlib
import logging
import math
import os
import pickle
import time
import tracemalloc

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import tessif.examples.data.tsf.py_hard as coded_examples
import tessif.frused.defaults as defaults
import tessif.parse as parse
import tessif.simulate as simulate
import tessif.transform.mapping2es.tsf as tsf
import tessif.transform.nxgrph as nxt
import tessif.visualize.compare as vis_compare
import tessif.visualize.nxgrph as nxv
from tessif.frused.namedtuples import MemoryTime, MemoryTimeConstraints, \
    SimulationProcessStepResults
from tessif.frused.paths import example_dir
from tessif.visualize import component_loads

logger = logging.getLogger(__name__)


def assess_scalability(N, T, model, N_resolution=4, T_resolution=4,
                       only_total=False, storage_folder=None,
                       example='minimal', **kwargs):
    """
    Estimate the scalability of a chosen energy system simulation model.
    Investigate an :ref:`energy system simulation model <SupportedModels>` for
    scalability in simulated time as well as number of components.

    Parameters
    ----------
    N: int
        Number of minimum self similar energy system units (MiSSESUs)
        the :attr:`self similar energy system
        <tessif.examples.data.tsf.py_hard.create_self_similar_energy_system>`
        consists of.

        (Adding a stepping parameter for N might also be helpful. Add one if
        you deem helpful/necessary)

    T: int
        Number of timeframe steps used for scaling.

        Has to be 2 or higher.

        (Adding a stepping parameter for T might also be helpful. Add one if
        you deem helpful/necessary)

    model: str
        String specifying one of the
        :attr:`~tessif.frused.defaults.registered_models` representing the
        :ref:`energy system simulation model <SupportedModels>` investigated.

    N_resolution: int, default=4
        Number of different energy system sizes to be measured.

        The amount of measured sizes might sometimes be fewer than the
        specified value if that is similar in size to the value of N.

    T_resolution: int, default=4
        Number of different timeframes to be measured.

        The amount of timeframes might sometimes be fewer than the specified
        value if that is similar in size to the value of T.

    only_total: bool, default=False
        Set to true to only return the total result.

    storage_folder: str, None, default=None
        String representing the top level folder the energy system data will be
        stored in.

        If ``None`` the :paramref:`N-th <assess_scalability.N>` energy system
        will be stored in
        ``examples_dir/application/computational_comparison/scalability/es_N``

        See :attr:`tessif.frused.paths.examples_dir` for more information on
        its location.

    example: str
        Specify which of tessif's hardcoded examples should be measured.
        Is passed to create_self_similar_energy_system(). For more info look at
        its docs.

    kwargs:
        Are passed to the create_self_similar_energy_system() function.

    Return
    ------
    ~typing.NamedTuple
        :attr:`~tessif.frused.namedtuples.MemoryTime` namedtuple
        :class:`dictionaries <dict>` containing the scalability assessment
        results as TxN :class:`DataFrames <pandas.DataFrame>`.
    """
    if storage_folder is None:
        storage_folder = os.path.join(example_dir, 'application',
                                      'computational_comparison',
                                      'scalability')

    # Create the timeframe.
    # T represents the max number of periods, T_resolution the number of steps.
    # This might still need a smarter solution.
    timesteps = np.arange(T, 1, -(T-1) // T_resolution)
    timesteps = sorted(timesteps)
    timeframes = list()
    for period in timesteps:
        timeframes.append(pd.date_range(
            datetime.now().date(),
            periods=period, freq='H'))

    # Create list of es sizes to be measured.
    # N is the max size of the es, N_resolution the number of steps.
    N_index = sorted(np.arange(N, 0, -N // N_resolution))

    # Generate lists in which the results of the measurements will be stored.
    time2 = list()
    measure_time = collections.namedtuple('measure_time',
                                          ['reading', 'parsing',
                                           'transformation', 'simulation',
                                           'post_processing', "result"])
    memory2 = list()
    measure_memory = collections.namedtuple('measure_memory',
                                            ['reading', 'parsing',
                                             'transformation', 'simulation',
                                             'post_processing', "result"])
    constraints2 = list()

    # The algorithm for stop_time and trace_memory. The es will be stored in
    # hdf5 and analyzed by both functions. For now, it's only possible to store
    # the es in hdf5 but that wouldn't be too difficult to change I guess.
    for number in N_index:
        time1 = list()
        memory = list()
        constraints = list()

        for timeframe in timeframes:
            # Create energy system with the size given by 'number' and the
            # timeframe specified in 'timeframe' and store it in a .hdf5 file.
            sses = coded_examples.create_self_similar_energy_system(
                N=number, timeframe=timeframe, unit=example, **kwargs)
            _ = sses.to_hdf5(
                directory=os.path.join(storage_folder, 'es_' + str(number)),
                filename='self_similar_energy_system.hdf5')
            path = os.path.join(storage_folder, 'es_' + str(number),
                                'self_similar_energy_system.hdf5')

            # Measure time and memory usage.
            if only_total is True:
                time_measurement = stop_time(
                    path=path, parser=parse.hdf5, model=model, only_total=True)
                memory_measurement = trace_memory(
                    path=path, parser=parse.hdf5, model=model, only_total=True)

                # Transform memory results from bytes to MB and round to first
                # digit and round time measurement in seconds to first digit:
                mm_rounded = round(memory_measurement * 1e-6, 1)
                tm_rounded = round(time_measurement, 1)
            else:
                time_measurement = measure_time._make(stop_time(
                    path=path, parser=parse.hdf5, model=model).values())
                memory_measurement = measure_memory._make(trace_memory(
                    path=path, parser=parse.hdf5, model=model).values())

                # Transform memory results from bytes to MB and round to first
                # digit:
                mm_rounded = measure_memory._make(
                    round(res_value * 1e-6, 1) for res_value in
                    memory_measurement)

                # Round time measurement in seconds to first digit.
                tm_rounded = measure_time._make(
                    round(res_value, 1) for res_value in time_measurement)

            # Count constraints. For that restore the Resultier object that was
            # created and dumped into a pickle file in 'trace_memory()'.
            d = os.path.join(storage_folder, 'es_' + str(number))
            f = 'resultier.tsf'
            restored_resultier = pickle.load(
                open(os.path.join(d, f), "rb"))

            time1.append(tm_rounded)
            memory.append(mm_rounded)
            constraints.append(restored_resultier.number_of_constraints)

        time2.append(time1)
        memory2.append(memory)
        constraints2.append(constraints)

    # Store the results in three pandas.DataFrames of N_resolution columns and
    # T_resolution rows. (If the value of N_resolution is close to the value of
    # N, the number of columns might be less. Same for T_resolution and T) In
    # case the measurement returns a dict (not at just a single value) the cell
    # is a tuple of values representing the single measurements.
    timings_data_frame = pd.DataFrame(data=time2, columns=timesteps,
                                      index=N_index)
    timings_data_frame = timings_data_frame.transpose()
    # A column name for the dataframe period would be nice.

    memory_data_frame = pd.DataFrame(data=memory2, columns=timesteps,
                                     index=N_index)
    memory_data_frame = memory_data_frame.transpose()

    constraints_data_frame = pd.DataFrame(data=constraints2, columns=timesteps,
                                          index=N_index)
    constraints_data_frame = constraints_data_frame.transpose()

    return MemoryTimeConstraints(memory_data_frame, timings_data_frame,
                                 constraints_data_frame)


def average(timeseries):
    """Calculate the average of different software results.

        Parameters
        ----------
        timeseries: ~collections.abc.Mapping, pandas.DataFrame
            Mapping of timeseries to an identifier or a
            DataFrame containing the timeseries as columns, the corresponding
            timestamps as index and the identifiers as column header.


        Returns
        -------
        average: np.array
            np.array containing the average timeseries data
     """

    timeseries = timeseries.astype('float64')
    average = np.zeros(len(timeseries))

    for j in range(len(average)):
        average[j] = np.array([
            round((timeseries.iloc[:, -5:5].sum(axis=1))[j] / len(
                timeseries.columns), 2)])

    return average


def compare_N_timeseries(timeseries, threshold):
    """
    Algorithm to detect intervals in which the given timeseries deviate from
    their mean by a certain threshold.

    Parameters
    ----------
    timeseries: ~collections.abc.Mapping, pandas.DataFrame
        Mapping of timeseries to an identifier or a
        DataFrame containing the timeseries as columns, the corresponding
        timestamps as index and the identifiers as column header.

        Note
        ----
        If no DataFrame is passed, the index will be set automatically as
        integers (0-indexed) counting the values position inside the
        timeseries. Meaning the N-th value will have and index of N-1.

    threshold: float
        Float representing the relative deviation of the given
        :paramref:`~compare_N_timeseries.timeseries` from their mean that
        is considered as threshold for identifying the series values as
        different.

        To recognize a series value as different from the others following
        statement has to be ``True``:

            :math:`|T(t)-\\overline{T}(t)| \geq \\text{threshold} \cdot \\overline{T}(t)`

    Returns
    -------
    load_differences: pandas.DataFrame
        DataFrame representing the comparison results. The first column
        represents the average timeseries. The following columns are filled by
        the timeseries (ordered as they were passed) in which differences
        were recognized. The index of the DataFrame represents the indices
        passed (usually timestamps) in which differences were detected.
    """
    timeseries = timeseries.astype('float64')
    # parse the timeseries to be a pandas DataFrame
    if not isinstance(timeseries, pd.DataFrame):
        data = pd.DataFrame.from_dict(data=timeseries, orient='columns')
    else:
        data = timeseries

    # adding  average to the dataframe
    data_co = copy.deepcopy(data)
    data_co.insert(loc=0, column='average', value=average(timeseries))

    results_df = pd.DataFrame(index=data_co.index)

    for column in data_co.columns:

        result_df_single = np.zeros(len(data_co))
        for i in range(len(data_co)):

            if data_co[column][i] >= data_co['average'][i] * (1 + threshold):
                result_df_single[i] = data_co[column][i]

            elif data_co[column][i] <= data_co['average'][i] * (1 - threshold):
                result_df_single[i] = data_co[column][i]

            else:
                result_df_single[i] = data_co['average'][i]

        results_df[column] = result_df_single

    return results_df


def statistically_compare_N_timeseries(timeseries, normalized=True,
                                       reference='', type='mean'):
    """
    Algorithm to calculate a number of statistical (values) for the given
    timeseries relative to their reference timeseries.

    Parameters
    ----------
    timeseries: ~collections.abc.Mapping, pandas.DataFrame
        Mapping of timeseries to an identifier or a
        DataFrame containing the timeseries as columns, the corresponding
        timestamps as index and the identifiers as column header.

        Note
        ----
        If no DataFrame is passed, the index will be set automatically as
        integers (0-indexed) counting the values position inside the
        timeseries. Meaning the N-th value will have and index of N-1.

    normalized: bool
        Determine the returned values to be normalized or not.

        default = "True"

    type: str
        Define the type of normalization. Statistical (values) can be
        normalized by 'mean' or by the timeseries 'range':

        default = "mean"

    reference: str
        Determine the reference system that is to serve as a reference to
        which the statistical values are determined.

    Returns
    -------
    ldr: pandas.DataFrame
        DataFrame holding the statistical load difference results. The
        index (rows) represent the calculated value names/types, the
        columns the respective model names. For Example::

                   omf  test
            rmse    42    42
            mae      0     0
            mbe   9000  9000
    """
    timeseries = timeseries.astype('float64')
    # parse the timeseries to be a pandas DataFrame
    if not isinstance(timeseries, pd.DataFrame):
        data = pd.DataFrame.from_dict(data=timeseries, orient='columns')
    else:
        data = timeseries

    # temporary results mapping to create the df later on
    results_dict = dict()
    data_co_st = copy.deepcopy(data)

    if reference == 'average' or reference == '':

        reference_data = average(data_co_st)

    else:
        reference_data = data_co_st[reference]

    # iterate through each of the given timeseries
    for column in data_co_st.columns:
        # create a result for each column using the functions listed in
        # analyze.statistical_value_mapping
        results_dict[column] = [
            calc_function(data_co_st[column], reference_data)
            for calc_function in statistical_value_mapping.values()]

    result_df_non_normalized = pd.DataFrame(
        results_dict,
        index=statistical_value_mapping.keys())

    result_df_normalized = pd.DataFrame()

    for column in result_df_non_normalized.columns:
        # iterate through each of the error results

        if type == 'mean':

            # normalized by mean
            result_df_normalized[column] = (
                result_df_non_normalized[column] / reference_data.mean())

        elif type == 'range':
            # divide each error by the difference of the maximum / minimum by
            # the average normalized by range.
            result_df_normalized[column] = (
                result_df_non_normalized[column] / abs(
                    reference_data.max() - reference_data.min()))

        else:
            return 'chose type of normalization'

    result_df_normalized_copy = copy.deepcopy(result_df_normalized)

    # to switch between normalized and non normalized errors
    if normalized is False:
        result_df = result_df_non_normalized
    else:
        result_df = result_df_normalized_copy
    return result_df


def _calculate_root_mean_square_error(data, average):
    """
    Algorithm to calculate the root-mean-square error for the given
    timeseries relative to their average timeseries.

    Parameters
    ----------
    data: ~collections.abc.Mapping, pandas.DataFrame
        Mapping of timeseries to an identifier or a
        DataFrame containing the timeseries as columns, the corresponding
        timestamps as index and the identifiers as column header.

    average: np.array
        np.array containing the average timeseries data

    Returns
    -------
    ldr: pandas.DataFrame
        The calculated  root-mean-square error of a time series
    """

    return round(np.sqrt(((data - average) ** 2).mean()), 3)


def _calculate_mean_absolute_error(data, average):
    """
    Algorithm to calculate the root mean absolute error for the given
    timeseries relative to their average timeseries

    Parameters
    ----------
    data: ~collections.abc.Mapping, pandas.DataFrame
        Mapping of timeseries to an identifier or a
        DataFrame containing the timeseries as columns, the corresponding
        timestamps as index and the identifiers as column header.

    average: np.array
        np.array containing the average timeseries data

    Returns
    -------
    ldr: pandas.DataFrame
        The calculated mean absolute error of a time series
    """

    return round(np.mean(np.absolute(data - average)), 3)


def _calculate_mean_biased_error(data, average):
    """
    Algorithm to calculate the root mean biased error for the given
    timeseries relative to their average timeseries

    Parameters
    ----------
    data: ~collections.abc.Mapping, pandas.DataFrame
        Mapping of timeseries to an identifier or a
        DataFrame containing the timeseries as columns, the corresponding
        timestamps as index and the identifiers as column header.

    average: np.array
        np.array containing the average timeseries data

    Returns
    -------
    ldr: pandas.DataFrame
        The calculated mean bias error of a time series
    """

    return round(np.mean(data - average), 3)


statistical_value_mapping = {
    'NRMSE': _calculate_root_mean_square_error,
    'NMAE': _calculate_mean_absolute_error,
    'NMBE': _calculate_mean_biased_error,
}
"""
:class:`~collections.abc.Mapping` of the statistical value calculation
utilities used to statistically compare the N timeseries.

Edit/ `Monkey Patch <https://en.wikipedia.org/wiki/Monkey_patch>`_ this mapping
to change the behavior of
:meth:`~tessif.analyze.statistically_compare_N_timeseries`.
"""


def lag_correlate(timeseries, number_of_steps):
    """
    Compares two datasets by applying a lag correlation analysis, to find out
    whether a potential (time) lag exists.

    During the lag correlation analysis the data of one set is shifted by up to
    :paramref:`~lag_correlate.maximum_lag` number of (time) steps to find out
    if a better correlation can be found.

    This would then imply that the data of one set might be shifted by a
    certain number of time steps, or in other words that one dataset might lag
    behind the other.

    Parameters
    ----------
    timeseries: pandas.DataFrame
        Mapping of timeseries to an identifier or a
        DataFrame containing the timeseries as columns, the corresponding
        timestamps as index and the identifiers as column header.

    number_of_steps: numpy arange
        Integer specifying the maximum lag to be assessed. Meaning during the
        lag correlation analysis the datasets are shifted by 0 to maximum_lag
        number of (time) steps to find out if a better correlation can be
        found. Which would imply that both datasets might be shifted by a
        certain number of (time) steps, or in other words whether one set
        lags behind.

    See also
    --------
    https://en.wikipedia.org/wiki/Cross-correlation


    Returns
    -------
    list
        List containing:

           1. position of the highest pearson correlation therefore follows the
                lag
           2. highest pearson correlation value of the up and down shifted data
                as float
    """

    def detc_lag(data, lag):
        """
        Subfunction to detect the lag in a timeseries.
        Shift the data to create a new dataframe to be pearson correlated in
        lag_correlate
        """

        if lag >= 0:
            data.iloc[:, 1] = data.iloc[:, 1].shift(lag)
        else:
            data.iloc[:, 0] = data.iloc[:, 0].shift(-lag)

        return round(data.iloc[:, 0].corr(data.iloc[:, 1]), 4)

    timeseries = timeseries.astype('float64')

    if not isinstance(timeseries, pd.DataFrame):
        data = pd.DataFrame.from_dict(data=timeseries, orient='columns')
    else:
        data = timeseries

    orig_data = copy.deepcopy(data)

    tmp = {}
    for i in number_of_steps:
        shifted_data = copy.deepcopy(orig_data)

        tmp[i] = detc_lag(shifted_data, i)

    tmp_2 = copy.deepcopy(tmp)

    for key in tmp_2.keys():
        tmp_2[key] = abs(tmp_2[key])

    lag = max(tmp_2, key=(lambda key: tmp_2[key]))

    # tmp[lag] is the value of the highest pearson correlation.

    result_df = [lag, tmp[lag]]

    return result_df


def create_average_model(data_dic):
    """
       function to create the "average" or "medium" model

       Parameters
       ----------
       data_dic: dictionary
       all data of the models each stored as Pandas DataFrames in a dictionary

       Returns
       -------
       dictionary
           contains the medium model
       """

    average_model_concat = pd.concat(data_dic.values(), sort=False)

    average_model = average_model_concat.groupby(average_model_concat.index)
    average_model_mean = average_model.mean()

    return average_model_mean


def mae_list(data_dic, reference=''):
    """
    Create a list of mean absolute errors form each model compared with a
    reference model

    Parameters
    ----------

    data_dic: dictionary
        all data of the models each stored as pandas DataFrames in a
        dictionary

    reference: str
        Defines the reference model to be used as a reference point for
        determining the statistical values. (average, omf, ppsa....)

    Returns
    -------
    pandas.DataFrame
        List of mean absolute errors from each model compared with a reference
        model.
    """
    if reference == 'average' or reference == '':

        reference_model = create_average_model(data_dic)

    else:
        reference_model = data_dic[reference]

    columns = []
    result_data = pd.DataFrame(index=reference_model.columns)
    for key, df in data_dic.items():
        columns.append(key)
        col = []

        for column in df.columns:
            j = round((np.mean(np.absolute(
                (df[column] - reference_model[column])))) / np.mean(
                reference_model[column]), 3)

            col.append(j)

        result_data[key] = col

    return result_data


def pearson_correlate(dataframe1, dataframe2):
    """
    Function to calculate the pearson correlation coefficient
    to quickly sort out difference between two different models

    Note
    ----
    Its only Possible to compare two different models

    Parameters
    ----------
    dataframe1: pandas.DataFrame
        Dataframe containing all components and flows of one model
        (calliope, fine, oemof, pypsa, ...)

    dataframe2: pandas.DataFrame
        Dataframe containing all components and flows of another software
        (calliope, fine, oemof, pypsa, ...)


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
    dataframe1 = dataframe1.astype('float64')
    dataframe2 = dataframe2.astype('float64')

    pearson = round(dataframe1.corrwith(dataframe2, axis=0), 4)

    return pearson.fillna(value='ocfz')


def pearson_list(data_dic, reference=""):
    """
    Create a list of pearson correlations from each model compared with a
    reference model.

    Parameters
    ----------

    data_dic: dictionary
    all data of the models each stored as Pandas DataFrames in a dictionary

    reference: str
    Define the reference model to be used as a reference point to determine the
    statistical values. (average, omf, ppsa....)

    Returns
    -------
    pandas.DataFrame
    List of pearson correlations from each model compared with a reference
    model.
    """
    pearson_results = pd.DataFrame()

    if reference == 'average' or reference == '':

        reference_model = create_average_model(data_dic)

    else:
        reference_model = data_dic[reference]

    for key, dataframes in data_dic.items():
        pearson_results[key] = pearson_correlate(reference_model, dataframes)

    return pearson_results


def autoselect(pearson_df, mae_df, pearson_threshold=0.7, mae_threshold=0.05,
               desired_condition="all"):
    """
    Algorythm that works out the differences of the individual time series of
    the components/flows from all the models studied. The pearson correlation
    and the mean absolute error are calculated once for the models in regard to
    a reference model. From the respective combinations of the two statistical
    quantities, it can be determined how strongly certain components/flows
    differ from each other. In general, a high pearson correlation means a high
    linear equality and a low mean absolute error means a small total
    difference of the values. Three different types of conditions can be
    processed.

    1. High interest / significantly different
        pearson correlation < pearson_threshold, mae > mae_threshold

    2. Medium interest / borderline significantly
        pearson correlation < pearson_threshold, mae <= mae_threshold
        pearson correlation >= pearson_threshold, mae > mae_threshold

    3. Least interesting / most likely of no interest
        pearson correlation >= pearson_threshold, mae <= mae_threshold

    See also
    --------
    https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
    https://en.wikipedia.org/wiki/Mean_absolute_error


    Parameters
    ----------
    pearson_df: panda.DataFrame
        Pearson correlations from each model compared with a reference model.

    mae_df: panda.DataFrame
        Mean absolute errors from each model compared with a reference model.

    pearson_threshold: float ; default = 0.7
        Define at which value the pearson correlation should be undercut to be
        considered as a significant difference.
        Large values mean high linear equality

    mae_threshold: float ; default = 0.05
        Defines at which value the mean absolute error should be exceeded to be
        considered as a significant difference. Small values mean that there
        are hardly any differences in the values of the time series.

    desired_condition: str ; default = "all"
        determines according to which condition the data should be filtered
            " condition_1"   or 'very_interesting'                  == High interest / significantly different.
            " condition_2"   or 'interesting_high_mae_low_pearson'  == Medium interest / boderline significantly
            " condition_2_3" or 'all_from_interest'                == Medium interest / boderline significantly shows both conditions 2 and 3
            " condition_3"   or 'interesting_low_mae_high_pearson'  == Medium interest / boderline significantly
            " condition_4"   or 'not_interesting'                   == Least interesting / most likely of no interest
            " condition_5"   or "all"                              == shows the complete data set (no condition)
    Returns
    -------
    dictionary
        Values of the pearson correlation and the mean absolute errors of the
        selected condition.
    """

    # crating a unique number to transform ocfz : to use boolean operators
    pearson_df.replace("ocfz", float(-0.000123), inplace=True)

    pearson_df = pearson_df.astype('float64')
    mae_df = mae_df.astype('float64')

    if desired_condition == 'very_interesting' or desired_condition == \
            'condition_1':

        condition = [[pearson_df.where(
            pearson_df < pearson_threshold),
            mae_df.where(mae_df > mae_threshold)]]

    elif desired_condition == 'interesting_high_mae_low_pearson' or \
            desired_condition == 'condition_2':

        condition = [[pearson_df.where(
            pearson_df < pearson_threshold),
            mae_df.where(mae_df <= mae_threshold)]]

    elif desired_condition == 'interesting_low_mae_high_pearson' or \
            desired_condition == 'condition_3':

        condition = [[pearson_df.where(
            pearson_df >= pearson_threshold),
            mae_df.where(mae_df > mae_threshold)]]

    elif desired_condition == 'not_interesting' or desired_condition == \
            'condition_4':

        condition = [[pearson_df.where(
            pearson_df >= pearson_threshold),
            mae_df.where(mae_df <= mae_threshold)]]

    elif desired_condition == "all" or desired_condition == 'condition_5':

        condition = [[pearson_df, mae_df]]

    elif desired_condition == 'all_from_interest' or desired_condition == \
            'condition_2_3':
        condition = [[pearson_df.where(pearson_df < pearson_threshold),
                      mae_df.where(mae_df <= mae_threshold)],
                     [pearson_df.where(pearson_df >= pearson_threshold),
                      mae_df.where(mae_df > mae_threshold)]]

    else:
        logger.warning("Use one of the following:")
        logger.warning(" condition_1")
        logger.warning(" condition_2")
        logger.warning(" condition_2_3")
        logger.warning(" condition_3")
        logger.warning(" condition_4")

    def cond(condition):
        condition_pearson = condition[0]
        condition_mae = condition[1]

        # Boolean transformation to drop out pairs not fulfilling the condition
        pearson_df_bool = condition_pearson.isna()
        mae_df_bool = condition_mae.isna()

        # creating a mask
        mask = mae_df_bool | pearson_df_bool

        pearson_df_final = condition_pearson.mask(mask)
        mae_df_final = condition_mae.mask(mask)

        # merging mae and pearson values in one dataframe for easy comparison
        result_df = pd.concat([pearson_df_final, mae_df_final], axis=1,
            keys=["pearson", "mae"]).swaplevel(0, 1, axis=1).sort_index(axis=1)

        result_df = result_df.dropna(axis=0, how='all')

        return result_df

    result_dic = {}
    for i in range(len(condition)):
        result_dic[i] = cond(condition[i])

    if len(result_dic.keys()) != 1:

        result_0 = result_dic[0].fillna(result_dic[1])
        result = pd.concat([result_0, result_dic[1]])
        result = result[~result.index.duplicated(keep='first')]
        result = result.replace([float(-0.000123), np.nan], [str("ocfz"), ""])
    else:
        result = result_dic[0]

    result = result.replace([float(-0.000123), np.nan], [str("ocfz"), ""])

    return result


def stop_time(path, parser, model, measurement="CPU", timeframe='primary',
              hook=None, only_total=False, trans_ops=None):
    """
    Measure elapsed wall time.

    Parameters
    ----------
    path: str
        String representing the path the energy system data resides in.
        e.g. ``examples_dir/application/computational_comparison/fractal.xlsx``
    model: str
        String specifying one of the
        :attr:`~tessif.frused.defaults.registered_models` representing the
        :ref:`energy system simulation model <SupportedModels>` investigated.
    parser: :class:`~collections.abc.Callable`
        Functional used to read in and parse the energy system data.
        Usually one of the module functions found in :mod:`tessif.parse`.
    measurement: str, default="CPU"
        String specifying which time measurement to use. Either ``"CPU"`` or
        ``"Wall"`` are supported using:

           - ``"CPU"`` for measuring the CPU time utilizing
             :func:`time.process_time`

           - ``"Wall"`` for measuring the elapsed wall time utilizing
             :func:`time.time`

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used.
        One of ``'primary'``, ``'secondary'``, etc... by convention.
    hook: dict, None, default=None
        Dictionary keying :mod:`~tessif.frused.hooks` callables by its
        :attr:`registered name
        <tessif.frused.defaults.registered_models>`. See a use case in
        :ref:`AutoCompare_HH`.
    only_total: bool, default=False
        Set to true to only return the total result.
    trans_ops: dict, None, default=None
        Dictionary keying transformation options
        of a model by its :attr:`registered name
        <tessif.frused.defaults.registered_models>`. For example the
        :paramref:`~tessif.transform.es2es.ppsa.transform.forced_links` option
        when using :ref:`Models_Pypsa` as in::

            trans_ops={'pypsa': {
                'forced_links': ['Transformator_1', 'Transformator_2']}
            }

    Return
    ------
    results: dict
        Dictionary containing timing results in seconds keyed by the
        corresponding simulation steps that were investigated:

            - ``reading``
            - ``parsing``
            - ``transformation``
            - ``simulation``
            - ``post_processing``
    """
    time_measurement_tool = {
        "CPU": "process_time",
        "cpu": "process_time",
        "Wall": "time",
        "wall": "time",
        "clock": "time",
        "wall-clock": "time",
    }

    if measurement not in time_measurement_tool:
        meas = measurement
        msg1 = f"Value for 'measurement' attribute: {meas} not recognized\n"
        msg2 = f"Use on of the following: {list(time_measurement_tool.keys())}"
        raise TypeError(msg1 + msg2)

    # Figure out model used
    used_model = None
    for internal_name, spellings in defaults.registered_models.items():
        if model in spellings:
            used_model = internal_name
            break

    timing_results = dict()

    # It might be a good idea to wrap each step or the whole process into a
    # loop to run it N times to create some statistical sound data.
    # There should be a parameter 'N' that is set to a sensible default.

    # 1) Read and parse in the tessif energy system data
    start_time1 = getattr(time, time_measurement_tool[measurement])()
    esm = parser(path, timeframe=timeframe)
    end_time1 = getattr(time, time_measurement_tool[measurement])()
    reading_time = end_time1 - start_time1  # time in seconds
    timing_results['reading'] = round(reading_time, 4)

    # 2) Create the tessif energy system
    start_time2 = getattr(time, time_measurement_tool[measurement])()
    es = tsf.transform(esm)
    end_time2 = getattr(time, time_measurement_tool[measurement])()
    parsing_time = end_time2 - start_time2  # time in seconds
    timing_results['parsing'] = round(parsing_time, 4)

    # 3) Transform the energy system into the requested model
    start_time3 = getattr(time, time_measurement_tool[measurement])()
    requested_model = importlib.import_module('.'.join([
        'tessif.transform.es2es', used_model]))

    if hook:
        es = hook(es)

    transform_ops = collections.defaultdict(dict)
    if trans_ops:
        for key, value in trans_ops.items():
            transform_ops[key] = value

    model_es = requested_model.transform(es, **transform_ops[used_model])
    end_time3 = getattr(time, time_measurement_tool[measurement])()
    transformation_time = end_time3 - start_time3  # time in seconds
    timing_results['transformation'] = round(transformation_time, 4)

    # 4) Execute simulation
    start_time4 = getattr(time, time_measurement_tool[measurement])()
    simulation_utility = getattr(simulate, '_'.join([used_model, 'from_es']))
    optimized_es = simulation_utility(model_es)
    end_time4 = getattr(time, time_measurement_tool[measurement])()
    simulation_time = end_time4 - start_time4  # time in seconds
    timing_results['simulation'] = round(simulation_time, 4)

    # 5) Create result utility
    start_time5 = getattr(time, time_measurement_tool[measurement])()
    requested_model_result_parsing_module = importlib.import_module('.'.join([
        'tessif.transform.es2mapping', used_model]))
    resultier = requested_model_result_parsing_module.AllResultier(
        optimized_es)
    end_time5 = getattr(time, time_measurement_tool[measurement])()
    post_processing_time = end_time5 - start_time5  # time in seconds
    timing_results['post_processing'] = round(post_processing_time, 4)

    # 6) Calculate the total time.
    timing_results["result"] = round(
        (reading_time + parsing_time + transformation_time + simulation_time +
         post_processing_time), 3)

    if only_total is True:
        timing_results = timing_results["result"]

    # Store the resultier into a file.
    resultier.dump(directory=os.path.dirname(path), filename='resultier.tsf')

    return timing_results


def trace_memory(path, parser, model, timeframe='primary', hook=None,
                 only_total=False, trans_ops=None):
    """
    Trace allocated memory.

    # Very similar in concept to stop_time()

    Parameters
    ----------
    path: str
        String representing the path the energy system data resides in.
        e.g. ``examples_dir/application/computational_comparison/fractal.xlsx``
    model: str
        String specifying one of the
        :attr:`~tessif.frused.defaults.registered_models` representing the
        :ref:`energy system simulation model <SupportedModels>` investigated.
    parser: :class:`~collections.abc.Callable`
        Functional used to read in and parse the energy system data.
        Usually one of the module functions found in :mod:`tessif.parse`.
    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used.
        One of ``'primary'``, ``'secondary'``, etc... by convention.
    hook: dict, None, default=None
        Dictionary keying :mod:`~tessif.frused.hooks` callables by its
        :attr:`registered name
        <tessif.frused.defaults.registered_models>`. See a use case in
        :ref:`AutoCompare_HH`.
    only_total: bool, default=False
        Set to true to only return the total result.
    trans_ops: dict, None, default=None
        Dictionary keying transformation options
        of a model by its :attr:`registered name
        <tessif.frused.defaults.registered_models>`. For example the
        :paramref:`~tessif.transform.es2es.ppsa.transform.forced_links` option
        when using :ref:`Models_Pypsa` as in::

            trans_ops={'pypsa': {
                'forced_links': ['Transformator_1', 'Transformator_2']}
            }

    Return
    ------
    results: dict
        Dictionary containing memory results in KiB keyed by the corresponding
        simulation steps that were investigated:

            - ``reading``
            - ``parsing``
            - ``transformation``
            - ``simulation``
            - ``post_processing``
    """

    used_model = None
    for internal_name, spellings in defaults.registered_models.items():
        if model in spellings:
            used_model = internal_name
            break

    memory_usage_results = dict()

    # 1) Read and parse in the tessif energy system data
    tracemalloc.start()
    esm = parser(path, timeframe=timeframe)
    reading_memory = tracemalloc.get_traced_memory()  # memory in KiB
    tracemalloc.stop()
    memory_usage_results['reading'] = reading_memory[1]

    # 2) Create the tessif energy system
    tracemalloc.start()
    es = tsf.transform(esm)
    parsing_memory = tracemalloc.get_traced_memory()  # memory in KiB
    tracemalloc.stop()
    memory_usage_results['parsing'] = parsing_memory[1]

    # 3) Transform the energy system into the requested model
    tracemalloc.start()
    requested_model = importlib.import_module('.'.join([
        'tessif.transform.es2es', used_model]))

    if hook:
        es = hook(es)

    transform_ops = collections.defaultdict(dict)
    if trans_ops:
        for key, value in trans_ops.items():
            transform_ops[key] = value

    model_es = requested_model.transform(es, **transform_ops[used_model])

    transformation_memory = tracemalloc.get_traced_memory()  # memory in KiB
    tracemalloc.stop()
    memory_usage_results['transformation'] = transformation_memory[1]

    # 4) Execute simulation
    tracemalloc.start()
    simulation_utility = getattr(simulate, '_'.join([used_model, 'from_es']))
    optimized_es = simulation_utility(model_es)
    simulation_memory = tracemalloc.get_traced_memory()  # memory in KiB
    tracemalloc.stop()
    memory_usage_results['simulation'] = simulation_memory[1]

    # 5) Create result utility
    tracemalloc.start()
    requested_model_result_parsing_module = importlib.import_module('.'.join([
        'tessif.transform.es2mapping', used_model]))
    resultier = requested_model_result_parsing_module.AllResultier(
        optimized_es)
    post_processing_memory = tracemalloc.get_traced_memory()  # memory in KiB
    tracemalloc.stop()
    memory_usage_results['post_processing'] = post_processing_memory[1]

    # 6) calculate total memory usage
    memory_usage_results['result'] = reading_memory[1] + parsing_memory[1] + \
                                     transformation_memory[1] + \
                                     simulation_memory[1] + \
                                     post_processing_memory[1]  # memory in KiB

    if only_total is True:
        memory_usage_results = memory_usage_results["result"]

    # Store the resultier into a file.
    resultier.dump(directory=os.path.dirname(path), filename='resultier.tsf')

    return memory_usage_results


class Comparatier:
    """
    Quickly compare any number of tessif's
    :ref:`supported energy supply system simulation models <SupportedModels>`.

    Parameters
    ----------
    path: str
        String representing the path the tessif energy system data is stored
        at. This :class:`energy system
        <tessif.model.energy_system.AbstractEnergySystem>` serves as scenario
        on which the :paramref:`~Comparatier.models` are compared.
    parser: :class:`~collections.abc.Callable`
        Functional used to read in and parse the energy system data.
        Usually one of the module functions found in :mod:`tessif.parse`.
    models: ~collections.abc.Sequence
        Sequence of strings naming the
        :attr:`~tessif.frused.defaults.registered_models` representing tessif's
        :ref:`supported energy supply system simulation models
        <SupportedModels>`.
    scaling: bool, default=False
        Bool indicating if scalability should be assessed using
        :func:`assess_scalability`.
    N: int, default=2
        Maximum number of minimum self similar energy system units the
        :attr:`self similar energy system
        <tessif.examples.data.tsf.py_hard.create_self_similar_energy_system>`
        is created with as part of the scalability assessment.
        assessment. Only used if :paramref:`~Comparatier.scaling` is ``True``.
    T: int, default=2
        Maximum number of timesteps used for scalability
        assessment. Only used if :paramref:`~Comparatier.scaling` is ``True``.
    hooks: dict, default=dict()
        Dictionary keying :mod:`~tessif.frused.hooks` callables by its
        :attr:`registered name
        <tessif.frused.defaults.registered_models>`. See a use case in
        :ref:`AutoCompare_HH`.
    trans_ops: dict, default=dict()
        Dictionary keying transformation options
        of a model by its :attr:`registered name
        <tessif.frused.defaults.registered_models>`. For example the
        :paramref:`~tessif.transform.es2es.ppsa.transform.forced_links` option
        when using :ref:`Models_Pypsa` as in::

            trans_ops={'pypsa': {
                'forced_links': ['Transformator_1', 'Transformator_2']}
            }

    Examples
    --------
    See :ref:`examples_auto_comparison` for a detailed example on how to use
    the :class:`Comparatier`.
    """

    def __init__(self, path, parser, models,
                 N=2, T=2, scaling=False,
                 storage_folder=None,
                 hooks=dict(),
                 trans_ops=dict()):

        self._path = path
        self._parser = parser
        self._scaling = scaling

        # 0) Make sure each of the passed models is a registered one and only
        #    appears once
        ms = self._match_registered_model_names(models)
        hooks = self._match_to_internal_model_name(hooks)
        transformation_options = self._match_to_internal_model_name(trans_ops)

        # turn the trans ops into a default dict for convenience access:
        tops = collections.defaultdict(dict)
        for key, value in transformation_options.items():
            tops[key] = value
        transformation_options = tops

        # sort the models alphabetically
        self._models = tuple(sorted((set(ms))))

        # 1) Create the tessif es
        self._tessif_es = tsf.transform(
            parser(path))

        # 2) As well as it's nxgrph representation
        self._analyzed_energy_system_graph = \
            self._tessif_es.to_nxgrph()

        # 3) Create a mapping of the optimized_energy_systems to be compared
        self._optimized_energy_systems = \
            self._generate_optimized_energy_systems(
                hooks=hooks,
                trans_ops=transformation_options)

        # 4) Create a mapping of the optimization results
        self._optimization_results = self._generate_optimization_results()

        # 5) Create the comparative optimization results
        self._comparative_results = self._generate_comparative_results()

        # 6) Create a mapping of the integrated component result graphs
        self._integrated_component_results_graphs = \
            self._generate_integrated_component_result_graphs()

        # 7) Create a mapping of the pearson correlation results
        # self._pearson_correlation_results = \
        #     self._create_pearson_correlation_results()

        # self._integrated_component_results_graph_charts = \
        #     self._generate_integrated_component_result_graph_charts()

        # 8) Create a mapping of the time measurement results
        self._time_measurement_results = \
            self._generate_time_measurement_results(
                hooks=hooks,
                trans_ops=transformation_options,
            )

        # 9) Create a mapping of the memory assessment results
        self._memory_usage_results = \
            self._generate_memory_usage_results(
                hooks=hooks,
                trans_ops=transformation_options,
            )

        # 10) Create a mapping of the integrated global results
        self._integrated_global_results = \
            self._generate_integrated_global_results()

        # 11) Create a mapping of the scalability results
        if self._scaling:
            self._scalability_results = \
                self._generate_scalability_results(
                    N=N, T=T, storage_folder=storage_folder)

    @property
    def baseline_es(self):
        """
        :class:`~tessif.model.energy_system.AbstractEnergySystem` serving as
        baseline scenario on which the :paramref:`~Comparatier.models` are
        compared.
        """
        return self._tessif_es

    @property
    def comparative_results(self):
        """
        :class:`ComparativeResultier` holding the results of each model
        keyed by component or by flow, depending on the results.
        """
        return self._comparative_results

    def create_lag_correlation(self, number_of_steps, component, flow):
        """
        Utility to compare the load results of 2 models by using a lag
        correlation.

        During the lag correlation analysis the load results of one model are
        shifted by up to :paramref:`~create_lag_correlation.maximum_lag` number
        of time steps to find out if a better correlation can be found.

        This would then imply that one model's load results would be shifted by
        a certain number of time steps, or in other words one model's load
        results might lag behind the other's.

        Parameters
        ----------
        maximum_lag: int
            Integer specifying the maximum lag to be assessed. Meaning during
            the lag correlation analysis the load results are shifted by 0 up
            to maximum_lag number of time steps to find out if a better
            correlation can be found.
            This would then imply that one model's load results would be
            shifted by a  certain number of time steps, or in other words one
            model's load results might lag behind the other's.

        See also
        --------
        :func:`lag_correlate`
        """

        lag_dict = dict()

        # iterate through the models
        for pos, model in enumerate(self._models):
            # the extract the flow result of the requested component
            # and map it to it's model name
            lag_dict[model] = self._optimization_results[
                model].node_outflows[component][flow]

        # create the timeseries df as requested by ``compare_N_timeseries``
        loads_df = pd.concat(
            lag_dict.values(), axis='columns', keys=lag_dict.keys())

        #  for lag
        #  creating a lag for testing the algorithm
        #  loads_df['ppsa'] = loads_df['ppsa'].shift(periods=26, fill_value=0)
        #  drop first n rows
        #  loads_df = loads_df.iloc[26:]
        #  drop last n rows
        #  loads_df = loads_df.iloc[:-26]

        # let the algorithm detect the load differences
        lag_corr = lag_correlate(
            timeseries=loads_df,
            number_of_steps=number_of_steps,

        )
        # return the result data frame

        return lag_corr

    @property
    def energy_systems(self):
        """
        :class:`~collections.abc.Mapping` of the optimized energy system
        models keyed by model name representing the compared energy supply
        system simulation model.
        """
        return self._optimized_energy_systems

    @property
    def graph(self):
        """
        :class:`networkx.DiGraph` object representing the energy system
        analyzed by this :class:`Comparatier`.
        """
        return self._analyzed_energy_system_graph

    @property
    def models(self):
        """ :class:`tuple` of the
        :attr:`registered models
        <tessif.frused.defaults.registered_models>` to compare. """
        return self._models

    @property
    def ICR_graphs(self):
        """
        Dictionary of :class:`networkx.DiGraph` objects keyed by model name.
        Representing the compared energy supply system simulation models and
        their :ref:`respective integrated component results
        <Integrated_Component_Results>`.

        Note
        ----
        To access the result data with which the graphs were plotted see
        :class:`networkx.Graph.nodes` and :attr:`networkx.Graph.edges` and
        :attr:`tessif.transform.nxgrph.Graph`.
        """
        return self._integrated_component_results_graphs

    def ICR_graph_charts(
            self,
            colored_by='name', legend=True, edge_width_scaling=10,
            **kwargs):
        """
        :class:`~collections.abc.Mapping` of :class:`matplotlib.figure.Figure`
        objects visualizing :class:`networkx.DiGraph` objects representing the
        energy system analyzed keyed by model name representing the compared
        energy supply system simulation models.

        The displayed graphs visualize following information:

            1. Edge length scales with flow costs
            2. Edge width scales with net flow rate
            3. Edge greyscale scales with co2 emission
            4. Node size scales width installed capacity
            5. Node filling scales width capacity factor

        Note
        ----
        Graph objects are accessible via :class:`Comparatier.ICR_graphs`.

        Results for generating the graph chart are stored within the respective
        graph object. (See :class:`networkx.Graph.nodes` and
        :attr:`networkx.Graph.edges` and
        :attr:`tessif.transform.nxgrph.Graph` for attribute accessing)

        Parameters
        ----------
        colored_by : {'component', 'name', 'carrier', 'sector'}, optional
            Specification on how to group nodes for coloring.
            (Respective node color dict provided by a
            :class:`~tessif.transform.es2mapping.base.ESTransformer` child)

            Default implementations are:

                - ``'component'``: Matches component to it's
                  :ref:`type <Models_Tessif_Concept_ESC>`
                - ``'name'``: Searches for keywords in str(node.uid.name)
                - ``'carrier'``: Searches for keywords in node.uid.carrier
                - ``'sector'``: Searches for keywords in node.uid.sector

            (Refer to :attr:`~tessif.frused.namedtuples.NodeColorGroupings` for
            namedtuple implementation)

        legend : bool, optional
            Whether to draw a legend or not. If ``True`` a legend is drawn.

        edge_width_scaling : ~numbers.Number
            Number with which the edge width is scaled. Useful for emphasizing
            edge width proportionality to net energy flow. Tweak this if node
            and figure size lead to edge widths too difficult to distinguish.

        kwargs :
            Kwargs are passed to
            :paramref:`tessif.visualize.nxgrph.draw_graph.kwargs`
            Useful for changing singular attributes of singular nodes as in::

                node_color={'Generator': 'red', }

            to color a node ``'red'`` of which the :attr:`str(node.uid)
            <tessif.frused.namedtuples.node_uid_styles>` representation yields
            ``'Generator'``

            Or as in::

                node_shape='o'

            To impose a circular :func:`shape
            <networkx.drawing.nx_pylab.draw_networkx_nodes>` on all nodes.
        """
        return self._draw_integrated_component_result_graph_charts(
            colored_by=colored_by, legend=legend,
            edge_width_scaling=edge_width_scaling,
            **kwargs)

    @property
    def integrated_global_results(self):
        """
        :class:`pandas.DataFrame` holding the singular value results (columns)
        for each model investigated (rows).

        Singular value results are:

            - ``costs``
            - ``emissions``
            - ``time``
            - ``memory``

        Optionally other global constraints can be formulated using the
        :attr:`~tessif.model.energy_system.AbstractEnergySystem.global_constraints`
        attribute of :class:`tessif's energy system
        <tessif.model.energy_system.AbstractEnergySystem>`

        This DataFrame holds the results for drawing the
        :attr:`global results chart <Comparatier.draw_global_results_chart>`.
        """
        return self._integrated_global_results

    @property
    def memory_usage_results(self):
        """
        :class:`collections.abc.Mapping` of :class:`dictionaries <dict>` of
        the time measurement results keyed by the compared energy supply system
        simulation models.
        """
        return self._memory_usage_results

    @property
    def path(self):
        """
        :class:`str` representing the path, the
        :attr:`~Comparatier.baseline_es` is stored.
        """
        return self._path

    @property
    def pearson_correlation(self):
        """
        :class:`dict` of :class:`pandas.DataFrame` objects holding the pearson
        correlation results of each component of each model pairing.

        Serves as main entry point for finding out which components to analyze
        more thoroughly.
        """
        return self._pearson_correlation_results

    @property
    def scalability_charts_2D(self):
        """
        :class:`~collections.abc.Mapping` of :class:`matplotlib.figure.Figure`
        objects visualizing the scalability of the compared energy supply
        system simulation models as array of curves.
        """
        if self._scaling:
            pass
        else:
            return "No scaling assessment performed"

    @property
    def scalability_charts_3D(self):
        """
        :class:`~collections.abc.Mapping` of :class:`matplotlib.figure.Figure`
        objects visualizing the scalability of the compared energy supply
        system simulation models as 3D field of (stacked) bars.
        """
        if self._scaling:
            scalability_charts_dict = dict()
            for model, scalability_results_tuple \
                    in self._scalability_results.items():
                scalability_charts_dict[model] = MemoryTime(
                    vis_compare.bar3D(
                        scalability_results_tuple.memory,
                        xyz_labels=('N', 'T', 'memory'),
                        title="Memory Usage Results of Model: '{}'".format(
                            model),
                    ),
                    vis_compare.bar3D(
                        scalability_results_tuple.time,
                        xyz_labels=('N', 'T', 'time',),
                        labels=self._time_measurement_results[model].keys(),
                        title="Time Measurement Results of Model: '{}'".format(
                            model),
                    )
                )
            return scalability_charts_dict
        else:
            return "No scaling assessment performed"

    @property
    def scalability_results(self):
        """
        :class:`~collections.abc.Mapping` of
        :attr:`~tessif.frused.namedtuples.MemoryTime` :class:`namedtuples
        <typing.NamedTuple>` keyed the compared energy supply system
        simulation models..
        """
        if self._scaling:
            return self._scalability_results
        else:
            return "No scaling assessment performed"

    @property
    def timing_results(self):
        """
        :class:`collections.abc.Mapping` of :class:`dictionaries <dict>` of
        the time measurement results keyed by the compared energy supply system
        simulation models.
        """
        return self._time_measurement_results

    @property
    def optimization_results(self):
        """
        :class:`~collections.abc.Mapping` of
        :class:`AllResultier<tessif.transform.es2mapping.base.ESTransformer>`
        objects holding the optimization results keyed by model name
        representing the compared energy supply system simulation model.
        """
        return self._optimization_results

    def calculate_load_differences(self, component, flow, threshold):
        """
        :class:`pandas.DataFrame` representing the detected load differences
        among models for the same component.

        The first column represents the average timeseries. The following
        columns are filled by the compared models' timeseries (ordered as
        they were passed) in which differences were recognized. The index of
        the DataFrame represents the points in time during the simulation
        where the differences occurred.

        Parameters
        ----------
        component: str
            The component's :class:`~tessif.frused.namedtuples.Uid` string
            representation (``str(component)``) of which the load differences
            among models is to be calculated.

        flow: str
            String representation of one of the :paramref:`component's
            <calculate_load_differences.component>` :attr:`flow interfaces
            <tessif.model.components.AbstractEsComponent.interfaces>` of which
            the load differences among models is to be calculated.

        threshold: float
            Float representing the relative deviation of the given
            :paramref:`component's <load_differences_charts.component>` load
            series from the mean of all components that
            is considered as threshold for identifying the series values as
            different.

            To recognize a series value as different from the others following
            statement has to be ``True``:

                :math:`|T(t)-\\overline{T}(t)| \geq \\text{threshold} \cdot \\overline{T}(t)`

        Return
        ------
        ldr: pandas.DataFrame
            DataFrame holding the load difference results.
        """

        loads_dict = dict()

        # iterate through the models
        for pos, model in enumerate(self._models):
            # the extract the flow result of the requested component
            # and map it to it's model name
            loads_dict[model] = self._optimization_results[
                model].node_outflows[component][flow]

        # create the timeseries df as requested by ``compare_N_timeseries``
        loads_df = pd.concat(
            loads_dict.values(), axis='columns', keys=loads_dict.keys())

        # for lag
        # creating a lag for testing the algorithm
        # loads_df['ppsa'] = loads_df['ppsa'].shift(periods=26, fill_value=0)
        # drop first n rows
        # loads_df = loads_df.iloc[26:]
        # drop last n rows
        # loads_df = loads_df.iloc[:-26]

        # let the algorithm detect the load differences
        load_differences = compare_N_timeseries(
            timeseries=loads_df,
            threshold=threshold)

        # return the result data frame
        return load_differences

    def calculate_statistical_load_differences(self, component, flow,
                                               normalized=True, type='mean',
                                               reference=""):
        """
        :class:`pandas.DataFrame` representing the statistical load differences
        among models for the same component. For example error values.

        Parameters
        ----------
        component: str
            The component's :class:`~tessif.frused.namedtuples.Uid` string
            representation (``str(component)``) of which the load differences
            among models is to be calculated.

        flow: str
            String representation of one of the :paramref:`component's
            <calculate_load_differences.component>` :attr:`flow interfaces
            <tessif.model.components.AbstractEsComponent.interfaces>` of which
            the load differences among models is to be calculated.

                :math:`|T(t)-\\overline{T}(t)| \geq \\text{threshold} \cdot \\overline{T}(t)`

        normalized: bool
            Determine the returned values to be normalized or not.

            default = "True"

        type: str
            Defines the type of normalization. Statistical (values) can be
            normalized in different matters. Two options by 'mean' or by the
            timeseries 'range':

            default = "mean"

        reference: str
            Define the reference model to be used as a reference point to
            determine the statistical values. (average, omf, ppsa....)

        Return
        ------
        ldr: pandas.DataFrame
            DataFrame holding the statistical load difference results. The
            index (rows) represent the calculated value names/types, the
            columns the respective model names.
        """

        loads_dict = dict()

        # iterate through the models
        for pos, model in enumerate(self._models):
            # the extract the flow result of the requested component
            # and map it to it's model name
            loads_dict[model] = self._optimization_results[
                model].node_outflows[component][flow]

        # create an additional dummy for testing
        # loads_dict['test'] = loads_dict[list(loads_dict.keys())[0]]

        # create the timeseries df as requested by ``compare_N_timeseries``
        loads_df = pd.concat(
            loads_dict.values(), axis='columns', keys=loads_dict.keys())

        # for lag
        # creating a lag for testing the algorithm
        # loads_df['ppsa'] = loads_df['ppsa'].shift(periods=26, fill_value=0)
        # drop first n rows
        # loads_df = loads_df.iloc[26:]
        # drop last n rows
        # loads_df = loads_df.iloc[:-26]

        # let the algorithm detect the load differences
        load_differences = statistically_compare_N_timeseries(
            timeseries=loads_df, normalized=normalized, type=type,
            reference=reference)

        # return the result data frame
        return load_differences

    def draw_global_results_chart(
            self,
            results_to_compare=('costs', 'emissions', 'time', 'memory'),
            title='default'
    ):
        """
        `Bar plot
        <https://matplotlib.org/3.3.1/api/_as_gen/matplotlib.pyplot.bar.html>`_
        for comparing the numerical results.

        Comparing one or all of

            - costs
            - emissions
            - simulation time
            - memory usage

        of the compared energy supply system simulation models.

        Utilizes :meth:`tessif.visualize.compare.bar`.

        Parameters
        ----------
        results_to_compare: ~collections.abc.Container
            Container holding the strings of the numerical results to compare.
            Any combination of the following values is recognized:

                - ``costs``
                - ``emissions``
                - ``time``
                - ``memory``

        title: str, default='default'
            String representing the plot title.
            If default is used title results in::

                "Integrated Global Results of Models '{self._models}'."

        Return
        ------
        ldc: matplotlib.figure.Figure
            Generated load difference chart
        """
        igrs = self._integrated_global_results

        if title == 'default':
            title = "Integrated Global Results of Models: {}".format(
                self._models)
        else:
            title = title

        fig = igrs.plot(kind='bar', title=title).figure

        return fig

    def draw_pearson_self_corr_grid(self):
        """correlation matrix
        Create a correlation matrix for each model to analyse
        interrelationships within each model.

        Return
        ------
        ldc: matplotlib.figure.Figures
            Return a correlation matrix for each model.
        """

        # get the model keyed all loads dataframes:
        all_loads_dict_raw = self.comparative_results.all_loads

        # removing default multi index of all_loads_dict_raw
        for key, dataframes in all_loads_dict_raw.items():
            dataframes.columns = dataframes.columns = [
                ' -> '.join(col) for col in dataframes.columns]
            dataframes.fillna(0, inplace=True)

        # dropping all columns that are filled with zeros
        all_loads_dict_drop_zero = {}
        for key, dataframes in all_loads_dict_raw.items():
            all_loads_dict_drop_zero[key] = dataframes.loc[
                                            :, (dataframes != 0).any(axis=0)]

        # check if all values in dataframes are the same if so: change first
        # value to zero to avoid NaN in correlation Matrix

        def unique_cols(df):
            a = df.to_numpy()  # df.values (pandas<0.24)
            return (a[0] == a).all(0)

        all_loads_dict_unique = {}

        for key, dataframes in all_loads_dict_drop_zero.items():
            all_loads_dict_unique[key] = unique_cols(dataframes)

            for key_1, array in all_loads_dict_unique.items():

                for i in range(len(array)):
                    if array[i] == True:
                        all_loads_dict_drop_zero[key].iloc[:, i].iloc[0] = 0

                else:
                    pass

        all_loads_dict = copy.deepcopy(all_loads_dict_drop_zero)

        # magic is happening pearson correlation
        all_loads_dict_corr_self = {}
        for key, dataframe in all_loads_dict.items():
            all_loads_dict_corr_self[key] = round(dataframe.corr(), 2)

        for key, dataframe in all_loads_dict_corr_self.items():
            fig = vis_compare.pearson_self_comparison(
                pearson_df=dataframe, titel_dic_key=key)

        return fig

    def draw_load_differences_chart(
            self, component, flow, threshold, title='default',
            x_axis_data=None, labels=[], colors=[], where='post',
            x_axis_label='x'):
        """
        :class:`matplotlib.figure.Figure` object visualizing the load
        differences among models for the same component im comparison
        to their mean.

        Parameters
        ----------
        component: str
            The component's :class:`~tessif.frused.namedtuples.Uid` string
            representation (``str(component)``) of which the load differences
            among models is to be calculated.

        flow: str
            String representation of one of the :paramref:`component's
            <calculate_load_differences.component>` :attr:`flow interfaces
            <tessif.model.components.AbstractEsComponent.interfaces>` of which
            the load differences among models is to be calculated.

        threshold: float
            Float representing the relative deviation of the given
            :paramref:`component's <load_differences_chart.component`> load
            series from the mean of all components that
            is considered as threshold for identifying the series values as
            different.

            To recognize a series value as different from the others following
            statement has to be ``True``:

                :math:`|T(t)-\\overline{T}(t)| \geq \\text{threshold} \cdot \\overline{T}(t)`

        title: str, default='default'
            String representing the plot title.
            If default is used title results in::

                "Time step resolved analysis of {component}'s flow to '{flow}'"

        x-axis_data: ~collections.abc.Iterable, None, default=None
        Iterable representing the x-axis data as in::

            x = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)
            x = range(13)
            x = pd.date_range(pd.datetime.now().date(), periods=13, freq='H')

            Note
            ----
            This parameter is only needed when
            :paramref:`~component_loads.step.data` is **NOT** supplied as a
            :class:`pandas.DataFrame`. It is ignored otherwise.

        labels: ~collections.abc.Iterable, default=[]
            Iterable of strings labeling the data sets in
            :paramref:`component_loads.step.data`.

            If not empty a legend entry will be drawn for each item.

            Must be of equal length or longer than
            :paramref:`~component_loads.step.data`.

            Note
            ----
            This parameter is only needed when
            :paramref:`~component_loads.step.data` is **NOT** supplied as a
            :class:`pandas.DataFrame`. It is ignored otherwise.

        colors: ~collections.abc.Iterable, default=[]
            Iterable of color specification string coloring the data sets in
            :paramref:`~component_loads.step.data`.

            If not empty each plot will be colord accordingly.
            Otherwise, matplotlib's default color rotation will be used.

            List of colors stated must be greater or equal the stacks to be
            plotted.

        x-axis_label: str, None, default='x'
            String labeling the x-axis.

            Use ``None`` to not plot any axis labels.

        where: str, default = 'post'
            # https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.step.html

            Define where the steps should be placed:

           'pre': The y value is continued constantly to the left from every x
            position, i.e. the interval (x[i-1], x[i]] has the value y[i].

           'post': The y value is continued constantly to the right from every
           x position, i.e. the interval [x[i], x[i+1]) has the value y[i].

            'mid': Steps occur half-way between the x positions.

        Returns
        -------
        ldc: matplotlib.figure.Figure
            Generated load difference chart
        """

        if title == 'default':
            title = "Time step resolved analysis of {}'s flow to '{}'".format(
                str(component), str(flow))
        else:
            title = title

        ax = component_loads.step(
            data=self.calculate_load_differences(
                component=component,
                flow=flow,
                threshold=threshold),
            title=title,
            colors=colors,
            where=where,
            x_axis_label=x_axis_label,
            labels=labels,
            x_axis_data=x_axis_data)

        return ax

    def draw_statistical_load_differences_chart(
            self, component, flow, normalized=True, title='default'):
        """
        :class:`matplotlib.figure.Figure` object visualizing the statistical
        results on comparing one component's load data among models.

        Parameters
        ----------
        component: str
            The component's :class:`~tessif.frused.namedtuples.Uid` string
            representation (``str(component)``) of which the load differences
            among models is to be calculated.

        flow: str
            String representation of one of the :paramref:`component's
            <calculate_load_differences.component>` :attr:`flow interfaces
            <tessif.model.components.AbstractEsComponent.interfaces>` of which
            the load differences among models is to be calculated.

        normalized: bool
            bool operator determine the returned values to be normalized or not
            default = "True"

        title: str, default='default'
            String representing the plot title.
            If default is used title results in::

                "Statistical analysis of {component}'s flow to '{flow}'"
        """

        if title == 'default':
            title = "Statistical analysis of {}'s flow to '{}'".format(
                str(component), str(flow))
        else:
            title = title

        ax = self.calculate_statistical_load_differences(
            component=component, flow=flow, normalized=normalized).plot(
            kind='bar', title=title if title else None)
        plt.tight_layout()

        ax.set_title(title, fontsize=12)
        plt.tick_params(labelsize=12)

        for p in ax.patches:
            """
            https://stackoverflow.com/questions/23591254/python-pandas-matplotlib-annotating-labels-above-bar-chart-columns
            """
            ax.annotate("%.4f" % p.get_height(),
                        (p.get_x() + p.get_width() / 2, p.get_height() / 2),
                        ha='center',
                        va='center', xytext=(0, 0), textcoords='offset points',
                        rotation=90, size=12)

        return ax.figure

    def separate_data(
            self, pearson_threshold=0.7, mae_threshold=0.05,
            threshold_moving_average=10, title="", condition="all",
            reference=""):
        """
        tool for  visualizing  and separating the differences of the individual
        time series of the components/flows from all the models studied,
        based on the previously selected condition. For the visualization the
        data are smooth before because only a trend should become visible

        See also
        --------
        https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
        https://en.wikipedia.org/wiki/Mean_absolute_error
        https://en.wikipedia.org/wiki/Moving_average

        Parameters
        ----------
        title: str
            String representing the plot title.

        pearson_threshold: float ; default = 0.7
            Defines at which value the person correlation should be undercut to
            be considered as a significant difference. Large values mean high
            linear equality

        mae_threshold: float ; default = 0.05
            Defines at which value the mean absolute error should be exceeded
            to be considered as a significant difference. Small values mean
            that there are hardly any differences in the values of the time
            series.

        threshold_moving_average: int

        condition: str ; default = "all"
            determines according to which condition the data should be filtered
                  " condition_1"   or 'very_interesting'                  == High interest / significantly different.
                  " condition_2"   or 'interesting_high_mae_low_pearson'  == Medium interest / boderline significantly
                  " condition_2_3" or 'all_from_interest'                == Medium interest / boderline significantly
                  " condition_3"   or 'interesting_low_mae_high_pearson'  == Medium interest / boderline significantly
                  " condition_4"   or 'not_interesting'                   == Least interesting / most likely of no interest:
                  " condition_5"   or "all"                              == shows the complete data set (no condition)

        reference: str
            Defines the reference model to be used as a reference point to
            determine the statistical values. (average, omf, ppsa....)

        Returns
        -------
        pd.Dataframe
            Contains the values of the pearson correlation and the mean
            absolute errors of the selected condition.

        matplotlib.figure.Figure
            Visualization of the components determined by the algorithm.
        """

        # STEP 0: filtering data
        # get the model keyed all loads dataframes:
        all_loads_dict_raw = self.comparative_results.all_loads

        # removing default multi index of all_loads_dict_raw
        for key, dataframes in all_loads_dict_raw.items():
            dataframes.columns = dataframes.columns = [
                ' flows to '.join(col) for col in dataframes.columns]

        all_loads_dict_raw_copy = copy.deepcopy(all_loads_dict_raw)

        # components and flow that only exist in all models
        common_cols = list(
            set.intersection(
                *(set(c) for c in all_loads_dict_raw.values())))
        # only compare components and flow that exist in all models and
        # replacing possible NaNs with zeros
        all_loads_dict_no_col_fill_na = {}
        for key, dataframes in all_loads_dict_raw.items():
            all_loads_dict_no_col_fill_na[key] = dataframes[
                common_cols].fillna(0)

        # logging whats dropped
        for key, dataframes in all_loads_dict_no_col_fill_na.items():

            dropped_flows = all_loads_dict_raw_copy[key].columns.difference(
                all_loads_dict_no_col_fill_na[key].columns
            )
            dropped_flows = list(dropped_flows)

            if dropped_flows:
                logger.info(40 * "-")
                logger.info("During statistical analysis")
                logger.info(f"{key} had to drop following flows:")
                for flow in dropped_flows:
                    logger.info(flow)

        # dropping all columns that are filled with zeros
        all_loads_dict_drop_zero = {}
        for key, dataframes in all_loads_dict_no_col_fill_na.items():
            all_loads_dict_drop_zero[key] = dataframes.loc[
                                            :, (dataframes != 0).any(axis=0)]

        all_loads_dict = copy.deepcopy(all_loads_dict_drop_zero)

        # create reference model
        if reference == "" or "average":
            reference_model = create_average_model(all_loads_dict_drop_zero)

        else:
            reference_model = all_loads_dict[reference]

        # STEP 1: pearson correlation

        pearson_results = pearson_list(all_loads_dict, reference=reference)

        # STEP 2:  mae list
        all_loads_dict_mae = {}
        for key, dataframes in all_loads_dict_drop_zero.items():
            all_loads_dict_mae[key] = dataframes.reindex_like(
                reference_model).fillna(0, downcast='infer')

        mae_results = mae_list(all_loads_dict_mae, reference=reference)

        # STEP 3: select flows and components

        autoselected_comps = autoselect(pearson_df=pearson_results,
                                        mae_df=mae_results,
                                        mae_threshold=mae_threshold,
                                        pearson_threshold=pearson_threshold,
                                        desired_condition=condition)

        # STEP 4:printing out results

        if autoselected_comps.empty:

            print('Can´t draw any flows or components -> empty Dataframe')

        else:

            def moving_average(data, w):
                """
                algorithm that smooths the time series with the moving average
                Parameters
                ----------
                data: pd.Dataframe
                    Dataframe containing components and flows of the selected
                    condition.  NICHT GANZ SICHER

                w : int
                    degree of moving average
                Returns
                -------
                pd.Dataframe
                    contains the smoothed data NiCHT GANZ SICHER
                """

                result = pd.DataFrame(index=data.index)
                for column in data:
                    result[column] = data[column].rolling(
                        window=w, center=True, min_periods=1).mean()

                return result

            # smoothing data
            for key, dataframes in all_loads_dict.items():
                all_loads_dict[key] = moving_average(
                    dataframes, threshold_moving_average)

            # merging all dataframes to one
            data_comp_df = pd.concat(
                all_loads_dict.values(),
                axis=1,
                keys=all_loads_dict.keys()
            )

            # swap column levels, so the software specifier is on top
            data_comp_df = data_comp_df.swaplevel(0, 1, axis="columns")

            # sort dataframe columns alphabetically for software
            data_comp_df = data_comp_df.sort_index(axis="columns")

            # selecting the autoselected comps to be visualized
            data_comp_df_final = data_comp_df[autoselected_comps.index]

            all_loads_draw = vis_compare.comp_plot(
                data_comp_df_final, title=title)

        return autoselected_comps, all_loads_draw

    def _generate_comparative_results(self):
        """Utility for creating a ComparativeResultier object."""
        return ComparativeResultier(
            all_resultiers=self.optimization_results)

    def _generate_integrated_component_result_graphs(self):
        """
        Utility for creating a dict of networkx graph representing
        the integrated component results.
        """
        graphs = dict()

        for model, es in self._optimized_energy_systems.items():
            requested_model_result_parsing_module = importlib.import_module(
                '.'.join(['tessif.transform.es2mapping', model]))

            hybridier = requested_model_result_parsing_module.ICRHybridier(es)

            grph = nxt.Graph(hybridier)

            graphs[model] = grph

        return graphs

    def _draw_integrated_component_result_graph_charts(
            self, colored_by='name', legend=True, edge_width_scaling=10,
            **kwargs):
        """
        Utility for creating a dict of networkx graph representing
        the integrated component results.
        """
        charts = dict()

        for model, es in self._optimized_energy_systems.items():

            requested_model_result_parsing_module = importlib.import_module(
                '.'.join(['tessif.transform.es2mapping', model]))

            hybridier = requested_model_result_parsing_module.ICRHybridier(
                es, colored_by=colored_by)

            for key, value in hybridier.edge_data()['edge_width'].items():
                hybridier.edge_data()['edge_width'][key] = (
                    edge_width_scaling * value)

            if legend:
                if colored_by == 'name':
                    legends = [
                        getattr(hybridier.legend_of_nodes, colored_by),
                        hybridier.legend_of_edge_styles]

                else:
                    legends = [
                        hybridier.legend_of_node_styles,
                        getattr(hybridier.legend_of_nodes, colored_by),
                        hybridier.legend_of_edge_styles]

            else:
                legends = None

            nxv.draw_graph(
                grph=self._integrated_component_results_graphs[model],
                formatier=hybridier,
                layout='neato',
                draw_fency_nodes=True,
                legends=legends,
                title="Integrated Component Results Graph of Model: '{}'".format(
                    model),
                **kwargs,
            )

            figure = plt.gcf()

            charts[model] = figure

        return charts

    def _generate_integrated_global_results(self):
        """
        Utility for extracting: ``costs, emissions, time and memory`` out of
        the model resultiers and time/memory result mappings, to bundle them
        in a singular :class:`pandas.DataFrame` for each model.
        """
        integrated_global_results = dict()

        for model, es in self._optimized_energy_systems.items():
            model_result_parsing_module = importlib.import_module(
                '.'.join(['tessif.transform.es2mapping', model]))

            resultier = model_result_parsing_module.IntegratedGlobalResultier(
                es)

            # 1) extract global simulation results (costs, emissions)
            integrated_global_results[model] = resultier.global_results

            # 2) extract simulation metadata (time and memory)
            # Turn dict into a namedtuple for better data frame handling:
            trs = SimulationProcessStepResults(
                **self._time_measurement_results[model])

            # this is only down to allow pandas.DataFrame.plot utility to work.
            # In an ideal world there would exist a function in
            # visualize.compare that draws
            # a normal bar for singular value and a stacked bar for tuples
            # sum all but last
            trs = trs.result
            #
            # round seconds down to 1 digit:

            trs = _round_decimals_down(trs, 1)

            integrated_global_results[model]['time (s)'] = trs

            # memory = self._memory_usage_results[model]
            mrs = SimulationProcessStepResults(
                **self._memory_usage_results[model])

            # this is only down to allow pandas.DataFrame.plot utility to work.
            # In an ideal world there would exist a function in
            # visualize.compare that draws
            # a normal bar for singular value and a stacked bar for tuples
            mrs = mrs.result
            #
            #
            # transform bytes to MB and round to first digit:
            mrs = _round_decimals_down(mrs * 1e-6, 1)

            integrated_global_results[model]['memory (MB)'] = mrs

        # # create an additional dummy for testing
        # integrated_global_results['test'] = integrated_global_results[
        #     list(integrated_global_results.keys())[0]]

        icr_df = pd.DataFrame.from_dict(
            data=integrated_global_results, orient='columns')

        return icr_df

    def _generate_optimization_results(self):
        """Utility for creating a dict of the optimization results.
        """
        optimized_energy_system_results = dict()

        for model, es in self._optimized_energy_systems.items():
            requested_model_result_parsing_module = importlib.import_module(
                '.'.join(['tessif.transform.es2mapping', model]))

            resultier = requested_model_result_parsing_module.AllResultier(
                es)

            optimized_energy_system_results[model] = resultier

        return optimized_energy_system_results

    def _generate_optimized_energy_systems(
            self, hooks=dict(), trans_ops=dict()):
        """Utility for creating dict of the optimized energy systems keyed to
        the registered model name.
        """
        optimized_energy_systems = dict()

        for registered_model_name in sorted(self._models):

            # figure out model transformer
            model_transformer = importlib.import_module('.'.join([
                'tessif.transform.es2es', registered_model_name]))

            # check if a hook needs to be executed
            if hooks:

                # if so iterated over all stated hooks
                for model, hook in hooks.items():
                    # if a match is found...
                    if model == registered_model_name:
                        # ... execute the hook ...
                        es = hook(es=self._tessif_es)
                        # ... and break out of the loop ...
                        break
                else:
                    # ... if not, then assign the original es
                    es = self._tessif_es
            # if no hooks where declared, just use the original es
            else:
                es = self._tessif_es

            # transform the model accordingly
            # check if a transformation option needs to be respected:
            if trans_ops:
                for model, options in trans_ops.items():
                    if model == registered_model_name:
                        model_es = model_transformer.transform(
                            es, **options)
                    else:
                        model_es = model_transformer.transform(es)
            else:
                model_es = model_transformer.transform(es)

            # optimize the model
            simulation_utility = getattr(simulate, '_'.join(
                [registered_model_name, 'from_es']))
            optimized_es = simulation_utility(model_es)

            # create a respective dict entry
            optimized_energy_systems[registered_model_name] = optimized_es

        return optimized_energy_systems

    def _generate_memory_usage_results(self, hooks=dict(), trans_ops=dict()):
        """
        Implement an algorithm that uses tessif.analyze.trace_memory on all
        the models the Comparatier was initialized with to generate a result
        dictionary containing the trace_memory results keyed by model name.
        """
        memory_usage_results = dict()

        for model in self._models:
            memory_usage_results[model] = trace_memory(
                path=self._path,
                parser=self._parser,
                model=model,
                hook=hooks[model] if model in hooks else None,
                trans_ops=trans_ops,
            )

        return memory_usage_results

    def _generate_scalability_results(self, N, T, storage_folder):
        """
        Implement an algorithm that uses tessif.analyze.assess_scalability on
        all the modes the Comparatier was initialized with to generate a
        results dictionary containing the assess_scalability results keyed
        by model name and time/memory
        """

        scalability_results = dict()
        for model in self._models:
            scalability_results[model] = assess_scalability(
                N=N,
                T=T,
                storage_folder=storage_folder,
                model=model)

        return scalability_results

    def _generate_time_measurement_results(
            self, hooks=dict(), trans_ops=dict()):
        """
        Implement algorithm that uses tessif.analyze.stop_time() on all the
        models the Comparatier was initialized with and generates a result
        dictionary containing the stop_time results keyed by model name.
        """
        time_measurement_results = dict()
        for model in self._models:
            time_measurement_results[model] = stop_time(
                path=self._path,
                parser=self._parser,
                model=model,
                hook=hooks[model] if model in hooks else None,
                trans_ops=trans_ops,
            )

        return time_measurement_results

    def _match_registered_model_names(self, models):
        """
        Utility for creating a tuple of the registered model names to compare.

        Parameters
        ----------
        models: ~collections.abc.Iterable
            Iterable of strings naming the
            :attr:`~tessif.frused.defaults.registered_models` representing
            tessif's :ref:`supported energy supply system simulation models
            <SupportedModels>`.
        """
        registered_models = list()
        for model in models:
            # figure out registered model name
            for internal_name, spellings in defaults.registered_models.items():
                if model in spellings:
                    registered_models.append(internal_name)
                    continue

        return tuple(registered_models)

    def _match_to_internal_model_name(self, dct):
        """ Utility to match stated model names to internal names."""
        matched_content = dict()
        for model, content in dct.items():
            # figure out registered model name
            for internal_name, spellings in defaults.registered_models.items():
                if model in spellings:
                    matched_content[internal_name] = content
                    continue

        return matched_content


class ComparativeResultier:
    """
    Utility for creating comparative dataframes out of optimization results.

    Uses :attr:`Comparatier.optimization_results` to create `multi indexed
    <https://pandas.pydata.org/pandas-docs/stable/user_guide/advanced.html>`_
    :class:`~pandas.DataFrame` objects storing the results of the same
    :class:`base energy system
    <tessif.model.energy_system.AbstractEnergySystem>` simulated using
    different :ref:`models <SupportedModels>` as it is done by using the
    :class:`Comparatier` to :ref:`auto compare <examples_auto_comparison>`
    those different models.

    Parameters
    ----------
    all_resultiers: dict
        Dictionairy of strings naming the
        :attr:`~tessif.frused.defaults.registered_models` representing tessif's
        :ref:`supported energy supply system simulation models
        <SupportedModels>` keying the :class:`results
        <tessif.transform.es2mapping.omf.AllResultier>` of those models.

        A mapping of this kind is returned by
        :attr:`Comparatier.optimization_results`.

    Examples
    --------
    Comparing the models :ref:`oemof <Models_Oemof>` and
    :ref:`pypsa <Models_Pypsa>` on
    :attr:`tessif's fully parameterized working example (fpwe)
    <tessif.examples.data.tsf.py_hard.create_fpwe>`:

    0. Silence the :mod:`~tessif.frused.spellings` module:

        >>> import tessif.frused.configurations as configurations
        >>> configurations.spellings_logging_level = 'debug'

    1. Create the :class:`Comparatier` object for automated comparison:

        >>> import tessif.analyze, tessif.parse, os
        >>> from tessif.frused.paths import write_dir

        >>> comparatier = tessif.analyze.Comparatier(
        ...     path=os.path.join(
        ...         write_dir, 'tsf', 'es_to_compare.hdf5'),
        ...     parser=tessif.parse.hdf5,
        ...     models=('oemof', 'pypsa'),
        ... )

    2. Get the :class:`ComparativeResultier` object using the comparatier.:

        >>> comparative_resultier = comparatier.comparative_results
        >>> print(type(comparative_resultier))
        <class 'tessif.analyze.ComparativeResultier'>

    3. Refer to the :ref:`detailed use case examples
       <examples_auto_comparison_comparative>`.
    """

    def __init__(
            self, all_resultiers,
            results_to_compare='all',
    ):

        self._all_resultiers = all_resultiers

        self._results_to_compare = {
            'capacities': 'node_installed_capacity',
            'costs': 'edge_specific_flow_costs',
            'cvs': 'node_characteristic_value',
            'emissions': 'edge_specific_emissions',
            'expansion_costs': 'node_expansion_costs',
            'loads': 'node_load',
            'net_energy_flows': 'edge_net_energy_flow',
            'original_capacities': 'node_original_capacity',
            'socs': 'node_soc',
            'weights': 'edge_weight',
        }

        self._create_comparative_component_results()

    @property
    def all_loads(self):
        """
        Dictionary of multi-indexed dataframes of all load results of all
        components keyed inside the dict by the respective
        :attr:`software specifier
        <tessif.frused.defaults.registered_models>`

        Top-level index represents the individual components, while the
        second-level index represent the respective outflow targets.

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

        Warning
        -------
        Depending on the energy system, this might be a huge dataframe. Hence,
        a lazy evaluation approach is chosen.

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_loads>` for accessing the
        all-loads results.

        """
        # create a 2 level multi-indexed df for each (node, outflow) df of a
        # singular model
        all_loads_dict = dict()
        for model, resultier in self._all_resultiers.items():
            df = pd.concat(
                [resultier.node_outflows[node]
                    for node in sorted(resultier.nodes)],
                keys=[node for node in sorted(resultier.nodes)],
                axis='columns')
            all_loads_dict[model] = df

        return all_loads_dict

    @property
    def all_socs(self):
        """DataFrame of all state of charges of all storages.

        DataFrame is indexed by component names and columned by respective
        :attr:`software specifiers
        <tessif.frused.defaults.registered_models>`

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_socs>` for accessing the
        all_capacities results.
        """
        all_socs = dict()

        if list(self._all_resultiers.values())[0].node_soc.keys():
            for software, resultier in self._all_resultiers.items():

                df = pd.concat(
                    [resultier.node_soc[node]
                     for node in resultier.node_soc],
                    keys=resultier.node_soc.keys(),
                    axis='columns')
                all_socs[software] = df

            all_socs_dtf = pd.concat(
                [all_socs[software] for software in all_socs],
                keys=all_socs.keys(),
                axis='columns')

        else:
            all_socs_dtf = pd.DataFrame()

        return all_socs_dtf

    @property
    def all_capacities(self):
        """DataFrame of all installed capacities post optimization.

        DataFrame is indexed by component names and columned by respective
        :attr:`software specifiers
        <tessif.frused.defaults.registered_models>`

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_caps>` for accessing the
        all_capacities results.
        """
        all_capacities_dict = dict()
        for software, resultier in self._all_resultiers.items():
            # write all component capacities into a pandas series
            ser = pd.Series(
                [resultier.node_installed_capacity[node]
                    for node in sorted(resultier.nodes)],
                index=[node for node in sorted(resultier.nodes)],
            )

            # deal with components that have more than one capacity (e.g. chps)
            # by concatenating component name and capacity specifier
            ser = ser.apply(pd.Series).stack()
            ser.index = [f"{prim} {sec}" if sec != 0 else prim
                         for prim, sec in ser.index]
            all_capacities_dict[software] = ser

        all_caps = pd.concat(
            all_capacities_dict.values(),
            keys=all_capacities_dict.keys(),
            axis="columns",
        )

        return all_caps

    @property
    def all_original_capacities(self):
        """DataFrame of all installed capacities pre optimization.

        DataFrame is indexed by component names and columned by respective
        :attr:`software specifiers
        <tessif.frused.defaults.registered_models>`

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_orig_caps>` for accessing the
        all_original_capacities results.
        """
        all_capacities_dict = dict()
        for software, resultier in self._all_resultiers.items():
            # write all component capacities into a pandas series
            ser = pd.Series(
                [resultier.node_original_capacity[node]
                    for node in sorted(resultier.nodes)],
                index=[node for node in sorted(resultier.nodes)],
            )

            # deal with components that have more than one capacity (e.g. chps)
            # by concatenating component name and capacity specifier
            ser = ser.apply(pd.Series).stack()
            ser.index = [f"{prim} {sec}" if sec != 0 else prim
                         for prim, sec in ser.index]
            all_capacities_dict[software] = ser

        all_caps = pd.concat(
            all_capacities_dict.values(),
            keys=all_capacities_dict.keys(),
            axis="columns",
        )

        return all_caps

    @property
    def all_net_energy_flows(self):
        """DataFrame of all net energy flows post optimization.

        DataFrame is indexed by component names and columned by respective
        :attr:`software specifiers
        <tessif.frused.defaults.registered_models>`

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_net_flows>` for accessing the
        all-loads results.
        """
        all_net_energy_flows_dict = dict()
        for software, resultier in self._all_resultiers.items():
            # write all component capacities into a pandas series
            ser = pd.Series(
                [resultier.edge_net_energy_flow[edge]
                    for edge in sorted(resultier.edges)],
                index=[edge for edge in sorted(resultier.edges)],
            )

            all_net_energy_flows_dict[software] = ser

        all_net_energy_flows = pd.concat(
            all_net_energy_flows_dict.values(),
            keys=all_net_energy_flows_dict.keys(),
            axis="columns",
        )

        return all_net_energy_flows

    @property
    def all_costs_incurred(self):
        """DataFrame of all net energy flows post optimization.

        DataFrame is indexed by component names and columned by respective
        :attr:`software specifiers
        <tessif.frused.defaults.registered_models>`

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_costs_incurred>` for accessing the
        all-loads results.
        """
        all_costs_incurred_dict = dict()
        for software, resultier in self._all_resultiers.items():
            # write all component capacities into a pandas series
            ser = pd.Series(
                [resultier.edge_total_costs_incurred[edge]
                    for edge in sorted(resultier.edges)],
                index=[edge for edge in sorted(resultier.edges)],
            )

            all_costs_incurred_dict[software] = ser

        all_costs_incurred = pd.concat(
            all_costs_incurred_dict.values(),
            keys=all_costs_incurred_dict.keys(),
            axis="columns",
        )

        return all_costs_incurred

    @property
    def all_emissions_caused(self):
        """DataFrame of all net energy flows post optimization.

        DataFrame is indexed by component names and columned by respective
        :attr:`software specifiers
        <tessif.frused.defaults.registered_models>`

        Example
        -------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_all_emissions_caused>` for accessing the
        all-loads results.
        """
        all_emissions_caused_dict = dict()
        for software, resultier in self._all_resultiers.items():
            # write all component capacities into a pandas series
            ser = pd.Series(
                [resultier.edge_total_emissions_caused[edge]
                    for edge in sorted(resultier.edges)],
                index=[edge for edge in sorted(resultier.edges)],
            )

            all_emissions_caused_dict[software] = ser

        all_emissions_caused = pd.concat(
            all_emissions_caused_dict.values(),
            keys=all_emissions_caused_dict.keys(),
            axis="columns",
        )

        return all_emissions_caused

    @property
    def capacities(self):
        """
        Return a mapping of the installed capacity results among models keyed
        by component uid.

        Note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_capacities>` for accessing the
        capacity results.
        """
        return self._capacities

    @property
    def costs(self):
        """
        Return a mapping of the flow cost results among models keyed by
        component edges.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_costs>` for accessing the
        cost results.
        """
        return self._costs

    @property
    def cvs(self):
        """
        Return a mapping of the characteristic value results among models
        keyed by component uid.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_cvs>` for accessing the
        characteristic value results.
        """
        return self._cvs

    @property
    def emissions(self):
        """
        Return a mapping of the flow emission results among models keyed by
        component edges.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not aN edge**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_emissions>` for accessing the
        emissions results.
        """
        return self._emissions

    @property
    def expansion_costs(self):
        """
        Return a mapping of the costs for expanding a nodes installed capacity.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_expansion_costs>` for accessing
        the emissions results.
        """
        return self._expansion_costs

    @property
    def loads(self):
        """
        Return a mapping of the load results among models keyed by component
        uid.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_loads>` for accessing the
        loads results.
        """
        return self._loads

    @property
    def net_energy_flows(self):
        """
        Return a mapping of the net energy flow results among models keyed by
        component edges.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not aN edge**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_nets>` for accessing the
        net energy flow results.
        """
        return self._net_energy_flows

    @property
    def original_capacities(self):
        """
        Return a mapping of the installed capacity prior to optimization among
        models keyed by component uid.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_original_capacities>` for
        accessing the original capacity results.
        """
        return self._original_capacities

    @property
    def socs(self):
        """
        Return a mapping of the state of charge results among models keyed by
        component uid.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not a Node**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_socs>` for accessing the
        state of charge results.
        """
        return self._socs

    @property
    def weights(self):
        """
        Return a mapping of the edge weight results among models keyed by
        component edges.

        note
        ----
        Entries of value **NaN** are to be interpreted as **Not aN edge**.
        Whereas ``None`` is a :mod:`tessif default <tessif.frused.defaults>`.

        Examples
        --------
        Refer to the :ref:`detailed comparatier example
        <examples_auto_comparison_comparative_weights>` for accessing the
        edge weight results.
        """
        return self._weights

    def _create_comparative_component_results(self):
        """ Utility for creating the comparative load results."""

        results = collections.defaultdict(
            lambda: collections.defaultdict(list))

        # iterate over every model's AllResultier
        for resultier in self._all_resultiers.values():
            # and of each Resultier over its nodes
            for node in resultier.nodes:
                # and for each result to compare, over its interface:
                for key, interface in self._results_to_compare.items():

                    # check if it's a node interface:
                    if node in getattr(resultier, interface):
                        # if yes, aggregate its node results into a list
                        results[key][node].append(
                            getattr(resultier, interface)[node])

            # and of each Resultier over its edges
            for edge in resultier.edges:
                # and for each result to compare, over its interface:
                for key, interface in self._results_to_compare.items():

                    # check if it's an edge interface:
                    if edge in getattr(resultier, interface):
                        # if yes, aggregate its edge results into a list
                        results[key][edge].append(
                            getattr(resultier, interface)[edge])

        # concat results across models
        for rtype, dct in results.copy().items():
            for energy_system_entity, result_list in dct.copy().items():

                # concat dataframe results
                if all([isinstance(result, pd.DataFrame)
                        for result in result_list]):
                    df = pd.concat(
                        result_list,
                        keys=self._all_resultiers.keys(),
                        axis='columns')
                    df.index.name = None
                    df = df.sort_index()  # sort dataframe for index
                    results[rtype][energy_system_entity] = df

                # concat series results
                elif all([isinstance(result, pd.Series)
                          for result in result_list]):

                    df = pd.concat(
                        result_list,
                        keys=self._all_resultiers.keys(),
                        axis='columns')
                    # name the dataframe
                    df.columns.name = energy_system_entity
                    df.index.name = None
                    df = df.sort_index()  # sort dataframe for index
                    results[rtype][energy_system_entity] = df

                # concat all other results
                else:
                    # enforce index and results to be the same length
                    for i in range(
                            len(self._all_resultiers) - len(result_list)):
                        result_list.append(None)
                        # result_list = pd.Series(result_list)

                    ser = pd.Series(
                        data=result_list,
                        index=self._all_resultiers.keys(),
                        name=energy_system_entity,
                    )

                    ser = ser.sort_index()  # sort series by index

                    # superseded by documenting NaN as Not a Node
                    # replace numpy nans because they are non-existent
                    # 'energy_system_entity's:
                    #
                    # if ser.dtype == 'float':
                    #     ser = ser.fillna('non-existent')

                    results[rtype][energy_system_entity] = ser

        for attribute_name in self._results_to_compare.keys():
            setattr(self, f'_{attribute_name}', dict(results[attribute_name]))


def _round_decimals_down(number, decimals=1):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor
