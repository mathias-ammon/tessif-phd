# tessif/transform/es2mapping/cllp.py
"""
:mod:`~tessif.transform.es2mapping.cllp` is a :mod:`tessif` module holding
:class:`~calliope.core.model.Model` transformer classes for
postprocessing results and providing a tessif uniform interface.
"""
from collections import defaultdict, abc
import logging

import pandas as pd

from tessif.frused import namedtuples as nts

from tessif.frused.defaults import energy_system_nodes as esn_defaults

import tessif.transform.es2mapping.base as base
import tessif.write.log as log


logger = logging.getLogger(__name__)


class CalliopeResultier(base.Resultier):
    """ Transform nodes and edges into their name representation. Child of
    :class:`~tessif.transform.es2mapping.base.Resultier` and mother of all
    calliope Resultiers.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    Note
    ----
    Calliope does not support Tessif's UID notation.
    To get as much as possible information the UID is stored as one string with
    separation via dot in the technology names. Sine Busses and Connectors are
    only calliope locations and no technologies they dont have a name parameter
    and thus do not have all UID information..

    """

    component_type_mapping = {
        'storage': 'storage',
        'conversion': 'transformer',
        'conversion_plus': 'transformer',
        'demand': 'sink',
        'supply': 'source',
        'nan': 'bus',  # not needed for calliope v.0.6.6 but for future update to v.0.6.8
        'transmission': 'connector'
        # not every transmission is linked to a connector
        # but the specific choosing will be done at other points
    }

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_nodes(self, optimized_es):
        r"""Return string representation of node labels as :class:`list`"""
        # Note: tessif uid doesnt get fully into the calliope model

        nodes = list()

        # each technology (tessif component) has it's own location
        for node in optimized_es.inputs.locs:
            if 'location' in str(node.data):
                # every technology has its own location with name that adds "location"
                # after tech name. To get rid of these we pass them.
                name = str(node.data).split(" location", 1)[0]
                nodes.append(name)
            elif 'reverse' in str(node.data):
                # Connectors are build using two separate locations.
                # One of them with the suffix 'reverse' which does not
                # need to be added as extra node here
                pass
            else:
                name = str(node.data)
                nodes.append(name)

        for count, node in enumerate(nodes):
            if node in optimized_es.inputs.names.techs.data:
                nodes[count] = str(optimized_es.inputs.names.loc[{'techs': f'{node}'}].data).split('.')[0]

        nodes.sort()  # to avoid ICR hybrider look different every time in doctests

        return nodes

    @log.timings
    def _map_node_uids(self, optimized_es):
        """ Return a list of node uids."""

        _uid_nodes = dict()

        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        # It is needed to build the UID's completely new,
        # cause calliope cannot store them the way Tessif does.

        for node in self.nodes:

            uid_dict = dict()
            uid_dict.update({
                'name': node,
                'component': 'bus',  # if it is not a bus it will be changed again
            })

            node = rename[node]

            for inheritance in optimized_es.inputs.inheritance:
                # need this tech variable in case of matching substrings in node names
                # e.g. 'oil sopply' as source and 'oil supply line' as bus would conflict and source interpreted as bus
                tech = str(inheritance.techs.data).split(':')[-1]

                if node == tech:

                    # Node name and Component type
                    comp = CalliopeResultier.component_type_mapping[f'{inheritance.data}']

                    uid_dict.update({
                        'component': comp
                    })

                    if node in optimized_es.inputs.names.techs.data:
                        uid_data = str(optimized_es.inputs.names.loc[{'techs': f'{node}'}].data).split('.')
                    else:
                        uid_data = []

                    # Others stored in technology name parameter as
                    #  ->  name.region.sector.carrier.node_type
                    # This does not work for busses or connectors,
                    # as they are locations only and no technologies in calliope
                    if len(uid_data) > 1:  # will be if not bus or connector
                        region = uid_data[1]
                        uid_dict.update({'region': region})

                        sector = uid_data[2]
                        uid_dict.update({'sector': sector})

                        carrier = uid_data[3]
                        uid_dict.update({'carrier': carrier})

                        node_type = uid_data[4]
                        uid_dict.update({'node_type': node_type})
                        break

                # check if it is a connector
                techs_data = str(inheritance.techs.data)
                if f'{node} reverse' in techs_data or f'{node} free transmission' in techs_data:
                    uid_dict.update({
                        'component': 'connector'
                    })
                    break

            # carrier is important and since previous definition doesnt
            # work on busses they are made here in another way. Also done if
            # none is given in tessif model.
            if 'carrier' not in uid_dict or uid_dict['carrier'] == 'None':
                for production in optimized_es.results.loc_tech_carriers_prod:
                    if f'{node}' in str(production.data):
                        carrier = str(production.data).split(":")[-1]
                        uid_dict.update({'carrier': carrier})
                        #   Looking at production is enough cause the info is stored as
                        #    producer::transmission::consumer::carrier
                        #   This means the consumers and their carrier can be found here as well as producers
                        break

            if uid_dict['component'] == 'bus' or uid_dict['component'] == 'connector':
                lat = float(optimized_es.inputs.loc_coordinates.loc[{'locs': f'{node}'}][0].data)
                lon = float(optimized_es.inputs.loc_coordinates.loc[{'locs': f'{node}'}][1].data)
                uid_dict.update({
                    'latitude': lat,
                    'longitude': lon,
                })
            else:
                lat = float(optimized_es.inputs.loc_coordinates.loc[{'locs': f'{node} location'}][0].data)
                lon = float(optimized_es.inputs.loc_coordinates.loc[{'locs': f'{node} location'}][1].data)
                uid_dict.update({
                    'latitude': lat,
                    'longitude': lon,
                })

            # store infos as class 'tessif.frused.namedtuples.Uid'
            uid = nts.Uid(**uid_dict)
            # build the dict containing the uids
            _uid_nodes[f'{uid_dict["name"]}'] = uid

        return _uid_nodes

    @log.timings
    def _map_edges(self, optimized_es):
        """Return string representation of (inflow, node) labels as
        :class:`list`"""

        edges = list()
        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        for node, uid in self._node_uids.items():

            # uid rename utility to be able to search for calliope tech name
            tech = rename[node]

            if uid.component.lower() == 'sink':
                for connection in optimized_es.inputs.loc_techs.data:
                    # The connection looks like "location1::transmission:location2" or "location::technology"
                    # only the transmission one links two locations containing information about edge
                    if f'transmission:{tech} location' in str(connection):
                        source = str(connection).split(':')[0]
                        target = node
                        edges.append(nts.Edge(source, target))

            elif uid.component.lower() == 'source':
                for connection in optimized_es.inputs.loc_techs.data:
                    # The connection looks like "location1::transmission:location2" or "location::technology"
                    # only the transmission one links two locations containing information about edge
                    if f'transmission:{tech} location' in str(connection):
                        source = node
                        target = str(connection).split(':')[0]
                        edges.append(nts.Edge(source, target))

            elif uid.component.lower() == 'connector':
                for connection in optimized_es.inputs.loc_techs.data:
                    # The connection looks like "location1::transmission:location2" or "location::technology"
                    # only the transmission one links two locations containing information about edge
                    # reverse connector has same busses linked
                    if tech == str(connection).split(':')[-1]:
                        source = node
                        target = str(connection).split(':')[0]
                        edges.append(nts.Edge(source, target))
                        # connectors go both ways always
                        edges.append(nts.Edge(target, source))

            elif uid.component.lower() == 'storage':
                for connection in optimized_es.inputs.loc_techs.data:
                    # The connection looks like "location1::transmission:location2" or "location::technology"
                    # only the transmission one links two locations containing information about edge
                    if f'transmission:{tech} location' in str(connection):
                        source = node
                        target = str(connection).split(':')[0]
                        edges.append(nts.Edge(source, target))
                        # storages go both ways always
                        edges.append(nts.Edge(target, source))

            elif uid.component.lower() == 'transformer':
                for count, connection in enumerate(optimized_es.inputs.energy_con.indexes['loc_techs']):
                    # The connection looks like "location1::transmission:location2" or "location::technology"
                    # only the transmission one links two locations containing information about edge
                    if f'transmission:{tech} location' in str(connection):
                        # if this is True this carrier is consumed
                        if optimized_es.inputs.energy_con.data[count]:
                            source = str(connection).split(':')[0]
                            target = node
                            edges.append(nts.Edge(source, target))
                        else:  # this carrier has be produced, as it is not consumed but connected to transformer
                            source = node
                            target = str(connection).split(':')[0]
                            edges.append(nts.Edge(source, target))

            # busses don't need to be done explicit cause every component
            # is only connected to busses. So the either point on the bus
            # already or they get pointed on by the bus already

        edges.sort()  # to avoid ICR hybrider look different every time in doctests

        return edges

    def _rename_nodes(self, optimized_es):
        """return dict of calliope tech and tech names"""
        # Some Nodes need to be renamed since calliope doesnt allow technology named like parent.
        # e.g. demand, supply, conversion, storage...
        # This rename utility is going to be used to determine
        # the calliope technology name for each node

        rename = dict()
        nodes = list()

        # each technology (tessif component) has it's own location
        for node in optimized_es.inputs.locs:
            if 'location' in str(node.data):
                # every technology has its own location with name that adds "location"
                # after tech name. To get rid of these we pass them.
                name = str(node.data).split(" location", 1)[0]
                nodes.append(name)
            elif 'reverse' in str(node.data):
                # Connectors are build using two separate locations.
                # One of them with the suffix 'reverse' which does not
                # need to be added as extra node here
                pass
            else:
                name = str(node.data)
                nodes.append(name)

        # try to rename nodes to tech param names instead of tech to walkaround conflicting names.
        for node in nodes:
            if node in optimized_es.inputs.names.techs.data:
                tessif_name = str(optimized_es.inputs.names.loc[{'techs': f'{node}'}].data).split('.')[0]
                technology_name = node
                rename[tessif_name] = technology_name
            else:
                # busses and connectors are not considered 'techs'
                rename[node] = node

        # dict looks like
        #   tessif_name: technology_name
        return rename


