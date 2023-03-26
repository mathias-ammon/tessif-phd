# visualize/nxgrph.py
""" :mod:`~tessif.visualize.nxgrph` is a :mod:`tessif`
interface drawing :class:`networkx.Graph` like objects. Designed to be used as
programmatic interface with the option for quick and easy humanly invoked
tweaks.

Visualizing graphs using  :mod:`~tessif.visualize.nxgrph` builds on
providing data in a 3-fold parameter system:

    - :paramref:`~draw_graph.dflts` are provided by
      :attr:`tessif.frused.defaults.nxgrph_visualize_defaults`
      serving as fallback data to garantuee a graph can be drawn.

    - :paramref:`attribute
      <draw_nodes.node_attr>` like parameters are
      (supposedly) provided by a
      :class:`tessif.transform.es2mapping.base.ESTransformer` child and will
      overwrite defaults (see
      :paramref:`~tessif.transform.es2mapping.base.ESTransformer.node_data`)
    - :paramref:`~draw_graph.kwargs` alllow human intervention and will
      overwrite programmatic input

Note
----
To make use of the programmatic interface see the
:mod:`tessif.transform.es2mapping` module. Choose one of the hard coded
:class:`tessif.transform.es2mapping.base.ESTransformer` childs, or create one
of your own and supply it to :paramref:`draw_graph.formatier`.


Example
-------

    Highlighting the edge from 1 to 2 and the node 0 in a 3-complete graph
    using 'human intervention':

    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.nxgrph as nxv
    >>> G = nx.complete_graph(3)
    >>> grphdrw = nxv.draw_graph(
    ...     G, node_color={0: 'red'}, edge_color={(1, 2): 'red'})

    IGNORE:
    >>> title = plt.gca().set_title('visualize.nxgrph module intent example')
    >>> plt.draw()
    >>> plt.pause(2)
    >>> plt.close('all')

    IGNORE

    Visualizing a results transformed ES simulation model - Design Case:

    1. Handle imports:

    >>> import tessif.examples.data.omf.py_hard as omf_examples
    >>> from tessif.transform.es2mapping import omf as tomf
    >>> from tessif.transform import nxgrph as nxt

    2. Simulate energy system (using oemof in this case):

    >>> es = omf_examples.create_star()

    3. Choose ES dependend :class:`Resultiers
       <tessif.transform.es2mapping.omf.LoadResultier>` and/or
       :class:`Formatiers <tessif.transform.es2mapping.omf.AllFormatier>` of
       your liking:

    >>> formatier = tomf.AllFormatier(es, cgrp='carrier')
    >>> grph = nxt.Graph(tomf.LoadResultier(es))

    4. Tweak edge width a little:

    >>> for key, value in formatier.edge_data()['edge_width'].items():
    ...     formatier.edge_data()['edge_width'][key] = 3 * value

    5. Draw the graph:

    >>> grphdrw = nxv.draw_graph(grph, formatier=formatier, layout='neato')
    >>> plt.draw()

    IGNORE:
    >>> title = plt.gca().set_title('visualize.nxgrph module design example')
    >>> plt.pause(7)
    >>> plt.close('all')

    IGNORE

    .. image:: images/design_example.png
        :align: center
        :alt: design_example
"""
from collections import defaultdict
from tessif.frused import namedtuples as nts
import networkx as nx
from matplotlib import pyplot as plt
import logging
import dcttools
from tessif.write import log
import tessif.frused.defaults as convs

logger = logging.getLogger(__name__)
dcttools.logger = logger


