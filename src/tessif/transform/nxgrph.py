# tessif/transform/nxgrph.py
"""
:mod:`nxgrph` is a :mod:`tessif` interface transforming the dictionairy
representation (see :mod:`tessif.transform.es2mapping`) of an (optimized)
energy system simulation model into a :class:`networkx.DiGraph`.

This module follows a 2 way approach on constructing :class:`networkx.Graph`
like objects:

    1. Approach is to expose a class like structure
       (:class:`~tessif.transform.nxgrph.Graph`) needing an
       :class:`~tessif.transform.es2mapping.base.ESTransformer` object for
       construction. Allowing automated postprocessing.

    2. Approach is exposing two explicit functions to create nodes and
       edges assuming a Graph like object already exists (which obviously
       could have been just constructed). This emulates puplic API
       functionality and allows the use of the dict processing capabilities
       coming with this module seperatey.


Note
----
When using this module to perform `NetworkX operations
<https://networkx.github.io/documentation/stable/reference/algorithms/index.html>`_
on the energy system it might be required to temporariliy `relabel nodes to
integers
<https://mriduls-networkx.readthedocs.io/en/latest/reference/relabel.html>`_
because of `complex node labeling
<https://networkx.github.io/documentation/stable/reference/generated/networkx.drawing.nx_agraph.pygraphviz_layout.html>`_.

"""
import tessif.frused.defaults as conventions
from tessif.frused.namedtuples import Edge
from tessif.write import log

import networkx
from collections import defaultdict
import logging
import dcttools


logger = logging.getLogger(__name__)


@log.timings
def create_nodes(graph, nodes, defaults={}, **kwargs):
    """
    Takes a nodelist of string uids as positional argument. All other
    arguments are aggregated into kwargs and end up as node attributes which
    are accesible via :attr:`networkx.Graph.nodes(data='attribute')
    <networkx.Graph.nodes>`

    Parameters
    ----------
    graph : :class:`networkx.Graph` like object
        Graph object the nodes are created for and added to.

    nodes: :class:`~collections.abc.Iterable`
        Iterable of node uids as strings as in::

            ['1', '2', '3']

        or::

            [str(node.uid) for node in energy_sytem.nodes]

    defaults : dict, default={}
        In case a dict is provided via :paramref:`~create_nodes.kwargs`
        and not every node is present in this dict, the keyword argument
        will be looked for in :paramref:`~create_nodes.defaults`.

    kwargs: value, dict
        Node attributes as keyword arguments to pass to the created nodes.
        Using a node dict as in ``{node: attribute}`` allows different
        attributes for each node.

        All keyword arguments can be single value arguments or
        ``{node_uid: value}`` dictionairies.
        :paramref:`~create_nodes.defaults` are used for those nodes not present
        in the dictionairy. Otherwise value will be set to ``None``.

        Note
        ----
        To pass a bunch of keyword arguments directly use
        :meth:`networkx.Graph.add_node` to supply them directly as in

        >>> import networkx
        >>> grph = networkx.Graph()
        >>> kwargs = {'arg_1': 'value_1', 'arg_2': 'value_2'}
        >>> grph.add_node('node_1', **kwargs)
        >>> print(grph.nodes(data=True))
        [('node_1', {'arg_1': 'value_1', 'arg_2': 'value_2'})]

    Return
    ------
    node_attr : dict
        A dictionairy holding the processed and passed node attributes.

    Examples
    --------
    Use a dict to populate each node seperatey. Use a single value for uniform
    value setting (logging stuff is done to enable tessif internal doctesting
    and can be ignored here):

    >>> from tessif.transform import nxgrph
    >>> import networkx as nx
    >>> import pprint
    >>> nodes = ['1', '2', '3']
    >>> grph = nx.DiGraph(name='my_graph')
    >>> node_attributes = nxgrph.create_nodes(
    ...     grph, nodes,
    ...     d=dict(zip(nodes, [10, 20, 30])),
    ...     i=1)
    >>> pprint.pprint(node_attributes)
    {'1': {'d': 10, 'i': 1}, '2': {'d': 20, 'i': 1}, '3': {'d': 30, 'i': 1}}
    """
    # Generate a node_attr dictionairy: {node: {attr: value}}
    # Use defaultdict adding a new dict entry if key not present
    node_attr = defaultdict(dict)

    # aggregate kwargs into a nested dict as in {node: {attr: parameter}}
    node_attr = dcttools.maggregate(
        tlkys=nodes, nstd_dcts=[node_attr, ], dcts=[defaults, ],
        **kwargs)

    #  create nodes, return empty dict as attribute if no attribute present
    for node in nodes:
        graph.add_node(node, **node_attr.get(node, {}))

    return node_attr


