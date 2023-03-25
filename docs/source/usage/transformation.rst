.. _Transformation:

**************
Transformation
**************

As laid out in :ref:`Introduction` and :ref:`Models_Tessif_Purpose`
:mod:`tessif` aims to provide a simple yet powerful interface for analysing
energy supply systems using different models. Hence a common task performed
with tessif is to parameterize an energy system once using
:class:`tessif's energy system
<tessif.model.energy_system.AbstractEnergySystem>` and then transforming
it into the different kinds of supported models to conduct simulations.


Following sections explain how such transfomations can be archieved using
singular models while also giving some examples. For comparing multiple models
on the same energy system, refer to the respective
:ref:`example hub section <examples_auto_comparison>`.

See here for :mod:`examples on pure model code <tessif.examples.data>` 


.. note::
   When aiming to perform large scale investigations, involving many different
   kinds of parameterized energy systems it is much more convenient to use
   the :mod:`simulate wrappers <tessif.simulate>` directly providing
   ``from_tessif=True`` as argument, as can be seen here
   :paramref:`here <tessif.simulate.omf>`.

.. contents:: Contents
   :local:
   :backlinks: top

.. _Transformation_Oemof:


Oemof
*****
:class:`Tessif energy systems <tessif.model.energy_system.AbstractEnergySystem>`
are transformed into :class:`oemof energy systems
<oemof.energy_system.EnergySystem>` using
:meth:`tessif.transform.es2es.omf.transform`.
      
The concept of :class:`oemof's energy system<oemof.energy_system.EnergySystem>`
and :class:`tessif's energy system
<tessif.model.energy_system.AbstractEnergySystem>` are quite similar in the sense
that both apply a generalization approach when modeling an energy system.


Transforming data sets from tessif to oemof is therefore quite simple. And in
case none of oemof's more specialized components are used, no data loss is to
be expected.

Following examples illustrate how instances of tessif energy systems can be
transformed into oemof energy systems


Minimum Working Example
=======================

.. note::
   A utility wrapper returning the tessif energy system as well as the
   transformed oemof energy system can be found in:
   ``tessif/examples/transformation/omf.py``

Utilizing the :ref:`example hub's <Examples>`
:meth:`~tessif.examples.data.tsf.py_hard.create_mwe` utility for conveniently
accessing basic :class:`tessif energy system
<tessif.model.energy_system.AbstractEnergySystem>` instance:

1. Create the mwe:

   >>> from tessif.examples.data.tsf.py_hard import create_mwe
   >>> tessif_es = create_mwe()

2. Transform the :mod:`tessif energy system
   <tessif.model.energy_system.AbstractEnergySystem>`:

   >>> from tessif.transform.es2es.omf import transform
   >>> oemof_es = transform(tessif_es)

3. Show node labels using the :attr:`omeof interface
   <oemof.network.Node.label>` as well as :mod:`tessif's uid concept
   <tessif.frused.namedtuples.Uid>`:

   >>> for node in oemof_es.nodes:
   ...     print(node.label.name)
   Pipeline
   Powerline
   Gas Station
   Demand
   Generator
   Battery

4. Simulate the oemof energy system:

   >>> import tessif.simulate as simulate
   >>> optimized_oemof_es = simulate.omf_from_es(oemof_es)

5. Extract some results:

   >>> import tessif.transform.es2mapping.omf as transform_oemof_results
   >>> load_results = transform_oemof_results.LoadResultier(
   ...     optimized_oemof_es)
   >>> print(load_results.node_load['Powerline'])
   Powerline            Battery  Generator  Battery  Demand
   1990-07-13 00:00:00    -10.0       -0.0      0.0    10.0
   1990-07-13 01:00:00     -0.0      -10.0      0.0    10.0
   1990-07-13 02:00:00     -0.0      -10.0      0.0    10.0
   1990-07-13 03:00:00     -0.0      -10.0      0.0    10.0

   
Constraints Types
=================

Following sections provide overview and examples on how tessif transforms
different constraint types, so oemof can interprete them.

The code examples illustrated makes use of tessif components as well as the
corresponding oemof transformation module:

    >>> # prepare a list of oemof and tessif busses, to be used later on
    >>> import tessif.model.components as tessif_components
    >>> import tessif.transform.es2es.omf as tsf_to_omf
    >>> tessif_bus = tessif_components.Bus(
    ...     name='my_bus',
    ...     inputs=('my_source.power', 'my_transformer.power'),
    ...     outputs=('my_sink.power', 'my_transformer.fuel'))
    >>> oemof_bus = list(tsf_to_omf.generate_oemof_busses((tessif_bus,)))[0]