@log.timings
def draw_nodes(
        grph, pos, node_attr, dflts, draw_fency_nodes=True,
        fltr='', xcptns=[], **kwargs):
    """
    Draw a Graph's nodes using the
    :func:`~networkx.drawing.nx_pylab.draw_networkx_nodes`

    Convenience wrapper for tweaking a nodes's position, shape, size and color.
    Designed to be called by :func:`draw_graph`. Nonetheless usable as
    standalone drawing utility.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn.

    pos : dict
        A dict with nodes as keys and positions as values

    node_attr : dict of dict
        A dict with attribute names as keys and dicts as values. Value dicts
        consist of nodes as keys and attribute parameters as values::

            {attr_name: {node: attr_parameter}}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` object.

        Use one of those for automated node designs. Will be unpacked and
        passed as kwargs to
        :func:`~networkx.drawing.nx_pylab.draw_networkx_nodes`

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during drawing. The :paramref:`~draw_nodes.node_attr` will be
        filled with all attributes missing and after that populated with the
        :paramref:`~draw_nodes.kwargs` values.

    draw_fency_nodes: bool
        Whether to use visualization to highlight node attributes or not.

        If ``True``:

            - nodes of variable size are visualized with outer fading circles
            - nodes of explicitly stated size are visualized using the
              ``node_fill_size`` attribute

        If ``False``:

            - nodes of variable size are drawn as filled circle at default size
            - nodes of explicitly stated size are drawn as filled circles

    fltr: str (default='')
        :paramref:`~draw_nodes.kwargs` filter strings. Kwargs having
        :paramref:`~draw_nodes.fltr` in them will be stripped
        of the filter keyword and passed on for drawing.

        For filtering without stripping list the respective kwarg in
        :paramref:`~draw_nodes.xcptns`

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :meth:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.

    xcptns: sequence of str (default=[])
        Sequence of key word arguments that won't be stripped of the
        :paramref:`~draw_nodes.fltr`.

        Whether a kwarg should be stripped or not, depends on the naming
        convention of :func:`~networkx.drawing.nx_pylab.draw_networkx_nodes`.
        Make sure to checkout their documentation to get expected behaviour.

    kwargs:
        If you don't want to make use of a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child. you can
        "manually" format your nodes using keyword arguments. They can either
        be the same for all nodes as in::

            node_size=10

        Or dictionairies using nodes as keys and attribute parameters as
        values as in::

            node_size={'node_1': 10, 'node_2': 3}

        Nodes not present as keys will be set as defined in
        :paramref:`~draw_nodes.dflts`. See
        :func:`~networkx.drawing.nx_pylab.draw_networkx_nodes` for supported
        kwargs.

    Return
    ------
    node_draws : list
        list of :class:`matplotlib.collections.PathCollection` representing
        the nodes

    Notes
    -----
    Current implementation needs ``node_fill_size`` entries to be present in
    all :paramref:`~draw_nodes.node_attr` node dicts (of the nodes beeing
    drawn) for drawing fency nodes. Hence it is recommended to have a default
    entry of ``node_fill_size`` in the  :paramref:`~draw_nodes.dflts` dict.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.nxgrph as nxv
    >>> from collections import defaultdict
    >>> G=nx.complete_graph(3)
    >>> pos=nx.spring_layout(G)
    >>> node_attr=defaultdict(dict)
    >>> defaults={'node_uid': None, 'node_size': 3000, 'node_shape':'o',
    ... 'node_fill_size': 3000, 'node_color': 'green', 'node_alpha': 1.0}
    >>> fltr='node_'
    >>> xcptns=['node_size', 'node_color', 'node_shape', 'node_fill_size']
    >>> node_draws = nxv.draw_nodes(
    ...     G, pos ,node_attr, defaults, draw_fency_nodes=False,
    ...     fltr=fltr, xcptns=xcptns, node_color='pink')
    >>> print(list(map(type, node_draws))[0])
    <class 'matplotlib.collections.PathCollection'>

    IGNORE:
    >>> title = plt.gca().set_title('draw_nodes example')
    >>> plt.draw()
    >>> plt.pause(2)
    >>> plt.close('all')

    IGNORE

    .. image:: images/draw_nodes_example.png
        :align: center
        :alt: draw_nodes_example.png


    """
    # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
    node_attr, node_dflts, node_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[node_attr, dflts, kwargs], fltr=fltr),
        fnd=fltr, xcptns=xcptns)

    # Swap keys to allow aggregation
    node_attr = dcttools.kswap(node_attr)

    # Aggregate all attributes into node_attr for drawing:
    node_attr = dcttools.maggregate(
        tlkys=grph.nodes, nstd_dcts=[node_attr, ], dcts=[node_dflts, ],
        **node_kwargs)

    # A list of networkx returned node linestyles
    node_draws = []

    # Iterate through nodes to respect possible updates
    for node in grph.nodes:

        # filter out non node kwargs:
        node_attr[node] = {key: value for key, value in node_attr[node].copy().items()
                           if key in convs.nx_label_kwargs['nodes']}

        # pop node fill size since it ain't a registered kwarg
        node_fill_size = node_attr[node].pop('node_fill_size')

        # 3.) Draw nodes:
        # check if node size is variable...
        if node_attr[node].get('node_size') == 'variable':

            # ... yes, so do you want to visualize that ? ....
            if draw_fency_nodes:
                # ... yes, so draw a multi circle with fading intensity
                # towards the outer radius (designed for visualizing variable
                # node sizes like buses)
                draws = 3

                for draw in range(draws):
                    # decrease node radius with each draw:
                    node_attr[node]['node_size'] = round(
                        dflts['node_size'] *
                        dflts['node_variable_size_scaling'] *
                        (1-draw/draws), 0)
                    # increase alpha with each draw:
                    node_attr[node]['alpha'] = round(
                        (draw+1)/draws, 3)

                    node_draws.append(nx.draw_networkx_nodes(
                        grph, pos, nodelist=[node],
                        **node_attr[node]))

            else:
                # ... no, variable nodes should be drawn in default size.
                node_attr[node]['node_size'] = dflts['node_size']

                node_draws.append(nx.draw_networkx_nodes(
                    grph, pos, nodelist=[node], **node_attr[node]))

        else:
            # ... no, node size is explicitly stated...
            # ... but do you want the fill_size attribute to be visualized? ...

            if draw_fency_nodes:
                # ... yes, so draw an outer border and an inner filled cycle
                draws = 2

                for draw in range(draws):
                    if draw == 0:
                        # Drawing outer border:
                        original_color = node_attr[node]['node_color']
                        node_attr[node]['node_color'] = 'white'
                        edgecolors = original_color
                    else:
                        # Drawing inner filled cycle:
                        original_size = node_attr[node]['node_size']
                        node_attr[node]['node_size'] = node_fill_size

                        edgecolors = node_attr[node].get(
                            'node_color', dflts['node_color'])

                    # Do the actual drawing
                    node_draws.append(nx.draw_networkx_nodes(
                        grph, pos, nodelist=[node],
                        edgecolors=edgecolors,
                        **node_attr[node]))

                    # restore dflts
                    node_attr[node]['node_color'] = original_color
                    if draw > 0:
                        node_attr[node]['node_size'] = original_size
            else:

                # ... no, just draw nodes with the size stated
                node_draws.append(nx.draw_networkx_nodes(
                    grph, pos, nodelist=[node], **node_attr[node]))

    return node_draws