@log.timings
def create_edges(graph, edges, defaults={}, **kwargs):
    """
    Convenience function to populate the Graph-object with edges.

    Takes an iterable of edge tuple uids as positional argument.
    All other arguments are aggregated into kwargs
    and end up as edge attributes which are accesible via
    :attr:`networkx.Graph.edges(data='attribute')
    <networkx.Graph.edges>`


    Parameters
    ----------
    graph : :class:`networkx.Graph` like object
        Graph object the nodes are created for and added to.

    edges: :class:`~collections.abc.Iterable`
        Iterable of edge uids as strings as in::

            [('1', '2'), ('2', '3'), ('3', '1')]

        or::

            [(str(inflow.uid), str(node.uid))
                for node in esystem.nodes for inflow in node.inputs.keys()]

    defaults : dict, default={}
        In case a dict is provided via :paramref:`~create_edges.kwargs`
        and not every node is present in this dict, the keyword argument
        will be looked for in :paramref:`~create_edges.defaults`.

    kwargs: value, dict
        Edge attributes as keyword arguments to pass to the created nodes.
        Using a node dict as in
        ``{('node_from_uid', 'node_to_uid'): value}`` allows different
        attributes for each node.

        All keyword arguments can be single value arguments or
        ``{('node_from_uid', 'node_to_uid'): value}`` dictionairies.
        :paramref:`~create_edges.defaults` are used for those edges not
        present in the dictionairy. Otherwise value will set to ``None``.

    Return
    ------
    edge_attr : dict
        A dictionairy holding the processed and passed edge attributes.

    Examples
    --------
    Use a dict to populate each edge seperatey. Use a single value for uniform
    value setting (logging stuff is done to enable tessif internal doctesting
    and can be ignored here):

    >>> from tessif.transform import nxgrph
    >>> import networkx as nx
    >>> import pprint
    >>> edges = [('1', '2'), ('2', '3')]
    >>> grph = nx.DiGraph(name='my_graph')
    >>> edge_attributes = nxgrph.create_edges(
    ...     grph, edges,
    ...     d=dict(zip(edges, [10, 20])),
    ...     v=1)
    >>> pprint.pprint(edge_attributes)
    {Edge(source='1', target='2'): {'d': 10, 'v': 1},
     Edge(source='2', target='3'): {'d': 20, 'v': 1}}

    """
    # Use namedtuplpes, cause idiomatic python:
    # transform edge iterable into a namedtuple Edge list:
    Edges = [Edge(*edge) for edge in edges]

    # generate an edge_attr dictionairy: {edge: {attr: value}}
    # Use default dict adding a new dict entry if key not present
    edge_attr = defaultdict(dict)

    # aggregate kwargs into a nested dict as in {edge: {attr: parameter}}
    edge_attr = dcttools.maggregate(
        tlkys=Edges, nstd_dcts=[edge_attr, ], dcts=[defaults, ],
        **kwargs)

    # Iterate through Edges to specify each edge individually:
    for edge in Edges:
        # Create edges, return empty dict if no edge attributes present
        graph.add_edge(edge.source, edge.target, **edge_attr.get(edge, {}))

    return edge_attr


