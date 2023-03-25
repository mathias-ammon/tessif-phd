.. _Models_Oemof:

*****
Oemof
*****

Following sections give detailed instructions on how to create ready-to-use
energy systems using :class:`oemof.core.energy_system.EnergySystem` objects.

.. contents:: Contents
   :local:
   :backlinks: top


Concept
*******
`Oemof <https://oemof.org/>`_ aims to be a community driven open science project
for enhancing energy system modelling. It consists of several open source
`repositories <https://github.com/oemof>`_ to model different aspects
of energy supply systems as well as `efforts <https://github.com/oemof/oemof>`_
for organising it's community.

At it's simulativ core oemof consists of a `pyomo interface <https://www.pyomo.org/>`_ (the `omeof.solph <https://github.com/oemof/oemof-solph>`_ package) for modelling energy supply system components using linear and mixed integer linear problem formulation. By providing a very general approach (`oemof.solph.components <https://oemof-solph.readthedocs.io/en/latest/reference/oemof.solph.html#module-oemof.solph.components>`_) as well as customized, specific models (`omeof.solph.custom <https://oemof-solph.readthedocs.io/en/latest/reference/oemof.solph.html#module-oemof.solph.custom>`_), :mod:`oemof.solph` tries to satisfy the most common use cases.

Apart from it's optimization core there exist several major helper libraries for providing:

   - Renewable feed-in data (`oemof.feedinlib <https://feedinlib.readthedocs.io/en/stable/>`_)
   - Demand and Output data for themal components (`oemof-thermal <https://oemof-thermal.readthedocs.io/en/latest/>`_)
   - Specific parameters for thermal applications (`tespy <https://tespy.readthedocs.io/en/master/>`_)
     
As well as a variety of extensions and small additional packages, all accessible via the main `repository <https://github.com/oemof>`_
    

Purpose
*******
Within the context of tessif, oemof solves primarily as another pyomo interface allowing most of :mod:`tessif's energy system model <tessif.model.energy_system>` to be directly transformed without major data loss, In fact tessif's general approach to energy system simulation was inspired by oemof. While oemof's human-interface for parameterizing components as well as extracting results tends to be tailored more towards people comfortable with programing, tessif aim's to provide an interface for engineers.


Examples
********
               
.. _Models_Oemof_Examples_Mwe:

Minimum Working Example
=======================

.. note::
   The exact same energy system can be accessed using
   :meth:`tessif.examples.data.omf.py_hard.create_mwe`.

1. Import everything necessary::

    from oemof import solph
    import pandas as pd
    from tessif.frused import namedtuples as nts

2. Create a simulation time frame of of 2 one hour timesteps as a
   :class:`pandas.DatetimeIndex`::

    simulation_time = pd.date_range(
        '7/13/1990', periods=2, freq='H')

3. Initialize an :class:`~oemof.core.energy_system.EnergySystem` object
   using the freshly generated :class:`pandas.DatetimeIndex`::

    es = solph.EnergySystem(timeindex=simulation_time)

4. Create oemof specific :class:`nodes <oemof.network.Node>`
   for a simple energy system consisting of:

   - A **Powerline** (:class:`~oemof.solph.network.Bus` object)::

      power_line = solph.Bus(
          label=nts.Uid(
              'Power Line', 53, 10, 'Germany',
              'Power', 'Electricity'))

   - A **Demand** of 10 energy units (
     :class:`~oemof.solph.network.Sink` object)::

      demand = solph.Sink(
          label=nts.Uid(
              'Demand', 53, 10, 'Germany',
              'Power', 'Electricity'),
          inputs={power_line: solph.Flow(
              nominal_value=10, fix=[1,1])})

   - A **Renewable** source feeding 8 and 2 energy units (
     :class:`~oemof.solph.network.Source` object)::

      renewable = solph.Source(
          label=nts.Uid(
              'Renewable', 53, 10, 'Germany',
              'Power', 'Electricity'),
          outputs={power_line: solph.Flow(
          nominal_value=10, fix=[0.8, 0.2], variable_costs=9)})

   - A **Distribution Network** of Chemically Bound Energy Carriers::

      cbet = solph.Bus(
          label=nts.Uid(
              'CBET', 53, 10, 'Germany',
              'Power', 'Electricity'))

   - A **Chemically Bound Energy Source** (
     :class:`~oemof.solph.network.Bus` object)::

      cbe = solph.Source(
          label=nts.Uid(
              'CBE', 53, 10, 'Germany',
              'Power', 'Electricity'),
          outputs={cbet: solph.Flow()})

   - A **Conventional Transformer** producting up to 10 energy units
     costing 10 per unit (:class:`~oemof.solph.network.Transformer` object)::

      conventional = solph.Transformer(
          label=nts.Uid(
              'Transformer', 53, 10, 'Germany',
              'Power', 'Electricity'),
          inputs={cbet: solph.Flow()},
          outputs={power_line: solph.Flow(
              nominal_value=10, variable_costs=10)},
          converstion_factors={power_line: 0.6})

5. :meth:`~oemof.core.energy_system.EnergySystem.add` nodes to the
   :class:`~oemof.core.energy_system.EnergySystem` object::

    es.add(power_line, demand, renewable,
           cbet, cbe, conventional)

6. Create an energy system :class:`~oemof.solph.models.Model` object::

    esm = solph.Model(es)

7. :meth:`~oemof.solph.models.BaseModel.solve` the
   :class:`~oemof.solph.models.Model` object::

    solver_msg = esm.solve(solver='glpk')

   .. _omf_results:

8. Pump :attr:`~oemof.core.energy_system.EnergySystem.results` into the
   :class:`~oemof.core.energy_system.EnergySystem`
   object to utilize its :meth:`~oemof.core.energy_system.EnergySystem.dump`
   functionality for saving the data::

    es.results['main'] = solph.processing.results(esm)
    es.results['meta'] = solph.processing.meta_results(esm)


9. Get tessifs installation path to dump the results in
   tessif/tessif/write/omf/dummies

   (path getting is quite hacky here. Done in this way to enable
   doctesting from all kind of crazy locations.)

   >>> from tessif.frused.paths import write_dir
   >>> import os
   >>> import pathlib
   >>> dpath = os.path.join(write_dir, 'omf')
   >>> pathlib.Path(dpath).mkdir(parents=True, exist_ok=True)

10. Store :attr:`~oemof.core.energy_system.EnergySystem.results` pumped
    :class:`~oemof.core.energy_system.EnergySystem` object::

     dump_msg = es.dump(dpath=dpath, filename='mwe.oemof')

    
11. Using this newly generated energy system in a different python context by
    importing it.
   
.. note::
   The code of steps 1 to 10 is wrapped in a
   :meth:`~tessif.examples.data.omf.py_hard.create_mwe` function for
   convenience meaning it is copy pastable.

..


  a. Import the wrapper functionality:

     >>> from tessif.examples.data.omf.py_hard import create_mwe
     >>> esys = create_mwe(directory=dpath, filename='mwe.oemof')

  b. Confirm the expected output:

     >>> for node in esys.nodes:
     ...     print(node.label.name)       
     Power Line
     Demand
     Renewable
     CBET
     CBE
     Transformer

12. For examples on how to extract result information out ouf the optimized
    energy system using tessif, see :mod:`tessif.transform.es2mapping.omf`
