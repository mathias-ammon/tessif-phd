"""
:mod:`tessif.transform.es2es.fine` is a :mod:`tessif` module aggregating all the
functionality for automatically transforming a :class:`tessif energy system
<tessif.model.energy_system.AbstractEnergySystem>` into an
:class:`fine energy system <fine.energy_system.EnergySystem>`.
"""
import collections
import numbers
import logging
import pandas as pd
from collections import abc
import FINE as fn
import numpy as np

import tessif.frused.namedtuples as nts
import tessif.frused.defaults as esn_defaults
import tessif.frused.configurations as config
import tessif.frused.spellings as spl

logger = logging.getLogger(__name__)


def parse_esM_parameters(tessif_es):
    """
    Create the FINE basic energy system model input and gather relevant information.

    Note
    ----
    To build a FINE energy system it is necessary to define all commodities and its units taking place within the
    energy system. For this purpose all carriers of the underlying tessif energy system are gathered out and stored
    in a set.Due to that workflow the emission default is defined by the respective global constraint or if any
    component of the tessif energy system has flow emissions.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components` objects with the needed informations.

    Return
    ------
    region: string
        FINE's parameters are often related to the specific region, which is specified in this string.
        (Default set by Tessif)
    commodities: set of strings
        FINE's energy system specified commodities (in tessif carriers).
    units: set of strings
        FINE's energy system specified commodity units (combined with the default unit in tessif).
    emission: string
        For post-processing the emission default is stored as a string within the energy system model.
    """
    fine_region = set()
    fine_commodities = set()
    fine_commodityUnitDict = dict()

    region = esn_defaults.energy_system_nodes['fine_region']
    fine_region.add(region)

    for cmp in tessif_es.busses:
        for com in cmp.interfaces:
            commodity = str(cmp.uid.name) + '.' + com.partition('.')[2]
            if commodity not in fine_commodities:
                fine_commodities.add(commodity)
                unit = str(config.power_reference_unit) + '_' + commodity
                fine_commodityUnitDict.update({str(commodity): unit})

    if hasattr(tessif_es, 'global_constraints'):
        for constraint in tessif_es.global_constraints:
            if constraint in spl.emissions:
                emission_default = constraint
                fine_commodities.add(emission_default)
                unit = str(config.power_reference_unit) + \
                    '_' + emission_default
                fine_commodityUnitDict.update({emission_default: unit})
            else:
                emission_default = 'emissions'
                for node in tessif_es.nodes:
                    if hasattr(node, 'flow_emissions'):
                        for interface in node.interfaces:
                            if node.flow_emissions[interface] != 0:
                                fine_commodities.add(emission_default)
                                unit = str(config.power_reference_unit) + \
                                    '_' + emission_default
                                fine_commodityUnitDict.update(
                                    {emission_default: unit})

    for constraint in tessif_es.global_constraints:
        if constraint not in spl.emissions and constraint not in fine_commodities:
            fine_commodities.add(constraint)
            unit = str(config.power_reference_unit) + '_' + constraint
            fine_commodityUnitDict.update({str(constraint): unit})

    for node in tessif_es.sources:
        for flow in node.flow_emissions:
            if node.flow_emissions[flow] != 0:
                commodity = node.uid.name + '.unlimitted'
                if commodity not in fine_commodities:
                    fine_commodities.add(commodity)
                    unit = str(config.power_reference_unit) + '_' + commodity
                    fine_commodityUnitDict.update({str(commodity): unit})

    for node in tessif_es.storages:
        for flow in node.flow_emissions:
            if node.flow_emissions[flow] != 0:
                for grid in tessif_es.busses:
                    if node.uid.name + '.' + node.output in grid.interfaces:
                        commodity = grid.uid.name + '.' + node.output + '+' + node.uid.name
                        if commodity not in fine_commodities:
                            fine_commodities.add(commodity)
                            unit = str(config.power_reference_unit) + \
                                '_' + commodity
                            fine_commodityUnitDict.update(
                                {str(commodity): unit})

    return ({'region': fine_region,
             'commodities': fine_commodities,
             'units': fine_commodityUnitDict,
             'emission_default': emission_default})


