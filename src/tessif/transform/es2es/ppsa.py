# tessif/transform/es2es/pypsa.py
"""
:mod:`tessif.transform.es2es.ppsa` is a :mod:`tessif` module aggregating all
the functionality for automatically transforming a :class:`tessif energy system
<tessif.model.energy_system.AbstractEnergySystem>` into a
:class:`pypsa energy system <pypsa.Network>`.
"""

import collections
import logging
import numbers

import numpy as np
import pandas as pd
import pypsa


from tessif.frused.spellings import (
    connector,
    combined_heat_power,
    heat_plant,
    power_plant,
    power2x,
    power2heat,
    flow_emissions as spellings_flow_emissions,
)
import tessif.frused.hooks.ppsa as pypsa_hooks

logger = logging.getLogger(__name__)


def infer_pypsa_transformer_types(tessif_transformers, forced_links=None):
    """
    Utility to infer how tessif transformers should be transformed into pypsa
    components.

    :class:`Tessif transformers <tessif.model.components.Transformer>`
    can have singular or multiple outputs and therefor be both:

        - `Pypsa links
          <https://pypsa.readthedocs.io/en/latest/components.html#link>`_
          (if #(outputs) > 1)
        - `Pypsa generators
          <https://pypsa.readthedocs.io/en/latest/components.html#generator>`_
          (if #(inputs) == #(outputs) == 1)

    For a tessif transformer being transformed into a pypsa link, **one** of
    the following has to be true:

        - :paramref:`Transformer.node_type
          <tessif.model.components.Transformer.node_type>` is found inside
          :attr:`tessif.frused.spellings.combined_heat_power`

        - number of :attr:`Transformer.outputs
          <tessif.model.components.Transformer.outputs>` > 1

    On the other hand, for a tessif transformer beeing transformed into a
    pypsa generator, **one** of the following has to be true:

        - :paramref:`Transformer.node_type
          <tessif.model.components.Transformer.node_type>` is found inside
          :attr:`tessif.frused.spellings.power_plant` or inside
          :attr:`tessif.frused.spellings.heat_plant`.

        - number of :attr:`Transformer.outputs
          <tessif.model.components.Transformer.outputs>` equals
          number of :attr:`Transformer.inputs
          <tessif.model.components.Transformer.outputs>` equals
          1.

    Parameters
    ----------
    tessif_transformers: ~collections.abc.Iterable
        Iterable of tessif transformers of which the appropriate
        transformation type is to be inferred.
    forced_links: ~collections.abc.Container, None, default=None
        Container of :ref:`uid representations <Labeling_Concept>` of
        :class:`tessif transformers <tessif.model.components.Transformer>`
        to be transfrormed into `pypsa links
        <https://pypsa.readthedocs.io/en/latest/components.html#link>`_.

    Return
    ------
    inferred_transformers: dict
        Mapping of :class:`Tessif transformer
        <tessif.model.components.Transformer>` uids keyed either by
        ``links`` or by ``generators``

    Examples
    --------
    Use the :ref:`example hub's <Examples>`
    :mod:`~tessif.examples.data.tsf.py_hard` data base for showcasing
    basic usage:

    1. Using the mwe:

        >>> from tessif.examples.data.tsf.py_hard import create_mwe

        >>> tessif_es = create_mwe()
        >>> iptts = infer_pypsa_transformer_types(tessif_es.transformers)
        >>> for i, (key, transformer_uids) in enumerate(iptts.items()):
        ...     if i > 0:
        ...         print()
        ...     print(f'{key}:')
        ...     print(10*'-')
        ...     for uid in transformer_uids:
        ...         print(uid)
        generators:
        ----------
        Generator
        <BLANKLINE>
        links:
        ----------

    """
    # make forced links iterable:
    if forced_links is None:
        forced_links = tuple()

    # create appropriate containers
    inferred_transformers = {
        'generators': list(),
        'links': list(),
    }

    # seperate links and generators
    for transformer in tessif_transformers:
        # links
        if (
                str(transformer.uid) in forced_links
                or transformer.uid.node_type in [
                    *combined_heat_power, *connector]
                or len(transformer.outputs) > 1
                or transformer.uid.name in [
                    *power2x,
                    *power2heat,
                ]
        ):
            inferred_transformers['links'].append(transformer.uid)

        # generators
        elif (
                transformer.uid.node_type in [*power_plant, *heat_plant] or
                (
                    len(transformer.outputs) == 1 and
                    len(transformer.inputs) == 1
                )
        ):
            inferred_transformers['generators'].append(transformer.uid)

    return inferred_transformers


def compute_unneeded_supply_chains(tessif_es, pypsa_generator_uids):
    """
    Utility to compute unneeded tessif components uids.

    Due to transforming certain :class:`tessif transformers
    <tessif.model.components.Transformer>`  into `pypsa generators
    <https://pypsa.readthedocs.io/en/stable/components.html#generator>`__
    corresponding supply chains (usually a :class:`tessif bus
    <tessif.model.components.Bus>` and a :class:`tessif source
    <tessif.model.components.Source>`) are not needed and hence need to be
    removed, to allow succesfull optimization.

    Parameters
    ----------
    tessif_es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        The tessif energy system of which the :paramref:`generator
        <pypsa_generator_uids>` supply chains are to be removed.

    pypsa_generator_uids: ~collections.abc.Iterable
        Iterable of :class:`tessif transformers
        <tessif.model.components.Transformer>` of which the corresponding
        supply chains need to be removed.
        Returned by :func:`infer_pypsa_transformer_types` ['generators'] by
        design.

    Return
    ------
    components_to_remove: dict
        Dictionairy of componend uid lists keyed by pypsa component type of
        components which are to be removed.

    Example
    --------
    Use the :ref:`example hub's <Examples>`
    :mod:`~tessif.examples.data.tsf.py_hard` data base for showcasing
    basic usage:

    1. Using the mwe:

        >>> from tessif.examples.data.tsf.py_hard import create_mwe

        >>> tessif_es = create_mwe()
        >>> gens = infer_pypsa_transformer_types(
        ...     tessif_es.transformers)['generators']

        >>> ctrs = compute_unneeded_supply_chains(
        ...     tessif_es=tessif_es,
        ...     pypsa_generator_uids=gens,
        ... )
        >>> for comp_type, components_to_remove in ctrs.items():
        ...     if comp_type != 'supply_chains':
        ...         print(f'{comp_type}: {components_to_remove}')
        Bus: ['Pipeline']
        Generator: ['Gas Station']
    """
    busses_to_remove, components_to_remove = list(), list()
    supply_chains = collections.defaultdict(list)

    # Create a list of busses, that are to be removed
    for transformer in tessif_es.transformers:
        if transformer.uid in pypsa_generator_uids:

            # iterate through all transformer inputs to get all connecting
            # busses
            for inbound in transformer.inputs:
                # Busses To Remove = btrs
                btrs = list()

                # iterate through all tessif busses
                for bus in tessif_es.busses:

                    # to find the generator to be removed input:
                    if any([outbound == f'{transformer.uid.name}.{inbound}'
                            for outbound in bus.outputs]):

                        # and then check whether the bus from which this input
                        # comes only feeds transformer that are to be
                        # generators
                        incoming_bus_outbounds = [
                            outbound.split('.')[0]
                            for outbound in bus.outputs]

                        generators_to_remove = [
                            uid.name for uid in pypsa_generator_uids]

                        # print(79*'-')
                        # print(bus.uid.name)
                        # print([outbound.split('.')[0]
                        #        for outbound in bus.outputs])
                        # print([uid.name for uid in pypsa_generator_uids])
                        # print(79*'-')

                        # if (
                        #         len(bus.outputs) == 1 and
                        #         len(bus.inputs) == 1
                        # ):

                        if all([bus_outbound in generators_to_remove
                                for bus_outbound in incoming_bus_outbounds]):

                            if bus not in busses_to_remove:
                                btrs.append(bus)

                busses_to_remove.extend(btrs)
                supply_chains[transformer.uid].extend(btrs)

                # iterate through all supplying busses to remove subsequent
                # sources
                for bus in btrs:
                    for inbound in bus.inputs:

                        ctrs = [
                            comp for comp in tessif_es.nodes
                            if any([inbound == f'{str(comp.uid)}.{interface}'
                                    for interface in comp.interfaces])
                        ]

                        supply_chains[transformer.uid].extend(ctrs)

    # Add all of the busses inputs to the components that are to be removed:
    for bus in busses_to_remove:
        # Components To Remove = ctrs
        for inbound in bus.inputs:

            ctrs = [
                comp for comp in tessif_es.nodes
                if any([inbound == f'{comp.uid.name}.{interface}'
                        for interface in comp.interfaces])
            ]
            components_to_remove.extend(ctrs)

    components_to_remove = {
        'Bus': [str(bus.uid) for bus in busses_to_remove],
        'Generator': [str(gen.uid) for gen in components_to_remove],
        'supply_chains': supply_chains,
    }

    return components_to_remove


