# src/tessif/visualize/dcgrph
""" :mod:`~tessif.visualize.dcgrph` is a :mod:`tessif`
interface drawing :class:`networkx.Graph` like objects. Designed to be used as
programmatic interface with the option for quick and easy humanly invoked
tweaks.

Visualizing graphs using  :mod:`~tessif.visualize.dcgrph` builds on
providing data in a 3-fold parameter system:

    1. :paramref:`~draw_graph.dflts` are provided by
       :attr:`tessif.frused.defaults.dcgrph_visualize_defaults`
       serving as fallback data to garantuee a graph can be drawn.

    2. :paramref:`attribute <draw_nodes.node_attr>` like parameters are
       (supposedly) provided by a
       :class:`tessif.transform.es2mapping.base.ESTransformer` child and will
       overwrite defaults (see
       :paramref:`~tessif.transform.es2mapping.base.ESTransformer.node_data`).

    3. :paramref:`~draw_graph.kwargs` alllow human intervention and will
       overwrite programmatic input.


Note
----
To make use of the programmatic interface see the
:mod:`tessif.transform.es2mapping` module. Choose one of the hard coded
:class:`tessif.transform.es2mapping.base.ESTransformer` childs, or create one
of your own and supply it to :paramref:`draw_graph.formatier`.


Examples
--------

Highlighting the edge from 1 to 2 and the node 0 in a 3-complete graph
using 'human intervention':

>>> import networkx as nx
>>> import tessif.visualize.dcgrph as dcv
>>> #
>>> app = dcv.draw_graph(
...     grph=nx.complete_graph(3),
...     node_color={0: 'red'},
...     edge_color={(1, 2): 'red'},
... )
>>> # commented out for doctesting. Uncomment to serve interactive drawing
>>> # to http://127.0.0.1:8050/
>>> # app.run_server(debug=False)

.. image:: images/dcgrph_minimal_example.png
    :align: center
    :alt: dcgrph minimal example

Visualizing a results transformed ES simulation model - Design Case:

1. Handle imports:

>>> import tessif.examples.data.omf.py_hard as omf_examples
>>> from tessif.transform.es2mapping import omf as tomf
>>> from tessif.transform import nxgrph as nxt

2. Create an optimized energy system model (using oemof in this case):

>>> esm = omf_examples.create_star()

3. Choose ES dependend :class:`Resultiers
   <tessif.transform.es2mapping.omf.LoadResultier>` and/or
   :class:`Formatiers <tessif.transform.es2mapping.omf.AllFormatier>` of
   your liking:

>>> formatier = tomf.AllFormatier(esm, cgrp='carrier', drawutil='dc')
>>> grph = nxt.Graph(tomf.FlowResultier(esm))

5. Draw the graph and tweak a node color and an edge style:

>>> import tessif.visualize.dcgrph as dcv
>>> app = dcv.draw_graph(
...     grph=grph,
...     formatier=formatier,
...     node_color={'Power Line': 'orange'},
...     edge_arrowstyle={('Unlimited Power', 'Power Line'): 'vee'},
... )
>>> # commented out for doctesting. Uncomment to serve interactive drawing
>>> # to http://127.0.0.1:8050/
>>> # app.run_server(debug=False)

.. image:: images/dcgrph_design_example.png
    :align: center
    :alt: dcgrph Design Case Example

"""
# 3rd party imports
from dash import html, dcc
import dash
import dash_cytoscape as cyto
import dash
from dash.dependencies import Input, Output

import dcttools
import logging
from pandas import DataFrame
import seaborn as sns
from networkx import (
    kamada_kawai_layout as kkl,
    fruchterman_reingold_layout as frl,
)

# built-in imports
from collections import defaultdict
import json
import importlib

# local imports
from tessif.frused.defaults import dcgrph_visualize_defaults as dflts
from tessif.frused import namedtuples as nts
from tessif.frused.spellings import energy_system_component_identifiers as esci
import tessif.frused.themes as themes
from tessif.frused.configurations import node_uid_seperator
from tessif.transform.es2es import infer_registered_model, infer_software_from_es
from tessif.transform import nxgrph as nxt
from tessif.model.energy_system import AbstractEnergySystem

logger = logging.getLogger(__name__)

tweak_em_all = [
    # Group selectors
    {
        'selector': 'node',
        'style': {
            'content': 'data(id)',
            'background-color': 'data(node_color)',
            'width': 'data(node_size)',
            'height': 'data(node_size)',
            'text-valign': 'data(node_label_position)',
            'font-weight': 'data(font_weight)',
            'font-size': 'data(font_size)',
            'shape': 'data(node_shape)',
            'border-width': 'data(node_border_width)',
            'border-style': 'data(node_border_style)',
            'border-color': 'data(node_border_color)',
            'background-opacity': 'data(node_opacity)',
            'background-fill': 'data(node_fill_gradient)',
            'background-gradient-stop-colors': 'data(node_gradient_colors)',
            'background-gradient-stop-positions': 'data(node_gradient_positions)',
        }
    },
    {
        'selector': 'edge',
        'style': {
            # The default curve style does not work with certain arrows
            'curve-style': 'data(edge_style)',
            'target-arrow-shape': 'data(edge_arrowstyle)',
            'target-arrow-color': 'data(edge_color)',
            'line-color': 'data(edge_color)',
            'line-style': 'data(edge_linestyle)',
            "line-dash-pattern": "data(edge_line_dashpattern)",
            # 'content': "data(id)",
            'width': 'data(edge_width)',
        }
    },
]
"""Dash stylesheet for parameterizing nodes and edges via dynamic arguments.

Parameterizing done via :func:`parse_dc_nodes` and :func:`parse_dc_edges`.
"""

generic_graph = [
    # Group selectors
    {
        'selector': 'node',
        'style': {
            'content': 'data(id)',
            'background-color': 'data(node_color)',
            'width': dflts['node_size'],
            'height': dflts['node_size'],
            'text-valign': dflts['node_label_position'],
            'font-weight': dflts['node_font_weight'],
            'font-size': dflts['node_font_size'],
            'node-shape': dflts['node_shape']
        }
    },
    {
        'selector': 'edge',
        'style': {
            'curve-style': dflts['edge_style'],
            'target-arrow-shape': dflts['edge_arrowstyle'],
            'target-arrow-color': dflts['edge_color'],
            'line-style': dflts['edge_linestyle'],
            'line-color': dflts['edge_color'],
            # 'content': "data(carrier)"
            'width': dflts['edge_width']
        }
    },
]
"""Generic graph dash stylesheet."""

advanced_graph = []
"""Advanced graph dash stylesheet."""


