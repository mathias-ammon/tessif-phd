"""
:mod:`tessif.transform.es2es.omf` is a :mod:`tessif` module aggregating all the
functionality for automatically transforming a :class:`tessif energy system
<tessif.model.energy_system.AbstractEnergySystem>` into an
:class:`oemof energy system <oemof.core.energy_system.EnergySystem>`.
"""
import collections
import numbers
from warnings import warn
import logging

import oemof.solph as solph
import numpy as np

import tessif.frused.namedtuples as nts
from tessif.frused import spellings
from tessif.model import components

logger = logging.getLogger(__name__)


def _to_oemof_conversions(tessif_conversions):
    """
    Translate tessif's conversions dictionairy into oemof's.

    Parameters
    ----------
    tessif_conversions: dict
        Tessif's :paramref:`efficiency map
        <tessif.model.component.Transformer.conversions>`

    Return
    ------
    oemof_conversions: dict
        Oemof's :class:`efficiency map <oemof.solph.network.transformer.Transformer>`

    Example
    -------
    >>> convs = {('fuel', 'electricity'): 0.3, ('air', 'electricity'): 0.2,
    ...          ('fuel', 'heat'): 0.4, ('air', 'heat'): 0.25, }
    >>> print(_to_oemof_conversions(convs))
    {'electricity': 0.3, 'air': 0.1111111111111111, 'heat': 0.4}
    """
    oemof_conversions = dict()
    for tple, factor in tessif_conversions.items():
        if tple[1] not in oemof_conversions:
            oemof_conversions[tple[1]] = factor
        elif tple[0] not in oemof_conversions:
            oemof_conversions[tple[0]] = factor
        else:
            oemof_conversions[tple[0]] = 1 / (
                1/oemof_conversions[tple[0]] + 1/factor)

    return oemof_conversions


