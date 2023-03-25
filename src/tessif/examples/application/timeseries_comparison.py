"""
Enerysystems to test timeseries algorithms

"""
import os

import numpy as np
from oemof.tools import economics
import pandas as pd

import tessif.frused.namedtuples as nts
from tessif.frused.paths import example_dir
from tessif.model import components, energy_system


def create_hhes_ar(periods=24, directory=None, filename=None):
    """
    Create a model of Hamburg's energy system using :mod:`tessif's
    model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_hhes.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``hhes.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_HH` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------
    Use :func:`create_hhes` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_hhes()

    >>> for node in es.nodes:
    ...     print(node.uid)
    coal supply line
    gas pipeline
    oil supply line
    waste supply
    powerline
    district heating pipeline
    biomass logistics
    gas supply
    coal supply
    oil supply
    waste
    pv1
    won1
    biomass supply
    imported el
    imported heat
    demand el
    demand th
    excess el
    excess th
    chp1
    chp2
    chp3
    chp4
    chp5
    chp6
    pp1
    pp2
    pp3
    pp4
    hp1
    p2h
    biomass chp
    est

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'coal supply': '#404040',
    ...         'coal supply line': '#404040',
    ...         'pp1': '#404040',
    ...         'pp2': '#404040',
    ...         'chp3': '#404040',
    ...         'chp4': '#404040',
    ...         'chp5': '#404040',
    ...         'hp1': '#b30000',
    ...         'imported heat': '#b30000',
    ...         'district heating pipeline': 'Red',
    ...         'demand th': 'Red',
    ...         'excess th': 'Red',
    ...         'p2h': '#b30000',
    ...         'bm1': '#006600',
    ...         'won1': '#99ccff',
    ...         'gas supply': '#336666',
    ...         'gas pipeline': '#336666',
    ...         'chp1': '#336666',
    ...         'chp2': '#336666',
    ...         'waste': '#009900',
    ...         'waste supply': '#009900',
    ...         'chp6': '#009900',
    ...         'oil supply': '#666666',
    ...         'oil supply line': '#666666',
    ...         'pp3': '#666666',
    ...         'pp4': '#666666',
    ...         'pv1': '#ffd900',
    ...         'imported el': '#ffd900',
    ...         'demand el': '#ffe34d',
    ...         'excess el': '#ffe34d',
    ...         'est': '#ffe34d',
    ...         'powerline': '#ffcc00',
    ...     },
    ...     node_size={
    ...         'powerline': 5000,
    ...         'district heating pipeline': 5000
    ...     },
    ...     layout='dot',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../data/images/hh_es_example.png
        :align: center
        :alt: Image showing the create_grid_es energy system graph.

    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('2019-01-01', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv_HH = pd.read_csv(os.path.join(d, 'solar_HH_2019.csv'), index_col=0,
                        sep=';')
    pv_HH = pv_HH.values.flatten()[0:periods]
    max_pv = np.max(pv_HH)

    # wind onshore:
    wo_HH = pd.read_csv(os.path.join(d, 'wind_HH_2019.csv'), index_col=0,
                        sep=';')
    wo_HH = wo_HH.values.flatten()[0:periods]
    max_wo = np.max(wo_HH)

    # electricity demand:
    de_HH = pd.read_csv(os.path.join(d, 'el_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    de_HH = de_HH['Last (MW)'].values.flatten()[0:periods]
    de_HH = np.array(de_HH)
    max_de = np.max(de_HH)

    # heat demand:
    th_HH = pd.read_csv(os.path.join(d, 'th_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    th_HH = th_HH['actual_total_load'].values.flatten()[0:periods]
    th_HH = np.array(th_HH)
    max_th = np.max(th_HH)

    # 4. Create the individual energy system components:
    in_stat = False
    cfba = 0

    # Global Constraints:

    global_constraints = {
        'name': '2019',
        'emissions': float('+inf'),
        'resources': float('+inf')}

    # Fossil Sources:

    gass = components.Source(
        name='gas supply',
        outputs=('gas',),
        region='HH',
        node_type='gas_supply',
        component='source',
        sector='coupled',
        carrier='gas',
    )

    # HKW ADM:

    chp1 = components.Transformer(
        name='gas power plant',
        inputs=('gas',),
        outputs=('electricity',
                 'hot_water'),
        conversions={
            ('gas', 'electricity'): 0.3773,
            ('gas', 'hot_water'): 0.3,
        },  # conventional_power_plants_DE.xls
        latitude=53.51,
        longitude=9.94985,
        region='HH',
        node_type='HKW ADM',
        component='transformer',
        sector='coupled',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf')),  # 6.75
            'hot_water': nts.MinMax(min=0, max=float('+inf'))
        },
        flow_costs={'gas': 0,
                    'electricity': 90,
                    'hot_water': 21.6},
        flow_emissions={'gas': 0.2,
                        'electricity': 0,
                        'hot_water': 0},

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 1),
        status_changing_costs=nts.OnOff(24, 0),
        costs_for_being_active=cfba,
    )

    # Heizwerk Hafencity:
    hp1 = components.Transformer(
        name='heat power plant',
        inputs=('gas',),
        outputs=('hot_water',),
        conversions={('waste', 'hot_water'): 0.96666, },
        latitude=53.54106052,
        longitude=9.99590096,
        region='HH',
        node_type='Heizwerk Hafencity',
        component='transformer',
        sector='heat',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=348),  # max=348
        },
        flow_costs={'gas': 0,
                    'hot_water': 20,
                    },
        flow_emissions={'gas': 0.0,  # 0.2
                        'hot_water': 0.2,
                        },

        expandable={'gas': False,
                    'hot_water': True},
        expansion_costs={'gas': 0,
                         'hot_water': 0, },
        expansion_limits={'gas': nts.MinMax(min=0, max=float('+inf')),
                          'hot_water': nts.MinMax(min=348, max=float('+inf'))},
    )

    # Biomass Combined Heat and Power

    # Renewables:

    pv1 = components.Source(
        name='solar',
        outputs=('electricity',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='power',
        carrier='solar',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 74},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv_HH, max=pv_HH)},

        expandable={'electricity': True},
        expansion_costs={'electricity': economics.annuity(capex=1000000, n=20,
                                                          wacc=0.05)},
        expansion_limits={'electricity': nts.MinMax(
            min=max_pv, max=float('+inf'))},
    )

    won1 = components.Source(
        name='wind',
        outputs=('electricity',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='power',
        carrier='wind',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_wo)},
        flow_costs={'electricity': 61},
        flow_emissions={'electricity': 0.007},  # 0.007
        timeseries={'electricity': nts.MinMax(min=wo_HH, max=wo_HH)},

        expandable={'electricity': True},
        expansion_costs={'electricity': economics.annuity(capex=1750000, n=20,
                                                          wacc=0.05)},
        expansion_limits={'electricity': nts.MinMax(
            min=max_wo, max=float('+inf'))},
    )

    # bm1 = components.Source(
    #     name='bm1',
    #     outputs=('electricity', 'hot_water'),
    #     region='HH',
    #     node_type='renewable',
    #     component='source',
    #     sector='coupled',
    #     carrier='biomass',

    #     flow_rates={'electricity': nts.MinMax(min=0, max=48.4),
    #                 'hot_water': nts.MinMax(min=0, max=126),
    #                 },
    #     flow_costs={'electricity': 61,  # 61
    #                 'hot_water': 20,  # 61
    #                 },
    #     flow_emissions={'electricity': 0.001,
    #                     'hot_water': 0.001,
    #                     },

    #     initial_status=in_stat,
    #     status_inertia=nts.OnOff(0, 9),
    #     status_changing_costs=nts.OnOff(40, 0),
    # )

    # Storages:

    est = components.Storage(
        name='electrical storage',
        input='electricity',
        output='electricity',
        capacity=1,
        initial_soc=1,

        region='HH',
        sector='power',
        carrier='electricity',
        component='storage',

        flow_rates={'electricity': nts.MinMax(0, float('+inf'))},
        flow_costs={'electricity': 20},
        flow_emissions={'electricity': 0},

        expendable={'capacity': True, 'electricity': False},
        expansion_costs={'capacity': economics.annuity(capex=1000000, n=10,
                                                       wacc=0.05)}
    )

    # P2H Karoline:

    p2h = components.Transformer(
        name='power to heat',
        inputs=('electricity',),
        outputs=('hot_water',),
        conversions={('electricity', 'hot_water'): 0.99, },
        latitude=53.55912,
        longitude=9.97148,
        region='HH',
        node_type='power2heat',
        component='transformer',
        sector='heat',
        carrier='hot_water',

        flow_rates={'electricity': nts.MinMax(min=0, max=float('+inf')),
                    'hot_water': nts.MinMax(min=0, max=45)},  # 45
        flow_costs={'electricity': 0,
                    'hot_water': 0},
        flow_emissions={'electricity': 0,
                        'hot_water': 0},  # 0.007
        expandable={'electricity': False,
                    'hot_water': True},
        expansion_costs={'hot_water': economics.annuity(capex=200000, n=30,
                                                        wacc=0.05)},
        expansion_limits={'hot_water': nts.MinMax(min=45, max=200)},

    )

    # Imported Electricity/ Heat:

    imel = components.Source(
        name='imported el',
        outputs=('electricity',),
        region='HH',
        node_type='import',
        component='source',
        sector='power',
        carrier='electricity',

        flow_costs={'electricity': 999},
        flow_emissions={'electricity': 0.401},

        expendable={'electricity': True},
        expansion_costs={'electricity': 999999999},
    )

    imth = components.Source(
        name='imported th',
        outputs=('hot_water',),
        region='HH',
        node_type='import',
        component='source',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),

        flow_costs={'hot_water': 999},
        flow_emissions={'hot_water': 0.1},

        expendable={'hot_water': True},
        expansion_costs={'hot_water': 999999999},
    )

    # Sinks:

    demand_el = components.Sink(
        name='demand el',
        inputs=('electricity',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='power',
        carrier='electricity',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_de)},
        timeseries={'electricity': nts.MinMax(min=de_HH, max=de_HH)},
    )

    demand_th = components.Sink(
        name='demand th',
        inputs=('hot_water',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),

        flow_rates={'hot_water': nts.MinMax(min=0, max=max_th)},
        timeseries={'hot_water': nts.MinMax(min=th_HH, max=th_HH)},
    )

    excess_el = components.Sink(
        name='excess el',
        inputs=('electricity',),
        region='HH',
        node_type='excess',
        component='sink',
        sector='power',
        carrier='electricity',
    )

    excess_th = components.Sink(
        name='excess th',
        inputs=('hot_water',),
        region='HH',
        node_type='excess',
        component='sink',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),
    )

    # Busses:

    gas_pipeline = components.Bus(
        name='gas pipeline',
        region='HH',
        node_type='gas_pipeline',
        component='bus',
        sector='coupled',
        carrier='gas',

        inputs=('gas supply.gas',),
        outputs=('gas power plant.gas',
                 'chp2.gas',

                 'heat power plant.gas'),
    )

    powerline = components.Bus(
        name='powerline',
        region='HH',
        node_type='powerline',
        component='bus',
        sector='power',
        carrier='electricity',

        inputs=('gas power plant.electricity',


                'solar.electricity',
                'wind.electricity',

                # 'bm1.electricity',

                'imported el.electricity',

                'electrical storage.electricity'),
        outputs=('demand el.electricity',
                 'excess el.electricity',

                 'electrical storage.electricity',

                 'power to heat.electricity',),
    )

    district_heating = components.Bus(
        name='district heating pipeline',
        region='HH',
        node_type='district_heating_pipeline',
        component='bus',
        sector='heat',
        carrier='hot_water',

        inputs=('gas power plant.hot_water',

                # 'bm1.hot_water',


                'imported th.hot_water',

                'power to heat.hot_water',

                'heat power plant.hot_water',),
        outputs=('demand th.hot_water',
                 'excess th.hot_water',),)

    # 4. Create the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Energy System Hamburg',
        busses=(gas_pipeline,
                powerline, district_heating,),
        sinks=(demand_el, demand_th, excess_el, excess_th,),
        sources=(gass, pv1,
                 won1, imel, imth,),
        transformers=(chp1,
                      hp1, p2h,),
        storages=(est,),
        timeframe=timeframe,
        global_constraints=global_constraints,
        # milp=True,
    )

    # 5. Store the energy system:
    if not filename:
        filename = 'hhes.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    """

    # 4. Create the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Energy System Hamburg',
        busses=( gas_pipeline,
                powerline, district_heating,),
        sinks=(demand_el, demand_th, excess_el, excess_th,),
        sources=(gass, pv1,
                 won1,),
        transformers=(chp1,
                      hp1, p2h,),
        storages=(),
        timeframe=timeframe,
        global_constraints=global_constraints,
        # milp=True,
    )

    # 5. Store the energy system:
    if not filename:
        filename = 'hhes_ar.tsf'

    explicit_es.dump(directory=directory, filename=filename)
    """

    return explicit_es


# 720
# 168

periods = 100  # int(8760/4)
RANDTS = np.random.randint(300, 400, periods)


def norm(maximum, minimum=0, period=periods, ones=np.ones(periods), t=None):
    f = ones * (1 / maximum)
    if t is None:
        ts = np.random.randint(minimum, maximum, period)
        pmax = np.array(ts * f)
    else:
        ts = t
        pmax = np.array(ts * f)

    return pmax


def create_statistical_example_msc(periods=24,):
    """
    Create a model of Hamburg's energy system using :mod:`tessif's
    model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_HH` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------
    Use :func:`create_statistical_example_msc()` to quickly access a tessif
    energy system model scenario combination (msc) to use for ting, or trying
    out this framework's utilities:

    >>> from tessif.examples.application import timeseries_comparison
    >>> msc = timeseries_comparison.create_statistical_example_msc()

    Visualize the msc as generic graph:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> drawing_data = nxv.draw_graph(
    ...     msc.to_nxgrph(),
    ...     node_color={
    ...        'Demand': '#ffe34d',
    ...        'Excess': '#ffe34d',
    ...        'Gas Supply': '#336666',
    ...        'Gas Pipeline': '#336666',
    ...        'Gas Powerplant': '#336666',
    ...        'Solar': '#FF7700',
    ...        'Powerline': '#ffcc00',
    ...        'Import': '#ffd900',
    ...     },
    ...     node_size={
    ...         'Powerline': 5000,
    ...     },
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../data/images/statistical_example_msc.png
        :align: center
        :alt: Image showing the create_grid_es energy system graph.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('2019-01-01', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv_HH = pd.read_csv(os.path.join(d, 'solar_HH_2019.csv'), index_col=0,
                        sep=';')
    pv_HH = pv_HH.values.flatten()[0:periods]
    max_pv = np.max(pv_HH)

    # electricity demand:
    de_HH = pd.read_csv(os.path.join(d, 'el_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    de_HH = de_HH['Last (MW)'].values.flatten()[0:periods]
    de_HH = np.array(de_HH)
    max_de = np.max(de_HH)

    # print("pv_HH")
    # print(pv_HH)
    # Global Constraints:

    global_constraints = {
        'name': '2019',
        'emissions': float('+inf'),  # 800,
        'resources': float('+inf')}

    powerline = components.Bus(
        name='Powerline',
        region='HH',
        sector='Power',
        node_type='AC-Bus',
        component='bus',
        carrier='electricity',

        inputs=('Gas Powerplant.electricity',
                'Import.electricity',
                'Solar.electricity',),
        outputs=('Demand.electricity',
                 'Excess.electricity',),
    )

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='power',
        carrier='electricity',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_de)},
        timeseries={'electricity': nts.MinMax(min=de_HH, max=de_HH)},
    )

    excess = components.Sink(
        name='Excess',
        region='HH',
        node_type='Demand',
        component='sink',
        carrier='electricity',

        inputs=('electricity',),
    )

    solar = components.Source(
        name='Solar',
        outputs=('electricity',),
        region='HH',
        sector='Power',
        carrier='electricity',
        component='source',
        node_type='renewable',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 9},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv_HH, max=pv_HH)},
        expandable={'electricity': True},
        expansion_costs={'electricity': 5},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    gas_pipeline = components.Bus(
        name='Gas Pipeline',
        region='HH',
        sector='Power',
        node_type='GAS',
        component='bus',
        carrier='gas',

        inputs=('Gas Supply.gas',),
        outputs=('Gas Powerplant.gas',),
    )

    gas_supply = components.Source(
        name='Gas Supply',
        region='HH',
        node_type='Gas Supply',
        component='source',
        carrier='GAS',
        # flow_costs=21,
        outputs=('gas',),
    )

    gas_powerplant = components.Transformer(
        name='Gas Powerplant',
        inputs=('gas',),
        outputs=('electricity',),
        conversions={('gas', 'electricity'): 0.4075, },
        region='HH',
        node_type='Gas Powerplant',
        component='transformer',
        sector='ELECTRICITY',
        carrier='GAS',

        flow_rates={'gas': nts.MinMax(min=0, max=float('+inf')),
                    'electricity': nts.MinMax(min=0, max=400), },
        flow_costs={'gas': 10,
                    'electricity': 82, },
        flow_emissions={'gas': 0.2,
                        'electricity': 0, },

    )

    el_import = components.Source(
        name='Import',
        outputs=('electricity',),
        region='HH',
        node_type='Import',
        component='source',
        carrier='electricity',

        flow_rates={'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'electricity': 999, },
        flow_emissions={'electricity': 0.45, },
    )

    explicit_es = energy_system.AbstractEnergySystem(
        uid="statistical_example_msc",
        busses=(powerline, gas_pipeline,),
        sinks=(demand, excess),
        sources=(el_import, solar, gas_supply,),
        transformers=(gas_powerplant,),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return explicit_es
