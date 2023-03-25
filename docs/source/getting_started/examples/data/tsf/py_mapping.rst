.. _py_mapping:

py_mapping
==========

.. contents:: Contents
   :local:
   :backlinks: top


Fully Parameteized Working Example
----------------------------------

.. note::
   Original code file can be found in:
   ``tessif/examples/data/tsf/py_mapping/fpwe.py``


Reading the Data
^^^^^^^^^^^^^^^^
Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>` logging
level to debug for decluttering doctest output:

>>> from tessif.frused import configurations
>>> configurations.spellings_logging_level = 'debug'

Reading in the data:

>>> from tessif.parse import python_mapping
>>> from tessif.examples.data.tsf.py_mapping import fpwe
>>> energy_system_mapping = python_mapping(fpwe.mapping)
>>> for key in energy_system_mapping.keys():
...    print(key)
sources
transformers
sinks
storages
busses
timeframe
global_constraints


Transforming the Read-In Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> from tessif.transform.mapping2es.tsf import transform
>>> es = transform(energy_system_mapping)
>>> for node in es.nodes:
...     print(node.uid.name)
Pipeline
Power Line
Gas Station
Demand
Generator
Battery



Using the Simulate Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^
Automatically do the steps from above utilizing the
:meth:`tessif.simulate.tsf_from_es` wrapper:

.. warning::
   Not yet implemented!


.. _Examples_Tsf_PyMapping_Data:

Original Data -- The Complete Mapping
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude::
   ../../../../../../src/tessif/examples/data/tsf/py_mapping/fpwe.py

  
Transhipment Problem Example
----------------------------
.. note::
   Original code file can be found in:
   ``tessif/examples/data/tsf/py_mapping/fpwe.py``
   
   A similar example can be found in
   :attr:`tessif.examples.data.tsf.py_hard.create_connected_es`


Reading the Data
^^^^^^^^^^^^^^^^
Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>` logging
level to debug for decluttering doctest output:

>>> from tessif.frused import configurations
>>> configurations.spellings_logging_level = 'debug'

Reading in the data:

>>> from tessif.parse import python_mapping
>>> from tessif.examples.data.tsf.py_mapping import transshipment
>>> energy_system_mapping = python_mapping(transshipment.mapping)
>>> for key in energy_system_mapping.keys():
...    print(key)
sources
transformers
sinks
storages
busses
connectors
timeframe
global_constraints



Transforming the Read-In Data into a Tessif Energy System
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> from tessif.transform.mapping2es.tsf import transform
>>> es = transform(energy_system_mapping)
>>> for node in es.nodes:
...     print(node.uid.name)
bus-01
bus-02
source-01
source-02
sink-01
sink-02
connector

Transforming the Tessif Energy System into an Oemof Energy System
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
>>> import tessif.transform.es2es.omf as tsf2omf
>>> omf_es = tsf2omf.transform(es)
>>> for node in omf_es.nodes:
...     print(str(node.label))
bus-01
bus-02
connector
source-01
source-02
sink-01
sink-02

Simulating and Post Processing the Oemof Energy System
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Handle the imports first:

    >>> import tessif.simulate
    >>> import tessif.transform.es2mapping.omf as post_process_omf
    >>> optimized_omf_es = tessif.simulate.omf_from_es(omf_es)

Postprocess the results:

    >>> load_results = post_process_omf.LoadResultier(optimized_omf_es)

Show some results:

    >>> print(load_results.node_load['connector'])
    connector              bus-01  bus-02  bus-01  bus-02
    1990-07-13 00:00:00 -5.555556   -0.00     0.0     5.0
    1990-07-13 01:00:00 -0.000000   -6.25     5.0     0.0
    1990-07-13 02:00:00 -0.000000   -0.00     0.0     0.0

    >>> print(load_results.node_load['bus-01'])
    bus-01               connector  source-01  connector  sink-01
    1990-07-13 00:00:00       -0.0  -5.555556   5.555556      0.0
    1990-07-13 01:00:00       -5.0 -10.000000   0.000000     15.0
    1990-07-13 02:00:00       -0.0 -10.000000   0.000000     10.0

    >>> print(load_results.node_load['bus-02'])
    bus-02               connector  source-02  connector  sink-02
    1990-07-13 00:00:00       -5.0     -10.00       0.00     15.0
    1990-07-13 01:00:00       -0.0      -6.25       6.25      0.0
    1990-07-13 02:00:00       -0.0     -10.00       0.00     10.0

.. _Examples_Tsf_PyMapping_Transshipment_Data:

Original Data -- The Complete Mapping
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude::
   ../../../../../../src/tessif/examples/data/tsf/py_mapping/transshipment.py
