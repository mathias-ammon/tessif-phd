Fully Parameterized Working Example
***********************************

.. note::
   In contrast to the mwe, the fpwe differs (among other things) by utilizing a
   fixed timeseries to model a solar panels output
   
>>> # Import hardcoded tessif energy system using the example hub:
>>> import tessif.examples.data.tsf.py_hard as tsf_examples

>>> # Create the tessif energy system:
>>> tsf_es = tsf_examples.create_fpwe()

>>> # Print the nodes inside this energy system:
>>> for node_uid in sorted([n.uid for n in tsf_es.nodes]):
...     print(node_uid)
Battery
Demand
Gas Station
Generator
Pipeline
Powerline
Solar Panel

>>> # Import the model transformation utilities:
>>> from tessif.transform.es2es import (
...     ppsa as tsf2pypsa,
...     omf as tsf2omf,
... )

>>> # transform the tessif energy system into oemof and pypsa:
>>> oemof_es = tsf2omf.transform(tsf_es)
>>> pypsa_es = tsf2pypsa.transform(tsf_es)

>>> # Import the simulation utility:
>>> import tessif.simulate

>>> # Optimize the energy systems:
>>> optimized_oemof_es = tessif.simulate.omf_from_es(oemof_es)
>>> optimized_pypsa_es = tessif.simulate.ppsa_from_es(pypsa_es)

>>> # Import the post processing utilities:
>>> from tessif.transform.es2mapping import (
...     ppsa as post_process_pypsa,
...     omf as post_process_oemof,
... )

>>> # Conduct the post processing:
>>> oemof_load_results = post_process_oemof.LoadResultier(optimized_oemof_es)
>>> pypsa_load_results = post_process_pypsa.LoadResultier(optimized_pypsa_es)

>>> # Show some results:
>>> print(oemof_load_results.node_load['Powerline'])
Powerline            Battery  Generator  Solar Panel  Battery  Demand
1990-07-13 00:00:00     -0.0       -0.0        -12.0      1.0    11.0
1990-07-13 01:00:00     -8.0       -0.0         -3.0      0.0    11.0
1990-07-13 02:00:00     -0.9       -3.1         -7.0      0.0    11.0

>>> print(pypsa_load_results.node_load['Powerline'])
Powerline            Battery  Generator  Solar Panel  Battery  Demand
1990-07-13 00:00:00     -0.0       -0.0        -12.0      1.0    11.0
1990-07-13 01:00:00     -8.0       -0.0         -3.0      0.0    11.0
1990-07-13 02:00:00     -0.9       -3.1         -7.0      0.0    11.0