def _parse_oemof_flow_parameters(component, target):

    # oemof interprets many parameters as normalized to the nominal value
    # tessif components do not specify a nominal value directly
    # they implicate it though through their flow rates.

    nominal_value = component.flow_rates[target].max
    if isinstance(nominal_value, collections.abc.Iterable):
        nominal_value = max(nominal_value)

    # linear flow parameters
    flow_params = dict()
    if nominal_value != float('inf'):

        # in some rare cases nominal value is 0. For ie reading external
        # renewable data for only a certain period, where there is no output
        if nominal_value == 0:
            flow_params.update(
                {
                    'nominal_value': nominal_value,

                    # linear gradient flow parameters
                    'positive_gradient': {
                        'ub': component.flow_gradients[target].positive,
                        'costs': component.gradient_costs[target].positive
                    },
                    'negative_gradient': {
                        'ub': component.flow_gradients[target].negative,
                        'costs': component.gradient_costs[target].negative
                    },
                }
            )
        else:
            # oemof uses specific values for the following set of parameters.
            flow_params.update(
                {
                    'nominal_value': nominal_value,
                    'min': component.flow_rates[target].min/nominal_value,
                    'max': component.flow_rates[target].max/nominal_value,

                    # linear gradient flow parameters
                    'positive_gradient': {
                        'ub': component.flow_gradients[target].positive,
                        'costs': component.gradient_costs[target].positive
                    },
                    'negative_gradient': {
                        'ub': component.flow_gradients[target].negative,
                        'costs': component.gradient_costs[target].negative
                    },
                }
            )
    else:
        if component.timeseries:
            if component.timeseries[target] is not None:
                # preset nominal value in case a timeseries is used
                # to parse specific values and existing when dealing with
                # expandable values
                flow_params['nominal_value'] = max(
                    component.timeseries[target].max)
                nominal_value = flow_params['nominal_value']
            else:
                flow_params['nominal_value'] = nominal_value
        else:
            flow_params['nominal_value'] = nominal_value

        flow_params['min'] = 0.0
        flow_params['max'] = 1.0

        # linear gradient flow parameters
        flow_params['positive_gradient'] = {
            'ub': float('inf'),
            'costs': component.gradient_costs[target].positive
        }
        flow_params['negative_gradient'] = {
            'ub': float('inf'),
            'costs': component.gradient_costs[target].negative
        }

    # optimization targets:
    flow_params.update({
        'variable_costs': component.flow_costs[target],
        'emissions': component.flow_emissions[target]})

    # component specific linear flow params:
    if hasattr(component, 'accumulated_amounts'):
        if target in component.accumulated_amounts:
            # parse minimum = 0 to None, to match oemof:
            if component.accumulated_amounts[target].min == 0:
                summed_min = None
            else:
                summed_min = component.accumulated_amounts[
                    target].min / nominal_value

            if component.accumulated_amounts[target].max == float('inf'):
                summed_max = None
            else:
                summed_max = component.accumulated_amounts[
                    target].max/nominal_value

            flow_params.update({
                'summed_min': summed_min,
                'summed_max': summed_max,
            })

    # expansion problem parameters:
    if component.expandable[target]:
        flow_params.pop('positive_gradient')
        flow_params.pop('negative_gradient')
        max_expansion = component.expansion_limits[target].max - flow_params[
            'nominal_value']
        min_expansion = component.expansion_limits[target].min - flow_params[
            'nominal_value']

        if max_expansion < 0:
            msg = (
                "Requested maximum expansion limit of " +
                f"'{component.expansion_limits[target].max}' of flow "
                f"'{target}' of component '{component.uid.name}' is below "
                "current installed capacity of "
                f"'{flow_params['nominal_value']}'. Falling back on current "
                "installed capacity as maximum."
            )
            logger.warning(msg)
            max_expansion = flow_params['nominal_value']

        elif max_expansion == float('+inf'):
            # oemofs inf expansion == None
            max_expansion = None

        if min_expansion < 0:
            msg = (
                "Requested minimum expansion limit of " +
                f"'{component.expansion_limits[target].min}' of the flow "
                f"'{target}' of component '{component.uid.name}' is below "
                "current installed capacity of "
                f"'{flow_params['nominal_value']}'. Falling back on 0.0 as "
                "minimum additionally installed capacity."
            )
            logger.warning(msg)
            min_expansion = 0.0

        flow_params.update({
            'investment': solph.Investment(
                # oemof min/max are interpreted as additional limits where as
                # tessif sees them as absolute values

                maximum=max_expansion,
                minimum=min_expansion,
                ep_costs=component.expansion_costs[target],
                existing=flow_params['nominal_value']),
            'nominal_value': None})

    # nonconvex problem parameters:
    if component._milp[target]:
        flow_params.update({
            'nonconvex': solph.NonConvex(
                startup_costs=component.status_changing_costs.on,
                shutdown_costs=component.status_changing_costs.off,
                activity_costs=component.costs_for_being_active,
                minimum_uptime=component.status_inertia.on,
                minimum_downtime=component.status_inertia.off,
                maximum_startups=component.number_of_status_changes.on,
                maximum_shutdowns=component.number_of_status_changes.off,
                initial_status=component.initial_status,
            )})

    # chp parameters
    if isinstance(component, components.CHP):
        flow_params.update({
            'H_L_FG_share_max': getattr(component.enthalpy_loss, 'max', None),
            'H_L_FG_share_min': getattr(component.enthalpy_loss, 'min', None),
            'P_max_woDH': getattr(component.power_wo_dist_heat, 'max', None),
            'P_min_woDH': getattr(component.power_wo_dist_heat, 'min', None),
            'Eta_el_max_woDH': getattr(
                component.el_efficiency_wo_dist_heat, 'max', None),
            'Eta_el_min_woDH': getattr(
                component.el_efficiency_wo_dist_heat, 'min', None),
            'Q_CW_min': component.min_condenser_load,
        })

    # timeseries parameters
    if component.timeseries:
        if target in component.timeseries:
            # enforce float type in case 'inf' strings were parsed
            minimum = np.array(component.timeseries[target][0]).astype(float)
            maximum = np.array(component.timeseries[target][1]).astype(float)

            # in some rare cases nominal value is 0. For ie reading external
            # renewable data for only a certain period, where there is no
            # output
            if nominal_value != 0:
                flow_params.update({
                    # use tuple indexing cause timeseries read in from
                    # external sources my prohibit use of namedtuple syntax
                    'min': minimum/nominal_value,
                    'max': maximum/nominal_value,
                })
            else:
                flow_params.update({
                    # use tuple indexing cause timeseries read in from
                    # external sources my prohibit use of namedtuple syntax
                    'min': minimum,
                    'max': maximum,
                })

    # replace tessif's infinity values with None, so oemof can handle them:
    for key, v in flow_params.copy().items():
        if key in ('positive_gradient', 'negative_gradient'):
            if flow_params[key]['ub'] == float('inf'):
                flow_params[key]['ub'] = None

        # only consider numeric values
        # if key != 'nominal_value':
        if isinstance(v, numbers.Number):
            if v == float('inf'):
                flow_params[key] = None

    if not isinstance(flow_params['max'], collections.abc.Iterable):
        if np.isnan(flow_params['max']):
            flow_params['max'] = 1.0

    return flow_params


def _generate_oemof_bus_connection_flows(oemof_busses, tessif_busses):
    """
    """
    bus_dict = {bus.label.name: bus for bus in oemof_busses}

    print(30*'-')
    print('Inside connection flows:')

    for outer_bus in tessif_busses:
        outputs = dict()
        inputs = dict()
        print(outer_bus.uid)
        for inner_bus in tessif_busses:
            for inflow in inner_bus.inputs:
                if str(outer_bus.uid) in inflow:
                    print('Constructing flow from {} to {} for {}'.format(
                        outer_bus.uid, inner_bus.uid, outer_bus.uid))
                    outputs[bus_dict[inner_bus.uid.name]] = solph.Flow()

            print(50*'-')
            for outflow in inner_bus.outputs:
                if str(outer_bus.uid) in outflow:
                    print('Constructing flow from {} to {} for {}'.format(
                        inner_bus.uid, outer_bus.uid, outer_bus.uid))

                    inputs[bus_dict[inner_bus.uid.name]] = solph.Flow()
                    print(inputs)
                    print(50*'=')

        b = solph.Bus(
            label=nts.Uid(*outer_bus.uid),
            # inputs=inputs,
            # balanced=False,
            outputs=outputs,
        )
        print(b.inputs)
        print(b.outputs)
        yield b


