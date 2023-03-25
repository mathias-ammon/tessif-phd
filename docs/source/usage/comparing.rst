.. _Comparison:

**********
Comparison
**********

Comparing different energy system simulation models, is one of tessif's main field of application.

Following sections prrovide detailed information on how to use them as well as consequential
links for more detailed information.

.. contents::
   :local:


Question Tessif Helps to Answer
*******************************
As laid out in :ref:`Introduction` and :ref:`Models_Tessif_Purpose`
:mod:`tessif` aims to provide a simple yet powerful interface for analysing
energy supply systems using different models.

Hence one of Tessif's primary use cases is to compare energy system simulation models
on a given energy system to answer two major questions:

1. Given an expansion and/or commitment problem, what could be a range of possible solutions using different approaches and underlying models?

   Tessif helps answering that by automatically conducting simulations on a singular energy system using it's :ref:`SupportedModels`. It also :ref:`aggregates the result's conveniently <hhes_overall_results>` to quickly get an idea of the range to expect of key target values like for example the expansion costs.

2. What would be the best model to perform a certain indepth analysis when modeling an energy system?

   Tessif helps answering that question by providing three major sources of information:

   a. A user guide on how tessif handles :ref:`model transformation <Transformation>`. This is basically overview on what solver constraints are formulated by each model and how that differs from :mod:`tessif's approach <tessif.model>`. When looking for certain model capabilities as in what can be constrained, this serves as a valuable entry point.

   b. A set of :ref:`application examples <Application>` for common energy system simulation scenarios, highlighting both simalarities and differences in results as well as modeling aproach.
      
   c. The :mod:`module <tessif.transform.es2es>` transforming the tessif energy system into the model specific energy system. Which holds not only the code base for transforming the models, but also information on what is transformed and how and in particular if something noteable appears, like :attr:`cutting of supply chains <tessif.transform.es2es.ppsa.compute_unneeded_supply_chains>` when using pypsa, for example.


.. _Usage_Comparing_Caveats:

Caveats of Parameterizing an Energy System for Comparison
*********************************************************
When :mod:`creating a tessif energy system <tessif.examples.data.tsf.py_hard>` to use as underlying energy system for comparing different :ref:`models <SupportedModels>`, parameterization of this energy system plays a key role in what results are to be expected. Following sections document some caveats the tessif users have encountered during use. 

.. _Usage_Comparing_Caveats_CHP:

CHP Plants
----------
Using :class:`~tessif.model.components.Transformer` objects to model Combined Heat and Power Plants can result in rather unexpected results. This mainly stemps from the fact the different models allow different degrees of freedom when parameterizing the chp plant.

Best advice here is to interprete the :attr:`~tessif.model.components.Transformer.conversions` as fixed ratios, which are seen as more important (by some models) than the acutally stated :attr:`~tessif.model.components.Transformer.flow_rates`. So make sure that, in case you want to limit the flow rates, those limits reflect the ratios given by the conversions.
Meaning if your conversions are i.e ``0.6`` and ``0.3`` make sure that the flow rates are something like ``200`` and ``100`` respectively.

Good Example
^^^^^^^^^^^^
Note, how the ``biomass`` -> ``electricity`` conversion reflects the flow rate ratios or vice versa.

Taken from :attr:`tessif.examples.data.tsf.py_hard.create_hhes`::

  # Biomass Combined Heat and Power
  bm_chp = components.Transformer(
      name='biomass chp',
      inputs=('biomass',),
      outputs=('electricity', 'hot_water',),
      conversions={
          ('biomass', 'electricity'): 48.4/126,
          ('biomass', 'hot_water'): 1,
      },
      flow_rates={
          'biomass': nts.MinMax(min=0, max=float('+inf')),
          'electricity': nts.MinMax(min=0, max=48.4),
          'hot_water': nts.MinMax(min=0, max=126),
      },
  )

