# examples/application/verification_scenarios/storages/phd/emissions.py
import tessif.frused.namedtuples as nts
import pandas as pd

mapping = {
    'sources': {
        'high_emiiting': {
            'name': 'Initial Charge',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=100)},
            # fixing flow rate to timeseries helps fine parsing mimimum flow
            'timeseries': {
                'electricity': nts.MinMax(
                    min=[110, 0, 0, 0, ],
                    max=[110, 0, 0, 0, ],
                ),
            },
        },
        'expensive': {
            'name': 'Expensive',
            'outputs': ('electricity',),
            # flow_rate between 0 and 10 (same as sink)
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            # costs > 0
            'flow_costs': {'electricity': 2},
        },
    },
    'transformers': {},
    'sinks': {
        'sink': {
            'name': 'Demand',
            'inputs': ('electricity',),
            # force an outflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'storages': {
        'storage': {
            'name': 'Battery',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'initial_soc': 0,
            "flow_emissions": {"electricity": 1},
        },
    },
    'busses': {
        'central_bus': {
            'name': 'Central Bus',
            'inputs': (
                'Initial Charge.electricity',
                'Expensive.electricity',
                'Battery.electricity',
            ),
            'outputs': (
                'Demand.electricity',
                'Battery.electricity',
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
            'emissions': 20,
        },
    },
}
