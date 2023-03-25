.. _Examples_Tessif_hdf5:

hdf5
====

HDF5 files can be parsed using the :doc:`h5py <h5py:index>` package.

.. contents:: Contents
   :local:
   :backlinks: top


Basic Energy System
-------------------

.. note::
   Original hdf5 data can be found in:
   ``tessif/examples/data/tsf/hdf5/``

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
>>> path = os.path.join(example_dir, 'data', 'tsf', 'hdf5', 'fpwe.hdf5')
>>> energy_system_mapping = parse.hdf5(path)
>>> for key in energy_system_mapping.keys():
...     print(key)
busses
global_constraints
sinks
sources
storages
timeframe
transformers

Transforming the Read-In Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> from tessif.transform.mapping2es.tsf import transform
>>> es = transform(energy_system_mapping)
>>> for node in es.nodes:
...     print(node.uid.name)
Pipeline
Powerline
Gas Station
Solar Panel
Demand
Generator
Battery

Using the from_external Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
>>> from tessif.model.energy_system import AbstractEnergySystem as AES
>>> es = AES.from_external(
...     path = path,
...     parser = parse.hdf5)


from_external parsed energy systems get an automated id:

>>> print(es.uid)
es_from_external_source


Show the parsed node names:

>>> for node in es.nodes:
...     print(node.uid.name)
Pipeline
Powerline
Gas Station
Solar Panel
Demand
Generator
Battery

>>> for transformer in es.transformers:
...     print(transformer.flow_rates)
{'electricity': MinMax(min=0, max=15), 'fuel': MinMax(min=0, max=50)}

Using the Simulate Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^