class Graph(networkx.DiGraph):
    """
    Graph object holding relevant energy system data as node and edge
    attributes.

    Convenience wrapper for creating a :class:`networkx.DiGraph` Designed to
    be used with a :class:`~tessif.transform.es2mapping.base.ESTransformer`
    object.

    For more flexibility and control use :func:`create_nodes` and
    :func:`create_edges`.

    Parameters
    ----------
    es_transformer : :class:`~tessif.transform.es2mapping.base.ESTransformer`
        Energy system to dictionairy transformer object returning its data as
        a 2 layer nested dict in the form of
        ``{attribute: {node/edge: parameter}}`` if accessed for
        :func:`~tessif.transform.es2mapping.base.ESTransformer.node_data` /
        :func:`~tessif.transform.es2mapping.base.ESTransformer.edge_data`
        respectively. As well es a default dictionairy for node and edge
        attributes if accessed for
        :attr:`~tessif.transform.es2mapping.base.ESTransformer.defaults`

    **kwargs : key word arguments
        kwargs are passed to :class:`networkx.DiGraph`

    Examples
    --------
    Use the :class:`Example Resultier
    <tessif.transform.es2mapping.base.XmplResultier>` to demonstrate behaviour:

    >>> from tessif.transform import nxgrph
    >>> from tessif.transform.es2mapping.base import XmplResultier
    >>> import pprint
    >>> grph = nxgrph.Graph(XmplResultier())
    >>> pprint.pprint(list(grph.nodes(data=True)))
    [('1', {'attr_xmpl': 'red'}),
     ('2', {'attr_xmpl': 'red'}),
     ('3', {'attr_xmpl': 'red'})]
    >>> pprint.pprint(list(grph.edges(data=True)))
    [('1', '2', {'attr_xmpl': 3}),
     ('2', '3', {'attr_xmpl': 5}),
     ('3', '1', {'attr_xmpl': 4})]

    Use the oemof minimum working example together with the AllResultier:

    >>> from tessif.transform.es2mapping.omf import AllResultier
    >>> import tessif.examples.data.omf.py_hard as omf_examples
    >>> grph = nxgrph.Graph(AllResultier(omf_examples.create_mwe()))
    >>> pprint.pprint(list(grph.edges(data='specific_flow_costs')))
    [('Power Line', 'Demand', 0),
     ('Renewable', 'Power Line', 9),
     ('CBET', 'Transformer', 0),
     ('CBE', 'CBET', 0),
     ('Transformer', 'Power Line', 10)]

    """
    @log.timings
    def __init__(self, es_transformer, **kwargs):
        # call super constructor (netowrkx.DiGraph())
        super().__init__(**kwargs)

        fltr = conventions.nxgrph_visualize_tags.node
        xcptns = conventions.nxgrph_visualize_xcptns.node
        node_attr, defaults = dcttools.kfrep(
            dcts=dcttools.kfltr(
                dcts=[es_transformer.node_data(), es_transformer.defaults],
                fltr=fltr),
            fnd=fltr, xcptns=xcptns)

        # Create a grpah
        create_nodes(
            graph=self,
            nodes=es_transformer.nodes,
            defaults=defaults,
            **node_attr)

        fltr = conventions.nxgrph_visualize_tags.edge
        xcptns = conventions.nxgrph_visualize_xcptns.edge
        edge_attr, defaults = dcttools.kfrep(
            dcts=dcttools.kfltr(
                dcts=[es_transformer.edge_data(), es_transformer.defaults],
                fltr=fltr),
            fnd=fltr, xcptns=xcptns)

        create_edges(
            graph=self,
            edges=es_transformer.edges,
            defaults=defaults,
            **edge_attr)

        logger.info("Successfully created an energy system graph with " +
                    "{:.0f} nodes and {:.0f} edges".format(
                        self.number_of_nodes(),
                        self.number_of_edges()))

    def __repr__(self):
        return '<%s.%s object at %s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            hex(id(self))
        )

    def __str__(self):
        return self.__repr__()