@log.timings
def drawing_node_labels(grph, pos, node_attr, dflts,
                        fltr='', xcptns=[], **kwargs):
    r"""
    Draw a Graph's node labels using
    :func:`~networkx.drawing.nx_pylab.draw_networkx_labels`

    Convenience wrapper for tweaking node label appearances. Designed to be
    called by :func:`draw_graph`. Nonetheless usable as standalone drawing
    utility.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn.

    pos : dict
        A dict with nodes as keys and positions as values

    node_attr : dict of dict
        A dict with attribute names as keys and dicts as values. Value dicts
        consist of nodes as keys and attribute parameters as values::

            {attr_name: {node: attr_parameter}}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use one of those for automated node label designs. Will be unpacked and
        passed as kwargs to
        :func:`~networkx.drawing.nx_pylab.draw_networkx_labels`

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during drawing. The :paramref:`~drawing_node_labels.node_attr` will be
        filled with all attributes missing and after that populated with the
        :paramref:`~drawing_node_labels.kwargs` values.

    fltr: str (default='')
        :paramref:`~drawing_node_labels.kwargs` filter strings. Kwargs having
        :paramref:`~drawing_node_labels.fltr` in them will be stripped
        of the filter keyword and passed on for drawing.

        For filtering without stripping list the respective kwarg in
        :paramref:`~drawing_node_labels.xcptns`

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :meth:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.

    xcptns: sequence of str (default=[])
        Sequence of key word arguments that won't be stripped of the
        :paramref:`~drawing_node_labels.fltr`.

        Whether a kwarg should be stripped or not, depends on the naming
        convention of  :func:`~networkx.drawing.nx_pylab.draw_networkx_labels`.
        Make sure to checkout their documentation for getting expected
        behaviour.

    kwargs:
        If you don't want to make use of a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child. you can
        "manually" format your nodes using keyword arguments. They can either
        be the same for all nodes as in::

            font_color='black'

        Or dictionairies using nodes as keys and attribute parameters as
        values as in::

           font_color={'node_1': 'red', 'node_2': 'blue'}

        Nodes not present as keys will be set as defined in
        :paramref:`~drawing_node_labels.dflts`. See
        :func:`~networkx.drawing.nx_pylab.draw_networkx_labels` for supported
        kwargs.

    Return
    ------
    node_uid_draws : dict
        :class:`matplotlib.text.Text` objects representing the drawn node
        labels keyed by label as in:

            ``{'node_uid': Text('drawn_label')}``

    Notes
    -----
    Current (August 2019) implementation of
    :func:`~networkx.drawing.nx_pylab.draw_networkx_labels` does not need any
    :paramref:`~drawing_node_labels.dflts` or
    :paramref:`~drawing_node_labels.xcptns` to be defined.

    Examples
    --------
    Drawing node labels (Cryptic :func:`print` is to demonstrate return):

    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.nxgrph as nxv
    >>> from collections import defaultdict
    >>> G=nx.complete_graph(3)
    >>> pos=nx.spring_layout(G)
    >>> node_attr=defaultdict(dict)
    >>> defaults={'node_uid': None}
    >>> fltr='node_'
    >>> node_uid_draws = nxv.drawing_node_labels(
    ...     G, pos, node_attr, defaults, fltr=fltr,
    ...     font_color='red', node_font_color='green')
    >>> print(
    ...     list(k for k in node_uid_draws)[0], ':',
    ...     list(map(type, (v for v in node_uid_draws.values())))[0])
    0 : <class 'matplotlib.text.Text'>

    IGNORE:
    >>> title = plt.gca().set_title('drawing_node_labels example')
    >>> plt.gca().margins(10, 10)
    >>> plt.draw()
    >>> plt.pause(2)
    >>> plt.close('all')

    IGNORE

    .. image:: images/drawing_node_labels_example.png
        :align: center
        :alt: drawing_node_labels_example_image.png
    """
    # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
    node_attr, dflts, kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[node_attr, dflts, kwargs], fltr=fltr),
        fnd=fltr, xcptns=xcptns)

    # Swap keys to allow aggregation
    node_attr = dcttools.kswap(node_attr)

    # Aggregate all attributes into node_attr for drawing
    node_attr = dcttools.maggregate(
        tlkys=grph.nodes, nstd_dcts=[node_attr, ], dcts=[dflts, ],
        **kwargs)

    # Text objects representing the node labels keyed by node labels
    node_uid_draws = {}

    # Draw nodes:
    for node in grph.nodes:
        # manually fix font_alpha (node_font_alpha before aggregating) to alpha
        # make sure it's set to 1 if neither defined in node_attr nor dflts
        node_attr[node]['alpha'] = node_attr[node].pop(
            'font_alpha', dflts.get('node_font_alpha', 1.0))

        # filter out non label kwargs:
        node_attr[node] = {key: value for key, value in node_attr[node].copy().items()
                           if key in convs.nx_label_kwargs['labels']}

        node_uid_draws.update(
            nx.draw_networkx_labels(grph, pos, **node_attr[node]))

    return node_uid_draws


