import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

mapping = {
    'sources': {
        'gas_station': {
            'name': 'Gas Station',
            'outputs': ('fuel',),
            # Minimum number of arguments required
            'latitude': 42,
            'longitude': 42,
            'region': 'Here',
            'sector': 'Power',
            'carrier': 'Fuel',
            'node_type': 'hub',
            'accumulated_amounts': {
                'fuel': nts.MinMax(min=0, max=float('+inf'))},
            'flow_rates': {'fuel': nts.MinMax(min=0, max=22)},
            'flow_costs': {'fuel': 0},
            'flow_emissions': {'fuel': 0},
            'flow_gradients': {
                'fuel': nts.PositiveNegative(positive=42, negative=42)},
            'gradient_costs': {
                'fuel': nts.PositiveNegative(positive=1, negative=1)},
            'timeseries': {
                'fuel': nts.MinMax(min=0, max=np.array([10, 22, 22]))},
            'expandable': {'fuel': False},
            'expansion_costs': {'fuel': 0},
            'expansion_limits': {'fuel': nts.MinMax(min=0, max=float('+inf'))},
            'milp': {'fuel': False},
            'initial_status': True,
            'status_inertia': nts.OnOff(on=1, off=1),
            'status_changing_costs': nts.OnOff(on=0, off=0),
            'number_of_status_changes': nts.OnOff(on=float('+inf'), off=10),
            'costs_for_being_active': 0,
            # Total number of arguments to specify source object
        },
    },
    'transformers': {
        'generator': {
            'name': 'Generator',
            'inputs': ('fuel',),
            'outputs': ('electricity',),
            'conversions': {('fuel', 'electricity'): 0.42},
            # Minimum number of arguments required
            'latitude': 42,
            'longitude': 42,
            'region': 'Here',
            'sector': 'Power',
            'carrier': 'Force',
            'node_type': 'hub',
            'flow_rates': {
                'fuel': nts.MinMax(min=0, max=50),
                'electricity': nts.MinMax(min=5, max=15)},
            'flow_costs': {'fuel': 0, 'electricity': 0},
            'flow_emissions': {'fuel': 0, 'electricity': 0},
            'flow_gradients': {
                'fuel': nts.PositiveNegative(positive=50, negative=50),
                'electricity': nts.PositiveNegative(positive=10, negative=10)},
            'gradient_costs': {
                'fuel': nts.PositiveNegative(positive=0, negative=0),
                'electricity': nts.PositiveNegative(positive=0, negative=0)},
            'timeseries': {'electricity': nts.MinMax(
                min=0, max=np.array([10, 22, 22]))},
            'expandable': {'fuel': False, 'electricity': False},
            'expansion_costs': {'fuel': 0, 'electricity': 0},
            'expansion_limits': {
                'fuel': nts.MinMax(min=0, max=float('+inf')),
                'electricity': nts.MinMax(min=0, max=float('+inf'))},
            'milp': {'electricity': True, 'fuel': False},
            'initial_status': True,
            'status_inertia': nts.OnOff(on=0, off=2),
            'status_changing_costs': nts.OnOff(on=0, off=0),
            'number_of_status_changes': nts.OnOff(on=float('+inf'), off=9),
            'costs_for_being_active': 0,
            # Total number of arguments to specify transformer object
        },
    },
    'sinks': {
        'demand': {
            'name': 'Demand',
            'inputs': ('electricity',),
            # Minimum number of arguments required
            'latitude': 42,
            'longitude': 42,
            'region': 'Here',
            'sector': 'Power',
            'carrier': 'Force',
            'node_type': 'hub',
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=0, max=float('+inf'))},
            'flow_rates': {'electricity': nts.MinMax(min=8, max=11)},
            'flow_costs': {'electricity': 0},
            'flow_emissions': {'electricity': 0},
            'flow_gradients': {
                'electricity': nts.PositiveNegative(positive=11, negative=11)},
            'gradient_costs': {
                'electricity': nts.PositiveNegative(positive=0, negative=0)},
            'timeseries': None,
            'expandable': {'electricity': False},
            'expansion_costs': {'electricity': 0},
            'expansion_limits': {
                'electricity': nts.MinMax(min=0, max=float('+inf'))},
            'milp': {'electricity': False},
            'initial_status': True,
            'status_inertia': nts.OnOff(on=2, off=1),
            'status_changing_costs': nts.OnOff(on=0, off=0),
            'number_of_status_changes': nts.OnOff(on=float('+inf'), off=8),
            'costs_for_being_active': 0,
            # Total number of arguments to specify sink object
        },
    },
    'storages': {
        'battery': {
            'name': 'Battery',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'initial_soc': 10,
            # Minimum number of arguments required
            'latitude': 42,
            'longitude': 42,
            'region': 'Here',
            'sector': 'Power',
            'carrier': 'Force',
            'node_type': 'hub',
            'idle_changes': nts.PositiveNegative(positive=0, negative=1),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            'flow_efficiencies': {
                'electricity': nts.InOut(inflow=0.95, outflow=0.98)},
            'flow_costs': {'electricity': 0},
            'flow_emissions': {'electricity': 0},
            'flow_gradients': {
                'electricity': nts.PositiveNegative(positive=10, negative=10)},
            'gradient_costs': {
                'electricity': nts.PositiveNegative(positive=0, negative=0)},
            'timeseries': None,
            'expandable': {'electricity': False},
            'expansion_costs': {'electricity': 0},
            'expansion_limits': {
                'electricity': nts.MinMax(min=0, max=float('+inf'))},
            'milp': {'electricity': False},
            'initial_status': True,
            'status_inertia': nts.OnOff(on=0, off=2),
            'status_changing_costs': nts.OnOff(on=0, off=0),
            'number_of_status_changes': nts.OnOff(on=float('+inf'), off=42),
            'costs_for_being_active': 0,
            # Total number of arguments to specify storage object
        },
    },
    'busses': {
        'fuel_supply_line': {
            'name': 'Pipeline',
            'inputs': ('Gas Station.fuel',),
            'outputs': ('Generator.fuel',),
            # Minimum number of arguments required
            'latitude': 42,
            'longitude': 42,
            'region': 'Here',
            'sector': 'Power',
            'carrier': 'fuel',
            'node_type': 'fuel_line',
            # Total number of arguments to specify bus object
        },
        'power_line': {
            'name': 'Power Line',
            'inputs': ('Generator.electricity', 'Battery.electricity'),
            'outputs': ('Demand.electricity', 'Battery.electricity'),
            # Minimum number of arguments required
            'latitude': 42,
            'longitude': 42,
            'region': 'Here',
            'sector': 'Power',
            'carrier': 'Force',
            'node_type': 'hub',
            # Total number of arguments to specify bus object
        },
    },
    'timeframe': {
        'primary': pd.date_range('7/13/1990', periods=3, freq='H'),
        'secondary': pd.date_range('10/03/2019', periods=3, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': float('+inf'),
                    'resources': float('+inf')},
        'secondary': {'name': '80% reduction',
                      'emissions': 1000,
                      'resources': float('+inf')},
    },
}