class IntegratedGlobalResultier(
        CalliopeResultier, base.IntegratedGlobalResultier):
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
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    Note
    ----
    Overall costs might differ from sum of OPEX and CAPEX on expansion problems
    due to rounding errors on calliope specific calculation using the lifetime,
    which is very small on small timeframes (lifetime = timesteps/8760).

    The Calliope objective differs from Tessif output if expansion problems with
    installed capacities are analysed. This is due to calliope not considering
    installed capacities by default and thus using the expansion minimum as
    installed capacity in tessif. The occuring costs are then erased in the mapping.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.IntegratedGlobalResultier>`.

    Examples
    --------
    1. Using :func:`~tessif.examples.data.tsf.py_hard.emission_objective` to
       quickly access a tessif energy system to use for doctesting, or trying
       out this frameworks utilities.

        >>> import tessif.examples.data.tsf.py_hard as tsf_examples
        >>> tsf_es = tsf_examples.emission_objective()

        Transform the energy system to an oemof energy system:

        >>> import tessif.transform.es2es.cllp as tessif_to_calliope
        >>> calliope_es = tessif_to_calliope.transform(tsf_es)

        Optmize the energy system:

        >>> import tessif.simulate as simulate
        >>> optimized_calliope_es = simulate.cllp_from_es(calliope_es, solver='cbc')

        Extract the global results:

        >>> import pprint
        >>> import tessif.transform.es2mapping.cllp as calliope_post_process
        >>> resultier = calliope_post_process.IntegratedGlobalResultier(
        ...     optimized_calliope_es)
        >>> pprint.pprint(resultier.global_results)
        {'capex (ppcd)': 0.0,
         'costs (sim)': 252.0,
         'emissions (sim)': 60.0,
         'opex (ppcd)': 252.0}

     2. Using a native calliope model.
        Calling and optimize a calliope energy system model.

        >>> from tessif.frused.paths import example_dir
        >>> import calliope
        >>> calliope.set_log_verbosity('ERROR', include_solver_output=False)
        >>> calliope_es = calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
        >>> calliope_es.run()

        >>> import tessif.transform.es2mapping.cllp as calliope_post_process
        >>> import pprint
        >>> resultier = calliope_post_process.IntegratedGlobalResultier(calliope_es)
        >>> pprint.pprint(resultier.global_results)
        {'capex (ppcd)': 0.0,
         'costs (sim)': 105.0,
         'emissions (sim)': 53.0,
         'opex (ppcd)': 105.0}
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_global_results(self, optimized_es):

        flow_results = FlowResultier(optimized_es)
        cap_results = CapacityResultier(optimized_es)

        total_emissions = 0.0
        flow_costs = 0.0
        capital_costs = 0.0
        total_costs = optimized_es.results.objective_function_value

        # Flow based OPEX and Emissions
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

        # Simulated total costs and CAPEX
        for node in self.nodes:

            initial_capacity = cap_results.node_original_capacity[node]
            final_capacity = cap_results.node_installed_capacity[node]
            expansion_cost = cap_results.node_expansion_costs[node]

            if not any(
                    [cap is None
                     for cap in (final_capacity, initial_capacity)]
            ):
                node_expansion_costs = (
                    (final_capacity - initial_capacity) *
                    expansion_cost
                )
                #   The objective needs adjustments to make sure, the result is comparable.
                #   Calliope doesn't have "installed capacities" and thus calculates expansion
                #   costs starting from 0 capacity. By using the minimum capacity as installed
                #   capacity and substract the costs for the expansion up to the minimum capacity,
                #   the results will become comparable.

                # NOTE
                # - Seems like a small rounding error exists
                #   This is most likely due to the lifetime input, which calliope needs (and rounds to 10^-8).
                #   Lifetime is set to timesteps/8760 and has huge rounding when optimize small timeframes
                if isinstance(initial_capacity, pd.Series):
                    initial_costs = sum(initial_capacity * expansion_cost)
                    total_costs -= initial_costs
                else:
                    initial_costs = initial_capacity * expansion_cost
                    total_costs -= initial_costs
            else:
                node_expansion_costs = 0

            if isinstance(initial_capacity, pd.Series):
                node_expansion_costs = sum(node_expansion_costs)

            capital_costs += node_expansion_costs

        return {
            'emissions (sim)': round(total_emissions, 0),
            'costs (sim)': round(total_costs, 0, ),
            'opex (ppcd)': round(flow_costs, 0),
            'capex (ppcd)': round(capital_costs, 0),
        }


class ScaleResultier(CalliopeResultier, base.ScaleResultier):
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
    1. Call and optimize a calliope energy system model.

    >>> from tessif.frused.paths import example_dir
    >>> import calliope as native_calliope
    >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
    >>> calliope_es.run()
    >>> import tessif.transform.es2mapping.cllp as calliope_post_process
    >>> resultier = calliope_post_process.ScaleResultier(calliope_es)

    2. Access the number of constraints.

    >>> print(resultier.number_of_constraints)
    194
    """
    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_number_of_constraints(self, optimized_es):
        """Interface to extract the number of constraints out of the
        :ref:`model <SupportedModels>` specific, optimized energy system.
        """
        # Accessing a protected member of a calliope class. This is not ideal
        # as it's name or behavior might get changed without warning.
        optimized_es._backend_model.compute_statistics()
        return optimized_es._backend_model.statistics.number_of_constraints


class LoadResultier(CalliopeResultier, base.LoadResultier):
    """
    Transforming flow results into dictionairies keyed by node.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.LoadResultier>`.

    Examples
    --------
    1. Calling and optimize a calliope energy system model.

    >>> from tessif.frused.paths import example_dir
    >>> import calliope as native_calliope
    >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
    >>> calliope_es.run()
    >>> import tessif.transform.es2mapping.cllp as calliope_post_process
    >>> resultier = calliope_post_process.LoadResultier(calliope_es)

    2. Accessing a node's outflows as positive numbers and a node's inflows as
       negative numbers:

        >>> print(resultier.node_load['Powerline'])
        Powerline            Battery  Generator  Solar Panel  Battery  Demand
        1990-07-13 00:00:00     -0.0       -0.0        -12.0      1.0    11.0
        1990-07-13 01:00:00     -8.0       -0.0         -3.0      0.0    11.0
        1990-07-13 02:00:00     -0.9       -3.1         -7.0      0.0    11.0

    3. Accessing a node's inflows as positive numbers:

        >>> print(resultier.node_inflows['Powerline'])
        Powerline            Battery  Generator  Solar Panel
        1990-07-13 00:00:00      0.0        0.0         12.0
        1990-07-13 01:00:00      8.0        0.0          3.0
        1990-07-13 02:00:00      0.9        3.1          7.0

    4. Accessing a node's outflows as positive numbers:

        >>> print(resultier.node_outflows['Powerline'])
        Powerline            Battery  Demand
        1990-07-13 00:00:00      1.0    11.0
        1990-07-13 01:00:00      0.0    11.0
        1990-07-13 02:00:00      0.0    11.0

    5. Accessing the sum of a node's inflow (in case it's a
       :class:`~oemof.solph.Sink`) or the sum of a node's outflows (in case
       it's NOT a :class:`~oemof.solph.Sink`):

        >>> print(resultier.node_summed_loads['Powerline'])
        1990-07-13 00:00:00    12.0
        1990-07-13 01:00:00    11.0
        1990-07-13 02:00:00    11.0
        dtype: float64
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_loads(self, optimized_es):
        """ Map loads to node labels"""
        # Use defaultdict of empty DataFrame as loads container:
        _loads = defaultdict(lambda: pd.DataFrame())
        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        for node, uid in self.uid_nodes.items():

            # uid rename utility to be able to search for calliope tech name
            node = rename[node]

            timesteps = optimized_es.results.timesteps.data
            timesteps = pd.to_datetime(timesteps)

            outflows = pd.DataFrame(index=timesteps)
            inflows = pd.DataFrame(index=timesteps)

            for edge in self.edges:
                source, target = edge

                tsf_source = source
                tsf_target = target
                # uid rename utility to be able to search for calliope tech name
                source = rename[source]
                target = rename[target]

                if source == node:
                    for count, connection in enumerate(
                            optimized_es.results.carrier_prod.loc_tech_carriers_prod.data):

                        if 'transmission' in str(connection):
                            # connection string will now be like 'consumer::transmission:producer::carrier'
                            con = str(connection).split(':')[0]
                            prod = str(connection).split(':')[3]

                            if f'{source} location' == prod or source == prod or f'{source} reverse' == prod:
                                if f'{target} location' == con or target == con or f'{target} reverse' == con:
                                    # busses don't have the location added. Connector has reverse added

                                    # if source in prod doesn't work cause some components
                                    # might be same as another ones substring. e.g. 'x supply' and 'x supply line'
                                    production = optimized_es.results.carrier_prod.data[count].transpose(
                                    )
                                    production = pd.DataFrame(
                                        data=production, index=timesteps,
                                        columns={f"{tsf_target}"})
                                    # make "-0" to "0"
                                    production = production.replace(
                                        {-float(0): float(0)})
                                    outflows = pd.concat(
                                        [outflows, production], axis='columns')

                elif target == node:
                    for count, connection in enumerate(
                            optimized_es.results.carrier_prod.loc_tech_carriers_prod.data):
                        # working with carrier_con instead of carrier_prod doesnt work due to
                        # connectors which then being shown wrong when looking at busses.
                        # This happens due to the fact that conversion doesnt happen in connector
                        # itself but at the transmission between connector and bus.

                        if 'transmission' in str(connection):
                            # connection string will now be like 'consumer::transmission:producer::carrier'
                            con = str(connection).split(':')[0]
                            prod = str(connection).split(':')[3]

                            if f'{source} location' == prod or source == prod or f'{source} reverse' == prod:
                                if f'{target} location' == con or target == con or f'{target} reverse' == con:
                                    # busses don't have the location added. Connector has reverse added

                                    # if source in prod doesn't work cause some components
                                    # might be same as another ones substring. e.g. 'x supply' and 'x supply line'
                                    consumption = optimized_es.results.carrier_prod.data[count].transpose(
                                    )
                                    consumption = pd.DataFrame(
                                        data=consumption, index=timesteps,
                                        columns={f"{tsf_source}"})
                                    # make values negative
                                    consumption = consumption.multiply(-1)
                                    # make "0" to "-0"
                                    consumption = consumption.replace(
                                        {0: -float(0), float(0): -float(0)})
                                    inflows = pd.concat(
                                        [inflows, consumption], axis='columns')

            time_series_results = pd.concat(
                [inflows, outflows], axis='columns')
            time_series_results.columns.name = uid.name

            _loads[uid.name] = time_series_results

        return dict(_loads)


