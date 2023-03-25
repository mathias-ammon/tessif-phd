"""
:mod:`tessif.transform.es2es.cllp` is a :mod:`tessif` module aggregating all the
functionality for automatically transforming a :class:`tessif energy system
<tessif.model.energy_system.AbstractEnergySystem>` into an
:class:`calliope energy system <calliope.core.model.Model>`.

Also the model data will be saved in .yaml and .csv files in calliope style.
This way these files can be used to be extended with calliope specific parameters
which might not be supported by tessif. If this is done, native calliope post processing
functions need to be used for analysing the model restults.
"""
import logging

import os
import ruamel.yaml
import numpy as np
import pandas as pd
import math
import calliope
import itertools

from tessif.frused.paths import write_dir


logger = logging.getLogger(__name__)


class MyDumper(ruamel.yaml.RoundTripDumper):
    """
    Dumper class to raise human readability of the written yaml files
    by creating Blank lines between the different technologies.
    Adapted class MyDumper from -->  https://github.com/yaml/pyyaml/issues/127
    """

    def write_line_break(self, data=None):
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()
        if len(self.indents) == 2:
            super().write_line_break()


def parse_flow_parameters(component, target, timesteps):
    """
    Utility to parse flow related parameters from :mod:`Tessif components
    <tessif.model.components>` to `Calliope components
    <https://calliope.readthedocs.io/en/stable/user/config_defaults.html>`_

    Parameters
    ----------
    component:
        Tessif component of which it's flow related parameters are parsed
        into calliope recognizable parameters

    target: str
        String representing the flow related interface from the components
        point of view.

    timesteps: int
        Integer representing number of timesteps.

    Return
    ------
    flow_params: dict
        Dictionary representing the parsed flow parameters ready to be used
        as key word arguments for creating calliope components. In special cases the
        dict will be adjusted in another function.

    Warning
    -------
    Component has different negative and positive flow gradient. Calliope sets gradient
    as a single value for both directions. Falling back on negative gradient for calliope.

    Calliope does not have installed capacities. The calliope min expansion is used
    to portray the installed capacity, this results in the tessif min expansion
    to not be able to be covered by calliope.

    Calliope storages only use one efficiency value for both directions. Falling
    back to outflow efficiency for both directions in case inflow and outflow are not the same.


    Calliope considers storage initial soc and storage loss as fraction of its capacity,
    so the initial soc and storage loss is set to Zero if the capacity is zero or infinity.
    Furthermore the initial soc will be set to Zero if it is set variable in tessif, due
    to Calliope not being able to handle a variable initial soc.

    If capacity is zero the the flow rates minimum is ignored cause calliope uses relative values.
    If capacity is infinity the flow rates will be min 0 and max 1 as relative values.

    Calliope does not have installed capacities. The calliope min expansion is used
    to portray the installed capacity, this results in the tessif min expansion
    to not be able to be covered by calliope.

    Maximum expansion limit is below current installed capacity. Falling back on current
    installed capacity as expansion maximum.

    Calliope doesnt support tessif's milp parameters. Thus they will be ignored.
    """

    flow_params = dict()

    flow_params.update(
        {
            'energy_cap_min': float(component.flow_rates[target].max),
            'energy_cap_max': float(component.flow_rates[target].max),
            'energy_cap_min_use': float(component.flow_rates[target].min) / float(component.flow_rates[target].max),
            'energy_eff': 1,  # adjusted in generate_calliope_conversion for transformers
            'energy_ramping': True,  # otherwise energy production will be constant
        }
    )

    if component.flow_rates[target].max == float('inf'):
        flow_params.update(
            {'energy_cap_min': 0,  # can not expand to infinity even if no cost are given
             'energy_cap_min_use': 0,
             }
        )

    if hasattr(component, 'flow_gradients'):
        if component.flow_gradients[target].positive < component.flow_rates[target].max:
            flow_params.update({
                'energy_ramping': component.flow_gradients[target].positive/component.flow_rates[target].max})
        elif component.flow_gradients[target].negative < component.flow_rates[target].max:
            flow_params.update({
                'energy_ramping': component.flow_gradients[target].negative / component.flow_rates[target].max})
        if component.flow_gradients[target].positive != component.flow_gradients[target].negative:
            msg = (
                f"'{component}' has different negative '{component.flow_gradients[target].negative}' "
                f"and positive '{component.flow_gradients[target].positive}' flow gradients. "
                f"Calliope considers only one value in both directions. "
                f"Falling back on the given negative flow gradient '{component.flow_gradients[target].negative}'. "
            )
            logger.warning(msg)

    if hasattr(component, 'accumulated_amounts'):
        flow_params.update(
            {
                'resource': float(component.accumulated_amounts[f'{target}'].max),
            }
        )

    if component.expandable[target] and 'storage' not in str(type(component)).lower():

        cap_max = component.expansion_limits[target].max
        flow_params.update(
            {
                'energy_cap_min': float(component.flow_rates[target].max),
                'energy_cap_max': cap_max,
                # lifetime is not a thing in Tessif, but needed for exp costs in calliope,
                'lifetime': timesteps/8760,
                #                            so it is assumed to be timeframe lenght
            }
        )

        if component.flow_rates[target].max == float('inf'):
            flow_params.update(
                {'energy_cap_min': 0,  # can not expand to infinity even if no cost are given
                 'energy_cap_min_use': 0,
                 }
            )

        # calliope assumes initial capacities to be zero,
        # so forcing expansion if expandable is needed to avoid negative expansion costs
        if component.expansion_limits[target].min != component.flow_rates[target].max:
            msg = (
                f"{component.uid.name}: Calliope does not have installed capacities. "
                f"The calliope min expansion is used to portray the installed capacity "
                f"'{component.flow_rates[target].max}', this results in the tessif min expansion "
                f"'{component.expansion_limits[target].min}' to not be able to be covered by calliope."
            )
            logger.warning(msg)

        if component.timeseries:
            flow_params.update(
                {
                    'resource_unit': 'energy_per_cap',  # to allow expansion on timeseries components
                    #                                     the resource has to be relatively to energy_cap
                }
            )

    if 'storage' in str(type(component)).lower():
        eff_in = component.flow_efficiencies[component.input].inflow
        eff_out = component.flow_efficiencies[component.output].outflow
        eff_average = math.sqrt(eff_in * eff_out)
        flow_params.update(
            {
                'energy_eff': eff_average,
                # 'storage_cap_equals': component.capacity,
                'storage_cap_min': component.capacity,
                'storage_cap_max': component.capacity,
                'energy_cap_min': 0,
                'energy_cap_max': float('inf'),
            }
        )

        if eff_out != eff_in:
            msg = (
                f"Storage '{component.uid.name}' has differing inflow "
                f"({eff_in}) and outflow ({eff_out}) efficiencies. "
                f"Calliope does only use one value for both directions and is using the average of "
                f"({eff_average}). Thus the SOC and standing loss will differ as well."
            )
            logger.warning(msg)

        if component.initial_soc:
            if component.capacity == 0:
                if component.initial_soc != 0 or component.idle_changes.negative != 0:
                    flow_params.update({
                        'storage_initial': 0,
                        'storage_loss': 0,
                    })
                    msg = (
                        f"Storage '{component.uid.name}' has zero capacity. "
                        f"Calliope considers initial soc and storage loss as "
                        f"fraction of capacity, so the initial soc and storage loss is set to Zero."
                    )
                    logger.warning(msg)
            else:
                flow_params.update(
                    {
                        'storage_initial': component.initial_soc / component.capacity,
                        'storage_loss': component.idle_changes.negative / component.capacity,
                    }
                )
            if component.capacity == float('inf'):
                msg = (
                    f"Storage '{component.uid.name}' infinite capacity may cause ignoring data. "
                    f"Calliope considers initial soc and storage loss as fraction of "
                    f"capacity leading to these becoming zero."
                )
                logger.warning(msg)
        elif component.initial_soc == 0:
            flow_params.update(
                {
                    'storage_initial': 0,
                }
            )
            if component.capacity == 0:
                flow_params.update(
                    {
                        'storage_loss': 0,
                    }
                )
                if component.idle_changes.negative != 0:
                    msg = (
                        f"Storage '{component.uid.name}' has zero capacity. "
                        f"Calliope considers storage loss as "
                        f"fraction of capacity, so the storage loss is set to Zero."
                    )
                    logger.warning(msg)
            else:
                flow_params.update(
                    {
                        'storage_loss': component.idle_changes.negative / component.capacity,
                    }
                )
        else:
            if component.capacity == 0:
                flow_params.update(
                    {
                        'storage_initial': 0,
                        'storage_loss': 0,
                    }
                )
                msg = (
                    f"Storage '{component.uid.name}' has zero capacity. "
                    f"Calliope considers initial soc and storage loss as "
                    f"fraction of capacity, so the inital soc is set to Zero."
                )
                logger.warning(msg)
            else:
                flow_params.update(
                    {
                        'storage_initial': 0,
                        'storage_loss': component.idle_changes.negative / component.capacity,
                    }
                )
                msg = (
                    f"Storage '{component.uid.name}' has no initial soc. "
                    f"Calliope needs initial soc and cant handle it as a "
                    f"optimization variable thus it is set to be zero."
                )
                logger.warning(msg)

        if component.capacity != 0:
            flow_params.update(
                {
                    'energy_cap_per_storage_cap_min':  0,
                    'energy_cap_per_storage_cap_max':  1 * (
                        component.flow_rates[f'{target}'].max / component.capacity),
                }
            )

        if component.flow_rates[f'{target}'].max > component.capacity:
            flow_params.update(
                {
                    'energy_cap_per_storage_cap_min': 0,
                    'energy_cap_per_storage_cap_max': 1,
                }
            )

        if component.expandable['capacity']:
            flow_params['energy_cap_max'] = float('inf')
            flow_params['energy_cap_min'] = 0
            flow_params.update(
                {
                    # lifetime is not a thing in Tessif, but needed for exp costs
                    'lifetime': timesteps/8760,
                    #                              in calliope, so it is assumed to be timeframe lenght
                }
            )
            if component.capacity == 0:
                flow_params.update(
                    {
                        'energy_cap_per_storage_cap_min': 0,
                        'energy_cap_per_storage_cap_max': 1,

                    }
                )
                if component.flow_rates[f'{target}'].min != 0:
                    msg = (
                        f"Calliope considers flows rate relative to capacity for expansion problems. "
                        f"Since Tessif takes absolute values, they need to divided by capacity."
                        f"Capacity of Zero would create division by zero, "
                        f"so the flow rate minimum will be ignored."
                    )
                    logger.warning(msg)
            elif component.capacity == float('inf'):
                flow_params.update(
                    {
                        'energy_cap_per_storage_cap_min': 0,
                        'energy_cap_per_storage_cap_max': 1,
                    }
                )
                msg = (
                    f"Calliope considers flows rate relative to capacity for expansion problems. "
                    f"Since Tessif takes absolute values, they need to divided by capacity."
                    f"Capacity of infinity would create relative of zero, "
                    f"so the given flow rates will be ignored and set to "
                    f"relative values min=0 and max=1."
                )
                logger.warning(msg)
            else:
                flow_params.update(
                    {
                        'energy_cap_per_storage_cap_min': 0,
                        'energy_cap_per_storage_cap_max': 1 * (
                            component.flow_rates[f'{target}'].max / component.capacity),
                    }
                )

            if component.expansion_limits['capacity'].min != component.capacity:
                msg = (
                    f"{component.uid.name}: Calliope does not have installed capacities. "
                    f"The calliope min expansion is used to portray the installed capacity "
                    f"'{component.capacity}', this results in the tessif min expansion "
                    f"'{component.expansion_limits['capacity'].min}' to not be able to be covered by calliope."
                )
                logger.warning(msg)

            if component.expansion_limits['capacity'].max >= component.capacity:
                flow_params.update(
                    {
                        'storage_cap_max': component.expansion_limits['capacity'].max,
                    }
                )
            else:
                msg = (
                    "Requested maximum expansion limit of "
                    f"'{component.expansion_limits['capacity'].max}' of "
                    f"'{'capacity'}' of component '{component.uid.name}' is below "
                    "current installed capacity of "
                    f"'{component.capacity}'. Falling back on current "
                    "installed capacity as maximum."
                )
                logger.warning(msg)
                flow_params.update(
                    {
                        'storage_cap_max': component.capacity,
                    }
                )

        if flow_params['energy_cap_per_storage_cap_max'] > 1:
            flow_params['energy_cap_per_storage_cap_max'] = 1

    # none of the tessif milp parameters exists in calliope
    if hasattr(component, 'milp'):
        i = False
        for k, v in component.milp():
            if bool(component.milp[k]) is True:
                i = True

        if not i:
            msg = (
                "Tessif's milp parameters don't exist in calliope "
                "and thus are getting ignored."
            )
            logger.warning(msg)

    return flow_params


