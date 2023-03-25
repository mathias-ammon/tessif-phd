# tessif/examples/application/calliope_integration_scenarios.py
# -*- coding: utf-8 -*-
"""
:mod:`~tessif.examples.application.calliope_integration_scenarios` is a :mod:`tessif`
module aggregating the research results of a master thesis titled
**Comparison of modelling tools to optimize energy systems via integration into
an existing framework for transforming energy system models**
conducted by Max Reimer.
"""
# 1. Import the needed packages:
import os

import numpy as np
import pandas as pd

import tessif.frused.namedtuples as nts
from tessif.frused.paths import example_dir
from tessif.model import components, energy_system


def create_sources_example():
    """
    Create a small energy system utilizing two emisison free and
    expandable sources, as well as an emitting one.

    This small energy system was used to analyse the implementation of tessif
    sources, busses and demands in calliope as well as compare it to fine, oemof and pypsa.
    It is the same as the create_expansion_plan_example in :mod:`~tessif.examples.data.tsf.py_hard`

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Examples
    --------
    Use :func:`create_expansion_plan_example` to quickly access a tessif
    energy system to use for doctesting, or trying out this framework's
    utilities.

    >>> import tessif.examples.application.calliope_integration_scenarios as examples
    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> es = examples.create_sources_example()
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Powerline': '#009900',
    ...                 'Emitting Source': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Capped Renewable': '#ffD700',
    ...                 'Uncapped Renewable': '#ffD700',},
    ...     node_size={'Powerline': 5000},
    ...     layout='dot')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../data/images/expansion_plan_example.png
        :align: center
        :alt: Image showing the expansion plan example energy system graph.
    """

    # 2. Create a simulation time frame of 2 one hour time steps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3. Creating the individual energy system components:

    # emitting source having no costs and no flow constraints but emissions
    emitting_source = components.Source(
        name='Emitting Source',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_emissions={
            'electricity': 1
        },
    )

    # capped source having no costs, no emission, no flow constraints
    # but existing and max installed capacity (for expansion) as well
    # as expansion costs
    capped_renewable = components.Source(
        name='Capped Renewable',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=1, max=2)},
        flow_costs={'electricity': 2, },
        expandable={'electricity': True},
        expansion_costs={'electricity': 1},
        expansion_limits={'electricity': nts.MinMax(min=1, max=4)},
    )

    # uncapped source having no costs and no emissions
    # but an externally set timeseries as well as expansion costs
    uncapped_min, uncapped_max = [1, 2, 3, 1], [1, 2, 3, 1]

    uncapped_renewable = components.Source(
        name='Uncapped Renewable',
        outputs=('electricity',),
        # Minimum number of arguments required
        # flow_rates={'electricity': nts.MinMax(min=0, max=1)},
        flow_costs={'electricity': 2, },
        expandable={'electricity': True},
        expansion_costs={'electricity': 2},
        timeseries={
            'electricity': nts.MinMax(
                min=uncapped_min,
                max=uncapped_max
            )
        },
        expansion_limits={
            'electricity': nts.MinMax(
                min=max(uncapped_max),
                max=float('+inf'),
            )
        },
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=(
            'Emitting Source.electricity',
            'Capped Renewable.electricity',
            'Uncapped Renewable.electricity'),
        outputs=('Demand.electricity',),
        # Minimum number of arguments required
    )

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    global_constraints = {'emissions': 20}

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Sources_Example',  # adjusted
        busses=(electricity_line,),
        sinks=(demand,),
        sources=(
            emitting_source,
            capped_renewable,
            uncapped_renewable,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return explicit_es


def create_storage_example():
    """
    Create a small energy system utilizing an expandable storage with a fixed
    capacity to outflow ratio.

    This small energy system was used to analyse the implementation of tessif
    storages in calliope as well as compare it to fine, oemof and pypsa.
    It is an adjusted model following the create_storage_fixed_ratio_expansion_example
    in :mod:`~tessif.examples.data.tsf.py_hard`

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Note
    ----
    Calliope does not differ between input and outpuf efficiency, while the other tools do.
    Since this difference is already known analysing this is not needed anymore, hence the
    in and output efficiencies are set to be the same to find out unknown differences.

    Examples
    --------
    Using :func:`create_storage_example` to quickly access a tessif energy
    system to use for doctesting, or trying out this frameworks utilities.

    >>> import tessif.examples.application.calliope_integration_scenarios as examples
    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> tsf_es = examples.create_storage_example()
    >>> grph = tsf_es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Powerline': '#009900',
    ...                 'Storage': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Generator': '#ffD700',},
    ...     node_size={'Storage': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../data/images/storage_es_example.png
        :align: center
        :alt: Image showing the create_storage_example energy system graph.
    """

    timeframe = pd.date_range('7/13/1990', periods=5, freq='H')

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        carrier='electricity',
        node_type='sink',
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        timeseries={
            'electricity': nts.MinMax(
                min=np.array([10, 10, 7, 5, 10]),  # adjusted
                max=np.array([10, 10, 7, 5, 10])  # adjusted
            )
        }
    )

    generator = components.Source(
        name='Generator',
        outputs=('electricity',),
        carrier='electricity',
        node_type='source',
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 0},
        timeseries={
            'electricity': nts.MinMax(
                min=np.array([19, 19, 19, 0, 0]),
                max=np.array([19, 19, 19, 0, 0])
            )
        }
    )

    powerline = components.Bus(
        name='Powerline',
        inputs=('Generator.electricity', 'Storage.electricity'),
        outputs=('Demand.electricity', 'Storage.electricity',),
        carrier='electricity',
        node_type='bus',
    )

    storage = components.Storage(
        name='Storage',
        input='electricity',
        output='electricity',
        capacity=1,
        initial_soc=0.5,  # new
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.01),  # new
        flow_rates={'electricity': nts.MinMax(min=0, max=0.1)},
        flow_efficiencies={
             'electricity': nts.InOut(inflow=0.9, outflow=0.9)},  # adjusted
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 0.5},
        expandable={'capacity': True, 'electricity': True},
        fixed_expansion_ratios={'electricity': True},
        expansion_costs={'capacity': 2, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=1, max=float('+inf')),
            'electricity': nts.MinMax(min=0.1, max=float('+inf'))},
    )

    storage_es = energy_system.AbstractEnergySystem(
        uid='Storage_Example',  # adjusted
        busses=(powerline,),
        sinks=(demand,),
        sources=(generator,),
        storages=(storage,),
        timeframe=timeframe
    )

    return storage_es