class CapacityResultier(base.CapacityResultier, LoadResultier):
    """Transforming installed capacity results dictionairies keyed by node.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.CapacityResultier>`.

    Note
    ----
    Expansion costs on CHP's will look different than they have been set in model.
    This is due to the fact, that calliope only considers one cost parameter, thus
    the different CHP parameters are put together to one value and later on cannot
    be separated again.

    Examples
    --------

    1. Transforming and optimize a tessif energy system using calliope.

    >>> import tessif.examples.data.tsf.py_hard as tsf_examples
    >>> import tessif.transform.es2es.cllp as tessif_to_calliope
    >>> import tessif.simulate as simulate
    >>> tsf_es = tsf_examples.create_mwe()
    >>> calliope_es = tessif_to_calliope.transform(tsf_es)
    >>> optimized_calliope_es = simulate.cllp_from_es(calliope_es, solver='cbc')
    >>> import tessif.transform.es2mapping.cllp as calliope_post_process
    >>> import pprint

    2. Display a small energy system's installed capacities after
       optimization as well as their original capacities:

        >>> resultier = calliope_post_process.CapacityResultier(optimized_calliope_es)
        >>> pprint.pprint(resultier.node_installed_capacity)
        {'Battery': 20.0,
         'Demand': 10.0,
         'Gas Station': 23.809524,
         'Generator': 10.0,
         'Pipeline': None,
         'Powerline': None}
        >>> pprint.pprint(resultier.node_original_capacity)
        {'Battery': 20.0,
         'Demand': 10.0,
         'Gas Station': 0.0,
         'Generator': 0.0,
         'Pipeline': None,
         'Powerline': None}

    3. Display a small energy system's characteristic values after
       optimization:

        >>> pprint.pprint(resultier.node_characteristic_value)
        {'Battery': 0.0,
         'Demand': 1.0,
         'Gas Station': 0.75,
         'Generator': 0.75,
         'Pipeline': None,
         'Powerline': None}

    4. Display a small energy system's reference capacity:

        >>> pprint.pprint(resultier.node_reference_capacity)
        23.809524

    5. Display capacity data for a multi output transformer:

        >>> tsf_es = tsf_examples.create_component_es(expansion_problem=True)
        >>> calliope_es = tessif_to_calliope.transform(tsf_es)
        >>> optimized_calliope_es = simulate.cllp_from_es(calliope_es, solver='cbc')
        >>> resultier = calliope_post_process.CapacityResultier(optimized_calliope_es)
        >>> print(resultier.node_installed_capacity['Biogas CHP'])
        Heatline     250.0
        Powerline    200.0
        dtype: float64
        >>> print(resultier.node_expansion_costs['Biogas CHP'])
        Heatline           0.0
        Powerline    3828125.0
        dtype: float64

        Note how the CHP expansion costs are only one value in Calliope even
        if they are splitted for each output in the Tessif energy system:

        >>> for transformer in tsf_es.transformers:
        ...     if transformer.uid.name == 'Biogas CHP':
        ...         print(transformer.expansion_costs)
        {'biogas': 0, 'electricity': 3500000, 'hot_water': 262500}

    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @property
    def node_characteristic_value(self):
        return self._characteristic_values

    def _map_installed_capacities(self, optimized_es):
        """Map installed capacities to node labels. None for nodes of variable
        size"""

        # Installed Capacities do actually not exist in Calliope as it assumes
        # everything to be 0 at start. It is assumed to be the minimum capacity
        # and the occuring costs will be sorted out in IntegratedGlobalResultier
        _installed_capacities = defaultdict(float)

        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        inst_cap = 0

        for node, uid in self.uid_nodes.items():

            # uid rename utility to be able to search for calliope tech name
            node = rename[node]

            if uid.component.lower() in ['bus', 'connector']:
                inst_cap = esn_defaults['variable_capacity']

            elif uid.component.lower() in ['source', 'sink']:
                inst_cap = float(
                    optimized_es.results.energy_cap.loc[{'loc_techs': f'{node} location::{node}'}].data)

            elif uid.component.lower() == 'storage':
                inst_cap = float(
                    optimized_es.results.storage_cap.loc[{'loc_techs_store': f'{node} location::{node}'}].data)

            elif uid.component.lower() == 'transformer':

                node_inst_cap_dict = dict()

                inst_cap = float(
                    optimized_es.results.energy_cap.loc[{'loc_techs': f'{node} location::{node}'}].data)

                if hasattr(optimized_es.inputs, 'carrier_ratios'):

                    # check if the transformer is a conversion plus technology (multi output)
                    if optimized_es.inputs.inheritance.loc[{'techs': f'{node}'}].data == 'conversion_plus':

                        for count, none_siso in enumerate(
                                optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus):

                            # none_siso string look like 'location::technology::carrier'
                            if node == str(none_siso.data).split(':')[2]:

                                flow = str(
                                    optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus.data[count])
                                flow = flow.split(':')[-1]

                                # replace carrier by bus
                                bus = flow  # to avoid error in case bus cannot be found, which should not happen

                                for transmission in optimized_es.inputs.loc_techs_transmission.data:

                                    # transmission string look like 'first location::carrier transmission:2nd location'
                                    carrier = str(transmission).split(
                                        ':')[2].split(' transmission')[0]
                                    loc1 = str(transmission).split(':')[
                                        0].split(' location')[0]
                                    loc2 = str(transmission).split(
                                        ':')[-1].split(' location')[0]

                                    if node == loc1 and flow == carrier:
                                        bus = loc2
                                        break
                                    elif node == loc2 and flow == carrier:
                                        bus = loc1
                                        break

                                node_inst_cap_dict[bus] = inst_cap

                                # carrier 'out' is always the primary one and 'out_2' has a ratio related to 'out'
                                ratios = optimized_es.get_formatted_array('carrier_ratios').loc[
                                    {'carrier_tiers': 'out_2'}].loc[{'techs': f'{node}'}].loc[
                                    {'locs': f'{node} location'}]

                                for ratio in ratios:
                                    if str(ratio.carriers.data) == flow:
                                        node_inst_cap_dict[bus] *= ratio.data
                                        break

                if node_inst_cap_dict:
                    # pop the input capacity
                    for edge in self.edges:
                        source, target = edge
                        if target == uid.name:
                            node_inst_cap_dict.pop(source)
                            break

                    inst_cap = pd.Series(node_inst_cap_dict).sort_index()

                else:
                    inst_cap = inst_cap

            _installed_capacities[uid.name] = inst_cap

        return dict(_installed_capacities)

    def _map_original_capacities(self, optimized_es):
        """Map pre-optimized installed capacities to node labels.
        tessif.frused.esn_defs['variable_capacity'] for
        nodes of variable size"""

        # Use default dict as installed capacities container:
        _installed_capacities = defaultdict(float)

        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        inst_cap = 0

        for node, uid in self.uid_nodes.items():

            # uid rename utility to be able to search for calliope tech name
            node = rename[node]

            if uid.component.lower() in ['bus', 'connector']:
                inst_cap = esn_defaults['variable_capacity']

            elif uid.component.lower() == 'source':
                inst_cap = float(
                    optimized_es.inputs.energy_cap_min.loc[{'loc_techs': f'{node} location::{node}'}].data)
                if str(inst_cap) == 'nan':
                    inst_cap = 0

            elif uid.component.lower() == 'sink':
                # doesn't have energy_cap_min, but since it cant be expandbale anyway the opt result can be used
                inst_cap = float(
                    optimized_es.results.energy_cap.loc[{'loc_techs': f'{node} location::{node}'}].data)
                if str(inst_cap) == 'nan':
                    inst_cap = 0

            elif uid.component.lower() == 'storage':
                inst_cap = float(
                    optimized_es.inputs.storage_cap_min.loc[{'loc_techs_store': f'{node} location::{node}'}].data)
                if str(inst_cap) == 'nan':
                    inst_cap = 0

            elif uid.component.lower() == 'transformer':

                node_inst_cap_dict = dict()

                inst_cap = float(
                    optimized_es.inputs.energy_cap_min.loc[{'loc_techs': f'{node} location::{node}'}].data)

                if hasattr(optimized_es.inputs, 'carrier_ratios'):

                    # check if the transformer is a conversion plus technology (multi output)
                    if optimized_es.inputs.inheritance.loc[{'techs': f'{node}'}].data == 'conversion_plus':

                        for count, none_siso in enumerate(
                                optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus):

                            # none_siso string look like 'location::technology::carrier'
                            if node == str(none_siso.data).split(':')[2]:

                                flow = str(
                                    optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus.data[count])
                                flow = flow.split(':')[-1]

                                # replace carrier by bus
                                bus = flow  # to avoid error in case bus cannot be found, which should not happen

                                for transmission in optimized_es.inputs.loc_techs_transmission.data:

                                    # transmission string look like 'first location::carrier transmission:2nd location'
                                    carrier = str(transmission).split(
                                        ':')[2].split(' transmission')[0]
                                    loc1 = str(transmission).split(':')[
                                        0].split(' location')[0]
                                    loc2 = str(transmission).split(
                                        ':')[-1].split(' location')[0]

                                    if node == loc1 and flow == carrier:
                                        bus = loc2
                                        break
                                    elif node == loc2 and flow == carrier:
                                        bus = loc1
                                        break

                                if str(inst_cap) == 'nan':
                                    inst_cap = 0

                                node_inst_cap_dict[bus] = inst_cap

                                # carrier 'out' is always the primary one and 'out_2' has a ratio related to 'out'
                                ratios = optimized_es.get_formatted_array('carrier_ratios').loc[
                                    {'carrier_tiers': 'out_2'}].loc[{'techs': f'{node}'}].loc[
                                    {'locs': f'{node} location'}]

                                for ratio in ratios:
                                    if str(ratio.carriers.data) == flow:
                                        node_inst_cap_dict[bus] *= ratio.data
                                        break

                if node_inst_cap_dict:
                    # pop the input capacity
                    for edge in self.edges:
                        source, target = edge
                        if target == uid.name:
                            node_inst_cap_dict.pop(source)
                            break

                    inst_cap = pd.Series(node_inst_cap_dict).sort_index()

                else:
                    if str(inst_cap) == 'nan':
                        inst_cap = 0
                    inst_cap = inst_cap

            _installed_capacities[uid.name] = inst_cap

        return dict(_installed_capacities)

    def _map_expansion_costs(self, optimized_es):

        expansion_costs = dict()

        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        # Map the respective expansion costs:
        for node, uid in self.uid_nodes.items():

            exp_cost = 0

            # uid rename utility to be able to search for calliope tech name
            node = rename[node]

            if hasattr(optimized_es.inputs, 'cost_energy_cap'):
                # calliope can't handle sink expansion
                if uid.component.lower() in ['bus', 'connector', 'sink']:
                    exp_cost = 0

                elif uid.component.lower() == 'source':
                    if f'{node} location::{node}' in optimized_es.inputs.cost_energy_cap.loc[
                            {'costs': f'monetary'}].loc_techs_investment_cost.data:

                        exp_cost = float(optimized_es.inputs.cost_energy_cap.loc[
                            {'costs': f'monetary'}].loc[
                            {'loc_techs_investment_cost': f'{node} location::{node}'}].data)
                        if str(exp_cost) == 'nan':
                            exp_cost = 0

                elif uid.component.lower() == 'transformer':
                    node_exp_cost_dict = dict()
                    if f'{node} location::{node}' in optimized_es.inputs.cost_energy_cap.loc[
                            {'costs': f'monetary'}].loc_techs_investment_cost.data:

                        exp_cost = float(optimized_es.inputs.cost_energy_cap.loc[
                            {'costs': f'monetary'}].loc[
                            {'loc_techs_investment_cost': f'{node} location::{node}'}].data)
                        if str(exp_cost) == 'nan':
                            exp_cost = 0

                    # Calliope only takes one value into account for expansion costs. This means the
                    # multiple values which can be modelled in Tessif are calculated to one representative
                    # calliope value. This can not be undone again, thus chp's do only have expansion
                    # costs refering to their primary carrier!
                    if hasattr(optimized_es.inputs, 'carrier_ratios'):

                        # check if the transformer is a conversion plus technology (multi output)
                        if optimized_es.inputs.inheritance.loc[{'techs': f'{node}'}].data == 'conversion_plus':

                            for count, none_siso in enumerate(
                                    optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus):

                                # none_siso string look like 'location::technology::carrier'
                                if node == str(none_siso.data).split(':')[2]:

                                    flow = str(
                                        optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus.data[
                                            count]
                                    )
                                    flow = flow.split(':')[-1]

                                    # replace carrier by bus
                                    bus = flow  # to avoid error in case bus cannot be found, which should not happen

                                    for transmission in optimized_es.inputs.loc_techs_transmission.data:

                                        # transmission string is 'first location::carrier transmission:2nd location'
                                        carrier = str(transmission).split(
                                            ':')[2].split(' transmission')[0]
                                        loc1 = str(transmission).split(':')[
                                            0].split(' location')[0]
                                        loc2 = str(transmission).split(
                                            ':')[-1].split(' location')[0]

                                        if node == loc1 and flow == carrier:
                                            bus = loc2
                                            break
                                        elif node == loc2 and flow == carrier:
                                            bus = loc1
                                            break

                                    for primary_carrier in optimized_es.inputs.lookup_primary_loc_tech_carriers_out:
                                        # primary_carrier.data looks like 'location::tech:carrier'
                                        if node == str(primary_carrier.data).split(':')[2]:
                                            if flow == str(primary_carrier.data).split(':')[-1]:
                                                if str(exp_cost) == 'nan':
                                                    exp_cost = 0
                                                node_exp_cost_dict[bus] = exp_cost
                                            else:
                                                node_exp_cost_dict[bus] = 0
                                            break

                    if node_exp_cost_dict:
                        # pop the input capacity
                        for edge in self.edges:
                            source, target = edge
                            if target == uid.name:
                                node_exp_cost_dict.pop(source)
                                break

                        exp_cost = pd.Series(node_exp_cost_dict).sort_index()

                    else:
                        exp_cost = exp_cost

            else:  # doesn't have cost_energy_cap, so all these show 0
                if uid.component.lower() in ['bus', 'connector', 'source', 'sink']:
                    exp_cost = 0
                elif uid.component.lower() == 'transformer':

                    node_exp_cost_dict = dict()
                    exp_cost = 0

                    if hasattr(optimized_es.inputs, 'carrier_ratios'):

                        # check if the transformer is a conversion plus technology (multi output)
                        if optimized_es.inputs.inheritance.loc[{'techs': f'{node}'}].data == 'conversion_plus':

                            for count, none_siso in enumerate(
                                    optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus):

                                # none_siso string look like 'location::technology::carrier'
                                if node == str(none_siso.data).split(':')[2]:

                                    flow = str(
                                        optimized_es.inputs.carrier_ratios.loc_tech_carriers_conversion_plus.data[
                                            count]
                                    )
                                    flow = flow.split(':')[-1]

                                    # replace carrier by bus
                                    bus = flow  # set equal to avoid error if bus not found, which should not happen

                                    for transmission in optimized_es.inputs.loc_techs_transmission.data:

                                        # transmission string look like
                                        # 'first location::carrier transmission:2nd location'
                                        carrier = str(transmission).split(
                                            ':')[2].split(' transmission')[0]
                                        loc1 = str(transmission).split(':')[
                                            0].split(' location')[0]
                                        loc2 = str(transmission).split(
                                            ':')[-1].split(' location')[0]

                                        if node == loc1 and flow == carrier:
                                            bus = loc2
                                            break
                                        elif node == loc2 and flow == carrier:
                                            bus = loc1
                                            break

                                    node_exp_cost_dict[bus] = 0

                    if node_exp_cost_dict:
                        # pop the input capacity
                        for edge in self.edges:
                            source, target = edge
                            if target == uid.name:
                                node_exp_cost_dict.pop(source)
                                break

                        exp_cost = pd.Series(node_exp_cost_dict).sort_index()

                    else:
                        exp_cost = exp_cost

            if hasattr(optimized_es.inputs, 'cost_storage_cap'):
                if uid.component.lower() == 'storage':
                    if f'{node} location::{node}' in optimized_es.inputs.cost_storage_cap.loc[
                            {'costs': f'monetary'}].loc_techs_investment_cost.data:

                        exp_cost = float(optimized_es.inputs.cost_storage_cap.loc[
                            {'costs': f'monetary'}].loc[
                            {'loc_techs_investment_cost': f'{node} location::{node}'}].data)
                        if str(exp_cost) == 'nan':
                            exp_cost = 0

            else:
                if uid.component.lower() == 'storage':
                    exp_cost = 0

            expansion_costs[uid.name] = exp_cost

        return expansion_costs

    @log.timings
    def _map_characteristic_values(self, optimized_es):
        """Map node label to characteristic value."""

        # Use default dict as capacity factors container:
        _characteristic_values = defaultdict(float)

        # Map the respective capacity factors:
        for node, uid in self.uid_nodes.items():

            characteristic_mean = pd.Series()

            inst_cap = self._installed_capacities[uid.name]

            # is the installed capacity a singular value?
            if not isinstance(inst_cap, abc.Iterable):

                if inst_cap != esn_defaults[
                        'variable_capacity']:

                    # storages
                    if uid.component.lower() == 'storage':
                        characteristic_mean = StorageResultier(
                            optimized_es).node_soc[str(uid.name)].mean(
                            axis='index')

                    # all other
                    else:
                        characteristic_mean = self.node_summed_loads[
                            str(uid.name)].mean(axis='index')

                    # deal with node of variable size, left unused:
                    if inst_cap == 0:
                        _characteristic_values[str(uid.name)] = 0
                    else:
                        _characteristic_values[
                            str(uid.name)] = characteristic_mean / inst_cap

                else:
                    _characteristic_values[
                        str(uid.name)] = esn_defaults[
                        'characteristic_value']

            else:
                characteristic_mean = self._outflows[
                    str(uid.name)].mean()

                # create the series beforehand
                char_values = pd.Series()
                for idx, cap in inst_cap.fillna(0).items():

                    if cap != 0:
                        char_values[idx] = characteristic_mean[idx] / cap
                    else:
                        char_values[idx] = 0

                # to replace nans by 0:
                _characteristic_values[
                    str(uid.name)] = char_values.fillna(0)

        return dict(_characteristic_values)


class StorageResultier(CalliopeResultier, base.StorageResultier):
    """
    Transforming storage results into dictionaries keyed by node.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.StorageResultier>`.

    Examples
    --------

    1. Transforming and optimize a tessif energy system using calliope.

    >>> import tessif.examples.data.tsf.py_hard as tsf_examples
    >>> import tessif.transform.es2es.cllp as tessif_to_calliope
    >>> import tessif.simulate as simulate
    >>> tsf_es = tsf_examples.create_storage_example()
    >>> calliope_es = tessif_to_calliope.transform(tsf_es)
    >>> optimized_calliope_es = simulate.cllp_from_es(calliope_es, solver='cbc')
    >>> import tessif.transform.es2mapping.cllp as calliope_post_process
    >>> import pprint

    2. Display a storage-node's capacity:

        >>> resultier = calliope_post_process.StorageResultier(optimized_calliope_es)
        >>> print(resultier.node_soc['Storage'])
        1990-07-13 00:00:00     8.100000
        1990-07-13 01:00:00    16.200000
        1990-07-13 02:00:00    27.000000
        1990-07-13 03:00:00    15.888889
        1990-07-13 04:00:00     4.777778
        Freq: H, Name: Storage, dtype: float64
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_states_of_charge(self, optimized_es):
        """ Map storage labels to their states of charge"""

        _socs = defaultdict(lambda: pd.Series())
        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        for node, uid in self.uid_nodes.items():

            # uid rename utility to be able to search for calliope tech name
            node = rename[node]

            if uid.component.lower() == 'storage':
                timesteps = optimized_es.results.timesteps.data
                timesteps = pd.DatetimeIndex(timesteps, freq='infer')
                soc = optimized_es.results.storage.loc[{'loc_techs_store': f'{node} location::{node}'}].data
                soc = pd.Series(soc)
                soc.index = timesteps
                soc.name = uid.name
                _socs[uid.name] = soc

        return dict(_socs)


class NodeCategorizer(CalliopeResultier, base.NodeCategorizer):
    """
    Categorizing the nodes of an optimized fine energy system.

    Categorization utilizes :attr:`~tessif.frused.namedtuples.Uid`.

    Nodes are categorized by:

        - Energy :paramref:`component
          <tessif.frused.namedtuples.Uid.component>`
          (One of the  'Bus', 'Sink', etc..)

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
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.NodeCategorizer>`.

    Note
    ----
    Calliope does not fully support tessif's uid notation. The UID is given inside the
    calliope technology name. Busses and connector are only locations and no techs,
    so they don't have any UID information besides the coordinates and the Carrier
    which information can be recreated using the in and output.
    The tessif component type can be identified since each calliope technology
    inherits from a parent technology which can be linked to a tessif component.
    Busses can be identified by the fact of not having a parent, due to not being a tech.

    Examples
    --------

    1. Calling and optimize a calliope energy system model.

    >>> from tessif.frused.paths import example_dir
    >>> import calliope as native_calliope
    >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
    >>> calliope_es.run()
    >>> import tessif.transform.es2mapping.cllp as calliope_post_process
    >>> import pprint

    2. Group energy system components by their
       :paramref:`Coordinates <tessif.frused.namedtuples.Uid.latitude>`:

        >>> resultier = calliope_post_process.NodeCategorizer(calliope_es)
        >>> pprint.pprint(resultier.node_coordinates)
        {'Battery': Coordinates(latitude=42.0, longitude=42.0),
         'Demand': Coordinates(latitude=42.0, longitude=42.0),
         'Gas Station': Coordinates(latitude=42.0, longitude=42.0),
         'Generator': Coordinates(latitude=42.0, longitude=42.0),
         'Pipeline': Coordinates(latitude=42.0, longitude=42.0),
         'Powerline': Coordinates(latitude=42.0, longitude=42.0),
         'Solar Panel': Coordinates(latitude=42.0, longitude=42.0)}

    3. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.region`:

        >>> pprint.pprint(resultier.node_region_grouped)
        {'Germany': ['Battery', 'Demand', 'Gas Station', 'Generator', 'Solar Panel'],
         'Unspecified': ['Pipeline', 'Powerline']}

    4. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.sector`

        >>> pprint.pprint(resultier.node_sector_grouped)
        {'Power': ['Battery', 'Demand', 'Gas Station', 'Generator', 'Solar Panel'],
         'Unspecified': ['Pipeline', 'Powerline']}

    5. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.node_type`:

        >>> pprint.pprint(resultier.node_type_grouped)
        {'Demand': ['Demand'],
         'Renewable': ['Solar Panel'],
         'Source': ['Gas Station'],
         'Storage': ['Battery'],
         'Transformer': ['Generator'],
         'Unspecified': ['Pipeline', 'Powerline']}

    6. Group energy system components by their energy
       :paramref:`~tessif.frused.namedtuples.Uid.carrier`:

        >>> pprint.pprint(resultier.node_carrier_grouped)
        {'Electricity': ['Battery', 'Demand', 'Generator', 'Powerline', 'Solar Panel'],
         'Fuel': ['Pipeline'],
         'Gas': ['Gas Station']}

    7. Map the `node uid representation <Labeling_Concept>` of each component
       of the energy system to their energy
       :paramref:`~tessif.frused.namedtuples.Uid.carrier` :

        >>> pprint.pprint(resultier.node_energy_carriers)
        {'Battery': 'electricity',
         'Demand': 'electricity',
         'Gas Station': 'Gas',
         'Generator': 'electricity',
         'Pipeline': 'fuel',
         'Powerline': 'electricity',
         'Solar Panel': 'electricity'}

    8. Map the `node uid representation <Labeling_Concept>` of each component
       of the energy system to their
       :paramref:`~tessif.frused.namedtuples.Uid.component`:

        >>> pprint.pprint(resultier.node_components)
        {'Bus': ['Pipeline', 'Powerline'],
         'Sink': ['Demand'],
         'Source': ['Gas Station', 'Solar Panel'],
         'Storage': ['Battery'],
         'Transformer': ['Generator']}

    Note how the many of the uid's data from busses (same for connectors)
    are unspecified due to their implementation in calliope not as a technologie
    but a combination of empty location and transmissions between each location.
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_node_components(self):
        """Nodes ordered by component "Bus" "Sink" etc.."""

        # Use default dict as sector strings container
        _component_nodes = defaultdict(list)

        # Map the respective components:
        for node, uid in self.uid_nodes.items():
            _component_nodes[uid.component.lower().capitalize()
                             ].append(str(node))

        return dict(_component_nodes)

    @log.timings
    def _map_node_sectors(self):
        """Nodes ordered by sector. i.e "Power" "Heat" "Mobility" "Coupled"."""

        # Use default dict as sector strings container
        _sectored_nodes = defaultdict(list)

        # Map the respective sectors:
        for node, uid in self.uid_nodes.items():
            _sectored_nodes[uid.sector.lower().capitalize()].append(str(node))

        return dict(_sectored_nodes)

    @log.timings
    def _map_node_regions(self):
        """Nodes ordered by region. i.e "World" "South" "Antinational"."""

        # Use default dict as sector strings container
        _regionalized_nodes = defaultdict(list)

        # Map the respective regions:
        for node, uid in self.uid_nodes.items():
            _regionalized_nodes[uid.region.lower().capitalize()
                                ].append(str(node))

        return dict(_regionalized_nodes)

    @log.timings
    def _map_node_coordinates(self):
        """Longitude and Latitude of each node present in energy system."""

        # Use default dict as coordinate namedtuple container
        _coordinates = defaultdict(nts.Coordinates)

        # Map the respective coordinates:
        for node, uid in self.uid_nodes.items():
            _coordinates[str(node)] = nts.Coordinates(
                uid.latitude, uid.longitude)

        return dict(_coordinates)

    @log.timings
    def _map_node_energy_carriers(self):
        """Nodes ordered by energy carrier. "Electricity", "Gas", "Heat"."""

        # Use default dict as carrier strings container
        _carrier_grouped_nodes = defaultdict(list)
        _node_energy_carriers = defaultdict(str)

        # Map the respective carriers:
        for node, uid in self.uid_nodes.items():
            _carrier_grouped_nodes[uid.carrier].append(
                str(node))
            _node_energy_carriers[str(node)] = uid.carrier

        return dict(_carrier_grouped_nodes), dict(_node_energy_carriers)

    @log.timings
    def _map_node_types(self):
        """Nodes grouped by "type" (arbitrary classification)"""

        # Use default dict as sector strings container
        _typed_nodes = defaultdict(list)

        # Map the respective node type:
        for node, uid in self.uid_nodes.items():
            _typed_nodes[uid.node_type].append(str(node))

        return dict(_typed_nodes)


class FlowResultier(base.FlowResultier, LoadResultier):
    """
    Transforming flow results into dictionairies keyed by edges.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.FlowResultier>`.

    Note
    ----
    Calliope can not assign different costs and emissions for each output of a CHP.
    To take those costs and emissions into account they are added to the input
    costs and emissions.

    Examples
    --------

    1. Calling and optimize a calliope energy system model.

    >>> from tessif.frused.paths import example_dir
    >>> import calliope
    >>> calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> calliope_es = calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
    >>> calliope_es.run()
    >>> import tessif.transform.es2mapping.cllp as calliope_post_process
    >>> import pprint

    2. Display the net energy flows of a small energy system:

    >>> resultier = calliope_post_process.FlowResultier(calliope_es)
    >>> pprint.pprint(resultier.edge_net_energy_flow)
    {Edge(source='Battery', target='Powerline'): 8.9,
     Edge(source='Gas Station', target='Pipeline'): 7.38,
     Edge(source='Generator', target='Powerline'): 3.1,
     Edge(source='Pipeline', target='Generator'): 7.38,
     Edge(source='Powerline', target='Battery'): 1.0,
     Edge(source='Powerline', target='Demand'): 33.0,
     Edge(source='Solar Panel', target='Powerline'): 22.0}

    3. Display the total costs incurred sorted by edge/flow:

    >>> pprint.pprint(resultier.edge_total_costs_incurred)
    {Edge(source='Battery', target='Powerline'): 0.0,
     Edge(source='Gas Station', target='Pipeline'): 73.8,
     Edge(source='Generator', target='Powerline'): 31.0,
     Edge(source='Pipeline', target='Generator'): 0.0,
     Edge(source='Powerline', target='Battery'): 0.0,
     Edge(source='Powerline', target='Demand'): 0.0,
     Edge(source='Solar Panel', target='Powerline'): 0.0}

    4. Display the total emissions caused sorted by edge/flow:

    >>> pprint.pprint(resultier.edge_total_emissions_caused)
    {Edge(source='Battery', target='Powerline'): 0.0,
     Edge(source='Gas Station', target='Pipeline'): 22.14,
     Edge(source='Generator', target='Powerline'): 31.0,
     Edge(source='Pipeline', target='Generator'): 0.0,
     Edge(source='Powerline', target='Battery'): 0.0,
     Edge(source='Powerline', target='Demand'): 0.0,
     Edge(source='Solar Panel', target='Powerline'): 0.0}


    5. Display the specific flow costs of this energy system:

    >>> pprint.pprint(resultier.edge_specific_flow_costs)
    {Edge(source='Battery', target='Powerline'): 0.0,
     Edge(source='Gas Station', target='Pipeline'): 10.0,
     Edge(source='Generator', target='Powerline'): 10.0,
     Edge(source='Pipeline', target='Generator'): 0.0,
     Edge(source='Powerline', target='Battery'): 0,
     Edge(source='Powerline', target='Demand'): 0.0,
     Edge(source='Solar Panel', target='Powerline'): 0.0}

    6. Display the specific emission of this energy system:

    >>> pprint.pprint(resultier.edge_specific_emissions)
    {Edge(source='Battery', target='Powerline'): 0.0,
     Edge(source='Gas Station', target='Pipeline'): 3.0,
     Edge(source='Generator', target='Powerline'): 10.0,
     Edge(source='Pipeline', target='Generator'): 0.0,
     Edge(source='Powerline', target='Battery'): 0,
     Edge(source='Powerline', target='Demand'): 0.0,
     Edge(source='Solar Panel', target='Powerline'): 0.0}

    7. Show the caluclated edge weights of this energy system:

    >>> pprint.pprint(resultier.edge_weight)
    {Edge(source='Battery', target='Powerline'): 0.1,
     Edge(source='Gas Station', target='Pipeline'): 1.0,
     Edge(source='Generator', target='Powerline'): 1.0,
     Edge(source='Pipeline', target='Generator'): 0.1,
     Edge(source='Powerline', target='Battery'): 0.1,
     Edge(source='Powerline', target='Demand'): 0.1,
     Edge(source='Solar Panel', target='Powerline'): 0.1}

    8. Access the reference emissions and net energy flow:

    >>> print(resultier.edge_reference_emissions)
    10.0

    >>> print(resultier.edge_reference_net_energy_flow)
    33.0
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_specific_flow_costs(self, optimized_es):
        r"""Energy specific flow costs mapped to edges."""
        # Use default dict as net energy flows container:
        _specific_flow_costs = defaultdict(float)
        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        # Map the respective flow costs:
        for edge in self.edges:
            tsf_source, tsf_target = edge

            # uid rename utility to be able to search for calliope tech name
            source = rename[tsf_source]
            target = rename[tsf_target]

            if hasattr(optimized_es.inputs, 'cost_om_con'):

                if f'{target} location::{target}' in optimized_es.inputs.cost_om_con.loc[
                        {'costs': 'monetary'}].loc_techs_om_cost.data:

                    cost_in = float(optimized_es.inputs.cost_om_con.loc[{'costs': 'monetary'}].loc[
                        {'loc_techs_om_cost': f'{target} location::{target}'}].data)

                    if str(cost_in) == 'nan':
                        cost_in = 0
                else:
                    cost_in = 0
            else:
                cost_in = 0

            if hasattr(optimized_es.inputs, 'cost_om_prod'):

                if f'{source} location::{source}' in optimized_es.inputs.cost_om_prod.loc[
                        {'costs': 'monetary'}].loc_techs_om_cost.data:
                    cost_out = float(optimized_es.inputs.cost_om_prod.loc[{'costs': 'monetary'}].loc[
                        {'loc_techs_om_cost': f'{source} location::{source}'}].data)

                    if str(cost_out) == 'nan':
                        cost_out = 0
                else:  # gonna happen for busses and connectors
                    cost_out = 0
            else:  # gonna happen for busses and connectors
                cost_out = 0

            _specific_flow_costs[
                nts.Edge(
                    f"{tsf_source}",
                    f"{tsf_target}")] = cost_in + cost_out

            # transformers that are not single input single output need adjustments
            if hasattr(optimized_es.inputs, 'lookup_primary_loc_tech_carriers_out'):

                for count2, loc_tech_carriers in enumerate(
                        optimized_es.inputs.lookup_primary_loc_tech_carriers_out.data):
                    # primary carrier out only exists if multiple outputs exist
                    # loc_tech_carriers like -> " tech location::tech::primary carrier "
                    tech = str(loc_tech_carriers).split(':')[2]
                    primary = str(loc_tech_carriers).split(':')[-1]

                    if source == tech:  # only happens if it is multi output

                        for count, loc_carrier in enumerate(optimized_es.inputs.loc_carriers.data):
                            # loc_carrier like -> loc::carrier
                            # only busses atached to none busses
                            loc = str(loc_carrier).split(':')[0]
                            carrier = str(loc_carrier).split(':')[-1]
                            if target == loc:
                                if primary == carrier:  # everything is fine
                                    pass
                                else:  # adjustment needed
                                    _specific_flow_costs[
                                        nts.Edge(
                                            f"{tsf_source}",
                                            f"{tsf_target}")
                                    ] = 0
                                break
                        break

        return dict(_specific_flow_costs)

    @log.timings
    def _map_specific_emissions(self, optimized_es):
        r"""Energy specific emissions mapped to edges."""
        # Use default dict as net energy flows container:
        _specific_emissions = defaultdict(float)
        # technology - node rename utility to be able to search for calliope tech name
        rename = self._rename_nodes(optimized_es=optimized_es)

        # Map the respective flow costs:
        for edge in self.edges:
            tsf_source, tsf_target = edge

            # uid rename utility to be able to search for calliope tech name
            source = rename[tsf_source]
            target = rename[tsf_target]

            if hasattr(optimized_es.inputs, 'cost_om_con'):
                if 'emissions' in optimized_es.inputs.cost_om_prod.costs:

                    if f'{target} location::{target}' in optimized_es.inputs.cost_om_con.loc[
                            {'costs': 'emissions'}].loc_techs_om_cost.data:

                        emi_in = float(optimized_es.inputs.cost_om_con.loc[{'costs': 'emissions'}].loc[
                            {'loc_techs_om_cost': f'{target} location::{target}'}].data)

                        if str(emi_in) == 'nan':
                            emi_in = 0
                    else:
                        emi_in = 0
                else:
                    emi_in = 0
            else:
                emi_in = 0

            if hasattr(optimized_es.inputs, 'cost_om_prod'):
                if 'emissions' in optimized_es.inputs.cost_om_prod.costs:

                    if f'{source} location::{source}' in optimized_es.inputs.cost_om_prod.loc[
                            {'costs': 'emissions'}].loc_techs_om_cost.data:

                        emi_out = float(optimized_es.inputs.cost_om_prod.loc[{'costs': 'emissions'}].loc[
                            {'loc_techs_om_cost': f'{source} location::{source}'}].data)

                        if str(emi_out) == 'nan':
                            emi_out = 0
                    else:  # gonna happen for busses and connectors
                        emi_out = 0
                else:  # no technology has emissions
                    emi_out = 0
            else:  # no technology has om_prod costs
                emi_out = 0

            _specific_emissions[
                nts.Edge(
                    f"{tsf_source}",
                    f"{tsf_target}")] = emi_in + emi_out

            # transformers that are not single input single output need adjustments
            if hasattr(optimized_es.inputs, 'lookup_primary_loc_tech_carriers_out'):

                for count2, loc_tech_carriers in enumerate(
                        optimized_es.inputs.lookup_primary_loc_tech_carriers_out.data):
                    # primary carrier out only exists if multiple outputs exist
                    # loc_tech_carriers like -> " tech location::tech::primary carrier "
                    tech = str(loc_tech_carriers).split(':')[2]
                    primary = str(loc_tech_carriers).split(':')[-1]

                    if source == tech:  # only happens if it is multi output

                        for count, loc_carrier in enumerate(optimized_es.inputs.loc_carriers.data):
                            # loc_carrier like -> loc::carrier
                            # only busses atached to none busses
                            loc = str(loc_carrier).split(':')[0]
                            carrier = str(loc_carrier).split(':')[-1]
                            if target == loc:
                                if primary == carrier:  # everything is fine
                                    pass
                                else:  # adjustment needed
                                    _specific_emissions[
                                        nts.Edge(
                                            f"{tsf_source}",
                                            f"{tsf_target}")
                                    ] = 0
                                break
                        break

        return dict(_specific_emissions)