def parse_cost_parameters(component, flow):
    """
    Utility to parse flow related parameters from :mod:`Tessif components
    <tessif.model.components>` to `Calliope components
    <https://calliope.readthedocs.io/en/stable/user/config_defaults.html>`_

    Parameters
    ----------
    component:
        Tessif component of which it's cost/emission related parameters are
        parsed into calliope recognizable parameters

    flow: str
        String representing the flow related interface from the components
        point of view.

    Return
    ------
    costs: dict
        Dictionary representing the costs ready to be used as key word
        arguments for creating calliope components. Calliope considers emissions
        as another cost parameter. The objective minimises only the monetary
        costs by default and not emission costs. In special cases the
        dict will be adjusted in another function.

    Warning
    -------
    Calliope doesn't support gradient costs and they will be ignored.

    Storage expansion costs will only be defined by capacity expansion costs

    Calliope only considers fixed ratios of energy flow to storage capacity.
    """

    costs = dict(
        monetary=dict(),
        emissions=dict(),
    )

    if hasattr(component, 'gradient_costs'):
        if component.gradient_costs[f'{flow}'].negative or component.gradient_costs[f'{flow}'].positive != 0:
            msg = (
                f"'{component.uid.name}' has gradient_costs. "
                f"Calliope doesn't support these and they will be ignored "
            )
            logger.warning(msg)

    # calliope demand only has Carrier consumption cost -> om_con
    if 'sink' in str(type(component)).lower():
        costs.update(
            {
                'monetary':
                    {
                        'om_con': component.flow_costs[f'{flow}'],
                    },
                'emissions':
                    {
                        'om_con': component.flow_emissions[f'{flow}'],
                    },
            }
        )

    # calliope supply has many different types of costs. In combination with tessif the following are needed:
    #   carrier production cost -> om_prod
    #   energy capacity cost    -> energy_cap
    #   interest rate           -> interest_rate  (needed for expansions) = 0
    if 'source' in str(type(component)).lower():
        costs.update(
            {
                'monetary':
                    {
                        'om_prod': component.flow_costs[f'{flow}'],
                    },
                'emissions':
                    {
                        'om_prod': component.flow_emissions[f'{flow}'],
                    },
            }
        )
        if component.expandable[f'{flow}']:
            costs['monetary'].update(
                {
                    'interest_rate': 0,
                    # no equivalent in tessif but needed to be set in calliope (same for lifetime) for expansions
                    'energy_cap': component.expansion_costs[f'{flow}'],
                }
            )

    # calliope conversion has many different types of costs. In combination with tessif the following are needed:
    #   carrier consumption cost -> om_con
    #   carrier production cost -> om_prod
    #   energy capacity cost    -> energy_cap
    #   interest rate           -> interest_rate  (needed for expansions)
    if 'transformer' in str(type(component)).lower():
        costs.update(
            {
                'monetary':
                    {
                        'om_con': component.flow_costs[f'{list(component.inputs)[0]}'],
                        'om_prod': component.flow_costs[f'{flow}'],
                    },
                'emissions':
                    {
                        'om_con': component.flow_emissions[f'{list(component.inputs)[0]}'],
                        'om_prod': component.flow_emissions[f'{flow}'],
                    },
            }
        )

    if 'storage' in str(type(component)).lower():
        costs.update(
            {
                'monetary':
                    {
                        'om_prod': component.flow_costs[f'{flow}'],
                    },
                'emissions':
                    {
                        'om_prod': component.flow_emissions[f'{flow}'],
                    },
            }
        )
        if component.expandable['capacity']:
            costs['monetary'].update(
                {
                    'interest_rate': 0,
                    # no equivalent in tessif but needed to be set in calliope (same for lifetime) for expansions
                    'storage_cap': component.expansion_costs['capacity'],
                }
            )
            if component.expansion_costs[flow] != 0:
                msg = (
                    f"'{component.uid.name}' has expansion costs for {flow}. "
                    f"These are not considered hence the energy flow is directly linked"
                    f" to the storage capacity by a factor and not separated. "
                )
                logger.warning(msg)
            if component.fixed_expansion_ratios[flow] is False:
                msg = (
                    f" {component}: Calliope only considers fixed ratios "
                    f"of energy flow to storage capacity."
                )
                logger.warning(msg)

    return costs