def parse_flow_parameters(tessif_es, cmp, interface):
    """
    Create FINE's component specific flow parameters out of tessif's components.

    Note
    ----
    FINE define the hasCapacityVariable (boolean) for each component. It is assumed that only Sink (Demand)
    has a False design variable due to the fact it is a given timeseries. Although the design variable is set
    Flase, if the the :paramref:`timeseries <tessif.model.components>`: minimum equals the maximum.
    All other design variables are set to True

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components` objects.

    cmp: collections.abc.Iterable
        Container of the specific components information.

    interface: collections.abc.Iterable
        Flow to be defined in FINE to which important parameters (e.g. costs and capacity) are assigned.

    Return
    ------
    flow_params: dict
        Container of all relevant flow parameters of the specific component.
    """
    esM_params = parse_esM_parameters(tessif_es)
    region = list(esM_params['region'])[0]
    flow_params = dict()
    # Start with declaring the design variable
    flow_params['hasCapacityVariable'] = True
    if cmp in tessif_es.sinks:
        flow_params['hasCapacityVariable'] = False
    if cmp.timeseries is not None:
        if np.array_equal(cmp.timeseries[interface].max, cmp.timeseries[interface].min):
            flow_params['hasCapacityVariable'] = False

            # Usecase of zero cost expample -> uncapped source
            if bool(cmp.expandable[interface]) is True:
                if cmp.expansion_limits[interface].max == float('+inf'):
                    flow_params['hasCapacityVariable'] = True

    # Capacity bounds can only be given for capacityVariable = True
    capacityMin = None
    capacityMax = None
    if flow_params['hasCapacityVariable'] is True:
        if cmp not in tessif_es.transformers and cmp not in tessif_es.storages:
            # Declaring capacities by expansion limit or flow rates
            if bool(cmp.expandable[interface]) is True:
                if cmp.expansion_limits[interface].max != float('+inf'):
                    capacityMax = float(cmp.expansion_limits[interface].max)
                    if cmp.flow_rates[interface].max != float('+inf') and capacityMax < cmp.flow_rates[interface].max:
                        capacityMax = float(cmp.flow_rates[interface].max)
            elif cmp.flow_rates[interface].max != float('+inf'):
                capacityMax = float(cmp.flow_rates[interface].max)

            if bool(cmp.expandable[interface]) is True:
                if cmp.expansion_limits[interface].min != 0.0:
                    capacityMin = float(cmp.expansion_limits[interface].min)
                    if cmp.flow_rates[interface].min != 0 and capacityMin < cmp.flow_rates[interface].max:
                        capacityMin = float(cmp.flow_rates[interface].max)

            elif cmp.flow_rates[interface].min != 0:
                capacityMin = float(cmp.flow_rates[interface].min)

        # Transformers can have multiple given flow rates or expansion limits.
        # The Min/Max Values calculated to the inflow are to be determined
        elif cmp in tessif_es.transformers:
            conv_factors = conversion_factors_identification(tessif_es, cmp)
            # Checking first which frame is the limiting -> expansion outweights the flow_rates if cmp is expandable
            limit_frame = cmp.flow_rates
            for flow in cmp.expansion_limits:
                if bool(cmp.expandable[flow]) is True:
                    if cmp.expansion_limits[flow] != nts.MinMax(min=0, max=float('+inf')):
                        limit_frame = cmp.expansion_limits
            # Multiply outflow values with efficiency and get absolut from inflow and store the min/max as capacity

            if limit_frame is not None:
                for flow in limit_frame:
                    if limit_frame[flow] != nts.MinMax(min=0, max=float('+inf')):
                        for conversion in conv_factors:
                            if flow == conversion.partition('.')[2]:
                                if capacityMax is not None:
                                    if limit_frame[flow].max / abs(conv_factors[conversion]) > capacityMax:
                                        capacityMax = float(
                                            limit_frame[flow].max / abs(conv_factors[conversion]))
                                else:
                                    capacityMax = float(
                                        limit_frame[flow].max / abs(conv_factors[conversion]))
                                if capacityMin is not None:
                                    if limit_frame[flow].min / abs(conv_factors[conversion]) < capacityMin:
                                        capacityMin = float(
                                            limit_frame[flow].min / abs(conv_factors[conversion]))
                                else:
                                    capacityMin = float(
                                        limit_frame[flow].min / abs(conv_factors[conversion]))

        if capacityMax == float('+inf'):
            capacityMax = None
        if capacityMin == 0.0:
            capacityMin = None

        flow_params['capacityMax'] = capacityMax
        flow_params['capacityMin'] = capacityMin

        # Case: Timeseries is given, the exact time values are fixed
        if cmp.timeseries is not None:
            if cmp not in tessif_es.transformers:
                operationRate = pd.DataFrame()
                if all(np.array(cmp.timeseries[interface].max).astype(float) == 0):
                    operationRate = cmp.timeseries[interface].max
                    operationRate = pd.DataFrame({region: operationRate})
                elif capacityMax is not None:
                    if capacityMax < float(max(cmp.timeseries[interface].max)):
                        capacityMax = float(max(cmp.timeseries[interface].max))
                        flow_params['capacityMax'] = capacityMax
                    operationRate = cmp.timeseries[interface].max
                    operationRate = pd.DataFrame(
                        {region: operationRate}) / capacityMax

                elif capacityMin is not None:
                    if capacityMin < float(min(cmp.timeseries[interface].min)):
                        capacityMin = float(min(cmp.timeseries[interface].min))
                        flow_params['capacityMin'] = capacityMin
                    operationRate = cmp.timeseries[interface].max
                    operationRate = pd.DataFrame(
                        {region: operationRate}) / capacityMin

                flow_params['operationRateMax'] = operationRate
            else:
                # Transformer can have different input/outputs -> maximum timeseries value needs to be detected
                # Output related timeseries have to be multiplicated with efficiency and maximum is to be taken
                capacityMin = None
                capacityMax = None
                limit_frame = cmp.timeseries
                for flow in limit_frame:
                    for conversion in conv_factors:
                        if flow == conversion.partition('.')[2]:
                            max_inflow = float(
                                max(limit_frame[flow].max)) / abs(conv_factors[conversion])
                            min_inflow = float(
                                min(limit_frame[flow].min)) / abs(conv_factors[conversion])
                            if all(np.array(cmp.timeseries[interface].max).astype(float) == 0):
                                operationRate = cmp.timeseries[interface].max
                                operationRate = pd.DataFrame(
                                    {region: operationRate})
                            elif capacityMax is not None:
                                if max_inflow > capacityMax:
                                    capacityMax = max_inflow
                                    operationRate = limit_frame[flow].max / \
                                        abs(conv_factors[conversion])
                            else:
                                capacityMax = max_inflow
                                operationRate = limit_frame[flow].max / \
                                    abs(conv_factors[conversion])

                            if capacityMin is not None:
                                if min_inflow < capacityMin:
                                    capacityMin = min_inflow
                            else:
                                capacityMin = min_inflow

                flow_params['capacityMin'] = capacityMin
                flow_params['capacityMax'] = capacityMax
                flow_params['operationRateMax'] = pd.DataFrame(
                    {region: operationRate})

    # Capacity Variable = False mostly representing a sink
    else:
        if cmp.timeseries is not None:
            if interface in cmp.flow_rates:
                flow_params['operationRateFix'] = pd.DataFrame(
                    {region: cmp.timeseries[interface].max})
        else:
            # Enable Variable Sinks (not working yet)
            # if cmp.timeseries is None:
            #     if cmp.flow_rates[interface].max != cmp.flow_rates[interface].min:
            #         flow_params['hasCapacityVariable'] = True
            #         flow_params['capacityMax'] = cmp.flow_rates[interface].max
            #         flow_params['capacityMin'] = cmp.flow_rates[interface].min

            # If one value is present for all time steps and demand is fixed
            if cmp.expansion_limits[interface].max != float('+inf'):
                flow_params['operationRateFix'] = pd.DataFrame(
                    {region: [cmp.expansion_limits[interface].max] * len(tessif_es.timeframe)})
            elif cmp.flow_rates[interface].max != float('+inf'):
                flow_params['operationRateFix'] = pd.DataFrame(
                    {region: [cmp.flow_rates[interface].max] * len(tessif_es.timeframe)})

    # Accumulated Amount of commodity limit. Create only if no timeseries is given
    if cmp not in tessif_es.transformers and cmp not in tessif_es.storages:
        if hasattr(cmp, 'accumulated_amounts'):
            if cmp.timeseries is None:
                if cmp.accumulated_amounts[interface].max != float('+inf'):
                    flow_params['commodityLimitID'] = cmp.uid.name + \
                        '.' + cmp.uid.carrier
                    flow_params['yearlyLimit'] = -(
                        8760 * cmp.accumulated_amounts[interface].max / len(tessif_es.timeframe))

    # Component specific flow parameters
    # Transformer/Conversion -> flow_gradient values can be considered in FINE (dynamic conversion)
    if cmp in tessif_es.transformers:
        if flow_params['hasCapacityVariable'] is True:
            for gradient in cmp.flow_gradients:
                if gradient in cmp.inputs:
                    if cmp.flow_gradients[gradient].positive != float('+inf') and capacityMax != None:
                        if cmp.flow_gradients[gradient].positive < capacityMax:
                            flow_params['rampUpMax'] = float(
                                cmp.flow_gradients[gradient].positive) / capacityMax
                        else:
                            flow_params['rampUpMax'] = 1.0
                    if cmp.flow_gradients[gradient].negative != float('+inf') and capacityMin != None:
                        if cmp.flow_gradients[gradient].negative < capacityMin:
                            flow_params['rampDownMax'] = cmp.flow_gradients[gradient].negative / capacityMax
                        else:
                            flow_params['rampDownMax'] = 1.0

    # Storage parameters
    # Get capacity Values start with getting capacity as interface if needed
    if cmp in tessif_es.storages:
        for cap in cmp.expandable:
            if cap in spl.storage_capacity:
                interface = cap
        if bool(cmp.expandable[interface]) is True:
            capacityMax = cmp.capacity
        else:
            capacityMax = None
            # capacityMax = cmp.capacity  # Matze hat hier Zeilten getauscht

        if bool(cmp.expandable[interface]) is True:
            if interface in cmp.flow_rates:
                if cmp.flow_rates[interface].max != float('+inf'):
                    if cmp.flow_rates[interface].max > capacityMax:
                        capacityMax = cmp.flow_rates[interface].max

            elif cmp.expansion_limits[interface].max != float('+inf'):
                if cmp.expansion_limits[interface].max > capacityMax:
                    capacityMax = cmp.expansion_limits[interface].max
            else:
                capacityMax = None
        flow_params['capacityMax'] = capacityMax

        capacityMin = 0.0
        if bool(cmp.expandable[interface]) is True:
            if interface in cmp.flow_rates:
                if cmp.flow_rates[interface].min != 0.0:
                    if cmp.flow_rates[interface].min < capacityMin:
                        capacityMin = cmp.flow_rates[interface].min

            elif cmp.expansion_limits[interface].min != 0.0:
                if cmp.expansion_limits[interface].min > capacityMin:
                    capacityMin = cmp.expansion_limits[interface].min
        if capacityMin == 0.0:
            capacityMin = None
        flow_params['capacityMin'] = capacityMin

        # The operation rate frame do have different names in the fine storage component
        if hasattr(flow_params, 'operationRateFix'):
            flow_params['chargeOpRateFix'] = flow_params['operationRateFix']
            flow_params.pop('operationRateFix')
        if hasattr(flow_params, 'operationRateMax'):
            flow_params['chargeOpRateMax'] = flow_params['operationRateMax']
            flow_params.pop('operationRateMax')

        output = cmp.output
        if cmp.flow_rates[output].max != float('+inf'):
            if flow_params['capacityMax'] is not None:
                flow_params['dischargeRate'] = cmp.flow_rates[output].max / \
                    flow_params['capacityMax']
                flow_params['chargeRate'] = cmp.flow_rates[output].max / \
                    flow_params['capacityMax']
            elif flow_params['capacityMin'] is not None:
                flow_params['dischargeRate'] = cmp.flow_rates[output].max / \
                    flow_params['capacityMin']
                flow_params['chargeRate'] = cmp.flow_rates[output].max / \
                    flow_params['capacityMin']

        # State of charge for periods
        flow_params['socOffsetDown'] = 0
        if cmp.final_soc is not None:
            if cmp.initial_soc == cmp.final_soc:
                flow_params['socOffsetDown'] = -1

        if cmp.initial_soc == cmp.final_soc:
            flow_params['isPeriodicalStorage'] = True

    # Interest rate is set to 0.08 by default in fine -> setting it to 0.0
    flow_params['interestRate'] = 0.0
    # Economic lifetime is set 10 years by default -> to the len of simulation period
    flow_params['economicLifetime'] = len(tessif_es.timeframe) / 8760

    # Define expansion costs
    for flow in cmp.interfaces:
        if bool(cmp.expandable[flow]) is True:
            if cmp in tessif_es.transformers:
                invest_cost = 0.0
                conv_factors = conversion_factors_identification(
                    tessif_es, cmp)
                for expansion in cmp.expandable:
                    if bool(cmp.expandable[expansion]) is True:
                        for conv in conv_factors:
                            if expansion == conv.partition('.')[2]:
                                invest_cost += float(cmp.expansion_costs[expansion]) * abs(
                                    conv_factors[conv])
            else:
                invest_cost = float(cmp.expansion_costs[interface])

            flow_params['investPerCapacity'] = invest_cost

    return flow_params


