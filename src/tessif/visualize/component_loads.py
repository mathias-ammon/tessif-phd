"""Visualize submodule to plot individual component loads/behavior.

:mod:`~tessif.visualize.components` is a :mod:`tessif` interface to visualize
energy system component loads and/or behavior.
"""
from matplotlib.ticker import MaxNLocator
import ittools
import collections
from math import copysign

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tessif.frused import configurations, spellings, themes


esci = spellings.energy_system_component_identifiers


def bar_lines(
        loads,
        component_type,
        load_type='both',
        labels=None,
        timeindex=None,
        ticks=5,
        line_colors=None,
        bar_colors=None,
        drop_zero=True,
        **kwargs
):
    """Plot an energy system component's loads as lines and stacked bars.

    When both inflows and outflows are given, those get distinguished by the
    sign of their values so that they can either be plotted as bars or as
    lines. Outflows are always negative and inflows positive. The inflow from
    and the outflow to a component must be given seperately or else they will
    not be plotted.

    The outflows of sources are plotted as bars and the inflows of sinks as
    lines. For other components inflows are bars and outflows are lines.

    Note
    ----
    bar_lines() treats +0.0 and -0.0 differently. Float zeros with a positive
    sign will be grouped with positive numbers and those with a negative sign
    with negative numbers.

    Parameters
    ----------
    loads : :class:`~pandas.DataFrame`, :class:`~numpy.ndarray`, \
    :class:`~collections.abc.Sequence`, :class:`~dict`
        DataFrame, matrix or dict with the energy system component's data to be
        plotted. The order of the stacked bars is the same as the order in
        'loads' with the first element in 'loads' being the bottom bar in the
        plot.

        In a DataFrame each column is an inflow or outflow and each line
        corresponds to a timestep. The column names are used as the labels of
        the graphs and the index entries become the tick labels for the x-axis
        if no other labels or timeindex are given.

        In a matrix (e.g. nested list or 2d ndarray) the lines are inflows or
        outflows and each column is a timestep.

        In a dict each key-value pair is an inflow or outflow. The dict-keys
        are used as the labels of the graphs if no other labels are given. The
        dict-values consist of ndarrays or Sequences where each entry
        corresponds a timestep

    component_type: :class:`str`
        Contains the :ref:`type <Models_Tessif_Concept_ESC>` of the plotted
        enery system component. Must be 'bus', 'sink', 'source', 'storage',
        'transformer'
        or 'connector'.

    load_type: :class:`str`, default='both'
        Contains the type of load from or to the plotted energy system
        component. Must be 'inflows', 'outflows' or 'both'.

    labels: :class:`~collections.abc.Iterable`, default=None
        Iterable containing strings that become the labels for the load graphs.
        The order of the entries must be the same as the order of 'loads',
        going from left to right for DataFrames und dicts and from top to
        bottom for matrices.

        The values that are given by 'labels' will be prefered over the values
        from inside the 'loads' DataFrame or dict. Those will be used when
        'labels' is None.

    timeindex: :class:`pandas.DatetimeIndex`, default=None
        If 'timeindex' is given, it is used as the ticklabels for the x-axis.
        Else, the index of 'loads' is used, if 'loads' is a dataframe.
        'timeindex' must have the same frequency as 'loads'.

    ticks: :class:`str`, default=5
        Number of ticklabels on the x-axis.

    line_colors: :class:`~collections.abc.Iterable`, default=None
        Iterable containing the colors for the line graphs. The colors can be
        in any format that matplotlib recognizes
        (e.g. ['green', '#0f0f0f', (0.1, 0.2, 0.5)]). The order of
        the colors in 'line_colors' is the order of the colors of the lines as
        they appear in the legend, starting from the top. If no colors are
        given, bar_lines() tries to map the colors from tessif.frused.themes to
        the names of the lines.

    bar_colors: :class:`~collections.abc.Iterable`, default=None
        Iterable containing the colors for the bar graphs. The colors can be
        in any format that matplotlib recognizes
        (e.g. ['green', '#0f0f0f', (0.1, 0.2, 0.5)]). The order of
        the colors in 'bar_colors' is the order of the colors of the bars as
        they appear in the legend, starting from the top. If no colors are
        given, bar_lines() tries to map the colors from tessif.frused.themes to
        the names of the bars.

    drop_zero: bool, default=True
        If ``True``, do not include columns holding only zeros. Otherwise they
        are added to the list of bars.

    **kwargs
        Options to pass to matplotlib plotting method.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes object holding the plotted figure elements.

    Examples
    --------
    >>> from tessif.visualize import component_loads

    Visualize the loads of a comonent of the 'Hamburg Energy System' example
    created with tessif:

    1. Use the :ref:`example hub's <Examples>`
    :meth:`~tessif.examples.data.tsf.py_hard.create_hhes` utility to
    create the energy system:

    >>> from tessif.examples.data.tsf.py_hard import create_hhes
    >>> tessif_es = create_hhes()

    2. Transform the :mod:`tessif energy system
    <tessif.model.energy_system.AbstractEnergySystem>`:

    >>> import tessif.transform.es2es.omf as tessif_to_oemof
    >>> oemof_es = tessif_to_oemof.transform(tessif_es)

    3. Simulate the oemof energy system:

    >>> import tessif.simulate as simulate
    >>> optimized_oemof_es = simulate.omf_from_es(oemof_es, solver='cbc')

    4. Extract the load results from one of the components:

    >>> import tessif.transform.es2mapping.omf as oemof_results
    >>> resultier = oemof_results.LoadResultier(optimized_oemof_es)
    >>> loads = resultier.node_load['powerline']

    5. Visualize the loads:

    >>> axes = component_loads.bar_lines(loads, component_type='bus')
    >>> # axes.figure.show() commented out for doctesting

    .. image:: images/Loads_hhes.png
            :align: center
            :alt: alternate text

    Visualize the loads of a component of the 'star' example energy system
    created with oemof:

    1. Use the :ref:`example hub's <Examples>`
    :meth:`~tessif.examples.data.omf.py_hard.create_star` utility to create the
    energy system and extract the load results from one of the components:

    >>> import tessif.examples.data.omf.py_hard as omf_examples
    >>> import tessif.transform.es2mapping.omf as oemof_results
    >>> resultier = oemof_results.LoadResultier(omf_examples.create_star())
    >>> loads = resultier.node_load['Power Line']

    2. Visualize the loads:

    >>> axes = component_loads.bar_lines(loads, component_type='bus')
    >>> # axes.figure.show() commented out for doctesting

    .. image:: images/Loads_star.png
            :align: center
            :alt: alternate text

    Visualize loads given as matrix:

    1. Create the matrix and the other parameters:

    >>> import pandas as pd
    >>> loads = [[-20.0, -10.0],
    ...          [-87.0, -97.0],
    ...          [10.0, 10.0],
    ...          [7.0, 7.0],
    ...          [90.0, 90.0]]
    >>> labels = ['Limited Power', 'Unlimited Power', 'Demand13', 'Demand7',
    ...           'Demand90']
    >>> timeindex = pd.date_range('7/13/1990', periods=2, freq='H')

    2. Visualize the loads:

    >>> figure = component_loads.bar_lines(
    ...     loads, component_type='bus', labels=labels, timeindex=timeindex)
    >>> # figure.show() commented out for doctesting

    .. image:: images/Loads_matrix.png
            :align: center
            :alt: alternate text
    """
    if isinstance(loads, pd.DataFrame):
        df = loads.copy()
    elif isinstance(loads, dict):
        df = pd.DataFrame(loads)
    elif isinstance(loads, np.ndarray):
        df = pd.DataFrame(loads.T)
    elif (isinstance(loads, collections.abc.Sequence)
            and not isinstance(loads, (str, bytes))):
        # transpose the matrix before it is converted to a DataFrame.
        df = pd.DataFrame(zip(*loads))
    else:
        raise TypeError(
            '%s type for loads data is not supported.' % type(loads))
    if labels:
        if len(labels) == len(df.columns):
            df.columns = labels
        else:
            warn("'labels' has the wrong length and will be ignored.")

    if not isinstance(component_type, str):
        raise TypeError("component_type must be <class 'str'>, not %s."
                        % type(component_type))
    elif component_type not in ['bus', 'connector', 'sink', 'source',
                                'storage', 'transformer']:
        raise ValueError("component_type must be 'bus', 'connector', 'sink', \
'source', 'storage' or 'transformer', not '%s'." % component_type)

    if not isinstance(load_type, str):
        raise TypeError("load_type must be <class 'str'>, not %s."
                        % type(load_type))
    elif load_type not in ['inflows', 'outflows', 'both']:
        raise ValueError("load_type must be 'inflows', 'outflows' or 'both', \
not '%s'." % load_type)

    if isinstance(timeindex, pd.DatetimeIndex):
        dates = timeindex
    else:
        dates = df.index

    # Split the df in one for the line graph and one for the bar chart.
    # If the positive or negative columns are displayed as bars or as lines
    # depends on the functions parameters.
    df_line = pd.DataFrame()
    df_bar = pd.DataFrame()
    if (component_type == 'source'
            or (component_type in ['bus', 'connector', 'storage',
                                   'transformer']
                and load_type == 'inflows')
            or (component_type == 'sink' and load_type == 'both')):
        for (columnName, columnData) in df.iteritems():
            # copysign(1, i) returns 1 if i > 0 or i == +0.0 and returns -1
            # if i < 0 or i == -0.0.
            if all(copysign(1, i) > 0 for i in columnData.values):
                df_bar[columnName] = columnData
            elif all(copysign(1, i) < 0 for i in columnData.values):
                df_line[columnName] = columnData.abs()
            else:
                warn("'%s' has positive and negative values and will not be \
plotted" % columnName)
    else:
        for (columnName, columnData) in df.iteritems():
            # copysign(1, i) returns 1 if i > 0 or i == +0.0 and returns -1
            # if i < 0 or i == -0.0
            if not all(entry == 0 for entry in columnData.values):
                if all(entry >= 0 for entry in columnData.values):
                    df_line[columnName] = columnData
                else:
                    df_bar[columnName] = columnData.abs()
            else:
                if not drop_zero:
                    df_bar[columnName] = columnData