def generate_calliope_bus_like_loc(busses):
    """
    Generates calliope locations, transmissions and links out of tessif busses.

    For tessif post processing it is needed to read the results from the busses.
    To connect components over these busses different locations for each component
    as well as for busses are being used. Bus locations don't contain any component,
    but transmissions to connect to components. Besides the location itself the
    transmission (no losses) and the links (information which locations to
    connect with the give transmission) are defined as well.

    Parameters
    ----------
    busses: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Bus` objects that are to
        be transformed into calliope locations, links and transmissions.

    Return
    ------
    loc :class:`~dict`
        Dictionary object yielding the bus location.

    links :class:`~dict`
        Dictionary object yielding the bus connected location. Links contain information about
        what regions are connected with which kind of transmission.

    transmission :class:`~dict`
        Dictionary object yielding the loss free transmissions
        between bus and component.

    Warning
    -------
    Dots are no valid symbols in component names, cause they
    are used to separate component from carrier in bus input/output data.
    """

    for bus in busses:
        loc = dict({
            f'{bus.uid.name}': {
                'coordinates': {'lat': float(bus.uid.latitude), 'lon': float(bus.uid.longitude)},
            }})

        # links connecting the components/locations with transmissions
        links, transmissions = dict(), dict()
        invalid_name = ['supply', 'conversion', 'conversion_plus',
                        'demand', 'transmission', 'storage', 'supply_plus']  # these bus names might cause problems
        for connection in bus.inputs:
            # should be "component.carrier" and not more dots
            if connection.count(".") > 1:
                msg = (
                    f"Connection to '{connection}' of Bus '{bus.uid.name}' "
                    f"contains multiple dots. The dots are used in calliope transformation "
                    f"to separate carrier from component. "
                    f"Avoid using dots in component names or carriers."
                )
                logger.warning(msg)
            component = connection.split(".", 1)[0]
            invalid_name = ['supply', 'conversion', 'conversion_plus',
                            'demand', 'transmission', 'storage', 'supply_plus']
            if component.lower() in invalid_name:
                link = dict({
                    f"{connection.split('.', 1)[1]}_{component} location,{bus.uid.name}": {
                        'techs': {f'{connection.split(".", 1)[1]} transmission': {'constraints': {'one_way': True}}}},
                })
                links.update(link)

            else:
                link = dict({
                    f'{component} location,{bus.uid.name}': {
                        'techs': {f'{connection.split(".", 1)[1]} transmission': {'constraints': {'one_way': True}}}},
                })
                links.update(link)

            transmission = dict({
                f'{connection.split(".", 1)[1]} transmission': {
                    'essentials': {
                        'name': f'{connection.split(".", 1)[1]} transmission',
                        'color': '#8465A9',
                        'parent': 'transmission',
                        'carrier': f'{connection.split(".", 1)[1]}'},
                    'constraints': {'energy_eff': 1, 'one_way': True},
                },
            })
            transmissions.update(transmission)

        for connection in bus.outputs:
            if connection.count(".") > 1:
                msg = (
                    f"Connection to '{connection}' of Bus '{bus.uid.name}' "
                    f"contains multiple dots. The dots are used in calliope transformation "
                    f"to separate carrier from component. "
                    f"Avoid using dots in component names or carriers."
                )
                logger.warning(msg)

            if connection in bus.inputs:
                # make storage links bidirectional
                component = connection.split(".", 1)[0]
                if component.lower() in invalid_name:
                    link = dict({
                        f"{connection.split('.', 1)[1]}_{component} location,{bus.uid.name}": {
                            'techs': {f'{connection.split(".", 1)[1]} transmission': {
                                'constraints': {'one_way': False}}}},
                    })
                    links.update(link)
                else:
                    links.update({f'{component} location,{bus.uid.name}': {
                        'techs': {f'{connection.split(".", 1)[1]} transmission': {'constraints': {'one_way': False}}}}})

            else:
                component = connection.split(".", 1)[0]
                if component.lower() in invalid_name:
                    link = dict({
                        f"{bus.uid.name},{connection.split('.', 1)[1]}_{component} location": {
                            'techs': {f'{connection.split(".", 1)[1]} transmission': {
                                'constraints': {'one_way': True}}}},
                    })
                    links.update(link)
                else:
                    link = dict({
                        f"{bus.uid.name},{component} location": {
                            'techs': {f'{connection.split(".", 1)[1]} transmission': {
                                'constraints': {'one_way': True}}}},
                    })
                    links.update(link)

                transmission = dict({
                    f'{connection.split(".", 1)[1]} transmission': {
                        'essentials': {
                            'name': f'{connection.split(".", 1)[1]} transmission',
                            'color': '#8465A9',
                            'parent': 'transmission',
                            'carrier': f'{connection.split(".", 1)[1]}'},
                        'constraints': {'energy_eff': 1, 'one_way': True},
                    },
                })
                transmissions.update(transmission)

        yield loc, links, transmissions


def generate_calliope_supply(sources, timeframe, es_name):
    """
    Create calliope supply out of tessif sources.

    Parameters
    ----------
    sources: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Source` objects that are to
        be transformed into calliope supply.

    timeframe:
        The timeframe to be analysed with the model.

    es_name:
        Model name which is used to save the timeseries CSV files in correct folder.

    Return
    ------
    supply :class:`~dict`
        Dictionary yielding the components data.

    loc :class:`~dict`
        Dictionary object yielding the components location.

    Warning
    -------
    Calliope can only handle sources of one output.

    Calliope handles timeseries relative to flow rates max. If flow rate max is zero
    or infinity, the timeseries max is used as maximum.
    """

    for source in sources:
        if len(source.outputs) > 1:
            msg = (
                f"Supply '{source.uid.name}' has multple outputs: {list(source.outputs)}. "
                f"This can't be handled by Calliope "
                f"the way Tessif handleds them. "
            )
            logger.warning(msg)

        if source.uid.name.lower() == 'supply':
            # conflict with calliope parent tech. Name change only affects
            # yaml and native calliope post processing. Tessif will sort out the previous name.
            source_name = f'{list(source.outputs)[0]}_{source.uid.name}'
        else:
            source_name = source.uid.name

        outputs, costs, grp_constraint = dict(), dict(), dict()

        for output_ in source.outputs:
            outputs['constraints'] = dict(  # setting the defaults (might be adjusted in parse_flow_parameters)
                {
                    'energy_prod': True,
                    'resource': 'inf',
                    'resource_unit': 'energy',
                }
            )
            outputs['constraints'].update(
                parse_flow_parameters(source, output_, len(timeframe)))
            costs['costs'] = parse_cost_parameters(source, output_)

            if source.timeseries:
                timeseries_max = np.array(
                    source.timeseries[output_].max).astype(float)
                timeseries_min = np.array(
                    source.timeseries[output_].min).astype(float)
                timeseries = timeseries_max

                if (timeseries_max == timeseries_min).all():
                    outputs['constraints'].update({'force_resource': True})

                if source.flow_rates[f'{output_}'].max == float('inf'):
                    flow_max = max(timeseries)
                    outputs['constraints']['energy_cap_min'] = float(flow_max)
                    outputs['constraints']['energy_cap_max'] = float(flow_max)
                elif source.flow_rates[f'{output_}'].max == 0:
                    msg = (
                        f"Source '{source.uid.name}' has flow_rates.max of 0 "
                        f"and a timeseries given. Calliope handles timeseries relative "
                        f"to flow_rates.max. Falling back to timeseries max instead of flow_rates max"
                    )
                    logger.warning(msg)
                    # assign this new so there doesnt need to be big adjustments for this case
                    flow_max = max(timeseries)
                elif outputs['constraints']['energy_cap_min'] == float('inf'):
                    flow_max = max(timeseries)
                else:
                    flow_max = source.flow_rates[f'{output_}'].max

                if float(outputs['constraints']['energy_cap_min']) <= float(max(timeseries)):
                    outputs['constraints']['energy_cap_min'] = float(
                        max(timeseries))
                    if not source.expandable[output_]:
                        outputs['constraints']['energy_cap_max'] = float(
                            max(timeseries))
                    flow_max = max(timeseries)

                for i in range(len(timeseries)):
                    timeseries[i] = timeseries[i] / flow_max
                timeseries = pd.DataFrame({'': timeframe, f'{source_name}': timeseries})

                timeseries.to_csv(
                    os.path.join(
                        write_dir, 'Calliope', f'{es_name}', 'timeseries_data', f'{source_name}.csv'), index=False)

                outputs['constraints'].update({'resource': f'file={source_name}.csv:{source_name}'})

                outputs['constraints'].update({'resource_unit': f'energy_per_cap'})
                outputs['constraints'].pop('energy_cap_min_use')

                if outputs['constraints']['energy_cap_min'] == float('inf'):
                    outputs['constraints']['energy_cap_min'] = float(flow_max)

            if float(source.accumulated_amounts[output_].max) != float('inf'):
                grp_constraint.update({
                    f'{source_name}_accumulated_amounts_max': dict(
                        techs=[source_name],
                        carrier_prod_max={f'{output_}': float(source.accumulated_amounts[output_].max)})
                })
            if float(source.accumulated_amounts[output_].min) != float(0):
                grp_constraint.update({
                    f'{source_name}_accumulated_amounts_min': dict(
                        techs=[source_name],
                        carrier_prod_min={f'{output_}': float(source.accumulated_amounts[output_].min)})
                })

        if outputs['constraints']['energy_cap_min'] == float('inf'):
            outputs['constraints']['energy_cap_min'] = float(0)

        supply = dict()
        # giving the uid information that cant get recreated on any other way
        uid = f'{source.uid.name}.{source.uid.region}.{source.uid.sector}.{source.uid.carrier}.{source.uid.node_type}'

        supply[f'{source_name}'] = dict(
            essentials=dict(
                name=uid,
                # only needed for visualisation in native calliope tools
                color=str('#FF7700'),
                parent='supply',
                carrier_out=list(source.outputs)[0],
            ),
        )

        supply[f'{source_name}'].update(outputs)
        supply[f'{source_name}'].update(costs)

        # creating the location in which the storage is called
        loc = dict({
            f'{source_name} location': {
                'coordinates': {'lat': float(source.uid.latitude), 'lon': float(source.uid.longitude)},
                'techs': {f'{source_name}': None},
            }})

        yield supply, loc, grp_constraint