@log.timings
def draw_edges(grph, pos, edge_attr, node_attr,
               dflts, fltr=('', ''), xcptns=([], [],), **kwargs):
    r"""
    Draw a Graph's edges using
    :func:`~networkx.drawing.nx_pylab.draw_networkx_edges`.

    Convenience wrapper for tweaking an edge's position shape, size and color.
    Designed to be called by :func:`draw_graph`. Nonetheless usable as
    standalone drawing utility.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn.

    pos : dict
        A dict with nodes as keys and positions as values

    edge_attr : dict of dict
        A dict with attribute names as keys and dicts as values. Value dicts
        consist of tuples of inflow node and target node as keys and attribute
        parameters as values::

            {attr_name: {(inflow, node): attr_parameter}}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use one of those for automated edge designs. Will be unpacked and
        passed as kwargs to
        :func:`~networkx.drawing.nx_pylab.draw_networkx_edges`.

    node_attr: dict of dict
        Used to acces ``node_shape`` and ``node_size`` attributes to correctly
        display edges when using custom node sizes and shapes. See also
        :paramref:`~draw_nodes.node_attr`.

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during drawing. The :paramref:`~draw_edges.edge_attr` will be
        filled with all attributes missing and after that populated with the
        :paramref:`~draw_edges.kwargs` values.

    fltr: 2-tuple of str (default=('',''))
        :paramref:`draw_edges.kwargs` filter strings. Kwargs having
        :paramref:`draw_edges.fltr` in them will be stripped
        of the filter keyword and passed on for drawing.

        - :code:`fltr[0]` applied to :paramref:`~draw_edges.node_attr`.
        - :code:`fltr[1]` applied to :paramref:`~draw_edges.edge_attr`.

        For filtering without stripping list the resptive kwarg in
        :paramref:`~draw_edges.xcptns`

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :meth:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.

    xcptns: 2-tuple of iterable of str (default=([],[]))
        2-tuple of iterable of key word arguments that won't be stripped of
        the :paramref:`~draw_edges.fltr`.

        - :code:`xcptns[0]` applied to :paramref:`~draw_edges.node_attr`.
        - :code:`xcptns[1]` applied to :paramref:`~draw_edges.edge_attr`.

        Whether a kwarg should be stripped or not, depends on the naming
        convention of :func:`~networkx.drawing.nx_pylab.draw_networkx_edges`.
        Make sure to checkout their documentation to get expected behaviour.

    kwargs:
        If you don't want to make use of a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child. you can
        "manually" format your edges using keyword arguments. They can either
        be the same for all edges as in::

            edge_width=10

        Or dictionairies using edge tuples as keys and attribute parameters as
        values as in::

            edge_width={('node_1', 'node_2'): 10, ('node_1': 'node_3'): 3}

        Edges not present as keys will be set as defined in

        :paramref:`~draw_edges.dflts`. See
        :func:`~networkx.drawing.nx_pylab.draw_networkx_edges` for supported
        kwargs.

    Return
    ------
    edge_draws : list
        list of :class:`matplotlib.patches.FancyArrowPatch` representing the
        edges

    Notes
    -----
    Current implementation needs ``node_size`` and ``node_shape`` entries
    to be  present in either the :paramref:`~draw_edges.edge_attr` dict or in
    the :paramref:`~draw_edges.dflts` dict. (With the last beeing recommended)

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.nxgrph as nxv
    >>> from collections import defaultdict
    >>> G=nx.complete_graph(3)
    >>> pos=nx.spring_layout(G)
    >>> edge_attr=defaultdict(dict)
    >>> node_attr=defaultdict(dict)
    >>> defaults={'node_size': 3000, 'node_shape':'o',
    ... 'edge_width': 1, 'edge_color': 'black',
    ... 'edge_arrowstyle': 'simple', 'edge_arrowsize': 7,
    ... 'edge_vmin': 0.0, 'edge_vmax': 1.0, 'edge_cmap': plt.cm.Greys}
    >>> fltr=('node_', 'edge_')
    >>> xcptns=(['node_size', 'node_shape'],
    ... ['edge_color', 'edge_vmin', 'edge_vmax', 'edge_cmap'])
    >>> edge_draws = nxv.draw_edges(G, pos, edge_attr, node_attr, defaults,
    ... fltr=fltr, xcptns=xcptns, edge_color='pink')
    >>> print(list(map(type, edge_draws))[0])
    <class 'matplotlib.collections.LineCollection'>

    IGNORE:
    >>> title = plt.gca().set_title('draw_edges example')
    >>> plt.gca().margins(0.5, 0.5)
    >>> plt.draw()
    >>> plt.pause(2)
    >>> plt.close('all')

    IGNORE

    .. image:: images/draw_edges_example.png
        :align: center
        :alt: draw_edges_example_image.png
    """

    # Create a namedtuple 'Edge' for better maintenance
    Edges = []
    for edge in grph.edges:
        Edges.append(nts.Edge(*edge))

    # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
    node_attr, node_dflts, node_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[node_attr, dflts, kwargs], fltr=fltr[0]),
        fnd=fltr[0], xcptns=xcptns[0])

    # Swap keys to allow aggregation
    node_attr = dcttools.kswap(node_attr)

    # Aggregate everything into node_attr for drawing:
    node_attr = dcttools.maggregate(
        tlkys=grph.nodes, nstd_dcts=[node_attr, ], dcts=[node_dflts, ],
        **node_kwargs)

    # Replace fltr in keys using kfrep to prefilter all attributes:
    edge_attr, edge_dflts, edge_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[edge_attr, dflts, kwargs], fltr=fltr[1]),
        fnd=fltr[1], xcptns=xcptns[1])

    edge_attr = dcttools.kswap(edge_attr)

    # Aggregate everything into edge_attr for drawing:
    edge_attr = dcttools.maggregate(
        tlkys=Edges, nstd_dcts=[edge_attr, ], dcts=[edge_dflts, ],
        **edge_kwargs)

    # List of matplotlib.collections.PathCollection objs representing the edges
    edge_draws = []

    # 3.) Iterate thorugh all edges for drawing:
    for edge in Edges:
        # Add node size to edge attribute dict:
        # networkx 2.5 expecpts iterable of source and target node sizes ...
        edge_attr[edge]['node_size'] = [
            node_attr[edge.source].get('node_size', dflts['node_size']),
            node_attr[edge.target].get('node_size', dflts['node_size'])]

        # but you need to provide a nodelist..
        # which in this case consists of source and target cause only 1 edge
        # is drawn at a singular call
        edge_attr[edge]['nodelist'] = [edge.source, edge.target]

        # convert variable node size to default * scaling:
        for i, node_size in enumerate(edge_attr[edge].copy()['node_size']):
            if node_size == 'variable':
                edge_attr[edge]['node_size'][i] = (
                    dflts['node_size'] * dflts['node_variable_size_scaling'])
        edge_attr[edge]['node_shape'] = node_attr[edge.target].get(
            'node_shape', dflts['node_shape'])

    # draw edges
    for edge in Edges:

        # filter out non label kwargs:
        edge_attr[edge] = {
            key: value for key, value in edge_attr[edge].copy().items()
            if key in convs.nx_label_kwargs['edges']}

        edge_draws.append(nx.draw_networkx_edges(
            grph, pos, edgelist=[edge], **edge_attr[edge]))

    return edge_draws