def parse_dc_nodes(grph, node_attr, dflts, fltr='node_', nrep='uid', **kwargs):
    r""" Parse data into a cytoscape dash node dictionairy.

    Convenience wrapper for tweaking a nodes's position, shape, size and color.
    Designed to be called by :func:`draw_graph`. Nonetheless usable as
    standalone drawing/parsing utility.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn. Usually returned by
        :func:`tessif.model.energy_system.AbstractEnergySystem.to_nxgrph`.

    node_attr : dict
        A nested dict with attribute names as keys and dicts as values. Value
        dicts consist of nodes as keys and attribute parameters as values::

            {attr_name: {node: attr_parameter}}

        Designed to be returned by an
        :class:`~tessif.transform.es2mapping.base.ESTransformer` object.
        Usually used for automated node designs. Will be unpacked and
        parsed into `cytoscape node data
        <https://dash.plotly.com/cytoscape/elements>`_.

        For user unput use :paramref:`~parse_dc_nodes.kwargs`.

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be provided by
        :attr:`tessif's defaults
        <tessif.frused.defaults.dcgrph_visualize_defaults>` and/or an
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during drawing. The :paramref:`~parse_dc_nodes.node_attr` will
        be filled with all attributes missing and after that populated with the
        :paramref:`~parse_dc_nodes.kwargs` values.

    fltr: str, default='node\_'
        :paramref:`~parse_dc_nodes.kwargs` filter strings. Kwargs having
        :paramref:`~parse_dc_nodes.fltr` in them will selected and passed on
        for drawing.

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :func:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.
        (e.g. using ``node_`` for node kwargs and ``edge_`` for edge kwargs.)

    nrep: str, default='uid'
        String specifying how to represent node labels inside
        :paramref:`draw_graph_from_data.data`.

        Possible options are:

            - ``nrep='name'`` to use
              :paramref:`tessif.frused.namedtuples.Uid.name`
            - ``nrep='uid'`` to use ``str(``
              :class:`tessif.frused.namedtuples.Uid` ``)``

        See the :func:`draw_generic_graph` examples for utilizing this kwarg.

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
        :paramref:`~parse_dc_nodes.dflts`.See `cytoscape node style
        documentation <https://js.cytoscape.org/#style/node-body>`_ for
        supported kwargs.

    Returns
    -------
    list
        List of dictionairies with a single key called ``'data'`` holding the
        dash cytoscape parsed edge styles as in::

            [{'data': {'id': 0, 'node_size': 30,...}},...]

    Examples
    --------
    Draw nodes from an nx-graph object:

    >>> from collections import defaultdict
    >>> import matplotlib.pyplot as plt
    >>> import networkx as nx
    >>> import tessif.visualize.dcgrph as dcv
    >>> #
    >>> G = nx.complete_graph(3)
    >>> defaults = {
    ...     'node_size': 30,
    ...     'node_shape': 'ellipse',
    ...     'node_fill_size': 30,
    ...     'node_color': 'green',
    ...     'node_fill_border_width': 1.5,
    ... }
    >>> node_data = dcv.parse_dc_nodes(
    ...     grph=G,
    ...     # designed to be returned by the api:
    ...     node_attr=defaultdict(dict),
    ...     dflts=defaults,
    ...     # user tweaked parameters:
    ...     node_color={1: 'red'},
    ...     node_size={1: 50, 0: "variable"},
    ...     node_shape={1: 'hexagon'},
    ...     node_fill_size={1: 50, 2: 10},
    ... )
    >>> #
    >>> for dct in node_data:
    ...     print(70*'-')
    ...     for key, value in dct['data'].items():
    ...         print(f"{key}: {value}")
    ----------------------------------------------------------------------
    node_size: 40
    node_shape: ellipse
    node_fill_size: 40
    node_color: green
    node_fill_border_width: 1.5
    id: 0
    node_fill_gradient: radial-gradient
    node_gradient_colors: ['#008000', '#4ea64e', '#9ccd9c', '#ebf3eb', '#FFFFFF', '#FFFFFF']
    node_border_style: None
    ----------------------------------------------------------------------
    node_size: 50
    node_shape: hexagon
    node_fill_size: 50
    node_color: red
    node_fill_border_width: 1.5
    id: 1
    ----------------------------------------------------------------------
    node_size: 30
    node_shape: ellipse
    node_fill_size: 10
    node_color: green
    node_fill_border_width: 1.5
    id: 2
    node_fill_gradient: radial-gradient
    node_gradient_colors: ['green', 'white']
    node_gradient_positions: [0, 22.222222222222218]
    node_border_width: 1.5
    node_border_style: None
    node_border_color: green

    >>> app = dcv.draw_graph_from_data(node_data)
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_node_example.png
        :align: center
        :alt: dcgrph node example
    """
    # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
    node_attr, node_dflts, node_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[node_attr, dflts, kwargs], fltr=fltr),
        fnd=fltr, rplc=fltr)

    # Swap keys to allow aggregation
    node_attr = dcttools.kswap(node_attr)

    # Aggregate all attributes into node_attr for drawing:
    node_attr = dcttools.maggregate(
        tlkys=grph.nodes, nstd_dcts=[node_attr, ], dcts=[node_dflts, ],
        **node_kwargs)

    # A list of networkx returned node linestyles
    cytoscape_nodes = []

    # parse node uid label representaion
    if nrep == 'uid':
        get_repr = _get_uid_string_representation
    elif nrep == 'name':
        get_repr = _get_uid_name
    else:
        raise KeyError("nrep argument must be 'uid' or 'name'")

    # Iterate through nodes to respect possible updates
    for node in grph.nodes:
        node_attr[node]["id"] = get_repr(node)
        data = {
            "data": node_attr[node]
        }

        # transform pandas dateframes to json to allow later drawing:
        for key, value in data['data'].copy().items():
            if isinstance(value, DataFrame):
                # pop tables with duplicate column labels
                # since they are not json tansformable
                # and are somewhat redundant anyways
                # (node inflows and node outflows together hold all
                # information) a formatier has to offer
                if value.columns.is_unique:
                    data["data"][key] = value.to_json(date_format='iso')
                else:
                    data["data"].pop(key)
                    logger.debug("Popped Dataframe for key: '{%s}'", key)
                    logger.debug(" Had a duplicate column label, which is ")
                    logger.debug("jsonable.")

        # parse variable node size
        if node_attr[node].get('node_size') == 'variable':
            data["data"].update(_create_variable_node(
                node_attr[node]['node_color']))

        # parse fill_size attribute, so cytoscrape can style accordingly
        elif node_attr[node].get('node_fill_size') is not None:
            fill_size = node_attr[node].get('node_fill_size')
            node_size = node_attr[node].get('node_size')
            if fill_size < node_size:
                data["data"].update(
                    _create_filled_node(
                        node_attr[node]['node_size'],
                        node_attr[node]['node_fill_size'],
                        node_attr[node]['node_color'],
                        node_attr[node]['node_fill_border_width'],
                    )
                )

        # if node_attr[node]["id"] == "hp1":
        #     print(79*'*')
        #     print("Inside parse dc nodes:")
        #     print(data)
        #     print(79*'*')
        cytoscape_nodes.append(data)

    return cytoscape_nodes


def _create_variable_node(color):
    """Create dcgraph dictionairy entries representing variable nodes."""

    # crate a gradient color palette using seaborn
    pal = sns.light_palette(color, 4, reverse=True).as_hex()
    pal.append("#FFFFFF")
    pal.append("#FFFFFF")
    variable_node_size_attributes = {
        "node_fill_gradient": "radial-gradient",
        "node_gradient_colors": pal,
        "node_size": dflts["node_variable_size"],
        "node_fill_size": dflts["node_variable_size"],
        "node_border_style": None,

        # "node_border_width": dflts["node_border_width"],
        # "node_border_style": dflts["node_border_style"],
        # "node_border_color": dflts["node_border_color"],
        # "node_opacity": 0,
    }

    return variable_node_size_attributes


def _create_filled_node(node_size, fill_size, color, border_width):
    """Create dcgraph dict entries representing partially filled nodes."""

    # not the best way, since it does not represent capacity factors purfectly.
    # Node layout is often calculated at the drawing step (when using
    # cytoscape built-in layouts) so adding an edge-less node like in nxgrph,
    # is not ideal/undesired/maybe even impossible.
    # an idea that comes to mind is to add nodes that get ignored by force
    # layouts by prociding a filter as in: return edge.weigth if
    # 'ingore-force' not in edge.uid.name
    edge = fill_size/node_size*100
    grad_pos = [0, edge*2/3]
    grad_cols = [color, "white"]
    filled_node_attribute = {
        "node_fill_gradient": "radial-gradient",
        "node_gradient_colors": grad_cols,
        "node_gradient_positions": grad_pos,
        "node_border_width": border_width,  # dflts["node_border_width"],
        "node_border_style": dflts["node_border_style"],
        "node_border_color": color,
    }

    return filled_node_attribute


