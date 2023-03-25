import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_emissions

# source, sink, storage
# sink demands a consistent inflow of 10
# source high flow_costs and no flow_emissions
# storage no flow_costs, enough load (initial soc) for feeding sink whole timeseries but high flow_emissions
# expected behaviour: storage will feed sink with a flow_rate 10 until global emission cap (50) is reached

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 10},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},          # force an inflow of exactly 10
        },
    },
    'storages': {
        'storageA': {
            'name': 'storage1',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'initial_soc': 100,
            'flow_emissions': {'electricity': 1},
        },
    },
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'storage1.electricity'),
            'outputs': ('sink1.electricity', 'storage1.electricity',),
            'component': 'bus',
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=10, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': 50,
                    'material': float('+inf')},
    },
}  # minimum working example storage - linear - flow_emissions