@log.timings
def drawing_edge_labels(grph, pos, edge_attr, dflts,
                        fltr='', xcptns=[], **kwargs):
    r"""
    Draw a Graph's edge labels using
    :func:`~networkx.drawing.nx_pylab.draw_networkx_edge_labels`.

    Convenience wrapper for tweaking edge label appearances. Designed to be
    called by :func:`draw_graph`. Nonetheless usable as standalone drawing
    utility.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn.

    pos : dict
        A dict with nodes as keys and positions as values

    edge_attr : dict of dict
        A dict with attribute names as keys and dicts as values. Value dicts
        consist of tuples of inflow node and target node as keys and attribute
        parameters as values::

            {attr_name: {(inflow, node): attr_parameter}}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use one of those for automated edge label designs. Will be unpacked and
        passed as kwargs to
        :func:`~networkx.drawing.nx_pylab.draw_networkx_edge_labels`.

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during drawing. The :paramref:`~drawing_edge_labels.edge_attr` will be
        filled with all attributes missing and after that populated with the
        :paramref:`~drawing_edge_labels.kwargs` values.

    fltr: str (default='')
        :paramref:`~drawing_edge_labels.kwargs` filter strings. Kwargs having
        :paramref:`~drawing_edge_labels.fltr` in them will be stripped
        of the filter keyword and passed on for drawing.

        For filtering without stripping list the respective kwarg in
        :paramref:`~drawing_edge_labels.xcptns`

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :meth:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.

    xcptns: sequence of str (default=[])
        Sequence of key word arguments that won't be stripped of the
        :paramref:`~drawing_edge_labels.fltr`.

        Whether a kwarg should be stripped or not, depends on the naming
        convention of
        :func:`~networkx.drawing.nx_pylab.draw_networkx_edge_labels`.
        Make sure to checkout their documentation to get expected behaviour.

    kwargs:
        If you don't want to make use of a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child. you can
        "manually" format your edges using keyword arguments. They can either
        be the same
        for all edges as in::

            edge_font_color = 'black'

        Or dictionairies using tuples of inflow node and target node as keys
        and attribute parameters as values as in::

           edge_font_color = {('n1', 'n2'): 'red', ('n1', 'n3'): 'blue'}

        Edges not present as keys will be set as defined in
        :paramref:`~drawing_edge_labels.dflts`.

        See :func:`~networkx.drawing.nx_pylab.draw_networkx_edge_labels` for
        supported kwargs.

    Return
    ------
    edge_label_draws : dict
        :class:`matplotlib.text.Text` objects representing the drawn edge
        labels keyed by edges as in:

        ``{('inflow_node', 'target_node'): Text('drawn_label')}``

    Notes
    -----
    Current (August 2019) implementation of
    :func:`~networkx.drawing.nx_pylab.draw_networkx_edge_labels` does not need
    any :paramref:`~drawing_edge_labels.dflts` and only
    ``edge_labels`` to be defined in :paramref:`~drawing_edge_labels.xcptns`.

    Examples
    --------
    Drawing edge labels. (Cryptic :func:`print` is to demonstrate return
    type):

    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.nxgrph as nxv
    >>> from collections import defaultdict
    >>> G=nx.complete_graph(3)
    >>> pos=nx.spring_layout(G)
    >>> edge_attr=defaultdict(dict)
    >>> defaults={'edge_labels': 'default'}
    >>> fltr='edge_'
    >>> xcptns=['edge_labels']
    >>> edge_label_draws = nxv.drawing_edge_labels(
    ...     G, pos, edge_attr, defaults,
    ...     fltr=fltr, xcptns=xcptns, edge_font_color='red',
    ...     edge_labels={(0,1): {(0, 1): 'label'}})
    >>> print(
    ...     list(k for k in edge_label_draws)[0], ':',
    ...     list(map(type, (v for v in edge_label_draws.values())))[0])
    (0, 1) : <class 'matplotlib.text.Text'>

    IGNORE:
    >>> title = plt.gca().set_title('drawing_edge_labels example')
    >>> plt.gca().margins(20, 20)
    >>> plt.draw()
    >>> plt.pause(2)
    >>> plt.close('all')

    IGNORE

    .. image:: images/drawing_edge_labels_example.png
        :align: center
        :alt: drawing_edge_labels_example_image.png

    """

    # Create a namedtuple 'Edge' for better maintenance
    Edges = []
    for edge in grph.edges:
        Edges.append(nts.Edge(*edge))

    # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
    edge_attr, edge_dflts, edge_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[edge_attr, dflts, kwargs], fltr=fltr),
        fnd=fltr, xcptns=xcptns)

    # Swap keys to allow aggregation
    edge_attr = dcttools.kswap(edge_attr)

    # Aggregate everything into edge_attr for drawing:
    edge_attr = dcttools.maggregate(
        tlkys=Edges, nstd_dcts=[edge_attr, ], dcts=[edge_dflts, ],
        **edge_kwargs)

    # manually fix edge_labels because netwrokx expects some wierd double keyed
    # behaviour
    for edge, attributes in edge_attr.items():
        if attributes['edge_labels'] == dflts['edge_labels']:
            edge_attr[edge]['edge_labels'] = {edge: dflts['edge_labels']}

    # Text objects containing the label keyed as edge tuples:
    edge_label_draws = {}

    # Iterate thorugh all edges for drawing:
    for edge in Edges:
        # manually fix font_alpha (node_font_alpha before aggregating) to alpha
        # make sure it's set to 1 if neither defined in node_attr nor dflts
        edge_attr[edge]['alpha'] = edge_attr[edge].pop(
            'font_alpha', dflts.get('edge_font_alpha', 1.0))

        # filter out non label kwargs:
        edge_attr[edge] = {key: value for key, value in edge_attr[edge].copy().items()
                           if key in convs.nx_label_kwargs['edge_labels']}

        # do the actual drawing
        edge_label_draws.update(
            nx.draw_networkx_edge_labels(grph, pos, **edge_attr[edge]))

    return edge_label_draws


@log.timings
def draw_legend(grph, ax, lgnds=[], dflts={}, fltr='', xcptns=[], **kwargs):
    """Draw a legend using :func:`matplotlib.pyplot.legend`.

    Convenience wrapper for customizing legend drawing.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn.

    ax: :class:`matplotlib.axes.Axes`
        Axes object to draw the legend on

    lgnds: Sequence of dict
        Iterable of legend kwarg dictionairies as in::

            [{'handles': [matplotlib_handle_objects],
              'labels': ['Names'],...}]

        One legend will be drawn for each dict. Designed to be
        provided by an  :class:`~tessif.transform.es2mapping.base.ESTransformer`
        child. Allows automated legend design.

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during legend drawing. The :paramref:`~draw_legend.lgnds` items will
        be filled with all attributes missing and after that populated with the
        :paramref:`~draw_legend.kwargs` values.

    fltr: str (default='')
        :paramref:`~draw_legend.kwargs` filter strings. Kwargs having
        :paramref:`~draw_legend.fltr` in them will be stripped
        of the filter keyword and passed on for drawing.

        For filtering without stripping list the respective kwarg in
        :paramref:`~draw_legend.xcptns`

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :meth:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.

    xcptns: sequence of str (default=[])
        Sequence of key word arguments that won't be stripped of the
        :paramref:`~draw_legend.fltr`.

        Whether a kwarg should be stripped or not, depends on the naming
        convention of  :func:`matplotlib.pyplot.legend`
        Make sure to checkout their documentation for getting expected
        behaviour.

    kwargs:
        If you don't want to make use of a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child. you can
        "manually" format your legends using keyword arguments as in::

            numpoints = 10

        Parameters not present as keys will be set as defined in
        :paramref:`~draw_legend.dflts` or :func:`matplotlib.pyplot.legend`
        provided defaults.

        See :func:`matplotlib.pyplot.legend` for supported kwargs.

    Return
    ------
    legends : list
        List of :class:`matplotlib.legend.Legend` that were drawn.

    Notes
    -----
    Make sure to provide handles and labels, or otherwise there will be no
    legend.

    """
    # Adjust legend location:
    # ... get bounding box of current plot:
    bbox = ax.get_position()
    # ... shrink bounding box to 80% of original width
    ax.set_position([bbox.x0, bbox.y0, bbox.width*0.8, bbox.height])

    # List of legend objects for returning
    legends = []

    # iterate through all lgnds
    for legend_kwargs in lgnds:

        # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
        legend_dflts, legend_kwargs, provided_kwargs = dcttools.kfrep(
            dcts=dcttools.kfltr(dcts=[dflts, legend_kwargs, kwargs], fltr=fltr),
            fnd=fltr, xcptns=xcptns)

        legend_attr = dcttools.flaggregate(
            dcts=[legend_dflts, legend_kwargs, provided_kwargs])

        # Create the legend object
        lgnd = ax.legend(**legend_attr)
        # Pass it to the artist for drawing
        ax.add_artist(lgnd)
        # add it to the list of legends for returning:
        legends.append(lgnd)

    return legends