def create_chp_example():
    """
    Create a small energy system using :mod:`tessif's
    model <tessif.model>` optimizing it for costs to demonstrate
    a chp application.

    This small energy system was used to analyse the implementation of tessif
    multi output transformer in calliope as well as compare it to fine, oemof and pypsa.
    It is an adjusted model following the create_chp
    in :mod:`~tessif.examples.data.tsf.py_hard`

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Examples
    --------

    Using :func:`create_chp` to quickly access a tessif energy system
    to use for doctesting, or trying out this frameworks utilities.

    >>> import tessif.examples.application.calliope_integration_scenarios as examples
    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> tsf_es = examples.create_chp_example()
    >>> grph = tsf_es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Gas Source': '#669999',
    ...         'Gas Grid': '#669999',
    ...         'CHP': '#6633cc',
    ...         'Backup Heat': 'red',
    ...         'Heat Grid': 'red',
    ...         'Heat Demand': 'red',
    ...         'Backup Power': 'yellow',
    ...         'Powerline': 'yellow',
    ...         'Power Demand': 'yellow',
    ...     },
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../transformation/auto_comparison/chp_graph.png
       :align: center
       :alt: Image showing analyzed chp graph.
    """

    # 2. Create a simulation time frame of four one-hour timesteps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    global_constraints = {'emissions': float('+inf')}

    # 3. Creating the individual energy system components:
    gas_supply = components.Source(
        name='Gas Source',
        outputs=('gas',),
        # Minimum number of arguments required
    )

    gas_grid = components.Bus(
        name='Gas Grid',
        inputs=('Gas Source.gas', ),
        outputs=('CHP.gas',),
        # Minimum number of arguments required
    )

    # conventional power supply is cheaper, but has emissions allocated to it
    chp = components.Transformer(
        name='CHP',
        inputs=('gas',),
        outputs=('electricity', 'heat'),
        conversions={
            ('gas', 'electricity'): 0.3,
            ('gas', 'heat'): 0.2,
        },
        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),  # new
            'electricity': nts.MinMax(min=0, max=3),  # new
            'heat': nts.MinMax(min=0, max=2)},  # new
        flow_costs={'electricity': 3, 'heat': 2, 'gas': 0},
        flow_emissions={'electricity': 2, 'heat': 3, 'gas': 0},
        expandable={'gas': False, 'electricity': True, 'heat': True},  # new
        expansion_costs={'gas': 0, 'electricity': 2, 'heat': 1},  # new
        expansion_limits={
            'gas': nts.MinMax(min=0, max=float('+inf')),  # new
            'electricity': nts.MinMax(min=3, max=float('+inf')),  # new
            'heat': nts.MinMax(min=2, max=float('+inf'))},  # new
    )

    # back up power, expensive
    backup_power = components.Source(
        name='Backup Power',
        outputs=('electricity',),
        flow_costs={'electricity': 100},  # adjusted
    )

    # Power demand needing 10 energy units per time step
    power_demand = components.Sink(
        name='Power Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    power_line = components.Bus(
        name='Powerline',
        inputs=('Backup Power.electricity', 'CHP.electricity'),
        outputs=('Power Demand.electricity',),
        # Minimum number of arguments required
    )

    # Back up heat source, expensive
    backup_heat = components.Source(
        name='Backup Heat',
        outputs=('heat',),
        flow_costs={'heat': 100},  # adjusted
    )

    # Heat demand needing 10 energy units per time step
    heat_demand = components.Sink(
        name='Heat Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        flow_rates={'heat': nts.MinMax(min=10, max=10)},
    )

    heat_grid = components.Bus(
        name='Heat Grid',
        inputs=('CHP.heat', 'Backup Heat.heat'),
        outputs=('Heat Demand.heat',),
        # Minimum number of arguments required
    )

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='CHP_Example',
        busses=(gas_grid, power_line, heat_grid),
        sinks=(power_demand, heat_demand),
        sources=(gas_supply, backup_power, backup_heat),
        transformers=(chp,),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return explicit_es