def generate_oemof_busses(busses):
    """
    Generates oemof busses out of tessif busses.

    Parameters
    ----------
    busses: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Bus` objects that are to
        be transformed into :class:`oemof.solph.network.bus.Bus` objects.

    Return
    ------
    generated_busses :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`bus objects
        <oemof.solph.network.bus.Bus>`.
    """
    tessif_busses = list(busses)

    # return _generate_oemof_bus_connection_flows(oemof_busses, tessif_busses)
    for bus in tessif_busses:
        yield solph.Bus(
            label=nts.Uid(*bus.uid),
        )


def generate_oemof_chps(chps, tessif_busses, oemof_busses):
    """Generate oemof chps out of tessif chps

    Parameters
    ----------
    chps: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.CHP` objects that
        are to be transformed into
        :class:`oemof.solph.components.extraction_turbine_chp.ExtractionTurbineCHP`
        or :class:`oemof.solph.components.generic_chp.GenericCHP` objects.

    tessif_busses: ~collections.abc.Iterable
        Collection of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~generate_oemof_chps.chps`.

        Used for figuring out connections.

    oemof_busses: ~collections.abc.Iterable
        Iterable of :class:`oemof.solph.network.bus.Bus` objects present in the
        same energy system as
        :paramref:`~generate_oemof_chps.chps`.

        Used for figuring out connections.

    Return
    ------
    generated_chps :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`chp objects
        <oemof.solph.network.bus.Bus>`.

    Examples
    --------
    >>> # utilize example hub for accessing a parameterized energy system
    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_variable_chp()

    >>> # generate the chps:
    >>> chp = list(generate_oemof_chps(
    ...     chps=es.chps,
    ...     tessif_busses=es.busses,
    ...     oemof_busses=generate_oemof_busses(es.busses)))[0]

    Label:

    >>> print(chp.label)
    CHP1

    Conversion Factors:

    >>> for key, value in chp.conversion_factors.items():
    ...     print('{}: {}'.format(key, value[123123]))
    Powerline: 0.3
    Heat Grid: 0.2
    Gas Grid: 1

    >>> linear_flow_params = (
    ...     'nominal_value', 'summed_min', 'summed_max',
    ...     'min', 'max', 'positive_gradient', 'negative_gradient')

    >>> for flow in list(
    ...     chp.inputs.values())+list(chp.outputs.values()):
    ...     print("Flow from '{}' to '{}'".format(
    ...         flow.label.input, flow.label.output))
    ...     print('Linear flow parameters')
    ...     for attr in linear_flow_params:
    ...         print('{}:'.format(attr), getattr(flow, attr))
    ...     print()
    Flow from 'Gas Grid' to 'CHP1'
    Linear flow parameters
    nominal_value: None
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0.0}
    negative_gradient: {'ub': [], 'costs': 0.0}
    <BLANKLINE>
    Flow from 'CHP1' to 'Powerline'
    Linear flow parameters
    nominal_value: 9
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0.0}
    negative_gradient: {'ub': [], 'costs': 0.0}
    <BLANKLINE>
    Flow from 'CHP1' to 'Heat Grid'
    Linear flow parameters
    nominal_value: 6
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0.0}
    negative_gradient: {'ub': [], 'costs': 0.0}
    <BLANKLINE>
    """
    bus_dict = {bus.label.name: bus for bus in oemof_busses}
    tessif_busses = list(tessif_busses)

    for chp in chps:
        # dicts being passed to create the transformer
        inputs = dict()
        outputs = dict()
        electrical_output = dict()
        heat_output = dict()
        conversion_factors = dict()
        cffc = dict()

        # temp dict for translating tessif's conversions to oemof's
        oemof_conversions = {}
        oemof_cffc = {}
        if chp.conversions:
            oemof_conversions = _to_oemof_conversions(chp.conversions)
        if chp.conversion_factor_full_condensation:
            oemof_cffc = _to_oemof_conversions(
                chp.conversion_factor_full_condensation)
        for bus in tessif_busses:
            for input_ in chp.inputs:
                bus_id = '.'.join([chp.uid.name, input_])
                if bus_id in bus.outputs:

                    # parse conversion factor if applicable:
                    if input_ in oemof_conversions:
                        conversion_factors[
                            bus_dict[bus.uid.name]] = oemof_conversions[input_]

                    # parse input flow (oemof flows are keyed to objects!)
                    inputs[bus_dict[bus.uid.name]] = solph.Flow(
                        **_parse_oemof_flow_parameters(chp, input_)
                    )

            for output in chp.outputs:
                bus_id = '.'.join([chp.uid.name, output])
                if bus_id in bus.inputs:

                    # parse conversion factor if applicable:
                    if output in oemof_conversions:
                        conversion_factors[
                            bus_dict[bus.uid.name]] = oemof_conversions[output]

                    # parse conversion factor for full condensation if
                    # applicable:
                    if output in oemof_cffc:
                        cffc[bus_dict[bus.uid.name]] = oemof_cffc[
                            output]

                    # parse input flow (oemof flows are keyed to objects!)
                    outputs[bus_dict[bus.uid.name]] = solph.Flow(
                        **_parse_oemof_flow_parameters(chp, output))

                    # Split the outputs into electrical and heat outputs.
                    if any(variation in output
                           for variation in spellings.power):
                        electrical_output[bus_dict[bus.uid.name]] = solph.Flow(
                            **_parse_oemof_flow_parameters(chp, output))
                    if any(variation in output
                           for variation in spellings.heat):
                        heat_output[bus_dict[bus.uid.name]] = solph.Flow(
                            **_parse_oemof_flow_parameters(chp, output))

        # Decide which oemof component to use depending on the given properties
        if len(chp.conversion_factor_full_condensation) > 0 and len(
                chp.conversions) == 0:
            warn("'%s' will be ignored. Has unsupported combination of"
                 " parameters." % chp.uid.name)
        elif len(chp.conversion_factor_full_condensation) > 0:
            yield solph.ExtractionTurbineCHP(
                label=nts.Uid(*chp.uid),
                inputs=inputs,
                outputs=outputs,
                conversion_factors=conversion_factors,
                conversion_factor_full_condensation=cffc)
        elif len(chp.conversions) == 0:
            yield solph.GenericCHP(
                label=nts.Uid(*chp.uid),
                fuel_input=inputs,
                electrical_output=electrical_output,
                heat_output=heat_output,
                Beta=chp.power_loss_index,
                back_pressure=chp.back_pressure,
            )
        else:
            yield solph.Transformer(
                label=nts.Uid(*chp.uid),
                outputs=outputs,
                inputs=inputs,
                conversion_factors=conversion_factors)