def generate_calliope_demand(sinks, timeframe, es_name):
    """
    Create calliope demand out of tessif sinks.

    Parameters
    ----------
    sinks: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Sinks` objects that are to
        be transformed into calliope demand.

    timeframe:
        The timeframe to be analysed with the model.

    es_name:
        Model name which is used to save the timeseries CSV files in correct folder.

    Return
    ------
    demand :class:`~dict`
        Dictionary yielding the components data.

    loc :class:`~dict`
        Dictionary object yielding the components location.

    Warning
    -------
    Calliope can only handle sinks of single inputs.

    Calliope can only consider one given timeseries for demands.
    If different max and min timeseries are given, the minimum timeseries will be used.

    """

    for sink in sinks:
        if len(sink.inputs) > 1:
            msg = (
                f"Sink '{sink.uid.name}' has multple inputs: {list(sink.inputs)}. "
                f"This can't be handled by Calliope "
                f"the way Tessif handleds them. "
            )
            logger.warning(msg)

        if sink.uid.name.lower() == 'demand':
            # conflict with calliope parent tech. Name change only affects
            # yaml and native calliope post processing. Tessif will sort out the previous name.
            sink_name = f'{list(sink.inputs)[0]}_{sink.uid.name}'
        else:
            sink_name = sink.uid.name

        inputs = dict()
        costs = dict()
        grp_constraint = dict()

        for input_ in sink.inputs:
            inputs['constraints'] = dict(  # setting the defaults (might be adjusted in parse_flow_parameters)
                {
                    'energy_con': True,
                    # 'force_resource': True,
                    'resource_unit': 'energy',
                }
            )
            # inputs['constraints'].update(parse_flow_parameters(sink, input_, timeframe))
            # demands have way less allowed_constraints making parse_flow_parameters an overkill
            costs['costs'] = parse_cost_parameters(sink, input_)

            if sink.timeseries:
                timeseries_max = - \
                    np.array(sink.timeseries[input_].max).astype(float)
                timeseries_min = - \
                    np.array(sink.timeseries[input_].min).astype(float)

                if not (timeseries_max == timeseries_min).all():
                    msg = (
                        f"Sink '{sink.uid.name}' has different min and max timeseries. "
                        f"Calliope can only consider one and will work with the "
                        f"min timeseries. "
                    )
                    logger.warning(msg)
                    timeseries = timeseries_min
                else:
                    inputs['constraints'].update({'force_resource': True})
                    timeseries = timeseries_max
            else:
                if sink.flow_rates[input_].max != float('inf'):
                    timeseries = - \
                        np.array(len(timeframe) *
                                 [sink.flow_rates[input_].max]).astype(float)
                    inputs['constraints'].update({'resource': f'df={sink_name}'})
                    inputs['constraints'].update({'force_resource': True})
                else:
                    timeseries = - \
                        np.array(len(timeframe) *
                                 [sink.flow_rates[input_].max]).astype(float)
                    inputs['constraints'].update({'resource': f'df={sink_name}'})
                    inputs['constraints'].update({'force_resource': False})

            if isinstance(timeseries, np.ndarray):
                timeseries = pd.DataFrame({'': timeframe, f'{sink_name}': timeseries})

                # timeseries is either saved as csv if model is created calliope like with yaml files
                # or is put as dict in model with linking key in technology
                timeseries.to_csv(
                    os.path.join(
                        write_dir, 'Calliope', f'{es_name}', 'timeseries_data', f'{sink_name}.csv'), index=False)
                inputs['constraints'].update({'resource': f'file={sink_name}.csv:{sink_name}'})

            if float(sink.accumulated_amounts[input_].max) != float('inf'):
                grp_constraint.update({
                    f'{sink_name}_accumulated_amounts_max': dict(
                        techs=[sink_name],
                        carrier_con_max={f'{input_}': float(sink.accumulated_amounts[input_].max)})
                })
            if float(sink.accumulated_amounts[input_].min) != float(0):
                grp_constraint.update({
                    f'{sink_name}_accumulated_amounts_min': dict(
                        techs=[sink_name],
                        carrier_con_min={f'{input_}': float(sink.accumulated_amounts[input_].min)})
                })

        demand = dict()
        # giving the uid information that cant get recreated on any other way
        uid = f'{sink.uid.name}.{sink.uid.region}.{sink.uid.sector}.{sink.uid.carrier}.{sink.uid.node_type}'

        demand[f'{sink_name}'] = dict(
            essentials=dict(
                name=uid,
                # only needed for visualisation in native calliope tools
                color=str('#cc0033'),
                parent='demand',
                carrier=list(sink.inputs)[0],
            ),
        )

        demand[f'{sink_name}'].update(inputs)
        demand[f'{sink_name}'].update(costs)

        # creating the location in which the storage is called
        loc = dict({
            f'{sink_name} location': {
                'coordinates': {'lat': float(sink.uid.latitude), 'lon': float(sink.uid.longitude)},
                'techs': {f'{sink_name}': None},
            }})

        yield demand, loc, grp_constraint


