""":mod:`~tessif.visualize.ldc` is a powerfull :mod:`tessif` line drawing utility based on
:func:`matplotlib.pyplot.plot`.

Designed to quickly draw arbitrarily complex sets of load duration curves.

Algorithm is build on a triple nested list engine which is able to visualize
plot data grouped as ``[categroy [subcategory [data]]]``

Default coloring uses :attr:`tessif.frused.themes.colors` and
:attr:`~tessif.frused.themes.cmaps`.
"""
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import collections
import ittools
from itertools import cycle
from tessif.frused import themes


def plot(loads, category_labels=[], category_colors=[],
         subcat_labels=[], subcat_colors=[],
         load_label='Load in', load_unit='MW',
         time_label='Cumulated time period in', time_unit='hours',
         title='Load duration curves', integer_ticks=True,
         **kwargs):
    r"""
    Draws a sophisticated bar plot for visualizing energy system load data.

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

            [Sbucategory 1, ..., Subcategory N] for each category

        - Lowest level:

            [Load at time step 1, .... load at time step N]
            for each subcategory

        Any nesting depth <= 3 can be handled and will be interpreted as
        stated above

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

    subcat_labels: :class:`~collections.abc.Iterable`, default=[]
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

    subcat_colors: :class:`~collections.abc.Iterable`, default=[]
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

    load_label : str, default='Load in'
        First part of the y label.

    load_unit : str, default ='MW'
        Second part of the y label

    time_label : str, default='Cumulated time period in'
        First part of the x label

    time_unit : str, default='hours'
        Second part of the x label

    title : str ='Load duration curves'
        Title displayed on the very top

    integer_ticks : bool, default=True
        Axes tick switch. If ``True`` there will only be integer ticks on both
        axis.

    kwargs :
        kwargs are passed to :func:`matplotlib.pyplot.subplots`
        Use them for sharing x and y axes for example.


    Notes
    -----
    When using the list engine to categorize load duration curves, be aware
    that the upper most load duration curve is the sum of all load duration
    curves in that category.

    Examples
    ---------
    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.ldc as ldc

    Creating the most simple load duration curve examplifying:

        - Using :func:`plot` as simple laod duration curve plotter
        - ``None`` usage to supress features
        - Omitting the outer iterable on the optional parameters
        - Using :paramref:`~plot.kwargs` to modify call to
          :func:`matplotlib.pyplot.subplots`

    >>> ldc.plot(
    ...     loads=[1,2,3],  # one load series
    ...     subcat_labels=None,   # None to supress feature
    ...     category_labels='Power',  # Omitting outer iterable
    ...     tight_layout=True)  # using **kwargs to ask for tight layout

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/LDC_simple.png
        :align: center
        :alt: alternate text

    Creating a ldc plot with 2 subcategories of the same category:

    >>> ldc.plot(
    ...     loads=[[1, 2, 3], [3, 2, 1]],  # 1 cat of 2 subcats of 3 laods each
    ...     subcat_labels=['PV', 'Wind'],   # 2 subcats, 2 labels
    ...     category_labels='Power',  # Omitting outer iterable
    ...     tight_layout=True)  # using kwargs to ask for tight layout

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/LDC_2subcats.png
        :align: center
        :alt: alternate text


    Creating a ldc plot with 2 categories of 1 subcategory each:

    >>> ldc.plot(
    ...     loads=[[[1, 2, 3]], [[4, 5, 6]]],  # 2 cats 1 subcat each
    ...     # Beware of appropriate nesting when not using all levels:
    ...     subcat_labels=[['Power'], ['Heat']],
    ...     # Use default (empty list) to tag loads by 'Category N'
    ...     category_labels=[],
    ...     sharex=True,  # using kwargs to share x axis
    ...     tight_layout=True)  # and ask for tight layout

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/LDC_2cats.png
        :align: center
        :alt: alternate text

    Creating an energy system load duration curve analysis plot with 2
    categories of 3/2 subcategories:

    >>> ldc.plot(
    ...     loads=[[[1, 2, 3], [3, 2, 1], [3, 2, 2]],
    ...           [[4, 5, 6], [6, 5, 4]]],
    ...     # labels are nested intuitively
    ...     subcat_labels=[['PV', 'Wind', 'Coal'], ['ST', 'Gas', ]],
    ...     # All kinds of iterables are supported:
    ...     category_labels=('Power', 'Heat'),
    ...     sharex=True,  # using kwargs to share x axis
    ...     tight_layout=True)  # and ask for tight layout

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/LDC_32.png
        :align: center
        :alt: alternate text

    Creating an energy system load duration curve analysis plot - Design Case:

    >>> ldc.plot(
    ...     # 3 cats, 3/2/4 subs
    ...     loads=[[[1, 2, 3], [2, 2, 1], [3, 1, 1]],
    ...            [[4, 6, 6], [6, 5, 4]],
    ...            [[3, 4, 5], [3, 3, 3], [4, 5, 6], [4, 2, 3]]],
    ...     # Varying subcat lengths
    ...     subcat_labels=[['PV', 'Wind', 'Water'], ['ST', 'Gas'],
    ...             ['Cars', 'Trucks', 'Shipping', 'Aviation']],
    ...     # All kinds of iterables are supported:
    ...     category_labels=('Power', 'Heat', 'Mobility'),
    ...     sharex=True,  # using kwargs to share x axis
    ...     tight_layout=True)  # and ask for tight layout

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(3)
    >>> plt.close('all')

    IGNORE

    .. image:: images/LDC_DesignCase.png
        :align: center
        :alt: alternate text
    """

    # # 1.) Prepare the plot data:
    # # 1.1) Make sure loads is a nested list of plots to be drawn:
    # if not all(isinstance(load, collections.Iterable) for load in loads):
    #     loads = [loads]

    # 1.) Handle input:
    # 1.1) Transform loads to: [Cats.., [Subcats.. [ Loads...]]]
    loads = ittools.nestify(ittools.itrify(loads, list), 3, list)

    # 1.2) Transform category parameters to ['Param 1', ... 'Param N']
    major_attr = [category_labels, category_colors]
    for pos, attribute in enumerate(major_attr):
        # category parameter was stated
        if attribute:
            # make sure each attribute is a list as in [Attribute, ...]
            major_attr[pos] = ittools.nestify(
                ittools.itrify(attribute, list), 1, list)

        # default was used, so utilize default themes (interfaces.themes.py)
        elif ittools.is_empty(attribute):
            # modify category_labels
            if pos == 0:
                major_attribute = ittools.Stringcrementor('Category', 1)
            # modify category_colors
            if pos == 1:
                major_attribute = cycle(themes.colors.sector.values())

            # create empty placeholder list
            major_attr[pos] = []

            # iterate through each load category...
            for category, category_laods in enumerate(loads):
                # to append major_attribute
                major_attr[pos].append(next(major_attribute))
    # copy changes to parameters:
    category_labels, category_colors = major_attr

    # 1.3) Transform subcategory parameters to
    #      [['Param 1',...], ..., ['Param N', ...]]
    attr = [subcat_labels, subcat_colors]
    for pos, attribute in enumerate(attr):
        if attribute:  # subcategory parameter was stated
            attr[pos] = ittools.nestify(
                ittools.itrify(attribute, list), 2, list)
        elif ittools.is_empty(attribute):
            if pos == 0:  # use default themes (interfaces.themes.py)
                themed = [ittools.Stringcrementor('Subcategory', 1)
                          for i in range(len(loads))]
            if pos == 1:
                themed = [clrc for clrc in themes.ccycles.sector.values()]

            # create empty placeholder list
            attr[pos] = []

            # iterate through each load category:
            for category, category_loads in enumerate(loads):
                # create empty nested placeholder list:
                attr[pos].append([])
                # iterate through each load subcategory
                for subcategory, subcat_loads in enumerate(category_loads):
                    attr[pos][category].append(next(themed[category]))
    # copy changes to parameters:
    subcat_labels, subcat_colors = attr

    # 1.3) Sort load data (Y-Axis) from highest to lowest:
    # iterate through each category:
    for category, category_loads in enumerate(loads):
        # iterate though each subcategory load:
        for subcat, subcat_loads in enumerate(category_loads):
            loads[category][subcat] = sorted(subcat_loads, reverse=True)

    # Compute the number of plots to be drawn if a category has more than
    # 1 subcategory an additional plot will be drawn for detailed analysis
    subplots = 1
    if len(loads) > 1:
        for cat_loads in loads:
            if len(cat_loads) > 1:
                subplots += 1

    # 2.) Create an empty canvas to draw on:
    f, ax = plt.subplots(subplots, 1, **kwargs)

    skipper = 0  # counter variable to skip unsubcategorized categories
    for subplt, axis in enumerate(
            ax if isinstance(ax, collections.Iterable) else [ax]):

        # Category overview plot:
        if subplt == 0 and len(loads) > 1:
            for category, cat_loads in enumerate(loads):

                sum_of_loads = list(  # aggregate all subcat loads
                    sum(load_data) for load_data in zip(*cat_loads))

                axis.plot(
                    list(range(1, len(sum_of_loads)+1)), sum_of_loads,
                    label=category_labels[
                        category] if category_labels else None,
                    color=category_colors[
                        category] if category_colors else None,
                )

        # 3.) Do the actual plotting:
        # Subcategory plots:
        else:
            # skip subcats that consist of only one load series
            # since they have been exhaustivley visualized in the overview plot
            if len(loads[subplt-1+skipper]) <= 1:
                skipper += 1

            for subcategory, subcat_loads in enumerate(
                    loads[subplt-1+skipper]):
                axis.plot(
                    list(range(1, len(subcat_loads)+1)), subcat_loads,
                    label=subcat_labels[subplt-1+skipper][
                        subcategory]if subcat_labels else None,
                    color=subcat_colors[subplt-1+skipper][
                        subcategory] if subcat_colors else None)
                axis.set_title(category_labels[subplt-1+skipper]
                               if category_labels else None)

    for axis in ax if isinstance(ax, collections.Iterable) else [ax]:
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        # Set y label:
        axis.set_ylabel('{} {}'.format(load_label, load_unit))
        # make y axius start at 0
        axis.set_ylim(bottom=0)

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

        if integer_ticks:
            axis.yaxis.set_major_locator(MaxNLocator(integer=True))

    if isinstance(ax, collections.Iterable):
        ax[-1].set_xlabel('{} {}'.format(time_label, time_unit))