Optimization Parameters
-----------------------
:class:`oemof energy systems components <oemof.energy_system.EnergySystem>`
formulate flow rate specific cost parameters subject to global minimization
bound to the individual component's :class:`oemof.solph.network.Flow`:

    - :paramref:`oemof.solph.network.Flow.variable_costs`

Example
^^^^^^^

Parameterize and transform a :class:`tessif source
<tessif.model.components.Source>` object:
    
>>> tessif_source = tessif_components.Source(
...     name='my_source', outputs=('power',),
...     flow_costs={'power': 42})
>>> oemof_source = list(tsf_to_omf.generate_oemof_sources(
...     sources=(tessif_source,),
...     tessif_busses=(tessif_bus,),
...     oemof_busses=(oemof_bus,)))[0]

To see optimization parameter conversion:

>>> for outflow in oemof_source.outputs.values():
...     print(outflow.variable_costs[0])
42
    
   
.. _Usage_Transformation_Oemof_LinearConstraints:

Linear Constraints
-------------------
:class:`oemof energy systems components <oemof.energy_system.EnergySystem>`
possibly formulate a number of linear constraints. These include:

   - :paramref:`oemof.solph.network.Flow.nominal_value`
   - :paramref:`oemof.solph.network.Flow.summed_min`
   - :paramref:`oemof.solph.network.Flow.summed_max`
   - :paramref:`oemof.solph.network.Flow.min`
   - :paramref:`oemof.solph.network.Flow.max`
   - :paramref:`oemof.solph.network.Flow.positive_gradient`
   - :paramref:`oemof.solph.network.Flow.negative_gradient`

Refer to `oemofs source code
<https://github.com/oemof/oemof-solph/blob/db1e30eec97962168389a2a105c79a92e2379c5c/src/oemof/solph/network/flow.py#L24>`_,
cause currently the documentation is in shambles.

Example
^^^^^^^
Parameterise and transform a :mod:`tessif sink
<tessif.model.components.Sink>` object: 

>>> tessif_sink = tessif_components.Sink(
...     name='my_sink', inputs=('power',),
...     accumulated_amounts={'power': (42, 84)},
...     flow_rates={'power': (0, 42)},
...     flow_gradients={'power': (0, 100)},
...     gradient_costs={'power': (1, 1)},
...     )
>>> oemof_sink = list(tsf_to_omf.generate_oemof_sinks(
...     sinks=(tessif_sink,),
...     tessif_busses=(tessif_bus,),
...     oemof_busses=(oemof_bus,)))[0]

To see linear constraint parameter conversions:

>>> for otpt in oemof_sink.inputs.values():
...     print('nominal_value:', otpt.nominal_value)
...     print('min:', otpt.min[0])
...     print('max:', otpt.max[0])
...     print('summed_max:', otpt.summed_max)
...     print('summed_min:', otpt.summed_min)
...     print('positive_gradient:', otpt.positive_gradient['ub'][0])
...     print('positive_gradient_costs:', otpt.positive_gradient['costs'])
...     print('negative_gradient:', otpt.negative_gradient['ub'][0])
...     print('negative_gradient_costs:', otpt.negative_gradient['costs'])
nominal_value: 42
min: 0.0
max: 1.0
summed_max: 2.0
summed_min: 1.0
positive_gradient: 0
positive_gradient_costs: 1
negative_gradient: 100
negative_gradient_costs: 1

In the context of :mod:`Tessif <tessif>` some linear parameters
are subject to global constraints but bound to the individual component's
:class:`oemof.solph.network.Flow`.

   - :paramref:`tessif.model.components.Sink.flow_emissions`

These are handled by tessif's transformation utilities In particular by:

   - :paramref:`tessif.transform.mapping2es.tsf.transform.global_constraints`
   - :paramref:`tessif.parse.python_mapping.global_constraints`

And are accessible via the energy system.

Expansion Constraints
---------------------
:class:`oemof energy systems components <oemof.energy_system.EnergySystem>` can
formulate a number of expansion problem constraints, but only if a dedicated
:class:`oemof.solph.options.Investment` object is created.
These expansion problem parameters include:

   - :paramref:`oemof.solph.options.Investment.maximum`
   - :paramref:`oemof.solph.options.Investment.minimum`
   - :paramref:`oemof.solph.options.Investment.existing`
   - :paramref:`oemof.solph.options.Investment.ep_costs`