def conversion_factors_identification(tessif_es, cmp):
    """
    Create FINE's commodityConversionFactors out of tessif's converions.

    Note
    ----
    Representing the efficiency the inflow
    is always a -1 float and the outflow is taken from tessif conversion.
    Additionally a transformer component can emit the limitation (e.g CO2) itself given in it's
    own tessif flow emissions param as a positive float.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components` objects that have related flow_emissions.

    cmp: tessif component
        Container of the specific components information from the respective Tessif Energy System.

    Return
    ------
    commodityConversionFactors: dictionary, assigns commodities (string) to a conversion factors (float)
        Same parameter as in FINE's conversion component representing the efficiency and the emissions.
    """
    tessif_busses = list(tessif_es.busses)

    commodityConversionFactors = dict()
    for com in cmp.interfaces:
        cmp_com = str(cmp.uid) + '.' + str(com)
        for grid in tessif_busses:
            grid_com = str(grid.uid.name) + '.' + str(com)
            if cmp_com in grid.inputs:
                for conversion in cmp.conversions:
                    if com in conversion:
                        if isinstance(cmp.conversions[conversion], collections.abc.Iterable):
                            commodityConversionFactors.update(
                                {grid_com: pd.Series(cmp.conversions[conversion])})
                        else:
                            commodityConversionFactors.update(
                                {grid_com: float(cmp.conversions[conversion])})
            if cmp_com in grid.outputs:
                commodityConversionFactors.update({grid_com: float(-1)})

    return commodityConversionFactors