def parse_flow_parameters(component, interface):
    """
    Utility to parse flow related parameters from :mod:`Tessif components
    <tessif.model.components>` to `Pypsa components
    <https://pypsa.readthedocs.io/en/latest/components.html>`_

    Parameters
    ----------
    component: :class:`tessif.model.components.AbstractEsComponent`
        Tessif component of which it's flow related parameters are parsed
        into pypsa recognizable parameters
    interface: str
        String representing the flow related interface from the components
        point of view. One of the components
        :attr:`~tessif.model.components.AbstractEsComponent.interfaces`.

    Return
    ------
    parsed_flow_parameters: dict
        Dictionairy representing the parsed flow parameters ready to be used
        as key word arguments for creating pypsa components.

    Raises
    ------
    ValueError:
        A value error is raised in case a nominal_value (max flow_rate value)
        is requested to be infinit AND in addition to milp parameters.

        This is due to the fact that an infinit nominal value is parsed into an
        expansion problem because pypsa can not deal with infinity values.
        Which in turn causes conflicts in dealing with milp parameters.

    Examples
    --------

    Parsing an fpwe component:

        >>> import tessif.examples.data.tsf.py_hard as coded_tsf_examples
        >>> fpwe = coded_tsf_examples.create_fpwe()
        >>> parsed_fps = parse_flow_parameters(
        ...     component=list(fpwe.transformers)[0],
        ...     interface='electricity',
        ... )
        >>> for attr, value in parsed_fps.items():
        ...    print(f"{attr} = {value}")
        p_nom = 15
        p_min_pu = 0.0
        p_max_pu = 1.0
        marginal_cost = 10

    Parsing an infinit value into an expansion problem:

        >>> import tessif.model.components as tcomps
        >>> tsf_infinity_source = tcomps.Source(
        ...     name='infinity',
        ...     outputs=('electricity',),
        ...     flow_rates={'electricity': (0, float('+inf'))},
        ...     flow_costs={'electricity': 0},
        ... )
        >>> parsed_fps = parse_flow_parameters(
        ...     component=tsf_infinity_source,
        ...     interface='electricity',
        ... )
        >>> for attr, value in parsed_fps.items():
        ...    print(f"{attr} = {value}")
        marginal_cost = 0
        p_nom = 0.0
        p_nom_min = 0.0
        p_nom_max = inf
        p_nom_extendable = True
        capital_cost = 0
        p_min_pu = 0.0
        p_max_pu = 1.0

    Using an infinit nominal value while also requesting milp parameters:

        >>> import tessif.model.components as tcomps
        >>> tsf_infinity_source = tcomps.Source(
        ...     name='infinity',
        ...     outputs=('electricity',),
        ...     flow_rates={'electricity': (0, float('+inf'))},
        ...     milp={'electricity': True}
        ... )
        >>> try:
        ...     parsed_fps = parse_flow_parameters(
        ...         component=tsf_infinity_source,
        ...         interface='electricity',
        ...     )
        ... except ValueError as e:
        ...     print(e)
        Pypsa cannot handle infinity nominal value and milp
        constraints at the same time for a singular flow.

    """
    # pypsa interprets many parameters as normalized to the nominal
    # value
    nominal_value = component.flow_rates[interface].max
    if isinstance(nominal_value, collections.abc.Iterable):
        nominal_value = max(nominal_value)

    # linear constraints
    flow_params = dict()
    if nominal_value != float('inf'):
        # infinity values are handled below
        flow_params['p_nom'] = nominal_value

        if nominal_value != 0:

            flow_params['p_min_pu'] = component.flow_rates[
                interface].min / nominal_value
            flow_params['p_max_pu'] = component.flow_rates[
                interface].max / nominal_value
        else:
            flow_params['p_min_pu'] = 0
            flow_params['p_max_pu'] = 1

    flow_params['marginal_cost'] = component.flow_costs[interface]

    # linear commitment constraints
    if component._milp[interface]:
        flow_params.update(
            {
                'committable': True,
                'start_up_cost': component.status_changing_costs.on,
                'shut_down_cost': component.status_changing_costs.off,
                # 'ramp_limit_start_up': component.flow_gradients[
                #     interface].positive,
                # 'ramp_limit_shut_down': component.flow_gradients[
                #     interface].negative,
                'min_up_time': component.status_inertia.on,
                'min_down_time': component.status_inertia.off,

                # following milp constraints are not supported by pypsa:
                # activity_costs: component.costs_for_being_active,
                # initial_status: component.initial_status,
                # number_of_shutdowns: component.number_of_status_changes[
                #    interface].off
                # number_of_start_ups: component.number_of_status_changes[
                #    interface].on

                # following constraints are not supported by tessif:
                # ramp_limit_start_up
                # ramp_limit_shut_down
                # down_time_before
            }
        )
        # parse gradients (which can be infinite in tessif
        positive_gradient = component.flow_gradients[interface].positive
        if positive_gradient == float('+inf'):
            flow_params['ramp_limit_up'] = 1.0
        else:
            flow_params['ramp_limit_up'] = positive_gradient/nominal_value

        negative_gradient = component.flow_gradients[interface].negative
        if negative_gradient == float('+inf'):
            flow_params['ramp_limit_down'] = 1.0
        else:
            flow_params['ramp_limit_down'] = negative_gradient/nominal_value

        # parse initial status
        if component.initial_status:
            flow_params['up_time_before'] = 1.0
        else:
            flow_params['up_time_before'] = 0.0

    # expansion constraints
    if component.expandable[interface]:
        # expansion and milp/commitment constraints are not compatible
        flow_params['committable'] = False
        flow_params.update(
            {
                'p_nom_extendable': True,
                'p_nom_max': component.expansion_limits[interface].max,
                'p_nom_min': component.expansion_limits[interface].min,
                'capital_cost': component.expansion_costs[interface],
            }
        )

        if component.timeseries is not None:
            if interface in component.timeseries:

                # warn the user in case maximum minimum time series is higher
                # than the minimum expansion, what make ppsa think it can sell
                # the component to make money
                if 'p_nom_min' in flow_params:
                    if flow_params['p_nom_min'] < component.flow_rates[
                            interface].max:
                        msg = (
                            "Minimum stated expansion limit "
                            f"(''{flow_params['p_nom_min']}'') of component "
                            f"''{component.uid.name}'' is lower than the "
                            "maximum stated flow rate value of "
                            f"''{component.flow_rates[interface].max}''."
                            "\n This may lead to pypsa selling the component "
                            "for the stated expansions costs, and hence "
                            "yield quite unpredictable results.\n\n"
                            "To avoid that, explicitly state the minimum and "
                            "maximum expansion limits of this component."
                        )
                        logger.warning(msg)

        elif 'p_nom_min' in flow_params:
            if flow_params['p_nom_min'] < component.flow_rates[interface].max:
                msg = (
                    "Minimum stated expansion limit "
                    f"(''{flow_params['p_nom_min']}'') of component "
                    f"''{component.uid.name}'' is lower than the "
                    "maximum stated flow rate value of "
                    f"''{component.flow_rates[interface].max}''."
                    "\n This may lead to pypsa selling the component "
                    "for the stated expansions costs, and hence "
                    "yield quite unpredictable results.\n\n"
                    "To avoid that, explicitly state the minimum and "
                    "maximum expansion limits of this component."
                )
                logger.warning(msg)

    # handle tessif's infinity values
    if nominal_value == float('inf'):
        # infinity values are handled by setting installed_capacity and
        # expansion_costs 0

        # milp + expansion cant be handled on the same flow
        if component._milp[interface]:
            msg = (
                "Pypsa cannot handle infinity nominal value and milp\n"
                "constraints at the same time for a singular flow."
            )
            raise ValueError(msg)

        # Handle case, the user wanted it to be expandable anyways:
        if component.expandable[interface]:

            flow_params['p_nom'] = 0.0
            flow_params['p_nom_extendable'] = True
            flow_params['p_min_pu'] = 0.0
            flow_params['p_max_pu'] = 1.0

            # handle implied flow_rate settings by passing a timeseries:
            if component.expansion_costs[interface] != 0:
                if component.timeseries:
                    if component.timeseries[interface] is not None:
                        # preset nominal value to distinguish use cases
                        flow_params['p_nom'] = max(
                            component.timeseries[interface].max)

                    else:
                        msg = (
                            "nominal_value == float('inf') & expansion_costs "
                            "!= 0.\n\n"
                            "Infinity nominal values in pypsa are handled by "
                            "setting them to 0 while making them expandable.\n"
                            "Expansion costs are currently set to non-zero. "
                            "Be aware that the sum of constraints as well as "
                            "the results might be different from what you "
                            "expect.\n"
                        )
                        logger.warning(msg)

        # Fall back on installed_cap & exp_cost = 0
        else:
            flow_params['p_nom'] = 0.0
            flow_params['p_nom_min'] = 0.0
            flow_params['p_nom_max'] = float('inf')
            flow_params['p_nom_extendable'] = True
            flow_params['capital_cost'] = 0
            flow_params['p_min_pu'] = 0.0
            flow_params['p_max_pu'] = 1.0

        for key, value in flow_params.copy().items():
            if isinstance(value, numbers.Number):
                if value == float('inf'):
                    if key != 'p_nom_max':
                        flow_params[key] = 1.0

    # handle tessif's timeseries arguments
    if component.timeseries is not None:
        if interface in component.timeseries:

            if flow_params['p_nom'] != 0:
                flow_params['p_min_pu'] = np.array(component.timeseries[
                    interface].min) / flow_params['p_nom']
                flow_params['p_max_pu'] = np.array(component.timeseries[
                    interface].max) / flow_params['p_nom']
            else:
                min_nominal_value = max(component.timeseries[interface].min)
                if min_nominal_value != 0:
                    flow_params['p_min_pu'] = np.array(component.timeseries[
                        interface].min) / min_nominal_value

                else:
                    flow_params['p_min_pu'] = 0.0

                max_nominal_value = max(component.timeseries[interface].max)
                if max_nominal_value != 0:
                    flow_params['p_max_pu'] = np.array(component.timeseries[
                        interface].max) / max(
                            component.timeseries[interface].max)
                else:
                    flow_params['p_max_pu'] = 1.0

            # warn the user in case maximum minimum time series is higher than
            # the minimum expansion, what make ppsa think it can sell
            # the component to make money
            if 'p_nom_min' in flow_params:
                if flow_params['p_nom_min'] < max(
                        component.timeseries[interface].max):
                    msg = (
                        "Minimum stated expansion limit "
                        f"(''{flow_params['p_nom_min']}'') of component "
                        f"''{component.uid.name}'' is lower than the maximum "
                        "stated timeseries value of "
                        f"''{max(component.timeseries[interface].max)}''.\n"
                        "This may lead to pypsa selling the component "
                        "for the stated expansions costs, and hence "
                        "yield quite unpredictable results.\n\n"
                        "To avoid that, explicitly state the minimum and "
                        "maximum expansion limits of this component."
                    )
                    logger.warning(msg)

    return flow_params