def generate_oemof_links(links, tessif_busses, oemof_busses):
    """
    Generates oemof links out of tessif links.

    Parameters
    ----------
    links: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Link` objects that are to
        be transformed into :class:`oemof.solph.custom.link.Link` objects.

    tessif_busses: ~collections.abc.Iterable
        Collection of :class:`tessif.model.components.Bus` objects present
        in the same energy system as :paramref:`~generate_oemof_links.links`.

        Used for figuring out connections.

    oemof_busses: ~collections.abc.Iterable
        Iterable of :class:`oemof.solph.network.bus.Bus` objects present in the
        same energy  system as :paramref:`~generate_oemof_links.links`.

        Used for fiuring out connections


    Return
    ------
    generated_links :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`link objects
        <oemof.solph.custom.link.Link>`.

    Examples
    --------
    Creating a small energy system:

    >>> # utilize example hub for accessing a parameterized energy system
    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_fpwe()
    """

    bus_dict = {bus.label.name: bus for bus in oemof_busses}
    tessif_busses = list(tessif_busses)

    for link in links:
        # dicts being passed to create the link
        inputs = dict()
        outputs = dict()
        conversion_factors = dict()

        # iterate through all tessif busses to figure out connection uid
        for bus in tessif_busses:

            # iterate through all link inputs...
            for input_ in link.inputs:

                # .. to match input string and bus uid
                if input_ in str(bus.uid):

                    # parse conversion factor:
                    # order of busses vary depending on user input...
                    for bus_tuple, conv_factor in link.conversions.items():
                        # .. to parse conversion factors in the right order
                        # check if current input uid (= the bus uid) matches
                        # the FIRST tuple entry
                        if str(bus.uid) == str(bus_tuple[0]):

                            # the resulting tuple key is constructed by taking
                            # the first input uid as first entry and the output
                            # uid (the one left in the conversion factors bus
                            # tuple) as second entry
                            t = (bus_dict[bus.uid.name],
                                 bus_dict[bus_tuple[1]])
                            conversion_factors[t] = conv_factor

                    # parse input flow (oemof flows are keyed to objects!)
                    inputs[bus_dict[bus.uid.name]] = solph.Flow()
                    # **_parse_oemof_flow_parameters(link, input_))

            # to the same for outputs as for the inputs (see comments there)...
            for output in link.outputs:

                if output in str(bus.uid):
                    # but leave out the conversion factor parsing since each
                    # connecting bus will serve as input (and hence gets
                    # iterated over using the inputs)

                    # parse input flow (oemof flows are keyed to objects!)
                    outputs[bus_dict[bus.uid.name]] = solph.Flow()
                    #  **_parse_oemof_flow_parameters(link, output) )

        yield solph.custom.Link(
            label=nts.Uid(*link.uid),
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors,
        )


def generate_oemof_sinks(sinks, tessif_busses, oemof_busses):
    """
    Generates oemof sinks out of tessif sinks.

    Parameters
    ----------
    sinks: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Sink` objects that are to
        be transformed into :class:`oemof.solph.network.sink.Sink` objects.

    tessif_busses: ~collections.abc.Iterable
        Collection of :class:`tessif.model.components.Bus` objects present
        in the same energy system as :paramref:`~generate_oemof_sinks.sinks`.

        Used for figuring out connections.

    oemof_busses: ~collections.abc.Iterable
        Iterable of :class:`oemof.solph.network.bus.Bus` objects present in the
        same energy system as :paramref:`~generate_oemof_sinks.sinks`.

        Used for fiuring out connections

    Return
    ------
    generated_sinks :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`sink objects
        <oemof.solph.network.bus.Bus>`.

    Examples
    --------
    >>> # utilize example hub for accessing a parameterized energy system
    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_fpwe()

    >>> # generate the sinks:
    >>> sink = list(generate_oemof_sinks(
    ...     sinks=es.sinks,
    ...     tessif_busses=es.busses,
    ...     oemof_busses=generate_oemof_busses(es.busses)))[0]

    >>> print(sink.label)
    Demand

    >>> linear_flow_params = (
    ...     'nominal_value', 'summed_min', 'summed_max',
    ...     'min', 'max', 'positive_gradient', 'negative_gradient')

    >>> for flow in sink.inputs.values():
    ...     print('Linear flow parameters:')
    ...     for attr in linear_flow_params:
    ...         print('{}:'.format(attr), getattr(flow, attr))
    Linear flow parameters:
    nominal_value: 11
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0}
    negative_gradient: {'ub': [], 'costs': 0}
    """
    bus_dict = {bus.label.name: bus for bus in oemof_busses}
    tessif_busses = list(tessif_busses)

    for sink in sinks:
        inputs = dict()
        for bus in tessif_busses:
            for input_ in sink.inputs:
                bus_id = '.'.join([sink.uid.name, input_])
                if bus_id in bus.outputs:
                    inputs[bus_dict[bus.uid.name]] = solph.Flow(
                        **_parse_oemof_flow_parameters(sink, input_)
                    )

        yield solph.Sink(
            label=nts.Uid(*sink.uid),
            inputs=inputs)