def generate_calliope_conversion(transformers, timeframe, es_name):
    """
    Create calliope conversion out of tessif transformers.

    Parameters
    ----------
    transformers: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Transformers` objects that are to
        be transformed into calliope conversion.

    timeframe:
        The timeframe to be analysed with the model.

    es_name:
        Model name which is used to save the timeseries CSV files in correct folder.

    Return
    ------
    conversion :class:`~dict`
        Dictionary yielding the components data.

    loc :class:`~dict`
        Dictionary object yielding the components location.

    Warning
    -------
    Calliope does only support timeseries for sinks and sources. Others will be ignored.
    """

    # setting this up here in case no transformer is used, there is still something needed to be yield

    conversion, loc = dict(), dict()

    for transformer in transformers:
        if transformer.uid.name.lower() == 'conversion':
            # conflict with calliope parent tech. Name change only affects
            # yaml and native calliope post processing. Tessif will sort out the previous name.
            transformer_name = f'{transformer.uid.carrier}_{transformer.uid.name}'
        else:
            transformer_name = transformer.uid.name

        if transformer.timeseries:
            msg = (
                f"Transformer '{transformer.uid.name}' has a timeseries given. "
                f"Calliope can only consider timeseries for sources and sinks. "
            )
            logger.warning(msg)

        # giving the uid information that cant get recreated on any other way
        uid = transformer.uid
        uid = f'{uid.name}.{uid.region}.{uid.sector}.{uid.carrier}.{uid.node_type}'

        conversion[f'{transformer_name}'] = dict(
            essentials=dict(
                name=uid,
                # only needed for visualisation in native calliope tools
                color=str('#99ccff'),
                parent='conversion',  # overwritten to conversion_plus if multi input/output
                carrier_in=list(transformer.inputs)[0],
                carrier_out=list(transformer.outputs)[0],
            ),
        )

        flows = dict({'constraints': {
            'energy_con': True,
            'energy_prod': True,
        }})
        costs = dict(costs=dict())

        # transformer to conversion
        if len(transformer.outputs) == 1 and len(transformer.inputs) == 1:
            input_ = list(transformer.inputs)[0]
            output_ = list(transformer.outputs)[0]
            flows['constraints'].update(parse_flow_parameters(
                transformer, output_, len(timeframe)))
            costs['costs'] = parse_cost_parameters(transformer, output_)

            eff = transformer.conversions[(f'{input_}', f'{output_}')]
            if type(eff) != float and type(eff) != int:
                eff = np.array(eff).astype(float)
                timeseries = pd.DataFrame({'': timeframe, f'{transformer_name}': eff})
                timeseries.to_csv(
                    os.path.join(
                        write_dir, 'Calliope', f'{es_name}', 'timeseries_data', f'{transformer_name}_eff.csv'),
                    index=False)
                eff = f'file={transformer_name}_eff.csv:{transformer_name}'

            flows['constraints'].update({
                'energy_cap_min': float(transformer.flow_rates[output_].max),
                'energy_eff': eff,
            })

            if transformer.expandable[f'{output_}']:
                if transformer.expandable[f'{input_}']:
                    exp_cost = transformer.expansion_costs[f'{output_}'] + transformer.expandable[f'{input_}'] / eff
                    limit_in = transformer.expansion_limits[f'{input_}'].max * eff
                    limit_out = transformer.expansion_limits[f'{output_}'].max
                    energy_cap_max = min(limit_in, limit_out)
                    flows['constraints'].update({
                        'energy_cap_max': energy_cap_max,
                    })
                else:
                    exp_cost = transformer.expansion_costs[f'{output_}']
                costs['costs']['monetary'].update(
                    {
                        'interest_rate': 0,
                        'energy_cap': exp_cost,
                    }
                )
            if transformer.expandable[f'{input_}'] and not transformer.expandable[f'{output_}']:
                exp_cost = transformer.expandable[f'{input_}'] / eff
                energy_cap_max = transformer.expansion_limits[f'{input_}'].max * eff
                flows['constraints'].update({
                    'energy_cap_max': energy_cap_max,
                })
                costs['costs']['monetary'].update(
                    {
                        'interest_rate': 0,
                        'energy_cap': exp_cost,
                    }
                )

        conversion[f'{transformer_name}'].update(flows)
        conversion[f'{transformer_name}'].update(costs)

        # transformer to conversion_plus
        if len(transformer.outputs) > 1 or len(transformer.inputs) > 1:
            conv_plus = generate_calliope_conversion_plus(
                transformer, len(timeframe))
            conversion[f'{transformer_name}']['essentials'].update(conv_plus['essentials'])
            conversion[f'{transformer_name}']['constraints'].update(conv_plus['constraints'])
            conversion[f'{transformer_name}']['costs'].update(conv_plus['costs'])

        if 'energy_cap_min' in flows['constraints'].keys():
            if flows['constraints']['energy_cap_min'] == float('inf'):
                flows['constraints'].update({'energy_cap_min': 0})

        # creating the location in which the storage is called
        loc.update(dict({
            f'{transformer_name} location': {
                'coordinates': {'lat': float(transformer.uid.latitude), 'lon': float(transformer.uid.longitude)},
                'techs': {f'{transformer_name}': None},
            }}))

    yield conversion, loc