def create_pypsa_busses(busses):
    """
    Creates pypsa buses out of tessif busses.

    Parameters
    ----------
    busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects that are to
        be transformed into `bus
        <https://pypsa.readthedocs.io/en/stable/components.html#bus>`_
        objects.

    Return
    ------
    :class:`~collections.abc.Sequence`
        Sequence of pypsa dictionairies representing the `bus
        <https://pypsa.readthedocs.io/en/stable/components.html#bus>`_
        components.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_mwe()
    >>> pypsa_busses = create_pypsa_busses(tsf_es.busses)
    >>> for i, bus in enumerate(pypsa_busses):
    ...     for attr, value in bus.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_busses) - 1:
    ...         print()
    class_name = Bus
    name = Pipeline
    x = 0.0
    y = 0.0
    carrier = None
    <BLANKLINE>
    class_name = Bus
    name = Powerline
    x = 0.0
    y = 0.0
    carrier = None
    """
    tessif_busses = list(busses)

    pypsa_bus_dicts = list()
    for bus in tessif_busses:
        pypsa_bus_dicts.append(
            {
                'class_name': 'Bus',
                'name': str(bus.uid),
                'x': bus.uid.longitude,
                'y': bus.uid.latitude,
                'carrier': bus.uid.carrier
            }
        )

    return pypsa_bus_dicts


def create_pypsa_generators_from_sources(sources, tessif_busses):
    """
    Create pypsa generators out of tessif sources.

    Parameters
    ----------
    sources: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Source` objects that are to
        be transformed into `generator
        <https://pypsa.readthedocs.io/en/stable/components.html#generator>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_generators_from_sources.sources`.

    Return
    ------
    :class:~collections.abc.Sequence
        Sequence of pypsa dictionairies representing the `generator
        <https://pypsa.readthedocs.io/en/stable/components.html#generator>`_
        components representing tessif sources.

    Note
    ----
    Tessif sources can have multiple outputs, pypsa generators not.
    So in case a tessif source requests to have multiple outputs, a singular
    pypsa generator is created for each output.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_fpwe()
    >>> pypsa_sources = create_pypsa_generators_from_sources(
    ...     tsf_es.sources, tsf_es.busses)
    >>> for i, source in enumerate(pypsa_sources):
    ...     for attr, value in source.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_sources) - 1:
    ...         print()
    class_name = Generator
    name = Gas Station
    bus = Pipeline
    carrier = Gas Station.carrier
    p_nom = 100
    p_min_pu = 0.0
    p_max_pu = 1.0
    marginal_cost = 10
    efficiency = 1.0
    flow_emissions = 3
    <BLANKLINE>
    class_name = Generator
    name = Solar Panel
    bus = Powerline
    carrier = electricity
    p_nom = 20
    p_min_pu = [0.6  0.15 0.35]
    p_max_pu = [0.6  0.15 0.35]
    marginal_cost = 0
    efficiency = 1.0
    flow_emissions = 0
    <BLANKLINE>
    class_name = Carrier
    name = Gas Station.carrier
    co2_emissions = 3.0

    Note how an extra Carrier object gets parsed to accomodate for the
    emission constraints.
    """
    tessif_sources = list(sources)
    tessif_busses = list(tessif_busses)

    pypsa_generator_dicts = list()
    pypsa_carrier_dicts = list()
    for source in tessif_sources:
        for output in source.outputs:
            for bus in tessif_busses:

                # reconstruct the connecting bus id...
                source_outp_bus_id = '.'.join([source.uid.name, output])

                # and check if it is an existing one by comparing it to all
                # bus inputs
                if source_outp_bus_id in bus.inputs:
                    # if the right one is found break out of the loop
                    pypsa_bus_uid = bus.uid
                    break

            new_gen = {
                'class_name': 'Generator',
                'name': str(source.uid),
                'bus': str(pypsa_bus_uid),
                'carrier': source.uid.carrier,
            }

            # check for generators of the same name present already
            counter = 0
            for generator_dict in pypsa_generator_dicts:
                if generator_dict['name'] == new_gen['name']:
                    counter += 1

            if counter != 0:
                new_gen['name'] = f'{str(source.uid)}_{counter}'

            new_gen.update(
                parse_flow_parameters(source, output)
            )

            # parse efficiency
            if hasattr(source, 'conversions'):
                for key, efficiency in source.conversions.items():
                    if output in key:
                        new_gen['efficiency'] = efficiency

            else:
                new_gen['efficiency'] = 1.0

            # parse emissions
            carrier_dict = {}
            emissions = source.flow_emissions[output]
            if emissions > 0:
                # individualize carrier for each generator
                new_gen['carrier'] = f"{new_gen['name']}.carrier"

                # create pypsa parseable carrier dict to constrain emissions
                carrier_dict.update(
                    {
                        'class_name': 'Carrier',
                        'name': new_gen['carrier'],
                        'co2_emissions': emissions * new_gen['efficiency']
                    }
                )

            new_gen['flow_emissions'] = emissions

            # print(79*'-')
            # print(new_gen)
            # print(79*'-')

            pypsa_generator_dicts.append(new_gen)

            # only add carriers if needed
            if len(carrier_dict) > 0:
                pypsa_carrier_dicts.append(carrier_dict)

    return [*pypsa_generator_dicts, *pypsa_carrier_dicts]