def flow_costs_identification(tessif_es):
    """
    Create Tessif costs for later use in es2mapping out of Tessif's objects.

    Note
    ----
    Since FINE's component's can only relate one specific cost to the process, it is neccessary to
    hand over the exact given ones through tessif. They are calculated to one value out of the single ones during
    the transformation process.

    Parameters
    ----------
    tessif_es: ~AbstractEnergySystem
        Container of itarable :class:`tessif.model.components` objects that have related flow_emissions.

    Return
    ------
    flow_costs: dict
        to use them later in the es2mapping for correct post processing.
    """
    flow_costs = dict()
    for node in tessif_es.nodes:
        if hasattr(node, 'flow_costs'):
            if len(node.flow_costs) == 1:
                for flow in node.flow_costs:
                    value = float(node.flow_costs[flow])
            else:
                value = dict()
                for flow in node.flow_costs:
                    # Identify the grid in which the source is feeding
                    for grid in tessif_es.busses:
                        for interface in grid.outputs:
                            if flow == interface.partition('.')[2]:
                                value.update(
                                    {grid.uid.name: float(node.flow_costs[flow])})

            flow_costs.update({node.uid.name: value})
        else:
            flow_costs.update({node.uid.name: 0.0})

    # Since Connectors are not in tessif nodes this fragment is needed to remind them in flow costs
    for connector in tessif_es.connectors:
        if connector.uid.name not in flow_costs:
            flow_costs.update({connector.uid.name: 0.0})

    # Store single values as float and not as series
    for node in flow_costs:
        if isinstance(flow_costs[node], abc.Iterable):
            if len(flow_costs[node]) == 1:
                flow_costs[node] = float(list(flow_costs[node].values())[0])
            elif len(flow_costs[node]) == 0:
                flow_costs[node] = 0.0

    return flow_costs


def flow_emissions_identification(tessif_es):
    """
    Create Tessif emission for later use in es2mapping out of Tessif's emitting objects.

    Note
    ----
    Since FINE's conversion component can only relate one specific emission to the process, it is neccessary to
    hand over the exact given through tessif. They are calculated to one value out of the single ones.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components` objects that have related flow_emissions.

    Return
    ------
    flow_emissions: dict
        to use them later in the es2mapping for correct post processing.
    """
    flow_emissions = dict()
    for node in tessif_es.nodes:
        if hasattr(node, 'flow_emissions'):
            if len(node.flow_emissions) == 1:
                for emissions in node.flow_emissions:
                    value = float(node.flow_emissions[emissions])
            else:
                value = dict()
                # Identify the grid in which the source is feeding
                for emissions in node.flow_emissions:
                    for grid in tessif_es.busses:
                        for interface in grid.outputs:
                            if emissions == interface.partition('.')[2]:
                                value.update({grid.uid.name: float(
                                    node.flow_emissions[emissions])})

            flow_emissions.update({node.uid.name: value})
        else:
            flow_emissions.update({node.uid.name: 0.0})

    # Store single values as float and not as series
    for node in flow_emissions:
        if isinstance(flow_emissions[node], abc.Iterable):
            if len(flow_emissions[node]) == 1:
                flow_emissions[node] = float(
                    list(flow_emissions[node].values())[0])
            elif len(flow_emissions[node]) == 0:
                flow_emissions[node] = 0.0

    return flow_emissions


def expansion_costs_identification(tessif_es):
    """
    Create Tessif expansion costs for later use in es2mapping out of Tessif's objects.

    Note
    ----
    Since FINE's component's can only relate one specific cost to the process, it is neccessary to
    hand over the exact given ones through tessif. They are calculated to one value out of the single ones during
    the transformation process.

    Parameters
    ----------
    tessif_es: ~AbstractEnergySystem
        Container of itarable :class:`tessif.model.components` objects that have related invest per capacity.

    Return
    ------
    expansion_costs: dict
        to use them later in the es2mapping for correct post processing.
    """
    expansion_costs = dict()
    for node in tessif_es.nodes:
        if hasattr(node, 'expansion_costs'):
            if len(node.expansion_costs) == 1:
                for flow in node.expansion_costs:
                    value = float(node.expansion_costs[flow])
            else:
                value = dict()
                for expansion in node.expansion_costs:
                    if node.expansion_costs[expansion] != 0:
                        if expansion in spl.storage_capacity:
                            value.update(
                                {expansion: float(node.expansion_costs[expansion])})
                    if node not in tessif_es.storages:
                        # Identify the grid in which the cmp is feeding
                        for grid in tessif_es.busses:
                            for interface in grid.outputs:
                                if expansion == interface.partition('.')[2] and interface.partition('.')[2] in node.outputs:
                                    value.update({grid.uid.name: float(
                                        node.expansion_costs[expansion])})
                value = pd.Series(value)
            expansion_costs.update({node.uid.name: value})
        else:
            expansion_costs.update({node.uid.name: 0.0})

    # Since Connectors are not in tessif nodes this fragment is needed to remind them in flow costs
    for connector in tessif_es.connectors:
        if connector.uid.name not in expansion_costs:
            expansion_costs.update({connector.uid.name: 0.0})

    # Store single values as float and not as series
    for node in expansion_costs:
        if isinstance(expansion_costs[node], abc.Iterable):
            if len(expansion_costs[node]) == 1:
                expansion_costs[node] = float(expansion_costs[node].values[0])
                # for k, v in expansion_costs[node].items():
                #     expansion_costs[node] = float(v)
            elif len(expansion_costs[node]) == 0:
                expansion_costs[node] = 0.0

    return expansion_costs


def create_FINE_busses(tessif_es):
    """
    Create FINE Transmissions out of Tessif's Busses.

    Parameters
    ----------
    tessif_es: ~AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Bus` objects that are to
        be transformed into FINE's transmission objects.

    Return
    ------
    fine_bus_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`bus objects`
    """
    tessif_busses = list(tessif_es.busses)
    esM_params = parse_esM_parameters(tessif_es)
    fine_commodities = esM_params['commodities']
    fine_bus_dicts = list()

    for bus in tessif_busses:
        cmp = bus
        commodity = str()

        # Grid commodities should always be the same
        for interface in cmp.interfaces:
            commodity = cmp.uid.name + '.' + interface.partition('.')[2]

        fine_bus_dicts.append(
            {'name': str(cmp.uid),
             'commodity': commodity,
             'hasCapacityVariable': True, })

    return fine_bus_dicts