def generate_oemof_sources(sources, tessif_busses, oemof_busses):
    """
    Generates oemof sources out of tessif sources.

    Parameters
    ----------
    sources: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Source` objects that are to
        be transformed into :class:`oemof.solph.network.source.Source` objects.

    tessif_busses: ~collections.abc.Iterable
        Collection of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~generate_oemof_sources.sources`.

        Used for figuring out connections.

    oemof_busses: ~collections.abc.Iterable
        Iterable of :class:`oemof.solph.network.bus.Bus` objects present in the
        same energy system as :paramref:`~generate_oemof_sources.sources`.

        Used for fiuring out connections

    Return
    ------
    generated_sources :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`source objects
        <oemof.solph.network.bus.Bus>`.

    Examples
    --------
    >>> # utilize example hub for accessing a parameterized energy system
    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_fpwe()

    >>> # generate the sources:
    >>> source = list(generate_oemof_sources(
    ...     sources=es.sources,
    ...     tessif_busses=es.busses,
    ...     oemof_busses=generate_oemof_busses(es.busses)))[0]

    >>> print(source.label)
    Gas Station

    >>> linear_flow_params = (
    ...     'nominal_value', 'summed_min', 'summed_max',
    ...     'min', 'max', 'positive_gradient', 'negative_gradient')

    >>> for flow in source.outputs.values():
    ...     print('Linear flow parameters:')
    ...     for attr in linear_flow_params:
    ...         print('{}:'.format(attr), getattr(flow, attr))
    Linear flow parameters:
    nominal_value: 100
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0}
    negative_gradient: {'ub': [], 'costs': 0}
    """
    bus_dict = {bus.label.name: bus for bus in oemof_busses}

    tessif_busses = list(tessif_busses)
    for source in sources:
        outputs = dict()
        for bus in tessif_busses:
            for output in source.outputs:

                # reconstruct the connecting bus id...
                bus_id = '.'.join([source.uid.name, output])

                # and check if it is an existing one by comparing it to all
                # bus inputs
                if bus_id in bus.inputs:
                    outputs[bus_dict[bus.uid.name]] = solph.Flow(
                        **_parse_oemof_flow_parameters(source, output)
                    )

        yield solph.Source(
            label=nts.Uid(*source.uid),
            outputs=outputs)


