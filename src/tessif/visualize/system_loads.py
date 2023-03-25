"""Powerful bar drawing utility based on :func:`matplotlib.pyplot.bar`.

While it is designed to quickly draw arbitrarily complex bar charts
representing energy system loads, it can be used as standalone drawing utility
for really just any bar chart.

Algorithm is build on a triple nested list engine which is able to visualize
plot data grouped as ``[category [subcategory [data]]]``

Default coloring uses :attr:`tessif.frused.themes.colors` and
:attr:`~tessif.frused.themes.cmaps`.
"""

# tessif/visualize/system_loads.py
import collections
from itertools import cycle
import importlib
from math import copysign
from warnings import warn

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import numpy as np

import ittools
from tessif.transform.es2es import (
    infer_registered_model,
    infer_software_from_es,
)
from tessif.frused import configurations, spellings, themes

esci = spellings.energy_system_component_identifiers


def bars(loads, index=[],  # basic plot data
         # category level
         category_labels=[], category_colors=[], category_hatches=[],
         labels=[], colors=[], hatches=[],  # subcategory level
         dticks=1, offset=0, fmt='%a. %m-%d',  # plot formatting
         ylabel="Power in MWh", **kwargs):
    r"""Draw a sophisticated bar plot for visualizing energy system load data.

    Works on a simple yet powerfull nested list engine. Able to automatically
    draw a simple bar chart or a full fledged energy system load analysis split
    by major and minor categorization options. Minor categorization uses triple
    nested lists, whereas major parameters are represented as double layer
    nested lists. See parameters for details. Calls
    :func:`matplotlib.pyplot.bar`.

    Parameters
    ----------
    loads : :class:`~collections.abc.Iterable`
        Iterable of numbers i.e. :class:`list`, :class:`pandas.Series` or
        :class:`pandas.DataFrame` etc.
        To be plotted data will be transformed into a triple nested list as::

            [  # Category Level
                [  # Subcategory Level
                    [  # Data Level
                    ]
                ]
            ]

        - Upper most level:

            [Sector 1, ..., Sector N]

        - In between:

            [Subcategory 1, ..., Subcategory N] for each category

        - Lowest level:

            [Load at timestep 1, .... load at timestep N]
            for each subcategory

        Any nesting depth <= 3 can be handled and will be interpreted as
        stated above

    index: :class:`~collections.abc.Iterable`, default = []
        Iterable of integers or entries on which `strftime
        <https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior>`_
        can be called.

        Use it to:

            - plot data over unequidistant indices (equidistant as in
              ``range(0, len(laod), dticks)`` e.g [3, 8, 20]
            - Print date/time/date/time strings as ticklabels,
              e.g: ``list(pd.DataFrame.index)``

    category_labels: :class:`~collections.abc.Iterable`, default=[]
        Iterable container of strings used to label category level entries.
        i.e.: ``['Power', 'Heat', 'Mobility']``

        Beware:

            - ``len(category_labels)`` !>= number of categories
            - Use ``None`` to **not** draw any major labels.
            - Use default to tag the n-th category by 'Category N'

    category_colors: :class:`~collections.abc.Iterable`, default=[]
        Iterable container of color strings used to color major categories
        when drawing the major category plot.
        i.e.: ``['yellow', 'red' 'blue']``

        Beware:

            - ``len(category_colors)`` !>= number of categories
            - Use ``None`` to use **matplotlib's default coloring cycle**.
            - Use ``[]`` (default) to invoke the
              :attr:`tessif.frused.themes.colors` coloring.

    category_hatches: :class:`~collections.abc.Iterable`, default=[]
        iterable container of hatch strings used to hatch major categories
        when drawing the major category plot. i.e.: ``['/', '\ ' '+']``

        Supported patterns:
        ``{'/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*'}``

        Beware:

            - ``len(category_hatches)`` !>= number of categories
            - Use ``None`` to **not** hatch at all
            - Use ``[]`` (default) to invoke the
              :attr:`tessif.frused.themes.hatches` hatching

    labels: :class:`~collections.abc.Iterable`, default=[]
        iterable container of strings used to tag subcategory level entries.
        i.e : ``[['PV', 'Wind'], ['Gas', 'ST'], ['Diesel', 'Petrol']]``
        Nest entries intuitively the way the loads are nested.

        Beware:

            - ``len(labels)`` !>= number of categories
            - ``len(nested_labels)`` !>= number of respective subcategory
              entries
            - Use ``None`` to not tag any subcategory level entries
            - Use ``[]`` (default) to tag the n-th subcategory entry by
              'Subcategory N'

    colors: :class:`~collections.abc.Iterable`, default=[]
        iterable container of strings used to color subcategory level entries.
        i.e:
        ``[['yellow' , '#123456'], ['red', 'crimson'], ['pink', 'black']]``
        Nest entries intuitively the way the loads are nested.

        Beware:

            - ``len(colors)`` !>= number of categories
            - ``len(nested_colors)`` !>= number of respective subcategories
            - Use ``None`` to use matplotlib's default coloring cycle.
            - Use ``[]`` (default) to invoke the
              :attr:`tessif.frused.themes.cmaps` coloring.

    hatches: :class:`~collections.abc.Iterable`, default=[]
        Iterable container of strings used to hatch subcategory level entries.
        i.e: ``[['/', '\ '], ['|', '-'], ['o', '*']]``

        Supported patterns:
        ``{'/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*'}``

        Beware:

            - ``len(hatches)`` !>= number of categories
            - ``len(nested_hatches)`` !>= number of respective subcategories
            - Use ``None`` to not hatch any subcategory level entry
            - Use ``[]`` (default) to invoke the `tessif.frused.themes.hmaps`
              hatching.

    dticks : positive scalar, optional, default = 1
        X axis tick distance in number of load entries.

        i.e dticks=12 with an hourly resolution of load level entries results
        in a tick every 12 hours.

    offset : positive scalar, optional, default = 0
        Amount of load entries the tick labels are moved.

        i.e offset=10 with an hourly resolution of load level entries moves
        all tick labels by 10 hours to the right.

    fmt : str, optional
        Date formatting string used to format and display tick labels if an
        index of type date/time/datetime was provided.

        i.e.: ``fmt='%a. %m-%d' of date(1, 1, 1)`` results in 'Mon. 01-01'

        See `strftime() and strptime() Behavior
        <https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior>`_
        for more details.

    kwargs :
        kwargs are passed to :func:`matplotlib.pyplot.bar`


    Notes
    -----
    The first load entry is drawn on top. This behavior was chosen cause the
    author thinks of it as the most intuitive way of bar plotting. To archieve
    that the algorithm reverses all iterables. Keep that in mind when
    providing iterables too long for one of the optional parameters cause this
    will lead to the first entries beeing dropped, not the last!

    Examples
    ---------
    >>> import matplotlib.pyplot as plt
    >>> from tessif.visualize import system_loads

    Creating the most simple bar plot examplifying:

        - Using :func:`plot` as simple bar plot wrapper
        - ``None`` usage to supress features
        - Omitting the outer iterable on the optional parameters

    >>> axes = system_loads.bars(
    ...     loads=[1,2,3],  # one load series
    ...     labels=None,   # None to suppress feature
    ...     category_labels='Power',  # Omitting outer iterable
    ...     hatches=None)
    >>> # axes.figure.show() # commented out for doctesting

    .. image:: images/Loads_simple.png
        :align: center
        :alt: alternate text

    Creating a bar plot with 2 subcategories of the same category:

    >>> axes = system_loads.bars(
    ...     loads=[[1, 2, 3], [3, 2, 1]],  # 1 cat of 2 subcats of 3 loads each
    ...     labels=['PV', 'Wind'],   # 2 subcats, 2 labels
    ...     category_labels=None,  # Use None to suppress features
    ...     hatches=None)
    >>> # axes.figure.show() # commented out for doctesting

    .. image:: images/Loads_2subcats.png
        :align: center
        :alt: alternate text


    Creating a bar plot with 2 categories of 1 subcategory each:

    >>> axes = system_loads.bars(
    ...     loads=[[[1, 2, 3]], [[4, 5, 6]]],  # 2 cats 1 subcat each
    ...     # Beware of appropriate nesting when not using all levels:
    ...     labels=[['Power'], ['Heat']],
    ...     # Use default (empty list) to tag loads by 'Category N'
    ...     category_labels=[],
    ...     hatches=None)
    >>> # axes.figure.show() # commented out for doctesting

    .. image:: images/Loads_2cats.png
        :align: center
        :alt: alternate text

    Creating an energy system load analysis bar plot with 2 categoriess with
    3/2 subcategories:

    >>> axes = system_loads.bars(
    ...     loads=[[[1, 2, 3], [3, 2, 1], [3, 2, 2]],
    ...           [[4, 5, 6], [6, 5, 4]]],
    ...     # labels are nested intuitively
    ...     labels=[['PV', 'Wind', 'Coal'], ['ST', 'Gas', ]],
    ...     # All kinds of iterables are supported:
    ...     category_labels=('Power', 'Heat'),
    ...     hatches=None)
    >>> # axes.figure.show() # commented out for doctesting

    .. image:: images/Loads_32.png
        :align: center
        :alt: alternate text

    Creating an energy system load analysis bar plot - Design Case:

    >>> axes = system_loads.bars(
    ...     # 3 cats, 3/2/4 subs
    ...     loads=[[[1, 2, 3], [2, 2, 1], [3, 1, 1]],
    ...            [[4, 6, 6], [6, 5, 4]],
    ...            [[3, 4, 5], [3, 3, 3], [4, 5, 6], [4, 2, 3]]],
    ...     # Varying subcat lengths
    ...     labels=[['PV', 'Wind', 'Water'], ['ST', 'Gas'],
    ...             ['Cars', 'Trucks', 'Shipping', 'Aviation']],
    ...     # All kinds of iterables are supported:
    ...     category_labels=('Power', 'Heat', 'Mobility'),
    ...     hatches=None)
    >>> # axes.figure.show() # commented out for doctesting

    .. image:: images/Loads_DesignCase.png
        :align: center
        :alt: alternate text
    """
    # 1.) Handle input:
    # 1.1) Transform loads to: [Cats.., [Subcats.. [ Loads...]]]
    loads = ittools.nestify(ittools.itrify(loads), 3)

    # 1.2) Transform category parameters to ['Param 1', ... 'Param N']
    major_attr = [category_labels, category_colors, category_hatches]
    for pos, lst in enumerate(major_attr):

        # category parameter was stated
        if lst:
            major_attr[pos] = ittools.nestify(ittools.itrify(lst), 1)

        # default was used, so utilize default themes (tessif.frused.themes.py)
        elif ittools.is_empty(lst):

            # modify category_labels
            if pos == 0:
                major_attribute = ittools.Stringcrementor('Category', 1)

            # modify category_colors
            if pos == 1:
                major_attribute = cycle(themes.colors.sector.values())

            # modify category_hatches
            if pos == 2:
                major_attribute = cycle(themes.hatches.sector.values())

            # create empty placeholder list
            major_attr[pos] = []

            # iterate through each load category...
            for cat, cat_loads in enumerate(loads):
                # to append major_attribute
                major_attr[pos].append(next(major_attribute))

    # copy changes to parameters:
    category_labels, category_colors, category_hatches = major_attr

    # 1.3) Transform subcategory parameters to
    #      [['Param 1',...], ..., ['Param N', ...]]
    attr = [labels, colors, hatches]
    for pos, lst in enumerate(attr):
        if lst:  # subcategory parameter was stated
            attr[pos] = ittools.nestify(ittools.itrify(lst), 2)
        elif ittools.is_empty(lst):
            if pos == 0:  # use default themes (tessif.frused.themes.py)
                themed = [ittools.Stringcrementor('Subcategory', 1)
                          for i in range(len(loads))]
            if pos == 1:
                themed = [clrc for clrc in themes.ccycles.sector.values()]

            if pos == 2:
                themed = [cycle(theme)
                          for theme in themes.hmaps.sector.values()]
            attr[pos] = []
            for cat, cat_loads in enumerate(loads):
                attr[pos].append([])
                for ltype, ltype_loads in enumerate(cat_loads):
                    attr[pos][cat].append(next(themed[cat]))
    labels, colors, hatches = attr  # copy changes

    # 1.4) Create ticks and labels for the x axis
    if not bool(index):  # no index was given, so create one
        index = list(range(len(loads[0][0])))

    if not all(isinstance(  # An index to infer time labels was passed
            tick, int) for tick in index):
        xticklabels = list(  # ... so infer labels
            tick.strftime(fmt) if not isinstance(tick, int) else tick
            for tick in index[0::dticks])
        index = range(len(loads[0][0]))  # ... and create a numeric one
    else:  # an index was stated explicitly
        xticklabels = list(
            map(str, list(range(index[0] + offset, index[-1] + 1, dticks))))

    xticks = range(  # tick from first+offset to last with a distance of dticks
        index[0] + offset, index[-1] + 1, dticks)

    # Compute the number of plots to be drawn if a category has more than
    # 1 subcategory an additional plot will be drawn for detailed analysis
    subplots = 1
    if len(loads) > 1:
        for cat_loads in loads:
            if len(cat_loads) > 1:
                subplots += 1

    # 2.) Do the plotting
    f, ax = plt.subplots(subplots, 1, sharex=False, tight_layout=True)

    skipper = 0  # counter variable to skip unsubcategorized categories
    for subplt, axis in enumerate(
            ax if isinstance(ax, collections.abc.Iterable) else [ax]):

        # Category overview plot:
        if subplt == 0 and len(loads) > 1:
            for category, cat_loads in enumerate(reversed(loads)):

                sum_of_loads = list(  # aggregate all subcat loads
                    sum(load_data) for load_data in zip(*cat_loads))

                if category == 0:  # start bar plot at y=0
                    bottom = [0 for i in range(len(sum_of_loads))]

                axis.bar(
                    index, sum_of_loads,
                    label=list(reversed(category_labels))[
                        category] if category_labels else None,
                    color=list(reversed(category_colors))[
                        category] if category_colors else None,
                    width=1.0,
                    bottom=bottom,
                    **kwargs
                )

                bottom = list(  # previous top end is next plots bottom
                    map(sum, zip(bottom, sum_of_loads)))

        # Subcategory plots:
        else:
            # skip subcats that consist of only one load series
            # since they have been exhaustively visualized in the overview plot
            if len(loads[subplt-1+skipper]) <= 1:
                skipper += 1

            # plot the subcat:
            for obj, obj_loads in enumerate(reversed(loads[subplt-1+skipper])):
                bottom = list(  # lower end = sum of all previous plots
                    sum(time_step_loads) for time_step_loads in zip(
                        *list(reversed(loads[subplt-1+skipper]))[:obj]))
                axis.bar(
                    index, obj_loads,
                    label=list(reversed(labels[subplt-1+skipper]))[
                        obj] if labels else None,
                    color=list(reversed(colors[subplt-1+skipper]))[
                        obj] if colors else None,
                    hatch=list(reversed(hatches[subplt-1+skipper]))[
                        obj] if hatches else None,
                    width=1.0,
                    bottom=bottom if bottom else 0,
                    **kwargs)
                axis.set_title(category_labels[subplt-1+skipper]
                               if category_labels else None)

    for axis in ax if isinstance(ax, collections.abc.Iterable) else [ax]:
        # axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        # axis.set_ylim(bottom=0)
        # # axis.set_xticks(xticks, minor=False)
        # axis.set_xticklabels(xticklabels, rotation=0, minor=False)
        if ylabel:
            axis.set_ylabel(ylabel)

        # 7.) Draw the legend
        bbox = axis.get_position()
        # 2.2) shrink bounding box to 80% of original width
        axis.set_position([bbox.x0, bbox.y0, bbox.width*0.8, bbox.height])
        handles, tags = axis.get_legend_handles_labels()
        if tags:
            axis.legend(handles[::-1], tags[::-1],
                        # labelspacing=1,
                        # title='This Title'
                        bbox_to_anchor=(1.0, 1), loc='upper left',
                        # borderaxespad=0
                        )

    return axis


