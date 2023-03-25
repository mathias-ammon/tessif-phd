# src/tessif/identify/timevarying.py
"""Identify submodule holding identification tools for timevarying results."""
import functools
import pandas as pd

from tessif.identify.core import (
    cluster,
    Identificier,
)

from tessif.identify.auxilliary import (
    filter_mutually_inclusive_columns,
    list_mutually_inclusive_columns,
    list_not_mutually_inclusive_columns,
    parse_reference_df,
)

from tessif.identify.calculate import (
    calc_evs,
    calc_corrs,
    calc_ardiffs,
)

from tessif.identify.timeframes import (
    significant_differences
)


class TimevaryingIdentificier(Identificier):
    """Identify components of which the flow results differ between softwares.


    Flows are identified using following logic:

        1. High interest / significantly different:

            - CORR < :paramref:`~Identificier.corr`
              (e.g. ``CORR < 0.7``)
            - ERROR_VALUE > :paramref:`~Identificier.error_value`:
              (e.g. ``ERROR_VALUE > 0.1``)

        2. Medium interest / borderline significantly different:

            - CORR < :paramref:`~Identificier.corr`
              (e.g. ``CORR < 0.7``)
            - ERROR_VALUE < :paramref:`~Identificier.error_value`:
              (e.g. ``ERROR_VALUE < 0.1``)

           And:

            - CORR > :paramref:`~Identificier.corr`
              (e.g. ``CORR > 0.7``)
            - ERROR_VALUE > :paramref:`~Identificier.error_value`:
              (e.g. ``ERROR_VALUE > 0.1``)

        3. Low Interest / not significantly different:

            - CORR > :paramref:`~Identificier.corr`
              (e.g. ``CORR > 0.7``)
            - ERROR_VALUE < :paramref:`~Identificier.error_value`:
              (e.g. ``ERROR_VALUE < 0.1``)

    Parameters
    ----------
    data: dict
        Dictionairy of multiindexed dataframes of all of all timevarying
        results of all components keyed inside the dict by the respective
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

        Usually returned by something like
        :attr:`tessif.analyze.ComparativeResultier.all_loads`.

    error_value: str
        String abbrevating the error value calculated. Currently supported are:

            - ``nmae`` for ``Normalized Mean Average Error`` (default)
            - ``nmbe`` for ``Normalized Mean Biased Error``
            - ``nrmse`` for ``Normalized Root Mean Square Error``

    error_value_threshold: float, default = 0.1
        Threshold value used for clustering data interest. Clustering is done
        according to :attr:`cluster_conditions`.

    correlation : {'pearson', 'kendall', 'spearman'} or callable
        Method of correlation:

        - pearson : standard correlation coefficient
        - kendall : Kendall Tau correlation coefficient
        - spearman : Spearman rank correlation
        - callable: callable with input two 1d ndarrays
          and returning a float.

    correlation_threshold: float, default = 0.7
        Threshold value used for clustering data interest. Clustering is done
        according to :attr:`cluster_conditions`.

    conditions_dict: dict, None, default=None
        Dictionairy keying :class:`container(s) <collections.abc.Container>`
        of dicts by the respective cluster labels "high", "medium" and "low".
        The dictionairies inside the tuples need to have following keywords:

            - ``thres`` specyfying the threshold used
            - ``oprt`` specifying the :mod:`operator` used.

        If ``None`` is used, following default conditions are applied::

            conditions = {
                "high": (
                    {"oprt": "lt", "thres": correlation_coefficient_threshold},
                    {"oprt": "ge", "thres": error_value_threshold},
                 ),
                "medium1": (
                    {"oprt": "ge", "thres": correlation_coefficient_threshold},
                    {"oprt": "ge", "thres": error_value_threshold},
                ),
                "medium2": (
                    {"oprt": "lt", "thres": correlation_coefficient_threshold},
                    {"oprt": "lt", "thres": error_value_threshold},
                ),
                "low": (
                    {"oprt": "ge", "thres": correlation_coefficient_threshold},
                    {"oprt": "lt", "thres": error_value_threshold},
                ),
            }

    reference: str, None, default=None
        Defines the reference results to be used for calculating the
        statistical error values and pearson correlation coeficients.

        In case ``None`` is used (default), the dataframes average is used as
        returned by :func:`average_timevarying_dataframe_results`.
    """

    def __init__(
            self,
            data,
            error_value="nmae",
            error_value_threshold=0.1,
            correlation="pearson",
            correlation_threshold=0.7,
            conditions_dict=None,
            reference=None,
    ):

        # init condition-related timevarying specific members
        self._corr_thres = correlation_threshold
        self._ev_thres = error_value_threshold

        if conditions_dict is None:
            conditions_dict = {
                "high": (
                    {"oprt": "lt", "thres": self._corr_thres},
                    {"oprt": "ge", "thres": self._ev_thres},
                ),
                "medium1": (
                    {"oprt": "ge", "thres": self._corr_thres},
                    {"oprt": "ge", "thres": self._ev_thres},
                ),
                "medium2": (
                    {"oprt": "lt", "thres": self._corr_thres},
                    {"oprt": "lt", "thres": self._ev_thres},
                ),
                "low": (
                    {"oprt": "ge", "thres": self._corr_thres},
                    {"oprt": "lt", "thres": self._ev_thres},
                ),
            }

        # init not-condition-related timevarying specific members
        self._ref_arg = reference
        self._softwares = tuple(data.keys())
        self._error_value = error_value
        self._corr = correlation

        # identify / seperate the result data
        self._mutual_components = list_mutually_inclusive_columns(
            data.values())
        self._non_mutual_components = list_not_mutually_inclusive_columns(
            data.values())

        # narrow down data set by only including mutually inclusive components
        self._inspected_loads = dict(
            zip(
                data.keys(),
                filter_mutually_inclusive_columns(data.values()),
            )
        )

        # calculate error values
        self._error_values = calc_evs(
            dataframes=self._inspected_loads.values(),
            labels=self._inspected_loads.keys(),
            reference=reference,
            error=error_value,
        )

        # calculate correlations
        self._corrs = calc_corrs(
            dataframes=self._inspected_loads.values(),
            method=self._corr,
            labels=self._inspected_loads.keys(),
            reference=reference,
            fillna=0,
        )

        # super class handles clustering and mapping interest
        super().__init__(
            data=data,
            conditions_dict=conditions_dict,
            reference=reference,
        )

        # only those timeframes wehre delta > threshold
        self._map_interest_timeframes()
        self._map_interest_averaged_results()

    @property
    def mutuals(self):
        """Mutual components between softwares"""
        return self._mutual_components

    @property
    def non_mutuals(self):
        """Non mutual components between softwares"""
        return self._non_mutual_components

    @property
    def error_value(self):
        """String specifying the error value used."""
        return self._error_value

    @property
    def correlation(self):
        """String specyfying the correlation used."""
        return self._corr

    @property
    def error_value_threshold(self):
        """Error value threshold used."""
        return self._ev_thres

    @property
    def correlation_coefficient_threshold(self):
        """Correlation value threshold used."""
        return self._corr_thres

    @property
    def error_values(self):
        """Calculated Normalized Medium Average Errors."""
        return self._error_values

    @property
    def corrs(self):
        """Calculated Pearson Correlation Coefficients."""
        return self._corrs

    @property
    def high_interest_averaged_results(self):
        """Mean and high interest results differing more than threshold."""
        return self._high_interest_averaged_results

    @property
    def medium_interest_averaged_results(self):
        """Mean and medium interest results differing more than threshold."""
        return self._medium_interest_averaged_results

    @property
    def low_interest_averaged_results(self):
        """Mean and low interest results differing more than threshold."""
        return self._low_interest_averaged_results

    @property
    def high_interest_timeframes(self):
        """Significant results identified as highly interesting."""
        return self._high_interest_timeframes

    @property
    def medium_interest_timeframes(self):
        """Significant results identified as medium interesting."""
        return self._medium_interest_timeframes

    @property
    def low_interest_timeframes(self):
        """Significant results identified as not very interesting."""
        return self._low_interest_timeframes

    def cluster_interest(self):
        """Cluster inter component results by interest."""
        # aggregate coorelation coefficient results df and
        # error value results df into one single df of tuples
        df = pd.DataFrame(
            {
                col: zip(self.corrs[col], self.error_values[col])
                for col in self.corrs.columns
            },
            index=self.corrs.index,
        )

        clustered_df = df.applymap(
            # use functools partial to provide additional params to "cluster"
            functools.partial(
                cluster,
                conditions_dict=self.cluster_conditions,
            ),
        )

        # merge medium1 and medium2 tags to "medium"
        clustered_df = clustered_df.replace(
            to_replace=["medium1", "medium2"],
            value=["medium", "medium"],
        )

        return clustered_df

    def map_interest_results(self, data):
        """Map data to identified interest categories."""
        for cluster in ["high", "medium", "low"]:
            clustered_results = dict()
            for flow in tuple(getattr(self, cluster).index):
                dtf = pd.concat(
                    [data[software][flow] for software in self._softwares],
                    keys=self._softwares,
                    axis="columns",
                )
                clustered_results[flow] = dtf

            setattr(self, f"_{cluster}_interest_results", clustered_results)

    def _map_interest_timeframes(self):
        for cluster in ["high", "medium", "low"]:
            clustered_results = dict()

            for flow in tuple(getattr(self, cluster).index):
                flow_results = getattr(
                    self, f"_{cluster}_interest_results")[flow].copy()

                identified_timeframes = significant_differences(
                    data=flow_results,
                    reference=self._ref_arg,
                    neighs=True,
                    threshold=self._ev_thres,
                )
                clustered_results[flow] = identified_timeframes

            setattr(self, f"_{cluster}_interest_timeframes", clustered_results)

    def _map_interest_averaged_results(self):
        for cluster in ["high", "medium", "low"]:
            clustered_results = dict()

            for flow in tuple(getattr(self, cluster).index):
                data = getattr(
                    self, f"_{cluster}_interest_results")[flow].copy()

                # parse reference
                ref = parse_reference_df(data, self._ref_arg)

                # calculate relative deviations
                method = "ardiffs"
                if method == "ardiffs":
                    relative_deviations = calc_ardiffs(data, ref)
                else:
                    relative_deviations = method(data, ref)

                # identify only those significant
                relative_significant_differences = relative_deviations[
                    relative_deviations > self._ev_thres]

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

                # identified_timeframes = significant_differences(
                #     data=data,
                #     reference=self._ref_arg,
                #     neighs=True,
                #     threshold=self._ev_thres,
                # )
                # clustered_results[flow] = identified_timeframes
                clustered_results[flow] = all_averaged

            setattr(self, f"_{cluster}_interest_averaged_results", clustered_results)