def create_FINE_sources(tessif_es):
    """
    Create FINE Sources out of Tessif's Sources.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Source` objects that are to
        be transformed into FINE's Source objects.

    Return
    ------
    fine_sources_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Source objects`
    """
    tessif_sources = list(tessif_es.sources)

    fine_sources_dicts = list()
    for source in tessif_sources:
        cmp = source
        for grid in tessif_es.busses:
            for interface in grid.inputs:
                if cmp.uid.name == interface.partition('.')[0]:
                    output = interface.partition('.')[2]
                    commodity = grid.uid.name + '.' + output

        # Check if source has emissions -> if so treat it as transformer (emitting source later)

        if cmp.flow_emissions[output] == 0:
            fine_source = {
                'name': str(source.uid),
                'commodity': commodity,
                'opexPerOperation': float(cmp.flow_costs[output]),
            }

            fine_source.update(parse_flow_parameters(tessif_es, cmp, output))

            fine_sources_dicts.append(fine_source)

    return fine_sources_dicts


def create_FINE_sinks(tessif_es):
    """
    Create FINE Sinks out of Tessif's Sinks.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Sink` objects that are to
        be transformed into FINE's Sink objects.

    Return
    ------
    fine_sources_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Sink objects`
    """
    tessif_sinks = list(tessif_es.sinks)

    fine_sinks_dicts = list()
    for sink in tessif_sinks:
        cmp = sink
        # Component commodity needs to fit the grid commodity uid
        for grid in tessif_es.busses:
            for interface in grid.interfaces:
                if cmp.uid.name == interface.partition('.')[0]:
                    commodity = grid.uid.name + '.' + \
                        interface.partition('.')[2]

                    for input in cmp.inputs:
                        fine_sink = {
                            'name': str(sink.uid),
                            'commodity': commodity,
                            'opexPerOperation': float(cmp.flow_costs[input]),
                            # 'commodityRevenue': cmp.flow_costs[input]
                        }

                        fine_sink.update(
                            parse_flow_parameters(tessif_es, cmp, input))

                        fine_sinks_dicts.append(fine_sink)

                        expandable = cmp.expandable[input]
                        expansion_costs = cmp.expansion_costs[input]
                        inst_cap = cmp.flow_rates[input].max
                        min_exp = cmp.expansion_limits[input].min
                        max_exp = cmp.expansion_limits[input].max

                        # expansion limits are specifics of installed capacity
                        if inst_cap != float("inf"):
                            min_expansion = min_exp / inst_cap
                            # cap lower end of min exp at 1
                            min_expansion = max(min_expansion, 1)
                            if max_exp == float("inf"):
                                max_expansion = max_exp
                            else:
                                max_expansion = 1
                        else:
                            min_expansion = 1
                            max_expansion = 1

                        if expandable:
                            fine_sink["hasCapacityVariable"] = expandable
                            fine_sink["investPerCapacity"] = expansion_costs
                            fine_sink["capacityMin"] = min_expansion
                            fine_sink["capacityMax"] = max_expansion

    return fine_sinks_dicts


def create_FINE_conversions(tessif_es):
    """
    Create FINE Conversion (dynamic) out of Tessif's Transformer.

    Note
    ----
    FINE's conversion parameters are related to the inflow. Tessif's parameters are related to the
    outflow, which means a recalculation is taking place.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Transformer` objects that are to
        be transformed into FINE's conversion objects.

    Return
    ------
    fine_transformer_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Conversion objects`
    """
    tessif_transformers = list(tessif_es.transformers)
    esM_params = parse_esM_parameters(tessif_es)
    fine_units = esM_params['units']
    emission_default = esM_params['emission_default']
    fine_conversions_dict = list()

    for transformer in tessif_transformers:
        cmp = transformer

        # Component commodity needs to fit the grid commodity uid which flows into the transformer (ergo is grid output)
        for grid in tessif_es.busses:
            for interface in grid.outputs:
                if cmp.uid.name == interface.partition('.')[0]:
                    grid_unit = interface.partition('.')[2]
                    commodity = grid.uid.name + '.' + grid_unit
                    physicalUnit = fine_units[commodity]

        input = grid_unit
        conversion_factors = conversion_factors_identification(tessif_es, cmp)
        fine_conversion = (
            {'name': str(transformer.uid),
             'commodityConversionFactors': conversion_factors,
             'physicalUnit': physicalUnit, })

        fine_conversion.update(parse_flow_parameters(tessif_es, cmp, input))

        # Recalculating the tessif outflow specific paramters to fine's inflow specific parameters
        opex = 0.0
        emissions = 0.0
        for interface in cmp.interfaces:
            for conversion in conversion_factors:
                com = conversion.partition('.')[2]
                if interface == com:
                    if interface in cmp.flow_costs:
                        opex += cmp.flow_costs[interface] * \
                            abs(conversion_factors[conversion])
                    if interface in cmp.flow_emissions:
                        emissions += cmp.flow_emissions[interface] * \
                            abs(conversion_factors[conversion])

        if isinstance(opex, collections.abc.Iterable):

            prt1 = "Current tessif -> fine transformation does not "
            prt2 = "support time varying efficiencies."
            logger.warning(prt1 + prt2)
            logger.warning("Average of stated efficiency is used.")
            logger.warning("This also impacts allocated emissions..")
            opex = np.mean(opex)
            emissions = np.mean(emissions)

        else:
            opex = float(opex)
            emissions = float(emissions)

        fine_conversion['opexPerOperation'] = opex
        fine_conversion['commodityConversionFactors'].update(
            {emission_default: emissions})

        fine_conversions_dict.append(fine_conversion)

    return fine_conversions_dict