def generate_oemof_storages(storages, tessif_busses, oemof_busses):
    """
    Generates oemof storages out of tessif storages.

    Parameters
    ----------
    storages: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Storage` objects that
        are to be transformed into :class:`oemof.solph.network.storage.Storage`
        objects.

    tessif_busses: ~collections.abc.Iterable
        Collection of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~generate_oemof_storages.storages`.

        Used for figuring out connections.

    oemof_busses: ~collections.abc.Iterable
        Iterable of :class:`oemof.solph.network.bus.Bus` objects present in the
        same energy system as :paramref:`~generate_oemof_storages.storages`.

        Used for fiuring out connections.

    Return
    ------
    generated_storages :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`storage objects
        <oemof.solph.network.bus.Bus>`.

    Examples
    --------
    >>> # utilize example hub for accessing a parameterized energy system
    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_fpwe()

    >>> # generate the storages:
    >>> storage = list(generate_oemof_storages(
    ...     storages=es.storages,
    ...     tessif_busses=es.busses,
    ...     oemof_busses=generate_oemof_busses(es.busses)))[0]

    Storage Uid:

    >>> print(storage.label)
    Battery

    Storage in and outflow efficiencies:

    >>> print('inflow:', storage.inflow_conversion_factor[12371293])
    inflow: 1

    >>> print('outflow:', storage.inflow_conversion_factor[107088076])
    outflow: 1

    Idle Changes:

    >>> print(storage.loss_rate[12371203])
    0.1

    Initial State Of Charge:

    >>> print(storage.initial_storage_level)
    1.0

    Flows:

    >>> linear_flow_params = (
    ...     'nominal_value', 'summed_min', 'summed_max', 'min', 'max',
    ...     'positive_gradient', 'negative_gradient', 'variable_costs',
    ...     'emissions',)

    >>> for flow in list(
    ...     storage.inputs.values())+list(storage.outputs.values()):
    ...     print("Flow from '{}' to '{}'".format(
    ...         flow.label.input, flow.label.output))
    ...     print('Linear flow parameters')
    ...     for attr in linear_flow_params:
    ...         print('{}:'.format(attr), getattr(flow, attr))
    Flow from 'Powerline' to 'Battery'
    Linear flow parameters
    nominal_value: 30
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0}
    negative_gradient: {'ub': [], 'costs': 0}
    variable_costs: []
    emissions: 0
    Flow from 'Battery' to 'Powerline'
    Linear flow parameters
    nominal_value: 30
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0}
    negative_gradient: {'ub': [], 'costs': 0}
    variable_costs: []
    emissions: 0
    """
    bus_dict = {bus.label.name: bus for bus in oemof_busses}
    tessif_busses = list(tessif_busses)

    for storage in storages:
        # dicts being passed to create the storage
        inputs = dict()
        outputs = dict()
        outflow_conversion_factor = {}

        for bus in tessif_busses:

            inp = storage.input
            bus_id = '.'.join([storage.uid.name, inp])
            if bus_id in bus.outputs:

                # parse inflow efficiency
                inflow_conversion_factor = storage.flow_efficiencies[
                    inp].inflow

                # parse input flow
                inflow_parameters = _parse_oemof_flow_parameters(storage, inp)

                # reset emission and costs, so they are attributed only
                # to the outflow
                inflow_parameters['emissions'] = 0
                inflow_parameters['variable_costs'] = 0

                inflow = solph.Flow(**inflow_parameters)

                # (oemof flows are keyed to objects!)
                inputs[bus_dict[bus.uid.name]] = inflow

            output = storage.output
            bus_id = '.'.join([storage.uid.name, output])
            if bus_id in bus.inputs:
                # parse inflow efficiency
                outflow_conversion_factor = storage.flow_efficiencies[
                    output].outflow

                # parse input flow (oemof flows are keyed to objects!)
                outputs[bus_dict[bus.uid.name]] = solph.Flow(
                    **_parse_oemof_flow_parameters(storage, output)
                )

        # compare initial and final soc
        balanced = False
        if storage.final_soc is not None:
            if storage.initial_soc == storage.final_soc:
                balanced = True

        if storage.capacity != 0:
            # normalize loss rate and initial state of charge
            initial_storage_level = storage.initial_soc / storage.capacity
            loss_rate = (storage.idle_changes.negative -
                         storage.idle_changes.positive)/storage.capacity
        else:
            initial_storage_level = 0
            loss_rate = 0

        # Initialize default "capacity" Investment (expansion problem)
        if storage.expandable['capacity']:

            max_expansion = storage.expansion_limits[
                'capacity'].max - storage.capacity

            min_expansion = storage.expansion_limits[
                'capacity'].min - storage.capacity

            if max_expansion < 0:
                msg = (
                    "Requested maximum expansion limit of " +
                    f"'{storage.expansion_limits['capacity'].max}' of storage "
                    f"'{storage.uid.name}' is below current installed "
                    f"capacity of '{storage.capacity}' Falling back on "
                    "current installed capacity as maximum Therefore adding 0 "
                    "additional capacity."
                )
                logger.warning(msg)
                max_expansion = 0.0

            elif max_expansion == float('+inf'):
                # oemofs inf expansion == None
                max_expansion = None

            if min_expansion < 0:
                msg = (
                    "Requested minimum expansion limit of " +
                    f"'{storage.expansion_limits['capacity'].min}' of storage "
                    f"'{storage.uid.name}' is below current installed "
                    f"capacity of '{storage.capacity}' Falling back on 0.0 as "
                    "minimum additionally installed capacity."
                )
                logger.warning(msg)
                min_expansion = 0.0

            capacity_investment = solph.Investment(
                ep_costs=storage.expansion_costs['capacity'],
                existing=storage.capacity,
                minimum=min_expansion,
                maximum=max_expansion
            )

            nominal_storage_capacity = None

            # check for fixed capacty/outflow relation
            if storage.fixed_expansion_ratios[f'{storage.output}']:
                if storage.capacity != 0:
                    output_capacity_relation = storage.flow_rates[
                        f'{storage.output}'].max / storage.capacity

                else:
                    msg = (
                        f"Storage '{storage.uid.name}' is requested to have "
                        f"an initial capacity of '{storage.capacity}' as "
                        "well as a fixed output expansion ratio. "
                        "falling back to an unfixed ratio, to allow "
                        "succesful optimization."
                    )

                    logger.warning(msg)
                    output_capacity_relation = None
            else:
                output_capacity_relation = None

            if storage.fixed_expansion_ratios[f'{storage.input}']:
                if storage.capacity != 0:
                    input_capacity_relation = storage.flow_rates[
                        f'{storage.input}'].max / storage.capacity

                else:
                    msg = (
                        f"Storage '{storage.uid.name}' is requested to have "
                        f"an initial capacity of '{storage.capacity}' as "
                        "well as a fixed input expansion ratio. "
                        "falling back to an unfixed ratio, to allow "
                        "succesful optimization."
                    )

                    logger.warning(msg)
                    input_capacity_relation = None
            else:
                input_capacity_relation = None

        else:
            capacity_investment = None
            nominal_storage_capacity = storage.capacity
            input_capacity_relation = None
            output_capacity_relation = None

        storage = solph.components.GenericStorage(
            label=nts.Uid(*storage.uid),
            nominal_storage_capacity=nominal_storage_capacity,
            inputs=inputs,
            outputs=outputs,
            loss_rate=loss_rate,
            initial_storage_level=initial_storage_level,
            inflow_conversion_factor=inflow_conversion_factor,
            outflow_conversion_factor=outflow_conversion_factor,
            balanced=balanced,
            investment=capacity_investment,
            invest_relation_input_capacity=input_capacity_relation,
            invest_relation_output_capacity=output_capacity_relation,
        )

        # todo: overhaul logging concept
        # create a logging entry when overhauling the logging concept
        # print()
        # print(79*'#')
        # print('cap:', storage.nominal_storage_capacity)
        # print('loss rate:', storage.loss_rate[0])
        # print('init soc:', storage.initial_storage_level)
        # print('out_conv:', storage.outflow_conversion_factor[0])
        # print('in_conv:', storage.inflow_conversion_factor[0])
        # print('balanced:', storage.balanced)
        # if capacity_investment:
        #     print('min_inv:', capacity_investment.minimum)
        #     print('max_inv:', capacity_investment.maximum)
        #     print('existing:', capacity_investment.existing)
        #     print('costs:', capacity_investment.ep_costs)

        # print('input_capacity_relation:', input_capacity_relation)
        # print('output_capacity_relation:', output_capacity_relation)
        # print(79*'#')
        # print()

        yield storage