def create_pypsa_sinks(sinks, tessif_busses, timeseries='max'):
    """
    Create pypsa generators out of tessif sinks.

    Parameters
    ----------
    sinks: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Sink` objects that are to
        be transformed into `load
        <https://pypsa.readthedocs.io/en/stable/components.html#load>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_generators_from_sources.sources`.

    timeseries: str, ['max', 'min', 'avg']
        String specifying how to handle timeseries values.
        Since `pypsa loads
        <https://pypsa.readthedocs.io/en/stable/components.html#load>`_
        can only handle fixed timeseries values (in contrast to time varying
        range of lower and upper load limits), a flag has to be stated
        how timeseries values are to be handled.

        Must be one of:

            - ``max`` (default):

                :attr:`flow_rate.max <tessif.model.components.Sink.flow_rates>`
                is used, for setting the timeseries values.

            - ``min`` (default):

                :attr:`flow_rate.min <tessif.model.components.Sink.flow_rates>`
                is used, for setting the timeseries values.

            - ``avg``:

                The average of each time step between
                :attr:`flow_rate.min and flow_rate.max
                <tessif.model.components.Sink.flow_rates>` is used.

    Return
    ------
    :class:`~collections.abc.Sequence`
        Sequence of pypsa dictionairies representing the `load
        <https://pypsa.readthedocs.io/en/stable/components.html#load>`_
        components representing tessif sinks.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_fpwe()
    >>> pypsa_sinks = create_pypsa_sinks(
    ...     tsf_es.sinks, tsf_es.busses)
    >>> for i, sink in enumerate(pypsa_sinks):
    ...     for attr, value in sink.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_sinks) - 1:
    ...         print()
    class_name = Load
    name = Demand
    bus = Powerline
    p_set = 11.0
    """
    tessif_sinks = list(sinks)
    tessif_busses = list(tessif_busses)

    pypsa_load_dicts = list()
    for sink in tessif_sinks:
        for inbound in sink.inputs:
            for bus in tessif_busses:

                # reconstruct the connecting bus id...
                source_outp_bus_id = '.'.join([sink.uid.name, inbound])

                # and check if it is an existing one by comparing it to all
                # bus outputs
                if source_outp_bus_id in bus.outputs:
                    # if the right one is found break out of the loop
                    pypsa_bus_uid = bus.uid
                    break

            new_load = {
                'class_name': 'Load',
                'name': str(sink.uid),
                'bus': str(pypsa_bus_uid),
            }

            new_load.update(
                parse_flow_parameters(sink, inbound)
            )

            # parse the general flow parameters into arguments the load "class"
            # comprehends:

            if timeseries == 'max':
                new_load['p_set'] = new_load['p_max_pu'] * new_load['p_nom']

            elif timeseries == 'min':
                new_load['p_set'] = new_load['p_min_pu'] * new_load['p_nom']

            elif timeseries == 'avg':
                new_load['p_set'] = (
                    np.mean(
                        list(
                            zip(
                                new_load['p_min_pu'], new_load['p_max_pu']
                            )
                        ),
                        axis=1)
                    * new_load['p_nom']
                )

            # pop general flow parameters the load "class" cannot comprehend:
            # print(79*'-')
            # print(new_load)
            # print(79*'-')

            for flow_param in [
                    'p_min_pu', 'p_max_pu', 'marginal_cost', 'p_nom',
                    'p_nom_min', 'p_nom_max', 'capital_cost',
                    'p_nom_extendable']:
                if flow_param in new_load:
                    new_load.pop(flow_param)

            pypsa_load_dicts.append(new_load)

    return pypsa_load_dicts


def create_pypsa_excess_sinks(sinks, tessif_busses):
    """
    Create pypsa generators out of tessif sinks.

    Parameters
    ----------
    sinks: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Sink` objects that are to
        be transformed into `storage units
        <https://pypsa.readthedocs.io/en/stable/components.html#storage-unit>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_generators_from_sources.sources`.


    Return
    ------
    :class:`~collections.abc.Sequence`
        Sequence of pypsa dictionairies representing the `storage unit
        <https://pypsa.readthedocs.io/en/stable/components.html#storage-unit>`_
        components representing tessif excess sinks.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_simple_transformer_grid_es()
    >>> tsf_excess_sinks = [sink for sink in tsf_es.sinks
    ...                     if str(sink.uid) in ("HV-XS", "MV-XS")]
    >>> pypsa_excess_sinks = create_pypsa_excess_sinks(
    ...     tsf_excess_sinks, tsf_es.busses)
    >>> for i, sink in enumerate(pypsa_excess_sinks):
    ...     for attr, value in sink.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_excess_sinks) - 1:
    ...         print()
    class_name = Bus
    name = HV-XS-Bus
    type = ignore
    <BLANKLINE>
    class_name = Link
    name = HV-XS-Link
    bus0 = HV-Bus
    bus1 = HV-XS-Bus
    type = ignore
    efficiency = 1.0
    p_min_pu = -1.0
    marginal_cost = 10
    p_nom_extendable = True
    capital_cost = 0
    <BLANKLINE>
    class_name = StorageUnit
    name = HV-XS
    bus = HV-XS-Bus
    type = excess_sink
    marginal_cost = 10
    p_nom = 0.0
    p_nom_min = 0.0
    p_nom_max = inf
    p_nom_extendable = True
    capital_cost = 0
    p_min_pu = -1.0
    p_max_pu = 0.0
    <BLANKLINE>
    class_name = Bus
    name = MV-XS-Bus
    type = ignore
    <BLANKLINE>
    class_name = Link
    name = MV-XS-Link
    bus0 = MV-Bus
    bus1 = MV-XS-Bus
    type = ignore
    efficiency = 1.0
    p_min_pu = -1.0
    marginal_cost = 10
    p_nom_extendable = True
    capital_cost = 0
    <BLANKLINE>
    class_name = StorageUnit
    name = MV-XS
    bus = MV-XS-Bus
    type = excess_sink
    marginal_cost = 10
    p_nom = 0.0
    p_nom_min = 0.0
    p_nom_max = inf
    p_nom_extendable = True
    capital_cost = 0
    p_min_pu = -1.0
    p_max_pu = 0.0
    """
    tessif_sinks = list(sinks)
    tessif_busses = list(tessif_busses)

    pypsa_storage_unit_dicts = list()
    for sink in tessif_sinks:
        for inbound in sink.inputs:
            for bus in tessif_busses:

                # reconstruct the connecting bus id...
                source_outp_bus_id = '.'.join([sink.uid.name, inbound])

                # and check if it is an existing one by comparing it to all
                # bus outputs
                if source_outp_bus_id in bus.outputs:
                    # if the right one is found break out of the loop
                    pypsa_bus_uid = bus.uid
                    break

            new_bus_unit = {
                'class_name': 'Bus',
                'name': "-".join([str(sink.uid), "Bus"]),
                "type": "ignore",
            }
            new_link_unit = {
                "class_name": "Link",
                'name': "-".join([str(sink.uid), "Link"]),
                'bus0': str(pypsa_bus_uid),
                'bus1': "-".join([str(sink.uid), "Bus"]),
                "type": "ignore",
                'efficiency': 1.0,
                'p_min_pu': -1.0,
                'marginal_cost': 0,
                'p_nom_extendable': True,
                'capital_cost': 0,
            }
            new_storage_unit = {
                'class_name': 'StorageUnit',
                'name': str(sink.uid),
                'bus': "-".join([str(sink.uid), "Bus"]),
                "type": "excess_sink",
            }

            new_storage_unit.update(
                parse_flow_parameters(sink, inbound)
            )

            # new_storage_unit["e_nom_extendable"] = True
            new_storage_unit["capital_cost"] = 0

            # make excess sink aka storage able to storage_unit energy
            new_storage_unit["p_min_pu"] = -1.0
            # but do not allow energy dispatch
            new_storage_unit["p_max_pu"] = 0.0

            # transfer excess costs to link, so pypsa recognizes:
            new_link_unit["marginal_cost"] = new_storage_unit["marginal_cost"]

            # print(79*'-')
            # print(new_storage_unit)
            # print(79*'-')
            pypsa_storage_unit_dicts.append(new_bus_unit)
            pypsa_storage_unit_dicts.append(new_link_unit)
            pypsa_storage_unit_dicts.append(new_storage_unit)

    return pypsa_storage_unit_dicts