class AllResultier(CapacityResultier, FlowResultier, StorageResultier,
                   ScaleResultier):
    r"""
    Transform energy system results into a dictionary keyed by attribute.

    Incorporates all the functionalities from its bases.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    Note
    ----
    This class allows interfacing with **ALL** framework processing utilities.
    It extracts every bit of info the author ever needed in his postprocessing.

    It is meant to be a "one fits all" solution for small energy systems.
    Perfectly fit for showing "proof of concepts" or debugging energy system
    components.

    **Not** meant to be used with **large energy systems**.
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)


class LabelFormatier(base.LabelFormatier, FlowResultier, CapacityResultier):
    r"""
    Generate component summaries as multiline label dictionairy entries.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.LabelFormatier>`.

    Examples
    --------

    1. Calling and optimize a calliope energy system model.

        >>> from tessif.frused.paths import example_dir
        >>> import calliope as native_calliope
        >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
        >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
        >>> calliope_es.run()

    2. Compile and display a node's summary:

        >>> import tessif.transform.es2mapping.cllp as calliope_post_process
        >>> formatier = calliope_post_process.LabelFormatier(calliope_es)
        >>> print(formatier.node_summaries['Demand'])
        {'Demand': 'Demand\n11 MW\ncf: 1.0'}

    2. Compile and display an edge's summary:

        >>> print(formatier.edge_summaries[('Solar Panel', 'Powerline')])
        {('Solar Panel', 'Powerline'): '22 MWh\n0.0 €/MWh\n0.0 t/MWh'}

    """

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es, **kwargs)


class NodeFormatier(base.NodeFormatier, CapacityResultier):
    r"""Transforming energy system results into node visuals.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

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

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.NodeFormatier>`.

    Examples
    --------

    1. Calling and optimize a calliope energy system model.

        >>> from tessif.frused.paths import example_dir
        >>> import calliope as native_calliope
        >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
        >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
        >>> calliope_es.run()

    2. Generate and display a small energy system's node shape mapping:

        >>> import tessif.transform.es2mapping.cllp as calliope_post_process
        >>> import pprint
        >>> formatier = calliope_post_process.NodeFormatier(calliope_es)
        >>> pprint.pprint(formatier.node_shape)
        {'Battery': 's',
         'Demand': '8',
         'Gas Station': 'o',
         'Generator': '8',
         'Pipeline': 'o',
         'Powerline': 'o',
         'Solar Panel': 's'}

    3. Generate and display a small energy system's node size mapping:

        >>> pprint.pprint(formatier.node_size)
        {'Battery': 300,
         'Demand': 330,
         'Gas Station': 3000,
         'Generator': 450,
         'Pipeline': 'variable',
         'Powerline': 'variable',
         'Solar Panel': 600}

    4. Generate and display a small energy system's node fill size mapping:

        >>> pprint.pprint(formatier.node_fill_size)
        {'Battery': 110.0,
         'Demand': 330.0,
         'Gas Station': 74.0,
         'Generator': 31.0,
         'Pipeline': None,
         'Powerline': None,
         'Solar Panel': 220.0}


    5. Generate and display a small energy system's node color mapping basd on
       the grouping:

        >>> formatier = calliope_post_process.NodeFormatier(calliope_es, cgrp='all')
        >>> pprint.pprint(formatier.node_color.name)
        {'Battery': '#ccff00',
         'Demand': '#330099',
         'Gas Station': '#336666',
         'Generator': '#ff6600',
         'Pipeline': '#336666',
         'Powerline': '#ffcc00',
         'Solar Panel': '#ff9900'}

        >>> pprint.pprint(formatier.node_color.carrier)
        {'Battery': '#FFD700',
         'Demand': '#FFD700',
         'Gas Station': '#336666',
         'Generator': '#FFD700',
         'Pipeline': '#AFAFAF',
         'Powerline': '#FFD700',
         'Solar Panel': '#FFD700'}

        >>> pprint.pprint(formatier.node_color.sector)
        {'Battery': '#ffff33',
         'Demand': '#ffff33',
         'Gas Station': '#ffff33',
         'Generator': '#ffff33',
         'Pipeline': '#AFAFAF',
         'Powerline': '#AFAFAF',
         'Solar Panel': '#ffff33'}

    6. Generate and display a small energy system's node color map (colors
       that are cycled through for each component type) mapping basd on the
       grouping:

        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.name.items()})
        {'Battery': <class 'str'>,
         'Demand': <class 'str'>,
         'Gas Station': <class 'str'>,
         'Generator': <class 'str'>,
         'Pipeline': <class 'str'>,
         'Powerline': <class 'str'>,
         'Solar Panel': <class 'str'>}

        (Hint for devs: Which color string is mapped depends on order of
        mapping. Therefore only the type is printed and not its string value
        since it may differ from doctest to doctest.)

    """

    def __init__(self, optimized_es, cgrp='name', **kwargs):

        super().__init__(optimized_es=optimized_es, cgrp=cgrp, **kwargs)


class MplLegendFormatier(base.MplLegendFormatier, CapacityResultier):
    r"""
    Generating visually enhanced matplotlib legends for nodes and edges.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

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

    1. Calling and optimize a calliope energy system model.

        >>> from tessif.frused.paths import example_dir
        >>> import calliope as native_calliope
        >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
        >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
        >>> calliope_es.run()

    2. Generate and display label grouped legend labels of a small energy
       system:

        >>> import tessif.transform.es2mapping.cllp as calliope_post_process
        >>> import pprint
        >>> formatier = calliope_post_process.MplLegendFormatier(calliope_es)
        >>> pprint.pprint(formatier.node_legend.name['legend_labels'])
        ['Battery',
         'Demand',
         'Gas Station',
         'Generator',
         'Pipeline',
         'Powerline',
         'Solar Panel']

    3. Generate and display matplotlib legend attributes to describe
       :paramref:`fency node styles
       <tessif.visualize.nxgrph.draw_nodes.draw_fency_nodes>`. Fency as in:

            - variable node size being outer fading circles
            - cycle filling being proportional capacity factors
            - outer diameter being proportional installed capacities

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

        # needed transformers

        # mpl legend formatier is the only class needing an extra formatier
        # instead of just inheriting it. This allows bundling as done in the
        # AllFormatier with its specific color group (cgrp) and still be able
        # to map the legends for all colors

        # a different plausible approach would be to only map the bundled
        # color, and implement some if clauses to only map the legend
        # requested. This also implies chaining the behaviour of
        # MplLegendFormatier.node_legend
        self._nformats = NodeFormatier(optimized_es, cgrp='all')

        super().__init__(optimized_es=optimized_es, cgrp='all',
                         markers=markers, **kwargs)


