# examples/application/verification_scenarios/chp/phd/emissions.py
import tessif.frused.namedtuples as nts
import pandas as pd

mapping = {
    'sources': {
        'expensive_power': {
            'name': 'Expensive Power',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            'flow_costs': {'electricity': 2},
        },
        'expensive_heat': {
            'name': 'Expensive Heat',
            'outputs': ('hot_water',),
            'flow_rates': {'hot_water': nts.MinMax(min=0, max=10)},
            'flow_costs': {'hot_water': 2},
        },
        'commodity': {
            'name': 'Gas Commodity',
            'outputs': ('gas',),
            # flow_rate between 0 and 10 (same as sink)
        },
    },
    'transformers': {
        'combined_heat_and_power': {
            'name': 'CHP',
            'inputs': ('gas',),
            'outputs': ("electricity", 'hot_water',),
            "conversions": {
                ('gas', 'electricity'): 0.5,
                ('gas', 'hot_water'): 0.4,
            },
            'flow_rates': {
                "gas": nts.MinMax(min=0, max=float("+inf")),
                'electricity': nts.MinMax(min=0, max=10),
                'hot_water': nts.MinMax(min=0, max=8),
            },
            "flow_costs": {'electricity': 1, 'hot_water': 1, 'gas': 0},
            "flow_emissions": {'electricity': 1, 'hot_water': 1, 'gas': 0},
        },

    },
    'sinks': {
        'power_demand': {
            'name': 'Power Demand',
            'inputs': ('electricity',),
            # force an inflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
        'heat_demand': {
            'name': 'Heat Demand',
            'inputs': ('hot_water',),
            # force an inflow of exactly 10
            'flow_rates': {'hot_water': nts.MinMax(min=10, max=10)},
        },
    },
    'storages': {},
    'busses': {
        'central_power_bus': {
            'name': 'Power Bus',
            'inputs': (
                'CHP.electricity',
                'Expensive Power.electricity',
            ),
            'outputs': (
                'Power Demand.electricity',
            ),
            'component': 'bus',
        },
        'central_heat_bus': {
            'name': 'Heat Bus',
            'inputs': (
                'CHP.hot_water',
                'Expensive Heat.hot_water',
            ),
            'outputs': (
                'Heat Demand.hot_water',
            ),
            'component': 'bus',
        },
        'gas_pipeline': {
            'name': 'Gas Pipeline',
            'inputs': (
                'Gas Commodity.gas',
            ),
            'outputs': (
                'CHP.gas',
            ),
            'component': 'bus',
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=4, freq='H'),
    },
    'global_constraints': {
        'primary': {
            'name': 'default',
            'emissions': 54,
        },
    },
}
