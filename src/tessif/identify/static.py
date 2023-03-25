# src/tessif/identify/core.py
"""Identify submodule providing identification utilities for static results."""

import functools
import pandas as pd

from tessif.identify.core import (
    cluster,
    Identificier,
)
from tessif.identify.calculate import calc_ardiffs, calc_reldiffs


class StaticIdentificier(Identificier):
    """Identify components of which the static results differ between softwares.


    Components are identified using following logic:

    Parameters
    ----------
    data: pandas.DataFrame
        Pandas DataFrame holding the static results. Indexed by
        components/flows, columned by softwares.

        DataFrames of this format can be obtained using
        :attr:`tessif.analyze.ComparativeResultier.all_capacities` or
        :attr:`tessif.analyze.ComparativeResultier.all_original_capacities` or
        :attr:`tessif.analyze.ComparativeResultier.all_net_energy_flows` for
        example.

    conditions_dict: dict, default=None
        Dictionairy describing the clustering categories as strings and the
        respective threshold above which a difference between softwares is
        considered to fall within this cluster.

        The dict keys :class:`container(s) <collections.abc.Container>`
        of dicts by the respective cluster labels "high", "medium" and "low".
        The dictionairies inside the tuples need to have following keywords:

        If ``None``, following default is used::

            conditions_dict = {
                "high": (
                    {"oprt": "ge", "thres": 0.3,
                    {"oprt": "ge", "thres": 0.3},
                ),
                "medium": (
                    {"oprt": "lt", "thres": 0.3},
                    {"oprt": "ge", "thres": 0.1},
                ),
                "low": (
                    {"oprt": "lt", "thres": 0.1},
                    {"oprt": "lt", "thres": 0.1},
                ),
            }

        which translates to:

            - high:   0.3 <= delta
            - medium: 0.1 <= delta < 0.3
            - low:    0.0 <= dleta < 0.1

    reference: str, None, default=None
        Defines the reference results to be used for calculating the
        absolute relative deviation between softwares.

        In case ``None`` is used (default), the dataframes average is used as
        returned by :func:`average_timevarying_dataframe_results`.
    """

    def __init__(self, data, conditions_dict=None, reference=None):
        if conditions_dict is None:
            conditions_dict = {
                "high": (
                    {"oprt": "ge", "thres": 0.3},
                    {"oprt": "ge", "thres": 0.3},
                ),
                "medium": (
                    {"oprt": "lt", "thres": 0.3},
                    {"oprt": "ge", "thres": 0.1},
                ),
                "low": (
                    {"oprt": "lt", "thres": 0.1},
                    {"oprt": "lt", "thres": 0.1},
                ),
            }

        super().__init__(
            data=data,
            conditions_dict=conditions_dict,
            reference=reference,
        )

    @property
    def relative_deviations(self):
        """Relative deviations between data and reference."""
        return self._rel_devs

    def cluster_interest(self):
        """Cluster inter component results by interest."""
        # transform cells into tuples of identical values based on number of
        # conditions

        # calculate relative deviations
        self._rel_devs = calc_reldiffs(self.data, self.reference)

        # buffer for increased readability
        num_of_conds = len(tuple(self.cluster_conditions.values())[0])
        rel_devs = self._rel_devs.abs()  # use abs reldiffs for clustering
        dtf = pd.DataFrame(
            {
                col: zip(*tuple(rel_devs[col] for _i in range(num_of_conds)))
                for col in rel_devs.columns
            },
            index=rel_devs.index,
        )

        clustered_df = dtf.applymap(
            # use functools partial to provide additional paramss to "cluster"
            functools.partial(
                cluster,
                conditions_dict=self.cluster_conditions,
            ),
        )

        return clustered_df

    def map_interest_results(self, data):
        """Map data to identified interest categories."""
        for cluster in ["high", "medium", "low"]:
            clustered_results = data.loc[getattr(self, cluster).index]
            setattr(self, f"_{cluster}_interest_results", clustered_results)