Problematic Example
^^^^^^^^^^^^^^^^^^^
Tessif's interface also allows the solver inferring the right ratio by for example setting the ``biomass`` -> ``electricity`` conversion to ``1``. This however leads to unexpected behaviour when using :ref:`Models_Pypsa`::

  # Biomass Combined Heat and Power
  bm_chp = components.Transformer(
      name='biomass chp',
      inputs=('biomass',),
      outputs=('electricity', 'hot_water',),
      conversions={
          # note the changed conversion
          # this can be problematic or cause unexpected behaviour:
          ('biomass', 'electricity'): 1,  # 48.4/126,
          ('biomass', 'hot_water'): 1,
      },
      flow_rates={
          'biomass': nts.MinMax(min=0, max=float('+inf')),
          'electricity': nts.MinMax(min=0, max=48.4),
          'hot_water': nts.MinMax(min=0, max=126),
      },
  )



.. _Usage_Comparing_Caveats_Expansion:

Expansion Problems
------------------
When formulating expansion problems like for example in :func:`tessif.examples.data.tsf.py_hard.create_expansion_plan_example` make sure to state the flow rates explicitly (even if they are 0) because otherwise tessif's default of not limiting the flow rate (by constraining it to ``float('+inf')``) can confuse some model-solver combination. Because mathematically, it doesn't make sense to expand something that is already infinite.

Good Example
^^^^^^^^^^^^
Note, how the ``biomass`` -> ``electricity`` conversion reflects the flow rate ratios or vice versa.

Taken from :attr:`tessif.examples.data.tsf.py_hard.create_expansion_plan_example`, slightly modified::

  # capped source having no costs, no emission, no flow constraints
  # but existing and max installed capacity (for expansion) as well
  # as expansion costs
  capped_renewable = components.Source(
      name='Capped Renewable',
      outputs=('electricity',),
  
      # Note how the flow rates are explicitly stated..
      flow_rates={'electricity': nts.MinMax(min=1, max=2)},
      flow_costs={'electricity': 2, },

      # .. while making it expandable
      expandable={'electricity': True},
      expansion_costs={'electricity': 1},
        
      # not stating the expansion limits results to min=0, max=float('+inf')
      # note how this is commented out to emulate not explicity stating it:
      # expansion_limits={'electricity': nts.MinMax(min=1, max=4)},
  )
    
Problematic Example
^^^^^^^^^^^^^^^^^^^
If the ``flow_rates`` are not stated specifically, the are set to a default of ``min=0`` and  ``max=float('+inf')``. Making it expandable also, may lead to :ref:`Models_Oemof` beeing confused. For assiting you in debugging however tessif logs a warning which helps you identify the component and issue::

  # capped source having no costs, no emission, no flow constraints
  # but existing and max installed capacity (for expansion) as well
  # as expansion costs
  capped_renewable = components.Source(
      name='Capped Renewable',
      outputs=('electricity',),
  
      # Note how the flow rates are not explicitly stated..
      # flow_rates={'electricity': nts.MinMax(min=1, max=2)},
      flow_costs={'electricity': 2, },

      # .. while making it expandable
      # which will log a warning and probably lead to oemof not beeing able
      # to optmize the energy system.
      expandable={'electricity': True},
      expansion_costs={'electricity': 1},
        
      # not stating the expansion limits results to min=0, max=float('+inf')
      # note how this is commented out to emulate not explicity stating it:
      # expansion_limits={'electricity': nts.MinMax(min=1, max=4)},
  )

.. _Usage_Comparing_Hooks:

Hooking into the energy system prior to simulation
**************************************************
Tessif provides powerfull :mod:`hooks <tessif.frused.hooks>` of various capabilities. One of the most usefull hook when doing a comparison, is the :attr:`reparameterize hook <tessif.frused.hooks.tsf.reparameterize_components>` It creates a new energy system out of the existing one while changing arbitrary parameters of arbitrary components. (Refer to :attr:`it's documentation <tessif.frused.hooks.tsf.reparameterize_components>` on how to use it syntactically correct.)