def create_connector_example():
    """
    Create a small energy system using :mod:`tessif's
    model <tessif.model>` optimizing it for costs to demonstrate
    a connector.

    This small energy system was used to analyse the implementation of tessif
    connector in calliope as well as compare it to fine, oemof and pypsa.
    It is an the same model as the create_connected_es
    in :mod:`~tessif.examples.data.tsf.py_hard`

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Examples
    --------
    Using :func:`create_connected_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this frameworks utilities:

    >>> import tessif.examples.application.calliope_integration_scenarios as examples
    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> es = examples.create_connector_example()
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'connector': '#9999ff',
    ...                 'bus-01': '#cc0033',
    ...                 'bus-02': '#00ccff'},
    ...     node_size={'connector': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../data/images/connected_es_example.png
        :align: center
        :alt: alternate text
    """

    timeframe = pd.date_range('7/13/1990', periods=3, freq='H')

    s1 = components.Sink(
        name='sink-01',
        inputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=15)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([0, 15, 10]), max=np.array([0, 15, 10]))})

    so1 = components.Source(
        name='source-01',
        outputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 0.8})

    mb1 = components.Bus(
        name='bus-01',
        inputs=('source-01.electricity',),
        outputs=('sink-01.electricity',),
    )

    s2 = components.Sink(
        name='sink-02',
        inputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=15)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([15, 0, 10]), max=np.array([15, 0, 10]))})

    so2 = components.Source(
        name='source-02',
        outputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 1.2})

    mb2 = components.Bus(
        name='bus-02',
        inputs=('source-02.electricity',),
        outputs=('sink-02.electricity',),
    )

    c = components.Connector(
        name='connector',
        interfaces=('bus-01', 'bus-02'),
        conversions={('bus-01', 'bus-02'): 0.9,
                     ('bus-02', 'bus-01'): 0.8})

    connected_es = energy_system.AbstractEnergySystem(
        uid='Connector_Example',  # adjusted
        busses=(mb1, mb2),
        sinks=(s1, s2,),
        sources=(so1, so2),
        connectors=(c,),
        timeframe=timeframe
    )

    return connected_es


