"""
:mod:`~tessif.visualize.compare` is a :mod:`tessif` interface allowing
visual comparision between data of the same type but coming different sources.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import collections
import ittools
from scipy.ndimage import zoom
import numbers
import itertools


def pareto2D(data, labels=[], colors=[], xy_labels=('x', 'y'),
             title=None, **kwargs):
    """
    Visualize the optimal results of 2 dependend variables.

    Uses a 2-depth nested sequence or a (2 column MultiIndex)
    :class:`pandas.DataFrame` as data input.

    Plotting is done using :func:`matplotlib.pyplot.plot`.

    Parameters
    ----------
    data: :class:`~collections.abc.Sequence`, :class:`pandas.DataFrame`
        3 depth sequence of the data to be drawn. As in::

            data = [([x1, ..., xN], [y1, ..., yN]), ...]

        Or a 2 column MultiIndex DataFrame as in::

            data = pandas.DataFrame(
                    zip([x1, ..., xN], [y1, ..., yN], ...),
                    colums=pd.MultiIndex.from_tuples(
                        itertools.product(['Case 1', 'Case 2'], ['x', 'y']))
                    )

    labels: :class:`~collections.abc.Sequence`, default=[]
        Sequence of strings labeling the data sets in
        :paramref:`pareto2D.data`.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than :paramref:`~pareto2D.data`

    colors: :class:`~collections.abc.Sequence`, default=[]
        :paramref:`~pareto2D.data`.
        Sequence of color specification string coloring the data sets in

        If not empty each plot will be colord accordingly.
        Otherwise matplotlibs default color rotation will be used.

        Must be of equal length or longer than :paramref:`~pareto2D.data`

    xy_labels: tuple, None, default=('x', 'y')
        2 tuple of axis labeling strings.

        First entry is interpreted as x label, second as y label. All others
        will be ignored.

        Use ``None`` to not plot any axis labels

    title: str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    kwargs:
        kwargs are passed to :func:`matplotlib.pyplot.plot`.

    Return
    -------
    pareto2D_draw : list
        List of :class:`matplotlib.lines.Line2D` objects of the drawn data.

    Example
    -------
    Most simple use case for drawing a pareto front (pf)

    >>> from tessif.visualize import compare
    >>> data=[[1, 2, 3, 4, 5], [10, 3, 2.5, 2.3, 2]]
    >>> pf=compare.pareto2D(data)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pf2d_simple.png
        :align: center
        :alt: alternate text

    3 Pareto Fronts (pfs) in 1 plot:

    >>> data=[([1, 2, 3, 4, 5], [10, 3, 2.5, 2.3, 2]),
    ... ([0.5, 1, 4, 4.5, 5], [12, 4, 3, 2.9, 2.8]),
    ... ([1, 2, 3.8, 4, 5.5], [13, 4.3, 3, 2.5, 1.9])]
    >>> labels=['Case 1', 'Case 2', 'Case 3']
    >>> pfs=compare.pareto2D(data, labels=labels, title='Pareto Front')

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pf2d_3pfs.png
        :align: center
        :alt: alternate text

    1 Pareto Front (pf) using a pandas.DataFrame and using matplotlib's kwargs:

    >>> import pandas as pd
    >>> data = pd.DataFrame(
    ... zip([1, 2, 3, 4, 5], [10, 3, 2.5, 2.3, 2]),
    ... columns=['Costs in €', 'CO$_2$'])
    >>> pf=compare.pareto2D(data, title='Pareto Front',
    ... xy_labels=tuple(data.columns), lw=10)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pf2d_kwargs.png
        :align: center
        :alt: alternate text

    2 Pareto Fronts (pfs) using a MultiIndex pandas.DataFrame:

    >>> import itertools
    >>> data = pd.DataFrame(zip(
    ... [1, 2, 3, 4, 5], [10, 3, 2.5, 2.3, 2],
    ... [1, 2, 3.8, 4, 5.5], [13, 4.3, 3, 2.5, 1.9]),
    ... columns=pd.MultiIndex.from_tuples(
    ... itertools.product(['Case 1', 'Case 2'], ['x', 'y'])))
    >>> pfs=compare.pareto2D(data, title='Pareto Fronts',
    ... labels = list(data.columns.levels[0]),
    ... xy_labels=tuple(data.columns.levels[1]))

    IGNORE;
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: images/Compare_pf2d_multi.png
        :align: center
        :alt: alternate text
    """

    # Handle data input
    x = []
    y = []
    if isinstance(data, collections.abc.Sequence):
        # make sure data is a 3 nested sequence as in
        # [([x], [y]), ([x], [y]) ([x], [y])]
        data = ittools.nestify(ittools.itrify(data), 3)

        # iterate through every data_set:
        for pos, data_set in enumerate(data):
            # ... to append x and y data respectively
            x.append(data_set[0])
            y.append(data_set[1])

    elif isinstance(data, pd.DataFrame):
        if isinstance(data.columns, pd.core.indexes.multi.MultiIndex):
            for data_set in data.columns.levels[0]:
                x.append(data[data_set].iloc[:, 0])
                y.append(data[data_set].iloc[:, 1])
        else:
            x.append(data.iloc[:, 0])
            y.append(data.iloc[:, 1])

    else:
        raise TypeError(
            'data is of type {} which could not be'.format(type(data)) +
            'handled. Refer to functions docstring for viable data types')

    # Draw pareto plot
    f = plt.figure()
    ax = f.add_subplot(1, 1, 1)

    # Set title:
    if title:
        ax.set_title(title)

    # Set axis labels:
    if xy_labels:
        ax.set_xlabel(xy_labels[0])
        ax.set_ylabel(xy_labels[1])

    # do the plotting:
    lines = []
    for pos, plot_data in enumerate(zip(x, y)):
        lines.append(ax.plot(
            # pass data
            plot_data[0], plot_data[1],
            label=labels[pos] if labels else None,
            c=colors[pos] if colors else None,
            # tweak color:
            **kwargs))

    if labels:
        ax.legend()

    return lines


def interpolate_pareto3D(
        data, interpolation_type='linear',
        labels=[], cmaps=[], xyz_labels=('x', 'y', 'z'), title=None,
        wireframes=[], scatter={'c': 'r', 'marker': 'o', 's': 20},
        zooming={'zoom': 1, 'order': 1},
        zoom_scatter={'c': 'b', 'marker': 'o', 's': 10}, legend=True,
        **kwargs):
    """
    Visualize the optimal results of 3 dependend variables. Comes down to
    drawing a 3D surface plot out of 3 1D arrays.

    Uses a 3-depth nested sequence or a (3 column MultiIndex)
    :class:`pandas.DataFrame` as data input.

    Plotting is done using `Axes3D.plot_surface
    <https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html#mpl_toolkits.mplot3d.Axes3D.plot_surface>`_.

    Parameters
    ----------
    data: :class:`~collections.abc.Sequence`, :class:`pandas.DataFrame`
        3 depth sequence of the data to be drawn. As in::

            data = [([x1, ..., xN], [y1, ..., yN], [z1, ..., zN]), ...]

        Or a 3 column MultiIndex DataFrame as in::

            data = pandas.DataFrame(
                    zip([x1, ..., xN], [y1, ..., yN], ...),
                    colums=pd.MultiIndex.from_tuples(
                        itertools.product(['Case 1', ..., 'Case N'],
                                          ['x', 'y', 'z']))
                    )

    labels: :class:`~collections.abc.Sequence`, default=[]
        Sequence of strings labeling the data sets in
        :paramref:`~pareto3D.data`.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than :paramref:`~pareto3D.data`

    cmaps: :class:`~collections.abc.Sequence`, default=[]
        Sequence of colormap specification strings for coloring the data sets
        in :paramref:`~interpolate_pareto3D.data`.

        If not empty each plot will be colored accordingly.
        Otherwise matplotlibs default color rotation will be used.

        Must be of equal length or longer than
        :paramref:`~interpolate_pareto3D.data`

        See `available colormaps
        <https://matplotlib.org/3.1.1/gallery/color/colormap_reference.html>`_

    xyz_labels: tuple, None, default=('x', 'y', 'z')
        3 tuple of axis labeling strings.

        First, second, third label are interpreted as x, y, z-label
        respectively. All others will be ignored.

        Use ``None`` to not plot any axis labels

    title : str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    scatter: dict, default={'c':'r', 'marker': 'o', 's':20}
        Draw an additional scatterplot to visualize input data.

        To conifgurate the scatter plot provide respective `kwargs
        <https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.scatter.html>`_
        in this dictionairy.

        Pass something that evaluates to ``False`` during the  ``is scatter:``
        call if you  don't want scatter points to be drawn.
        (i.e. ``{}`` or ``None``)

    wireframes: :class:`~collections.abc.Sequence`, default=[]
        Sequence of bools. Visualize the data set as a wireframe plot instead
        of a surface plot if respective entry is``True``.

        Must be of equal length or longer than
        :paramref:`~interpolate_pareto3D.data`

    zooming : dict, default={zoom=1, order=1}
        Use the `scipy's zoom utility
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.zoom.html>`_
        to generate additional data points.

        Highly unscientific depending on the context used. Nonetheless quite
        beautifull and handy in times.

    zoom_scatter: dict, default={'c': 'b', 'marker': 'o', 's':10}
        Creates zoomed scatter points if zooming['zoom'] > 1. See also
        :paramref:`~interpolate_pareto3D.scatter`.

    legend: bool, default=True
        Draws a legend describing :paramref:`~interpolate_pareto3D.scatter` and
        :paramref:`~interpolate_pareto3D.zoom_scatter` if ``True`` and one of
        the beforenamed scatter plots is drawn.

    **kwargs:
        kwargs are passed to `Axes3D.plot_surface
        <https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html#mpl_toolkits.mplot3d.Axes3D.plot_surface>`_

    Return
    -------
    pfs : list
        List of `Collections of 3D polygons
        <https://matplotlib.org/mpl_toolkits/mplot3d/api.html#mpl_toolkits.mplot3d.art3d.Poly3DCollection>`_
        of the drawn data.

    Example
    -------
    Most simple use case for drawing a pareto front (pf):

    >>> from tessif.visualize import compare
    >>> data=([10, 10, 2, 2, 3], [14, 2, 14, 1.8, 3], [1, 3, 3, 4.9, 2])
    >>> pf=compare.interpolate_pareto3D(data)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(0.1)

    IGNORE

    .. image:: images/Compare_pfi3d_simple.png
        :align: center
        :alt: alternate text

    3 Pareto Fronts (pfs) in 1 plot:

    >>> data = [([10, 10, 2, 2, 3], [14, 2, 14, 1.8, 3], [1, 3, 3, 4.9, 2]),
    ...         ([12, 12, 4, 4, 5], [16, 4, 16, 3.8, 5], [3, 5, 5, 7, 2]),
    ...         ([16, 16, 8, 8, 9], [26, 9, 26, 8.8, 9], [7, 9, 9, 11, 6])]
    >>> labels = ['Case 1', 'Case 2', 'Case 3']
    >>> cmaps = ['viridis', 'magma', 'Reds']
    >>> wireframes = [False, True, True]
    >>> pfs = compare.interpolate_pareto3D(
    ...     data, labels=labels, cmaps=cmaps,
    ...     title='Interpolated Pareto Fronts', wireframes=wireframes)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pfi3d_3pfs.png
        :align: center
        :alt: alternate text

    1 Pareto Front (pf) using a pandas.DataFrame and using matplotlib's kwargs
    while getting rid of this pesky scatter plot:

    >>> import pandas as pd
    >>> data = pd.DataFrame(
    ...     zip([12, 12, 4, 4, 5], [16, 4, 16, 3.8, 5], [3, 5, 5, 7, 2]),
    ...     columns=['CO$_2$', 'Ressources Used in $ Equiv', 'Costs in €'])
    >>> pf = compare.interpolate_pareto3D(
    ...     data, title='Interpolated Pareto Front',
    ...     xyz_labels=tuple(data.columns), scatter=None)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(0.1)

    IGNORE

    .. image:: images/Compare_pfi3d_kwargs.png
        :align: center
        :alt: alternate text

    2 Pareto Fronts (pfs) using a MultiIndex pandas.DataFrame and zoom in:

    >>> import itertools
    >>> data = pd.DataFrame(
    ...     zip([10, 10, 2, 2, 3], [14, 2, 14, 1.8, 3], [1, 3, 3, 4.9, 2],
    ...         [16, 16, 8, 8, 9], [26, 9, 26, 8.8, 9], [7, 9, 9, 11, 6]),
    ...     columns=pd.MultiIndex.from_tuples(
    ...         itertools.product(['Case 1', 'Case 2'], ['x', 'y', 'z'])))
    >>> pfs = compare.interpolate_pareto3D(
    ...     data,
    ...     title='Zoomed Interpolated Pareto Fronts',
    ...     labels = list(data.columns.levels[0]),
    ...     cmaps = ['jet', 'magma'],
    ...     xyz_labels=tuple(data.columns.levels[1]),
    ...     zooming={'zoom': 2, 'order': 1},
    ...     wireframes=[False, True])

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: images/Compare_pfi3d_multi.png
        :align: center
        :alt: alternate text

    """

    # Handle data input
    x = []
    y = []
    z = []
    length = 1

    if isinstance(data, collections.abc.Sequence):
        # make sure data is a 3 nested sequence as in
        # [([x], [y]), ([x], [y]) ([x], [y])]
        data = ittools.nestify(ittools.itrify(data), 3)

        # iterate through every data_set:
        for pos, data_set in enumerate(data):
            # ... to append x and y data respectively
            x.append(data_set[0])
            y.append(data_set[1])
            z.append(data_set[2])
        # length of data set euqals len(data).
        length = len(data)

    elif isinstance(data, pd.DataFrame):
        if isinstance(data.columns, pd.core.indexes.multi.MultiIndex):
            for data_set in data.columns.levels[0]:
                x.append(data[data_set].iloc[:, 0])
                y.append(data[data_set].iloc[:, 1])
                z.append(data[data_set].iloc[:, 2])

        else:
            x.append(data.iloc[:, 0])
            y.append(data.iloc[:, 1])
            z.append(data.iloc[:, 2])
        # length equals len() of one of the lists:
        length = len(x)

    else:
        raise TypeError(
            'data is of type {} which could not be'.format(type(data)) +
            'handled. Refer to functions docstring for viable data types')

    # handle wireframe demands:
    wfs = []  # alias wireframes to prevent unexpected bahaviour
    for i in range(length):
        wfs.append(wireframes[i] if wireframes else False)

    # Draw pareto plot
    # Use GridSpec for easy and intuitive subplot creation
    gs = mpl.gridspec.GridSpec(nrows=1, ncols=30)
    fig = mpl.pyplot.figure()

    # Create a 3D subplot in the first 30-len(data) columns

    ax = fig.add_subplot(gs[:-2*length], projection="3d")
    ax.set_proj_type('ortho')
    # Create a 3D subplot in the last 2*length columns
    cb_axes = []
    for i in range(length):
        cb_axes.append(fig.add_subplot(gs[-2*(i+1)]))

    # Set title:
    if title:
        ax.set_title(title)

    # Set axis labels:
    if xyz_labels:
        ax.set_xlabel(xyz_labels[0])
        ax.set_ylabel(xyz_labels[1])
        ax.set_zlabel(xyz_labels[2])

    # do the plotting:
    surfaces = []
    for pos, plot_data in enumerate(zip(x, y, z)):

        # prepare the data be 3 2D arrays:
        linx = np.linspace(
            round(min(plot_data[0])), round(max(plot_data[0])),
            round(max(plot_data[0])) - round(min(plot_data[0]))+1)
        liny = np.linspace(
            round(min(plot_data[1])), round(max(plot_data[1])),
            round(max(plot_data[1])) - round(min(plot_data[1]))+1)

        X, Y = np.meshgrid(plot_data[0], plot_data[1])
        X, Y = np.meshgrid(linx, liny)

        # interpolate the missing data
        Z = griddata(
            (np.array(plot_data[0]), np.array(plot_data[1])),
            np.array(plot_data[2]),
            (X, Y),
            method=interpolation_type)

        # zoom in:
        Xzoom = zoom(X, **zooming)
        Yzoom = zoom(Y, **zooming)
        Zzoom = zoom(Z, **zooming)

        # Get colormap
        cmap = mpl.pyplot.get_cmap(name=cmaps[pos] if cmaps else 'jet')
        # Normalize colormap to plot data
        normalize = mpl.colors.Normalize(
            vmin=Zzoom.min(),
            vmax=Zzoom.max())

        # Visualize zoomed data as scatter points if an acutal zoom occured:
        zdata = None
        if zoom_scatter and zooming['zoom'] > 1:
            zdata = ax.scatter(
                Xzoom, Yzoom, Zzoom,
                label='Zoomed data', **zoom_scatter)

        # Visualize input data as scatter points:
        idata = None
        if scatter:
            idata = ax.scatter(X, Y, Z, label='Input data', **scatter)

        # Draw scatter legend if requested:
        if legend:
            handles = []
            # and input data handle if used
            if idata:
                handles.append(idata)
            # add zoomed data handle if used
            if zdata:
                handles.append(zdata)
            # pass handles to legend drawing utility
            if handles:
                ax.legend(handles=handles)

        # 3D plot is requested be a colored wireframe plot:
        if wfs[pos]:

            # Draw the 3D surface plot
            wfp = ax.plot_surface(
                Xzoom, Yzoom, Zzoom,
                vmin=0, vmax=Z.max(),
                facecolors=cmap(normalize(Zzoom)),
                shade=False)
            wfp.set_facecolors((0, 0, 0, 0))
            surfaces.append(wfp)
        else:
            # 3D plot is requested be a surface plot:
            surfaces.append(ax.plot_surface(
                # pass data
                Xzoom, Yzoom, Zzoom,
                label=labels[pos] if labels else None,
                cmap=cmap,
                norm=normalize,
                ** kwargs))

        # Visualize input data as scatter points:
        if scatter:
            ax.scatter(
                xs=plot_data[0], ys=plot_data[1], zs=plot_data[2],
                **scatter)

        # Draw the colorbar
        mpl.colorbar.ColorbarBase(ax=cb_axes[pos], cmap=cmap, norm=normalize,
                                  label=labels[pos] if labels else None,)

        # Change axis so (0, 0, 0) is in the far bottom left corner:
        ax.set_xlim(0, max(plot_data[0]))
        ax.set_ylim(max(plot_data[1]), 0)

    return surfaces


def pareto3D(data, labels=[], cmaps=[], xyz_labels=('x', 'y', 'z'), title=None,
             wireframes=[], scatter={'c': 'r', 'marker': 'o', 's': 20},
             zooming={'zoom': 1, 'order': 1},
             zoom_scatter={'c': 'b', 'marker': 'o', 's': 10}, legend=True,
             **kwargs):
    """
    Optimal results of 1 variable dependend of 2 other. Comes down to drawing
    a 3D plot out of 2 1D arrays  and 1 2D array.

    Uses a 3-depth nested sequence or a list of 3 column
    class:`pandas.DataFrame` as data input.

    Plotting is done using :func:`matplotlib.pyplot.plot`.

    Parameters
    ----------
    data: :class:`~collections.abc.Sequence`
        3 depth sequence of the data to be drawn. As in::

            data = [([x1, ..., xN], [y1, ..., yN],
                    [z(x1, y1), ..., z(xN, y1)],[z(x1, yN), ..., z(xN, yN)]),
                   ...]

        Or an sequence of :class:`pandas.DataFrame` as in::

            data = [pandas.DataFrame(
                        [z(x1, yN), ..., z(xN, yN)], colums=[i for i in x],
                        index[i for i in y]),
                    pandas.DataFrame(
                        [z(x1, yN), ..., z(xN, yN)], colums=[i for i in x],
                        index[i for i in y])]

    labels: :class:`~collections.abc.Sequence`, default=[]
        Sequence of strings labeling the data sets in
        :paramref:`~pareto3D.data`.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than :paramref:`~pareto3D.data`

    cmaps: :class:`~collections.abc.Sequence`, default=[]
        Sequence of colormap specification strings for coloring the data sets
        in :paramref:`~interpolate_pareto3D.data`.

        If not empty each plot will be colored accordingly.
        Otherwise matplotlibs default color rotation will be used.

        Must be of equal length or longer than
        :paramref:`~interpolate_pareto3D.data`

        See `available colormaps
        <https://matplotlib.org/3.1.1/gallery/color/colormap_reference.html>`_

    xyz_labels: tuple, None, default=('x', 'y', 'z')
        3 tuple of axis labeling strings.

        First, second, third label are interpreted as x, y, z-label
        respectively. All others will be ignored.

        Use ``None`` to not plot any axis labels

    title : str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    scatter: dict, default={'c':'r', 'marker': 'o', 's':20}
        Draw an additional scatterplot to visualize input data.

        To conifgurate the scatter plot provide respective `kwargs
        <https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.scatter.html>`_
        in this dictionairy.

        Pass something that evaluates to ``False`` during the  ``is scatter:``
        call if you  don't want scatter points to be drawn.
        (i.e. ``{}`` or ``None``)

    wireframes: :class:`~collections.abc.Sequence`, default=[]
        Sequence of bools. Visualize the data set as a wireframe plot instead
        of a surface plot if respective entry is``True``.

        Must be of equal length or longer than
        :paramref:`~interpolate_pareto3D.data`

    zooming : dict, default={zoom=1, order=1}
        Use the `scipy's zoom utility
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.zoom.html>`_
        to generate additional data points.

        Highly unscientific depending on the context used. Nonetheless quite
        beautifull and handy in times.

    zoom_scatter: dict, default={'c': 'b', 'marker': 'o', 's':10}
        Creates zoomed scatter points if zooming['zoom'] > 1. See also
        :paramref:`~interpolate_pareto3D.scatter`.

    legend: bool, default=True
        Draws a legend describing :paramref:`~interpolate_pareto3D.scatter` and
        :paramref:`~interpolate_pareto3D.zoom_scatter` if ``True`` and one of
        the beforenamed scatter plots is drawn.

    **kwargs:
        kwargs are passed to `Axes3D.plot_surface
        <https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html#mpl_toolkits.mplot3d.Axes3D.plot_surface>`_

    Return
    -------
    pfs : list
        List of `Collections of 3D polygons
        <https://matplotlib.org/mpl_toolkits/mplot3d/api.html#mpl_toolkits.mplot3d.art3d.Poly3DCollection>`_
        of the drawn data.

    Example
    -------
    Most simple use case for drawing a pareto front (pf):

    >>> from tessif.visualize import compare
    >>> data=([5, 2, 1], [30, 20, 10], [[2, 3, 4], [6, 8, 12], [8, 10, 20]])
    >>> pf=compare.pareto3D(data)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pf3d_simple.png
        :align: center
        :alt: alternate text

    2 Pareto Fronts (pfs) in 1 plot:

    >>> data=[([5, 2, 1], [30, 20, 10], [[2, 3, 4], [6, 8, 12], [8, 10, 20]]),
    ... ([5, 2, 1], [30, 20, 10], [[4, 5, 6], [8, 10, 14], [10, 12, 22]])]
    >>> labels=['Case 1', 'Case 2']
    >>> cmaps=['viridis', 'magma']
    >>> wireframes=[False, True]
    >>> pfs=compare.pareto3D(
    ... data, labels=labels, cmaps=cmaps, title='Zoomed Pareto Fronts',
    ... wireframes=wireframes, zooming={'zoom': 2, 'order': 1})

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pf3d_2pfs_wire.png
        :align: center
        :alt: alternate text


    1 Pareto Front (pf) using a pandas.DataFrame and using matplotlib's kwargs
    while getting rid of this pesky scatter plot:

    >>> import pandas as pd
    >>> x = [30, 20, 10]
    >>> y = [5, 2, 1]
    >>> data = pd.DataFrame(
    ... [[2, 3, 4], [6, 8, 12], [8, 10, 20]],
    ... index=[i for i in y],
    ... columns=[i for i in x])
    >>> xyz_labels=['CO$_2$', 'Ressources Used in $ Equiv', 'Costs in €']
    >>> pf=compare.pareto3D(data, title='Pareto Front',
    ... xyz_labels=xyz_labels, scatter=None)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_pf3d_kwargs.png
        :align: center
        :alt: alternate text



    2 Pareto Fronts (pfs) using a list of  pandas.DataFrames:

    >>> x = [30, 20, 10]
    >>> y = [5, 2, 1]
    >>> xyz_labels=['CO$_2$', 'Ressources Used in $ Equiv', 'Costs in €']
    >>> data = [pd.DataFrame(
    ... [[2, 3, 4], [6, 8, 12], [8, 10, 20]],
    ... index=[i for i in y],
    ... columns=[i for i in x]),
    ... pd.DataFrame(
    ... [[4, 5, 6], [8, 10, 14], [10, 12, 22]],
    ... index=[i for i in y],
    ... columns=[i for i in x])]
    >>> pfs=compare.pareto3D(data, title='Pareto Fronts',
    ... labels = ['Case 1', 'Case 2'],
    ... cmaps = ['jet', 'magma'],
    ... xyz_labels=xyz_labels)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: images/Compare_pf3d_2pfs.png
        :align: center
        :alt: alternate text
    """

    # Handle data input
    x = []
    y = []
    z = []
    length = 1

    # docstring calls for [pd.DataFrame] but be liberal in what you accept
    if isinstance(data, pd.DataFrame):
        data = [data]

    if isinstance(data[0], collections.abc.Sequence):
        # make sure data is a 3 nested sequence as in
        # [([x], [y], [z]), ([x], [y], [z]) ([x], [y], [z])]
        data = ittools.nestify(ittools.itrify(data), 4)

        # iterate through every data_set:
        for pos, data_set in enumerate(data):
            # ... to append x and y data respectively
            x.append(data_set[0])
            y.append(data_set[1])
            z.append(np.array(data_set[2]))
        # length of data set euqals len(data).
        length = len(data)

    elif isinstance(data[0], pd.DataFrame):
        for data_set in data:
            x.append(data_set.columns.values)
            y.append(data_set.index.values)
            z.append(data_set.values)

        # length equals len() of one of the lists:
        length = len(x)

    else:
        raise TypeError(
            'data is of type {} which could not be'.format(type(data)) +
            'handled. Refer to functions docstring for viable data types')

    # handle wireframe demands:
    wfs = []  # alias wireframes to prevent unexpected bahaviour
    for i in range(length):
        wfs.append(wireframes[i] if wireframes else False)

    # Draw pareto plot
    # Use GridSpec for easy and intuitive subplot creation
    gs = mpl.gridspec.GridSpec(nrows=1, ncols=30)
    fig = mpl.pyplot.figure()

    # Create a 3D subplot in the first 30-len(data) columns

    ax = fig.add_subplot(gs[:-2*length], projection="3d")
    ax.set_proj_type('ortho')
    # Create a 3D subplot in the last 2*length columns
    cb_axes = []
    for i in range(length):
        cb_axes.append(fig.add_subplot(gs[-2*(i+1)]))

    # Set title:
    if title:
        ax.set_title(title)

    # Set axis labels:
    if xyz_labels:
        ax.set_xlabel(xyz_labels[0])
        ax.set_ylabel(xyz_labels[1])
        ax.set_zlabel(xyz_labels[2])

    # do the plotting:
    surfaces = []
    for pos, plot_data in enumerate(zip(x, y, z)):

        # prepare the x-y data be 2D arrays:
        X, Y = np.meshgrid(plot_data[0], plot_data[1])
        Z = plot_data[2]

        # Get colormap
        cmap = mpl.pyplot.get_cmap(name=cmaps[pos] if cmaps else 'jet')
        # Normalize colormap to plot data
        normalize = mpl.colors.Normalize(
            Z.min(),
            Z.max())

        # zoom in:
        Xzoom = zoom(X, **zooming)
        Yzoom = zoom(Y, **zooming)
        Zzoom = zoom(Z, **zooming)

        # Visualize zoomed data as scatter points if an acutal zoom occured:
        zdata = None
        if zoom_scatter and zooming['zoom'] > 1:
            zdata = ax.scatter(
                Xzoom, Yzoom, Zzoom,
                label='Zoomed data', **zoom_scatter)

        # Visualize input data as scatter points:
        idata = None
        if scatter:
            idata = ax.scatter(X, Y, Z, label='Input data', **scatter)

        # Draw scatter legend if requested:
        if legend:
            handles = []
            # and input data handle if used
            if idata:
                handles.append(idata)
            # add zoomed data handle if used
            if zdata:
                handles.append(zdata)
            # pass handles to legend drawing utility
            if handles:
                ax.legend(handles=handles)

        # 3D plot is requested be a colored wireframe plot:
        if wfs[pos]:

            # Draw the 3D surface plot
            wfp = ax.plot_surface(
                Xzoom, Yzoom, Zzoom,
                vmin=0, vmax=Zzoom.max(),
                facecolors=cmap(normalize(Zzoom)),
                shade=False,
                **kwargs)
            wfp.set_facecolors((0, 0, 0, 0))
            surfaces.append(wfp)
        else:
            # 3D plot is requested be a surface plot:
            surfaces.append(ax.plot_surface(
                # pass data
                Xzoom, Yzoom, Zzoom,
                label=labels[pos] if labels else None,
                cmap=cmap,
                norm=normalize,
                ** kwargs))

        # Draw the colorbar
        mpl.colorbar.ColorbarBase(ax=cb_axes[pos], cmap=cmap, norm=normalize,
                                  label=labels[pos] if labels else None,)

        # Change axis so (0, 0, 0) is in the far bottom left corner:
        ax.set_xlim(0, max(plot_data[0]))
        ax.set_ylim(max(plot_data[1]), 0)

    return surfaces


def best_bar(data, method=np.mean, duplicate=True, lowest=True, descriptive='',
             indicator_labels=[], colors=[], set_labels=[], title=None,
             **kwargs):
    r"""
    Compare different bar plotted data sets containing the same kind of data.
    Choose a best candidate depending on :paramref:`~best_bar.method`.

    Uses a 2-depth nested sequence or a :class:`pandas.DataFrame` as data
    input.

    Plotting is done using :func:`matplotlib.pyplot.bar`.

    Parameters
    ----------
    data: :class:`~collections.abc.Sequence` or a :class:`pandas.DataFrame`
        2 depth sequence of the data to be drawn. As in::

            data = [(indicator1, ..., indicatorN), ...]

        Or a DataFrame as in::

            data = pandas.DataFrame(
                    [(indicator1, ..., indicatorN), ...],
                    colums=['indicator1', ..., 'indicatorN])
                    )

    method: str, functional, default=np.mean
        Comparative method to choose the best candidate.

        If an indicator(column) name is provided datasets are compared based
        on it, depending on :paramref:`~best_bar.lowest`

        If a functional is provided it is passed to `pandas.DataFrame.apply
        <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.apply.html>`_
        and evaluated depending on :paramref:`~best_bar.lowest`.

        Use ``'rmin'`` or ``'rmax'`` (as str) to evaluate min/max of the sum
        of the data sets. :paramref:`~best_bar.lowest` will be ignored then.

        Note
        ----
        `pandas.DataFrame.apply
        <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.apply.html>`_
        also accepts strings of `pandas.DataFrame attributes
        <https://pandas.pydata.org/pandas-docs/stable/reference/frame.html>`_.
        For improved readability however it is recommended to state the
        functionals as functionals.

    lowest: bool, default=True
        Decide if lowest (``True``) or highest (``False``)  method value is
        considered best.

    duplicate: bool, default=True
        Best candidate(s) is(are) copied/moved to the end for visual
        highlighting for True/False respectively.

    descriptive : str, default=''
        String describing the best candidate evaluation method
        above the bar plot.

        When default is used a descriptive is tried to be inferred
        from following standard descriptives:

        - :math:`\min\left(\sum data \right)` for ``'rmin'``
        - :math:`\max\left(\sum data \right)` for ``'rmax'``
        - :math:`\min\left(data \right)` for ``'min'``
        - :math:`\max\left(data \right)` for ``'max'``
        - :math:`\text{mean}\left(data \right)` for ``'np.mean'``
        - :math:`\text{std}\left(data \right)` for ``'np.std'``

        Or in case an indicator label name was passed from
        :paramref:`~best_bar.indicator_labels`.

    indicator_labels: sequence of str, default = []
        Sequence of strings labeling the indicators of the
        :paramref:`~best_bar.data` subsets.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than the nested sequences in
        :paramref:`~best_bar.data`.

    colors: sequence of color strings, default = []
        color specifications for the data sets in :paramref:`~best_bar.data`.

        If not empty each bar will be colored accordingly.
        Otherwise matplotlibs default color rotation will be used.

        Must be of equal length or longer than the nested sequences in
        :paramref:`~best_bar.data`

    set_labels: :class:`collections.abc.Sequence`, default=[]
        labels for the data sets in :paramref:`bar.data`.

        If not empty an x-axis label will be drawn for each item.

        Must be of equal length or longer than :paramref:`bar.data`

    title: str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    kwargs: dict
        kwargs are passed to :func:`matplotlib.pyplot.bar`.

    Return
    -------
    bars : list
        List of :class:`~matplotlib.container.BarContainer` objects
        representing the drawn data.

    Example
    -------
    Most simple use case for drawing a comparitive bar plot

    >>> from tessif.visualize import compare
    >>> data = [(1, 2, 2), (1, 2, 3), (3, 2, 1), (2, 2, 2)]
    >>> bars = compare.best_bar(data)

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_bar_simple.png
        :align: center
        :alt: alternate text

    Modify the evaluation method, add a nicer description and get rid of the
    ugly duplicates:

    >>> data=[(1, 2, 2, 3), (1, 2, 3, 4), (4, 3, 2, 1), (2, 3, 2, 2)]
    >>> bars=best_bar(
    ...     data, method=np.std, duplicate=False,
    ...     descriptive='standard deviation')

    .. image:: images/Compare_bar_noduplicate.png
        :align: center
        :alt: alternate text

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    A simplified use case for an energy system analysis:

    >>> bars=best_bar(
    ...     data,
    ...     method=np.mean,
    ...     lowest=False,
    ...     indicator_labels=['Costs', 'CO$_2$', 'Ressources', 'Land Usage'],
    ...     colors=['gold', 'black', 'blue', 'green'],
    ...     set_labels=['Sufficiency', 'Wind', 'Storage', 'Wind&Solar'],
    ...     title='Renewables, CHP, Storage - Northern Germany')

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(.1)

    IGNORE

    .. image:: images/Compare_bar_es_simple.png
        :align: center
        :alt: alternate text

    Everybody wants to use pandas.DataFrames because they are awesome. Make
    sure to transform the indices and columns to lists!

    This Example use an indicator as evaluatoin method:

    >>> df=pd.DataFrame(data,
    ... index=['Sufficiency', 'Wind', 'Storage', 'Wind&Solar'],
    ... columns=['Costs', 'CO$_2$', 'Ressources', 'Land Usage'])
    >>> bars=best_bar(
    ...     data,
    ...     method='Costs',
    ...     lowest=True,
    ...     duplicate=False,
    ...     indicator_labels=df.columns.tolist(),
    ...     set_labels=df.index.tolist(),
    ...     title='Renewables, CHP, Storage - Northern Germany')

    IGNORE:
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: images/Compare_bar_es_dataframe.png
        :align: center
        :alt: alternate text
    """

    # Is data passed as sequence ?
    if isinstance(data, collections.abc.Sequence):
        # yes, so transform it into a DataFrame for data science
        data = ittools.nestify(data, 2)
        df = pd.DataFrame(
            data,
            index=set_labels if set_labels else None,
            columns=indicator_labels if indicator_labels else None)

    # map row summing functionals to respective strings
    # allows distinguishing max from rmax (which is max(sum()))
    rfunctionals = {'rmin': min, 'rmax': max}

    # map indicator labels (columns) to 'label' for annotating best candidate
    best_column = {k: '\'{}\''.format(v)
                   for k, v in zip(df.columns, df.columns)}

    # map frequently used methods to their default annotation string
    mannotate = {
        'rmin': '$\\min\\left(\\sum data \\right)$',
        'rmax': '$\\max\\left(\\sum data \\right)$',
        np.mean: '$mean\\left(data \\right)$',
        np.std: '$std\\left(data \\right)$',
    }

    # add indicator labels to themethod  annotation map
    mannotate.update({**best_column})

    # Figure out the best case:
    best_count = 0
    best_value = 0
    # method is an actual column provided:
    if method in df.columns:
        # lowest is the best ?
        if lowest is True:
            # yes, so get the lowest value
            best_value = df.min(axis='index')[method]
        else:
            #  no, so get the highest value
            best_value = df.max(axis='index')[method]

        # extract the rows(indices) containing the best value
        best_data_set = df.loc[df[method] == best_value]

    # method is not a column provided but is it a summing functional ?
    elif method in rfunctionals.keys():
        # yes, so select the right one:
        functional = rfunctionals[method]

        # calc sum of each row and use the rfunctional to compute best value
        best_value = functional(df.sum(axis='columns'))
        # extract the rows (indices) of which the sum equals the best value
        best_data_set = df.loc[df.sum(axis='columns') == best_value]
    else:
        # no its an 'apply-on-each-cell' functional
        if lowest is True:
            # compute the best value as minimum
            best_value = min(df.apply(method, axis='columns'))
        else:
            # compute the best value as maximum
            best_value = max(df.apply(method, axis='columns'))

        # extract the rows (indices) containing the best value
        best_data_set = df.loc[df.apply(method, axis='columns') == best_value]

    # count the number of datasets having the best value
    best_count = len(best_data_set.index)
    # add the best datasets to the end for visual highlighting
    df = df.append(best_data_set)

    # remove duplicates if requested
    if not duplicate:
        df = df.drop_duplicates(keep='last')

    # Draw annotated bar plot
    f = plt.figure()
    ax = f.add_subplot(1, 1, 1)

    # Set title:
    if title:
        ax.set_title(title)

    # calculate x vector the bars are plot on:
    x = np.arange(len(df.index))

    # calculate the data_set length (nested sequence of data):
    dsl = len(list(zip(*df.to_numpy())))
    bar_width = 1 / dsl - 0.1

    # draw bars
    for pos, indicator in enumerate(zip(*df.to_numpy())):
        ax.bar(
            x + (pos-dsl/2) * bar_width + bar_width/2,
            indicator, width=bar_width,
            color=colors[pos] if colors else None,
            label=df.columns[pos] if indicator_labels else None)

    # plot vertical line to separte best from all
    plt.axvline(len(df.index)-best_count-0.5, c='k')

    # if a column value is considered best emphasize it by drawing a
    # horizontal line
    if method in df.columns:
        plt.axhline(best_value, c='k', ls='--', lw=0.5)

    # annotate best candidate(s):
    # expand yaxis so the best candidate annotiation/highest bar fits
    ax.set_ylim(0, max([max(best_data_set.max()) + 0.5, max(df.max())]))

    # figue out method annotation:
    # was the parameter used ?
    if descriptive:
        # yes, so just utilize the user input
        mannotation = descriptive
    elif method in mannotate:
        # no, so try falling back on a default description
        mannotation = mannotate[method]
    else:
        # no, and no default description, so just show the ugly truth:
        mannotation = str(method)

    # is best value a float ?
    if isinstance(best_value, float):
        # yes, so limit shown output to 2 decimals
        best_value = round(best_value, 2)

    # create the annotation label:
    annotation = 'Best candidate{}. Evaluated to \n{} using {}{}'.format(
        's' if best_count > 1 else '',  # plural s if not just 1 best candidate
        best_value,  # inform user of best value by displaying it
        '' if method in rfunctionals  # state 'lowest'/'highest' if meaningfull
        else 'lowest ' if lowest else 'highest ',
        mannotation   # add the freshly constructed method string
    )

    # draw the annotation:
    ax.annotate(annotation,  # the freshly constructed annotation string
                xy=(len(df.index) - (best_count/2 + 0.5),  # x position
                    max(best_data_set.max())+0.2),  # y position
                xytext=(0, 0),  # (x,y) offset
                textcoords="offset points",  # dimension of xy
                ha='center', va='bottom')

    # Use number of data_sets i.e len(data) as x ticks
    ax.set_xticks(x)

    # Are the data sets labeled ?
    if set_labels:
        # yes, so show the set labels on x ticks.
        ax.set_xticklabels(df.index)

    # Are the indicators labeled ?
    if indicator_labels:
        # yes, so display them as legend
        # Adjust legend location:
        # get bounding box of current plot:
        bbox = ax.get_position()
        # shrink bounding box to 80% of original width
        ax.set_position([bbox.x0, bbox.y0, bbox.width*0.8, bbox.height])
        plt.legend(
            labelspacing=1,
            bbox_to_anchor=(1.0, 1),
            loc='upper left',)


def bar(data, indicator_labels=[], colors=[], set_labels=[], title=None,
        **kwargs):
    """
    Simple bar plotting utility.

    Used for visually comparing scalar data of the same type among sets
    (usually parameters to compare different scenarios or models).

    Note
    ----
    To automatically choose and visualize a best candidate among
    scenarios/models, consider using :meth:`best_bar`.

    Parameters
    ----------
    data: :class:`~collections.abc.Container` or a :class:`pandas.DataFrame`
        2 levels deep container of the data to be drawn. As in::

            data = [(indicator1, ..., indicatorN), ...]

        Or a :class:`~pandas.DataFrame` as in::

            data = pandas.DataFrame(
                    [(indicator1, ..., indicatorN), ...],
                    colums=['indicator1', ..., 'indicatorN])
                    )

        The number of indicators (the length of the nested container or the
        number of columns inside the data frame) equals the number of bars to
        drawn per set.

        The number of sets is determined by the number of entries in the top
        level container or the number of rows inside the data frame.

    indicator_labels: sequence of str, default = []
        Sequence of strings labeling the indicators of the
        :paramref:`~best_bar.data` subsets.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than the nested sequences in
        :paramref:`~best_bar.data`.

    colors: sequence of color strings, default = []
        color specifications for the data sets in :paramref:`~best_bar.data`.

        If not empty each bar will be colored accordingly.
        Otherwise matplotlibs default color rotation will be used.

        Must be of equal length or longer than the nested sequences in
        :paramref:`~best_bar.data`

    set_labels: :class:`collections.abc.Sequence`, default=[]
        labels for the data sets in :paramref:`bar.data`.

        If not empty an x-axis label will be drawn for each item.

        Must be of equal length or longer than :paramref:`bar.data`

    title: str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    kwargs: dict
        kwargs are passed to :func:`matplotlib.pyplot.bar`.
    """
    pass


def bar3D(data, xy_data=None, labels=[], colors=[],
          xyz_labels=('x', 'y', 'z'), title=None):
    """
    Visualize a variable dependend on two others as a field of (stacked) bars.

    Designed for visualizing the :mod:`scalibility assessment
    <tessif.analyze.assess_scalability>` when comparing different energy
    system simulation models.

    TODOS:

    1.) Implement all the parameters listed below
    2.) Make the plot prettier
    3.) Create the 2 example in the example section at the end of this docstring


    Parameters
    ----------
    data: :class:`~collections.abc.Container` or a :class:`pandas.DataFrame`
        2 levels deep container holding the of the data to be drawn. As in::

            data = [[z(x1, y1), ... z(xN, y1,)],
                    ...
                    [z(xN, y1), ... z(xN, yN,)]]

        Or a DataFrame as in::

            data = pandas.DataFrame(
                    data = [[z(x1, y1), ... z(xN, y1,)],
                            ...
                            [z(xN, y1), ... z(xN, yN,)]
                           ],
                    colums=x_values,
                    index=y_values)
                    )

        Warning
        -------
        If providing data **NOT** as a :class:`pandas.DataFrame`
        :paramref:`~bar3D.xy_data` has to be provided.

    xy_data: tuple, None, default=None
        2 tuple containing the data for the x and y-axis repsectively.

        First entry will be interpreted as x-axis data, second as y-axis data.
        All others will be ignored. An examplary tuples could be::

            xy = ((1, 2, 3, 4, 5, 6), (2, 3, 4, 5, 1, 3, 10))
            xy = (range(12), range(0, 24,2))

        Warning
        -------
        This parameter is only needed when :paramref:`~bar3D.data` is **NOT**
        supplied as a :class:`pandas.DataFrame`. It is ignored otherwise.

    labels: :class:`~collections.abc.Sequence`, default=[]
        Sequence of strings labeling the data sets in
        :paramref:`bar3D.data`.

        If not empty a legend entry will be drawn for each item.

        Must be of equal length or longer than :paramref:`~bar3D.data`

    colors: :class:`~collections.abc.Sequence`, default=[]
        Sequence of color specification string coloring the data sets in
        :paramref:`~bar3D.data`.

        If not empty each plot will be colord accordingly.
        Otherwise matplotlibs default color rotation will be used.

        Number of colors stated must be greater equal the number of stacks to
        be plotted.

    xyz_labels: tuple, None, default=('x', 'y')
        3 tuple of axis labeling strings.

        First entry is interpreted as x label, second as y label, third as z
        label. All others will be ignored.

        Use ``None`` to not plot any axis labels

    title: str, default=None
        Title to be shown above the plot. If ``None`` no title will be drawn.

    Examples
    --------
    """
    # baseline example taken from https://stackoverflow.com/a/38088169
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # label and title setting needs to repsect parameters
    ax.set_xlabel("N")
    ax.set_ylabel("T")
    ax.set_zlabel("time/memory")
    # ax.set_xlim3d(0, 10)
    # ax.set_ylim3d(0, 10)

    if isinstance(data, pd.DataFrame):
        x = data.columns.tolist()
        y = data.index.tolist()
        z = data.to_numpy()
    else:
        x = xy_data[0]
        y = xy_data[1]
        z = data

    # # +BEGIN_EXAMPLE
    # # -----------------------------------------------------------------------
    # # the 2 examples below should be used to visualize the bar3D in its
    # # example section in the docstring above

    # y = [10, 20, 30]  # this is t
    # x = [1, 2, ]  # this is n

    # # z(N, T) describes (z(N1, T),...,z(NN, T)
    # # this is the form the results come out of assess_scalability's DataFrame
    # # in case there is only a single measurement for each N/T combination
    # # z = [[1, 2], [3, 4], [4, 6]]

    # # this is the form the results come out of assess_scalability's DataFrame
    # # in case there is an array of measurements for each N/T combination
    # z = [[(1, 1, 1, 1, 3, 2), (1, 1, 1, 2, 6, 4)],
    #      [(1, 1, 1, 1, 6, 4), (1, 1, 1, 2, 12, 8)],
    #      [(1, 1, 1, 1, 12, 8), (1, 1, 1, 2, 24, 16)], ]
    # # -----------------------------------------------------------------------
    # # END_EXAMPLE

    X = x * len(y)
    Y = [element for element in y for i in range(len(x))]

    # Parse z (data) dependent on it being a stacked bar plot (3 level deep
    # container) or a simple bar plot (2 levels deep container):
    if isinstance(z[0][0], numbers.Number):
        # z is 2 levels deep, aka a single bar plot
        number_of_stacked_bars = 1
        Z = [list(itertools.chain.from_iterable(z))]

    else:
        # z is 3 levels deep, aka a stacked bar plot
        Z = list(itertools.chain.from_iterable(z))
        Z = list(zip(*Z))
        number_of_stacked_bars = len(Z)

    zpos = np.zeros(len(X))

    # bar width and thickness need some adjustment
    dx = np.ones(len(X))
    dy = np.ones(len(Y))

    _zpos = zpos   # the starting zpos for each bar
    for i in range(number_of_stacked_bars):
        ax.bar3d(X, Y, _zpos, dx, dy, Z[i],
                 color=colors[i] if colors else None)
        # add the height of each bar to know where to start the next
        _zpos += Z[i]

    if title:
        ax.set_title(title)

    return fig


def comp_plot(data_comp_df, title=''):
    """
    Draws hidden components / flows of all models in one figure.
    Designed to detect initial relationships between components.

    Parameters
    ----------
    data_comp_df: pandas.MultiIndex
    MultiIndex, which contains all time series of the pre selected components/flows of all models

    title: str, default=''
        Title to be shown above the plot. If '' no title will be drawn.

    """

    def trim_axs(axs, N):
        """
        Reduce *axs* to *N* Axes. All further Axes are removed from the figure.
        """
        axs = axs.flat
        for ax in axs[N:]:
            ax.remove()
        return axs[:N]

    keys = data_comp_df.keys().get_level_values(0).unique().to_list()
    figsize = (16, 8)
    cols = 2
    if len(keys) % 2 == 0:
        rows = len(keys) // cols
    else:
        rows = len(keys) // cols + 1
    # axes = generate_subplots(len(keys),row_wise=False)
    axes = plt.figure(figsize=figsize, constrained_layout=True).subplots(
        rows, cols, sharex='col')
   # t=0
    if len(keys) % 2 != 0:
        axes = trim_axs(axes, len(keys))
    lines = []
    labels = []
    for key, ax in zip(keys, axes.flat):  # axes):
        ax.set_title(f'{key}', fontsize=16)
        # ,c = colors if colors else None)
        axPLot = ax.plot(data_comp_df[key].abs())
        lines.extend(axPLot)
        labels.extend((data_comp_df[key].columns))
        ax.tick_params(axis='both', which='major', labelsize=11)
        ax.tick_params(axis='both', which='minor', labelsize=11)
        ax.tick_params(axis='x', which='both', labelrotation=45)
        ax.grid()
        # ax.legend(data_comp_df[key].columns)

    lines = list(dict.fromkeys(lines))
    labels = list(dict.fromkeys(labels))
    plt.figlegend(lines, labels, loc=9, fontsize=12, ncol=len(labels))
    plt.suptitle(title, fontsize=15)

    return plt.show()


def pearson_self_comparison(pearson_df, titel_dic_key):
    """
    correlation matrix
    plot a correlation matrix for each model to analyse interrelationships with in each model

    Parameters
    ----------
    pearson_df: pandas.DataFrame
    DataFrame containing the results of the correlation of the models with themselves.

    titel_dic_key: str
        string containing the names of the models or their components / flows.
        these are used for the automatic labeling of the martixes
    """

    labels = pearson_df.columns  # get abbv state names.

    fig = plt.figure(figsize=(14, 14))  # figure so we can add axis
    ax = fig.add_subplot(111)  # define axis, so we can modify
    ax.matshow(pearson_df, cmap=plt.cm.RdYlGn)  # display the matrix
    ax.set_xticks(np.arange(len(labels)))  # show them all!
    ax.set_yticks(np.arange(len(labels)))  # show them all!
    ax.tick_params(axis='x', which='both', labelrotation=90)
    ax.set_xticklabels(labels)  # set to be the abbv (vs useless #)
    ax.set_yticklabels(labels)
    fig.suptitle('Self correlation of model {}'.format(
        str(titel_dic_key)), fontsize=16)

    # values inside the grid
    for (i, j), z in np.ndenumerate(pearson_df):
        ax.text(j, i, '{:0.01f}'.format(z), ha='center', va='center')

    plt.tight_layout(pad=0)

    return ax.figure


def memory_usage(path, parser, model):
    from tessif.analyze import trace_memory
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    stoptime = trace_memory(path, parser, model)

    fig = plt.figure('Time measurement')
    plt.ylabel('time in s')
    plt.xlabel('measured steps')
    plt.bar(stoptime.keys(), stoptime.values())
    plt.show()


def simulation_time(path, parser, model):
    from tessif.analyze import stop_time
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    stoptime = stop_time(path, parser, model)

    fig = plt.figure('Time measurement')
    plt.ylabel('time in s')
    plt.xlabel('measured steps')
    plt.bar(stoptime.keys(), stoptime.values())
    plt.show()


def visualize2D_assess_scalability(scalability_results):
    """Wrapper for df.plot()

    Only necessary if assess_scalability is used with only_total=False.
    Otherwise the df.plot() function can be used directly."""
    time_list2 = list()
    memory_list2 = list()

    for i in range(scalability_results.time.shape[0]):
        time_list = list()
        memory_list = list()

        for j in range(scalability_results.time.shape[1]):
            memory_list.append(scalability_results.memory.iloc[i, j].result)
            time_list.append(scalability_results.time.iloc[i, j].result)

        memory_list2.append(memory_list)
        time_list2.append(time_list)

    columns = scalability_results.time.columns.tolist()

    # es müssen der index und der column name von asses scalability übernommen werden!
    time_dataframe = pd.DataFrame(data=time_list2,
                                  index=scalability_results.time.index,
                                  columns=scalability_results.time.columns)
    memory_dataframe = pd.DataFrame(data=memory_list2,
                                    index=scalability_results.memory.index,
                                    columns=scalability_results.time.columns)

    # would be nice to retrieve the data also in tabular form
    time_dataframe.plot()
    memory_dataframe.plot()

    plt.show()


def visualize3D_assess_scalability(scalability_results):

    bar3D(
        scalability_results.memory,
        xyz_labels=('N', 'T', 'memory'),
        title="Memory Usage Results",
    ),
    bar3D(
        scalability_results.time,
        xyz_labels=('N', 'T', 'time',),
        title="Time Measurement Results",
    )

    plt.show()