def create_FINE_storages(tessif_es):
    """
    Create FINE Storage out of Tessif's Storage.

    Note
    ----
    FINE's Storage is not able to handle flow related emissions. All results are calculated without those emissions.
    Further, the initial and final SOC is yet not to be adjusted by the user. This causes different results between
    the models for some py_hard examples.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Storage` objects that are to
        be transformed into FINE's Storage objects.

    Return
    ------
    fine_storage_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Storage objects`

    Warning:
    -------
        If an initial state of charge is given, a warning is issued and further optimization is done without any SOC.

        The self-discharge in FINE is normalized, which is why a warning is given as soon
        as no initial capacity is specified, but a self-discharge rate.

    """
    tessif_storages = list(tessif_es.storages)
    esM_params = parse_esM_parameters(tessif_es)

    fine_storages_dicts = list()
    for storage in tessif_storages:
        cmp = storage
        commodity = str()

        # Component commodity needs to fit the grid commodity uid
        for grid in tessif_es.busses:
            for interface in grid.outputs:
                if cmp.uid.name == interface.partition('.')[0]:
                    commodity = grid.uid.name + '.' + \
                        interface.partition('.')[2]

        # Declare if interface for storage are capacity or flow related
        interface = storage.output
        for capacity in spl.storage_capacity:
            if capacity in cmp.expandable:
                if bool(cmp.expandable[capacity]) is True:
                    interface = capacity

        if cmp.flow_emissions[cmp.output] == 0:
            fine_storage = (
                {'name': str(storage.uid),
                 'commodity': commodity,
                 'chargeEfficiency': float(cmp.flow_efficiencies[cmp.output].inflow),
                 'dischargeEfficiency': float(cmp.flow_efficiencies[cmp.output].outflow),
                 'opexPerDischargeOperation': float(cmp.flow_costs[cmp.output]),
                 # 'selfDischarge': cmp.idle_changes.negative/cmp.capacity,
                 }
            )

            fine_storage.update(parse_flow_parameters(
                tessif_es, cmp, interface))

            # self discharge (idle change) is normalized in FINE but not in tessif
            # use already identified capacity from storage
            if cmp.idle_changes.negative is not None:
                if cmp.capacity != 0.0:
                    fine_storage['selfDischarge'] = cmp.idle_changes.negative / cmp.capacity
                else:
                    fine_storage['selfDischarge'] = cmp.idle_changes.negative
                    if cmp.idle_changes.negative != 0.0:
                        msg = (
                            "No start capacity for " +
                            f"'{cmp.uid.name}' is given, but a loss rate '{cmp.idle_changes.negative}' "
                            "FINE needs to get an normalized value. "
                        )
                        logger.warning(msg)

            if cmp.initial_soc != 0:
                msg = (
                    "Requested initial state of charge " +
                    f"'{cmp.initial_soc}' for '{cmp.uid.name}' "
                    "All FINE results are calculated with a variable initial and final SOC  "
                )
                logger.warning(msg)

            fine_storages_dicts.append(fine_storage)

    return fine_storages_dicts


def create_FINE_connectors(tessif_es):
    """
    Create FINE Connector as double conversion out of Tessif's Connector.

    Note
    ----
    A conversion component is used that converts a single inflow (-1) to a single outflow (+1)
    without losses. Since a connector can work in both directions, two conversion components
    must be created, with opposite flows.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Connector` objects that are to
        be transformed into FINE's conversion (twice) objects.

    Return
    ------
    fine_connector_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Connector objects`
    """
    tessif_connectors = list(tessif_es.connectors)
    esM_params = parse_esM_parameters(tessif_es)
    fine_units = esM_params['units']

    fine_connector_dicts = list()
    for connector in tessif_connectors:
        cmp = connector
        reverse_flow_count = 0
        for conversion in cmp.conversions:
            fine_connector = dict()

            fine_connector['name'] = str(connector.uid)

            if reverse_flow_count == 1:
                fine_connector['name'] = str(connector.uid) + '.reverse'
            # Reverse is indicator for second transformer representing the returning flow
            commodityConversionFactors = dict()
            inflow = conversion[0]
            outflow = conversion[1]

            # physicalUnit representing the connector output
            physicalUnit = str()
            grid_com = str()
            for grid in tessif_es.busses:
                if grid.uid.name == outflow:
                    for output in grid.outputs:
                        grid_com = output.partition('.')[2]
                    physicalUnit = fine_units[outflow + '.' + grid_com]

            fine_connector['physicalUnit'] = physicalUnit

            commodityConversionFactors.update(
                {inflow + '.' + grid_com: float(-1)})
            commodityConversionFactors.update(
                {outflow + '.' + grid_com: float(cmp.conversions[conversion])})

            fine_connector['commodityConversionFactors'] = commodityConversionFactors

            fine_connector_dicts.append(fine_connector)
            reverse_flow_count = reverse_flow_count + 1

    return fine_connector_dicts


def create_FINE_constraints(tessif_es):
    """
    Create FINE Emission Constraints as sink out of Tessif's global constraints.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container the global constraint limiting the optimization process.

    Return
    ------
    fine_constraints_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Constraints objects`
    """
    fine_constraints_dict = list()
    esM_params = parse_esM_parameters(tessif_es)
    commodities = esM_params['commodities']
    emission_default = esM_params['emission_default']

    for constraint in tessif_es.global_constraints:
        if isinstance(tessif_es.global_constraints[constraint], numbers.Number):
            if tessif_es.global_constraints[constraint] != float('+inf'):
                if len(tessif_es.timeframe) < 8760:
                    yearlyLimit = 8760 * \
                        tessif_es.global_constraints[constraint] / \
                        len(tessif_es.timeframe)
                else:
                    yearlyLimit = tessif_es.global_constraints[constraint]
            # else:
            #     yearlyLimit = 1000000000000000  # Ask if this is ok?
                for com in commodities:
                    if com == constraint:
                        commodity = constraint
                fine_constraint = {
                    'name': constraint,
                    'commodity': commodity,
                    'hasCapacityVariable': False,
                    'commodityLimitID': constraint,
                    'yearlyLimit': yearlyLimit
                }

                fine_constraints_dict.append(fine_constraint)

            else:
                for com in commodities:
                    if com == constraint:
                        commodity = constraint
                fine_constraint = {
                    'name': constraint,
                    'commodity': commodity,
                    'hasCapacityVariable': True,
                }

                fine_constraints_dict.append(fine_constraint)

    return fine_constraints_dict


