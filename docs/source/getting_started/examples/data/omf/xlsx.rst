.. _Examples_Omf_Xlsx:
   
xlsx
====

Engineers love spreadsheets. Yep they do.

.. contents:: Contents
   :local:
   :backlinks: top


Basic Energy System
-------------------

.. note::
   Original Spreadsheet data can be found in:
   ``tessif/examples/data/omf/xlsx/energy_system.xlsx``

Reading the Data
^^^^^^^^^^^^^^^^
Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>` logging
level to debug for decluttering doctest output:

>>> from tessif.frused import configurations
>>> configurations.spellings_logging_level = 'debug'

Reading in the data:

>>> from tessif.parse import xl_like
>>> from tessif.frused.paths import example_dir
>>> import os
>>> p = os.path.join(example_dir, 'data', 'omf', 'xlsx', 'energy_system.xls')
>>> energy_system_mapping = xl_like(p, engine='xlrd')
>>> for key in energy_system_mapping.keys():
...     print(key)
Info
Grid
Renewable
Demand
Commodity
mimo_transformers
global_constraints
timeframe


.. _Examples_Omf_Xlsx_Timeframe:

Displaying the parsed timeframe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> print(energy_system_mapping['timeframe'])
            timeindex
0 2016-01-01 00:00:00
1 2016-01-01 01:00:00
2 2016-01-01 02:00:00
3 2016-01-01 03:00:00
4 2016-01-01 04:00:00


Tansforming the Read-In Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
>>> from tessif.transform.mapping2es.omf import transform
>>> es = transform(energy_system_mapping)
>>> for node in es.nodes:
...     print(node.label.name)
Power Grid
Gas Grid
Heat Grid
Coal Grid
PV
Onshore
Offshore
Gas
Coal
Power Demand
Heat Demand
Gas_CHP
Coal_PP
Gas_HP


Using the Simulate Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^
Automatically do the steps from above utilizing the :meth:`~tessif.simulate.omf` wrapper:

>>> from tessif import simulate
>>> import functools
>>> import tessif.parse as parse
>>> es = simulate.omf(
...     path = p,
...     parser=functools.partial(
...         parse.xl_like, engine='xlrd'),
...     )
>>> print(type(es.results))
<class 'pyomo.opt.results.results_.SolverResults'>
>>> print(len(es.nodes) is len(es.results['main']))
True
