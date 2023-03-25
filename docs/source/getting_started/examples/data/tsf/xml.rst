.. _Examples_Tessif_Xml:

xml
===

XML files can be parsed using python's :mod:`xml.etree.ElementTree` library.

.. contents:: Contents
   :local:
   :backlinks: top


Basic Energy System
-------------------

.. note::
   Original xml data can be found in:
   ``tessif/examples/data/tsf/xml/``

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
>>> path = os.path.join(example_dir, 'data', 'tsf', 'xml', 'fpwe.xml')
>>> energy_system_mapping = parse.xml(path)
>>> for key in energy_system_mapping.keys():
...     print(key)
bus
sink
storage
source
transformer
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
...     path = path,
...     parser = parse.xml)


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

Original Data -- Xml File **fpwe.xml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/tsf/xml/fpwe.xml
   :language: xml