def parse_dc_edges(grph, edge_attr, node_attr,
                   dflts, fltr=('node_', 'edge_'), nrep='uid',
                   **kwargs):
    r"""Draw a Graph's edges.

    Convenience wrapper for tweaking an edge's position shape, size and color.
    Designed to be called by :func:`draw_graph`. Nonetheless usable as
    standalone drawing utility.

    Parameters
    ----------
    grph : :class:`networkx.Graph` like
        The graph object to be drawn. Usually returned by
        :func:`tessif.model.energy_system.AbstractEnergySystem.to_nxgrph`.

    edge_attr : dict
        A nested dict with attribute names as keys and dicts as values. Value
        dicts consist of tuples of inflow node and target node as keys and
        attribute parameters as values::

            {attr_name: {(inflow, node): attr_parameter}}

        Designed to be returned by a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use one of those for automated edge designs. Will be unpacked and
        passed as kwargs to
        :func:`~networkx.drawing.nx_pylab.draw_networkx_edges`.

    node_attr: dict
        Nested dict used to acces ``node_shape`` and ``node_size`` attributes
        to correctly display edges when using custom node sizes and shapes. See
        also :paramref:`~parse_dc_nodes.node_attr`.

        .. note::

           These node_attr will only be used for edge positioning. Use
           :func:`parse_dc_nodes` for manipulating node data that gets
           drawn.

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Designed to be provided by
        :attr:`tessif's defaults
        <tessif.frused.defaults.dcgrph_visualize_defaults>` and/or an
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child.

        Use this dictionairy to key all the attributes you want be accessed
        during drawing. The :paramref:`~parse_dc_nodes.node_attr` will
        be filled with all attributes missing and after that populated with the
        :paramref:`~parse_dc_edges.kwargs` values.

    fltr: ~collection.abc.Container defalut=('node\_', 'edge\_')
        :paramref:`parse_dc_edges.kwargs` filter strings. Kwargs having
        :paramref:`parse_dc_edges.fltr` in them will be sorted and  passed on
        for drawing.

        - :code:`fltr[0]` applied to :paramref:`~parse_dc_edges.node_attr`.
        - :code:`fltr[1]` applied to :paramref:`~parse_dc_edges.edge_attr`.

        Allows for wrapping the function with other drawing subutilities into
        a toplevel function like :meth:`draw_graph` wihtout sacrificing the
        possibility to manipulate each sublevel call via ``kwargs``.
        (e.g. using ``node_`` for node kwargs and ``edge_`` for edge kwargs.)

    nrep: str, default='uid'
        String specifying how to represent node labels inside
        :paramref:`draw_graph_from_data.data`.

        Possible options are:

            - ``nrep='name'`` to use
              :paramref:`tessif.frused.namedtuples.Uid.name`
            - ``nrep='uid'`` to use ``str(``
              :class:`tessif.frused.namedtuples.Uid` ``)``

        See the :func:`draw_generic_graph` examples for utilizing this kwarg.

    kwargs:
        If you don't want to make use of a
        :class:`~tessif.transform.es2mapping.base.ESTransformer` child, you can
        "manually" format your nodes and edges using keyword arguments. They
        can either be the same for all edges as in::

            edge_width=10

        Or dictionairies using edge tuples as keys and attribute parameters as
        values as in::

            edge_width={('node_1', 'node_2'): 10, ('node_1': 'node_3'): 3}

        Edges not present as keys will be set as defined in

        :paramref:`~parse_dc_edges.dflts`. See `cytoscape edge style
        documentation <https://js.cytoscape.org/#style/edge-line>`_ for
        supported kwargs.

    Returns
    -------
    list
        List of dictionairies with a single key called ``'data'`` holding the
        dash cytoscape parsed edge styles as in::

            [{'data': {'source': 0, 'target': 1, 'edge_width': 1.5,}}, ...]


    Examples
    --------
    Draw edges from an nx-graph object:

    >>> # third party imports
    >>> import networkx as nx
    >>> # standard library imports
    >>> from collections import defaultdict
    >>> # built-in imports
    >>> import tessif.visualize.dcgrph as dcv
    >>> #
    >>> G = nx.complete_graph(3)
    >>> # create tiny nodes, so dash cytoscape knows where to draw edges:
    >>> node_data = dcv.parse_dc_nodes(
    ...     grph=G,
    ...     node_attr=defaultdict(dict),
    ...     dflts={'node_size': .1},
    ... )
    >>> defaults = {
    ...     'edge_width': 1.5,
    ...     'edge_style': 'bezier',
    ...     'edge_color': 'green',
    ...     'edge_arrowstyle': 'triangle',
    ...     'edge_arrowsize': 1,
    ... }
    >>> #
    >>> edge_data = dcv.parse_dc_edges(
    ...     G,
    ...     # mocked here, because designed to be returned by the api:
    ...     edge_attr=defaultdict(dict),
    ...     node_attr=defaultdict(dict),
    ...     dflts=defaults,
    ...     # user tweaked parameters:
    ...     edge_color={
    ...         (1, 2): 'pink',
    ...         (0, 1): dcv.greyscale2hex(.3),
    ...     },
    ...     edge_width={(1, 2): 5},
    ...     edge_arrowstyle={(0, 2): 'vee'},
    ... )
    >>> #
    >>> for dct in edge_data:
    ...     print(70*'-')
    ...     for key, value in dct['data'].items():
    ...         print(f"{key}: {value}")
    ----------------------------------------------------------------------
    edge_width: 1.5
    edge_style: bezier
    edge_color: #b2b2b2
    edge_arrowstyle: triangle
    edge_arrowsize: 1
    source: 0
    target: 1
    ----------------------------------------------------------------------
    edge_width: 1.5
    edge_style: bezier
    edge_color: green
    edge_arrowstyle: vee
    edge_arrowsize: 1
    source: 0
    target: 2
    ----------------------------------------------------------------------
    edge_width: 5
    edge_style: bezier
    edge_color: pink
    edge_arrowstyle: triangle
    edge_arrowsize: 1
    source: 1
    target: 2

    >>> app = dcv.draw_graph_from_data(data=node_data + edge_data)
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_edge_example.png
        :align: center
        :alt: dcgrph node example

    """
    # Create a namedtuple 'Edge' for better maintenance
    Edges = []
    for edge in grph.edges:
        Edges.append(nts.Edge(*edge))

    # Use kfrep to replace fltr in keys and kfltr for prefiltering prefix
    node_attr, node_dflts, node_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[node_attr, dflts, kwargs], fltr=fltr[0]),
        fnd=fltr[0], rplc=fltr[0])

    # Swap keys to allow aggregation
    node_attr = dcttools.kswap(node_attr)

    # Aggregate everything into node_attr for drawing:
    node_attr = dcttools.maggregate(
        tlkys=grph.nodes, nstd_dcts=[node_attr, ], dcts=[node_dflts, ],
        **node_kwargs)

    # Replace fltr in keys using kfrep to prefilter all attributes:
    edge_attr, edge_dflts, edge_kwargs = dcttools.kfrep(
        dcts=dcttools.kfltr(dcts=[edge_attr, dflts, kwargs], fltr=fltr[1]),
        fnd=fltr[1], rplc=fltr[1])

    edge_attr = dcttools.kswap(edge_attr)

    # Aggregate everything into edge_attr for drawing:
    edge_attr = dcttools.maggregate(
        tlkys=Edges, nstd_dcts=[edge_attr, ], dcts=[edge_dflts, ],
        **edge_kwargs)

    # List of matplotlib.collections.PathCollection objs representing the edges
    cytoscape_edges = []

    # parse node uid label representaion
    if nrep == 'uid':
        # use str(node)
        get_repr = _get_uid_string_representation
    elif nrep == 'name':
        # use node.uid
        get_repr = _get_uid_name

    # Iterate through nodes to respect possible updates
    for edge in Edges:

        edge_attr[edge]["source"] = get_repr(edge.source)
        edge_attr[edge]["target"] = get_repr(edge.target)
        data = {
            "data": edge_attr[edge],
        }

        # transform pandas dateframes to json to allow later drawing:
        for key, value in data["data"].copy().items():
            if isinstance(value, DataFrame):
                # pop tables with duplicate column labels
                # since they are not json tansformable
                # and are somewhat redundant anyways
                # (node inflows and node outflows together hold all
                # information) a formatier has to offer
                if value.columns.is_unique:
                    data["data"][key] = value.to_json(orient='columns')
                else:
                    data["data"].pop(key)
                    logger.debug("Popped Dataframe for key: '{%s}'", key)
                    logger.debug(" Had a duplicate column label, which is ")
                    logger.debug("not jsonable.")

            # string cast tuple key
            if isinstance(key, tuple):
                data["data"][str(key)] = data["data"].pop(key)
                logger.debug("\nString cast tuple key: '{%s}' ", key)
                logger.debug("to be in accordance with dash cytoscape.\n")

            # parse dicts to json to allow tuple keys in value dicts
            # e.g. edge_summaries =
            # {('Battery', 'Powerline'): '10 MWh\n0.1 €/MWh\n0.0 t/MWh'}
            if isinstance(value, dict):
                tuple_data = data["data"].pop(key)
                data["data"][key] = json.dumps(
                    [{'key': k, 'value': v} for k, v in tuple_data.items()])
                logger.debug("\nSerialize dict value under key: '{%s}' ", key)
                logger.debug("into {'key': k, 'value': v}.")
                logger.debug("to be in accordance with dash cytoscape.\n")

            # replace dotted patterns by larger spaced dashes for cosmetic
            # reasons
            if key == "edge_linestyle" and value == "dotted":

                data["data"]["edge_line_dashpattern"] = (6, 8)
                data["data"]["edge_linestyle"] = 'dashed'

        cytoscape_edges.append(data)

    return cytoscape_edges


