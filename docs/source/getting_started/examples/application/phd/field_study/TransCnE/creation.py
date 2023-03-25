import os

import numpy as np
import pandas as pd

import tessif.frused.namedtuples as nts
from tessif.frused.paths import example_dir
from tessif.model import components, energy_system


def create_transcne_es(
        periods=24,
        transformer_efficiency=0.93,
        gridcapacity=60000,
        expansion=False
):
    """Create the TransCnE system model scenarios combinations.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    gridcapacity : int, default=60000
        Transmission capacity of the transformers of the gridstructure
        (at 0 the parts of the grid are not connected)

    expansion: bool, default=False
        If ``True`` :ref:`gridcapacity` is subject to expansion.

    Note
    ----
    Changes compared to `Hanke Project Thesis
    <https://tore.tuhh.de/handle/11420/11759>`_:

        1. Rename ``"Power Source [Voltage]"`` to
           ``"Deficit Source [Voltage]"``
        2. Rename ``"Power Sinks [Voltage]"`` to ``"Excess Sinks [Voltage]"``
        3. Rename ``"[High/Mid/Low] Voltage Powerline"`` to ``"[High/Mid/Low]
           Voltage Grid"``
        4. Rename ``"[Voltage to Voltage] Transformator"`` to
           ``"[Voltage to Voltage] Transfer"``
        5. Change :ref:`gridcapacity` to reference the maximum outflow.
        6. :ref:`expansion` capabilities are added to allow :ref:`gridcapacity`
           to be expanded
        7. Default :ref:`transformer_efficiency` is decreased to ``0.93`` to
           discourage energy circulation between to grid busses to dissipate
           surplus amounts.
        8. Outflow costs of 10 cost units per power unit are added to all
           ``Transfer`` components, to further discourage energy circulation
           between to grid busses to dissipate surplus amounts and to encourage
           local production and consumption.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
    }

    # -------------Low Voltage and heat ------------------

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='Renewable',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'low-voltage-electricity': 60.85},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('low-voltage-electricity', 'heat'),
        conversions={
            ('fuel', 'low-voltage-electricity'): 0.33,
            ('fuel', 'heat'): 0.52,
        },
        # Minimum number of arguments required',
        sector='Coupled',
        carrier='low-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'low-voltage-electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697),
        },
        flow_costs={'fuel': 0, 'low-voltage-electricity': 124.4, 'heat': 31.1},
        flow_emissions={
            'fuel': 0,
            'low-voltage-electricity': 0.1573,
            'heat': 0.0732,
        },
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        sector='Power',
        carrier='gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='gas',
        node_type='bus',
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Grid',
        inputs=(
            'BHKW.low-voltage-electricity',
            'Deficit Source LV.low-voltage-electricity',
            'Solar Panel.low-voltage-electricity',
            'Medium Low Transfer.low-voltage-electricity',
        ),
        outputs=(
            'Household Demand.low-voltage-electricity',
            'Commercial Demand.low-voltage-electricity',
            'Low Medium Transfer.low-voltage-electricity',
            'Excess Sink LV.low-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=(
            'BHKW.heat',
            'Solar Thermal.heat',
            'Power to Heat.heat',
            'HKW.heat',
        ),
        outputs=('District Heating Demand.heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
    )

    # ----- -------Medium Voltage and Heat ------------------

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='power',
        carrier='medium-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'medium-voltage-electricity': 61.1},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('medium-voltage-electricity',),
        outputs=('heat',),
        conversions={('medium-voltage-electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 0, 'heat': 0},
        flow_emissions={'medium-voltage-electricity': 0, 'heat': 0},
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Grid',
        inputs=(
            'Onshore Wind Power.medium-voltage-electricity',
            'High Medium Transfer.medium-voltage-electricity',
            'Low Medium Transfer.medium-voltage-electricity',
            'Deficit Source MV.medium-voltage-electricity',
        ),
        outputs=(
            'Car charging Station.medium-voltage-electricity',
            'Industrial Demand.medium-voltage-electricity',
            'Power to Heat.medium-voltage-electricity',
            'Medium High Transfer.medium-voltage-electricity',
            'Medium Low Transfer.medium-voltage-electricity',
            'Excess Sink MV.medium-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    # ----------------- High Voltage -------------------------

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='high-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'high-voltage-electricity': 106.4},
        flow_emissions={'high-voltage-electricity': 0},
        timeseries={
            'high-voltage-electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('high-voltage-electricity', 'heat'),
        conversions={
            ('fuel', 'high-voltage-electricity'): 0.24,
            ('fuel', 'heat'): 0.6,
        },
        # Minimum number of arguments required
        sector='Coupled',
        carrier='high-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96),
        },
        flow_costs={
            'fuel': 0,
            'high-voltage-electricity': 80.65,
            'heat': 20.1625,
        },
        flow_emissions={
            'fuel': 0,
            'high-voltage-electricity': 0.5136,
            'heat': 0.293,
        },
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.43},
        # Minimum number of arguments required
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=43913),
        },
        flow_costs={'fuel': 0, 'high-voltage-electricity': 80.65},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.5136},
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.59},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='generator',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'high-voltage-electricity': nts.MinMax(min=0, max=26742),
        },
        flow_costs={'fuel': 0, 'high-voltage-electricity': 88.7},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.3366},
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
    )

    high_electricity_line = components.Bus(
        name='High Voltage Grid',
        inputs=(
            'Offshore Wind Power.high-voltage-electricity',
            'HKW2.high-voltage-electricity',
            'GuD.high-voltage-electricity', 'HKW.high-voltage-electricity',
            'Medium High Transfer.high-voltage-electricity',
            'Deficit Source HV.high-voltage-electricity',
        ),
        outputs=(
            'Pumped Storage.high-voltage-electricity',
            'High Medium Transfer.high-voltage-electricity',
            'Excess Sink HV.high-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    # Gridstructure and Transformer

    low_medium_transformator = components.Transformer(
        name='Low Medium Transfer',
        inputs=('low-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('low-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        flow_emissions={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 0},
        expandable={
            'low-voltage-electricity': False,
            'medium-voltage-electricity': expansion,
        },
        expansion_costs={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        expansion_limits={
            'low-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    medium_low_transformator = components.Transformer(
        name='Medium Low Transfer',
        inputs=('medium-voltage-electricity',),
        outputs=('low-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'low-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'low-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),

        },
        flow_costs={
            'medium-voltage-electricity': 0,
            'low-voltage-electricity': 10,
        },
        flow_emissions={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 0,
        },
        expandable={
            'medium-voltage-electricity': False,
            'low-voltage-electricity': expansion,
        },
        expansion_costs={
            'medium-voltage-electricity': 0,
            'low-voltage-electricity': 10,
        },
        expansion_limits={
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'low-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    medium_high_transformator = components.Transformer(
        name='Medium High Transfer',
        inputs=('medium-voltage-electricity',),
        outputs=('high-voltage-electricity',),
        conversions={
            ('medium-voltage-electricity',
             'high-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'high-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 10,
        },
        flow_emissions={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 0,
        },
        expandable={
            'medium-voltage-electricity': False,
            'high-voltage-electricity': expansion,
        },
        expansion_costs={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 10,
        },
        expansion_limits={
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'high-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    high_medium_transformator = components.Transformer(
        name='High Medium Transfer',
        inputs=('high-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={
            ('high-voltage-electricity',
             'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        flow_emissions={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 0,
        },
        expandable={
            'high-voltage-electricity': False,
            'medium-voltage-electricity': expansion,
        },
        expansion_costs={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        expansion_limits={
            'high-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    # ---------- Deficit Sources ---------------

    power_source_lv = components.Source(
        name='Deficit Source LV',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
    )

    power_source_mv = components.Source(
        name='Deficit Source MV',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
        },
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
    )

    power_source_hv = components.Source(
        name='Deficit Source HV',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
    )

    power_sink_lv = components.Sink(
        name='Excess Sink LV',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
    )

    # ------------------- Excess Sinks --------------------------
    power_sink_mv = components.Sink(
        name='Excess Sink MV',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
        },
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
    )

    power_sink_hv = components.Sink(
        name='Excess Sink HV',
        inputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
    )

    # 4. Create the actual energy system:
    if expansion:
        uid = "TransE"
    else:
        uid = "TransC"

    es = energy_system.AbstractEnergySystem(
        uid=uid,
        busses=(
            gas_supply_line,
            low_electricity_line,
            heat_line,
            medium_electricity_line,
            high_electricity_line,
            coal_supply_line,
            biogas_supply_line,
        ),
        sinks=(
            household_demand,
            commercial_demand,
            heat_demand,
            industrial_demand,
            car_charging_station_demand,
            power_sink_lv,
            power_sink_mv,
            power_sink_hv,
        ),
        sources=(
            solar_panel,
            offshore_wind_power,
            onshore_wind_power,
            gas_supply,
            coal_supply,
            solar_thermal,
            biogas_supply,
            power_source_lv,
            power_source_mv,
            power_source_hv,
        ),
        transformers=(
            bhkw_generator,
            power_to_heat,
            gud_generator,
            hkw_generator,
            high_medium_transformator,
            low_medium_transformator,
            medium_low_transformator,
            medium_high_transformator,
            hkw_generator_2,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return es
