.. _Examples_Tessif_Config_Flat:

flat
====

Flat config files can be parsed using python's default
:mod:`configparser`.

.. contents:: Contents
   :local:
   :backlinks: top


Basic Energy System
-------------------

.. note::
   Original config file data can be found in:
   ``tessif/examples/data/tsf/cfg/flat/basic``
   
Reading The Data
^^^^^^^^^^^^^^^^
Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>` logging
level to debug for decluttering doctest output:

>>> from tessif.frused import configurations
>>> configurations.spellings_logging_level = 'debug'

Reading in the data:

>>> from tessif import parse
>>> from tessif.frused.paths import example_dir
>>> import os
>>> folder = os.path.join(example_dir, 'data', 'tsf', 'cfg', 'flat', 'basic')
>>> energy_system_mapping = parse.flat_config_folder(folder)

Printing the sorted keys to check for succesfull reading:

>>> keys = list(energy_system_mapping.keys())
>>> for key in sorted(keys):
...     print(key)
bus
global_constraints
sink
source
storage
timeframe
transformer


Transforming the Read-In Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> from tessif.transform.mapping2es.tsf import transform
>>> es = transform(energy_system_mapping)
>>> for node in es.nodes:
...     print(node.uid.name)
Pipeline
Power Line
Air Chanel
Gas Station
Solar Panel
Air
Demand
Generator
Battery

Using the from_external Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
>>> from tessif.model.energy_system import AbstractEnergySystem as AES
>>> es = AES.from_external(
...     path = folder,
...     parser = parse.flat_config_folder)


from_external parsed energy systems get an automated id:

>>> print(es.uid)
es_from_external_source


Show the parsed node names:

>>> for node in es.nodes:
...     print(node.uid.name)
Pipeline
Power Line
Air Chanel
Gas Station
Solar Panel
Air
Demand
Generator
Battery

>>> for transformer in es.transformers:
...     print(transformer.flow_rates)
{'air': MinMax(min=0, max=inf), 'electricity': MinMax(min=0, max=15), 'fuel': MinMax(min=0, max=50)}

Using the Simulate Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^

   
Original Data -- Configuration File **Busses**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/busses.cfg

Original Data -- Configuration File **Sinks**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/sinks.cfg

Original Data -- Configuration File **Storages**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/storages.cfg   
   
Original Data -- Configuration File **Sources**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/sources.cfg

.. _Examples_Tsf_Cfg_Flat:

Original Data -- Configuration File **Timeframe**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/timeframe.cfg

Original Data -- Configuration File **Transformers**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/transformers.cfg

Original Data -- Configuration File **Timeframe**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/timeframe.cfg
   
Original Data -- Configuration File **Global_Constraints**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../../src/tessif/examples/data/tsf/cfg/flat/basic/global_constraints.cfg