def create_component_example(
        expansion_problem=False, periods=8760,):
    """
    Create a model of a generic component based energy system using
    :mod:`tessif's model <tessif.model>`.

    This energy system was used to compare calliope to fine, oemof and pypsa in a
    bigger example for the timeframe of a year in hourly resolution.
    It is an the same model as the create_component_es
    in :mod:`~tessif.examples.data.tsf.py_hard`

    Parameters
    ----------
    expansion_problem : bool, default=False
        Boolean which states whether a commitment problem (False)
        or expansion problem (True) is to be solved

    periods : int, default=3
        Number of time steps of the evaluated timeframe
        (one time step is one hour)

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Examples
    --------
    Use :func:`create_component_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.application.calliope_integration_scenarios as examples
    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> es = examples.create_component_example()
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...        'Hard Coal Supply': '#666666',
    ...        'Hard Coal Supply Line': '#666666',
    ...        'Hard Coal PP': '#666666',
    ...        'Hard Coal CHP': '#666666',
    ...        'Solar Panel': '#FF7700',
    ...        'Heat Storage': '#cc0033',
    ...        'Heat Demand': 'Red',
    ...        'Heat Plant': '#cc0033',
    ...        'Heatline': 'Red',
    ...        'Power To Heat': '#cc0033',
    ...        'Biogas CHP': '#006600',
    ...        'Biogas Line': '#006600',
    ...        'Biogas Supply': '#006600',
    ...        'Onshore Wind Turbine': '#99ccff',
    ...        'Offshore Wind Turbine': '#00ccff',
    ...        'Gas Station': '#336666',
    ...        'Gas Line': '#336666',
    ...        'Combined Cycle PP': '#336666',
    ...        'El Demand': '#ffe34d',
    ...        'Battery': '#ffe34d',
    ...        'Powerline': '#ffcc00',
    ...        'Lignite Supply': '#993300',
    ...        'Lignite Supply Line': '#993300',
    ...        'Lignite Power Plant': '#993300',
    ...      },
    ...     node_size={
    ...        'Powerline': 5000,
    ...        'Heatline': 5000
    ...    },
    ...      title='Component Based Example Energy System Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../data/images/component_es_example.png
       :align: center
       :alt: Image showing the create_component_es energy system graph.

    """
    # Create a simulation time frame
    timeframe = pd.date_range('1/1/2019', periods=periods, freq='H')

    # Initiate the global constraints depending on the scenario
    if expansion_problem is False:
        use_case = 'commitment'  # new
        global_constraints = {
            'name': 'Commitment_Scenario',
            'emissions': float('+inf'),
        }
    else:
        use_case = 'expansion'  # new
        global_constraints = {
            'name': 'Expansion_Scenario',
            'emissions': 250000,
        }

    # Variables for timeseries of fluctuate wind, solar and demand

    csv_data = pd.read_csv(os.path.join(example_dir, 'data', 'tsf', 'load_profiles',
                                        'component_scenario_profiles.csv'), index_col=0, sep=';')

    # solar:
    pv = csv_data['pv'].values.flatten()[0:periods]
    # scale relative values with the installed pv power
    pv = pv * 1100

    # wind onshore:
    wind_onshore = csv_data['wind_on'].values.flatten()[0:periods]
    # scale relative values with installed onshore power
    wind_onshore = wind_onshore * 1100

    # wind offshore:
    wind_offshore = csv_data['wind_off'].values.flatten()[0:periods]
    # scale relative values with installed offshore power
    wind_offshore = wind_offshore * 150

    # electricity demand:
    el_demand = csv_data['el_demand'].values.flatten()[0:periods]
    max_el = np.max(el_demand)

    # heat demand:
    th_demand = csv_data['th_demand'].values.flatten()[0:periods]
    max_th = np.max(th_demand)

    # Creating the individual energy system components:

    # ---------------- Sources (incl wind and solar) -----------------------

    hard_coal_supply = components.Source(
        name='Hard Coal Supply',
        outputs=('Hard_Coal',),
        sector='Power',
        carrier='Hard_Coal',
        node_type='source',
        accumulated_amounts={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'Hard_Coal': 0},
        flow_emissions={'Hard_Coal': 0},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'Hard_Coal': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False},
        expansion_costs={'Hard_Coal': 0},
        expansion_limits={'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
    )

    lignite_supply = components.Source(
        name='Lignite Supply',
        outputs=('lignite',),
        sector='Power',
        carrier='Lignite',
        node_type='source',
        accumulated_amounts={
            'lignite': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'lignite': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'lignite': 0},
        flow_emissions={'lignite': 0},
        flow_gradients={
            'lignite': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'lignite': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'lignite': False},
        expansion_costs={'lignite': 0},
        expansion_limits={'lignite': nts.MinMax(min=0, max=float('+inf'))},
    )

    fuel_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        sector='Power',
        carrier='Gas',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'fuel': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 0},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
    )

    biogas_supply = components.Source(
        name='Biogas Supply',
        outputs=('biogas',),
        sector='Power',
        carrier='Biogas',
        node_type='source',
        accumulated_amounts={
            'biogas': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'biogas': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'biogas': 0},
        flow_emissions={'biogas': 0},
        flow_gradients={
            'biogas': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'biogas': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'biogas': False},
        expansion_costs={'biogas': 0},
        expansion_limits={'biogas': nts.MinMax(min=0, max=float('+inf'))},
    )

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1100)},
        flow_costs={'electricity': 80},
        flow_emissions={'electricity': 0.05},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(pv))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 1000000},
        expansion_limits={'electricity': nts.MinMax(
            min=1100, max=float('+inf'))},
    )

    onshore_wind_turbine = components.Source(
        name='Onshore Wind Turbine',
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1100)},
        flow_costs={'electricity': 60},
        flow_emissions={'electricity': 0.02},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(wind_onshore))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 1750000},
        expansion_limits={'electricity': nts.MinMax(
            min=1100, max=float('+inf'))},
    )

    offshore_wind_turbine = components.Source(
        name='Offshore Wind Turbine',
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=150)},
        flow_costs={'electricity': 105},
        flow_emissions={'electricity': 0.02},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(wind_offshore))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 3900000},
        expansion_limits={'electricity': nts.MinMax(
            min=150, max=float('+inf'))},
    )

    # ---------------- Transformer -----------------------

    hard_coal_chp = components.Transformer(
        name='Hard Coal CHP',
        inputs=('Hard_Coal',),
        outputs=('electricity', 'hot_water',),
        conversions={('Hard_Coal', 'electricity'): 0.4,
                     ('Hard_Coal', 'hot_water'): 0.4},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=300),
            'hot_water': nts.MinMax(min=0, max=300)},
        flow_costs={'Hard_Coal': 0, 'electricity': 80, 'hot_water': 6},
        flow_emissions={'Hard_Coal': 0, 'electricity': 0.8, 'hot_water': 0.06},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'Hard_Coal': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False,
                    'electricity': expansion_problem, 'hot_water': expansion_problem},
        expansion_costs={'Hard_Coal': 0,
                         'electricity': 1750000, 'hot_water': 131250},
        expansion_limits={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=300, max=float('+inf')),
            'hot_water': nts.MinMax(min=300, max=float('+inf'))},
    )

    hard_coal_power_plant = components.Transformer(
        name='Hard Coal PP',
        inputs=('Hard_Coal',),
        outputs=('electricity',),
        conversions={('Hard_Coal', 'electricity'): 0.43},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=500), },
        flow_costs={'Hard_Coal': 0, 'electricity': 80},
        flow_emissions={'Hard_Coal': 0, 'electricity': 0.8},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'Hard_Coal': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False, 'electricity': expansion_problem},
        expansion_costs={'Hard_Coal': 0, 'electricity': 1650000},
        expansion_limits={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=500, max=float('+inf'))},
    )

    combined_cycle_power_plant = components.Transformer(
        name='Combined Cycle PP',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.6},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=600)},
        flow_costs={'fuel': 0, 'electricity': 90},
        flow_emissions={'fuel': 0, 'electricity': 0.35},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': expansion_problem},
        expansion_costs={'fuel': 0, 'electricity': 950000},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=600, max=float('+inf'))},
    )

    lignite_power_plant = components.Transformer(
        name='Lignite Power Plant',
        inputs=('lignite',),
        outputs=('electricity',),
        conversions={('lignite', 'electricity'): 0.4},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'lignite': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=500)},
        flow_costs={'lignite': 0, 'electricity': 65},
        flow_emissions={'lignite': 0, 'electricity': 1},
        flow_gradients={
            'lignite': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'lignite': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'lignite': False, 'electricity': expansion_problem},
        expansion_costs={'lignite': 0, 'electricity': 1900000},
        expansion_limits={
            'lignite': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=500, max=float('+inf'))},
    )

    biogas_chp = components.Transformer(
        name='Biogas CHP',
        inputs=('biogas',),
        outputs=('electricity', 'hot_water',),
        conversions={('biogas', 'electricity'): 0.4,
                     ('biogas', 'hot_water'): 0.5},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'biogas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=200),
            'hot_water': nts.MinMax(min=0, max=250)},
        flow_costs={'biogas': 0, 'electricity': 150, 'hot_water': 11.25},
        flow_emissions={'biogas': 0, 'electricity': 0.25, 'hot_water': 0.01875},
        flow_gradients={
            'biogas': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'biogas': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'biogas': False,
                    'electricity': expansion_problem, 'hot_water': expansion_problem},
        expansion_costs={'biogas': 0,
                         'electricity': 3500000, 'hot_water': 262500},
        expansion_limits={
            'biogas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=200, max=float('+inf')),
            'hot_water': nts.MinMax(min=250, max=float('+inf'))},
    )

    heat_plant = components.Transformer(
        name='Heat Plant',
        inputs=('fuel',),
        outputs=('hot_water',),
        conversions={('fuel', 'hot_water'): 0.9},
        sector='Power',
        carrier='hot_water',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=450)},
        flow_costs={'fuel': 0, 'hot_water': 35},
        flow_emissions={'fuel': 0, 'hot_water': 0.23},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'hot_water': expansion_problem},
        expansion_costs={'fuel': 0, 'hot_water': 390000},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=450, max=float('+inf'))},
    )

    power_to_heat = components.Transformer(
        name='Power To Heat',
        inputs=('electricity',),
        outputs=('hot_water',),
        conversions={('electricity', 'hot_water'): 0.99},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=100)},
        flow_costs={'electricity': 0, 'hot_water': 20},
        flow_emissions={'electricity': 0, 'hot_water': 0.0007},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'electricity': False, 'hot_water': expansion_problem},
        expansion_costs={'electricity': 0, 'hot_water': 100000},
        expansion_limits={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=100, max=float('+inf'))},
    )

    # ---------------- Storages -----------------------

    storage = components.Storage(
        name='Battery',
        input='electricity',
        output='electricity',
        capacity=100,
        initial_soc=0,
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.5),
        flow_rates={'electricity': nts.MinMax(min=0, max=33)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'electricity': 400},
        flow_emissions={'electricity': 0.06},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': expansion_problem, 'electricity': expansion_problem},
        fixed_expansion_ratios={'electricity': expansion_problem},
        expansion_costs={'capacity': 1630000, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=100, max=float('+inf')),
            'electricity': nts.MinMax(min=33, max=float('+inf'))},
    )

    heat_storage = components.Storage(
        name='Heat Storage',
        input='hot_water',
        output='hot_water',
        capacity=50,
        initial_soc=0,
        sector='Heat',
        carrier='hot_water',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.25),
        flow_rates={'hot_water': nts.MinMax(min=0, max=10)},
        flow_efficiencies={
            'hot_water': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'hot_water': 20},
        flow_emissions={'hot_water': 0},
        flow_gradients={
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'hot_water': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': expansion_problem, 'hot_water': expansion_problem},
        fixed_expansion_ratios={'hot_water': expansion_problem},
        expansion_costs={'capacity': 4500, 'hot_water': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=50, max=float('+inf')),
            'hot_water': nts.MinMax(min=10, max=float('+inf'))},
    )

    # ---------------- Sinks -----------------------

    el_demand = components.Sink(
        name='El Demand',
        inputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=max_el)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(el_demand),
            max=np.array(el_demand))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    heat_demand = components.Sink(
        name='Heat Demand',
        inputs=('hot_water',),
        sector='Heat',
        carrier='hot_water',
        node_type='demand',
        accumulated_amounts={
            'hot_water': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'hot_water': nts.MinMax(min=0, max=max_th)},
        flow_costs={'hot_water': 0},
        flow_emissions={'hot_water': 0},
        flow_gradients={
            'hot_water': nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'hot_water': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'hot_water': nts.MinMax(
            min=np.array(th_demand),
            max=np.array(th_demand))},
        expandable={'hot_water': False},
        expansion_costs={'hot_water': 0},
        expansion_limits={'hot_water': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    # ---------------- Busses -----------------------

    fuel_supply_line = components.Bus(
        name='Gas Line',
        inputs=('Gas Station.fuel',),
        outputs=('Combined Cycle PP.fuel', 'Heat Plant.fuel'),
        sector='Coupled',
        carrier='Gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas Line',
        inputs=('Biogas Supply.biogas',),
        outputs=('Biogas CHP.biogas',),
        sector='Coupled',
        carrier='Biogas',
        node_type='bus',
    )

    hard_coal_supply_line = components.Bus(
        name='Hard Coal Supply Line',
        inputs=('Hard Coal Supply.Hard_Coal',),
        outputs=('Hard Coal PP.Hard_Coal', 'Hard Coal CHP.Hard_Coal',),
        sector='Coupled',
        carrier='Hard_Coal',
        node_type='bus',
    )

    lignite_supply_line = components.Bus(
        name='Lignite Supply Line',
        inputs=('Lignite Supply.lignite',),
        outputs=('Lignite Power Plant.lignite',),
        sector='Power',
        carrier='Lignite',
        node_type='bus',
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=('Combined Cycle PP.electricity', 'Battery.electricity',
                'Lignite Power Plant.electricity', 'Hard Coal PP.electricity',
                'Hard Coal CHP.electricity', 'Solar Panel.electricity',
                'Offshore Wind Turbine.electricity', 'Biogas CHP.electricity',
                'Onshore Wind Turbine.electricity',
                ),
        outputs=('El Demand.electricity', 'Battery.electricity',
                 'Power To Heat.electricity'),
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='Heatline',
        inputs=('Heat Plant.hot_water', 'Hard Coal CHP.hot_water', 'Biogas CHP.hot_water',
                'Power To Heat.hot_water', 'Heat Storage.hot_water'),
        outputs=('Heat Demand.hot_water', 'Heat Storage.hot_water'),
        sector='Heat',
        carrier='hot_water',
        node_type='bus',
    )

    # Creating the actual energy system:

    explicit_es = energy_system.AbstractEnergySystem(
        uid=f'Component_{use_case}_es',  # adjusted
        busses=(fuel_supply_line, electricity_line, hard_coal_supply_line,
                lignite_supply_line, biogas_supply_line, heat_line,),
        sinks=(el_demand, heat_demand),
        sources=(fuel_supply, solar_panel, onshore_wind_turbine, hard_coal_supply,
                 lignite_supply, offshore_wind_turbine, biogas_supply,),
        transformers=(combined_cycle_power_plant, hard_coal_power_plant, lignite_power_plant,
                      biogas_chp, heat_plant, power_to_heat, hard_coal_chp),
        storages=(storage, heat_storage),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return explicit_es