Example
^^^^^^^
Parameterise and transform a :mod:`tessif source
<tessif.model.components.Source>` object: 

>>> tessif_source = tessif_components.Source(
...     name='my_source', outputs=('power',),
...     flow_rates={'power': (0, 30)},
...     expandable={'power': True},
...     expansion_costs={'power': 5},
...     expansion_limits={'power': (30, 100)}
...     )

>>> oemof_source = list(tsf_to_omf.generate_oemof_sources(
...     sources=(tessif_source,),
...     tessif_busses=(tessif_bus,),
...     oemof_busses=(oemof_bus,)))[0]

To see expansion problem parameter conversions:

>>> for otpt in oemof_source.outputs.values():
...    print('ep_costs:', otpt.investment.ep_costs)
...    print('existing:', otpt.investment.existing)
...    print('maximum:', otpt.investment.maximum)
...    print('minimum:', otpt.investment.minimum)
ep_costs: 5
existing: 30
maximum: 70
minimum: 0

.. note::
   Note how oemof uses minimum/maximum expansion constraints as additional
   installed capacity, whereas tessif defines them as absolute values.


Mixed Integer Linear Constraints
--------------------------------
:class:`oemof energy systems components <oemof.energy_system.EnergySystem>`
possibly formulate a number of mixed integer linear problem (milp) constraints,
but only if a dedicated :class:`oemof.solph.options.NonConvex` object is
created. These milp parameters include:

   - :paramref:`oemof.solph.options.NonConvex.startup_costs`
   - :paramref:`oemof.solph.options.NonConvex.shutdown_costs`
   - :paramref:`oemof.solph.options.NonConvex.activity_costs`
   - :paramref:`oemof.solph.options.NonConvex.minimum_uptime`
   - :paramref:`oemof.solph.options.NonConvex.minimum_downtime`
   - :paramref:`oemof.solph.options.NonConvex.maximum_startups`
   - :paramref:`oemof.solph.options.NonConvex.maximum_shutdowns`
   - :paramref:`oemof.solph.options.NonConvex.initial_status`

Example
^^^^^^^

Parameterise and transform a :mod:`tessif transformer
<tessif.model.components.Transformer>` object: 

>>> tessif_transformer = tessif_components.Transformer(
...     name='my_transformer', inputs=('fuel',), outputs=('power',),
...     conversions={('fuel', 'power'): 0.42},
...     milp={'power': True, 'fuel': False},
...     number_of_status_changes=(13, 15),
...     costs_for_being_active=7,
...     status_changing_costs=(9, 1),
...     status_inertia=(0, 2),
...     initial_status=(1),
...     )

>>> oemof_transformer = list(tsf_to_omf.generate_oemof_transformers(
...     transformers=(tessif_transformer,),
...     tessif_busses=(tessif_bus,),
...     oemof_busses=(oemof_bus,)))[0]

To see mixed integer linear problem parameter conversions:

>>> for otpt in oemof_transformer.outputs.values():
...     print('startup_costs:', otpt.nonconvex.startup_costs[0])
...     print('shutdown_costs:', otpt.nonconvex.shutdown_costs[0])
...     print('activity_costs:', otpt.nonconvex.activity_costs[0])
...     print('minimum_uptime:', otpt.nonconvex.minimum_uptime)
...     print('minimum_downtime:', otpt.nonconvex.minimum_downtime)
...     print('maximum_startups:', otpt.nonconvex.maximum_startups)
...     print('maximum_shutdowns:', otpt.nonconvex.maximum_shutdowns)
...     print('initial_status:', otpt.nonconvex.initial_status)
startup_costs: 9
shutdown_costs: 1
activity_costs: 7
minimum_uptime: 0
minimum_downtime: 2
maximum_startups: 13
maximum_shutdowns: 15
initial_status: 1
   

Pypsa
*****

Minimum Working Example
=======================

Constraints Types
=================
Following sections provide overview and examples on how tessif transform
different constraint types, so pypsa can interprete them.

The code examples illustrated makes use of tessif components as well as the
corresponding oemof transformation module:

    >>> # prepare a list of oemof and tessif busses, to be used later on
    >>> import tessif.model.components as tessif_components
    >>> import tessif.transform.es2es.ppsa as tsf2pypsa
    >>> tessif_bus = tessif_components.Bus(
    ...     name='my_bus',
    ...     inputs=('my_source.power', 'my_transformer.power'),
    ...     outputs=('my_sink.power', 'my_transformer.fuel'))