def draw_graph(
        grph,
        formatier=None,
        layout='cose',
        stylesheet=tweak_em_all,
        defaults=dflts,
        fd_kwargs=None,
        **kwargs):
    """Draw a Networkx Graph using Dash-Cytoscape.

    Evaluates formatier node and edge data to call
    :func:`draw_graph_from_data`.

    Parameters
    ----------
    grph : :class:`networkx.Graph`-like
        The graph object to be drawn.

    formatier: :class:`~tessif.transform.es2mapping.base.ESTransformer`-like,
        Object designed for automating energy system graph design. A collection
        of graph styling attributes packed inside dictionairies matching the
        networkx drawing interface demands.

        If ``None``, only :paramref:`draw_graph.defaults` and
        :paramref:`draw_graph.defaults` are used for styling.

    layout: str, dict, default='cose'
        String specifying one of the dash cytoscape layouts, or a dict for
        manual node positioning.

        See `dash layouts <https://dash.plotly.com/cytoscape/layout>`_
        and `cytoscape layouts <https://js.cytoscape.org/#layouts>`_
        for details on available layouts.

    stylesheet: dict, default = :attr:`tweak_em_all`
        Dictionairy of selector and styles to specify which node/edge
        attributes are used for what styling. See the `Dash-Cytoscape
        <https://dash.plotly.com/cytoscape/styling>`_ documentation for
        guidance on how to formulate and use these dicts. Examples
        used in :mod:`tessif.visualize.dcgrph` are:
        :attr:`tweak_em_all`, :attr:`generic_graph` and :attr:`advanced_graph`.

        Refer als to :func:`draw_generic_graph` and :func:`draw_advanced_graph`
        on how to use these stylesheets to preset certain layouts.

    dflts: dict
        A dict with attribute names as keys and default parameters as values::

            {attr_name: default}

        Standard implementation uses
        :attr:`tessif.frused.defaults.dcgrph_visualize_defaults` as baseline
        dict, which gets updated by the :paramref:`~draw_graph.formatier`
        defaults.

    fd_kwargs: dict
        Dictionairy of keyword arguments passed to
        :paramref:`draw_graph_from_data.kwargs`. Used to manipulate both, the
        :paramref:`~draw_graph_from_data.layout`, in case its one of the
        built-in `dash layouts <https://dash.plotly.com/cytoscape/layout>`_
        and/or the `Dash-Cytoscape Component
        <https://dash.plotly.com/cytoscape/reference>`_ rendering the graph.

    kwargs
        Keyword arguments used to manipulate node and edge styles as described
        in :paramref:`parse_dc_nodes.kwargs`
        and :paramref:`parse_dc_edges.kwargs`, respectively.

        They can either be the same for all nodes/edges as in::

            node_size=10
            edge_color=black

        Or dictionairies using nodes/edges as keys and attribute parameters as
        values as in::

            node_size={'node_1': 10, 'node_2': 3}
            edge_color={('node_1', 'node_2'): red}

        Nodes not present as will be set as defined in
        :paramref:`parse_dc_nodes.dflts` and :paramref:`parse_dc_edges.dflts`

        See `cytoscape style documentation <https://js.cytoscape.org/#style>`_
        for supported kwargs.

    Returns
    -------
    dash.dash.Dash
        `Dash app object <https://dash.plotly.com/reference#the-app-object>`_
        wrapping the the Javascript engines into a python interface. Used to
        start and manipulate the plot session.

    Examples
    --------
    Reusing the example from above w/o tweaking...

    >>> import tessif.examples.data.omf.py_hard as omf_examples
    >>> from tessif.transform.es2mapping import omf as tomf
    >>> from tessif.transform import nxgrph as nxt
    >>> esm = omf_examples.create_star()
    >>> formatier = tomf.AllFormatier(esm, cgrp='carrier', drawutil='dc')
    >>> grph = nxt.Graph(tomf.FlowResultier(esm))
    >>> import tessif.visualize.dcgrph as dcv

    ... using the default force-layout ``cose``:

    >>> app = dcv.draw_graph(
    ...     grph=grph,
    ...     formatier=formatier,
    ...     # layout='cose,  # default
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_cose_example.png
        :align: center
        :alt: dcgrph cose layout example

    ... using the :func:`networkx.drawing.layout.spring_layout`:

    >>> app = dcv.draw_graph(
    ...     grph=grph,
    ...     formatier=formatier,
    ...     layout='fruchterman_reingold',
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_frurei_example.png
        :align: center
        :alt: dcgrph frurei layout example

    ... using the :func:`networkx.drawing.layout.kamada_kawai_layout`:

    >>> app = dcv.draw_graph(
    ...     grph=grph,
    ...     formatier=formatier,
    ...     layout='kamada_kawai',
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_kamada_example.png
        :align: center
        :alt: dcgrph frurei layout example

    ... using a custom layout by providing a position dictionairy:

    >>> import networkx as nx
    >>> pos = nx.fruchterman_reingold_layout(
    ...     G=grph,
    ...     weight='weight',
    ...     scale=250,
    ... )
    >>> # transforming the dict to how dcgraph expects it:
    >>> pos = {k: {'x': v[0], 'y': v[1]} for k, v in pos.items()}
    >>> app = dcv.draw_graph(
    ...     grph=grph,
    ...     formatier=formatier,
    ...     layout=pos,
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_pos_example.png
        :align: center
        :alt: dcgrph cose layout example

    Providing forwarded layout kwargs to customize the
    `Dash-Cytoscape 'breadthfirst' Layout
    <https://dash.plotly.com/cytoscape/layout>`__:

    >>> import networkx as nx
    >>> from collections import defaultdict
    >>> import tessif.visualize.dcgrph as dcv

    >>> G = nx.complete_graph(5)
    >>> node_data = dcv.parse_dc_nodes(
    ...     grph=G,
    ...     node_attr=defaultdict(dict),
    ...     dflts={'node_size': 60},
    ... )
    >>> edge_data = dcv.parse_dc_edges(
    ...     G,
    ...     edge_attr=defaultdict(dict),
    ...     node_attr=defaultdict(dict),
    ...     dflts={'edge_color': 'black', 'edge_width': 2},
    ... )

    >>> app = dcv.draw_graph(
    ...     grph=G,
    ...     layout='breadthfirst',
    ...     fd_kwargs={'layout_roots': '[id = "2"]'},
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_kwargs2_example.png
        :align: center
        :alt: dcgrph cose layout example

    >>> app = dcv.draw_graph(
    ...     grph=G,
    ...     layout='breadthfirst',
    ...     fd_kwargs={'layout_roots': '#1, #4'},
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_kwargs1-4_example.png
        :align: center
        :alt: dcgrph cose layout example
    """
    named_layouts = {
        'kamada_kawai': {
            k: {'x': v[0], 'y': v[1]} for k, v in kkl(
                G=grph, weight='weight', scale=250).items()
        },
        'fruchterman_reingold': {
            k: {'x': v[0], 'y': v[1]} for k, v in frl(
                G=grph, weight='weight', scale=250).items()
        },
        'cose': 'cose',
        'breadthfirst': 'breadthfirst',
    }

    if isinstance(layout, dict):
        layout_dict = layout
    elif layout in named_layouts:
        layout_dict = named_layouts[layout]
    else:
        viable_layouts = [
            'kamada_kawai', 'fruchtermann_reingold', 'cose']
        msg = "Error: 'layout' must be one of %s" % viable_layouts
        raise KeyError(msg)

    if formatier:
        defaults = dict(defaults, **formatier.defaults)
        node_attr = formatier.node_data()
        edge_attr = formatier.edge_data()
    else:
        # defaults = defaults
        node_attr = defaultdict(dict)
        edge_attr = defaultdict(dict)

    node_data = parse_dc_nodes(
        grph=grph,
        node_attr=node_attr,
        dflts=defaults,
        # user tweaked parameters:
        **kwargs)

    edge_data = parse_dc_edges(
        grph=grph,
        edge_attr=edge_attr,
        node_attr=node_attr,
        dflts=defaults,
        # user tweaked parameters:
        **kwargs
    )

    if not fd_kwargs:
        fd_kwargs = {}

    return draw_graph_from_data(
        data=node_data + edge_data,
        layout=layout_dict,
        **fd_kwargs,
    )