#             if all(copysign(1, i) >= 0 for i in columnData.values):
#                 df_line[columnName] = columnData
#             elif all(copysign(1, i) <= 0 for i in columnData.values):
#                 df_bar[columnName] = columnData.abs()
#             else:
#                 warn("'%s' has positive and negative values and will not be \
# plotted" % columnName)

    # Add an additional column to df_line, where for each entry is the sum of
    # the other columns at that time step.
    if len(df_line.columns) > 1:
        if component_type == 'sink':
            df_line['Total Inflow'] = df_line.sum(axis=1)
        else:
            df_line['Total Outflow'] = df_line.sum(axis=1)

    # If no line_colors or bar_colors are given, try to map the column names to
    # the colors in tessif.frused.themes. When not possible use matplotlibs
    # default_colors.
    default_colors = iter(mcolors.TABLEAU_COLORS)
    if line_colors:
        colors_lines = line_colors
    else:
        colors_lines = [None] * len(df_line.columns)
        for i, column_name in enumerate(df_line.columns):
            for key, variations in esci.name.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_lines[i]:
                        colors_lines[i] = next(themes.ccycles.name[key])
            for key, variations in esci.carrier.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_lines[i]:
                        colors_lines[i] = next(themes.ccycles.carrier[key])
            for key, variations in esci.sector.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_lines[i]:
                        colors_lines[i] = next(themes.ccycles.sector[key])
            for key, variations in esci.component.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_lines[i]:
                        colors_lines[i] = next(themes.ccycles.component[key])
            if column_name == 'Total Inflow' or column_name == 'Total Outflow':
                colors_lines[i] = '#cd0000'
            if not colors_lines[i]:
                colors_lines[i] = next(default_colors)
    if bar_colors:
        colors_bars = bar_colors
    else:
        colors_bars = [None] * len(df_bar.columns)
        for i, column_name in enumerate(df_bar.columns):
            for key, variations in esci.name.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_bars[i]:
                        colors_bars[i] = next(themes.ccycles.name[key])
            for key, variations in esci.carrier.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_bars[i]:
                        colors_bars[i] = next(themes.ccycles.carrier[key])
            for key, variations in esci.sector.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_bars[i]:
                        colors_bars[i] = next(themes.ccycles.sector[key])
            for key, variations in esci.component.items():
                if any(variation in column_name for variation in variations
                       if isinstance(column_name, str)):
                    if not colors_bars[i]:
                        colors_bars[i] = next(themes.ccycles.component[key])
            if not colors_bars[i]:
                colors_bars[i] = next(default_colors)

    linestyles = ['-', ':', '--', '-.', ':', '--', '-.', ':', '--', '-.', ':']

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    if len(df_line.columns) > 0:
        df_line = df_line.reset_index(drop=True)
        df_line.plot(kind='line', ax=ax, drawstyle='steps-mid',
                     color=colors_lines, linewidth=2.5, style=linestyles,
                     **kwargs)
    if len(df_bar.columns) > 0:
        df_bar = df_bar.reset_index(drop=True)
        df_bar.plot(kind='bar', ax=ax, stacked=True, linewidth=0, width=1,
                    color=colors_bars, **kwargs)

    if df.columns.name:
        ax.set_title("Loads of '%s'" % df.columns.name)
    else:
        ax.set_title("Loads")
    ax.set_ylabel('Power in %s' % configurations.power_reference_unit)

    # Show only some datetime ticks
    ax.set_xticks(range(0, len(dates), int(len(dates)/ticks)+1))
    ax.set_xticklabels(
        [item.strftime('%Y-%m-%d %H:%M') if isinstance(item, pd.DatetimeIndex)
         else item for item in dates.tolist()[::int(len(dates)/ticks)+1]],
        rotation=0)

    return ax