def conversion_as_emitting_sources(tessif_es):
    """
    Create FINE conversion out of Tessif's emitting sources.

    Note
    ----
    Since FINE's sources can't have related specific emissions,
    a corresponding conversion component needs to be created. This transformer is fed by an unlimitted
    source without any limitations. All flow parameters are related to this transformer,
    which contains the flow emissions as well as the flow itself with given parameters.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Source` objects that have related flow_emissions.

    Return
    ------
    fine_emitting_source_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Conversion objects`
    """
    esM_params = parse_esM_parameters(tessif_es)
    fine_emission_sources_dict = list()
    fine_emission_grids_dict = list()
    fine_conversion_emissions_dict = list()
    emission_default = esM_params['emission_default']

    for cmp in tessif_es.sources:
        for flow in cmp.flow_emissions:
            # Check if source has emissions
            if cmp.flow_emissions[flow] != 0:
                # Identify the grid in which the source is feeding
                for grid in tessif_es.busses:
                    for interface in grid.interfaces:
                        if cmp.uid.name == interface.partition('.')[0]:
                            commodity = grid.uid.name + '.' + \
                                interface.partition('.')[2]
                # Adding unlimitted source to the esM
                fine_emission_source = {
                    'name': cmp.uid.name + '.unlimitted',
                    'commodity': cmp.uid.name + '.unlimitted',
                    'hasCapacityVariable': True, }
                fine_emission_sources_dict.append(fine_emission_source)

                # Adding transformer/conversion as source producing the commodity and the emission
                conversion_factors = {cmp.uid.name + '.unlimitted': -1, commodity: 1,
                                      emission_default: float(cmp.flow_emissions[flow])}

                fine_emission_conversion = {
                    'name': cmp.uid.name,
                    'physicalUnit': esM_params['units'][commodity],
                    'commodityConversionFactors': conversion_factors,
                    'opexPerOperation': float(cmp.flow_costs[flow])
                }

                fine_emission_conversion.update(
                    parse_flow_parameters(tessif_es, cmp, flow))

                fine_conversion_emissions_dict.append(fine_emission_conversion)

    return {'Sources': fine_emission_sources_dict,
            'Source_Conversions': fine_conversion_emissions_dict}


def conversion_as_emitting_storage(tessif_es):
    """
    Create FINE conversions out of Tessif's emitting storages and the storage itself.

    Note
    ----
    This fragment is crucial if the actual used storages do have any emissions
    - if conversion components added to the es which charge/discharge the storage.
    - Storage commodity is renamed due to precise formulation for the optimization process -> name it back later
    - conversion input/output need to be deleted for post processing capabillities

    FINE's Storage is not able to handle flow related emissions. All results are calculated without those emissions.
    Further, the initial and final SOC is yet not to be adjusted by the user. This causes different results between
    the models for some py_hard examples.

    Parameters
    ----------
    tessif_es: AbstractEnergySystem
        Container of itarable :class:`tessif.model.components.Storage` objects that have related flow_emissions.

    Return
    ------
    fine_emission_storages_dict: collections.abc.Iterable
        Dictionary object containing the transformed :class:`Storage objects`
    storage_conversions_dict: collections.abc.Iterable
        Dictionary object containing the storage related :class:`Conversion objects`

    Warning:
    -------
        If an initial state of charge is given, a warning is issued and further optimization is done without any SOC.

        The self-discharge in FINE is normalized, which is why a warning is given as soon
        as no initial capacity is specified, but a self-discharge rate.

    """
    esM_params = parse_esM_parameters(tessif_es)
    emission_default = esM_params['emission_default']

    fine_emission_storages_dict = list()
    storage_conversions_dict = list()

    for cmp in tessif_es.storages:
        for flow in cmp.flow_emissions:
            # Check if source has emissions
            if cmp.flow_emissions[flow] != 0:
                # Identify the grid in which the source is feeding
                for grid in tessif_es.busses:
                    for interface in grid.interfaces:
                        if cmp.uid.name == interface.partition('.')[0]:
                            commodity = grid.uid.name + '.' + \
                                interface.partition('.')[2]

                conversion_factors = {commodity: -1,
                                      commodity + '+' + cmp.uid.name: 1, }

                # Adding batterie charge to the esM
                input_conversion = {
                    'name': cmp.uid.name + '.input',
                    'hasCapacityVariable': True,
                    'physicalUnit': esM_params['units'][commodity+'+'+cmp.uid.name],
                    'commodityConversionFactors': conversion_factors,
                }

                storage_conversions_dict.append(input_conversion)

                # Declare if interface for storage are capacity or flow related
                interface = cmp.output
                for capacity in spl.storage_capacity:
                    if capacity in cmp.expandable:
                        if bool(cmp.expandable[capacity]) is True:
                            interface = capacity

                fine_storage = (
                    {'name': str(cmp.uid),
                     'commodity': commodity + '+' + cmp.uid.name,
                     'chargeEfficiency': float(cmp.flow_efficiencies[cmp.output].inflow),
                     'dischargeEfficiency': float(cmp.flow_efficiencies[cmp.output].outflow),
                     'opexPerDischargeOperation': float(float(cmp.flow_costs[cmp.output])),
                     # Check default of tessif
                     # 'selfDischarge': cmp.idle_changes.negative/cmp.capacity,
                     }
                )

                fine_storage.update(parse_flow_parameters(
                    tessif_es, cmp, interface))

                # self discharge (idle change) is normalized in FINE but not in tessif
                # use already identified capacity from storage
                if cmp.idle_changes.negative is not None:
                    if cmp.capacity != 0.0:
                        fine_storage['selfDischarge'] = float(
                            cmp.idle_changes.negative / cmp.capacity)
                    else:
                        fine_storage['selfDischarge'] = float(
                            cmp.idle_changes.negative)
                        if cmp.idle_changes.negative != 0.0:
                            msg = (
                                "No start capacity for " +
                                f"'{cmp.uid.name}' is given, but a loss rate '{cmp.idle_changes.negative}' "
                                "FINE needs to get an normalized value. "
                            )
                            logger.warning(msg)

                fine_emission_storages_dict.append(fine_storage)

                conversion_factors = {commodity: 1, commodity + '+' + cmp.uid.name: -1,
                                      emission_default: float(cmp.flow_emissions[flow])}

                # Adding batterie discharge with emissions to the esM
                output_conversion = {
                    'name': cmp.uid.name + '.output',
                    'hasCapacityVariable': True,
                    'physicalUnit': esM_params['units'][commodity+'+'+cmp.uid.name],
                    'commodityConversionFactors': conversion_factors,
                }

                storage_conversions_dict.append(output_conversion)

    return {'Storage': fine_emission_storages_dict,
            'Storage_Conversions': storage_conversions_dict, }