def create_pypsa_generators_from_transformers(transformers, tessif_busses):
    """
    Create pypsa generators out of tessif transformers.

    Parameters
    ----------
    transformers: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Transformer` objects that
        are to be transformed into `generator
        <https://pypsa.readthedocs.io/en/stable/components.html#generator>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_generators_from_transformers.transformers`.

    Return
    ------
    :class:~collections.abc.Sequence
        Sequence of pypsa dictionairies representing the `generator
        <https://pypsa.readthedocs.io/en/stable/components.html#generator>`_
        components representing tessif transformers.

    Note
    ----
    Tessif transformers can have multiple outputs, pypsa generators not.
    So in case a tessif transformer requests to have multiple outputs, a
    singular pypsa generator is created for each output.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_fpwe()
    >>> pypsa_transformers = create_pypsa_generators_from_transformers(
    ...     tsf_es.transformers, tsf_es.busses)
    >>> for i, transformer in enumerate(pypsa_transformers):
    ...     for attr, value in transformer.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_transformers) - 1:
    ...         print()
    class_name = Generator
    name = Generator
    bus = Powerline
    carrier = Generator.carrier
    p_nom = 15
    p_min_pu = 0.0
    p_max_pu = 1.0
    marginal_cost = 10
    efficiency = 0.42
    flow_emissions = 10
    <BLANKLINE>
    class_name = Carrier
    name = Generator.carrier
    co2_emissions = 4.2

    Note how an extra Carrier object gets parsed to accomodate for the
    Generator allocated  emission constraints.
    """

    return create_pypsa_generators_from_sources(
        sources=transformers,
        tessif_busses=tessif_busses)