def bars_from_es(optimized_es, ignore=None, drop_zeros=True, **kwargs):
    """Draw sytem model energy "generation" as advanced bar plot.

    Convenience wrapper for :func:`bars`. Load results are
    automatically sorted by :attr:`~tessif.frused.namedtuples.Uid.sector`
    to draw a stacked bar plot for each sector in conjunction with an overall
    stacked bar plot of the entire model-scenario-combination results.

    Parameters
    ----------
    optimized_es
        Optimized energy supply system model scenario combination.
        Usually returned by one of the respective :mod:`tessif.simulate`
        functionalities.

    ignore: ~collections.abc.Container, None, default=None
        Container of node uid representations to not be included

    drop_zeros: bool, default=True
        If ``True`` all zero loads will be dropped. This can however lead
        unsuccesfull plotting. In this case zero columns need to be kept and
        nodes ignored manually using :paramref:`~bars_from_es.ignore`

    kwargs
        Key word arguments are passed to :func:`bars`

    Returns
    -------
    matplotlib.axes
        Matplotlib axes object holding the plotted figure elements.

    Examples
    --------
    When using :func:`bars_from_es` usually two usecases occur.

    1. Dropping all-zero entries because each sector has at least one
       not-all-zeros-load associated. But there are still some commodity sources
       present which need to be ignored manually for a sensible plot:

       >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
       >>> hh_msc = hardcoded_tsf_examples.create_hhes()

       >>> component_msc = hardcoded_tsf_examples.create_component_es(periods=50)

       >>> import tessif.transform.es2es.omf as tsf2omf  # nopep8
       >>> oemof_hh_msc = tsf2omf.transform(hh_msc)
       >>> oemof_comp_msc = tsf2omf.transform(component_msc)

       >>> import tessif.simulate  # nopep8
       >>> optimized_oemof_hh_msc = tessif.simulate.omf_from_es(oemof_hh_msc)
       >>> optimized_oemof_comp_msc = tessif.simulate.omf_from_es(oemof_comp_msc)

       >>> from tessif.visualize import system_loads  # nopep8
       >>> axes = system_loads.bars_from_es(
       ...     optimized_oemof_hh_msc,
       ...     drop_zeros=True,
       ...     ignore=[
       ...         "coal supply",
       ...         "biomass supply",
       ...     ],
       ... )
       >>> # axes.figure.show() # commented out for doctesting

       For the image shown the model-scenario-combination was optimized using
       ``periods=8760``

       .. image:: images/Loads_hhes2.png
           :align: center
           :alt: alternate text

    2. Not dropping all-zero entries, because at least one sector consists of
       only all-zeros-loads, is required, to enable plotting. In addition some
       commodity sources are ignored manually to draw a sensible plot:

       >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
       >>> component_msc = hardcoded_tsf_examples.create_component_es(periods=25)

       >>> import tessif.transform.es2es.omf as tsf2omf  # nopep8
       >>> oemof_comp_msc = tsf2omf.transform(component_msc)

       >>> import tessif.simulate  # nopep8
       >>> optimized_oemof_comp_msc = tessif.simulate.omf_from_es(
       ...     oemof_comp_msc)

       >>> from tessif.visualize import system_loads  # nopep8
       >>> axes = system_loads.bars_from_es(
       ...     optimized_oemof_hh_msc,
       ...     drop_zeros=False,
       ...     ignore=[
       ...          "Gas Station",
       ...          "Hard Coal Supply",
       ...          "Lignite Supply",
       ...          "Biogas Supply",
       ...     ],
       ... )
       >>> # axes.figure.show() # commented out for doctesting

       For the image shown the model-scenario-combination was optimized using
       ``periods=8760``

       .. image:: images/Loads_comp_es.png
           :align: center
           :alt: alternate text
    """
    if ignore is None:
        ignore = ()
    # infer model
    software = infer_software_from_es(optimized_es)
    internal_software_name = infer_registered_model(software)

    # import post processing utility
    post_processing = importlib.import_module(
        ".".join(["tessif.transform.es2mapping", internal_software_name]))

    # post process and create formatier...
    load_resultier = post_processing.LoadResultier(optimized_es)

    # extract all present sectors
    sectors = set(uid.sector.lower()
                  for uid in load_resultier.uid_nodes.values())
    # and sort them into a tuple of desired order
    sorted_sectors = tuple(
        sector
        for sector in ("power", "heat", "mobility", "coupled")
        if sector in sectors
    )

    sector_sorted_loads_dict = {
        key: {"loads": [], "names": []}
        for key in sorted_sectors
    }

    # sort the load results by sector and seperate labels and loads
    for node, uid in load_resultier.uid_nodes.items():

        if node not in ignore:
            if uid.component == 'source' or uid.component == 'transformer':
                outflows = load_resultier.node_outflows[node]
                if drop_zeros:
                    outflows = outflows.loc[:, (outflows != 0).any(axis=0)]

                if not outflows.empty:
                    if len(outflows.columns) == 1:
                        loads_to_add = [list(outflows.iloc[:, 0])]
                        names_to_add = [node]
                    else:
                        names_to_add, loads_to_add = list(), list()
                        for col in outflows.columns:
                            loads_to_add.append(list(outflows[col]))
                            names_to_add.append(f"{node} ({col})")

                    for sector, data_dict in sector_sorted_loads_dict.items():
                        if uid.sector.lower() == sector:
                            data_dict["names"].extend(names_to_add)
                            data_dict["loads"].extend(loads_to_add)

    axes = bars(
        loads=[sector_sorted_loads_dict[sector]["loads"]
               for sector in sorted_sectors],
        labels=[sector_sorted_loads_dict[sector]["names"]
                for sector in sorted_sectors],
        category_labels=sorted_sectors,
        hatches=None,
    )
    return axes