def generate_oemof_transformers(transformers, tessif_busses, oemof_busses):
    """
    Generates oemof transformers out of tessif transformers.

    Parameters
    ----------
    transformers: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Transformer` objects that
        are to be transformed into :class:`oemof.solph.network.transformer.Transformer`
        objects.

    tessif_busses: ~collections.abc.Iterable
        Collection of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~generate_oemof_transformers.transformers`.

        Used for figuring out connections.

    oemof_busses: ~collections.abc.Iterable
        Iterable of :class:`oemof.solph.network.bus.Bus` objects present in the
        same energy system as
        :paramref:`~generate_oemof_transformers.transformers`.

        Used for figuring out connections.

    Return
    ------
    generated_transformers :class:`~collections.abc.Generator`
        Generator object yielding the transformed :class:`transformer objects
        <oemof.solph.network.bus.Bus>`.

    Examples
    --------
    >>> # utilize example hub for accessing a parameterized energy system
    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_fpwe()

    >>> # generate the transformers:
    >>> transformer = list(generate_oemof_transformers(
    ...     transformers=es.transformers,
    ...     tessif_busses=es.busses,
    ...     oemof_busses=generate_oemof_busses(es.busses)))[0]

    Label:

    >>> print(transformer.label)
    Generator

    Conversion Factors:

    >>> for key, value in transformer.conversion_factors.items():
    ...     print('{}: {}'.format(key, value[123123]))
    Powerline: 0.42
    Pipeline: 1

    >>> linear_flow_params = (
    ...     'nominal_value', 'summed_min', 'summed_max',
    ...     'min', 'max', 'positive_gradient', 'negative_gradient')

    >>> for flow in list(
    ...     transformer.inputs.values())+list(transformer.outputs.values()):
    ...     print("Flow from '{}' to '{}'".format(
    ...         flow.label.input, flow.label.output))
    ...     print('Linear flow parameters')
    ...     for attr in linear_flow_params:
    ...         print('{}:'.format(attr), getattr(flow, attr))
    ...     print()
    Flow from 'Pipeline' to 'Generator'
    Linear flow parameters
    nominal_value: 50
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0}
    negative_gradient: {'ub': [], 'costs': 0}
    <BLANKLINE>
    Flow from 'Generator' to 'Powerline'
    Linear flow parameters
    nominal_value: 15
    summed_min: None
    summed_max: None
    min: []
    max: []
    positive_gradient: {'ub': [], 'costs': 0}
    negative_gradient: {'ub': [], 'costs': 0}
    <BLANKLINE>
    """
    bus_dict = {bus.label.name: bus for bus in oemof_busses}
    tessif_busses = list(tessif_busses)

    for transformer in transformers:
        # dicts being passed to create the transformer
        inputs = dict()
        outputs = dict()
        conversion_factors = dict()

        # temp dict for translating tessif's conversions to oemof's
        oemof_conversions = _to_oemof_conversions(transformer.conversions)
        for bus in tessif_busses:
            for input_ in transformer.inputs:
                bus_id = '.'.join([transformer.uid.name, input_])
                if bus_id in bus.outputs:

                    # parse conversion factor if applicable:
                    if input_ in oemof_conversions:
                        conversion_factors[
                            bus_dict[bus.uid.name]] = oemof_conversions[input_]

                    # parse input flow (oemof flows are keyed to objects!)
                    inputs[bus_dict[bus.uid.name]] = solph.Flow(
                        **_parse_oemof_flow_parameters(transformer, input_)
                    )

            for output in transformer.outputs:
                bus_id = '.'.join([transformer.uid.name, output])
                if bus_id in bus.inputs:
                    # parse conversion factor if applicable:
                    if output in oemof_conversions:
                        conversion_factors[
                            bus_dict[bus.uid.name]] = oemof_conversions[output]

                    # parse input flow (oemof flows are keyed to objects!)
                    outputs[bus_dict[bus.uid.name]] = solph.Flow(
                        **_parse_oemof_flow_parameters(transformer, output))

        yield solph.Transformer(
            label=nts.Uid(*transformer.uid),
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors)