def draw_graph_from_data(data, layout='cose', stylesheet=tweak_em_all, ilstyle=None, **kwargs):
    """Draw graph utility.

    Parameters
    ----------
    data: dict
        Dictionairy holding node and/or edge data. Usually returned by
        :func:`parse_dc_nodes` and/or :func:`parse_dc_edges`.

        See the `Dash-Cytoscape Elements Documentation
        <https://dash.plotly.com/cytoscape/elements>`_ on how to create custom
        data dictionairies.

    layout: str, dict, default='cose'
        String specifying one of the dash cytoscape layouts, or a dict for
        manual node positioning.

        See `dash layouts <https://dash.plotly.com/cytoscape/layout>`_
        and `cytoscape layouts <https://js.cytoscape.org/#layouts>`_
        for details on available layouts.

    stylesheet: dict, default = :attr:`tweak_em_all`
        Dictionairy of selector and styles to specify which node/edge
        attributes are used for what styling. See the `Dash-Cytoscape
        <https://dash.plotly.com/cytoscape/styling>`_ documentation for
        guidance on how to formulate and use these dicts. Examples
        used in :mod:`tessif.visualize.dcgrph` are:
        :attr:`tweak_em_all`, :attr:`generic_graph` and :attr:`advanced_graph`.

        Refer als to :func:`draw_generic_graph` and :func:`draw_advanced_graph`
        on how to use these stylesheets to preset certain layouts.

    ilstyle: dict, default = None
        Dictionairy supplying inline styles for the `Dash-Cytoscape Component
        <https://dash.plotly.com/cytoscape/reference>`_ The key value pairings
        are translated to html/css by DASH. Using following conventions:

            - Properties in the style dictionary are camelCased
            - The class key is renamed as className
            - Style properties in pixel units can be supplied as just numbers
              without the px unit

        For more information, pleas refer to:

            -  https://dash.plotly.com/layout#more-about-html-components
            -  https://dash.plotly.com/dash-html-components
            -  https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div

    kwargs
        Keyword arguments are supplied to the `Dash-Cytoscape Component
        <https://dash.plotly.com/cytoscape/reference>`_ rendering the graph.

        To manipulate the :paramref:`~draw_graph_from_data.layout` prefix
        the keyword argument with ``'layout_'`` as seen in the examples below.

        See the documentation on the `Dash-Cytoscape Component
        <https://dash.plotly.com/cytoscape/reference>`_ for an explanation on
        available options.

        See `dash layouts <https://dash.plotly.com/cytoscape/layout>`_
        and `cytoscape layouts <https://js.cytoscape.org/#layouts>`_
        for details on available layouts and available arguments.

    Returns
    -------
    dash.dash.Dash
        `Dash app object <https://dash.plotly.com/reference#the-app-object>`_
        wrapping the the Javascript engines into a python interface. Used to
        start and manipulate the plot session.

    Example
    -------
    See the :func:`parse_dc_edges` example section for a basic understanding of
    how to manually construct your node and edge data.

    Design Case:

    >>> # 1. Using tessifs example hub to quickly create an energy system
    >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples  # nopep8
    >>> tsf_es = hardcoded_tsf_examples.create_mwe()

    >>> # 2. Transform tessif energy system into oemof energy system
    >>> import tessif.transform.es2es.omf as tsf2omf  # nopep8
    >>> omf_es = tsf2omf.transform(tsf_es)

    >>> # 3. Optimize oemof energy system
    >>> import tessif.simulate  # nopep8
    >>> optimized_omf_es = tessif.simulate.omf_from_es(omf_es)

    >>> # 4. Post process the optimized oemof energy system: and create the nx DiGraph
    >>> import tessif.transform.es2mapping.omf as post_process_omf   # nopep8
    >>> import tessif.transform.nxgrph as nxt  # nopep8
    >>> formatier = post_process_omf.AllFormatier(
    ...     optimized_omf_es, cgrp='name', drawutil='dc')
    >>> nxgrph = nxt.Graph(post_process_omf.OmfResultier(optimized_omf_es))

    >>> # 5. Do the drawing
    >>> import tessif.visualize.dcgrph as dcv  # nopep8
    >>> from tessif.frused.defaults import dcgrph_visualize_defaults as dcdefs  # nopep8
    >>> node_data = dcv.parse_dc_nodes(
    ...     grph=nxgrph,
    ...     node_attr=formatier.node_data(),
    ...     dflts=dcdefs,
    ... )

    >>> edge_data = dcv.parse_dc_edges(
    ...     grph=nxgrph,
    ...     edge_attr=formatier.edge_data(),
    ...     node_attr=formatier.node_data(),
    ...     dflts=dcdefs,
    ... )

    >>> app = dcv.draw_graph_from_data(
    ...     data=edge_data+node_data, layout='cose')

    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_design_from-data_example.png
        :align: center
        :alt: dcgrph cose layout example


    Use a different stylesheet for a more generic visualization:

    >>> from tessif.visualize.dcgrph import generic_graph  # nopep8
    >>> app = dcv.draw_graph_from_data(
    ...     data=edge_data+node_data,
    ...     stylesheet=generic_graph,
    ... )

    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_tweaked-design_from-data_example.png
        :align: center
        :alt: dcgrph cose layout example

    More advanced example in
    manipulating the :paramref:`~draw_graph_from_data.layout` using
    :paramref:`~draw_graph_from_data.kwargs`, while also changing
    the :paramref:`~draw_graph_from_data.ilstyle`:

    >>> import networkx as nx
    >>> from collections import defaultdict
    >>> import tessif.visualize.dcgrph as dcv
    >>> from tessif.frused.defaults import dcgrph_visualize_defaults as dcdefs

    >>> G = nx.balanced_tree(3, 2)

    >>> node_data = dcv.parse_dc_nodes(
    ...     grph=G,
    ...     node_attr=defaultdict(dict),
    ...     dflts={'node_size': 60},
    ... )
    >>> edge_data = dcv.parse_dc_edges(
    ...     G,
    ...     edge_attr=defaultdict(dict),
    ...     node_attr=defaultdict(dict),
    ...     dflts=dcdefs,
    ...     edge_arrowstyle='vee',
    ...     edge_color='black',
    ... )

    >>> app = dcv.draw_graph_from_data(
    ...     data=node_data + edge_data,
    ...     layout='breadthfirst',
    ...     ilstyle={'width': 'calc(100% - 30vh)'},
    ...     layout_roots='[id = "0"]',
    ...     layout_animate='True',
    ...     minZoom=0.1,
    ...     maxZoom=10,
    ... )

    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_layout-ilstyle_from-data_example.png
        :align: center
        :alt: dcgrph cose layout example
    """
    # parse layout
    # Use kfrep to find and replace layout_kwarg with kwarg
    kfrepped_kwarg_dicts = dcttools.kfrep(
        # filte out layout kwargs
        dcts=dcttools.kfltr(dcts=[kwargs], fltr='layout_'),
        # replace 'layout_' by nothing, so kwarg gets returned
        fnd='layout_',
        rplc='',
    )
    layout_kwargs = kfrepped_kwarg_dicts[0]

    if isinstance(layout, dict):
        lout_dict = {
            'name': 'preset',
            'positions': layout,
        }
    else:
        lout_dict = {
            'name': layout,
            **layout_kwargs
        }

    # parse inline style
    inline_style = {
        'height': '95vh',
        'width': 'calc(100% - 100px)',
        'float': 'left'
    }
    if ilstyle:
        inline_style = {**inline_style, **ilstyle}

    # parse cytoscape kwargs:
    # define some defautls:
    default_cyto_kwargs = {
        'minZoom': 0.5,
        'maxZoom': 4,
    }
    cyto_kwargs = {k: v for k,
                   v in kwargs.items() if k in cyto.Cytoscape()._prop_names}

    cyto_kwargs = {**default_cyto_kwargs, ** cyto_kwargs}

    # create the graph plotting component
    ct = cyto.Cytoscape(
        id='cytoscape-image-export',
        layout=lout_dict,
        style=inline_style,
        stylesheet=stylesheet,
        elements=data,
        **cyto_kwargs)

    # enable svg export
    cyto.load_extra_layouts()

    app = _create_dash_app_from_ct_graph(ct_graph=ct)

    return app