@log.timings
def draw_graph(
        grph, formatier=None, layout='dot',
        draw_node_labels=True, draw_fency_nodes=False,
        draw_edge_labels=False, legends=None,
        defaults=convs.nxgrph_visualize_defaults,
        tags=convs.nxgrph_visualize_tags,
        exceptions=convs.nxgrph_visualize_xcptns, **kwargs):
    r"""
    Draw a fully customizable energy system graph.

    For customizing use automated visual parameter dicts generated
    by something like :class:`~tessif.transform.es2mapping.base.ESTransformer`
    or tweak individual parameters using :paramref:`draw_graph.kwargs`.


    Parameters
    ----------
    grph : :class:`networkx.Graph`-like
        The graph object to be drawn.

    formatier: :class:`~tessif.transform.es2mapping.base.ESTransformer`-like,
        Object designed for automating energy system graph design. A collection
        of graph styling attributes packed inside dictionairies matching the
        networkx drawing interface demands.
        default=None

    layout: str, default='dot'
        String to define the layout used by
        :func:`networkx.drawing.nx_pydot.graphviz_layout`

        See the `doc page <https://graphviz.gitlab.io/documentation/>`_ and the
        `documentation <https://graphviz.gitlab.io/_pages/pdf/dot.1.pdf>`_ for
        more details on graph layouts.

    draw_node_labels : bool, default=True
        Draw node labels if True.
        See also :func:`drawing_node_labels`

    draw_fency_nodes : bool ,default=False
        Draw visually verbose nodes if True.
        See also :paramref:`draw_nodes.draw_fency_nodes`

    draw_edge_labels : bool, default=False
        Draw edge labels if True.
        See also :func:`drawing_edge_labels`

    legends: :class:`~collections.abc.Sequence` of dict, default=None
        Attempt legend drawing If ``not None``.
        See :paramref:`draw_legend.lgnds` for details.

    defaults: dict
        Dicts providing visual attribute defaults used when
        :paramref:`~draw_graph.formatier` does not provide one.
        default = :attr:`~tessif.frused.conventions.nxgrph_visualize_defaults`

    tags: tuple
        Tuple of strings used to filter out :paramref:`~draw_graph.kwargs`.
        Field number 0/1 will be interpreted as node/edge tags respectively.
        default = :attr:`~tessif.frused.conventions.nxgrph_visualize_tags`

    exceptions: tuple
        Tuple of :class:`~collections.abc.Sequence` objects containing
        attrbiute keys not to be stripped of :paramref:`draw_graph.tags`.
        Field number 0/1 will be interpreted as node/edge xctpns respectively.
        default = :attr:`~tessif.frused.conventions.nxgrph_visualize_xcptns`

    title: str
        Title to use for the plot.

    kwargs : key word arguments
        Unfortunately networkx does not use consistant naming convention
        when using their kwargs. Edge kwargs are mostly prefixed  with
        ``edge_`` but not all of them
        (i.e.  :func:`~networkx.drawing.nx_pylab.draw_networkx_edge_labels`).

        Hence :mod:`tessif.visualize` allows prefixing (or tagging in
        general)  ALL keywords. The current tags used to seperate the kwargs
        are: :attr:`~tessif.frused.conventions.nxgrph_visualize_tags`

        The tags will be stripped of the attribute when passed as unpacked
        dict to the respective networkx drawing utility. This is of course very
        susceptible to  changes. Let's hope an appropriate deprecation warning
        will be thrown  when they decide to change that. Simply adding the
        respective entry to :paramref:`draw_graph.exceptions` will hopefully
        ensure future compatibility.

        For a list of sensible kwargs see also:

            - :func:`networkx.drawing.nx_pylab.draw_networkx`
            - :paramref:`draw_nodes.kwargs`
            - :paramref:`drawing_node_labels.kwargs`
            - :paramref:`draw_edges.kwargs`
            - :paramref:`drawing_edge_labels.kwargs`
            - :paramref:`draw_legend.kwargs`

    Return
    ------
    graphdraw : dict
        dict containing the drawn data keyed by its elements as in::

            {'nodes': draw_nodes(),
             'node_lables': drawing_node_labels(),
             'edges': draw_edges(),
             'edge_labels': drawing_edge_labels(),
             'legends': draw_legend()}

    Examples
    --------
    Using :attr:`tessif.frused.defaults.nxgrph_visualize_defaults`,
    :attr:`tessif.frused.defaults.nxgrph_visualize_tags` and
    :attr:`tessif.frused.defaults.nxgrph_visualize_xcptns` for default
    drawing.

    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.nxgrph as nxv
    >>> G=nx.complete_graph(3)
    >>> graphdraw = nxv.draw_graph(G, node_color='pink', edge_color='red')
    >>> for key, value in graphdraw.items():
    ...    print(key, ':', type(value[0]))
    nodes : <class 'matplotlib.collections.PathCollection'>
    node_uids : <class 'matplotlib.text.Text'>
    edges : <class 'matplotlib.collections.LineCollection'>

    IGNORE:
    >>> title = plt.gca().set_title('draw_graph example')
    >>> plt.draw()
    >>> plt.pause(2)
    >>> plt.close('all')

    IGNORE

    .. image:: images/draw_graph_example.png
        :align: center
        :alt: draw_graph_example_image.png
    """
    # Create an empty dict to store the drawing elements for returning
    graphdraw = {}

    # Create an empty canvas to draw on:
    f, ax = plt.subplots()

    # Switch of axix plotting
    ax.set_axis_off()

    # Define draw_graph defaults which are to be used when no formatter was
    # passed
    if formatier:
        # Overwrite defaults with possible formatier.defaults
        defaults = dict(defaults, **formatier.defaults)

    # Generate layout
    pos = nx.drawing.nx_agraph.graphviz_layout(
        grph, prog=layout,
    )
    # args='-Gsplines=true -Granksep=10 -Goverlap=scalexy')

    # Visualize nodes...
    # ... generate a node_attr dictionairy: {node: {attr: value}}...
    # ... Using formatier as base if given:
    if formatier:
        node_attr = formatier.node_data()
    # Use empty defaultdict if not..:
    else:
        # ... to enable aggregate algorithm inside the draw_* functions
        node_attr = defaultdict(dict)

    # Draw nodes:
    graphdraw['nodes'] = draw_nodes(grph, pos, node_attr, defaults,
                                    draw_fency_nodes, fltr=tags[0],
                                    xcptns=exceptions[0], **kwargs)

    # Draw node labels:
    if draw_node_labels:
        graphdraw['node_uids'] = drawing_node_labels(
            grph, pos, node_attr, defaults,
            fltr=tags[0], xcptns=[], **kwargs)

    # Visualize edges...
    # ... Generate a edge_attr dictionairy: {Edge: {attr: vaue}}...
    # ... Use formatier as base if given:
    if formatier:
        edge_attr = formatier.edge_data()
    # Use empty defaultdict if not:
    else:
        edge_attr = defaultdict(dict)

    # Draw edges:
    graphdraw['edges'] = draw_edges(
        grph, pos, edge_attr, node_attr, defaults,
        fltr=(tags[0], tags[1]), xcptns=(exceptions[0], exceptions[1]),
        **kwargs)

    # Draw edge lables:
    if draw_edge_labels:
        graphdraw['edge_labels'] = drawing_edge_labels(
            grph, pos, edge_attr, defaults,
            fltr=tags[1], xcptns=exceptions[1], **kwargs)

    # Draw legend:
    if legends:
        graphdraw['legends'] = draw_legend(
            grph, ax, legends, defaults, fltr=tags[2], **kwargs)

    if kwargs.get('title', None) is not None:
        ax.set_title(kwargs.get('title'))

    return graphdraw


