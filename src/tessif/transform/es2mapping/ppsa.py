# tessif/transform/es2mapping/ppsa.py
"""
:mod:`~tessif.transform.es2mapping.pypsa` is a :mod:`tessif` module holding
:class:`pypsa.Network` transformer classes for postprocessing results and
providing a tessif uniform interface.
"""
import logging
from collections import defaultdict, abc

import numpy as np
import pandas as pd

import tessif.transform.es2mapping.base as base
import tessif.write.log as log

from tessif.frused import (
    configurations as configs,
    namedtuples as nts,
)

from tessif.frused.defaults import (
    energy_system_nodes as esn_defaults,
)


logger = logging.getLogger(__name__)


class PypsaResultier(base.Resultier):
    r""" Transform nodes and edges into their name representation. Child of
    :class:`~tessif.transform.es2mapping.base.Resultier` and mother of all
    pypsa Resultiers.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    Examples
    --------
    Use the hard :mod:`coded pypsa examples
    <tessif.examples.data.pypsa.py_hard>` to test this resultiers capabilities:

    >>> import tessif.examples.data.pypsa.py_hard as coded_examples
    >>> optimized_pypsa_es = coded_examples.emission_objective()
    >>> resultier = PypsaResultier(optimized_pypsa_es)

    1. Get a list of present nodes:

        >>> for node in resultier.nodes:
        ...     print(node)
        Power Line
        Renewable
        Gas Generator
        Demand

    2. Get a list of present edges:

        >>> for edge in resultier.edges:
        ...     source, target = edge
        ...     print(f"{source} -> {target}")
        Renewable -> Power Line
        Gas Generator -> Power Line
        Power Line -> Demand

    3. Get a dict for node string representations and their uids:

        >>> for name, uid in resultier.uid_nodes.items():
        ...     print(name, type(uid))
        Power Line <class 'tessif.frused.namedtuples.Uid'>
        Renewable <class 'tessif.frused.namedtuples.Uid'>
        Gas Generator <class 'tessif.frused.namedtuples.Uid'>
        Demand <class 'tessif.frused.namedtuples.Uid'>

    """

    component_type_mapping = {
        'buses': 'bus',
        'generators': 'transformer',
        'links': 'connector',
        'loads': 'sink',
        'storage_units': 'storage',
        'transformers': 'transformer',
    }

    edge_busses = {
        'generators': ('bus',),
        'links': ('arbitrary',),
        'loads': ('bus',),
        'storage_units': ('bus',),
        'transformers': ('bus0', 'bus1',),
    }

    # use pypsa "type" attribute to ignore certain components
    types_to_ignore = [
        "ignore",
    ]

    def __init__(self, optimized_es, **kwargs):

        if not hasattr(optimized_es, "excess_sinks"):
            setattr(optimized_es, "excess_sinks", {})

        super().__init__(optimized_es=optimized_es, **kwargs)
        self._uid_nodes = self._map_node_uids(optimized_es)

    @log.timings
    def _map_node_uids(self, optimized_es):
        r"""Return node uids as mapped to their string representation"""

        nodes = dict()
        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                if not any([itype == getattr(
                            optimized_es, ntype).loc[name]["type"]
                            for itype in PypsaResultier.types_to_ignore]):

                    # preliminary uid for ease of access
                    prelim_uid = nts.Uid.reconstruct(name)
                    # enforce component data field for post processing
                    if prelim_uid.component is None:
                        uid_dict = prelim_uid._asdict()
                        uid_dict[
                            'component'] = PypsaResultier.component_type_mapping[
                                ntype]
                        # auto correct excess sinks:
                        if getattr(optimized_es, ntype).loc[name]["type"] == "excess_sink":
                            uid_dict['component'] = "sink"
                        uid = nts.Uid(**uid_dict)
                    else:
                        uid = prelim_uid
                    nodes[name] = uid
        return nodes

    @log.timings
    def _map_nodes(self, optimized_es):
        r"""Return string representation of node labels as :class:`list`"""

        nodes = list()
        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                # ignore respectively flagged components
                if not any([itype == getattr(
                        optimized_es, ntype).loc[name]["type"]
                        for itype in PypsaResultier.types_to_ignore]):

                    # pypsa result tables already represent a node uid's
                    # string representation
                    nodes.append(name)
        return nodes

    @log.timings
    def _map_edges(self, optimized_es):
        es = optimized_es

        edges = list()
        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(es, ntype).index:

                # ignore respectively flagged components
                if not any([itype == getattr(
                        optimized_es, ntype).loc[name]["type"]
                        for itype in PypsaResultier.types_to_ignore]):

                    if ntype in PypsaResultier.edge_busses.keys():
                        # distinguish between components of 2 distinct edges
                        # that always have edges like bus0 -> node -> bus1
                        if len(PypsaResultier.edge_busses[ntype]) == 2:
                            e = nts.Edge(
                                name,
                                # get bus1 edge from its tabular entry
                                # string representation
                                getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][1]][name]
                            )
                            edges.append(e)
                            edges.append(nts.Edge(e.target, e.source))

                            e = nts.Edge(
                                # get bus0 from tabular entry
                                getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][0]][name],
                                name
                            )
                            edges.append(e)
                            edges.append(nts.Edge(e.target, e.source))

                        # gens always have edges like generator -> bus
                        elif ntype == 'generators':
                            edges.append(
                                nts.Edge(
                                    name,
                                    getattr(es, ntype)[
                                        PypsaResultier.edge_busses[ntype][0]][name]
                                )
                            )
                        # loads always have edges like bus -> load
                        elif ntype == 'loads':
                            edges.append(
                                nts.Edge(
                                    getattr(es, ntype)[PypsaResultier.edge_busses[
                                        ntype][0]][name],
                                    name
                                )
                            )

                        # storages always have edges like bus <=> storage
                        # except for when they mimic excess sinks:
                        elif ntype == 'storage_units':
                            e = nts.Edge(
                                getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][0]][name],
                                name
                            )
                            edges.append(e)
                            # only add returning edge if not a excess sink
                            # emulating storage
                            if not getattr(
                                    es, ntype).loc[name].type == "excess_sink":
                                edges.append(nts.Edge(e.target, e.source))

                        elif ntype == 'links':
                            # inputs

                            if hasattr(es.links, 'multiple_inputs'):
                                if bool(es.links.multiple_inputs[name]):
                                    bus_cols = [
                                        col for col in es.links.columns
                                        if 'bus' in col and 'bus1' not in col
                                    ]
                                    for bus in bus_cols:
                                        e = nts.Edge(
                                            getattr(es, ntype)[bus][name],
                                            name
                                        )
                                        edges.append(e)
                                else:
                                    # multiple_inputs attribute present but false
                                    e = nts.Edge(es.links['bus0'][name], name)
                                    edges.append(e)

                            else:
                                # multiple_inputs attribute not present
                                e = nts.Edge(
                                    es.links['bus0'][name],
                                    name
                                )
                                edges.append(e)
                                # link could be a siso transformer
                                if hasattr(es.links, 'siso_transformer'):
                                    if not bool(es.links.siso_transformer[name]):
                                        if hasattr(es.links, 'multiple_outputs'):
                                            if not bool(es.links.multiple_outputs[name]):

                                                # no its not so it must be generic link
                                                # and therfor be bidirectional
                                                edges.append(
                                                    nts.Edge(e.target, e.source))

                                        else:
                                            # no its not so it must be generic link
                                            # and therfor be bidirectional
                                            edges.append(
                                                nts.Edge(e.target, e.source))

                                # or just have multiple outputs
                                elif hasattr(es.links, 'multiple_outputs'):
                                    if not bool(es.links.multiple_outputs[name]):
                                        # no its not so it must be generic link
                                        # and therfor be bidirectional
                                        e = nts.Edge(e.target, e.source)
                                        if e not in edges:
                                            edges.append(e)

                                else:
                                    # no its not so it must be a generic link
                                    # and therfor be bidirectional
                                    edges.append(nts.Edge(e.target, e.source))

                            # outputs
                            if hasattr(es.links, 'multiple_outputs'):
                                if bool(es.links.multiple_outputs[name]):
                                    bus_cols = [
                                        col for col in es.links.columns
                                        if 'bus' in col and 'bus0' not in col
                                    ]

                                    for bus in bus_cols:
                                        e = nts.Edge(
                                            name,
                                            getattr(es, ntype)[bus][name]
                                        )
                                        edges.append(e)
                                else:
                                    # multiple_outputs attribute present but false
                                    e = nts.Edge(name, es.links['bus1'][name])
                                    edges.append(e)

                                    # is it a siso transformer ?
                                    if hasattr(es.links, 'siso_transformer'):
                                        if not bool(es.links.siso_transformer[name]):
                                            if hasattr(es.links, 'multiple_inputs'):
                                                if not bool(es.links.multiple_inputs[name]):
                                                    # no its not so it must be a generic link
                                                    # and therfor be bidirectional
                                                    edges.append(
                                                        nts.Edge(e.target, e.source))
                                            else:
                                                # no its not so it must be a
                                                # generic link
                                                # and therfor be bidirectional
                                                edges.append(
                                                    nts.Edge(e.target, e.source))

                                    elif hasattr(es.links, 'multiple_inputs'):
                                        if not bool(es.links.multiple_inputs[name]):
                                            # no its not so it must be a generic link
                                            # and therfor be bidirectional
                                            edges.append(
                                                nts.Edge(e.target, e.source))
                                    else:
                                        # no its not so it must be a generic link
                                        # and therfor be bidirectional
                                        edges.append(
                                            nts.Edge(e.target, e.source))

                            else:
                                # multiple_outputs attribute not present
                                e = nts.Edge(
                                    name,
                                    # get bus1 edge from its tabular entry
                                    # string representation
                                    es.links['bus1'][name]
                                )
                                edges.append(e)

                                # link could be a siso transformer
                                if hasattr(es.links, 'siso_transformer'):
                                    if not bool(es.links.siso_transformer[name]):
                                        # no its not so it must be a generic link
                                        # and therfor be bidirectional
                                        edges.append(
                                            nts.Edge(e.target, e.source))
                                else:
                                    # no its not so it must be a generic link
                                    # and therfor be bidirectional
                                    edges.append(nts.Edge(e.target, e.source))

                        else:
                            raise TypeError(
                                f"Pypsa component '{ntype}' not recognized")

        # add excess sinks:
        for excs in es.excess_sinks:
            link_name = "-".join([excs, "Link"])
            bus_name = getattr(es, "links").loc[link_name]["bus0"]
            e = nts.Edge(bus_name, excs)
            edges.append(e)

        edges_to_remove = []
        for ntype in ["links", "buses"]:
            for edge in edges:
                df = getattr(es, ntype)
                if any([
                        edge_comp in df[df["type"] == "ignore"].index
                        for edge_comp in edge]):
                    edges_to_remove.append(edge)

        # print(edges_to_remove)
        return [edge for edge in edges if edge not in edges_to_remove]

    def _map_edge_uids(self, optimized_es):
        r"""Return string representation of (inflow, node) labels as
        :class:`list`"""
        es = optimized_es

        edges = list()
        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(es, ntype).index:
                if ntype in PypsaResultier.edge_busses.keys():

                    # distinguish between components of 2 distinct edges
                    # the always have edges like bus0 -> node -> bus1
                    if len(PypsaResultier.edge_busses[ntype]) == 2:
                        e = nts.Edge(
                            # reassamble node Uid from its string
                            # representation
                            nts.Uid(
                                *name.split(configs.node_uid_seperator)),
                            name,
                            # reassamble bus1 edge from its tabular entry
                            # string representation
                            nts.Uid(*getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][1]][
                                        name].split(
                                            configs.node_uid_seperator)),
                        )
                        edges.append(e)
                        edges.append(nts.Edge(e.target, e.source))

                        e = nts.Edge(
                            # reassamble Uid from its string representation
                            nts.Uid(*getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][0]][
                                        name].split(
                                            configs.node_uid_seperator)),
                            # reassamble bus1 edge from its tabular entry
                            # string representation
                            nts.Uid(
                                *name.split(configs.node_uid_seperator)),
                        )
                        edges.append(e)
                        edges.append(nts.Edge(e.target, e.source))
                        # generators always have edges like gen -> bus
                    elif ntype == 'generators':
                        edges.append(
                            nts.Edge(
                                # reassamble Uid from its string representation
                                nts.Uid(
                                    *name.split(configs.node_uid_seperator)),
                                # reassamble bus edge from its tabular entry
                                # string representation
                                nts.Uid(*getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][0]][
                                        name].split(
                                            configs.node_uid_seperator)),
                            )
                        )
                    # loads always have edges like bus -> load
                    elif ntype == 'loads':
                        edges.append(
                            nts.Edge(
                                # reassamble node Uid from its string
                                # representation
                                nts.Uid(*getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][0]][
                                        name].split(
                                            configs.node_uid_seperator)),
                                # reassamble bus1 edge from its tabular entry
                                # string representation
                                nts.Uid(
                                    *name.split(configs.node_uid_seperator)),
                            )
                        )

                    # storages always have edges like bus <=> storage
                    elif ntype == 'storage_units':
                        edges.append(
                            nts.Edge(
                                # reassamble node Uid from its string
                                # representation
                                nts.Uid(*getattr(es, ntype)[
                                    PypsaResultier.edge_busses[ntype][0]][
                                        name].split(
                                            configs.node_uid_seperator)),
                                # reassamble bus edge from its tabular entry
                                # string representation
                                nts.Uid(
                                    *name.split(configs.node_uid_seperator)),
                            )
                        )
                        # only add returning edge if not a excess sink
                        # emulating storage
                        if not getattr(
                                es, ntype).loc[name].type == "excess_sink":
                            edges.append(
                                nts.Edge(
                                    nts.Uid(
                                        *name.split(configs.node_uid_seperator)),
                                    nts.Uid(*getattr(es, ntype)[
                                        PypsaResultier.edge_busses[ntype][0]][
                                            name].split(
                                                configs.node_uid_seperator)),
                                )
                            )
                    else:
                        raise TypeError(
                            f"Pypsa component '{ntype}' not recognized")

        return edges