def draw_generic_graph(energy_system, color_group='name', nrep='name', **kwargs):
    """Draw generic graph utility.

    The generic graph layout tries to enhance visual comprehensivnes while
    keeping the information conveyed relatively low to facilitate quick human
    comprehension, resulting in following layout constraints.

    Nodes:

        - Node color (circular shape fill color) corresponds to of the
          following:

            * energy sector (:paramref:`~tessif.frused.namedtuples.Uid.sector`)
            * component type (storage, fossile fule powerplant, etc... )
              (:paramref:`~tessif.frused.namedtuples.Uid.component`)
            * energy carrier (wind, electricity, solar, hot water, etc...)
              (:paramref:`~tessif.frused.namedtuples.Uid.carrier`)
            * name (All components having ’offshore’ as part of their name for
              example)
              (:paramref:`~tessif.frused.namedtuples.Uid.name`)

        - Node size (circular shape diameter) is the same for each component.
        - Node position (arrangement of the circular shapes) is chosen to lower
          the amount subjectively perceived chaos, using either a
          hirarchical grid shape or a force layout, with as little overlapping
          edges as possible.

    Edges:

        - Edge length (arrow shaft length) is a result of node positioning
        - Edge color (arrow shaft and tip) is always black

    Parameters
    ----------
    energy_system
        Energy system object to be visualized.
        Either  :class:`Tessif's System
        <tessif.model.energy_system.AbstractEnergySystem>`
        or one of the :ref:`SupportedModels`
    color_group: str, dict, default='name'
        String specifying which of the
        :attr:`~tessif.frused.namedtuples.NodeColorGroupings` is used to theme
        the node colors or dictionairy mapping node uid string representations
        to color values. Later is shown in the last example below.
    nrep: str, default='name'
        String specifying how to represent node labels inside
        :paramref:`draw_graph_from_data.data`. Information gets passed to
        :paramref:`draw_graph.kwargs`, where it subsequently gets passed on to
        :paramref:`parse_dc_nodes.nrep` and :paramref:`parse_dc_edges.nrep`.

        Possible options are:

            - ``nrep='name'`` to use
              :paramref:`tessif.frused.namedtuples.Uid.name`
            - ``nrep='uid'`` to use ``str(``
              :class:`tessif.frused.namedtuples.Uid` ``)``

    kwargs
        Kwargs get passed on to :paramref:`draw_graph.kwargs`. Can be used in
        conjunction with a :paramref:`draw_graph.fd_kwargs` dict, to e.g.
        manipulate the layout, as shown in the last example below.

    Examples
    --------
    Default use case:

    >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
    >>> import tessif.visualize.dcgrph as dcv
    >>> tsf_es = hardcoded_tsf_examples.create_fpwe()

    >>> app = dcv.draw_generic_graph(
    ...     energy_system=tsf_es,
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_generic_fpwe_example.png
        :align: center
        :alt: dcgrph draw_generic_graph example

    Using the :ref:`node uid representation <Labeling_Concept>` in conjunction
    with  :attr:`~tessif.frused.namedtuples.NodeColorGroupings`:

    >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
    >>> import tessif.visualize.dcgrph as dcv
    >>> import tessif.frused.configurations as configurations
    >>> # Use one of 'name' (default), 'carrier', 'sector' or 'component'
    >>> style = 'carrier'
    >>> configurations.node_uid_style = style
    >>> tsf_es = hardcoded_tsf_examples.create_fpwe()

    >>> app = dcv.draw_generic_graph(
    ...     energy_system=tsf_es,
    ...     color_group=style,
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_carrier_fpwe_example.png
        :align: center
        :alt: dcgrph node carrier grouped draw_generic_graph example

    Using :paramref:`~draw_generic_graph.nrep` to use ``str(node.uid)`` as node
    labels, while using ``'sector'`` as grouping of choice:

    >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
    >>> import tessif.visualize.dcgrph as dcv
    >>> import tessif.frused.configurations as configurations
    >>> # Use one of 'name' (default), 'carrier', 'sector' or 'component'
    >>> style = 'sector'
    >>> configurations.node_uid_style = style
    >>> tsf_es = hardcoded_tsf_examples.create_fpwe()

    >>> app = dcv.draw_generic_graph(
    ...     energy_system=tsf_es,
    ...     color_group=style,
    ...     nrep='uid',
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_sector_fpwe_example.png
        :align: center
        :alt: dcgrph node sector grouped draw_generic_graph example

    Use :paramref:`draw_generic_graph.kwargs` and a
    :paramref:`draw_graph.fd_kwargs` dictionairy to manipulate the layout:

    >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
    >>> import tessif.visualize.dcgrph as dcv
    >>> import tessif.frused.configurations as configurations
    >>> # Use one of 'name' (default), 'carrier', 'sector' or 'component'
    >>> style = 'name'
    >>> configurations.node_uid_style = style
    >>> tsf_es = hardcoded_tsf_examples.create_connected_es()

    >>> app = dcv.draw_generic_graph(
    ...     energy_system=tsf_es,
    ...     layout='breadthfirst',
    ...     fd_kwargs={'layout_roots': '[id = "connector"]'},
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_layout_fpwe_example.png
        :align: center
        :alt: dcgrph layout manipulating draw_generic_graph example

    Visualizing an optimized energy system model using
    :func:`draw_generic_graph`:

    >>> import tessif.examples.data.omf.py_hard as omf_examples
    >>> import tessif.visualize.dcgrph as dcv
    >>> #
    >>> optimized_es = omf_examples.create_star()

    >>> app = dcv.draw_generic_graph(energy_system=optimized_es)
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_generic_oemof_example.png
        :align: center
        :alt: dcgrph draw generic graph of an optimized oemof es

    Exploiting :func:`draw_generic_graph`: to tweak complex graph behavior.
    This is not recommended, since it would be more verbose constucting the
    node and edge data manually. It is possible, however.

    >>> import tessif.examples.data.tsf.py_hard as hardcoded_tsf_examples
    >>> import tessif.visualize.dcgrph as dcv

    >>> tsf_es = hardcoded_tsf_examples.create_hhes()

    >>> # preparing node colors:
    >>> node_color={
    ...     'coal supply': '#404040',
    ...     'coal supply line': '#404040',
    ...     'pp1': '#404040',
    ...     'pp2': '#404040',
    ...     'chp3': '#404040',
    ...     'chp4': '#404040',
    ...     'chp5': '#404040',
    ...     'hp1': '#b30000',
    ...     'imported heat': '#b30000',
    ...     'district heating pipeline': 'Red',
    ...     'demand th': 'Red',
    ...     'excess th': 'Red',
    ...     'p2h': '#b30000',
    ...     'bm1': '#006600',
    ...     'won1': '#99ccff',
    ...     'gas supply': '#336666',
    ...     'gas pipeline': '#336666',
    ...     'chp1': '#336666',
    ...     'chp2': '#336666',
    ...     'waste': '#009900',
    ...     'waste supply': '#009900',
    ...     'chp6': '#009900',
    ...     'oil supply': '#666666',
    ...     'oil supply line': '#666666',
    ...     'pp3': '#666666',
    ...     'pp4': '#666666',
    ...     'pv1': '#ffd900',
    ...     'imported el': '#ffd900',
    ...     'demand el': '#ffe34d',
    ...     'excess el': '#ffe34d',
    ...     'est': '#ffe34d',
    ...     'powerline': '#ffcc00',
    ... }

    >>> # preparing root nodes:
    >>> roots = [
    ...     "coal supply",
    ...     "oil supply",
    ...     "gas supply",
    ...     "biomass supply",
    ...     "waste",
    ... ]
    >>> layout_roots = ""
    >>> for pos, supply in enumerate(roots):
    ...     if pos != len(roots)-1:
    ...         layout_roots += f'[id = "{supply}"], '
    ...     else:
    ...         layout_roots += f'[id = "{supply}"]'

    >>> # do the drawing
    >>> app = dcv.draw_generic_graph(
    ...     energy_system=tsf_es,
    ...     layout='breadthfirst',
    ...     fd_kwargs={
    ...         "layout_nodeDimensionsIncludeLabels": True,
    ...         "layout_roots": layout_roots,
    ...     },
    ...     color_group=node_color,
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_generic_complex_example.png
        :align: center
        :alt: dcgrph draw generic graph of an optimized oemof es
    """
    if isinstance(energy_system, AbstractEnergySystem):
        nxgrph = energy_system.to_nxgrph()
        node_strings = [str(node.uid) for node in energy_system.nodes]
    else:
        # creat nxgrph form optimized_es:
        nxgrph, formatier = _nxgrph_and_formatier_from_optimized_es(
            energy_system, color_group)
        node_strings = [node for node in nxgrph.nodes]

    # def map_node_group_colors(node_uids, group):

    #     color_map = dict()
    #     for uid in node_uids:
    #         for key, variations in getattr(esci, group).items():
    #             if any(tag == getattr(uid, group) for tag in variations):
    #                 color_map[uid] = getattr(themes.colors, group)[key]

    #     return color_map

    if not isinstance(color_group, dict):
        _color_group = {
            'component': 'component',
            'sector': 'sector',
            'name': 'name',
            'carrier': 'carrier',
        }

        _color_map = themes.match_theme(
            strings=node_strings,
            theme='colors',
            grouping=_color_group[color_group],
        )
        _color_map = {str(k): v for k, v in _color_map.items()}
    else:
        _color_map = color_group

    return draw_graph(
        grph=nxgrph,
        stylesheet=generic_graph,
        node_color=_color_map,
        nrep=nrep,
        **kwargs
    )