def generate_calliope_conversion_plus(transformer, timesteps):
    """
    Create calliope conversion_plus specific data out of tessif transformers with
    multiple in or outputs. Calliope can consider any number of in and outputs, but
    only 3 that are forced to act at same time. In tessif definition e.g. CHP's are
    always forced to produce heat as well when electricity is produced.

    Parameters
    ----------
    transformer:
        A single tranformer of :class:`tessif.model.components.Transformers` objects that are to
        be transformed into calliope conversion_plus, due to having multi inputs or multi outputs,
        which cant be handled by the conversion technology.

    timesteps:
        The number of timesteps to be analysed with the model.

    Return
    ------
    conv_plus :class:`~dict`
        Dictionary returning the conversion_plus specific data
        ready to be used in generate_calliope_conversion.

    Raises
    ------
    NotImplementedError
        Raised if more than 1 input or more than 3 outputs is used, because calliope
        can't handle these cases in combination with tessif parameter definitions.

    Warning
    -------
    Calliope does not have installed capacities. The calliope min expansion is used
    to portray the installed capacity, this results in the tessif min expansion
    to not be able to be covered by calliope.

    Calliope only considers one representative capacity value on multiple output transformers.
    The capacity of the other outputs are set relative to the primary carrier and so are their expansion limits.

    Calliope doesnt support tessif's milp parameters. Thus they will be ignored.
    """

    conv_plus = dict(essentials=dict(),
                     constraints=dict(),
                     costs=dict())

    conv_plus['essentials'].update({'parent': 'conversion_plus'})

    # calliope (within the used carrier definition) can only consider 3 outputs.
    # The not used definition would allow more outputs, but does not have set relations between each carrier.
    if len(transformer.outputs) > 3:
        msg = (
            "\n Transformers with more than 3 outputs are not \n"
            " implemented for Calliope."
        )
        raise NotImplementedError(msg)

    # Multiple inputs are not considered. This works in calliope,but would result in
    # huge difficulties considering the tessif parameter definitions in the es2es as well as es2mapping since
    # the capacity, costs and emissions in calliope can only refer to one in-/output. So these multiple tessif
    # values need to be calculated to one corresponding value for calliope.
    if len(transformer.inputs) > 1:
        msg = (
            "\n Transformers with more than 1 input are not \n"
            " implemented for Calliope."
        )
        raise NotImplementedError(msg)

    if 1 < len(transformer.outputs) < 3:
        outputs = list(transformer.outputs)
        # sort alphabetically to avoid randomized primary carrier
        outputs.sort()
        for counter, output_ in enumerate(outputs):
            conv_plus['essentials'].update({
                f'carrier_out_{counter+1}': output_

            })
            # need to assign a carrier to be the primary one. First carrier is chosen
            if counter == 0:
                conv_plus['essentials'].update(
                    {'primary_carrier_out': output_})

        conv_plus['essentials']['carrier_out'] = conv_plus['essentials'].pop(
            'carrier_out_1')

        conv_plus['essentials'].update({
            'carrier_in': list(transformer.inputs)[0]
        })

        if len(transformer.outputs) == 2:
            inp = list(transformer.inputs)[0]
            out1 = outputs[0]
            out2 = outputs[1]
            conv1 = transformer.conversions[(f'{inp}', f'{out1}')]
            conv2 = transformer.conversions[(f'{inp}', f'{out2}')]
            carrier_ratio = conv2 / conv1

            initial0 = transformer.flow_rates[inp].max * conv1
            initial1 = transformer.flow_rates[out1].max
            initial2 = transformer.flow_rates[out2].max / carrier_ratio
            # specify which limit does limit the most after converting them to regard primary output
            cap_ini = min(initial0, initial1, initial2)

            conv_plus['constraints'].update({
                f'carrier_ratios.carrier_out_2.{out2}': carrier_ratio,
                'energy_eff': conv1,
                'energy_cap_max': cap_ini,
                'energy_cap_min': cap_ini,
                'energy_ramping': True,
            })
            # e.g. both conversions are equal: carrier_ratios is 1 meaning both carriers are produced in same amount
            # e.g. 2nd conversions is half 1st: carrier_ratios is 0.5 meaning half carrier2 is produced compared to 1
            # energy eff defines how much of input carrier is gonna be used in primary output
            if conv_plus['constraints']['energy_cap_min'] == float('inf'):
                conv_plus['constraints']['energy_cap_min'] = 0

            # move costs and emissions to a single value recognised at input
            conv_plus['costs'].update({
                'monetary': {
                    'om_con': transformer.flow_costs[inp],
                    'om_prod':
                        transformer.flow_costs[out1] +
                        transformer.flow_costs[out2] * carrier_ratio
                },
                'emissions': {
                    'om_con': transformer.flow_emissions[inp],
                    'om_prod':
                        transformer.flow_emissions[out1] +
                        transformer.flow_emissions[out2] * carrier_ratio
                },
            })

            # calliope can only consider one capacity maximum.
            exp = False
            for k, v in transformer.expandable.items():
                if bool(transformer.expandable[k]) is True:
                    exp = True

            if exp:

                cap0 = transformer.expansion_limits[inp].max * conv1
                cap1 = transformer.expansion_limits[out1].max
                cap2 = transformer.expansion_limits[out2].max / carrier_ratio
                # specify which expansion limit does limit the most after converting them to regard primary output
                cap_max = min(cap0, cap1, cap2)
                cost0 = transformer.expansion_costs[inp]
                cost1 = transformer.expansion_costs[out1]
                cost2 = transformer.expansion_costs[out2]

                cap_cost = cost1 + (cost2 * carrier_ratio) + (cost0 / conv1)

                if transformer.expansion_limits[out1].min != transformer.flow_rates[out1].max:
                    msg = (
                        f"{transformer.uid.name}: Calliope does not have installed capacities. "
                        f"The calliope min expansion is used to portray the installed capacity "
                        f"'{transformer.flow_rates[out1].max}', this results in the tessif min expansion "
                        f"'{transformer.expansion_limits[out1].min}' to not be able to be covered by calliope."
                    )
                    logger.warning(msg)

                conv_plus['costs']['monetary'].update({
                    'interest_rate': 0,
                    # no equivalent in tessif but needed to be set in calliope (same for lifetime) for expansions
                    'energy_cap': cap_cost,
                },
                )

                conv_plus['constraints'].update({
                    'energy_cap_max': cap_max,
                    'energy_cap_min': cap_ini,
                    'lifetime': timesteps / 8760,
                    # lifetime is not a thing in Tessif, but needed for exp costs
                    # in calliope, so it is assumed to be timeframe lenght
                })

        if len(transformer.outputs) == 3:
            inp = list(transformer.inputs)[0]
            outputs = list(transformer.outputs)
            outputs.sort()
            out1 = outputs[0]
            out2 = outputs[1]
            out3 = outputs[2]

            conv1 = transformer.conversions[(f'{inp}', f'{out1}')]
            conv2 = transformer.conversions[(f'{inp}', f'{out2}')]
            conv3 = transformer.conversions[(f'{inp}', f'{out3}')]
            carrier_ratio2 = conv2 / conv1
            carrier_ratio3 = conv3 / conv1

            initial0 = transformer.flow_rates[inp].max * conv1
            initial1 = transformer.flow_rates[out1].max
            initial2 = transformer.flow_rates[out2].max / carrier_ratio2
            initial3 = transformer.flow_rates[out3].max / carrier_ratio3
            # specify which limit does limit the most after converting them to regard primary output
            cap_ini = min(initial0, initial1, initial2, initial3)

            conv_plus['constraints'].update({
                f'carrier_ratios.carrier_out_2.{out2}': carrier_ratio2,
                f'carrier_ratios.carrier_out_3.{out3}': carrier_ratio3,
                'energy_cap_max': cap_ini,
                'energy_cap_min': cap_ini,
                'energy_eff': conv1,
                'energy_ramping': True,
            })
            # e.g. both conversions are equal: carrier_ratios is 1 meaning both carriers are produced in same amount
            # e.g. 3rd conversions is half 1st: carrier_ratios is 0.5 meaning half carrier3 is produced compared to 1
            # energy eff defines how much of input carrier is gonna be used in primary output
            if conv_plus['constraints']['energy_cap_min'] == float('inf'):
                conv_plus['constraints']['energy_cap_min'] = 0

            # move costs and emissions to a single value recognised at input
            conv_plus['costs'].update({
                'monetary': {
                    'om_con': transformer.flow_costs[inp],
                    'om_prod':
                        transformer.flow_costs[out1] +
                        transformer.flow_costs[out2] / carrier_ratio2 +
                        transformer.flow_costs[out3] / carrier_ratio3
                },
                'emissions': {
                    'om_con': transformer.flow_costs[inp],
                    'om_prod':
                        transformer.flow_emissions[out1] +
                        transformer.flow_emissions[out2] / carrier_ratio2 +
                        transformer.flow_emissions[out3] / carrier_ratio3
                },
            })

            # calliope can only consider one capacity maximum.
            exp = False
            for k, v in transformer.expandable.items():
                if bool(transformer.expandable[k]) is True:
                    exp = True

            if exp:

                cap0 = transformer.expansion_limits[inp].max * conv1
                cap1 = transformer.expansion_limits[out1].max
                cap2 = transformer.expansion_limits[out2].max / carrier_ratio2
                cap3 = transformer.expansion_limits[out3].max / carrier_ratio3
                # specify which expansion limit does limit the most after converting them to regard primary output
                cap_max = min(cap0, cap1, cap2, cap3)
                cost0 = transformer.expansion_costs[inp]
                cost1 = transformer.expansion_costs[out1]
                cost2 = transformer.expansion_costs[out2]
                cost3 = transformer.expansion_costs[out3]

                cap_cost = cost1 + (cost2 * carrier_ratio2) + \
                    (cost3 * carrier_ratio3) + (cost0 / conv1)

                if transformer.expansion_limits[out1].min != transformer.flow_rates[out1].max:
                    msg = (
                        f"{transformer.uid.name}: Calliope does not have installed capacities. "
                        f"The calliope min expansion is used to portray the installed capacity "
                        f"'{transformer.flow_rates[out1].max}', this results in the tessif min expansion "
                        f"'{transformer.expansion_limits[out1].min}' to not be able to be covered by calliope."
                    )
                    logger.warning(msg)

                conv_plus['costs']['monetary'].update({
                    'interest_rate': 0,
                    # no equivalent in tessif but needed to be set in calliope (same for lifetime) for expansions
                    'energy_cap': cap_cost,
                },
                )

                conv_plus['constraints'].update({
                    'energy_cap_max': cap_max,
                    'energy_cap_min': cap_ini,
                    'lifetime': timesteps / 8760,
                    # lifetime is not a thing in Tessif, but needed for exp costs
                    # in calliope, so it is assumed to be timeframe lenght
                })

    if hasattr(transformer, 'milp'):
        i = False
        for k, v in transformer.milp():
            if bool(transformer.milp[k]) is True:
                i = True

        if i:
            msg = (
                "Tessif's milp parameters don't exist in calliope "
                "and thus are getting ignored."
            )
            logger.warning(msg)

    return conv_plus


def generate_calliope_storage(storages, timeframe):
    """
    Create calliope storages out of tessif storages.

    Parameters
    ----------
    storages: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Storage` objects that are to
        be transformed into calliope storage.

    timeframe:
        The timeframe to be analysed with the model.

    Return
    ------
    storage :class:`~dict`
        Dictionary yielding the components data.

    loc :class:`~dict`
        Dictionary object yielding the components location.

    cyclic_store :class:`~bool`
        Boolean object yielding if the storage is cyclic or not.

    Warning
    -------
    Calliope does only support timeseries for sinks and sources. Others will be ignored.

    Final_soc can only be taken into account if it equals initial_soc and both are not None.
    Else it will be a result of the optimization.
    """

    # setting this up here in case no storage is used, there is still something needed to be yield
    store, loc = dict(), dict()
    cyclic_store = list()

    for storage in storages:
        if storage.uid.name.lower() == 'storage':
            # conflict with calliope parent tech. Name change only affects
            # yaml and native calliope post processing. Tessif will sort out the previous name.
            storage_name = f'{storage.uid.carrier}_{storage.uid.name}'
        else:
            storage_name = storage.uid.name

        if storage.timeseries:
            msg = (
                f"Storage '{storage.uid.name}' has a timeseries given. "
                f"Calliope can only consider"
                f" timeseries for sources and sinks. "
            )
            logger.warning(msg)

        flows = dict()
        costs = dict()
        input_ = storage.input
        flows['constraints'] = dict(  # setting the defaults (might be adjusted in parse_flow_parameters)
            {
                'energy_con': True,
                'energy_prod': True,
                'storage_cap_max': storage.capacity,
                # 'force_asynchronous_prod_con': True  # enable/disable charge and discharge in same timestep
                # Calling this (no matter if True or False) will result in a mixed integer problem
            }
        )
        flows['constraints'].update(
            parse_flow_parameters(storage, input_, len(timeframe)))
        costs['costs'] = parse_cost_parameters(storage, input_)

        # creating the location in which the storage is called
        loc.update(dict({
            f'{storage_name} location': {
                'coordinates': {'lat': float(storage.uid.latitude), 'lon': float(storage.uid.longitude)},
                'techs': {f'{storage_name}': None},
            }}))

        # calliope can only consider all storages cyclic or none, but cant differ individually
        # So every storage is checked whether it is cyclic or not and then checked if all are same
        # (if not none cyclic is forced for all storages)
        if storage.final_soc:
            if storage.initial_soc:
                if storage.initial_soc == storage.final_soc:
                    cyclic_store.append(True)
                else:
                    cyclic_store.append(False)
                    msg = (
                        f"Storage '{storage.uid.name}' has a final_soc '{storage.final_soc}'. "
                        f"Calliope doesnt support final_soc setting. "
                        f"Final_soc can only be taken into account if it equals initial_soc "
                        f"else it will be a result of the optimization."
                    )
                    logger.warning(msg)
            else:
                cyclic_store.append(False)
                msg = (
                    f"Storage '{storage.uid.name}' has a final_soc '{storage.final_soc}'. "
                    f"Calliope doesnt support final_soc setting. "
                    f"Final_soc can only be taken into account if it equals initial_soc "
                    f"and both are not None."
                    f"Else it will be a result of the optimization."
                )
                logger.warning(msg)
        else:
            cyclic_store.append(False)

        # giving the uid information that cant get recreated on any other way
        uid = storage.uid
        uid = f'{uid.name}.{uid.region}.{uid.sector}.{uid.carrier}.{uid.node_type}'

        store[f'{storage_name}'] = dict(
            essentials=dict(
                name=uid,
                # only needed for visualisation in native calliope tools
                color=str('#ffcc00'),
                parent='storage',
                carrier=storage.input,
            ),
        )

        store[f'{storage_name}'].update(flows)
        store[f'{storage_name}'].update(costs)

    yield store, loc, cyclic_store


