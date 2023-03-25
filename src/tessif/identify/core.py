# src/tessif/identify/core.py
"""Tessif module providing the core identification utilities."""
import abc
import logging
import operator

import pandas as pd

from tessif.identify.auxilliary import parse_reference_df

logger = logging.getLogger(__name__)


class Identificier(abc.ABC):
    """Identificaiton Base Class.

    Identificaiton algorithm houses in :attr:`Identificier.cluster_interest`
    which needs to be overriden by child specific implementations.

    Parameters
    ----------
    data
        Result data to be analyzed for significant differences.

    conditions_dict: dict, None, default=None
        Dictionairy keying :class:`container(s) <collections.abc.Container>`
        of dicts by the respective cluster labels "high", "medium" and "low".
        The dictionairies inside the tuples need to have following keywords:

            - ``thres`` specyfying the threshold used
            - ``oprt`` specifying the :mod:`operator` used.

        Used to cluster :paramref:`~Identificier.data` by category/cluster
        label.

    reference: str, None, default=None
        Defines the reference results to be used for calculating the
        statistical error values and pearson correlation coeficients.

        In case ``None`` is used (default), the dataframes average is used as
        returned by :func:`average_timevarying_dataframe_results`.
    """

    def __init__(self, data, conditions_dict, reference=None):

        self.data = data
        self._conditions = conditions_dict
        self._reference = parse_reference_df(data, reference)

        # core utility: cluster component flows by interest
        self._clustered_interest = self.cluster_interest()

        # map respective results
        self.map_interest_results(data)

    @property
    def of_high_interest(self):
        """Node uid representations identified as of ``high interest``."""
        dtf = self.clustered_interest
        dtf = dtf[dtf == "high"].stack().unstack()
        return dtf

    @property
    def high(self):
        """Alias for :attr:`of_high_interest`."""
        return self.of_high_interest

    @property
    def high_interest_results(self):
        """Inter component results identified as highly interesting."""
        return self._high_interest_results

    @property
    def of_medium_interest(self):
        """Node uid representations identified as of ``medium interest``."""
        dtf = self.clustered_interest
        dtf = dtf[dtf == "medium"].stack().unstack()
        return dtf

    @property
    def medium(self):
        """Alias for :attr:`of_medium_interest`."""
        return self.of_medium_interest

    @property
    def medium_interest_results(self):
        """Inter component results identified as mediumly interesting."""
        return self._medium_interest_results

    @property
    def of_low_interest(self):
        """Node uid representations identified as of ``low interest``."""
        return dict(self._of_low_interest)

    @property
    def low(self):
        """Alias for :attr:`of_low_interest`."""
        dtf = self.clustered_interest
        dtf = dtf[dtf == "low"].stack().unstack()
        return dtf

    @property
    def low_interest_results(self):
        """Inter component results identified as lowly interesting."""
        return self._low_interest_results

    @property
    def cluster_conditions(self):
        """Dictionairy of clustering conditions used."""
        return self._conditions

    @property
    def clustered_interest(self):
        """Inter component results clustered by interest."""
        return self._clustered_interest

    @property
    def reference(self):
        """Reference Model Used for Ientifications."""
        return self._reference

    @abc.abstractmethod
    def cluster_interest(self):
        """Cluster inter component results by interest."""

    @abc.abstractmethod
    def map_interest_results(self, data):
        """Map data to identified interest categories."""


def cluster(values, conditions_dict):
    """Cluster value(s) on condition(s).

    Uses a dcitionairy of conditions utilizing pythons
    :mod:`operators <operator>`.

    Parameters
    ----------
    values: ~collections.abc.Container
        Container of :class:`number(s) <numbers.Number>` on which the cluster
        conditions are checked on.
    conditions_dict: dict
        Dictionairy keying :class:`container(s) <collections.abc.Container>`
        of dicts by the respective cluster labels. The dictionairies inside
        the tuples need to have following keywords:

            - ``thres`` specyfying the threshold used
            -  ``oprt`` specifying the :mod:`operator` used.

    Returns
    -------
    ~collections.abc.Hashable
        Dictionairy key specifying the cluster. Usually a string or a number.

    Examples
    --------
    Using a single value condition check with 2 categories/clusters. Note that
    on single value conditions both, the value itself as well as the inner
    conditions dict must be Containers. Hence the trailing ``,`` to turn both
    into tuples.

    >>> values = [(9000,), (9001,), (42,)]
    >>> conditions = {
    ...     "Its over 9000!": ({"oprt": "gt", "thres": 9000},),
    ...     "Nope": ({"oprt": "le", "thres": 9000},),
    ... }

    >>> for value in values:
    ...     print(cluster(value, conditions))
    Nope
    Its over 9000!
    Nope

    Multiple values and conditions (inner dict tuple length) can be used. Their
    length must match however:

    >>> values = [
    ...     ([0, 1], "high"),
    ...     ([1, 1],  "medium1"),
    ...     ([0, 0],  "medium2"),
    ...     ([1, 0],  "low"),
    ... ]

    >>> # first condition = pcc, second condition = nmae
    >>> conditions = {
    ...     "high": ({"oprt": "lt", "thres": 0.7}, {"oprt": "ge", "thres": 0.1}),
    ...     "medium1": ({"oprt": "ge", "thres": 0.7}, {"oprt": "ge", "thres": 0.1}),
    ...     "medium2": ({"oprt": "lt", "thres": 0.7}, {"oprt": "lt", "thres": 0.1}),
    ...     "low": ({"oprt": "ge", "thres": 0.7}, {"oprt": "lt", "thres": 0.1}),
    ... }

    >>> for value_pairing in values:
    ...     print(cluster(value_pairing[0], conditions))
    high
    medium1
    medium2
    low
    """

    for cluster, conditions in conditions_dict.items():
        if all(
                [
                    getattr(operator, cond["oprt"])(values[pos], cond["thres"])
                    for pos, cond in enumerate(conditions)
                ]
        ):
            return cluster
    else:
        logger.warning("Value could not be clustered.")
        return None