class IntegratedGlobalResultier(
        PypsaResultier, base.IntegratedGlobalResultier):
    """
    Extracting the integrated global results out of the energy system and
    conveniently aggregating them (rounded to unit place) inside a dictionairy
    keyed by result name.

    Integrated global results (IGR) mapped by result name.

    Integrated global results currently consist of meta and non-meta
    results. the **meta** results are handled by the :mod:`~tessif.analyze`
    module (see :attr:`tessif.analyze.Comparatier.integrated_global_results`)
    and consist of:

        - ``time``
        - ``memory``

    results, whereas the **non-meta** results usually consist of:

        - ``emissions``
        - ``costs``

    results which are handled here. Tessif's energy system, however, allow to
    formulate a number of
    :attr:`~tessif.model.energy_system.AbstractEnergySystem.global_constraints`
    which then would automatically be post processed here.

    The befornamed strings serve as key inside the mapping.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.IntegratedGlobalResultier>`.

    Examples
    --------
    >>> import tessif.examples.data.pypsa.py_hard as coded_examples
    >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
    >>> import pprint

    1. Global results on an emissions constrained es:

        >>> emission_constrained_es = coded_examples.emission_objective()
        >>> resultier = post_process_pypsa.IntegratedGlobalResultier(
        ...     emission_constrained_es)
        >>> pprint.pprint(resultier.global_results)
        {'capex (ppcd)': 0.0,
         'costs (sim)': 110.0,
         'emissions (sim)': 0.0,
         'opex (ppcd)': 110.0}

    2. Global results on an unconstrained es:

        >>> unconstrained_es = coded_examples.create_mwe()
        >>> resultier = post_process_pypsa.IntegratedGlobalResultier(
        ...     unconstrained_es)
        >>> pprint.pprint(resultier.global_results)
        {'capex (ppcd)': 0.0,
         'costs (sim)': 190.0,
         'emissions (sim)': 0.0,
         'opex (ppcd)': 190.0}
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_global_results(self, optimized_es):

        flow_results = FlowResultier(optimized_es)
        cap_results = CapacityResultier(optimized_es)

        total_emissions = 0.0
        flow_costs = 0.0

        capital_costs = 0.0

        for edge in self.edges:
            net_energy_flow = flow_results.edge_net_energy_flow[edge]
            specific_emissions = flow_results.edge_specific_emissions[edge]
            specific_flow_costs = flow_results.edge_specific_flow_costs[edge]

            total_emissions += (
                net_energy_flow *
                specific_emissions
            )

            flow_costs += (
                net_energy_flow *
                specific_flow_costs
            )

        for node in self.nodes:
            initial_capacity = cap_results.node_original_capacity[node]
            final_capacity = cap_results.node_installed_capacity[node]
            expansion_cost = cap_results.node_expansion_costs[node]

            if not any(
                    [cap is None
                     for cap in (final_capacity, initial_capacity)]
            ):

                # expansion costs for storages needs to be corrected, since
                # pypsa uses power/flow expansion exclusively
                if node in optimized_es.storage_units.index:
                    expansion_cost /= optimized_es.storage_units[
                        'max_hours'][node]

                node_expansion_costs = (
                    (final_capacity - initial_capacity) *
                    expansion_cost
                )
            else:
                node_expansion_costs = 0

            if isinstance(initial_capacity, pd.Series):
                node_expansion_costs = sum(node_expansion_costs)

            capital_costs += node_expansion_costs

        return {
            'emissions (sim)': round(total_emissions, 0),
            'costs (sim)': round(optimized_es.objective, 0),
            'opex (ppcd)': round(flow_costs, 0),
            'capex (ppcd)': round(capital_costs, 0),
        }


class ScaleResultier(PypsaResultier, base.ScaleResultier):
    """
    Extract number of constraints and store them as int.

    Parameters
    ----------
    optimized_es:
        :ref:`Model <SupportedModels>` specific, optimized energy system
        containing its results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.ScaleResultier>`.

    Examples
    --------

    1. Call and optimize a Pypsa energy system model.

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> resultier = post_process_pypsa.ScaleResultier(
        ...     pypsa_examples.create_transshipment_problem())

    2. Access the number of constraints.

        >>> print(resultier.number_of_constraints)
        13
    """
    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_number_of_constraints(self, optimized_es):
        """Interface to extract the number of constraints out of the
        :ref:`model <SupportedModels>` specific, optimized energy system.
        """
        return optimized_es.results.problem.number_of_constraints


class LoadResultier(PypsaResultier, base.LoadResultier):
    """
    Transforming flow results into dictionairies keyed by node uid string
    representation.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.LoadResultier>`.

    Examples
    --------
    1. Accessing a node's outflows as positive numbers and a node's inflows as
       negative numbers:
       (See :attr:`tessif.transform.es2mapping.base.LoadResultier.node_load`
       for more documentation):

        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> resultier = post_process_pypsa.LoadResultier(
        ...     coded_pypsa_examples.create_transshipment_problem())
        >>> print(resultier.node_load['connector-01->02'])
        connector-01->02     bus-01  bus-02  bus-01  bus-02
        1990-07-13 00:00:00   -10.0    -0.0     0.0    10.0
        1990-07-13 01:00:00    -0.0    -5.0     5.0     0.0
        1990-07-13 02:00:00    -0.0    -0.0     0.0     0.0

    2. Accessing a node's inflows as positive numbers
       (See :attr:`tessif.transform.es2mapping.base.LoadResultier.node_inflows`
       for more documentation):

        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> resultier = post_process_pypsa.LoadResultier(
        ...     coded_pypsa_examples.create_transshipment_problem())
        >>> print(resultier.node_inflows['sink-01'])
        sink-01              bus-01
        1990-07-13 00:00:00     0.0
        1990-07-13 01:00:00    15.0
        1990-07-13 02:00:00    10.0

    3. Accessing a node's inflows as positive numbers (See
       :attr:`tessif.transform.es2mapping.base.LoadResultier.node_outflows`
       for more documentation):

        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> resultier = post_process_pypsa.LoadResultier(
        ...     coded_pypsa_examples.create_transshipment_problem())
        >>> print(resultier.node_outflows['bus-02'])
        bus-02               connector-01->02  sink-02
        1990-07-13 00:00:00               0.0     15.0
        1990-07-13 01:00:00               5.0      0.0
        1990-07-13 02:00:00               0.0     10.0

    4. Accessing a node's summed inflows as positive numbers (in case it is
       of component
       :attr:`sink <tessif.frused.defaults.registered_component_types>`)
       or a node's summed outflows (in case it is not a sink).
       (See
       :attr:`tessif.transform.es2mapping.base.LoadResultier.node_summed_loads`
       for more documentation):

        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> resultier = post_process_pypsa.LoadResultier(
        ...     coded_pypsa_examples.create_transshipment_problem())
        >>> print(resultier.node_summed_loads['bus-01'])
        1990-07-13 00:00:00    10.0
        1990-07-13 01:00:00    15.0
        1990-07-13 02:00:00    10.0
        Freq: H, dtype: float64
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_loads(self, optimized_es):
        """ Map loads to node labels

        Note:
        -----
        Altough tessif's :mod:`~tessif.frused.hooks` allow using it's
        :ref:`uid concept <Labeling_Concept>`, the component distinguish
        mechanisms only rely soley on native pypsa, to increase robustness.
        """
        # Use defaultdict of empty DataFrame as loads container:
        _loads = defaultdict(lambda: pd.DataFrame())

        es = optimized_es

        for ntype, tsf_comp in PypsaResultier.component_type_mapping.items():
            for name in getattr(es, ntype).index:
                if ntype in ['generators', 'storage_units']:

                    df = getattr(es, f"{ntype}_t")['p'][name].to_frame()
                    df.columns = [getattr(es, f"{ntype}")['bus'][name]]

                    if ntype == 'storage_units':
                        # pypsa link/transformer power is positive if it's
                        # withdrawing power from the bus, so the oppositve of
                        # tessif's convention
                        # (inflows < 0, outflows > 0, for all components)
                        inflows = df[df < 0].fillna(-0.)
                        outflows = df[df > 0].fillna(0.)

                        # a seperate column for in and outflow is created
                        # but only if it is NOT an excess sink emulating
                        # storage
                        if getattr(es, ntype).loc[name].type == "excess_sink":
                            df = inflows
                        else:
                            df = pd.concat([inflows, outflows], axis='columns')

                    # name the index column...
                    df.columns.name = name

                    # ... and override the 'snapshot' index name
                    df.index.name = None

                    _loads[name] = df
                if ntype == 'loads':
                    # incoming flows are < 0 by tessif's convention
                    df = -1 * getattr(es, "loads_t")['p'][name].to_frame()
                    df.columns = [es.loads['bus'][name]]

                    # name the index column...
                    df.columns.name = name

                    # ... and override the 'snapshot' index name
                    df.index.name = None

                    _loads[name] = df

                if ntype in ['links', 'transformers']:

                    # construct df out of the power flows from bus0
                    df = getattr(es, f"{ntype}_t")['p0'][name].to_frame()
                    # rename the column to bus0's name
                    bus0_name = getattr(es, f"{ntype}")['bus0'][name]
                    df.columns = [bus0_name]

                    # add all other bus columns
                    additional_bus_cols = [
                        col for col in getattr(
                            # replace all '' values with nan to drop them
                            es, f"{ntype}").loc[name].replace(
                                '', np.nan).dropna().index
                        if 'bus' in col and 'bus0' not in col]

                    for i, bus in enumerate(additional_bus_cols):

                        # add the column of busi
                        busi_name = getattr(es, f"{ntype}")[f"bus{i+1}"][name]
                        df[busi_name] = getattr(es, f"{ntype}_t")[
                            f"p{i+1}"][name]

                    # distinguish between links used as connectors and links
                    # used as transformers (for i.e chps)
                    if len(additional_bus_cols) > 1:
                        # multiple out or inputs means, the link is a
                        # transformer, usually a chp
                        df = df.multiply(-1)

                    #     # sito_transformer flag used but false
                    #     else:
                    #         # not a siso transformer but only 2 intefaces,
                    #         # means it is a connector.
                    #         # pypsa link/transformer power is positive if it's
                    #         # withdrawing power from the bus, so the oppositve
                    #         # of tessif's convention
                    #         # (inflows < 0, outflows > 0, for all components)
                    #         outflows = -1 * df[df < 0].fillna(-0.)
                    #         inflows = -1 * df[df > 0].fillna(0)

                    #         # a seperate column for in and outflow is created
                    #         df = pd.concat([inflows, outflows], axis='columns')

                    else:
                        if hasattr(es.links, 'siso_transformer'):
                            if bool(es.links.siso_transformer[name]):
                                # siso transformer.
                                # since pypsa's sign convention is the
                                # opposite of tessif's, it needs to be
                                # multiplied by -1
                                df = df.multiply(-1)
                            else:
                                # not a siso transformer but only 2 intefaces,
                                # means it is a connector.
                                # pypsa link/transformer power is positive if it's
                                # withdrawing power from the bus, so the oppositve
                                # of tessif's convention
                                # (inflows < 0, outflows > 0, for all components)
                                outflows = -1 * df[df < 0].fillna(-0.)
                                inflows = -1 * df[df > 0].fillna(0)

                                # a seperate column for in and outflow is created
                                df = pd.concat(
                                    [inflows, outflows], axis='columns')
                        else:
                            # not a siso transformer but only 2 intefaces,
                            # means it is a connector.
                            # pypsa link/transformer power is positive if it's
                            # withdrawing power from the bus, so the oppositve
                            # of tessif's convention
                            # (inflows < 0, outflows > 0, for all components)
                            outflows = -1 * df[df < 0].fillna(-0.)
                            inflows = -1 * df[df > 0].fillna(0)

                            # a seperate column for in and outflow is created
                            df = pd.concat([inflows, outflows], axis='columns')

                    # name the index column...
                    df.columns.name = name
                    # ... and override the 'snapshot' index name
                    df.index.name = None

                    _loads[name] = df

        # bus flows are not intrinsicly mapped by pypsa
        for name in getattr(es, 'buses').index:

            # compile a list of bus adjacent edges first
            bus_edges = list()
            for edge in self.edges:
                for e in edge:
                    if name == str(e):
                        bus_edges.append(
                            nts.Edge(edge[0], edge[1]))

            # use that edge to
            for edge in bus_edges:
                # access its nodes
                for node in edge:
                    # and filter out the node not beeing the bus
                    if str(node) != name:
                        # and set the respecive flow results times -1 because
                        # the perspective from outgoing is switching to
                        # incoming and vice versa

                        # take excess edges into account
                        if str(node) not in es.excess_sinks:
                            series = -1 * _loads[str(node)][name]
                        else:
                            link_name = "-".join([node, "Link"])
                            origin_bus_name = es.links.loc[link_name]["bus0"]
                            bus_name = "-".join([node, "Bus"])
                            series = -1 * _loads[str(node)][bus_name]
                            series = series.rename(origin_bus_name)

                        if isinstance(series, pd.Series):
                            series.name = str(node)
                            _loads[name][str(node)] = series
                        else:
                            if str(node) not in _loads[name].columns:
                                for label, col in series.iteritems():
                                    col.name = str(node)
                                    _loads[name] = pd.concat(
                                        [_loads[name], col], axis='columns')

            # name the index column
            _loads[name].columns.name = name

        # clean "ignore" artifacts
        for node in _loads.copy():
            if node not in self.nodes:
                _loads.pop(node)

        # rename the excess sink columns
        for node in es.excess_sinks:
            bus_name = "-".join([node, "Bus"])
            link_name = "-".join([node, "Link"])
            origin_bus_name = es.links.loc[link_name]["bus0"]
            _loads[node] = _loads[node].rename(
                columns={bus_name: origin_bus_name})

        return dict(_loads)


