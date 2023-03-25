Time Varying Efficiency Transformer
***********************************

Occasionally it can be useful to model a transformer with time varying
efficiency, i.e. a singular efficiency value for each timestep. Common
application is modelling a heat pump with ambient temperature dependent
efficiency values. In this case a function would be developed to map the
ambient temperature to a machine specific efficiency value prior to
optimizatinón. A time varying temperature profile input would lead to a
respective timeseries of efficiency numbers which in turn would then be
used to parameterize the transformer.

The
:attr:`~tessif.examples.data.tsf.py_hard.create_time_varying_efficiency_transformer`
can be used to try out this time varying efficiency transformers. Following
results show case its usage.

.. contents:: Contents
   :local:
   :backlinks: top


Tessif Energy System
====================
>>> from tessif.examples.data.tsf.py_hard import create_time_varying_efficiency_transformer
>>> tsf_es = create_time_varying_efficiency_transformer()
>>> for transformer in tsf_es.transformers:
...     print(transformer.conversions)
{('energy', 'electricity'): [0.6, 0.8, 0.4]}


Software Specific Transformations
=================================

Note the pypsa particularities

>>> import tessif.transform.es2es.omf as tsf2omf  # nopep8
>>> import tessif.transform.es2es.ppsa as tsf2pypsa  # nopep8
>>> import tessif.transform.es2es.fine as tsf2fine  # nopep8
>>> import tessif.transform.es2es.cllp as tsf2cllp  # nopep8

>>> omf_es = tsf2omf.transform(tsf_es)
>>> pypsa_es = tsf2pypsa.transform(tsf_es, forced_links=("Transformer",))
>>> fine_es = tsf2fine.transform(tsf_es)
>>> cllp_es = tsf2cllp.transform(tsf_es)


Software Specific Optimizatinos
===============================
>>> import tessif.simulate as optimize  # nopep8
>>> optimized_omf_es = optimize.omf_from_es(omf_es)
>>> optimized_pypsa_es = optimize.ppsa_from_es(pypsa_es)
>>> optimized_fine_es = optimize.fine_from_es(fine_es)
>>> optimized_cllp_es = optimize.cllp_from_es(cllp_es)


Post-Processing Using Tessif
----------------------------
>>> import tessif.transform.es2mapping.omf as post_process_omf  # nopep8
>>> import tessif.transform.es2mapping.ppsa as post_process_pypsa  # nopep8
>>> import tessif.transform.es2mapping.fine as post_process_fine  # nopep8
>>> import tessif.transform.es2mapping.cllp as post_process_cllp  # nopep8

>>> omf_all_res = post_process_omf.AllResultier(optimized_omf_es)
>>> pypsa_all_res = post_process_pypsa.AllResultier(optimized_pypsa_es)
>>> fine_all_res = post_process_fine.AllResultier(optimized_fine_es)
>>> cllp_all_res = post_process_cllp.AllResultier(optimized_cllp_es)


Results Insepction
==================

Loads
-----

>>> print(omf_all_res.node_load["Transformer"])
Transformer            Com Bus  Powerline
1990-07-13 00:00:00 -16.666667       10.0
1990-07-13 01:00:00 -12.500000       10.0
1990-07-13 02:00:00 -25.000000       10.0

>>> print(pypsa_all_res.node_load["Transformer"])
Transformer            Com Bus  Powerline
1990-07-13 00:00:00 -16.666667       10.0
1990-07-13 01:00:00 -12.500000       10.0
1990-07-13 02:00:00 -25.000000       10.0

>>> print(fine_all_res.node_load["Transformer"])
Transformer            Com Bus  Powerline
1990-07-13 00:00:00 -16.666667       10.0
1990-07-13 01:00:00 -12.500000       10.0
1990-07-13 02:00:00 -25.000000       10.0

>>> print(cllp_all_res.node_load["Transformer"])
Transformer            Com Bus  Powerline
1990-07-13 00:00:00 -16.666667       10.0
1990-07-13 01:00:00 -12.500000       10.0
1990-07-13 02:00:00 -25.000000       10.0

Inflows
-------

>>> print(omf_all_res.node_inflows["Transformer"])
Transformer            Com Bus
1990-07-13 00:00:00  16.666667
1990-07-13 01:00:00  12.500000
1990-07-13 02:00:00  25.000000

>>> print(pypsa_all_res.node_inflows["Transformer"])
Transformer            Com Bus
1990-07-13 00:00:00  16.666667
1990-07-13 01:00:00  12.500000
1990-07-13 02:00:00  25.000000

>>> print(fine_all_res.node_inflows["Transformer"])
Transformer            Com Bus
1990-07-13 00:00:00  16.666667
1990-07-13 01:00:00  12.500000
1990-07-13 02:00:00  25.000000

>>> print(cllp_all_res.node_inflows["Transformer"])
Transformer            Com Bus
1990-07-13 00:00:00  16.666667
1990-07-13 01:00:00  12.500000
1990-07-13 02:00:00  25.000000


Outflows
--------

>>> print(omf_all_res.node_outflows["Transformer"])
Transformer          Powerline
1990-07-13 00:00:00       10.0
1990-07-13 01:00:00       10.0
1990-07-13 02:00:00       10.0

>>> print(pypsa_all_res.node_outflows["Transformer"])
Transformer          Powerline
1990-07-13 00:00:00       10.0
1990-07-13 01:00:00       10.0
1990-07-13 02:00:00       10.0

>>> print(fine_all_res.node_outflows["Transformer"])
Transformer          Powerline
1990-07-13 00:00:00       10.0
1990-07-13 01:00:00       10.0
1990-07-13 02:00:00       10.0