def draw_advanced_graph(
        optimized_es,
        nodes_to_remove=(),
        layout='style',
        color_group='name',
        nrep='name',
        reference_node_width=None,
        reference_edge_width=None,
        reference_edge_blackness=None,
        **kwargs
):
    """Draw advanced graph utility.

    The generic graph layout tries to enhance visual comprehensivnes while
    keeping the information conveyed relatively low to facilitate quick human
    comprehension, resulting in following layout constraints.

    Nodes:

        - Node color (circular shape fill color) corresponds to of the
          following:

            * energy sector (:paramref:`~tessif.frused.namedtuples.Uid.sector`)
            * component type (storage, fossile fule powerplant, etc... )
              (:paramref:`~tessif.frused.namedtuples.Uid.component`)
            * energy carrier (wind, electricity, solar, hot water, etc...)
              (:paramref:`~tessif.frused.namedtuples.Uid.carrier`)
            * name (All components having ’offshore’ as part of their name for
              example)
              (:paramref:`~tessif.frused.namedtuples.Uid.name`)

        - Node size (circular shape diameter) is the same for each component.
        - Node position (arrangement of the circular shapes) is chosen to lower
          the amount subjectively perceived chaos, using either a
          hirarchical grid shape or a force layout, with as little overlapping
          edges as possible.

    Edges:

        - Edge length (arrow shaft length) is a result of node positioning
        - Edge color (arrow shaft and tip) is always black

    Parameters
    ----------
    tessif_es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system, used to draw the generic graph from.
    nodes_to_remove: ~collections.abc.Iterable
        Iterable of node uid representations to remove. Uses
        ``netowrkx.Graph.remove_node`` to remove nodes and adjacent edges
        prior to drawing the advanced graph.
    layout: str, default='style'
        String specifying the layout used. Use either one of the layouts found
        in :paramref:`draw_graph_from_data.layout`, or use one of the
        following:

            - ``'style'`` for using the `cose layout
              <https://js.cytoscape.org/#layouts/cose>`_ in conjunction with
              the :paramref:`correlated line style
              <tessif.transform.es2mapping.base.EdgeFormatier.cls>`, to
              visualize specific flow cost thresholds.

            - ``'length'`` for using the
              :func:`networkx.drawing.layout.kamada_kawai_layout` in
              conjunction a solid edge linestyle, visualizing specific flow
              costs via edge lengths in the sense of, the longer, the more
              expansive.

            - ``'cose'`` for using the `cose layout
              <https://js.cytoscape.org/#layouts/cose>`_ in conjunction with
              solid edge linestyle, taken flow costs somewhat into account,
              in the sense of the shorter, the more expansive.

    color_group: str, default='name'
        String specifying which of the
        :attr:`~tessif.frused.namedtuples.NodeColorGroupings` is used to theme
        the node colors
    nrep: str, default='name'
        String specifying how to represent node labels inside
        :paramref:`draw_graph_from_data.data`. Information gets passed to
        :paramref:`draw_graph.kwargs`, where it subsequently gets passed on to
        :paramref:`parse_dc_nodes.nrep` and :paramref:`parse_dc_edges.nrep`.

        Possible options are:

            - ``nrep='name'`` to use
              :paramref:`tessif.frused.namedtuples.Uid.name`
            - ``nrep='uid'`` to use ``str(``
              :class:`tessif.frused.namedtuples.Uid` ``)``

    kwargs
        Keyword argument are passed on to
        :paramref:`draw_graph_from_data.kwargs`. as well as to
        :paramref:`parse_dc_nodes.kwargs` and
        :paramref:`parse_dc_edges.kwargs`.

    Examples
    --------
    Default use case correlating edge style to specfic flow costs in the sense
    of the more solid, the more expansive:

    >>> import tessif.examples.data.omf.py_hard as omf_examples
    >>> import tessif.visualize.dcgrph as dcv

    >>> optimized_es = omf_examples.create_star()
    >>> app = dcv.draw_advanced_graph(optimized_es)
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_default_advanced_example.png
        :align: center
        :alt: dcgrph draw_advanced_graph design example

    Directly manipulating the `cytoscape layout
    <https://js.cytoscape.org/#layouts>`__ using ``'layout_'`` prefixed kwargs:

    >>> app = dcv.draw_advanced_graph(
    ...     optimized_es=optimized_es,
    ...     layout_nodeDimensionsIncludeLabels=True,
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_layout-kwarg_advanced_example.png
        :align: center
        :alt: dcgrph draw_advanced_graph design example

    Using the predefined ``'length'`` layout for correlating edge length
    to specfic flow costs in the sense of the longer, the more expansive:

    >>> app = dcv.draw_advanced_graph(
    ...     optimized_es=optimized_es,
    ...     layout='length',
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_layout-length_advanced_example.png
        :align: center
        :alt: dcgrph draw_advanced_graph design example

    Using the predefined ``'cose'`` layout for using a nonde repulsion layout
    while loosely correlating edge length to specfic flow costs.
    Meaning, the shorter the edge the higher the specific flow costs. With the
    edge lengthalso beeing influenced by node size i.e. installed capacity in
    the sense of the higher the installed capacity, the larger the node the
    greater the distance to other nodes:

    >>> app = dcv.draw_advanced_graph(
    ...     optimized_es=optimized_es,
    ...     layout='cose',
    ... )
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_layout-cose_advanced_example.png
        :align: center
        :alt: dcgrph draw_advanced_graph design example

    Since the above layout is somewhat unintuitive, it can be tweaked using the
    `cytoscape layout <https://js.cytoscape.org/#layouts>`__ kwargs forcing the
    layout to take label size into account effectively negating node size:

    >>> app = dcv.draw_advanced_graph(
    ...     optimized_es=optimized_es,
    ...     layout='cose',
    ...     layout_nodeDimensionsIncludeLabels=True,
    ... )
    >>> # comparing the layout to the specific flow costs:
    >>> from tessif.transform.es2mapping.omf import FlowResultier
    >>> flow_res = FlowResultier(optimized_es)
    >>> for node, flow_costs in sorted(
    ...         flow_res.edge_specific_flow_costs.items()):
    ...     print(node, flow_costs)
    Edge(source='Limited Power', target='Power Line') 1
    Edge(source='Power Line', target='Demand13') 0
    Edge(source='Power Line', target='Demand7') 0
    Edge(source='Power Line', target='Demand90') 0
    Edge(source='Unlimited Power', target='Power Line') 2
    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: images/dcgrph_layout-cose-tweaked_advanced_example.png
        :align: center
        :alt: dcgrph draw_advanced_graph design example
    """
    # creat nxgrph form optimized_es:
    nxgrph, formatier = _nxgrph_and_formatier_from_optimized_es(
        optimized_es,
        color_group,
        reference_node_width=reference_node_width,
        reference_edge_blackness=reference_edge_blackness,
        reference_edge_width=reference_edge_width,
    )

    # parse layout
    if layout == "style":
        edge_kwargs = {}
        layout_kwargs = {"layout": "cose"}
    elif layout == "cose":
        edge_kwargs = {"edge_linestyle": "solid"}
        layout_kwargs = {"layout": "cose"}
    elif layout == "length":
        edge_kwargs = {"edge_linestyle": "solid"}
        layout_kwargs = {
            "layout": {
                k: {'x': v[0], 'y': v[1]} for k, v in kkl(
                    G=nxgrph, weight='weight', scale=250).items()
            },
        }
    else:
        edge_kwargs = {}
        layout_kwargs = {"layout": layout}

    # remove nodes if requested
    for node in nodes_to_remove:
        if node in nxgrph.nodes:
            nxgrph.remove_node(node)

    # parse the node data
    node_data = parse_dc_nodes(
        grph=nxgrph,
        # designed to be returned by the api:
        node_attr=formatier.node_data(),
        dflts=dflts,
        nrep=nrep,
        **kwargs
    )

    # parse the node data
    edge_data = parse_dc_edges(
        grph=nxgrph,
        # mocked here, because designed to be returned by the api:
        edge_attr=formatier.edge_data(),
        node_attr=formatier.node_data(),
        dflts=dflts,
        nrep=nrep,
        **edge_kwargs,
        **kwargs
    )

    return draw_graph_from_data(
        data=edge_data+node_data,
        **layout_kwargs,
        **kwargs
    )