@log.timings
def draw_graphical_representation(
        formatier, colored_by='name', shift_colors=False):
    r"""
    Example for a visually enhanced energy graph drawing.

    Mainly designed as reference on how to exploit the dictionairy aggregating
    capabilities of :func:`draw_graph` and the convenience of a
    :class:`~tessif.transform.es2mapping.base.ESTransformer` child when trying
    to use :func:`~networkx.drawing.nx_pylab.draw` like functions of networkx.

    Creates a plain :class:`networkx.DiGraph` object only consisting of nodes
    and edges found in :paramref:`~draw_graphical_representation.formatier`.

    This plain graph is then provided to :func:`draw_graph` with the
    :paramref:`~draw_graphical_representation.formatier` providing
    manually stated key word arguments.

    This is of course not the design case, because this behaviour could be
    easily archived only using :func:`draw_graph` while providing an
    :paramref:`~draw_graph.formatier` returning the desired formats when
    accessed for
    :attr:`~tessif.transform.es2mapping.base.ESTransformer.node_data`
    and :attr:`~tessif.transform.es2mapping.base.ESTransformer.edge_data`.
    This however assumes we are commited enough to write our own
    :class:`~tessif.transform.es2mapping.base.ESTransformer` instead of simply
    tweaking the hell out of the ones already hard coded via simple keyword
    arguments.

    Parameters
    ----------
    formatier : :class:`~tessif.transform.es2mapping.base.ESTransformer`
        Energy system to dictionairy transformer object returning its data
        as a 2 layer nested dict in the form of
        ``{attribute: {node/edge: parameter}}`` if accessed for
        ``node_data``/``edge_data`` respectively. As well es a default
        dictionairy for node and edge attributes.

    colored_by : {'name', 'carrier', 'sector'}, optional
        Specification on how to group nodes for coloring.
        (Respective node color dict provided by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child)

        Default implementations are:

            - 'component': Searches for keywords in node.label.component
            - 'label': Searches for keywords in str(node.label)
            - 'carrier': Searches for keywords in node.label.carrier
            - 'sector': Searches for keywords in node.label.sector

        (Refer to :attr:`~tessif.frused.namedtuples.NodeColorGroupings` for
        namedtuple implementation)

        Note
        ----
        To try out tweaking things your own way, create a custom Formatier
        class inheriting
        :class:`~tessif.transform.es2mapping.base.ESTransformer` and overwrite
        ``_map_node_colors()`` for additional coloring logic.

    shift_colors : bool, default=False
        Use a colormap cycle for color groupings if ``True``. Otherwise all
        nodes of one group are colored the same.
        (Respective node color map dict provided by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child)

    Return
    ------
    networkx.DiGraph
        Graph object visualized.

    Example
    -------
    Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
    logging level to debug for decluttering doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'


    Simulate the omeof standard energy system and draw it:

    >>> from tessif.frused.paths import example_dir
    >>> from tessif.transform.es2mapping import omf as tomf
    >>> from tessif.transform import nxgrph as nxt
    >>> from tessif.visualize import nxgrph as nxv
    >>> import os
    >>> from tessif import simulate
    >>> from tessif import parse
    >>> es = simulate.omf(
    ...     path=os.path.join(example_dir, 'data', 'omf',
    ...                       'xlsx', 'energy_system.xlsx'),
    ...     parser=parse.xl_like)
    >>> formatier = tomf.AllFormatier(es, cgrp='all')
    >>> grph = nxt.Graph(tomf.FlowResultier(es))
    >>> for key, value in formatier.edge_data()['edge_width'].items():
    ...    formatier.edge_data()['edge_width'][key] = 4 * value
    >>> nxv.draw_graphical_representation(
    ...     formatier=formatier, colored_by='name')

    IGNORE:
    >>> title = plt.gca().set_title('graphical_representation example')
    >>> plt.draw()
    >>> plt.pause(10)
    >>> plt.close('all')

    IGNORE

    .. image:: images/graphical_representation_example.png
        :align: center
        :alt: alternate text
    """
    # Alias the energy system transformer serving as formatter
    fmt = formatier

    # Create a dummy graph only containing nodes and edges
    grph = nx.DiGraph()
    grph.add_nodes_from(fmt.nodes)
    grph.add_edges_from(fmt.edges)

    # 3.) draw the esgraph:
    draw_graph(
        grph,
        layout='dot',
        draw_node_labels=False,
        draw_fency_nodes=True,
        draw_edge_labels=False,
        node_size=fmt.node_size,
        node_fill_size=fmt.node_fill_size,
        node_shape=fmt.node_shape,
        node_color=getattr(fmt.node_color_maps, colored_by)
        if shift_colors else getattr(fmt.node_color, colored_by),
        edge_width=fmt.edge_width,
        edge_color=fmt.edge_color,
        legends=[fmt.node_style_legend,
                 getattr(fmt.node_legend, colored_by),
                 fmt.edge_style_legend]
        if not colored_by == 'name' else [getattr(
            fmt.node_legend, colored_by), fmt.edge_style_legend],
    )