def response(signals, responses=[], transfers=[], sigplot=plt.step,
             replot=plt.plot, shape=(), title='', titles=[], legend=False,
             integer_ticks=True, **kwargs):
    r"""Plot signal and response over their respective value position.

    Designed to quickly draw input and response signals of basically any kind
    of transfer function not only those representing energy system components.
    Constructstwo pandas.DataFrames internally for data handling.

    Plots :paramref:`~response.signals` using :paramref:`~response.sigplot` and
    :paramref:`~response.responses` using :paramref:`~response.replot` into
    the same diagram (one for each pairing). Use
    :paramref:`~response.transfers` to compute responses if none are stated.


    Parameters
    ----------
    signals: :class:`~collections.abc.Iterable`, :class:`pandas.DataFrame`
        2 depth iterable of the the input signals to be drawn as in ::

            signals = [(s0, ..., sN), ..., (s0, ..., sN)]

        Or as in::

            signals = pandas.DataFrame(
                zip((s0, ..., sN), ..., (s0, ..., sN)),
                columns=['Signal1', ..., 'SignalN'])

        If only 1 signal is to be plotted, outer iterable can be omitted.

    responses: :class:`~collections.abc.Iterable`, :class:`pandas.DataFrame`
        2 depth iterable of the output responses to be drawn as in ::

            responses = [(r0, ..., rN), ..., (r0, ..., rN)]

        Or as in::

            responses = pandas.DataFrame(
                zip((s0, ..., sN), ..., (s0, ..., sN)),
                columns=['Response1', ..., 'ResponseN'])

        Must be of equal length or longer than :paramref:`response.signals`.
        If only 1 signal is to be plotted, outer iterable can be omitted.
        Default=[]

        Make use of the `SciPy signal library
        <https://docs.scipy.org/doc/scipy/reference/signal.html>`_ for
        an easy to use yet powerfull signal visualizing tool.

    transfers : :class:`~collections.abc.Iterable`, :class:`pandas.DataFrame`
        2 depth iterable of functionals to compute the responses in case none
        are provided (i.e if :paramref:`response.responses` evaluates to
        ``None``).

        Must be of equal length or longer than :paramref:`response.signals`.
        If only 1 signal is to be plotted, outer iterable can be omitted.
        default=[]

    sigplot: :class:`~collections.abc.Iterable`, default=matplotlib.pyplot.plot
        Iterable of functionals to plot the signals. Use
        :func:`functools.partial` for supplying parameters. See also the
        Examples section.

    replot: :class:`~collections.abc.Iterable`, default=matplotlib.pyplot.bar
        Iterable of functionals to plot the responses. Use
        :func:`functools.partial` for supplying parameters. See also the
        Examples section.

    shape: tuple, default=()
        Tuple of subplot dimenstions. Use this to arrange the `subplots
        <https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.subplots.html>`_
        beeing drawn.
        ``shape[0]/[1]`` will be interpreted as number of rows/columns
        respectively.
        If default or ``None``, there will be 1 subplot per row (i.e (:,1))

    title: str, default=''
        Super titel of the figure

    titles: :class:`~collections.abc.Iterable`, default=[]
        Iterable of strings titeling the subplots. If not empty a title is
        drawn. Must be of equal length or longer than :paramref:`signals`

    legend: bool, default=False
        Legend switch. If ``True`` a legend is attempted to be drawn.
        Use :func:`functools.partial`
        for supplying labels. See also the Examples section.

    integer_ticks: bool, default=True
        Axes tick switch. If ``True`` there will only be integer ticks on both
        axis.

    kwargs:
        Kwargs are passed to `matplotlib.pyplot.subplots
        <https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.subplots.html>`_

        Use them for sharing x and y axes for example.

    Return
    ------
    plt_handles : 2-tuple of handles
        2-tuple of handle containers of the plots drawn as in
        :code:`(signal_handles, response_handles)`

    Examples
    --------
    Standard Use Case Using:

        - :func:`functools.partial` to tweak plotting
        - :paramref:`~response.shape` to arrange the subplots
        - :paramref:`~response.kwargs` to handle shared axes

    >>> import functools
    >>> import matplotlib.pyplot as plt

    >>> signals = [(0, 0, 1, 1), (0, 2, 2, 0), (0, 0, 1, 1),
    ...            (0, 2, 2, 0), (0, 0, 1, 1), (0, 2, 2, 0)]
    >>> responses = [(0, 0, 0.5, 1), (0, 1, 2, 1), (0, 0, 0.5, 1),
    ...              (0, 1, 2, 1), (0, 0, 0.5, 1), (0, 1, 2, 1)]
    >>> sigs, responses = response(
    ...     signals, responses,
    ...     sigplot=functools.partial(plt.step, label='Input'),
    ...     replot=functools.partial(
    ...         plt.plot, c='orange', label='Reponse'),
    ...     legend=True, shape=(2, 3),
    ...     title='Standard Use Case Example',
    ...     titles=list('Subplot ' + str(i) for i in range(1, 7)),
    ...     sharex='col', sharey='row')
    >>> fig = plt.gcf()
    >>> # fig.show()

    .. image:: images/Components_Standard.png
        :align: center
        :alt: alternate text


    Scipy Example Using:

        - `SciPy signal library
          <https://docs.scipy.org/doc/scipy/reference/signal.html>`_
          to compute filtered responses
        - using the default :paramref:`~response.shape` for plotting
        - using :paramref:`~titles` to inform the viewer about the filters used

    >>> import scipy.signal as signal
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt

    >>> t = np.linspace(-1, 1, 201)
    >>> x = (np.sin(2*np.pi*0.75*t*(1-t) + 2.1) +
    ...      0.1*np.sin(2*np.pi*1.25*t + 1) +
    ...      0.18*np.cos(2*np.pi*3.85*t))
    >>> xn = x + np.random.randn(len(t)) * 0.08
    >>> sigs, responses = response(signals=[xn, xn],
    ...       responses=[
    ...           signal.filtfilt(*signal.butter(3, 0.05), xn),
    ...           signal.filtfilt(*signal.cheby1(3, 6, 0.05), xn)],
    ...       sigplot=functools.partial(plt.plot, label='Noisy Input'),
    ...       replot=functools.partial(
    ...           plt.plot, c='r', lw=3, label='Filtered response'),
    ...       legend=True, title='scipy.signals example',
    ...       titles=['3rd Order Butter Filter', '3rd Order Cheby Filter'])
    >>> fig = plt.gcf()
    >>> # fig.show()

    .. image:: images/Components_ScipySignal.png
        :align: center
        :alt: alternate text


    Custom Functionals Example Using:

        - lambda style functionals
        - latex syntax when labeling

    >>> import math
    >>> transfers = [lambda x: x**2, lambda x: x**3,
    ...              lambda x: 1/(x+1), lambda x: 1/math.sqrt(1+x**2)]
    >>> sigs, responses = response(
    ...     signals[:4], transfers=transfers, shape=(2, 2),
    ...     replot=functools.partial(
    ...         plt.plot, alpha=0.8, c='navy', label='output'),
    ...     sigplot=functools.partial(
    ...         plt.step, lw=2, c='purple', label='input'),
    ...     titles=list('Output computed using ' + func for func in
    ...         ['$x^2$', '$x^3$', r'$\frac{1}{x+1}$',
    ...          r'$\frac{1}{\sqrt{1+x^2}}$']),
    ...     legend=True)

    >>> fig = plt.gcf()
    >>> # fig.show()

    .. image:: images/Components_CustomFunctionals.png
        :align: center
        :alt: alternate text
    """

    # is signals a sequence/array and not a data frame ?
    if isinstance(signals, (collections.abc.Sequence, np.ndarray)):

        # handle pandas Series beeing passed
        for position, signal in enumerate(signals.copy()):
            if isinstance(signal, pd.Series):
                signals[position] = tuple(signal)

        # yes, so make sure signals is a 2 nested iterable as in
        # [(s0, ..., sN), ..., (s0, ..., sN)]
        signals = ittools.nestify(ittools.itrify(signals), 2)

        # transform signals into a pandas.DataFrame:
        signals = pd.DataFrame(zip(*signals))

    # is responses a sequence/array and not a data frame ?
    if not ittools.is_empty(responses):
        if isinstance(responses, (collections.abc.Sequence, np.ndarray)):

            # handle pandas Series beeing passed
            for position, response in enumerate(responses.copy()):
                if isinstance(response, pd.Series):
                    responses[position] = tuple(response)

            # yes, make sure responses is a 2 nested iterable as in
            # [(r0, ..., rN), ..., (r0, ..., rN)]
            responses = ittools.nestify(ittools.itrify(responses), 2)

            # transform responses into a pandas.DataFrame:
            responses = pd.DataFrame(zip(*responses))

    # is transfers a sequence/array and not a data frame ?
    else:

        if not isinstance(transfers, pd.DataFrame):
            # make sure transfers is a 2 nested iterable as in
            # [(t0, ..., tN), ..., (t0, ..., tN)]
            transfers = ittools.nestify(ittools.itrify(transfers), 1)

        for pos, column in enumerate(signals):
            responses.append(list(map(transfers[pos], signals[column])))

        # transform responses into a pandas.DataFrame:
        responses = pd.DataFrame(zip(*responses))

    # itrify titles to allow ommiting list for only one title provided
    if not ittools.is_empty(titles):
        titles = ittools.nestify(ittools.itrify(titles), 1)

    # figue out subplot arrangement
    if shape:
        # if explicitly stated, use it:
        shp = (shape[0], shape[1])
    else:
        # if default was used, draw one plot for each row:
        shp = (len(signals.columns.tolist()), 1)

    # Create the figure and axes:
    f, ax = plt.subplots(*shp, **kwargs)

    # make sure ax is a 2d array to allow 2d indexing even for (1,1) shapes
    ax = np.array(ax, ndmin=2).reshape(shp)

    # create a 1d to 2d index mapper:
    idx2d = ittools.Index2D(shp)

    # Was a super title requested to be drawn ?
    if title:
        # yes, so do it
        plt.suptitle(title)

    # create handle containers for returning
    signal_handles, response_handles = [], []

    # do the plotting:
    for pos, col in enumerate(signals):
        # select proper axis:
        plt.sca(ax[idx2d(pos)])

        # plot the signals
        signal_handles.append(
            sigplot(range(len(signals[col])), signals[col]))
        # plot the response:
        response_handles.append(
            replot(range(len(responses.iloc[:, pos])), responses.iloc[:, pos]))

        # was legend requested to be drawn ?
        if legend:
            # yes so do it mapping the 1d index to a 2d:
            ax[idx2d(pos)].legend()

        # were title requested to be drawn ?
        if not ittools.is_empty(titles):
            ax[idx2d(pos)].set_title(titles[pos])

        if integer_ticks:
            ax[idx2d(pos)].xaxis.set_major_locator(
                MaxNLocator(integer=True))
            ax[idx2d(pos)].yaxis.set_major_locator(
                MaxNLocator(integer=True))

    return signal_handles, response_handles


