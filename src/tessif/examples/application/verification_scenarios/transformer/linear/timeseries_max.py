import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# timeseries

# two sources, one transformer, two sinks
# source1 feed transformer with fuel
# transformer transforms fuel into heat and electricity with a forced (in)flow rate of fuel given through timeseries
# transformer outflow heat goes into sink1 and electricity to sink2 with forced flow_rate of electricity (due to conversion)
# source2 feeds sinks directly with high flow_costs
# expected behaviour: transormer feeds sinks electricity demand until limited fuel flow_rate is reached, remaining demand will be given from source2

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('fuel',),
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('heat', 'electricity',),
            'flow_costs': {
                'heat': 100,
                'electricity': 100,
            },
        },
    },
    'transformers': {
        'transformerA': {
            'name' : 'transformer1',
            'inputs': ['fuel',],
            'outputs': ['heat', 'electricity',],
            'conversions': {
                ('fuel', 'heat'): 0.5,
                ('fuel', 'electricity'): 0.5,
            },
            'timeseries': {
                'fuel': nts.MinMax( min=[20, 18, 16, 14, 12, 10, 8, 6, 4, 2, ],
                                    max=[20, 18, 16, 14, 12, 10, 8, 6, 4, 2, ]),
                'heat': nts.MinMax(min=0, max=[20, 18, 16, 14, 12, 10, 8, 6, 4, 2, ]),
                'electricity': nts.MinMax(min=0, max=[20, 18, 16, 14, 12, 10, 8, 6, 4, 2, ]),
            }
        }
    },
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('heat',),
            },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_rates': {
                'electricity': nts.MinMax(min=10, max=10),                          # force a flow rate of exactly 10
            },
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source1.fuel',),
            'outputs': ('transformer1.fuel',),
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('transformer1.heat', 'transformer1.electricity', 'source2.heat', 'source2.electricity',),
            'outputs': ('sink1.heat', 'sink2.electricity',),
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
}  # minimum working example transformer - linear - timeseries