Parameterization Contradiction
------------------------------
Hooking into the tessif energy system prior to simulation to change key components enables the user to use the same underlying, stored and/or hardcoded energy system for multiple :ref:`SupportedModels` smoothing out any parameterization contradictions.


Examples
^^^^^^^^
Following sections provide examples on how to hook into the energy system prior to simulation to archieve certain results. Mostly emission constraints beeing met.

Combined Heat and Power Plant Example
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
A basic example can found in :ref:`auto comparison of the brief combined heat and power example <AutoCompare_CHP>`. This example constructs a simple chp providing inexpensive heat and power for a respective heat and power grid, of which each is backed up by a more expensive energy source. The chp however has emissions allocated to its electrical and thermal power outflow. This poses a real challenge to :ref:`Models_Pypsa` since the underlying component does not support binding energy carriers to it, which in turn are necessary for :ref:`Models_Pypsa` to respect the stated constraints.

In its basic simulation, emissions are unconstrained, and hence the chp runs at :ref:`max power capacity <AutoCompare_CHP_Unconstrained_Loads>`. Results in :ref:`160 <AutoCompare_CHP_Unconstrained_Results>` units emitted.

For the :ref:`second run <AutoCompare_CHP_Constrained>` however, emissions are constrained to 100 units. Leading the chp to :ref:`only cover the electricity demand in partial <AutoCompare_CHP_Constrained_Loads>`. So the overall emission constrained can be :ref:`met <AutoCompare_CHP_Constrained_Results>`. This is archieved by hooking into the tessif energy system pypsa uses, prior to simulation. The repsective code snippet is as follows::

  import functools
  from tessif.frused.hooks.tsf import reparameterize_components

  comparatier = tessif.analyze.Comparatier(
      path=os.path.join(write_dir, 'tsf', 'constrained_chp_example.hdf5'),
      parser=tessif.parse.hdf5,
      models=('oemof', 'pypsa'),
      hooks={
          'pypsa': functools.partial(
              reparameterize_components,
              components={
                  'CHP': {
                      'flow_emissions': {'electricity': 0, 'heat': 0, 'gas': 0},
                  },
                  'Gas Source': {
                      'flow_emissions': {'gas': 2*0.3+3*0.2},
                  },
              }
          )
      },
  )



Hamburg Energy System
<<<<<<<<<<<<<<<<<<<<<

A prominent use case of that can be observed in the :ref:`auto comparison of the hamburg energy system <AutoCompare_HH>`. The multitude of combined heat and power plants (CHPs) in combination with using :ref:`Models_Oemof` and :ref:`Models_Pypsa`, leads to contradicting co2-emissions parameterization:

:ref:`Models_Pypsa` CHPs do not respect outflow allocated co2-emissions correctly, hence allocating them to their energy source seems logical. Singular output power plants like a regular coal fired power plant however will be seperated from its energy source when using :ref:`Models_Pypsa` so it's co2-emissions have to be allocated to the component itself. This however would lead the :ref:`Models_Oemof` power plants to have the emissions allocated twice, one occurence at the energy source and another one at the plant itself. There are many workounds for this particular contradiction. A convenient one though is to use the befornamed hook and just delete the :ref:`Models_Oemof` power plant allocated emissions.
     
For the complete syntax of this, see the :ref:`auto comparison example <AutoCompare_HH>`. The part where the hook is formulated can bee seen here::

  import functools
  from tessif.frused.hooks.tsf import reparameterize_components

  comparatier = tessif.analyze.Comparatier(
      path=os.path.join(write_dir, 'tsf', 'hhes_comparison.hdf5'),
      parser=tessif.parse.hdf5,
      models=('oemof', 'pypsa'),
      hooks={
          'oemof': functools.partial(
              reparameterize_components,
              components={
                  'pp1': {
                      'flow_emissions': {'electricity': 0, 'coal': 0},
                  },
                  'pp2': {
                      'flow_emissions': {'electricity': 0, 'coal': 0},
                  },
              }
          )
      },
  )