def step(
        data,
        x_axis_data=None,
        labels=[],
        colors=[],
        title=None,
        x_axis_label=None,
        y_axis_label=None,
        where='post',
):
    """Draw step plot to compare component loads using matplotlib.

    Parameters
    ----------
    data: ~collections.abc.Container, pandas.DataFrame
        2 levels deep container holding the of the data to be drawn. As in::

            data = [[y1(x1), ... y1(xN)],
                    ...
                    [yN(x1), ... yN(xN)]]

        where :math:`y_n(x)` describes the n-th model's load series.

        Or a :class:`pandas.DataFrame` where each column describes a singular
        timeseries and the index the coresponding x-axis values (usually the
        point of time during the optimization the respective load data occured).
        The column entries will be used as legend entry labels.

        Warning
        -------
        If providing data **NOT** as a :class:`pandas.DataFrame`
        :paramref:`~component_loads.x-axis_data` and
        :paramref:`~component_loads.labels` have to be provided.

    x-axis_data: ~collections.abc.Iterable, None, default=None
        Iterable representing the x-axis data as in::

            x = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)
            x = range(13)
            x = pandas.date_range(pd.datetime.now().date(),
                                  periods=13, freq='H')

        Note
        ----
        This parameter is only needed when :paramref:`~component_loads.data`
        is **NOT** supplied as a :class:`pandas.DataFrame`. It is ignored
        otherwise.

    labels: ~collections.abc.Iterable, default=[]
        Iterable of strings labeling the data sets in
        :paramref:`component_loads.data`.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than
        :paramref:`~component_loads.data`.

        Note
        ----
        This parameter is only needed when :paramref:`~component_loads.data`
        is **NOT** supplied as a :class:`pandas.DataFrame`. It is ignored
        otherwise.

    colors: ~collections.abc.Iterable, default=[]
        Iterable of color specification string coloring the data sets in
        :paramref:`~component_loads.data`.

        If not empty each plot will be colord accordingly.
        Otherwise matplotlibs default color rotation will be used.

        List of colors stated must be greater equal the stacks to be plotted.

    title: str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    x-axis_label: str, None, default=None
        String labeling the x axis.

        Use ``None`` to not plot the x-axis label. (Note that the x-axis-labels
        are independent of the x-ticks lables)

    y_axis_label: str, None, default=None
        String labeling the y axis.

        Use ``None`` to not plot the y-axis label. (Note that the y-axis-labels
        are independent of the y-ticks lables)

    where: str, default = 'post'
        # https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.step.html

        Define where the steps should be placed:

        'pre': The y value is continued constantly to the left from every x
         position, i.e. the interval (x[i-1], x[i]] has the value y[i].

        'post': The y value is continued constantly to the right from every x
        position, i.e. the interval [x[i], x[i+1]) has the value y[i].

        'mid': Steps occur half-way between the x positions.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes object holding the plotted figure elements.
    """
    # parse data input
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data=np.array(data).transpose())
    else:
        data = data

    fig, ax = plt.subplots()

    if title:
        ax.set_title(title)

    if x_axis_label:
        ax.set_xlabel(x_axis_label)

    if y_axis_label:
        ax.set_ylabel(y_axis_label)

    for pos, column in enumerate(data):
        # https://stackoverflow.com/questions/40766909/suggestions-to-plot-overlapping-lines-in-matplotlib/40767005
        lw = 3 - pos / len(data)
        ls = ['-', '--', '-.', ':', ][pos % 4]

        ax.step(
            x_axis_data if x_axis_data is not None else data.index,
            data[column],
            label=labels[pos] if labels else column,
            linestyle=ls, linewidth=lw,
            c=colors[pos] if colors else None,
            where=where if where else None
        )

    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # rotate both major and minor x axis ticks by 45 degree
    ax.tick_params(axis='x', which='both', labelrotation=45)

    # ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01), ncol=3)
    ax.legend()
    # plt.tight_layout()

    return ax