Optimization Parameters
-----------------------
`pypsa energy systems components
<https://pypsa.readthedocs.io/en/latest/components.html>`_ formulate flow rate
specific cost parameters subject to global minimization
bound to the individual component's ``marginal_cost`` attribute.


Example
^^^^^^^

Parameterize and transform a :class:`tessif source
<tessif.model.components.Source>` object:
    
>>> tessif_source = tessif_components.Source(
...     name='my_source', outputs=('power',),
...     flow_costs={'power': 42})
>>> pypsa_source_dict = tsf2pypsa.create_pypsa_generators_from_sources(
...     sources=[tessif_source],
...     tessif_busses=[tessif_bus],
... )[0]

To see optimization parameter conversion:

>>> from pypsa import Network
>>> pypsa_es = Network()
>>> pypsa_es.add(**pypsa_source_dict)
>>> print(pypsa_es.generators.marginal_cost['my_source'])
42.0


Global Constraints
------------------
In the context of :mod:`Tessif <tessif>` some linear parameters
are subject to global constraints but bound to the individual component's
:attr:`~tessif.model.components.Source.flow_rates`. These are:

   - :paramref:`tessif.model.components.Source.flow_emissions`

These are handled by tessif's transformation utilities In particular by:

   - :paramref:`tessif.transform.mapping2es.tsf.transform.global_constraints`
   - :paramref:`tessif.parse.python_mapping.global_constraints`

And are accessible via the energy system. Pypsa however uses a completely
`different approach
<https://pypsa.readthedocs.io/en/latest/optimal_power_flow.html?#global-constraints>`_.
It binds a certain CO2 generation to the usage of a `primary energy carrier
<https://pypsa.readthedocs.io/en/latest/components.html#carrier>`_.

Transforming between tessif's and pypsa's approach is done by:

   - :class:`tessif.transform.es2mapping.ppsa.IntegratedGlobalResultier`
   - :func:`tessif.transform.es2es.ppsa.transform_emissions`
   

     
.. _Usage_Transformation_Pypsa_LinearConstraints:

Linear Constraints
-------------------
`pypsa energy systems components
<https://pypsa.readthedocs.io/en/latest/components.html>`_
possibly formulate a number of linear constraints. These include:

   - ``p_nom``, ``q_nom``
   - ``p_min_pu``
   - ``p_max_pu``

.. note::

   Note that pypsa does not include a
   :paramref:`~tessif.model.components.Source.accumulated_amounts` (minimum and
   maximum) constraint.

   Further more, the attributes: ``ramp_limit_up`` and ``ramp_limit_down`` are
   considered :ref:`milp constraints
   <Usage_Transformation_Pypsa_MilpConstraints>`, where as in :mod:`tessif
   <tessif.model.components>` and :ref:`oemof
   <Usage_Transformation_Oemof_LinearConstraints>` they are considered as
   linear constraints.
   

Example
^^^^^^^
Parameterise and transform a :mod:`tessif source
<tessif.model.components.Source>` object:

>>> tessif_source = tessif_components.Source(
...     name='my_source', outputs=('power',),
...     accumulated_amounts={'power': (42, 84)},
...     flow_rates={'power': (0, 42)},
...     flow_gradients={'power': (0, 100)},
...     gradient_costs={'power': (1, 1)},
...     )

>>> pypsa_source_dict = tsf2pypsa.create_pypsa_generators_from_sources(
...     sources=[tessif_source],
...     tessif_busses=[tessif_bus],
... )[0]

Add the new component to a pypsa energy system:

>>> from pypsa import Network
>>> pypsa_es = Network()
>>> pypsa_es.add(**pypsa_source_dict)

To see expansion problem parameter conversions:

>>> print(pypsa_es.generators[
...     ["p_nom", "p_min_pu", "p_max_pu", "ramp_limit_up", "ramp_limit_down"]])
attribute  p_nom  p_min_pu  p_max_pu  ramp_limit_up  ramp_limit_down
Generator                                                           
my_source   42.0       0.0       1.0            NaN              NaN


Expansion Constraints
---------------------
`pypsa energy systems components
<https://pypsa.readthedocs.io/en/latest/components.html>`_
can formulate a number of expansion problem constraints.
These expansion problem parameters include:

   - ``p_nom_extendable``
   - ``p_nom_min``
   - ``p_nom_max``
   - ``capital_cost``
     
