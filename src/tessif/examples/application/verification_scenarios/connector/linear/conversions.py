import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd


# conversions

#

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 10},                          # flow_costs set to a value > 0
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 100},                         # flow_costs set to a value > 0
        },
    },
    'connectors': {
        'connectorA': {
            'name': 'connector1',
            'interfaces': ['bus1', 'centralbus'],
            'conversions': {('bus1', 'centralbus'): 0.7,
                              ('centralbus', 'bus1'): 0.7,},
        },
        'connectorB': {
            'name': 'connector2',
            'interfaces': ['bus1', 'centralbus'],
            'conversions': {('bus1', 'centralbus'): 0.9,
                              ('centralbus', 'bus1'): 0.9,},
        },
    },
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},  # force a flow rate of exactly 10
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source1.electricity',),
            'outputs': ('sink1.electricity',),
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('source2.electricity',),
            'outputs': ('sink2.electricity',),
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=10, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': float('+inf'),
                    'material': float('+inf')},
    },
}  # minimum working example connector - linear - initial_soc
