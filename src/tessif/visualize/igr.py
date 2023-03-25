# src/tessif/visualize/igr.py
"""Module to conveniently plot Integrated Global Results."""
import plotly.express as px


def _plot_mpl_bar_figures(df, **kwargs):
    return df.plot(kind='bar', **kwargs).figure


def _plot_plexp_bar_figures(df, **kwargs):
    return px.bar(df, **kwargs)


def plot(igr_df, draw_util="mpl", ptype="bar", plt_config=None, **kwargs):
    """Plot integrated global results.

    Parameters
    ----------
    igr_df: :class:`pandas.DataFrame`
        DataFrame holding the IGR values. With softwares (e.g.
        ["omf", fine", ...]) as columns and result values (e.g.
        ["capex", "emissions", ...]) as index.
    draw_util: str
        String specifying the drawing utility. Currently supported are:

            - ``"mpl"`` using matplotlib via :attr:`pandas.DataFrame.plot`
            - ``"plexp"`` using ``plotly.express`` via
              `plotly.express.bar
              <https://plotly.com/python-api-reference/generated/plotly.express.bar>`_
    ptype: str
        String specifying the plot type. Currently only ``"bar"`` is supported
        for drawing bar plots.
    plt_config: dict, None, default=None
        Dict specifying :paramref:`draw_util` and :paramref:`ptype` specific
        kwargs. Get aggregated and overriden by :paramref:`plot.kwargs`.
    kwargs
        Keyword arguments for conveniently overriding
        :paramref:`plot.plt_config`. Useful in the case
        :paramref:`plot.plt_config` is hardcoded somewhere, or provided by an
        external api. Does not alter the orginal :paramref:`plot.plt_config`
        dict.

    Returns
    -------
    dict
        Dictionairy keyed by ``"costs"`` and ``"non_costs"`` holding figures of
        the respective :paramref:`plot.draw_util` tools.

    Examples
    --------
    >>> # preparing the data:
    >>> igrs = {
    ...     "omf": {
    ...         "total costs": 42289118239,
    ...         "opex": 734140364,
    ...         "capex": 41554977878,
    ...         "emisisons": 250000,
    ...     },
    ...     "ppsa": {
    ...         "total costs": 37727776780,
    ...         "opex": 823007841,
    ...         "capex": 36904768288,
    ...         "emisisons": 265508,
    ...     },
    ...     "fine": {
    ...         "total costs": 42289118279,
    ...         "opex": 734140364,
    ...         "capex": 41554976118,
    ...         "emisisons": 250000,
    ...     },
    ... }
    >>> import pandas as pd
    >>> df = pd.DataFrame(igrs)

    Using :attr:`pandas.DataFrame.plot`:

    >>> mpl_config = {
    ...     "title": "Integrated Global Results Relative to 'Oemof'",
    ...     "ylabel": "",
    ...     "xlabel": "Result Values",
    ...     "rot": 0,
    ... }

    >>> from tessif.visualize import igr
    >>> figures = igr.plot(
    ...     igr_df=df,
    ...     plt_config=mpl_config,
    ...     draw_util="mpl",
    ...     ptype="bar",
    ... )

    >>> # uncomment when reusing this example
    >>> # figures["costs"].show()
    >>> # figures["non_costs"].show()

    .. image:: images/mpl_igr_costs.png
        :align: center
        :alt: Matplotlib IGR "Costs" example bar chart

    .. image:: images/mpl_igr_noncosts.png
        :align: center
        :alt: Matplotlib IGR "Non Costs" example bar chart

    Using `plotly.express.bar
    <https://plotly.com/python-api-reference/generated/plotly.express.bar>`_:

    >>> plexp_config = {
    ...     "title": "Integrated Global Results",
    ...     "barmode": "group",
    ...     "text_auto": True,
    ... }

    >>> from tessif.visualize import igr
    >>> figures = igr.plot(
    ...     igr_df=df,
    ...     plt_config=plexp_config,
    ...     ptype="bar",
    ...     draw_util="plexp",
    ... )

    >>> # uncomment when reusing this example
    >>> # figures["costs"].show()
    >>> # figures["non_costs"].show()

    .. image:: images/plexp_igr_costs.png
        :align: center
        :alt: Plotly express IGR "Costs" example bar chart

    .. image:: images/plexp_igr_noncosts.png
        :align: center
        :alt: Plotly express IGR "Non Costs" example bar chart
    """
    if plt_config is None:
        plt_config = {}

    plt_config = {**plt_config, **kwargs}
    # split the dataframe index into costs and non-costs (
    # i.e. secondary constraints like emissions, ressources, land_use etc.)
    result_category_index = {}
    result_category_index["non_costs"] = [
        ind for ind in igr_df.index if not any(
            [cost_label in ind for cost_label in ["costs", "opex", "capex"]])]

    result_category_index["costs"] = [
        ind for ind in igr_df.index if ind not in result_category_index[
            "non_costs"]]

    plotting_tool = {
        ("mpl", "bar"): _plot_mpl_bar_figures,
        ("plexp", "bar"): _plot_plexp_bar_figures
    }

    # create the figures
    figures = {}
    for result_category, columns in result_category_index.items():
        filtered_kwargs = {}
        for key, value in plt_config.items():
            if not isinstance(value, dict):
                filtered_kwargs[key] = value
            else:
                filtered_kwargs[key] = value[result_category]

        df = igr_df.loc[columns]
        if result_category == "costs":
            df.index.name = "Cost Results"
        else:
            df.index.name = "Secondary Constraint Results"
        figures[result_category] = plotting_tool[(draw_util, ptype)](
            df=df,
            **filtered_kwargs
        )

    return figures
