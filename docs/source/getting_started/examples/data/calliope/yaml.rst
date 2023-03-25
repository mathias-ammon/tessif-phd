.. _examples_data_calliope_yaml:

yaml
****

Other than Tessif, Calliope does usually read the model from yaml files.
Examples of these are stored in the calliope folder inside the 
tessif examples data folder. Additionally any model created with tessif
and transformed to calliope will be stored as yaml in the calliope
folder inside the tessif write folder.

For deeper information on how to build, run and analyse an energy
system model using calliope refer to the `documentation of calliope
<https://calliope.readthedocs.io/en/stable/>`_.

.. contents:: Contents
   :local:
   :backlinks: top

Minimum working example
=======================
.. note::
   Original yaml data can be found in
   ``tessif/examples/data/calliope/mwe/``
   as well as its subfolders.

Original Data yaml Files
------------------------

**mwe/model.yaml**
^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/mwe/model.yaml
   :language: yaml

**mwe/model_config/techs.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/mwe/model_config/techs.yaml
   :language: yaml

**mwe/model_config/locations.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/mwe/model_config/locations.yaml
   :language: yaml

Use Case
--------

1. Read the energy system model and optimize it

    >>> from tessif.frused.paths import example_dir
    >>> import pprint
    >>> import calliope
    >>> calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> es = calliope.Model(f'{example_dir}/data/calliope/mwe/model.yaml')
    >>> es.run()

2. Print out the objective value

    >>> # See the set production costs
    >>> print(f'Objective: {es.results.objective_function_value}')
    Objective: 61.0

3. Use Tessif post processing

    >>> from tessif.transform.es2mapping.cllp import LoadResultier
    >>> loads = LoadResultier(es)
    >>> print(loads.node_load['Powerline'])
    Powerline            Battery  Generator  Battery  Demand
    1990-07-13 00:00:00    -10.0       -0.0      0.0    10.0
    1990-07-13 01:00:00     -0.0      -10.0      0.0    10.0
    1990-07-13 02:00:00     -0.0      -10.0      0.0    10.0
    1990-07-13 03:00:00     -0.0      -10.0      0.0    10.0

    >>> from tessif.transform.es2mapping.cllp import IntegratedGlobalResultier
    >>> global_res = IntegratedGlobalResultier(es)
    >>> pprint.pprint(global_res.global_results)
    {'capex (ppcd)': 0.0,
     'costs (sim)': 61.0,
     'emissions (sim)': 0.0,
     'opex (ppcd)': 61.0}

Fully parameterized working example
===================================
.. note::
   Original yaml data can be found in
   ``tessif/examples/data/calliope/fpwe/``
   as well as its subfolders.

Original Data -- yaml Files
---------------------------

**fpwe/model.yaml**
^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/fpwe/model.yaml
   :language: yaml

**fpwe/model_config/techs.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/fpwe/model_config/techs.yaml
   :language: yaml

**fpwe/model_config/locations.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/fpwe/model_config/locations.yaml
   :language: yaml


Use Case
--------

1. Read the energy system model and optimize it

    >>> from tessif.frused.paths import example_dir
    >>> import pprint
    >>> import calliope
    >>> calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> es = calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')
    >>> es.run()

2. Print out the objective value

    >>> # See the set production costs
    >>> print(f'Objective: {es.results.objective_function_value}')
    Objective: 104.809524

3. Use Tessif post processing

    >>> from tessif.transform.es2mapping.cllp import LoadResultier
    >>> loads = LoadResultier(es)
    >>> print(loads.node_load['Powerline'])
    Powerline            Battery  Generator  Solar Panel  Battery  Demand
    1990-07-13 00:00:00     -0.0       -0.0        -12.0      1.0    11.0
    1990-07-13 01:00:00     -8.0       -0.0         -3.0      0.0    11.0
    1990-07-13 02:00:00     -0.9       -3.1         -7.0      0.0    11.0

    >>> from tessif.transform.es2mapping.cllp import IntegratedGlobalResultier
    >>> global_res = IntegratedGlobalResultier(es)
    >>> pprint.pprint(global_res.global_results)
    {'capex (ppcd)': 0.0,
     'costs (sim)': 105.0,
     'emissions (sim)': 53.0,
     'opex (ppcd)': 105.0}

CHP expansion example
=====================
.. note::
   Original yaml data can be found in
   ``tessif/examples/data/calliope/chp_expansion/``
   as well as its subfolders.

This energy system model was created to further inspect the parameter
definitions of CHPs when they are expandable. It can be optimized using 
calliope and then be inspected using either the usual calliope commands
as well as the tessif post processing.

Original Data -- yaml Files
---------------------------

**chp_expansion/model.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/chp_expansion/model.yaml
   :language: yaml

**chp_expansion/model_config/techs.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/chp_expansion/model_config/techs.yaml
   :language: yaml

**chp_expansion/model_config/locations.yaml**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude::
   ../../../../../../src/tessif/examples/data/calliope/chp_expansion/model_config/locations.yaml
   :language: yaml

Use Case
--------

1. Read the energy system model and optimize it

    >>> from tessif.frused.paths import example_dir
    >>> import pprint
    >>> import calliope
    >>> calliope.set_log_verbosity('ERROR', include_solver_output=False)
    >>> es = calliope.Model(f'{example_dir}/data/calliope/chp_expansion/model.yaml')
    >>> es.run()