def create_pypsa_links_from_transformers(transformers, tessif_busses):
    """
    Create pypsa links out of tessif transformers.

    Parameters
    ----------
    transformers: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Transformer` objects that
        are to be transformed into `link
        <https://pypsa.readthedocs.io/en/stable/components.html#link>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_links_from_transformers.transformers`.

    Return
    ------
    :class:~collections.abc.Sequence
        Sequence of pypsa dictionairies representing the `link
        <https://pypsa.readthedocs.io/en/stable/components.html#link>`_
        components representing tessif transformers.

    Warning
    -------
    In case of chp transformation pypsa uses the highest installed capacity as
    reference capacity to calculate outgoing flows using the respective
    conversion factors.

    Make sure the conversion factors reflect the expected
    installed capacities. If target capacaties are 100 and 50, make sure
    conversion factors are of ration 2/1 (i.e 0.6 and 0.3).

    Raises
    ------
    NotImplementedError
        Raised if more than 1 input is used, because tessif can't handle this
        case yet.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    Singular output Link:

    >>> tsf_es = tsf_examples.create_fpwe()
    >>> pypsa_links = create_pypsa_links_from_transformers(
    ...     tsf_es.transformers, tsf_es.busses)
    >>> for i, link in enumerate(pypsa_links):
    ...     for attr, value in link.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_links) - 1:
    ...         print()
    class_name = Link
    name = Generator
    efficiency = 0.42
    bus0 = Pipeline
    bus1 = Powerline
    siso_transformer = True
    flow_costs = 10
    expansion_costs = 0
    flow_emissions = 10
    p_nom = 35.714285714285715
    p_min_pu = 0.0
    p_max_pu = 1.0
    marginal_cost = 4.2
    capital_cost = 0
    carrier = Generator.carrier
    <BLANKLINE>
    class_name = Carrier
    name = Generator.carrier
    co2_emissions = 4.2

    Note how an extra Carrier object gets parsed to accomodate for the
    Link allocated emission constraints.


    Multiple output Links:

    >>> tsf_es = tsf_examples.create_hhes()
    >>> tessif_transformers = [
    ...     t for t in tsf_es.transformers
    ...     if ('biomass chp' in str(t.uid) or 'chp3' in str(t.uid))]
    >>> pypsa_links = create_pypsa_links_from_transformers(
    ...     tessif_transformers, tsf_es.busses)
    >>> for i, link in enumerate(pypsa_links):
    ...     for attr, value in link.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_links) - 1:
    ...         print()
    class_name = Link
    name = chp3
    efficiency2 = 0.4075
    efficiency = 0.4
    bus0 = coal supply line
    bus1 = district heating pipeline
    bus2 = powerline
    multiple_outputs = True
    flow_costs2 = 82.0
    flow_costs = 19.68
    expansion_costs2 = 0
    expansion_costs = 0
    flow_emissions2 = 0
    flow_emissions = 0
    p_nom = 732.5
    p_min_pu = 0.0
    p_max_pu = 1.0
    marginal_cost = 41.287
    capital_cost = 0
    p_nom2 = 461.3496932515338
    <BLANKLINE>
    class_name = Link
    name = biomass chp
    efficiency2 = 0.3841269841269841
    efficiency = 1.0
    bus0 = biomass logistics
    bus1 = district heating pipeline
    bus2 = powerline
    multiple_outputs = True
    flow_costs2 = 61
    flow_costs = 20
    expansion_costs2 = 0
    expansion_costs = 0
    flow_emissions2 = 0
    flow_emissions = 0
    p_nom = 126.0
    p_min_pu = 0.0
    p_max_pu = 1.0
    marginal_cost = 43.43174603174603
    capital_cost = 0
    p_nom2 = 126.0
    """

    tessif_transformers = list(transformers)
    tessif_busses = list(tessif_busses)

    pypsa_link_dicts = list()
    pypsa_carrier_dicts = list()

    for transformer in tessif_transformers:
        input_busses = dict()
        output_busses = dict()
        emissions, costs, capacities, expansion_costs = list(), list(), list(), list()
        efficiencies = list()

        for bus in tessif_busses:
            for pos, inbound in enumerate(transformer.inputs):

                # reconstruct the connecting bus id...
                transformer_input_bus_id = '.'.join(
                    [transformer.uid.name, inbound])

                # and check if it is an existing one by comparing it to all
                # bus outputs
                if transformer_input_bus_id in bus.outputs:
                    # if the right one is found store it pypsa compatibly
                    input_busses[f'bus{pos}'] = str(bus.uid)

        for bus in tessif_busses:
            # inbound needs to be found before outbound
            # that's why tessif busses are iterated twice
            for pos, output in enumerate(transformer.outputs):

                # reconstruct the connecting bus id...
                transformer_outp_bus_id = '.'.join(
                    [transformer.uid.name, output])

                # and check if it is an existing one by comparing it to all
                # bus inputs
                if transformer_outp_bus_id in bus.inputs:
                    # if the right one is found store it pypsa compatibly
                    output_busses[f'bus{len(input_busses)+pos}'] = str(bus.uid)

                    # costs
                    costs.append(
                        transformer.flow_costs[output])

                    # expansion costs
                    expansion_costs.append(
                        transformer.expansion_costs[output])

                    # emissions
                    emissions.append(
                        transformer.flow_emissions[output])

                    # installed capacity
                    frate = transformer.flow_rates[output].max
                    if isinstance(frate, collections.abc.Iterable):
                        frate = max(frate)
                    capacities.append(frate)

                    for conversion in transformer.conversions:
                        if output in conversion:
                            efficiencies.append(
                                transformer.conversions[conversion])

        # sort efficiency, costs, emissions and capacity for highest capacity
        # so the highest capacity outflow represent p_nom

        output_bound_params = pd.DataFrame(
            data=zip(capacities, efficiencies, costs, expansion_costs,
                     emissions, output_busses.values()),
            columns=('capacities', 'efficiencies', 'costs',
                     'expansion_costs', 'emissions', 'busses'),
        )

        output_bound_params = output_bound_params.sort_values(
            by='capacities',
            axis='index',
            ascending=False,
        )

        capacities = list(output_bound_params['capacities'])
        costs = list(output_bound_params['costs'])
        expansion_costs = list(output_bound_params['expansion_costs'])
        emissions = list(output_bound_params['emissions'])
        efficiencies = list(output_bound_params['efficiencies'])

        # output busses need to be parsed in a special manner
        output_bus_list = list(output_bound_params['busses'])
        output_busses = dict()
        for counter, bus in enumerate(output_bus_list):
            output_busses[f'bus{len(input_busses)+counter}'] = bus

        # parse the efficiencies for pypsa to understand
        if len(input_busses) > 1 or len(output_busses) > 1:

            # mimo transformer
            if len(input_busses) > 1 and len(output_busses) > 1:
                raise NotImplementedError

            # miso transformer
            elif len(input_busses) > 1:
                raise NotImplementedError

            # simo transformer, usually chps
            elif len(output_busses) > 1:

                # parse installed capacities
                parsed_capacities = dict()
                for counter, capacity in enumerate(capacities):
                    if capacity == float('+inf'):
                        capacity = 0
                    else:
                        capacity /= efficiencies[counter]
                    parsed_capacities[f"p_nom{counter+1}"] = capacity

                parsed_capacities['p_nom'] = parsed_capacities.pop("p_nom1")

                # parse efficiencies
                parsed_efficiencies = dict()

                for counter, efficiency in enumerate(efficiencies):

                    # hack inside the efficiency to account for p_nom1+
                    # which only works if it is not extendable

                    # if counter != 0 and parsed_capacities['p_nom'] != 0:
                    #     p_nomi = parsed_capacities[f"p_nom{counter+1}"]
                    #     efficiency = p_nomi/parsed_capacities[
                    #         'p_nom'] * efficiency

                    parsed_efficiencies[f"efficiency{counter+1}"] = efficiency

                parsed_efficiencies[
                    'efficiency'] = parsed_efficiencies.pop("efficiency1")

                # parse costs
                parsed_costs = dict()

                for counter, cost in enumerate(costs):

                    parsed_costs[f"flow_costs{counter+1}"] = cost

                parsed_costs[
                    'flow_costs'] = parsed_costs.pop("flow_costs1")

                # parse expansion costs
                parsed_expansion_costs = dict()

                for counter, exp_cost in enumerate(expansion_costs):

                    parsed_expansion_costs[f"expansion_costs{counter+1}"] = exp_cost

                parsed_expansion_costs[
                    'expansion_costs'] = parsed_expansion_costs.pop("expansion_costs1")

                # parse emissions
                parsed_emissions = dict()

                for counter, emission in enumerate(emissions):
                    parsed_emissions[f"flow_emissions{counter+1}"] = emission

                parsed_emissions[
                    'flow_emissions'] = parsed_emissions.pop("flow_emissions1")

        # siso transformer
        else:

            siso_output = tuple(transformer.outputs)[0]
            parsed_efficiencies = {
                "efficiency": list(transformer.conversions.values())[0]}
            parsed_emissions = {
                'flow_emissions': transformer.flow_emissions[
                    siso_output]}
            parsed_costs = {
                'flow_costs': transformer.flow_costs[
                    siso_output]}
            parsed_expansion_costs = {
                'expansion_costs': transformer.expansion_costs[
                    siso_output]}

            # p_nom in links refers to highest occurring flow. so in the
            # context of a siso transformer, this means the input. Hence the
            # tessif output needs to be divided by its efficiency:
            cap = transformer.flow_rates[siso_output].max
            if isinstance(cap, collections.abc.Iterable):
                cap = max(cap)

            # distinguish between time series efficiencies (e.g. temp dependet
            # heat pump) and singular value sisos:
            eff = parsed_efficiencies['efficiency']
            if isinstance(eff, collections.abc.Iterable):
                eff = min(eff)

            parsed_capacities = {'p_nom': cap / eff}

            if cap == float("+inf"):
                parsed_capacities = {"p_nom": 0}
            else:
                parsed_capacities = {'p_nom': cap / eff}

            # output = siso_output

        # add post processor tags, if necessary
        post_processor_tags = dict()
        if len(input_busses) > 1:
            post_processor_tags['multiple_inputs'] = True

        if len(output_busses) > 1:
            post_processor_tags['multiple_outputs'] = True

        if len(output_busses) == len(input_busses) == 1:
            post_processor_tags['siso_transformer'] = True

        new_link = {
            'class_name': 'Link',
            'name': str(transformer.uid),
            **parsed_efficiencies,
            **input_busses,
            **output_busses,
            **post_processor_tags,
            **parsed_costs,
            **parsed_expansion_costs,
            **parsed_emissions,
        }

        parsed_flow_parameters = parse_flow_parameters(transformer, output)

        # pypsa link costs are evaluated before efficiency, hence tessif's
        # flow specific cost approach is modeled by calculating the sum of
        # the products of each flow cost by its efficiency i.e:
        # c = c_th * eta_th + c_el * eta_el for a chp:
        parsed_flow_parameters['marginal_cost'] = 0
        for cost, efficiency in zip(costs, efficiencies):

            # for time varying efficiencies the maximum is used
            if isinstance(efficiency, collections.abc.Iterable):
                parsed_flow_parameters['marginal_cost'] = [
                    cost * entry for entry in efficiency]

            else:
                parsed_flow_parameters['marginal_cost'] += cost * efficiency

        parsed_flow_parameters['marginal_cost']
        new_link.update(**parsed_flow_parameters)
        # print(79*'-')
        # print(parsed_flow_parameters)
        # print(79*'-')

        # account for siso corrected capacities in case of extendable capacity:
        # note extend to all links
        # if len(input_busses) == len(output_busses) == 1:

        if 'p_nom_extendable' in new_link:
            if (
                    new_link['p_nom'] == new_link['p_nom_min'] and
                    new_link['p_nom_extendable']
            ):
                parsed_capacities['p_nom_min'] = parsed_capacities['p_nom']

            # capital costs need to be multiplied with efficiency as pypsa
            # calculates with the highest flow,
            # which is usually the input cause efficiencies smaller than 1
            new_link['capital_cost'] = 0
            for out in transformer.outputs:
                for key, efficiency in transformer.conversions.items():
                    if out in key:
                        # for time varying efficiencies the maximum is used
                        if isinstance(efficiency, collections.abc.Iterable):
                            efficiency = max(efficiency)

                        new_link['capital_cost'] += transformer.expansion_costs[f'{out}'] * efficiency
        else:
            new_link['capital_cost'] = 0
            for i in range(len(expansion_costs)):
                if i == 0:
                    new_link['expansion_costs'] = 0
                else:
                    new_link[f'expansion_costs{i+1}'] = 0

        new_link.update(**parsed_capacities)

        # account for input based capacity on extendable links;
        # set min expansion to input corrected capacity:

        # if new_link['p_nom_min'] < new_link['p_nom']:
        #     new_link['p_nom_min'] = new_link['p_nom']

        # parse emissions, so pypsa respects them:
        input_attributed_emissions = np.dot(
            tuple(parsed_emissions.values()),
            tuple(parsed_efficiencies.values())
        )

        if isinstance(input_attributed_emissions, collections.abc.Iterable):

            input_attributed_emissions = max(input_attributed_emissions)
            if input_attributed_emissions > 0:
                logger.warning("Due to time varying efficiencies,")
                logger.warning(f"component '{new_link['name']}'")
                logger.warning(
                    "may not have their emissions allocated correctly.")
                logger.warning("Emissions at maxiimum efficiency are used")

        carrier_dict = dict()
        if input_attributed_emissions > 0:
            new_link['carrier'] = f"{new_link['name']}.carrier"

            # create pypsa parseable carrier dict to constrain emissions
            carrier_dict = {
                'class_name': 'Carrier',
                'name': new_link['carrier'],
                'co2_emissions': input_attributed_emissions,
            }

        # pop general flow parameters the link "class" cannot comprehend:
        for flow_param in ['committable']:
            if flow_param in new_link:
                new_link.pop(flow_param)

        pypsa_link_dicts.append(new_link)

        # only add carriers if needed
        if len(carrier_dict) > 0:
            pypsa_carrier_dicts.append(carrier_dict)

    return [*pypsa_link_dicts, *pypsa_carrier_dicts]