def transform(tessif_es, **kwargs):
    """
    Transform a tessif energy system into an oemof energy system.

    Parameters
    ----------
    tessif_es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        The tessif energy system that is to be transformed into an
        oemof energy system.

    Return
    ------
    oemof_es: :class:`oemof.solph.network.energy_system.EnergySystem`
        The oemof energy system that was transformed out of the tessif
        energy system.

    Examples
    --------
    Use the :ref:`example hub's <Examples>`
    :meth:`~tessif.examples.data.tsf.py_hard.create_mwe` utility for showcasing
    basic usage:

    1. Create the mwe:

        >>> from tessif.examples.data.tsf.py_hard import create_mwe
        >>> tessif_es = create_mwe()

    2. Transform the :mod:`tessif energy system
       <tessif.model.energy_system.AbstractEnergySystem>`:

        >>> oemof_es = transform(tessif_es)

    3. Show node labels using the :attr:`oemof interface
       <oemof.network.Node.label>` as well as :mod:`tessif's uid concept
       <tessif.frused.namedtuples.Uid>`:

        >>> for node in oemof_es.nodes:
        ...     print(node.label.name)
        Pipeline
        Powerline
        Gas Station
        Demand
        Generator
        Battery

    4. Simulate the oemof energy system:

        >>> import tessif.simulate as simulate
        >>> optimized_oemof_es = simulate.omf_from_es(oemof_es)

    5. Extract some results:

        >>> import tessif.transform.es2mapping.omf as transform_oemof_results
        >>> load_results = transform_oemof_results.LoadResultier(
        ...     optimized_oemof_es)
        >>> print(load_results.node_load['Powerline'])
        Powerline            Battery  Generator  Battery  Demand
        1990-07-13 00:00:00    -10.0       -0.0      0.0    10.0
        1990-07-13 01:00:00     -0.0      -10.0      0.0    10.0
        1990-07-13 02:00:00     -0.0      -10.0      0.0    10.0
        1990-07-13 03:00:00     -0.0      -10.0      0.0    10.0

    |

    **A slightly more advanced example:**

    >>> from tessif.examples.data.tsf.py_hard import create_fpwe
    >>> tessif_es = create_fpwe()
    >>> oemof_es = transform(tessif_es)
    >>> optimized_oemof_es = simulate.omf_from_es(oemof_es)
    >>> load_results = transform_oemof_results.LoadResultier(
    ...     optimized_oemof_es)
    >>> print(load_results.node_load['Powerline'])
    Powerline            Battery  Generator  Solar Panel  Battery  Demand
    1990-07-13 00:00:00     -0.0       -0.0        -12.0      1.0    11.0
    1990-07-13 01:00:00     -8.0       -0.0         -3.0      0.0    11.0
    1990-07-13 02:00:00     -0.9       -3.1         -7.0      0.0    11.0
    """

    oemof_busses = list(generate_oemof_busses(tessif_es.busses))

    energy_system_components = list()
    energy_system_components.extend(oemof_busses)

    for link in generate_oemof_links(
            links=tessif_es.connectors,
            tessif_busses=tessif_es.busses,
            oemof_busses=oemof_busses):
        energy_system_components.append(link)

    for source in generate_oemof_sources(
            sources=tessif_es.sources,
            tessif_busses=tessif_es.busses,
            oemof_busses=oemof_busses):
        energy_system_components.append(source)

    # add sink to the energy system nodes
    # (e.g. demands, excess nodes, exports, ...)

    for sink in generate_oemof_sinks(
            sinks=tessif_es.sinks,
            tessif_busses=tessif_es.busses,
            oemof_busses=oemof_busses):
        energy_system_components.append(sink)

    # add multiple input multiple output transformers
    for transformer in generate_oemof_transformers(
            transformers=tessif_es.transformers,
            tessif_busses=tessif_es.busses,
            oemof_busses=oemof_busses):
        energy_system_components.append(transformer)

    # add single input two outputs generic chps and extraction turbine chps
    for chp in generate_oemof_chps(
            chps=tessif_es.chps,
            tessif_busses=tessif_es.busses,
            oemof_busses=oemof_busses):
        energy_system_components.append(chp)

    # # add single input two outputs sito flex transformers
    # for sito_flex_transformer in generate_sito_flex_transformers(
    #         es_object_types, bus_dict):
    #     es_nodes.append(sito_flex_transformer)

    # # add single input single output offset transformers
    # for transformer in generate_siso_nonlinear_transformers(
    #         es_object_types, bus_dict):
    #     es_nodes.append(transformer)

    # add generic storages
    for storage in generate_oemof_storages(
            storages=tessif_es.storages,
            tessif_busses=tessif_es.busses,
            oemof_busses=oemof_busses):
        energy_system_components.append(storage)

    energy_system = solph.EnergySystem(timeindex=tessif_es.timeframe)
    energy_system.add(*energy_system_components, **kwargs)

    # add global constraints (no parsing here, since oemof allocates global
    # constraints to the underlying solver model exclusively)
    energy_system.global_constraints = tessif_es.global_constraints

    return energy_system