class CapacityResultier(base.CapacityResultier, LoadResultier):
    """Transforming installed capacity results dictionairies keyed by node.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    Raises
    ------
    NotImplementedError:
        Raised when postprocessing a Link that is supposed to have multiple
        in and outputs. Caus right now this doesn't seem possible.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.CapacityResultier>`.


    Examples
    --------
    1. Accessing the installed capacities and the characteristic values of the
       :attr:`Transshipment Problem
       <tessif.examples.data.ppsa.create_transshipment_problem>`

       (See
       :attr:`tessif.transform.es2mapping.base.CapacityResultier.node_installed_capacity`
       for more documentation):

        >>> # import post pypsa processing and example modules:
        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

        >>> # optimize the energy system:
        >>> pypsa_es = coded_pypsa_examples.create_transshipment_problem()

        >>> # post process the capacity results:
        >>> resultier = post_process_pypsa.CapacityResultier(pypsa_es)

        >>> # access the capacity results:
        >>> for node, capacity in resultier.node_installed_capacity.items():
        ...     print(f'{node}: {capacity}')
        bus-01: None
        bus-02: None
        source-01: 10.0
        source-02: 10.0
        connector-01->02: 10.0
        sink-01: 15.0
        sink-02: 15.0

        >>> # acces the characteristic value results:
        >>> for node, cv in resultier.node_characteristic_value.items():
        ...     if cv is not None:
        ...         cv = round(cv, 2)
        ...     print(f'{node}: {cv}')
        bus-01: None
        bus-02: None
        source-01: 1.0
        source-02: 0.67
        connector-01->02: 0.5
        sink-01: 0.56
        sink-02: 0.56


    2. Accessing the installed capacities and the characteristic value of the
       :attr:`Storage Example
       <tessif.examples.data.ppsa.create_storage_example>`

        >>> # import post pypsa processing and example modules:
        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

        >>> # optimize the energy system:
        >>> pypsa_es = coded_pypsa_examples.create_storage_example()

        >>> # post process the capacity results:
        >>> resultier = post_process_pypsa.CapacityResultier(pypsa_es)

        >>> # access the capacity results:
        >>> for node, capacity in resultier.node_installed_capacity.items():
        ...     print(f'{node}: {capacity}')
        Power Line: None
        Variable Source: 19.0
        Demand: 10.0
        Storage: 30.0

        >>> # acces the characteristic value results:
        >>> for node, cv in resultier.node_characteristic_value.items():
        ...     if cv is not None:
        ...         cv = round(cv, 2)
        ...     print(f'{node}: {cv}')
        Power Line: None
        Variable Source: 0.6
        Demand: 0.94
        Storage: 0.58

    3. Accessing the installed capacities and the characteristic value of the
       :attr:`Transformer
       <tessif.examples.data.ppsa.create_transformer_example>`

        >>> # import post pypsa processing and example modules:
        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

        >>> # optimize the energy system:
        >>> pypsa_es = coded_pypsa_examples.create_transformer_example()

        >>> # post process the capacity results:
        >>> resultier = post_process_pypsa.CapacityResultier(pypsa_es)

        >>> # access the capacity results:
        >>> for node, capacity in resultier.node_installed_capacity.items():
        ...     print(f'{node}: {capacity}')
        380kV: None
        110kV: None
        Source-380kV: 20.0
        Source-110kV: 20.0
        Demand-380kV: 10.0
        Demand-110kV: 10.0
        Transformer: 160.0

        >>> # acces the characteristic value results:
        >>> for node, cv in resultier.node_characteristic_value.items():
        ...     if cv is not None:
        ...         cv = round(cv, 2)
        ...     print(f'{node}: {cv}')
        380kV: None
        110kV: None
        Source-380kV: 0.5
        Source-110kV: 0.5
        Demand-380kV: 1.0
        Demand-110kV: 1.0
        Transformer: 0.06
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

        # clean excess sink / ignore artifact nodes
        for res_dict in [
                self._installed_capacities,
                self._original_capacities,
                self._expansion_costs,
                self._characteristic_values]:
            for node in res_dict.copy():
                if node not in self.nodes:
                    res_dict.pop(node)

    def _map_installed_capacities(self, optimized_es):

        inst_cap = dict()

        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                if ntype in ['generators', 'links', 'storage_units']:
                    capacity = getattr(optimized_es, ntype)['p_nom_opt'][name]

                    if ntype == 'storage_units':
                        factor = getattr(optimized_es, ntype)[
                            'max_hours'][name]
                    elif ntype == 'links':
                        # pypsa assumes max flow as p_nom_opt for links
                        # but in case of non-connector links
                        # max net output is considered to be the
                        # 'installed capacity'

                        # check for tessif hooked links:
                        if any(
                                [hasattr(optimized_es.links, attr)
                                 for attr in [
                                    'siso_transformer',
                                    'multiple_outputs',
                                    'multiple_inputs']
                                 ]
                        ):
                            factor = optimized_es.links['efficiency'][name]

                        # account for excess sinks added invisible links
                        if name in [nme + "-Link"
                                    for nme in optimized_es.excess_sinks]:
                            capacity = float("+inf")
                            factor = 1
                        # for multiple outputs, tessif calculates a capacity
                        # for each otput, assuming there is only 1 input
                        elif hasattr(optimized_es.links, 'multiple_outputs'):
                            if hasattr(optimized_es.links, 'multiple_inputs'):
                                if optimized_es.links['multiple_inputs'][name]:
                                    msg = (
                                        "Using multiple in and outputs in a " +
                                        "pyppsa Link is not supported, " +
                                        "cause it is not possible to decide " +
                                        "which pN is meant to be what."
                                    )
                                    raise NotImplementedError(msg)

                            # figure out all additional outputs (pN | N > 1)
                            # since pypsa has only 1 p_nom_opt attribute per
                            # link the others are tried to be inferred

                            additional_output_keys = [
                                key for key in optimized_es.links.keys()
                                if 'p_nom' in key and not any([c in key for c in [
                                    'min', 'max', 'extendable', 'opt']])]

                            # pop p_nom, since p_nom_opt can be used for that
                            if additional_output_keys:
                                additional_output_keys.pop(0)

                            # get the load results to check if capacity needs
                            # to be inferred
                            outflows = self.node_outflows[name]
                            # map bus uids to max output names (= capacity)
                            capacity_dict = dict()
                            for counter, result_key in enumerate(
                                    ['p_nom_opt', *additional_output_keys]):
                                # reverse load results because of tessif's and
                                # pypsa's different sign convention

                                outflow_node = optimized_es.links[
                                    f'bus{1+counter}'][name]

                                if outflow_node != '':
                                    # if link is extendable p_nom_opt will
                                    # refer to the highest flow occuring. In
                                    # case of chps, it refers to the inflow.
                                    # Therefor it needs to be multiplied with
                                    # the link efficiency
                                    extendable = optimized_es.links[
                                        'p_nom_extendable'][name]

                                    if extendable and counter == 0:
                                        factor = optimized_es.links[
                                            'efficiency'][name]
                                    else:
                                        # p_nom_opt only works for the first
                                        # flow
                                        # (in case of expansion, the second one
                                        # usually gets inferred)
                                        if counter == 0:
                                            factor = optimized_es.links[
                                                'efficiency'][name]
                                        else:
                                            factor = optimized_es.links[
                                                f'efficiency{counter+1}'][name]
                                        # factor = 1

                                    capacity = optimized_es.links[
                                        'p_nom_opt'][name] * factor

                                    if counter != 0:

                                        flows = outflows[outflow_node]
                                        if not flows.empty:
                                            inferred_capacity = max(flows)
                                        else:
                                            inferred_capacity = 0

                                        if inferred_capacity > capacity:
                                            capacity = inferred_capacity

                                    capacity_dict[outflow_node] = capacity

                            # make the dict a series, for prettier output in
                            # case there actually is more than 1 outflow node:
                            if len(capacity_dict) > 1:
                                capacity = pd.Series(capacity_dict)

                            factor = 1

                        else:
                            # check for time varying transformer-kind links:
                            if not optimized_es.links_t["efficiency"].empty:
                                if name in optimized_es.links_t["efficiency"].columns:
                                    factor = min(
                                        optimized_es.links_t["efficiency"][name])
                                else:
                                    factor = optimized_es.links[
                                        'efficiency'][name]
                            else:
                                factor = optimized_es.links[
                                    'efficiency'][name]

                    else:
                        factor = 1

                    inst_cap[name] = factor * capacity

                if ntype == 'transformers':
                    inst_cap[name] = getattr(
                        optimized_es, ntype)['s_nom_opt'][name]

                if ntype == 'buses':
                    inst_cap[name] = esn_defaults['variable_capacity']

                if ntype == 'loads':
                    # distinguish series and scalar results
                    cap = getattr(optimized_es, ntype)['p_set'][name]
                    if cap == 0.0:
                        # check if load present. Sometimes pypsa omits load if
                        # not used
                        if name in optimized_es.loads_t['p_set']:
                            inst_cap[name] = max(
                                getattr(optimized_es, 'loads_t')[
                                    'p_set'][name])
                        else:
                            inst_cap[name] = cap
                    else:
                        inst_cap[name] = cap

        return inst_cap

    def _map_original_capacities(self, optimized_es):
        """
        """
        inst_cap = dict()

        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                if ntype in ['generators', 'links', 'storage_units']:
                    capacity = getattr(optimized_es, ntype)['p_nom'][name]

                    if ntype == 'storage_units':
                        factor = getattr(optimized_es, ntype)[
                            'max_hours'][name]

                    elif ntype == 'links':
                        # pypsa assumes max flow as p_nom_opt for links
                        # but in case of non-connector links
                        # max net output is considered to be the
                        # 'installed capacity'
                        if any(
                                [hasattr(optimized_es.links, attr)
                                 for attr in [
                                    'siso_transformer',
                                    'multiple_outputs',
                                    'multiple_inputs']
                                 ]
                        ):
                            factor = optimized_es.links['efficiency'][name]

                        # for multiple outputs, tessif calculates a capacity
                        # for each otput, assuming there is only 1 input
                        if hasattr(optimized_es.links, 'multiple_outputs'):

                            # figure out all additional outputs (pN | N > 1)
                            additional_output_keys = [
                                key for key in optimized_es.links.keys()
                                if 'p_nom' in key and not any(
                                    [
                                        c in key for c in [
                                            'min', 'max',
                                            'extendable', 'opt'
                                        ]
                                    ]
                                )
                            ]

                            # pop p_nom, since p_nom_opt can be used for that
                            if additional_output_keys:
                                additional_output_keys.pop(0)

                            # map bus uids to max output names (= capacity)
                            capacity_dict = dict()
                            for counter, result_key in enumerate(
                                    ['p_nom', *additional_output_keys]):

                                outflow_node = optimized_es.links[
                                    f'bus{1+counter}'][name]

                                if outflow_node != '':
                                    # if link is extendable p_nom_opt will
                                    # refer to the highest flow occuring. In
                                    # case of chps refers to the inflow.
                                    # Therefor it needs to multiplied with the
                                    # link efficiency
                                    extendable = optimized_es.links[
                                        'p_nom_extendable'][name]

                                    if extendable:
                                        if counter == 0:
                                            factor = optimized_es.links[
                                                'efficiency'][name]
                                        else:
                                            factor = optimized_es.links[
                                                f'efficiency{counter+1}'][name]
                                    else:
                                        # p_nom_opt only works for the first
                                        # flow
                                        # (in case of expansion, the second one
                                        # usually gets inferred)

                                        # note: 2nd getting inferred probably
                                        # not true any more
                                        # if original cap is mapped like
                                        # expected needs to be observed
                                        factor = 1

                                    capacity = optimized_es.links[
                                        result_key][name] * factor

                                    capacity_dict[outflow_node] = capacity

                            # make the dict a series, for prettier output in
                            # case there actually is more than 1 outflow node:
                            if len(capacity_dict) > 1:
                                capacity = pd.Series(capacity_dict)
                            # else:
                            #     capacity = capacity
                            factor = 1

                    else:
                        factor = 1

                    inst_cap[name] = factor * capacity

                if ntype == 'transformers':
                    inst_cap[name] = getattr(
                        optimized_es, ntype)['s_nom'][name]

                if ntype in ['loads', 'buses']:
                    inst_cap[name] = self.node_installed_capacity[name]

        return inst_cap

    def _map_expansion_costs(self, optimized_es):
        expansion_costs = dict()

        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                if hasattr(getattr(optimized_es, ntype), 'capital_cost'):

                    costs = getattr(
                        optimized_es, ntype)['capital_cost'][name]

                    # account for multliple output links (chps mostly)
                    if ntype == 'links':
                        if hasattr(optimized_es.links, 'siso_transformer'):
                            costs = getattr(
                                optimized_es, ntype)['expansion_costs'][name]

                        if hasattr(optimized_es.links, 'multiple_outputs'):
                            if optimized_es.links['multiple_outputs'][name]:
                                additional_output_keys = [
                                    key for key in optimized_es.links.keys()
                                    if 'expansion_costs' in key]

                                if additional_output_keys:
                                    additional_output_keys.pop(0)

                                cost_dict = dict()

                                for counter, result_key in enumerate(
                                        ['expansion_costs', *additional_output_keys]):
                                    outflow_node = optimized_es.links[
                                        f'bus{1 + counter}'][name]
                                    if counter == 0:
                                        cost = optimized_es.links['expansion_costs'][name]
                                    else:
                                        cost = optimized_es.links[f'expansion_costs{counter+1}'][name]
                                    cost_dict[outflow_node] = cost
                                if len(cost_dict) > 1:
                                    costs = pd.Series(cost_dict)

                    if ntype == 'storage_unit':
                        costs = getattr(
                            optimized_es, ntype)['capital_cost'][name]
                        max_hours = getattr(
                            optimized_es, ntype)['max_hours'][name]

                        costs /= max_hours

                else:
                    costs = esn_defaults['expansion_costs']

                expansion_costs[name] = costs

        return expansion_costs

    def _map_characteristic_values(self, optimized_es):
        """Map node uid string representation to characteristic value."""

        summed_loads = self.node_summed_loads

        # Use default dict as capacity factors container:
        _characteristic_values = defaultdict(float)

        # Map the respective capacity factors:
        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                if not any([itype == getattr(
                            optimized_es, ntype).loc[name]["type"]
                            for itype in PypsaResultier.types_to_ignore]):

                    if ntype in ['generators', 'links', 'loads', 'transformers']:

                        inst_cap = self.node_installed_capacity[name]
                        if not isinstance(inst_cap, abc.Iterable):
                            if self.node_installed_capacity[name] != 0:
                                _characteristic_values[name] = (
                                    summed_loads[name].mean(axis='index') /
                                    inst_cap
                                )
                            else:
                                _characteristic_values[name] = 0.0

                    if ntype == 'links':
                        inst_cap = self.node_installed_capacity[name]
                        if isinstance(inst_cap, abc.Iterable):
                            # create series beforehand
                            series = (
                                self.node_outflows[name].mean() /
                                inst_cap
                            )
                            # to fill nan with 0
                            _characteristic_values[name] = series.fillna(0.0)

                    if ntype == 'buses':
                        _characteristic_values[name] = esn_defaults[
                            'characteristic_value']

                    if ntype == 'storage_units':
                        # account for unused storages:
                        if self.node_installed_capacity[name] == 0:
                            _characteristic_values[name] = 0
                        else:
                            _characteristic_values[name] = (
                                StorageResultier(optimized_es).node_soc[
                                    name].mean(axis='index') /
                                self.node_installed_capacity[name]
                            )

        return _characteristic_values


class StorageResultier(PypsaResultier, base.StorageResultier):
    r""" Transforming storage results into dictionairies keyed by node.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.StorageResultier>`.

    Examples
    --------
    1. Accessing the storage's soc inside the :attr:`Storage Example
       <tessif.examples.data.ppsa.create_storage_example>`

       (See
       :attr:`tessif.transform.es2mapping.base.StorageResultier.node_soc`
       for more documentation):

        >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> resultier = post_process_pypsa.StorageResultier(
        ...     coded_pypsa_examples.create_storage_example())
        >>> print(resultier.node_soc['Storage'])
        1990-07-13 00:00:00     9.0
        1990-07-13 01:00:00    18.0
        1990-07-13 02:00:00    30.0
        1990-07-13 03:00:00    20.0
        1990-07-13 04:00:00    10.0
        Freq: H, Name: Storage, dtype: float64
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_states_of_charge(self, optimized_es):
        """ Map storage labels to their states of charge"""

        _socs = dict()
        for name in getattr(optimized_es, 'storage_units').index:
            df = getattr(optimized_es, 'storage_units_t')[
                'state_of_charge'][name]

            _socs[name] = df

            # Override the pypsa "snapshot" index name
            _socs[name].index.name = None

        return _socs


class NodeCategorizer(PypsaResultier, base.NodeCategorizer):
    r""" Categorizing the nodes of an optimized pypsa energy system.

    Categorization utilizes :attr:`~tessif.frused.namedtuples.Uid`.

    Nodes are categorized by:

        - Energy :paramref:`sector <tessif.frused.namedtuples.Uid.sector>`
          ('power', 'heat', 'mobility', 'coupled')

        - :paramref:`Region <tessif.frused.namedtuples.Uid.region>`
          ('arbitrary label')

        - :paramref:`Coordinates <tessif.frused.namedtuples.Uid.latitude>`
          (latitude, longitude in degree)

        - Energy :paramref:`carrier <tessif.frused.namedtuples.Uid.carrier>`
          ('solar', 'wind', 'electricity', 'steam' ...)

        - :paramref:`Node type <tessif.frused.namedtuples.Uid.node_type>`
          ('arbitrary label')

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.NodeCategorizer>`.

    Examples
    --------

    Note
    ----
    Pypsa has no intrinsic way of utilizing :attr:`Uids
    <tessif.frused.namedtuples.Uid>` besides using its string representation as
    name. Therefor it is necessary to utilize tessif's :attr:`node uid styles
    <tessif.frused.namedtuples.node_uid_styles>` as demonstrated in the
    examples below, to reap the benefits of the :class:`NodeCategorizer`.

    For the uid representation technique to work you either have to construct
    the pypsa after changing the
    :attr:`~tessif.frused.configurations.node_uid_style`.


    0. Handle the imports of the following examples and simulate the
       energy system:

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> import pprint

    1. Display the energy system component's
       :paramref:`Coordinates <tessif.frused.namedtuples.Uid.latitude>`:

        >>> # change the uid style to use coordinates
        >>> configs.node_uid_style = 'coords'
        >>> resultier = post_process_pypsa.NodeCategorizer(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(resultier.node_coordinates)
        {'bus-01_53_10': Coordinates(latitude='53', longitude='10'),
         'bus-02_53_10': Coordinates(latitude='53', longitude='10'),
         'connector-01->02_53_10': Coordinates(latitude='53', longitude='10'),
         'sink-01_53_10': Coordinates(latitude='53', longitude='10'),
         'sink-02_53_10': Coordinates(latitude='53', longitude='10'),
         'source-01_53_10': Coordinates(latitude='53', longitude='10'),
         'source-02_53_10': Coordinates(latitude='53', longitude='10')}

    2. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.region`:

        >>> # change the uid style to use regions
        >>> configs.node_uid_style = 'region'
        >>> resultier = post_process_pypsa.NodeCategorizer(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(resultier.node_region_grouped)
        {'Germany': ['bus-01_Germany',
                     'bus-02_Germany',
                     'source-01_Germany',
                     'source-02_Germany',
                     'connector-01->02_Germany',
                     'sink-01_Germany',
                     'sink-02_Germany']}



    3. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.sector`

        >>> # change the uid style to use sectors
        >>> configs.node_uid_style = 'sector'
        >>> resultier = post_process_pypsa.NodeCategorizer(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(resultier.node_sector_grouped)
        {'Power': ['bus-01_Power',
                   'bus-02_Power',
                   'source-01_Power',
                   'source-02_Power',
                   'connector-01->02_Power',
                   'sink-01_Power',
                   'sink-02_Power']}


    4. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.node_type`:

        >>> # change the uid style to use node types
        >>> configs.node_uid_style = 'node_type'
        >>> resultier = post_process_pypsa.NodeCategorizer(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(resultier.node_type_grouped)
        {'AC-bus': ['bus-01_AC-Bus', 'bus-02_AC-Bus'],
         'AC-link': ['connector-01->02_AC-Link'],
         'AC-sink': ['sink-01_AC-Sink', 'sink-02_AC-Sink'],
         'AC-source': ['source-01_AC-Source', 'source-02_AC-Source']}


    5 Group energy system components by their energy
      :paramref:`~tessif.frused.namedtuples.Uid.carrier`:

        >>> # change the uid style to use the energy carrier
        >>> configs.node_uid_style = 'carrier'
        >>> resultier = post_process_pypsa.NodeCategorizer(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(resultier.node_carrier_grouped)
        {'Electricity': ['bus-01_Electricity',
                         'bus-02_Electricity',
                         'source-01_Electricity',
                         'source-02_Electricity',
                         'connector-01->02_Electricity',
                         'sink-01_Electricity',
                         'sink-02_Electricity']}



    6. Map the `node uid representation <Labeling_Concept>` of each component
       of the energy system to their energy
       :paramref:`~tessif.frused.namedtuples.Uid.carrier`:

        >>> # change the uid style to use the energy carrier
        >>> configs.node_uid_style = 'carrier'
        >>> resultier = post_process_pypsa.NodeCategorizer(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(resultier.node_energy_carriers)
        {'bus-01_Electricity': 'Electricity',
         'bus-02_Electricity': 'Electricity',
         'connector-01->02_Electricity': 'Electricity',
         'sink-01_Electricity': 'Electricity',
         'sink-02_Electricity': 'Electricity',
         'source-01_Electricity': 'Electricity',
         'source-02_Electricity': 'Electricity'}


        >>> # reset the uid style
        >>> configs.node_uid_style = 'name'

    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)


class FlowResultier(base.FlowResultier, LoadResultier):
    """
    Transforming flow results into dictionairies keyed by edges.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.FlowResultier>`.

    Examples
    --------

    0. Handle the imports of the following examples:

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

    1. Display the net energy flows of a small energy system:

        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> for edge, net_flow in resultier.edge_net_energy_flow.items():
        ...     print(f"{edge.source}->{edge.target}:", net_flow)
        connector-01->02->bus-01: 5.0
        source-01->bus-01: 30.0
        connector-01->02->bus-02: 10.0
        source-02->bus-02: 20.0
        bus-01->connector-01->02: 10.0
        bus-02->connector-01->02: 5.0
        bus-01->sink-01: 25.0
        bus-02->sink-02: 25.0

    2. Display the total costs incurred:

        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> for edge, tcosts in resultier.edge_total_costs_incurred.items():
        ...     print(f"{edge.source}->{edge.target}:", tcosts)
        source-01->bus-01: 27.0
        source-02->bus-02: 22.0
        bus-01->connector-01->02: 0.0
        connector-01->02->bus-01: 0.0
        connector-01->02->bus-02: 0.0
        bus-02->connector-01->02: 0.0
        bus-01->sink-01: 0.0
        bus-02->sink-02: 0.0

    3. Display the total emissions caused:

        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> for edge, tems in resultier.edge_total_emissions_caused.items():
        ...     print(f"{edge.source}->{edge.target}:", tems)
        source-01->bus-01: 0.0
        source-02->bus-02: 0.0
        bus-01->connector-01->02: 0.0
        connector-01->02->bus-01: 0.0
        connector-01->02->bus-02: 0.0
        bus-02->connector-01->02: 0.0
        bus-01->sink-01: 0.0
        bus-02->sink-02: 0.0

    4. Display the specific flow costs of several small energy systems:

        >>> # transshipment using links:
        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> for edge, flow_costs in resultier.edge_specific_flow_costs.items():
        ...     print(f"{edge.source}->{edge.target}:", flow_costs)
        source-01->bus-01: 0.9
        source-02->bus-02: 1.1
        bus-01->connector-01->02: 0.0
        connector-01->02->bus-01: 0.0
        connector-01->02->bus-02: 0.0
        bus-02->connector-01->02: 0.0
        bus-01->sink-01: 0.0
        bus-02->sink-02: 0.0

        >>> # Postprocessing storage costs:
        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_storage_example())
        >>> for edge, flow_costs in resultier.edge_specific_flow_costs.items():
        ...     print(f"{edge.source}->{edge.target}:", flow_costs)
        Variable Source->Power Line: 2.0
        Storage->Power Line: 1.0
        Power Line->Demand: 0.0
        Power Line->Storage: 0.0


    5. Display the specific emission of several small energy systems:

        >>> # Energy system allocating carriers and emission:
        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.emission_objective())
        >>> for edge, emissions in resultier.edge_specific_emissions.items():
        ...     print(f"{edge.source}->{edge.target}:", emissions)
        Power Line->Demand: 0.0
        Renewable->Power Line: 0.0
        Gas Generator->Power Line: 0.0

        >>> # Energy system not allocating carriers and emissions:
        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_storage_example())
        >>> for edge, emissions in resultier.edge_specific_emissions.items():
        ...     print(f"{edge.source}->{edge.target}:", emissions)
        Power Line->Demand: 0.0
        Power Line->Storage: 0.0
        Variable Source->Power Line: 0.0
        Storage->Power Line: 0.0


    6. Show the caluclated edge weights of a small energy systems:

        >>> # using the storage example one more time
        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.create_storage_example())
        >>> for edge, weight in resultier.edge_weight.items():
        ...     print(f"{edge.source}->{edge.target}:", weight)
        Variable Source->Power Line: 1.0
        Storage->Power Line: 0.5
        Power Line->Demand: 0.1
        Power Line->Storage: 0.1

    7. Access the reference emissions and net energy flow:

        >>> resultier = post_process_pypsa.FlowResultier(
        ...     pypsa_examples.emission_objective())

        >>> print(resultier.edge_reference_emissions)
        1

        >>> print(resultier.edge_reference_net_energy_flow)
        40.0
    """

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_specific_flow_costs(self, optimized_es):
        r"""Eenergy specific flow costs mapped to edges."""

        # Use default dict as net energy flows container:
        _specific_flow_costs = defaultdict(float)
        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:
                if ntype in ['generators', 'storage_units']:
                    costs = getattr(optimized_es, ntype)['marginal_cost'][name]
                    factor = 1

                    for outflow in self.outbounds[name]:
                        # beware: pypsa bidirectional links respect costs as
                        # negative when flow exists from bus02 -> bus01
                        _specific_flow_costs[
                            nts.Edge(name, outflow)] = costs * factor

                if ntype == 'links':
                    if any(
                        [hasattr(optimized_es.links, attr) for attr in [
                            'siso_transformer',
                            'multiple_outputs',
                            'multiple_inputs']
                         ]
                    ):
                        # pure pysa link costs are set before evaluating
                        # efficiency
                        additional_bus_cols = [
                            col for col in optimized_es.links.columns
                            if 'bus' in col and 'bus0' not in col]

                        for counter, bus in enumerate(additional_bus_cols):
                            edge = nts.Edge(
                                name, optimized_es.links[bus][name])
                            if counter == 0:
                                eta = optimized_es.links['efficiency'][name]
                                if hasattr(optimized_es.links, 'flow_costs'):
                                    costs = optimized_es.links[
                                        'flow_costs'][name]
                                else:
                                    msg = (
                                        "Costs for transformer like link " +
                                        f"{name} were not specified using " +
                                        "tessif's hooks. Costs are not "
                                        "distributed among flows correctly!"
                                    )
                                    logger.warning(msg)
                                    costs = optimized_es.links[
                                        'marginal_cost'][name]
                            else:
                                eta = optimized_es.links[f'efficiency{counter+1}'][name]
                                if hasattr(optimized_es.links, 'flow_costs'):
                                    costs = optimized_es.links[
                                        f'flow_costs{counter+1}'][name]
                                else:
                                    msg = (
                                        "Costs for transformer like link " +
                                        f"{name} were not specified using " +
                                        "tessif's hooks. Costs are not "
                                        "distributed among flows correctly!"
                                    )
                                    logger.warning(msg)
                                    costs = optimized_es.links[
                                        'marginal_cost'][name]

                            _specific_flow_costs[edge] = costs

        # # check for bidirectional flows and add respective costs
        # for edge, cost in _specific_flow_costs.copy().items():
        #     reversed_edge = nts.Edge(
        #         edge.target,
        #         edge.source)
        #     if reversed_edge in self.edges:
        #         if reversed_edge not in _specific_flow_costs:
        #             _specific_flow_costs[reversed_edge] = cost
        #         elif cost != 0 and _specific_flow_costs[reversed_edge] == 0:
        #             _specific_flow_costs[reversed_edge] = cost

        # set all other flows costs according to global defaults
        for edge in self.edges:
            if edge not in _specific_flow_costs.keys():
                if edge.target in optimized_es.excess_sinks:
                    _specific_flow_costs[edge] = getattr(
                        optimized_es, "storage_units").loc[
                            edge.target].marginal_cost
                else:
                    _specific_flow_costs[edge] = esn_defaults['flow_costs']

        # clean ignore artifacts:
        for edge in _specific_flow_costs.copy():
            if edge not in self.edges:
                _specific_flow_costs.pop(edge)

        return dict(_specific_flow_costs)

    def _map_specific_emissions(self, optimized_es):
        r"""Eenergy specific emissions mapped to edges.
        PyPSA attributes emissions relative to primary energy input.
        """

        # Use default dict as net energy flows container:
        _specific_emissions = defaultdict(float)

        for ntype in PypsaResultier.component_type_mapping:
            for name in getattr(optimized_es, ntype).index:

                if hasattr(getattr(optimized_es, ntype), 'flow_emissions'):

                    # pure pysa link costs are set before evaluating
                    # efficiency
                    additional_bus_cols = [
                        col for col in getattr(
                            # replace all '' values with nan to drop them
                            optimized_es, f"{ntype}").loc[name].replace(
                                '', np.nan).dropna().index
                        if 'bus' in col and 'bus0' not in col]

                    for counter, bus in enumerate(additional_bus_cols):
                        edge = nts.Edge(
                            name,
                            getattr(optimized_es, ntype)[bus][name]
                        )

                        if counter == 0:
                            emissions = getattr(optimized_es, ntype)[
                                'flow_emissions'][name]

                        else:
                            emissions = getattr(optimized_es, ntype)[
                                f'flow_emissions{counter+1}'][name]

                        _specific_emissions[edge] = emissions

                else:
                    msg = (
                        f"Component of name '{name}' does not have a flow " +
                        "bound emisison value attribute.\n" +
                        "Falling back on default value: " +
                        f"'{esn_defaults['emissions']}'."
                    )
                    logger.debug(msg)

                    for outflow in self.outbounds[name]:
                        _specific_emissions[nts.Edge(
                            name, outflow)] = esn_defaults['emissions']

        # # check for bidirectional flows and add respective emissions
        # for edge, emission in _specific_emissions.copy().items():
        #     reversed_edge = nts.Edge(
        #         edge.target,
        #         edge.source)
        #     if reversed_edge in self.edges:
        #         if reversed_edge not in _specific_emissions:
        #             _specific_emissions[reversed_edge] = emission
        #         elif emission > 0 and _specific_emissions[reversed_edge] == 0:
        #             _specific_emissions[reversed_edge] = emission

        # set all other emisisons according to global defaults
        # set all other flows costs according to global defaults
        for edge in self.edges:
            if edge not in _specific_emissions.keys():
                if edge.target in optimized_es.excess_sinks:
                    _specific_emissions[edge] = getattr(
                        optimized_es, "storage_units").loc[
                            edge.target].marginal_cost
                else:
                    _specific_emissions[edge] = esn_defaults['emissions']

        # clean ignore artifacts:
        for edge in _specific_emissions.copy():
            if edge not in self.edges:
                _specific_emissions.pop(edge)

        return dict(_specific_emissions)


class AllResultier(CapacityResultier, FlowResultier, StorageResultier,
                   ScaleResultier):
    r"""
    Transform energy system results into a dictionary keyed by attribute.

    Incorporates all the functionalities from its bases.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    Note
    ----
    This class allows interfacing with **ALL** framework processing utilities.
    It extracts every bit of info the author ever needed in his postprocessing.

    It is meant to be a "one fits all" solution for small energy systems.
    Perfectly fit for showing "proof of concepts" or debugging energy system
    components.

    **Not** meant to be used with **large energy systems**.

    Examples
    --------

    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)


class LabelFormatier(base.LabelFormatier, FlowResultier, CapacityResultier):
    r"""
    Generate component summaries as multiline label dictionairy entries.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.LabelFormatier>`.

    Examples
    --------

    0. Handle the imports of the following examples and simulate the
       energy system:

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

    1. Compile and display a node's summary:

    >>> formatier = post_process_pypsa.LabelFormatier(
    ...     pypsa_examples.create_storage_example())
    >>> for node, label in formatier.node_summaries.items():
    ...     print(node, label)
    Power Line {'Power Line': 'Power Line\n var'}
    Variable Source {'Variable Source': 'Variable Source\n19 MW\ncf: 0.6'}
    Demand {'Demand': 'Demand\n10 MW\ncf: 0.9'}
    Storage {'Storage': 'Storage\n30 MWh\ncv: 0.6'}


    2. Compile and display an edge's summary:

    >>> print(formatier.edge_summaries[('Variable Source', 'Power Line')])
    {('Variable Source', 'Power Line'): '57 MWh\n2.0 €/MWh\n0.0 t/MWh'}

    """

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es, **kwargs)


class NodeFormatier(base.NodeFormatier, CapacityResultier):
    r"""Transforming energy system results into node visuals.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrer', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionairy.

    drawutil: str, default='nx'
        Which drawuing utility backend to format node size, fil_size and
        shape to. ``'dc'`` for :mod:`plotly-dash-cytoscape
        <tessif.visualize.dcgrph>` or ``'nx'`` for
        :mod:`networkx-matplotlib <tessif.visualize.nxgrph>`.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.NodeFormatier>`.

    Examples
    --------

    0. Handle the imports of the following examples and simulate the
       energy system:

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> import pprint

    1. Generate and display a small energy system's node shape mapping:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(formatier.node_shape)
        {'bus-01': 'o',
         'bus-02': 'o',
         'connector-01->02': 'o',
         'sink-01': '8',
         'sink-02': '8',
         'source-01': '8',
         'source-02': '8'}

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_storage_example())
        >>> pprint.pprint(formatier.node_shape)
        {'Demand': '8', 'Power Line': 'o', 'Storage': 's', 'Variable Source': '8'}

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready shapes:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_transshipment_problem(),
        ...     drawutil="dc")
        >>> pprint.pprint(formatier.node_shape)
        {'bus-01': 'ellipse',
         'bus-02': 'ellipse',
         'connector-01->02': 'rectangle',
         'sink-01': 'ellipse',
         'sink-02': 'ellipse',
         'source-01': 'round-octagon',
         'source-02': 'round-octagon'}


        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_storage_example(),
        ...     drawutil="dc")
        >>> pprint.pprint(formatier.node_shape)
        {'Demand': 'ellipse',
         'Power Line': 'ellipse',
         'Storage': 'round-hexagon',
         'Variable Source': 'round-octagon'}

    2. Generate and display a small energy system's node size mapping:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(formatier.node_size)
        {'bus-01': 'variable',
         'bus-02': 'variable',
         'connector-01->02': 2000,
         'sink-01': 3000,
         'sink-02': 3000,
         'source-01': 2000,
         'source-02': 2000}

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_storage_example())
        >>> pprint.pprint(formatier.node_size)
        {'Demand': 1000,
         'Power Line': 'variable',
         'Storage': 3000,
         'Variable Source': 1900}

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready sizes scaled
        to a different default node size:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_transshipment_problem(),
        ...     drawutil="dc")
        >>> pprint.pprint(formatier.node_size)
        {'bus-01': 'variable',
         'bus-02': 'variable',
         'connector-01->02': 60,
         'sink-01': 90,
         'sink-02': 90,
         'source-01': 60,
         'source-02': 60}

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_storage_example(),
        ...     drawutil="dc")
        >>> pprint.pprint(formatier.node_size)
        {'Demand': 30, 'Power Line': 'variable', 'Storage': 90, 'Variable Source': 57}

    3. Generate and display a small energy system's node fill size mapping:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> for node, fill_size in formatier.node_fill_size.items():
        ...     if fill_size is not None:
        ...         fill_size = round(fill_size, 2)
        ...     print(node, fill_size)
        bus-01 None
        bus-02 None
        source-01 2000.0
        source-02 1333.0
        connector-01->02 1000.0
        sink-01 1667.0
        sink-02 1667.0

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready sizes scaled
        to a different default node size:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_transshipment_problem(),
        ...     drawutil="dc")
        >>> for node, fill_size in formatier.node_fill_size.items():
        ...     if fill_size is not None:
        ...         fill_size = round(fill_size, 2)
        ...     print(node, fill_size)
        bus-01 None
        bus-02 None
        source-01 60.0
        source-02 40.0
        connector-01->02 30.0
        sink-01 50.0
        sink-02 50.0

    4. Generate and display a small energy system's node color mapping basd on
       the grouping:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_storage_example())
        >>> pprint.pprint(formatier.node_color)
        {'Demand': '#330099',
         'Power Line': '#ffcc00',
         'Storage': '#ff0099',
         'Variable Source': '#9999ff'}

    6. Generate and display a small energy system's node color map (colors
       that are cycled through for each component type) mapping basd on the
       grouping:

        >>> formatier = post_process_pypsa.NodeFormatier(
        ...     pypsa_examples.create_storage_example(), cgrp='all')
        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.name.items()})
        {'Demand': <class 'str'>,
         'Power Line': <class 'str'>,
         'Storage': <class 'str'>,
         'Variable Source': <class 'str'>}


        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.carrier.items()})
        {'Demand': <class 'str'>,
         'Power Line': <class 'str'>,
         'Storage': <class 'str'>,
         'Variable Source': <class 'str'>}

        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.sector.items()})
        {'Demand': <class 'str'>,
         'Power Line': <class 'str'>,
         'Storage': <class 'str'>,
         'Variable Source': <class 'str'>}

        (Hint for devs: Which color string is mapped depends on order of
        mapping. Therefore only the type is printed and not its string value
        since it may differ from doctest to doctest.)

    """

    def __init__(self, optimized_es, cgrp='name', drawutil='nx', **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            cgrp=cgrp,
            drawutil=drawutil,
            **kwargs)


class MplLegendFormatier(base.MplLegendFormatier, CapacityResultier):
    r"""
    Generating visually enhanced matplotlib legends for nodes and edges.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrer', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionairy.

    markers: str, default='formatier'
        What marker to use for legend entries. Either ``'formatier'`` or
        one of the :any:`matplotlib.markers`.

        If ``'formatier'`` is used, markers will be inferred from
        :attr:`NodeFormatier.node_shape`.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.MplLegendFormatier>`.

    Examples
    --------

    0. Handle the imports of the following examples and simulate the
       energy system:

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> import pprint

    1. Generate and display name grouped legend labels of a small energy
       system:

        >>> formatier = post_process_pypsa.MplLegendFormatier(
        ...     pypsa_examples.create_mwe(), cgrp='all')
        >>> pprint.pprint(formatier.node_legend.name['legend_labels'])
        ['Demand', 'Gas Generator', 'Power Line', 'Renewable']


    2. Generate and display matplotlib legend attributes to describe
       :paramref:`fency node styles
       <tessif.visualize.nxgrph.draw_nodes.draw_fency_nodes>`. Fency as in:

            - variable node size being outer fading circles
            - cycle filling being proportional capacity factors
            - outer diameter being proportional installed capacities

        >>> formatier = post_process_pypsa.MplLegendFormatier(
        ...     pypsa_examples.create_mwe(), cgrp='all')
        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_style_legend.items()})
        {'legend_bbox_to_anchor': <class 'tuple'>,
         'legend_borderaxespad': <class 'int'>,
         'legend_handles': <class 'list'>,
         'legend_labels': <class 'list'>,
         'legend_labelspacing': <class 'int'>,
         'legend_loc': <class 'str'>,
         'legend_title': <class 'str'>}

    """

    def __init__(self, optimized_es, cgrp='all',
                 markers='formatier', **kwargs):

        # mpl legend formatier is the only class needing an extra formatier
        # instead of just inheriting it. This allows bundeling as done in the
        # AllFormatier with its specific color group (cgrp) and still be able
        # to map the legends for all colors

        # a different plausible approach would be to only map the bundled
        # color, and implement some if clauses to only map the legend
        # requested. This also implies chaning the bahaviour of
        # MplLegendFormatier.node_legend
        self._nformats = NodeFormatier(
            optimized_es, cgrp='all', drawutil='nx')

        super().__init__(optimized_es=optimized_es, cgrp='all',
                         markers=markers, **kwargs)


class EdgeFormatier(base.EdgeFormatier, FlowResultier):
    r"""Transforming energy system results into edge visuals.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    drawutil: str, default='nx'
        Which drawuing utility backend to format node size, fil_size and
        shape to. ``'dc'`` for :mod:`plotly-dash-cytoscape
        <tessif.visualize.dcgrph>` or ``'nx'`` for
        :mod:`networkx-matplotlib <tessif.visualize.nxgrph>`.

    cls: tuple, default=None
        2-Tuple / :attr:`CLS namedtuple <tessif.frused.namedtuples.CLS>`
        defining the relative flow cost thresholds and the respective style
        specifications. Used to map specific flow costs to edge line style
        representations.

        If  ``None``, default implementation is used based on
        :paramref:`~EdgeFormatier.drawutil`.

        For ``drawutil='nx'``
        `Networkx-Matplotlib
        <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_linestyle>`_::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        For ``drawutil='dc'``
        `Dash-Cytoscape <https://js.cytoscape.org/#style/edge-line>`_ styles
        are used::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        Translating to all edges of relative specific flows costs, between
        ``0`` and ``.33`` are correlated to have a ``':'``/``'dotted'``
        linestyle.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.EdgeFormatier>`.

    Examples
    --------

    0. Handle the imports:

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_examples
        >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
        >>> import pprint

    1. Generate and display a small energy system's edge widths:

        >>> formatier = post_process_pypsa.EdgeFormatier(
        ...     pypsa_examples.create_transshipment_problem())
        >>> pprint.pprint(list(sorted(formatier.edge_width.items())))
        [(Edge(source='bus-01', target='connector-01->02'), 0.33),
         (Edge(source='bus-01', target='sink-01'), 0.83),
         (Edge(source='bus-02', target='connector-01->02'), 0.17),
         (Edge(source='bus-02', target='sink-02'), 0.83),
         (Edge(source='connector-01->02', target='bus-01'), 0.17),
         (Edge(source='connector-01->02', target='bus-02'), 0.33),
         (Edge(source='source-01', target='bus-01'), 1.0),
         (Edge(source='source-02', target='bus-02'), 0.67)]

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready widths,
        scaled to a different default edge width:

        >>> formatier = post_process_pypsa.EdgeFormatier(
        ...     pypsa_examples.create_transshipment_problem(),
        ...     drawutil='dc')
        >>> pprint.pprint(list(sorted(formatier.edge_width.items())))
        [(Edge(source='bus-01', target='connector-01->02'), 2.33),
         (Edge(source='bus-01', target='sink-01'), 5.83),
         (Edge(source='bus-02', target='connector-01->02'), 1.17),
         (Edge(source='bus-02', target='sink-02'), 5.83),
         (Edge(source='connector-01->02', target='bus-01'), 1.17),
         (Edge(source='connector-01->02', target='bus-02'), 2.33),
         (Edge(source='source-01', target='bus-01'), 7.0),
         (Edge(source='source-02', target='bus-02'), 4.67)]

    2. Generate and display a small energy system's edge colors:

        >>> formatier = post_process_pypsa.EdgeFormatier(
        ...     pypsa_examples.create_mwe())
        >>> pprint.pprint(list(sorted(formatier.edge_color.items())))
        [(Edge(source='Gas Generator', target='Power Line'), [0.15]),
         (Edge(source='Power Line', target='Demand'), [0.15]),
         (Edge(source='Renewable', target='Power Line'), [0.15])]

        (:func:`~networkx.drawing.nx_pylab.draw_networkx_edges` expects
        iterable of floats when using a colormap)

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready colors,
        directly scaling the relativ specific emissions to a hex-color value.

        >>> formatier = post_process_pypsa.EdgeFormatier(
        ...     pypsa_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(list(sorted(formatier.edge_color.items())))
        [(Edge(source='Gas Generator', target='Power Line'), '#d8d8d8'),
         (Edge(source='Power Line', target='Demand'), '#d8d8d8'),
         (Edge(source='Renewable', target='Power Line'), '#d8d8d8')]

    3. Generate and display a small energy system's edge line styles:

        >>> formatier = post_process_pypsa.EdgeFormatier(
        ...     pypsa_examples.create_mwe())
        >>> pprint.pprint(list(sorted(formatier.edge_linestyle.items())))
        [(Edge(source='Gas Generator', target='Power Line'), '-'),
         (Edge(source='Power Line', target='Demand'), ':'),
         (Edge(source='Renewable', target='Power Line'), '-')]


        Compare these to the :mod:`~tessif.visualize.dcgrph` ready styles,
        using different specifiers:

        >>> formatier = post_process_pypsa.EdgeFormatier(
        ...     pypsa_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(list(sorted(formatier.edge_linestyle.items())))
        [(Edge(source='Gas Generator', target='Power Line'), 'solid'),
         (Edge(source='Power Line', target='Demand'), 'dotted'),
         (Edge(source='Renewable', target='Power Line'), 'solid')]
    """

    def __init__(self, optimized_es, drawutil='nx', cls=None, **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            drawutil=drawutil,
            cls=cls,
            **kwargs)


class AllFormatier(
        LabelFormatier, NodeFormatier, MplLegendFormatier, EdgeFormatier):
    r"""
    Transforming ES results into visual expression dicts keyed by attribute.
    Incorperates all the functionalities from its
    parents.

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrer', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionairy.

        Used by :class:`NodeFormatier` and :class:`MplLegendFormatier`

    markers: str, default='formatier'
        What marker to use for legend entries. Either ``'formatier'`` or
        one of the :any:`matplotlib.markers`.

        If ``'formatier'`` is used, markers will be inferred from
        :attr:`NodeFormatier.node_shape`.

        Used by :class:`MplLegendFormatier`

    drawutil: str, default='nx'
        Which drawuing utility backend to format node size, fil_size and
        shape to. ``'dc'`` for :mod:`plotly-dash-cytoscape
        <tessif.visualize.dcgrph>` or ``'nx'`` for
        :mod:`networkx-matplotlib <tessif.visualize.nxgrph>`.

    cls: tuple, default=None
        2-Tuple / :attr:`CLS namedtuple <tessif.frused.namedtuples.CLS>`
        defining the relative flow cost thresholds and the respective style
        specifications. Used to map specific flow costs to edge line style
        representations.

        If  ``None``, default implementation is used based on
        :paramref:`~EdgeFormatier.drawutil`.

        For ``drawutil='nx'``
        `Networkx-Matplotlib
        <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_linestyle>`_::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        For ``drawutil='dc'``
        `Dash-Cytoscape <https://js.cytoscape.org/#style/edge-line>`_ styles
        are used::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        Translating to all edges of relative specific flows costs, between
        ``0`` and ``.33`` are correlated to have a ``':'``/``'dotted'``
        linestyle.

    Note
    ----
    This class allows interfacing with **ALL** framework processing utilities.
    It extracts every bit of info the author ever needed in his postprocessing.

    It is meant to be a "one fits all" solution for small energy systems.
    Perfectly fit for showing "proof of concepts" or debugging energy system
    components.

    **Not** meant to be used with **large energy systems**.
    """

    def __init__(self, optimized_es, cgrp='all',
                 markers='formatier',
                 drawutil='nx',
                 cls=None,
                 **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            cgrp=cgrp, markers=markers, drawutil=drawutil, **kwargs)

        # initializing edge formatier seperately, because of differing
        # init signature causing a wierd unrespecting of drawutl
        super(EdgeFormatier, self).__init__(
            optimized_es=optimized_es,
            drawutil=drawutil,
            cls=cls,
            **kwargs)


class ICRHybridier(PypsaResultier, base.ICRHybridier):
    """
    Aggregate numerical and visual information for visualizing
    the :ref:`Integrated_Component_Results` (ICR).

    Parameters
    ----------
    optimized_es: :class:`~pypsa.Network`
        An optimized pypsa network.

    See also
    --------
    For non :ref:`model <SupportedModels>` specific attributes see
    the respective :class:`base class
    <tessif.transform.es2mapping.base.ICRHybridier>`.
    """

    def __init__(self, optimized_es, colored_by='name', **kwargs):
        base.ICRHybridier.__init__(
            self,
            optimized_es=optimized_es,
            node_formatier=NodeFormatier(optimized_es, cgrp=colored_by),
            edge_formatier=EdgeFormatier(optimized_es),
            mpl_legend_formatier=MplLegendFormatier(optimized_es),
            **kwargs)

    @ property
    def node_characteristic_value(self):
        r"""Characteristic values of the energy system components mapped to
        their :ref:`node uid representation <Labeling_Concept>`.

        Components of variable size or have a characteristic value as stated in
        :attr:`tessif.frused.defaults.energy_system_nodes`.

        Characteristic value in this context means:

            - :math:`cv = \frac{\text{characteristic flow}}
              {\text{installed capacity}}` for:

                - :class:`~tessif.model.components.Source` objects (
                  `generator
                  <https://pypsa.readthedocs.io/en/stable/components.html#generator>`__
                  in pypsa)

                - :class:`~tessif.model.components.Sink` objects (
                  `load
                  <https://pypsa.readthedocs.io/en/stable/components.html#load>`_
                  in pypsa)
                - :class:`~tessif.model.components.Transformer` objects (
                  `generator
                  <https://pypsa.readthedocs.io/en/stable/components.html#generator>`__
                  in pypsa)
                - :class:`~tessif.model.components.Connector` objects (
                  `link
                  <https://pypsa.readthedocs.io/en/stable/components.html#link>`_
                  or `transformer
                  <https://pypsa.readthedocs.io/en/stable/components.html#transformer>`_
                  in pypsa)

            - :math:`cv = \frac{\text{mean}\left(\text{SOC}\right)}
              {\text{capacity}}` for:

                - :class:`~tessif.model.components.Storage` (
                  `generator
                  <https://pypsa.readthedocs.io/en/stable/components.html#storage-unit>`_
                  in pypsa)


        Characteristic flow in this context means:

            - ``mean(`` :attr:`LoadResultier.node_summed_loads
              <tessif.transform.es2mapping.base.LoadResultier.node_summed_loads>`
              ``)``

                - :class:`~tessif.model.components.Source` objects
                - :class:`~tessif.model.components.Sink` objects

            - ``mean(0th outflow)`` for:

                - :class:`~tessif.model.components.Transformer` objects

        The **node fillsize** of :ref:`integrated component results graphs
        <Integrated_Component_Results>` scales with the
        **characteristic value**.
        If no capacity is defined (i.e for nodes of variable size, like busses
        or excess sources and sinks, node size is set to it's default (
        :attr:`nxgrph_visualize_defaults[node_fill_size]
        <tessif.frused.defaults.nxgrph_visualize_defaults>`).
        """
        return self._caps.node_characteristic_value
