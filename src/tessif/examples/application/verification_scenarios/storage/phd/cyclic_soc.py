import tessif.frused.namedtuples as nts
import pandas as pd


mapping = {
    'sources': {
        'over_producing': {
            'name': 'Over Producing',
            'outputs': ('electricity',),
            # flow rates fixed to 11, helps pypsa parsing installed capacity
            'flow_rates': {'electricity': nts.MinMax(min=11, max=11)},
            # fixing flow rate to timeseries helps fine parsing mimimum flow
            'timeseries': {
                'electricity': nts.MinMax(
                    min=[11, 11, 11, 11, ],
                    max=[11, 11, 11, 11, ],
                ),
            },
            # costs > 0
            'flow_costs': {'electricity': 1},
        },
        'expensive': {
            'name': 'Unused Expensive',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=11)},
            # costs > over_producing
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
        },
    },
    'busses': {
        'central_bus': {
            'name': 'Central Bus',
            'inputs': (
                'Over Producing.electricity',
                'Unused Expensive.electricity',
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
        'primary': {'name': 'default',
                    'emissions': float('+inf'),
                    'material': float('+inf')},
    },
}