class EdgeFormatier(base.EdgeFormatier, FlowResultier):
    r"""Transforming energy system results into edge visuals.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.EdgeFormatier>`.

    Examples
    --------

    1. Calling and optimize a calliope energy system model.

        >>> from tessif.frused.paths import example_dir
        >>> import calliope as native_calliope
        >>> native_calliope.set_log_verbosity('ERROR', include_solver_output=False)
        >>> calliope_es = native_calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
        >>> calliope_es.run()

    1. Generate and display a small energy system's edge withs:

        >>> import tessif.transform.es2mapping.cllp as calliope_post_process
        >>> import pprint
        >>> formatier = calliope_post_process.EdgeFormatier(calliope_es)
        >>> pprint.pprint(list(sorted(formatier.edge_width.items())))
        [(Edge(source='Battery', target='Powerline'), 0.27),
         (Edge(source='Gas Station', target='Pipeline'), 0.22),
         (Edge(source='Generator', target='Powerline'), 0.1),
         (Edge(source='Pipeline', target='Generator'), 0.22),
         (Edge(source='Powerline', target='Battery'), 0.1),
         (Edge(source='Powerline', target='Demand'), 1.0),
         (Edge(source='Solar Panel', target='Powerline'), 0.67)]

        >>> dc_formatier = calliope_post_process.EdgeFormatier(
        ...     calliope_es,
        ...     drawutil="dc")
        >>> pprint.pprint(list(sorted(dc_formatier.edge_width.items())))
        [(Edge(source='Battery', target='Powerline'), 1.89),
         (Edge(source='Gas Station', target='Pipeline'), 1.57),
         (Edge(source='Generator', target='Powerline'), 0.66),
         (Edge(source='Pipeline', target='Generator'), 1.57),
         (Edge(source='Powerline', target='Battery'), 0.5),
         (Edge(source='Powerline', target='Demand'), 7.0),
         (Edge(source='Solar Panel', target='Powerline'), 4.67)]

    2. Generate and display a small energy system's edge colors:

        >>> pprint.pprint(list(sorted(formatier.edge_color.items())))
        [(Edge(source='Battery', target='Powerline'), [0.15]),
         (Edge(source='Gas Station', target='Pipeline'), [0.3]),
         (Edge(source='Generator', target='Powerline'), [1.0]),
         (Edge(source='Pipeline', target='Generator'), [0.15]),
         (Edge(source='Powerline', target='Battery'), [0.15]),
         (Edge(source='Powerline', target='Demand'), [0.15]),
         (Edge(source='Solar Panel', target='Powerline'), [0.15])]

        (:func:`~networkx.drawing.nx_pylab.draw_networkx_edges` expects
        iterable of floats when using a colormap)

        >>> pprint.pprint(list(sorted(dc_formatier.edge_color.items())))
        [(Edge(source='Battery', target='Powerline'), '#d8d8d8'),
         (Edge(source='Gas Station', target='Pipeline'), '#b2b2b2'),
         (Edge(source='Generator', target='Powerline'), '#000000'),
         (Edge(source='Pipeline', target='Generator'), '#d8d8d8'),
         (Edge(source='Powerline', target='Battery'), '#d8d8d8'),
         (Edge(source='Powerline', target='Demand'), '#d8d8d8'),
         (Edge(source='Solar Panel', target='Powerline'), '#d8d8d8')]
    """

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es,
                         **kwargs)


class AllFormatier(
        LabelFormatier, NodeFormatier, MplLegendFormatier, EdgeFormatier):
    r"""
    Transforming ES results into visual expression dicts keyed by attribute.
    Incorporates all the functionalities from its
    parents.

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrier', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionary.

        Used by :class:`NodeFormatier` and :class:`MplLegendFormatier`

    markers: str, default='formatier'
        What marker to use for legend entries. Either ``'formatier'`` or
        one of the :any:`matplotlib.markers`.

        If ``'formatier'`` is used, markers will be inferred from
        :attr:`NodeFormatier.node_shape`.

        Used by :class:`MplLegendFormatier`

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
                 markers='formatier', **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            cgrp=cgrp, markers=markers, **kwargs)


class ICRHybridier(CalliopeResultier, base.ICRHybridier):
    """
    Aggregate numerical and visual information for visualizing
    the :ref:`Integrated_Component_Results` (ICR).

    Parameters
    ----------
    optimized_es: :class:`~calliope.core.model.Model`
        An optimized calliope energy system containing its
        inputs as well as results.

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
        r"""Map node label to characteristic value.

        Components of variable size have a characteristic value of ``None``.

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