>>> print(cllp_all_res.node_outflows["Transformer"])
Transformer          Powerline
1990-07-13 00:00:00       10.0
1990-07-13 01:00:00       10.0
1990-07-13 02:00:00       10.0

Summed_Loads
------------

>>> print(omf_all_res.node_summed_loads["Transformer"])
1990-07-13 00:00:00    10.0
1990-07-13 01:00:00    10.0
1990-07-13 02:00:00    10.0
Freq: H, dtype: float64

>>> print(pypsa_all_res.node_summed_loads["Transformer"])
1990-07-13 00:00:00    10.0
1990-07-13 01:00:00    10.0
1990-07-13 02:00:00    10.0
Freq: H, dtype: float64

>>> print(fine_all_res.node_summed_loads["Transformer"])
1990-07-13 00:00:00    10.0
1990-07-13 01:00:00    10.0
1990-07-13 02:00:00    10.0
Freq: H, dtype: float64

>>> print(cllp_all_res.node_summed_loads["Transformer"])
1990-07-13 00:00:00    10.0
1990-07-13 01:00:00    10.0
1990-07-13 02:00:00    10.0
dtype: float64


Installed Capacities
--------------------

>>> print(omf_all_res.node_installed_capacity["Transformer"])
10.0

>>> print(pypsa_all_res.node_installed_capacity["Transformer"])
10.0

>>> print(fine_all_res.node_installed_capacity["Transformer"])
10

>>> print(cllp_all_res.node_installed_capacity["Transformer"])
10.0


Original Capacities
-------------------

>>> print(omf_all_res.node_original_capacity["Transformer"])
0

>>> print(pypsa_all_res.node_original_capacity["Transformer"])
0.0

>>> print(fine_all_res.node_original_capacity["Transformer"])
0.0

>>> print(cllp_all_res.node_original_capacity["Transformer"])
0.0

Reference Capacities
--------------------

Highest Installed Capacity:

>>> print(omf_all_res.node_reference_capacity)
25.0

>>> print(pypsa_all_res.node_reference_capacity)
25.0

>>> print(fine_all_res.node_reference_capacity)
25.0

>>> print(cllp_all_res.node_reference_capacity)
25.0


Characteristic Values
---------------------

>>> print(omf_all_res.node_characteristic_value["Transformer"])
1.0

>>> print(round(pypsa_all_res.node_characteristic_value["Transformer"], 1))
1.0

>>> print(fine_all_res.node_characteristic_value["Transformer"])
1.0

>>> print(cllp_all_res.node_characteristic_value["Transformer"])
1.0

Net Energy Flows
----------------

Note that the tessif -> fine implementation has some issues here

>>> print(omf_all_res.edge_net_energy_flow[("Transformer", "Powerline")])
30.0

>>> print(pypsa_all_res.edge_net_energy_flow[("Transformer", "Powerline")])
30.0

>>> print(fine_all_res.edge_net_energy_flow[("Transformer", "Powerline")])
0.0

>>> print(cllp_all_res.edge_net_energy_flow[("Transformer", "Powerline")])
30.0


Costs
-----

>>> print(omf_all_res.edge_specific_flow_costs[("Transformer", "Powerline")])
100

>>> print(pypsa_all_res.edge_specific_flow_costs[("Transformer", "Powerline")])
100.0

>>> print(fine_all_res.edge_specific_flow_costs[("Transformer", "Powerline")])
100.0

>>> print(cllp_all_res.edge_specific_flow_costs[("Transformer", "Powerline")])
100.0

Emissions
---------

>>> print(omf_all_res.edge_specific_emissions[("Transformer", "Powerline")])
1000

>>> print(pypsa_all_res.edge_specific_emissions[("Transformer", "Powerline")])
1000.0

>>> print(fine_all_res.edge_specific_emissions[("Transformer", "Powerline")])
1000.0

>>> print(cllp_all_res.edge_specific_emissions[("Transformer", "Powerline")])
1000.0

Edge Weights
------------

>>> print(omf_all_res.edge_weight[("Transformer", "Powerline")])
0.1

>>> print(pypsa_all_res.edge_weight[("Transformer", "Powerline")])
0.1

>>> print(fine_all_res.edge_weight[("Transformer", "Powerline")])
0.1

>>> print(cllp_all_res.edge_weight[("Transformer", "Powerline")])
0.1


Integrated Global Results
-------------------------

>>> omf_igr = post_process_omf.IntegratedGlobalResultier(optimized_omf_es)
>>> ppsa_igr = post_process_pypsa.IntegratedGlobalResultier(optimized_pypsa_es)
>>> fine_igr = post_process_fine.IntegratedGlobalResultier(optimized_fine_es)
>>> cllp_igr = post_process_cllp.IntegratedGlobalResultier(optimized_cllp_es)


>>> print("omf:", omf_igr.global_results)
omf: {'emissions (sim)': 30000.0, 'costs (sim)': 3000.0, 'opex (ppcd)': 3000.0, 'capex (ppcd)': 0.0}

>>> print("ppsa:", ppsa_igr.global_results)
ppsa: {'emissions (sim)': 30000.0, 'costs (sim)': 3000.0, 'opex (ppcd)': 3000.0, 'capex (ppcd)': 0.0}

Note how the current tessif -> fine implementation averages the time varying efficiencies
thus leading to higher costs and emissions while at the same time not processing the
net energy flow correctly:

>>> print("fine:", fine_igr.global_results)
fine: {'emissions (sim)': 32500.0, 'costs (sim)': 3250.0, 'opex (ppcd)': 0.0, 'capex (ppcd)': 0.0}

>>> print("cllp:", cllp_igr.global_results)
cllp: {'emissions (sim)': 30000.0, 'costs (sim)': 3000.0, 'opex (ppcd)': 3000.0, 'capex (ppcd)': 0.0}