def create_pypsa_connectors(connectors, tessif_busses):
    """
    Create pypsa links out of tessif connectors.

    Parameters
    ----------
    connectors: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Connector` objects that
        are to be transformed into `link
        <https://pypsa.readthedocs.io/en/stable/components.html#link>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_links_from_connectors.connectors`.

    Return
    ------
    :class:~collections.abc.Sequence
        Sequence of pypsa dictionairies representing the `link
        <https://pypsa.readthedocs.io/en/stable/components.html#link>`_
        components representing tessif connectors.

    Note
    ----
    Transforming :class:`tessif connectors <tessif.model.components.Connector>`
    to `pypsa links
    <https://pypsa.readthedocs.io/en/stable/components.html#link>`__
    following compatibility issues are faced:

        - Pypsa links are one-directional according to their efficiency
          calculations. For bidirectional tessif links to make sense,
          bidirectional pypsa links are set to an efficiency of 1.0.
        - Tessif connectors are not designed to constrain their flows,
          where as pypsa links are. Therefor pypsa links created from
          tessif connectors are parameterized as follows:

            1. nominal capacity is extendable having no extension costs
            2. specific min/max power flow is set to -1.0/1.0 respectively
            3. flow specific costs are set to 0.0

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_connected_es()
    >>> pypsa_links = create_pypsa_connectors(
    ...     tsf_es.connectors, tsf_es.busses)
    >>> for i, link in enumerate(pypsa_links):
    ...     for attr, value in link.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_links) - 1:
    ...         print()
    class_name = Link
    name = connector
    bus0 = bus-01
    bus1 = bus-02
    efficiency = 1.0
    p_min_pu = -1.0
    marginal_cost = 0
    p_nom_extendable = True
    capital_cost = 0
    """

    tessif_connectors = list(connectors)
    tessif_busses = list(tessif_busses)

    pypsa_link_dicts = list()
    for connector in tessif_connectors:

        new_link = {
            'class_name': 'Link',
            'name': str(connector.uid),
            'bus0': sorted(list(connector.inputs))[0],
            'bus1': sorted(list(connector.inputs))[1],
            'efficiency': 1.0,
            'p_min_pu': -1.0,
            'marginal_cost': 0,
            'p_nom_extendable': True,
            'capital_cost': 0,
        }

        pypsa_link_dicts.append(new_link)

    return pypsa_link_dicts


def create_pypsa_storages(storages, tessif_busses):
    """
    Create pypsa generators out of tessif storages.

    Parameters
    ----------
    storages: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Storage` objects that are
        to be transformed into `generator
        <https://pypsa.readthedocs.io/en/stable/components.html#generator>`_
        objects.

    tessif_busses: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Bus` objects present
        in the same energy system as
        :paramref:`~create_pypsa_storages.storages`.

    Return
    ------
    :class:`~collections.abc.Sequence`
        Sequence of pypsa dictionairies representing the `storage
        <https://pypsa.readthedocs.io/en/stable/components.html#storage>`_
        components representing tessif storages.

    Note
    ----
    Pypsa forces the ratio of capacity and output flow to be constant, even
    during expansion. Doing that it restricts possible capacty expansion
    in relation to out_flow expansion. Meaning, outflow expansion is subject
    to parameterization while capacity expansion is just a subsequent
    byproduct.

    Since this seems quite unintuitive, tessif parameterizes it the other way
    round, meaning the values for capacity expansion are enforced on the flow
    rate expansion repsecting the stated ration of capacity to flow rate.

    Example
    -------
    >>> import tessif.examples.data.tsf.py_hard as tsf_examples

    >>> tsf_es = tsf_examples.create_fpwe()
    >>> pypsa_storages = create_pypsa_storages(
    ...     tsf_es.storages, tsf_es.busses)
    >>> for i, storage in enumerate(pypsa_storages):
    ...     for attr, value in storage.items():
    ...         print(f"{attr} = {value}")
    ...     if i < len(pypsa_storages) - 1:
    ...         print()
    class_name = StorageUnit
    name = Battery
    bus = Powerline
    max_hours = 0.3333333333333333
    efficiency_store = 1
    efficiency_dispatch = 1
    state_of_charge_initial = 10
    cyclic_state_of_charge = False
    standing_loss = 0.1
    inflow = 0
    flow_emissions = 0
    p_nom = 30
    p_min_pu = -1.0
    p_max_pu = 1.0
    marginal_cost = 0
    """
    tessif_storages = list(storages)
    tessif_busses = list(tessif_busses)

    pypsa_storage_dicts = list()
    pypsa_carrier_dicts = list()
    for storage in tessif_storages:

        for bus in tessif_busses:

            inbound = storage.input

            # reconstruct the connecting bus id...
            storage_outp_bus_id = '.'.join(
                [storage.uid.name, inbound])

            # and check if it is an existing one by comparing it to all
            # bus inputs
            if storage_outp_bus_id in bus.outputs:
                # if the right one is found store it pypsa compatibly
                connecting_bus = bus.uid

        # parse initial and final soc:
        cyclic_state_of_charge = False
        if storage.final_soc is not None:
            if storage.initial_soc == storage.final_soc:
                cyclic_state_of_charge = True

        # parse idle changes, to deal with 0 install capacity:
        if storage.capacity != 0:
            standing_loss = storage.idle_changes.negative/storage.capacity
        else:
            standing_loss = 0

        new_storage = {
            'class_name': 'StorageUnit',
            'name': str(storage.uid),
            'bus': connecting_bus,
            'max_hours': storage.capacity/storage.flow_rates[
                storage.output].max,
            'efficiency_store': storage.flow_efficiencies[
                storage.input].inflow,
            'efficiency_dispatch': storage.flow_efficiencies[
                storage.output].outflow,
            'state_of_charge_initial': storage.initial_soc,
            'cyclic_state_of_charge': cyclic_state_of_charge,
            'standing_loss': standing_loss,
            'inflow': storage.idle_changes.positive,
            'flow_emissions': storage.flow_emissions[storage.input]
        }

        new_storage.update(
            parse_flow_parameters(storage, storage.input)
        )

        # pop commitable attribute, since storage ain't got one
        if 'committable' in new_storage:
            new_storage.pop('committable')

        # default parsing set p_min_pu to 0, but it needs to be -1.0 by default
        if new_storage['p_min_pu'] == 0.0:
            new_storage['p_min_pu'] = -1.0

        # handle infinite flow and finite capacity conflict:
        if new_storage['max_hours'] == new_storage['p_nom'] == 0.0:
            # if new_storage['state_of_charge_initial'] != 0.0:
            #     new_storage['p_nom'] = new_storage['state_of_charge_initial']
            new_storage['max_hours'] = 1.0

        # storage expansion focues on capacity rather than on flow parameters
        # so they need to be adjusted accordingly:
        if storage.expandable['capacity']:
            if not storage.expandable[f'{storage.output}']:
                msg = (
                    f"Storage '{storage.uid.name}' is requested to have "
                    "an expandable capacity, but a non-expandable output "
                    f"'{storage.output}'. PyPSA however fixed flow rate to "
                    "capacity expansion. falling back to an expandable "
                    "outflow, to allow succesful optimization."
                )
                logger.warning(msg)

            new_storage['p_nom_extendable'] = True
            new_storage['capital_cost'] = storage.expansion_costs['capacity'] * \
                new_storage['max_hours']
            new_storage['p_nom_min'] = storage.expansion_limits[
                'capacity'].min / new_storage['max_hours']
            new_storage['p_nom_max'] = storage.expansion_limits[
                'capacity'].max / new_storage['max_hours']

        # new_storage['state_of_charge_initial_per_period'] = True

        # print(79*'-')
        # for attr, value in new_storage.items():
        #     print(f'{attr}: {value}')
        # print(79*'-')

        # parse emissions
        carrier_dict = {}
        if new_storage['flow_emissions'] > 0:
            # individualize carrier for each storage
            new_storage['carrier'] = f"{new_storage['name']}.carrier"

            # create pypsa parseable carrier dict to constrain emissions
            carrier_dict.update(
                {
                    'class_name': 'Carrier',
                    'name': new_storage['carrier'],
                    'co2_emissions': new_storage['flow_emissions']
                }
            )

        new_storage['marginal_cost'] = storage.flow_costs[storage.input]

        pypsa_storage_dicts.append(new_storage)

        # only add carriers if needed
        if len(carrier_dict) > 0:
            pypsa_carrier_dicts.append(carrier_dict)

    return [*pypsa_storage_dicts, *pypsa_carrier_dicts]