.. note::
   In contrast to oemof where an ``existing`` parameter exists
   (see :class:`oemof.solph.options.Investment`), the already existing amount of
   installed capacity is defined by using the :ref:`linear constraint
   <Usage_Transformation_Pypsa_LinearConstraints>` ``p_nom``.

   The same approach is used by tessif, where the :attr:`maximum flow rate
   <tessif.model.components.Source.flow_rates>` is used for the amount of
   capacity already installed.
   

Example
^^^^^^^
Parameterise and transform a :mod:`tessif source
<tessif.model.components.Source>` object: 

>>> tessif_source = tessif_components.Source(
...     name='my_source', outputs=('power',),
...     expandable={'power': True},
...     expansion_costs={'power': 5},
...     expansion_limits={'power': (0, 100)}
...     )

>>> pypsa_source_dict = tsf2pypsa.create_pypsa_generators_from_sources(
...     sources=[tessif_source],
...     tessif_busses=[tessif_bus],
... )[0]

Add the new component to a pypsa energy system:

>>> from pypsa import Network
>>> pypsa_es = Network()
>>> pypsa_es.add(**pypsa_source_dict)

To see expansion problem parameter conversions:

>>> print(pypsa_es.generators[
...     ["p_nom_extendable", "p_nom_min", "p_nom_max", "capital_cost", ]])
attribute  p_nom_extendable  p_nom_min  p_nom_max  capital_cost
Generator                                                      
my_source              True        0.0      100.0           5.0


.. _Usage_Transformation_Pypsa_MilpConstraints:

Mixed Integer Linear Constraints
--------------------------------
`pypsa energy systems components
<https://pypsa.readthedocs.io/en/latest/components.html>`_
possibly formulate a number of mixed integer linear problem (milp) constraints.
These milp parameters include:

   - ``committable``
   - ``start_up_cost``
   - ``shut_down_cost``
   - ``ramp_limit_up``
   - ``ramp_limit_down``
   - ``min_up_time``
   - ``min_down_time``
   - ``up_time_before``
     
In constrast to oemof and tessif, pypsa does not constrain the number of
:attr:`start ups and shutdowns
<tessif.model.components.Source.number_of_status_changes>`. It also does not
allow to formulate an :attr:`activity cost parameter
<tessif.model.components.Source.status_changing_costs>`.

Pypsa however fomulates a number of milp constraints, other models don't:
   
   - ``ramp_limit_start_up``
   - ``ramp_limit_shut_down`` 
   - ``down_time_before``
     

Example
^^^^^^^

Parameterise and transform a :mod:`tessif transformer
<tessif.model.components.Transformer>` object: 

>>> tessif_transformer = tessif_components.Transformer(
...     name='my_transformer',
...     inputs=('fuel',),
...     outputs=('power',),
...     conversions={('fuel', 'power'): 0.42},
...     flow_rates={'power': (0, 100), 'fuel': (0, float('+inf'))},
...     flow_gradients={
...         'power': (100, 50),
...         'fuel': (float('+inf'), float('+inf'))},
...     milp={'power': True, 'fuel': False},
...     number_of_status_changes=(13, 15),
...     costs_for_being_active=7,
...     status_changing_costs=(9, 1),
...     status_inertia=(0, 2),
...     initial_status=(False),
...     )

>>> pypsa_generator_dict = tsf2pypsa.create_pypsa_generators_from_transformers(
...     transformers=[tessif_transformer],
...     tessif_busses=[tessif_bus],
... )[0]

Add the new component to a pypsa energy system:

>>> from pypsa import Network
>>> pypsa_es = Network()
>>> pypsa_es.add(**pypsa_generator_dict)

To see the milp parameter conversions:

>>> print(pypsa_es.generators[
...     ["committable", "start_up_cost", "shut_down_cost"]])
attribute       committable  start_up_cost  shut_down_cost
Generator                                                 
my_transformer         True            9.0             1.0

>>> print(pypsa_es.generators[
...     ["ramp_limit_up", "ramp_limit_down"]])
attribute       ramp_limit_up  ramp_limit_down
Generator                                     
my_transformer            1.0              0.5

>>> print(pypsa_es.generators[
...     ["min_up_time", "min_down_time", "up_time_before"]])
attribute       min_up_time  min_down_time  up_time_before
Generator                                                 
my_transformer            0              2               0
    

Tessif does not formulate any of the following constraints, hence they are set
to their default values:

>>> print(pypsa_es.generators[
...     ["ramp_limit_start_up", "ramp_limit_shut_down", "down_time_before" ]])
attribute       ramp_limit_start_up  ramp_limit_shut_down  down_time_before
Generator                                                                  
my_transformer                  1.0                   1.0                 0