@log.timings
def draw_numerical_representation(
        formatier, colored_by='name', shift_colors=False):
    """
    Examplary code for a numerically enhanced energy graph drawing.

    Mainly designed as reference on how to exploit the dictionairy aggregating
    capabilities of :func:`draw_graph` and the convenience of a
    :class:`~tessif.transform.es2mapping.base.ESTransformer` child when trying
    to use the :func:`~networkx.drawing.nx_pylab.draw` like functions of
    networkx.

    Creates a plain :class:`networkx.DiGraph` object only consisting of nodes
    and edges found in
    :paramref:`~draw_numerical_representation.formatier`.

    This plain graph is then provided to :func:`draw_graph` with the
    :paramref:`~draw_numerical_representation.formatier` providing
    manually stated key word arguments.

    This is of course not the design case, because this behaviour could be
    easily archived only using :func:`draw_graph` while providing an
    :paramref:`~draw_graph.formatier` returning the desired formats when
    accessed for
    :attr:`~tessif.transform.es2mapping.base.ESTransformer.node_data`
    and :attr:`~tessif.transform.es2mapping.base.ESTransformer.edge_data`.
    This however assumes we are commited enough to write our own
    :class:`~tessif.transform.es2mapping.base.ESTransformer` instead of simply
    tweaking the hell out of the ones already hard coded via simple keyword
    arguments.

    Parameters
    ----------
    formatier : :class:`~tessif.transform.es2mapping.base.ESTransformer`
        Energy system to dictionairy transformer object returning its data
        as a 2 layer nested dict in the form of
        ``{attribute: {node/edge: parameter}}`` if accessed for
        ``node_data``/``edge_data`` respectively. As well es a default
        dictionairy for node and edge attributes.

    colored_by : {'name', 'carrier', 'sector'}, optional
        Specification on how to group nodes for coloring.
        (Respective node color dict provided by an
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child)

        Default implementations are:

            - 'name': Searches for keywords in str(node.label)
            - 'carrier': Searches for keywords in node.label.carrier
            - 'sector': Searches for keywords in node.label.sector

        (Refer to :attr:`~tessif.frused.namedtuples.NodeColorGroupings` for
        namedtuple implementation)

        Note
        ----
        To try out tweaking things your own way, create a custom Formatier
        class inheriting
        :class:`~tessif.transform.es2mapping.base.ESTransformer` and overwrite
        ``_map_node_colors()`` for additional coloring logic.

    shift_colors : bool, default=False
        Use a colormap cycle for color groupings if ``True``. Otherwise all
        nodes of one group are colored the same.
        (Respective node color map dict provided by an
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child)

    Example
    -------
    Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
    logging level to debug for decluttering doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Simulate the omeof standard energy system and draw it:

    >>> from tessif.frused.paths import example_dir
    >>> from tessif.transform.es2mapping import omf as tomf
    >>> from tessif.transform import nxgrph as nxt
    >>> from tessif.visualize import nxgrph as nxv
    >>> import os
    >>> from tessif import parse, simulate
    >>> es = simulate.omf(
    ...     path=os.path.join(example_dir, 'data', 'omf',
    ...                       'xlsx', 'energy_system.xlsx'),
    ...     parser=parse.xl_like)
    >>> formatier = tomf.AllFormatier(es, cgrp='all')
    >>> grph = nxt.Graph(tomf.FlowResultier(es))
    >>> nxv.draw_numerical_representation(
    ...     formatier=formatier, colored_by='sector')

    IGNORE:
    >>> title = plt.gca().set_title('numerical_representation example')
    >>> plt.draw()
    >>> plt.pause(10)
    >>> plt.close('all')

    IGNORE

    .. image:: images/numerical_representation_example.png
        :align: center
        :alt: alternate text

    """
    # Alias the energy system transformer serving as formatter
    fmt = formatier

    # Create a dummy graph only containing nodes and edges
    grph = nx.DiGraph()
    grph.add_nodes_from(fmt.nodes)
    grph.add_edges_from(fmt.edges)

    # Draw the esgraph:
    draw_graph(
        grph,
        layout='sfdp',
        draw_node_labels=True,
        draw_fency_nodes=False,
        draw_edge_labels=True,
        node_uids=fmt.node_summaries,
        node_size=3000,
        node_color=getattr(fmt.node_color_maps, colored_by)
        if shift_colors else getattr(fmt.node_color, colored_by),
        edge_labels=fmt.edge_summaries,
        legends=[getattr(fmt.node_legend, colored_by)],
    )