def generate_calliope_connector(connectors, busses):
    """
    Create calliope location out of tessif connectors. A connector component
    does not exist in calliope. The tessif connector is to be transformed
    into a transmission-only-location linked to the bus locations connected
    to the connector with transmission with losses. The connector efficiency is
    splitted on both transmission lines going from bus1 over connector
    location to bus2. Also the transmission are forced to be one way only, so
    the transmission bus2 over connector location to bus1 can have a different
    efficiency So overall 4 transmission lines and one location are used to
    represent the tessif connector in calliope.

    Parameters
    ----------
    connectors: ~collections.abc.Sequence
        Sequence of :class:`tessif.model.components.Connector` objects that are to
        be transformed into calliope locations, links and transmission.

    busses: ~collections.abc.Iterable
        Iterable of :class:`tessif.model.components.Bus` objects that are to
        be used for correct transformation of connector.

    Return
    ------
    loc :class:`~dict`
        Dictionary object yielding the components location.

    links :class:`~dict`
        Dictionary object yielding the components links. Links contain information about
        what regions are connected with which kind of transmission.

    transmission :class:`~dict`
        Dictionary object yielding the components transmissions with connector losses.
    """

    loc, links, transmissions = dict(), dict(), dict()

    for connector in connectors:
        loc.update(dict({
            f'{connector.uid.name}': {
                'coordinates': {'lat': float(connector.uid.latitude), 'lon': float(connector.uid.longitude)},
            },
            f'{connector.uid.name} reverse': {
                'coordinates': {'lat': float(connector.uid.latitude), 'lon': float(connector.uid.longitude)},
            },
        }))

        # 1st connector location
        # links connecting the locations (connector, busses) with transmissions having losses
        connected_busses = []
        for connection in connector.interfaces:
            connected_busses.append(f'{connection}')
            for bus in busses:
                if connection == bus.uid.name:
                    for inp in bus.inputs:
                        carrier = inp.split('.', 1)[1]

        # links from bus 1 over connector to bus 2 (with same transmission on both sides)
        link1 = dict({
            f"{connected_busses[0]},{connector.uid.name}": {
                'techs': {f'{connector.uid.name} free transmission': None}},
        })
        link2 = dict({
            f"{connector.uid.name},{connected_busses[1]}": {
                'techs': {f'{connector.uid.name} transmission 1': None}},
        })
        links.update(link1)
        links.update(link2)

        # calculate eff that can be used on both transmissions to add up being same as tessif
        eff = connector.conversions[(f'{connected_busses[0]}', f'{connected_busses[1]}')]
        transmission = dict({
            f'{connector.uid.name} transmission 1': {
                'essentials': {
                    'name': f'{connector.uid.name} transmission 1',
                    'color': '#8465A9',
                    'parent': 'transmission',
                    'carrier': f'{carrier}'
                },
                'constraints': {'energy_eff': eff, 'one_way': True},
            },
        })
        transmissions.update(transmission)

        # 2nd connector location
        # links from bus 2 over connector to bus 1 (with same transmission on both sides)
        link1 = dict({
            f"{connected_busses[1]},{connector.uid.name} reverse": {
                'techs': {f'{connector.uid.name} free transmission': None}},
        })
        link2 = dict({
            f"{connector.uid.name} reverse,{connected_busses[0]}": {
                'techs': {f'{connector.uid.name} transmission 2': None}},
        })
        links.update(link1)
        links.update(link2)

        # calculate eff that can be used on both transmissions to add up being same as tessif
        eff = connector.conversions[(f'{connected_busses[1]}', f'{connected_busses[0]}')]
        transmission = dict({
            f'{connector.uid.name} transmission 2': {
                'essentials': {
                    'name': f'{connector.uid.name} transmission 2',
                    'color': '#8465A9',
                    'parent': 'transmission',
                    'carrier': f'{carrier}',
                },
                'constraints': {'energy_eff': eff, 'one_way': True},
            },
        })
        transmissions.update(transmission)

        # The efficiency is taken into account from bus to connector.
        # Connector to the other bus is loss free
        transmission = dict({
            f'{connector.uid.name} free transmission': {
                'essentials': {
                    'name': f'{connector.uid.name} free transmission',
                    'color': '#8465A9',
                    'parent': 'transmission',
                    'carrier': f'{carrier}',
                },
                'constraints': {'energy_eff': 1, 'one_way': True},
            },
        })
        transmissions.update(transmission)

    yield loc, links, transmissions


