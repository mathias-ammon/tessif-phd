import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# conversions

# one sources, one transformer, two sinks
# source1 feeds transformer with fuel and fixed flow rate
# transformer transforms fuel into heat and electricity with given conversion
# transformer outflow heat goes into sink1 and electricity to sink2
# expected behaviour: flow rate of fuel source is split due to conversion factor and flows accordingly to sink1 and sink2

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('fuel',),
            'flow_rates': {
                'fuel': nts.MinMax(min=10, max=10),  # force a flow rate of exactly 10
            },
        },
    },
    'transformers': {
        'transformerA': {
            'name': 'transformer1',
            'inputs': ['fuel', ],
            'outputs': ['heat', 'electricity', ],
            'conversions': {
                ('fuel', 'heat',): 0.5,
                ('fuel', 'electricity',): 0.5,
            },
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
            'inputs': ('transformer1.heat', 'transformer1.electricity',),
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
}  # minimum working example transformer - linear - conversions