2. Print out the flow result

    >>> # See the set production costs
    >>> print(es.inputs.cost_om_prod.loc[{'loc_techs_om_cost': 'CHP location::CHP'}].loc[{'costs': 'monetary'}].data)
    array(1.)

    >>> # See the production result for each CHP carrier
    >>> print(es.get_formatted_array('carrier_prod').loc[{'carriers':'electricity'}].sum('locs').to_pandas().T['CHP'])
    timesteps
    1990-07-13 00:00:00    8.0
    1990-07-13 01:00:00    8.0
    1990-07-13 02:00:00    8.0
    1990-07-13 03:00:00    8.0
    Name: CHP, dtype: float64
    >>> print(es.get_formatted_array('carrier_prod').loc[{'carriers':'heat'}].sum('locs').to_pandas().T['CHP'])
    timesteps
    1990-07-13 00:00:00    6.4
    1990-07-13 01:00:00    6.4
    1990-07-13 02:00:00    6.4
    1990-07-13 03:00:00    6.4
    Name: CHP, dtype: float64

    >>> # See the variable costs of the CHP
    >>> print(es.get_formatted_array('cost_var').loc[{'costs':'monetary'}].loc[{'locs':'CHP location'}].sum('techs'))
    Out[64]:
    <xarray.DataArray 'cost_var' (timesteps: 4)>
    array([8., 8., 8., 8.])
    Coordinates:
        costs      <U8 'monetary'
        locs       <U12 'CHP location'
      * timesteps  (timesteps) datetime64[ns] 1990-07-13 ... 1990-07-13T03:00:00

So it can be seen that production costs of CHP refer to the primary output.

3. Print out the capacity

    >>> # See the input expansion costs
    >>> print(es.get_formatted_array('cost_energy_cap').sum('locs').to_pandas().T)
    costs  emissions  monetary
    techs
    CHP          0.0       1.0

    >>> # See the expansion cost result
    >>> print(es.get_formatted_array('cost_investment').sum('locs').to_pandas().T)
    costs  emissions  monetary
    techs
    CHP          0.0       8.0

With the already known flow maximum it can be seen that the energy capacity costs of CHP refer to the primary output.


4. Compare to tessif post processing

    >>> from tessif.transform.es2mapping.cllp import FlowResultier
    >>> flow = FlowResultier(es)
    >>> pprint.pprint(flow.edge_net_energy_flow)
    {Edge(source='Backup Heat', target='Heat Grid'): 14.4,
     Edge(source='Backup Power', target='Powerline'): 8.0,
     Edge(source='CHP', target='Heat Grid'): 25.6,
     Edge(source='CHP', target='Powerline'): 32.0,
     Edge(source='Gas Grid', target='CHP'): 64.0,
     Edge(source='Gas Source', target='Gas Grid'): 64.0,
     Edge(source='Heat Grid', target='Heat Demand'): 40.0,
     Edge(source='Powerline', target='Power Demand'): 40.0}

    >>> pprint.pprint(flow.edge_specific_flow_costs)
    {Edge(source='Backup Heat', target='Heat Grid'): 1000.0,
     Edge(source='Backup Power', target='Powerline'): 1000.0,
     Edge(source='CHP', target='Heat Grid'): 0,
     Edge(source='CHP', target='Powerline'): 1.0,
     Edge(source='Gas Grid', target='CHP'): 0,
     Edge(source='Gas Source', target='Gas Grid'): 0.0,
     Edge(source='Heat Grid', target='Heat Demand'): 0.0,
     Edge(source='Powerline', target='Power Demand'): 0.0}

    >>> from tessif.transform.es2mapping.cllp import CapacityResultier
    >>> cap_res = CapacityResultier(es)
    >>> print(cap_res.node_original_capacity['CHP'])
    Heat Grid    0.0
    Powerline    0.0
    dtype: float64
    >>> print(cap_res.node_installed_capacity['CHP'])
    Heat Grid    6.4
    Powerline    8.0
    dtype: float64
    >>> print(cap_res.node_expansion_costs['CHP'])
    Heat Grid    0.0
    Powerline    1.0
    dtype: float64

    >>> from tessif.transform.es2mapping.cllp import LoadResultier
    >>> loads = LoadResultier(es)
    >>> print(loads.node_load['Powerline'])
    Powerline            Backup Power  CHP  Power Demand
    1990-07-13 00:00:00          -2.0 -8.0          10.0
    1990-07-13 01:00:00          -2.0 -8.0          10.0
    1990-07-13 02:00:00          -2.0 -8.0          10.0
    1990-07-13 03:00:00          -2.0 -8.0          10.0
    >>> print(loads.node_load['Heat Grid'])
    Heat Grid            Backup Heat  CHP  Heat Demand
    1990-07-13 00:00:00         -3.6 -6.4         10.0
    1990-07-13 01:00:00         -3.6 -6.4         10.0
    1990-07-13 02:00:00         -3.6 -6.4         10.0
    1990-07-13 03:00:00         -3.6 -6.4         10.0

    >>> from tessif.transform.es2mapping.cllp import IntegratedGlobalResultier
    >>> global_res = IntegratedGlobalResultier(es)
    >>> pprint.pprint(global_res.global_results)
    {'capex (ppcd)': 8.0,
     'costs (sim)': 22440.0,
     'emissions (sim)': 32.0,
     'opex (ppcd)': 22432.0}

    >>> print(f'Objective: {es.results.objective_function_value}')
    Objective: 22440.0