def transform(tessif_es, warnings=False, aggregate=None):
    """
    Transform a tessif energy system into an calliope energy system.
    In difference to the transform function the transform_and_save_yaml function does save the model in calliope style.
    Meaning the model is saved in separate yaml files as well as timeseries in csv files.
    These files are then read to build the calliope.core.model.Model.

    Parameters
    ----------
    tessif_es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        The tessif energy system model that is to be transformed into a
        calliope energy system model.

    warnings: :class: `~bool`
        Boolean to determine whether calliope specific warnings shall be
        shown in output or errors only.

    aggregate: int, default=None
        Integer defining the time series aggregation. E.g. "6" means that 6 of the hourly
        timesteps are going to be aggregated to one 6 hour timestep.

        Note
        ----
        The length of the optimized timeframe should be divisible by this value.

    Return
    ------
    calliope_es: :class:`calliope.core.model.Model`
        The calliope energy system model that was transformed out of the
        tessif energy system model.

    Warning
    -------
    The calliope transformation doesn't support Tessif CHP Component.
    Using a Transformer with 2 outputs is recommended.

    Calliope either has all or none storages cyclic. If the es2es transformation
    wants some to be cyclic and others not to be, none will be cyclic.

    Calliope only considers global emission constraints.

    Raises
    ------
    ValueError
        Calliope needs timeframes of at least 2 periods.

    NotImplementedError
        Raised if more than 1 input or more than 3 outputs is used, because calliope
        can't handle these cases in combination with tessif parameter definitions.

    TypeError
        For timeseries aggregation the parameter 'aggregate' needs to be of type integer.

    Examples
    --------
    Use the :ref:`example hub's <Examples>`
    :meth:`~tessif.examples.data.tsf.py_hard.create_mwe` utility for showcasing
    basic usage:

    1. Create the mwe:

        >>> from tessif.examples.data.tsf.py_hard import create_mwe
        >>> tsf_es = create_mwe()

    2. Transform the :mod:`tessif energy system
       <tessif.model.energy_system.AbstractEnergySystem>`:

        >>> from tessif.transform.es2es import cllp
        >>> cllp_es = cllp.transform(tsf_es)

    4. Simulate the calliope energy system model:

        >>> import tessif.simulate as simulate
        >>> optimized_calliope_es = simulate.cllp_from_es(cllp_es)

    5. Extract some results:

        >>> import tessif.transform.es2mapping.cllp as transform_calliope_results
        >>> node_results = transform_calliope_results.CalliopeResultier(
        ...     optimized_calliope_es)
        >>> for node in node_results.nodes:
        ...     print(node)
        Battery
        Demand
        Gas Station
        Generator
        Pipeline
        Powerline

        >>> load_results = transform_calliope_results.LoadResultier(
        ...     optimized_calliope_es)
        >>> print(load_results.node_load['Powerline'])
        Powerline            Battery  Generator  Battery  Demand
        1990-07-13 00:00:00    -10.0       -0.0      0.0    10.0
        1990-07-13 01:00:00     -0.0      -10.0      0.0    10.0
        1990-07-13 02:00:00     -0.0      -10.0      0.0    10.0
        1990-07-13 03:00:00     -0.0      -10.0      0.0    10.0
    """

    model_demands, model_supply, model_conversion, model_storage = dict(), dict(), dict(), dict()
    model_locations, model_links, model_transmissions = dict(), dict(), dict()
    storage_cycles = []
    supply_accumulated_amounts, demand_accumulated_amounts = dict(), dict()

    if len(tessif_es.timeframe) == 1:
        msg = (
            f"Calliope needs timeframes of at least 2 periods."
        )
        raise ValueError(msg)

    if not os.path.exists(f'{write_dir}/Calliope/{tessif_es.uid}'):
        os.makedirs(f'{write_dir}/Calliope/{tessif_es.uid}')
    if not os.path.exists(f'{write_dir}/Calliope/{tessif_es.uid}/model_config'):
        os.makedirs(f'{write_dir}/Calliope/{tessif_es.uid}/model_config')
    if not os.path.exists(f'{write_dir}/Calliope/{tessif_es.uid}/timeseries_data'):
        os.makedirs(f'{write_dir}/Calliope/{tessif_es.uid}/timeseries_data')

    for chp in tessif_es.chps:
        if chp:
            msg = (
                f"Calliope doesn't support the Tessif CHP component type. "
                f"A Transformer might be able to represent the component."
            )
            raise NotImplementedError(msg)

    for loc, links, transmissions in generate_calliope_bus_like_loc(
            busses=tessif_es.busses,
    ):
        model_locations.update(loc)
        model_links.update(links)
        model_transmissions.update(transmissions)

    for loc, links, transmissions in generate_calliope_connector(
            connectors=tessif_es.connectors,
            busses=tessif_es.busses,
    ):
        model_locations.update(loc)
        model_links.update(links)
        model_transmissions.update(transmissions)

    for sink, loc, grp_constraint in generate_calliope_demand(
            sinks=tessif_es.sinks,
            timeframe=tessif_es.timeframe,
            es_name=tessif_es.uid,
    ):
        model_demands.update(sink)
        model_locations.update(loc)
        demand_accumulated_amounts.update(grp_constraint)

    for source, loc, grp_constraint in generate_calliope_supply(
            sources=tessif_es.sources,
            timeframe=tessif_es.timeframe,
            es_name=tessif_es.uid,
    ):
        model_supply.update(source)
        model_locations.update(loc)
        supply_accumulated_amounts.update(grp_constraint)

    for transformer, loc in generate_calliope_conversion(
            transformers=tessif_es.transformers,
            timeframe=tessif_es.timeframe,
            es_name=tessif_es.uid,
    ):
        model_conversion.update(transformer)
        model_locations.update(loc)

    for storage, loc, cyclic in generate_calliope_storage(
            storages=tessif_es.storages,
            timeframe=tessif_es.timeframe,
    ):
        model_storage.update(storage)
        storage_cycles.extend(cyclic)
        model_locations.update(loc)

    # calliope can only consider all storages cyclic or none, but cant differ individually
    cyclic_storage = False
    # compare each element in list with the rest of this list
    for element, others in itertools.combinations(storage_cycles, 2):
        if element != others:
            cyclic_storage = False
            msg = (
                f"Some Storages are cyclic and others aren't. "
                f"Calliope can not differ this option individually "
                f"but only set all cyclic or none. Thus the storages "
                f"are set to be not cyclic. "
            )
            logger.warning(msg)
            break
        else:
            cyclic_storage = element

    technologies = dict(techs=dict())
    technologies['techs'].update(model_demands)
    technologies['techs'].update(model_supply)
    technologies['techs'].update(model_conversion)
    technologies['techs'].update(model_storage)
    technologies['techs'].update(model_transmissions)

    locations = dict(locations=dict(), links=dict())
    locations['locations'].update(model_locations)
    locations['links'].update(model_links)

    model = dict()
    model['import'] = list(
        {
            str('model_config/techs.yaml'),
            str('model_config/locations.yaml'),
        }
    )

    subset_time = [str(tessif_es.timeframe[0]), str(tessif_es.timeframe[-1])]
    # subset_time might be unnecessary due to csv files are as long as timeframe is
    # Still using it here, in case the yaml & csv will be used with calliope specific functions

    model['model'] = dict(
        {
            'name': str(tessif_es.uid),
            'calliope_version': '0.6.6-post1',
            'timeseries_data_path': 'timeseries_data',  # dataframes path
            'subset_time': subset_time,
        }
    )

    model['group_constraints'] = dict()
    if tessif_es.global_constraints:
        if 'emissions' in tessif_es.global_constraints:
            emi_cap = tessif_es.global_constraints['emissions']
            if emi_cap == float('inf'):
                # calliope v0.6.6 struggles with some group constraints like
                # 'inf' or inf or '.inf' does not work
                # while .inf does work but seems like there is no way to get it without the ' '
                model['group_constraints'].update({
                    'systemwide_emission_cap': dict(cost_max=dict(emissions=None))
                })
            else:
                model['group_constraints'].update({
                    'systemwide_emission_cap': dict(cost_max=dict(emissions=float(emi_cap)))
                })

        if not model['group_constraints']:
            msg = (
                f"Calliope can only consider global constraint "
                f"'emissions' "
            )
            logger.warning(msg)

    if supply_accumulated_amounts:
        model['group_constraints'].update(supply_accumulated_amounts)
    if demand_accumulated_amounts:
        model['group_constraints'].update(demand_accumulated_amounts)

    model['run'] = dict(
        {
            'solver': 'cbc',  # default, but can be changed via tessif.simulate function
            'cyclic_storage': cyclic_storage,
            'objective_options.cost_class': {'monetary': 1},
        }
    )

    # For translation in yaml file the dictionary values need to be either bool, int, float or str.
    # Some other types might work too, but e.g. '0.0' as numpy.float does not work while '0.0' as float does
    for key, value in technologies.items():  # key == techs
        for key1, value1 in value.items():  # key1 == each technology
            for key2, value2 in value1.items():  # key2 == essentials, constraints and costs of each tech
                for key3, value3 in value2.items():  # key3 == param key. Value3 might be param but can also be dicts
                    if not isinstance(value3, dict):
                        if isinstance(value3, (np.floating, np.integer)):
                            technologies[key][key1][key2][key3] = float(value3)
                    else:
                        for key4, value4 in value3.items():  # value4 shouldnt be a dict anymore
                            if isinstance(value4, (np.floating, np.integer)):
                                technologies[key][key1][key2][key3][key4] = float(
                                    value4)

    if aggregate:
        if isinstance(aggregate, int):
            model['model'].update({
                'time': {
                    'function': 'resample',
                    'function_options':
                        {'resolution': f'{aggregate}H'}
                }
            })
        else:
            msg = (
                f"Aggregate parameter needs to be an Integer or NoneType."
            )
            raise TypeError(msg)

    # storing the model in yaml files:
    with open(f'{write_dir}/Calliope/{tessif_es.uid}/model.yaml', 'w') as model_file:
        ruamel.yaml.dump(model, model_file,
                         default_flow_style=False, Dumper=MyDumper)
    with open(f'{write_dir}/Calliope/{tessif_es.uid}/model_config/techs.yaml', 'w') as techs_file:
        ruamel.yaml.dump(technologies, techs_file,
                         default_flow_style=False, Dumper=MyDumper)
    with open(f'{write_dir}/Calliope/{tessif_es.uid}/model_config/locations.yaml', 'w') as locations_file:
        ruamel.yaml.dump(locations, locations_file,
                         default_flow_style=False, Dumper=MyDumper)

    if warnings:
        calliope.set_log_verbosity('WARNING', include_solver_output=False)
    else:
        calliope.set_log_verbosity('ERROR', include_solver_output=False)

    calliope_es = calliope.Model(f'{write_dir}/Calliope/{tessif_es.uid}/model.yaml')

    return calliope_es