def greyscale2hex(greyscale, minn=0.0, maxn=1.0):
    """Correlate a number within a certain range to a hex encoded gray value.

    Parameters
    ----------
    greyscale: ~numbers.Number
        Number between :paramref:`minn` and :paramref:`maxn` representing the
        greyscale. Where :paramref:`minn` =  ``'white'`` and
        :paramref:`maxn` = ``'black'``.
    minn: ~number.Number, default=0.0
        Lower boundary resulting in a white color hex value
    maxn: ~number.Number, default=1.0
        Upper boundary resulting in a black color hex value

    Returns
    -------
    hex
        single hex color value representing the correlated grayscale color.

    Examples
    --------
    >>> greyscale2hex(.3)
    '#b2b2b2'
    >>> greyscale2hex(.7)
    '#4c4c4c'
    >>> greyscale2hex(50, 0, 100)
    '#7f7f7f'
    >>> greyscale2hex(1e10, 0, 1e20)
    '#fefefe'
    >>> greyscale2hex(0)
    '#ffffff'
    >>> greyscale2hex(1)
    '#000000'
    >>> greyscale2hex(0.0)
    '#ffffff'
    >>> greyscale2hex(1.0)
    '#000000'
    """
    greyscale = _clamp(greyscale, minn, maxn)
    rgb_int = int((maxn-greyscale)/maxn * 255)
    return "#{0:02x}{1:02x}{2:02x}".format(rgb_int, rgb_int, rgb_int)


def _clamp(number, minn, maxn):
    """Clamp number to be within [minn, maxn]."""
    return max(min(maxn, number), minn)


def _get_uid_string_representation(tessif_es_node):
    """Return node uid string representation"""
    return str(tessif_es_node)


def _get_uid_name(tessif_es_node):
    """Return nod uid name."""
    return tessif_es_node.split(node_uid_seperator)[0]


def _nxgrph_and_formatier_from_optimized_es(
        optimized_es,
        color_group,
        reference_node_width=None,
        reference_edge_width=None,
        reference_edge_blackness=None,
):
    # infer model
    software = infer_software_from_es(optimized_es)
    internal_software_name = infer_registered_model(software)

    # import post processing utility
    post_processing = importlib.import_module(
        ".".join(["tessif.transform.es2mapping", internal_software_name]))

    # post process and create formatier...
    formatier = post_processing.AllFormatier(
        optimized_es,
        cgrp=color_group,
        drawutil='dc',
        reference_capacity=reference_node_width,
        reference_net_energy_flow=reference_edge_width,
        reference_emissions=reference_edge_blackness,
    )

    # .. as well as the nxgraph
    nxgrph = nxt.Graph(post_processing.FlowResultier(optimized_es))

    return nxgrph, formatier


def _create_dash_app_from_ct_graph(ct_graph):
    """Wrap the dc app creation to refactor callbacks and layout specifics."""
    # preload the app for drawing
    app = dash.Dash(__name__)

    app.layout = html.Div(
        [
            html.Div(
                className='eight columns',
                children=[ct_graph, ]
            ),
            html.Div(
                className='two columns',
                children=[
                    html.Div('Download graph:'),
                    html.Button("as jpg", id="btn-get-jpg"),
                    html.Button("as png", id="btn-get-png"),
                    html.Button("as svg", id="btn-get-svg"),
                ],
            )
        ],
    )

    @app.callback(
        Output('image-text', 'children'),
        Input('cytoscape-image-export', 'imageData'),
    )
    def put_image_string(data):
        return data

    @app.callback(
        Output("cytoscape-image-export", "generateImage"),
        [
            # Input('tabs-image-export', 'value'),
            Input("btn-get-jpg", "n_clicks"),
            Input("btn-get-png", "n_clicks"),
            Input("btn-get-svg", "n_clicks"),
        ])
    def get_image(
            # tab,
            get_jpg_clicks,
            get_png_clicks,
            get_svg_clicks,
    ):

        # File type to output of 'svg, 'png', 'jpg', or 'jpeg' (alias of 'jpg')
        ftype = None

        # 'store': Stores the image data in 'imageData' !only jpg/png are
        # supported
        # 'download'`: Downloads the image as a file with all data handling
        # 'both'`: Stores image data and downloads image as file.
        action = 'store'

        ctx = dash.callback_context
        if ctx.triggered:
            input_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # if input_id != "tabs":
            action = "download"
            ftype = input_id.split("-")[-1]

        return {
            'type': ftype,
            'action': action
        }

    return app