def transform(tessif_es, **kwargs):
    """
    Transform a tessif energy system into a fine energy system.

    Parameters
    ----------
    tessif_es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        The tessif energy system that is to be transformed into an
        fine energy system.

    Return
    ------
    esM: :class:`FINE.energySystemModel.EnergySystemModel`
        The fine energy system that was transformed out of the tessif
        energy system.

    Examples
    --------
    Use the :ref:`example hub's <Examples>`
    :meth:`~tessif.examples.data.tsf.py_hard.create_storage_example` utility for showcasing
    basic usage:

    1. Create the a storage example:

        >>> from tessif.examples.data.tsf.py_hard import create_storage_example
        >>> tessif_es = create_storage_example()

    2. Transform the :mod:`tessif energy system
       <tessif.model.energy_system.AbstractEnergySystem>`:

        >>> fine_es = transform(tessif_es)

    3. Simulate the fine energy system:

        >>> import tessif.simulate as simulate
        >>> optimized_fine_es = simulate.fine_from_es(fine_es)

    4. Extract some results:

        >>> import tessif.transform.es2mapping.fine as transform_fine_results
        >>> load_results = transform_fine_results.LoadResultier(optimized_fine_es)
        >>> print(load_results.node_load['Powerline'])
        Powerline            Generator  Storage  Demand  Storage
        1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
        1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
        1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
        1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
        1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0
    """
    esM_params = parse_esM_parameters(tessif_es)
    esM = fn.energySystemModel.EnergySystemModel(
        locations=esM_params['region'],
        commodities=esM_params['commodities'],
        commodityUnitsDict=esM_params['units'],
        numberOfTimeSteps=len(tessif_es.timeframe),
        hoursPerTimeStep=1,
        costUnit=config.cost_unit,
        verboseLogLevel=2,
    )
    # Adding Timesteps to the energy system model for post processing.
    setattr(esM, 'timesteps', tessif_es.timeframe)

    # Adding UID's from tessif's energy system to FINE's
    uids = dict()
    for node in tessif_es.nodes:
        uids.update({str(node.uid): node.uid})
    setattr(esM, 'uid_dict', uids)

    # Adding the default for emission to the energy system
    emission_default = esM_params['emission_default']
    setattr(esM, 'emission_default', emission_default)

    # Adding the flow costs for single and multiple flow cmp's to the esM
    flow_costs = flow_costs_identification(tessif_es)
    setattr(esM, 'flow_costs', flow_costs)

    # Adding the flow costs for single and multiple flow cmp's to the esM
    expansion_costs = expansion_costs_identification(tessif_es)
    setattr(esM, 'expansion_costs', expansion_costs)

    # Adding the flow costs for single and multiple flow cmp's to the esM
    flow_emissions = flow_emissions_identification(tessif_es)
    setattr(esM, 'flow_emissions', flow_emissions)

    # Lead developer hack, cause he doesnt know what hes doin
    sink_str_reprs = [str(sink.uid) for sink in tessif_es.sinks]
    setattr(esM, "sinks", sink_str_reprs)

    # Adding busses to the respective energy system model
    fine_busses = list(create_FINE_busses(tessif_es))
    energy_system_components = list()
    energy_system_components.extend(fine_busses)
    for bus_dict in fine_busses:
        esM.add(fn.Transmission(esM=esM, **bus_dict))

    # Adding sources to the respective energy system model
    fine_sources = list(create_FINE_sources(tessif_es))
    energy_system_components.extend(fine_sources)
    for source_dict in fine_sources:
        esM.add(fn.Source(esM=esM, **source_dict))

    # Adding sinks to the respective energy system model
    fine_sinks = list(create_FINE_sinks(tessif_es))
    energy_system_components.extend(fine_sinks)
    for sink_dict in fine_sinks:
        esM.add(fn.Sink(esM=esM, **sink_dict))

    # Adding transformer to the respective energy system model
    fine_conversions = list(create_FINE_conversions(tessif_es))
    energy_system_components.extend(fine_conversions)
    for conversion_dict in fine_conversions:
        if 'rampUpMax' in conversion_dict.keys() or 'rampDownMax' in conversion_dict.keys():
            esM.add(fn.ConversionDynamic(esM=esM, **conversion_dict))
        else:
            esM.add(fn.Conversion(esM=esM, **conversion_dict))

    # Adding storages to the respective energy system model
    fine_storages = list(create_FINE_storages(tessif_es))
    energy_system_components.extend(fine_storages)
    for storages_dict in fine_storages:
        esM.add(fn.Storage(esM=esM, **storages_dict))

    # Adding Connector as Transformer to the respective energy system model
    fine_connectors = list(create_FINE_connectors(tessif_es))
    energy_system_components.extend(fine_connectors)
    for connectors_dict in fine_connectors:
        esM.add(fn.Conversion(esM=esM, **connectors_dict))

    # Adding Sink as Emission Constraint to the respective energy system model
    fine_constraints_dict = list(create_FINE_constraints(tessif_es))
    energy_system_components.extend(fine_constraints_dict)
    for fine_constraint_dict in fine_constraints_dict:
        esM.add(fn.Sink(esM=esM, **fine_constraint_dict))

    # Adding Source Emissions to the respective energy system model
    fine_source_emissions_dict = list(
        conversion_as_emitting_sources(tessif_es)['Sources'])
    energy_system_components.extend(fine_source_emissions_dict)
    for source_emission_dict in fine_source_emissions_dict:
        esM.add(fn.Source(esM=esM, **source_emission_dict))
    fine_conversion_emissions_dict = list(
        conversion_as_emitting_sources(tessif_es)['Source_Conversions'])
    energy_system_components.extend(fine_conversion_emissions_dict)
    for conversion_emission_dict in fine_conversion_emissions_dict:
        esM.add(fn.Conversion(esM=esM, **conversion_emission_dict))

    # Adding Storage Emissions to the respective energy system model
    fine_storage_conversion_emissions_dict = list(
        conversion_as_emitting_storage(tessif_es)['Storage_Conversions'])
    energy_system_components.extend(fine_storage_conversion_emissions_dict)
    for conversion_storage_emission_dict in fine_storage_conversion_emissions_dict:
        esM.add(fn.Conversion(esM=esM, **conversion_storage_emission_dict))
    fine_storage_emissions_dict = list(
        conversion_as_emitting_storage(tessif_es)['Storage'])
    energy_system_components.extend(fine_storage_emissions_dict)
    for storage_emission_dict in fine_storage_emissions_dict:
        esM.add(fn.Storage(esM=esM, **storage_emission_dict))

    return esM