def transform(tessif_es, transformer_style='infer', forced_links=None, excess_sinks=None):
    """
    Transform a tessif energy system into a pypsa energy system.

    Parameters
    ----------
    tessif_es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        The tessif energy system that is to be transformed into a
        pypsa energy system.
    transformer_style: str
        String specifying how tessif transformer should be transformed into
        pypsa components:

            - ``infer`` (default):

                Transformers are treated according to
                :func:`infer_pypsa_transformer_types` with the exception of
                :paramref:`forced_links`, which are treated as
                `Pypsa links
                <https://pypsa.readthedocs.io/en/latest/components.html#link>`_

            - ``links``:

                All transformers are treated as links, giving up pypsa
                commitment simulations and plant related CO2 emissions, but
                preserving tessif energy system representation. (Meaning
                all nodes present inside the tessif energy system will be
                present inside the pypsa energy system.)

    forced_links: ~collections.abc.Container, None, default=None
        Container of :ref:`uid representations <Labeling_Concept>` of
        :class:`tessif transformers <tessif.model.components.Transformer>`
        to be transfrormed into `pypsa links
        <https://pypsa.readthedocs.io/en/latest/components.html#link>`_.

    excess_sinks: ~collections.abc.Container, None, default=None
        Container of :ref:`uid representations <Labeling_Concept>` of
        :class:`tessif sinks <tessif.model.components.Sink>`
        to be transfrormed into `pypsa store units
        <https://pypsa.readthedocs.io/en/latest/components.html#store>`_.

    Return
    ------
    pypsa_es: :class:`pypsa.Network`
        The pypsa energy system that was transformed out of the tessif
        energy system.

    Examples
    --------
    Use the :ref:`example hub's <Examples>`
    :meth:`~tessif.examples.data.tsf.py_hard.create_mwe` utility for showcasing
    basic usage:

    1. Create the mwe:

        >>> from tessif.examples.data.tsf.py_hard import create_mwe
        >>> tessif_es = create_mwe()
        >>> for node_uid in sorted([n.uid for n in tessif_es.nodes]):
        ...     print(node_uid)
        Battery
        Demand
        Gas Station
        Generator
        Pipeline
        Powerline

    2. Transform the :mod:`tessif energy system
       <tessif.model.energy_system.AbstractEnergySystem>`:

        >>> import tessif.transform.es2es.ppsa as tsf2pypsa
        >>> pypsa_es = tsf2pypsa.transform(tessif_es)

    3. Simulate the :class:`pypsa energy system <pypsa.Network>` using
       :func:`tessif's simulate wrapper <tessif.simulate.ppsa_from_es>`:

        >>> import tessif.simulate
        >>> optimized_pypsa_es = tessif.simulate.ppsa_from_es(pypsa_es)

    4. Show the simulation objective using pypsa's native interface:

        >>> print(optimized_pypsa_es.objective)
        61.0

    """
    # copy the existing component attribute dict:
    custom_attributes = pypsa.descriptors.Dict(
        {k: v.copy() for k, v in pypsa.components.component_attrs.items()}
    )

    # add flow bound emission values:
    custom_attributes.update(
        **pypsa_hooks.add_flow_bound_emissions(custom_attributes)
    )

    # add siso transformer label:
    custom_attributes.update(
        **pypsa_hooks.add_siso_transfromer_type(custom_attributes)
    )

    # scan the tessif transforms to find out if any of them fulfills one of the
    # following condition:
    #     - is a chp (aka uid.node_type == spellings.chp)
    #     - number of interfaces > 2
    # cause if so, the link component needs to be extended
    if (
            any([
                len(transformer.interfaces) > 2
                for transformer in tessif_es.transformers
            ])
            or
            any([
                transformer.uid.node_type in combined_heat_power
                for transformer in tessif_es.transformers
            ])
    ):

        number_of_additional_interfaces = max(
            [len(transformer.interfaces)
             for transformer in tessif_es.transformers]
        ) - 2  # -2, cause there are already 2 busses present by default

        # expand the link component using the appropriate hook
        custom_attributes.update(
            **pypsa_hooks.extend_number_of_link_interfaces(
                custom_attributes,
                additional_interfaces=number_of_additional_interfaces
            )
        )

    # create the energy system overriding the custom component attributes
    es = pypsa.Network(override_component_attrs=custom_attributes)

    # transform the timeframe
    timeframe = tessif_es.timeframe
    es.set_snapshots(timeframe)

    # transform the emission constraint:
    for constraint, limit in tessif_es.global_constraints.items():
        if constraint in spellings_flow_emissions:
            if limit < float('+inf'):

                es.add(class_name='GlobalConstraint',
                       name="co2_limit",
                       sense="<=",
                       constant=limit)

    # list of relatively straight forward transformation
    basic_transformations = [
        # 'sinks',
        'connectors',
        'storages',
    ]

    # transform busses first
    for bus_dict in create_pypsa_busses(tessif_es.busses):
        es.add(**bus_dict)

    # transform the basic components:
    for component in basic_transformations:
        for comp_dict in globals()[f'create_pypsa_{component}'](
                getattr(tessif_es, component), tessif_es.busses):
            es.add(**comp_dict)

    # sinks -> loads
    if not excess_sinks:
        excess_sinks = {}  # change None to empty dict to make it iterable

    for sink_dict in create_pypsa_sinks(
            sinks=[sink for sink in tessif_es.sinks
                   if str(sink.uid) not in excess_sinks],
            tessif_busses=tessif_es.busses):

        es.add(**sink_dict)

    setattr(es, "excess_sinks", excess_sinks)
    for storage_dict in create_pypsa_excess_sinks(
            sinks=[sink for sink in tessif_es.sinks
                   if str(sink.uid) in excess_sinks],
            tessif_busses=tessif_es.busses):
        es.add(**storage_dict)

    # sources -> generators
    for gen_dict in create_pypsa_generators_from_sources(
            sources=tessif_es.sources,
            tessif_busses=tessif_es.busses):
        es.add(**gen_dict)

    # For now, chps from tessif's CHP class are treated like transformers.
    for chp_dict in create_pypsa_links_from_transformers(
            transformers=tessif_es.chps,
            tessif_busses=tessif_es.busses):
        es.add(**chp_dict)

    # handle the quite delicate task of transforming the transformers
    if transformer_style == 'links':
        for link_dict in create_pypsa_links_from_transformers(
                tessif_es.transformers):
            es.add(**link_dict)
    else:
        # transform transformer according to the inferred type:
        transformer_types = infer_pypsa_transformer_types(
            tessif_es.transformers,
            forced_links=forced_links)

        # transform transformers into generators:
        for gen_dict in create_pypsa_generators_from_transformers(
            transformers=[
                transformer for transformer in tessif_es.transformers
                if transformer.uid in transformer_types['generators']],
            tessif_busses=tessif_es.busses
        ):
            es.add(**gen_dict)

        # remove the subsequent supply chains:
        for comp_type, components_to_remove in compute_unneeded_supply_chains(
                tessif_es=tessif_es,
                pypsa_generator_uids=transformer_types['generators']
        ).items():
            if comp_type != 'supply_chains':
                for comp in components_to_remove:
                    es.remove(comp_type, comp)
            else:
                # reallocate supply chain emission and costs to the remaining
                # generator:
                for gen_name, supplying_comps in components_to_remove.items():
                    for comp in supplying_comps:
                        # reallocate emissions if necessary
                        if hasattr(comp, 'flow_emissions'):

                            # assume component is a 1 outflow source
                            if list(comp.flow_emissions.values())[0] > 0:
                                # so add 1/eta * emissions to the respective
                                # generator further down the supply chain
                                es.generators.at[
                                    str(gen_name), 'flow_emissions'] += (
                                        list(comp.flow_emissions.values())[0] /
                                        es.generators[
                                            'efficiency'][str(gen_name)]
                                )

                                es.carriers.at[
                                    es.generators[
                                        'carrier'][str(gen_name)],
                                    'co2_emissions'] += list(
                                    comp.flow_emissions.values())[0]

                        # reallocate costs if necessary
                        if hasattr(comp, 'flow_costs'):
                            # assume component is a 1 outflow source
                            # so add 1/eta * emissions to the respective gen
                            es.generators.at[str(gen_name), 'marginal_cost'] += (
                                list(comp.flow_costs.values())[0] /
                                es.generators['efficiency'][str(gen_name)]
                            )

        # transform transformers into links:
        for gen_dict in create_pypsa_links_from_transformers(
            transformers=[
                transformer for transformer in tessif_es.transformers
                if transformer.uid in transformer_types['links']],
            tessif_busses=tessif_es.busses
        ):
            es.add(**gen_dict)

    es.uid = tessif_es.uid

    return es
