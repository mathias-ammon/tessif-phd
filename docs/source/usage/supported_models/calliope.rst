.. _Models_Calliope:

********
Calliope
********

Following sections give detailed instructions on how to create ready-to-use
energy systems using :class:`calliope.core.model.Model` objects.

.. contents:: Contents
   :local:
   :backlinks: top


Concept
*******
`Calliope <https://www.callio.pe/>`_ aims to be a free and open source framework
for energy system modelling and optimization. It is being developed on
`GitHub <https://github.com/calliope-project/calliope>`_.

Calliope consists of a `pyomo interface <https://www.pyomo.org/>`_
for modelling energy supply system components using linear and mixed integer linear problem formulation.
By providing a very general approach (`calliope components <https://calliope.readthedocs.io/en/stable/user/config_defaults.html#abstract-base-technology-groups>`_)
:mod:`Calliope` tries to satisfy the most common use cases.

Unlike FINE, Oemof and PyPSA a Calliope model data is going to be stored
in .yaml and .csv files. Alternatively these data can be read from python dictionaries
and pandas dataframes, but in :mod:`Tessif` yaml and csv files are going to be used,
since calliope refers to the easier human readability of the yaml files,
A comparatively small :mod:`py_hard <tessif.examples.data.calliope.py_hard>`
does exist though.

Purpose
*******
Within the context of :mod:`Tessif`, :mod:`Calliope` serves
another pyomo solver interface with the goal to optimize the system for the
minimum costs. :mod:`Calliope` could do an emission minimization as well, but in :mod:`Tessif`
emissions are only constraint by a maximum allowed, while minimum costs are the target.



Using :mod:`Calliope` through :mod:`Tessif` is somewhat of a challenge since the
parameterization on some components differ quite a lot and others might
not even be included in :mod:`Calliope`. Nevertheless there are still enough
components with a similar to same parameterization to transform a :class:`Tessif's Energy System
<tessif.model.energy_system.AbstractEnergySystem>` into a :class:`calliope.core.model.Model`.

USP
***
:mod:`Calliope` provides one feature that is not included in :mod:`Tessif`
but has to be mentioned here as a unique selling point. This is the so called
`Spores mode <https://calliope.readthedocs.io/en/stable/user/advanced_features.html#spores-mode>`_
which allows to calculate alternative results that are more expensive than the optimal result
(the allowed cost range is user defined relatively to optimum) but differ in usage of technologies
and therefore might present an interesting result fitting with socially or politically issues
that are not represented inside the model parameters.

Examples
********
               
.. _Models_Calliope_Examples_Mwe:

Minimum Working Example
=======================

1. Create the model.yaml which is going to be called to build the energy system model

.. code-block:: yaml

   import:
     - mwe_config/locations.yaml
     - mwe_config/techs.yaml

   model:
     name: Minimum_Working_Example
     calliope_version: 0.6.6-post1
     timeseries_data_path: mwe_data
     subset_time:
     - '1990-07-13 00:00:00'
     - '1990-07-13 03:00:00'

   run:
     solver: cbc
     cyclic_storage: false
     objective_options.cost_class:
       monetary: 1

2. Create the model_config/techs.yaml file holding the technology information.

.. code-block:: yaml

    techs:

      # build a demand
      # NOTE: Can't be named demand due to the name being blocked by its parent.
      # Thus it is going to be renamed using the carrier.
      electricity_Demand:
        essentials:
          name: Demand
          parent: demand
          carrier: electricity
        constraints:
          energy_con: true
          resource_unit: energy
          resource: file=electricity_Demand.csv:electricity_Demand
          force_resource: true

      Gas Station:
        essentials:
          name: Gas Station
          parent: supply
          carrier_out: fuel
        constraints:
          resource: .inf
          energy_ramping: true

      Generator:
        essentials:
          name: Generator
          parent: conversion
          carrier_in: fuel
          carrier_out: electricity
        constraints:
          energy_eff: 0.42
          energy_ramping: true
        costs:
          monetary:
            om_prod: 2

      Battery:
        essentials:
          name: Battery
          parent: storage
          carrier: electricity
        constraints:
          storage_cap_max: 20
          energy_cap_min: 20
          energy_cap_max: 20
          energy_ramping: true
          storage_cap_min: 20
          storage_initial: 0.5
        costs:
          monetary:
            om_prod: 0.1

      fuel transmission:
        essentials:
          name: fuel transmission
          parent: transmission
          carrier: fuel
        constraints:
          one_way: true

      electricity transmission:
        essentials:
          name: electricity transmission
          parent: transmission
          carrier: electricity
        constraints:
          one_way: true


3. Create the model_config/locations.yaml file holding the locations information.
   Each technology is going to be called in a separated location. This way calliope
   can be used with tessif energy systems and post processing.

.. code-block:: yaml

    locations:

      Pipeline:
        coordinates: {lat: 0.0, lon: 0.0}

      Powerline:
        coordinates: {lat: 0.0, lon: 0.0}

      electricity_Demand location:
        coordinates: {lat: 0.0, lon: 0.0}
        techs:
          electricity_Demand:

      Gas Station location:
        coordinates: {lat: 0.0, lon: 0.0}
        techs:
          Gas Station:

      Generator location:
        coordinates: {lat: 0.0, lon: 0.0}
        techs:
          Generator:

      Battery location:
        coordinates: {lat: 0.0, lon: 0.0}
        techs:
          Battery:

    # links do connect the different locations using a transmission technology
    links:

      Gas Station location,Pipeline:
        techs:
          fuel transmission:
            constraints:
              one_way: true

      Pipeline,Generator location:
        techs:
          fuel transmission:
            constraints:
              one_way: true

      Battery location,Powerline:
        techs:
          electricity transmission:
            constraints:
              one_way: false

      Generator location,Powerline:
        techs:
          electricity transmission:
            constraints:
              one_way: true

      Powerline,electricity_Demand location:
        techs:
          electricity transmission:
            constraints:
              one_way: true

.. note::
   The presented example yaml files are identical to those in tessif\examples\data\calliope\mwe.
..

4. Save the timeseries data in a .csv file. From this point on python is going to be used.

.. code-block:: python

    import pandas as pd
    import numpy as np
    from tessif.frused.paths import example_dir

    simulation_time = pd.date_range(
    '7/13/1990', periods=4, freq='H')

    demand_timeseries = np.array(4*[-10])

    demand_timeseries = pd.DataFrame({'': simulation_time, 'electricity_Demand': demand_timeseries})

    # commented out for better doctesting
    # timeseries.to_csv(
    #     os.path.join(
    #         example_dir, 'data', 'calliope', 'timeseries_data', f'mwe_electricity_Demand.csv'), index=False)


.. note::
   Each Calliope model needs at least one timeseries.
..

5. Build and optimize the model.

    >>> from tessif.frused.paths import example_dir
    >>> import calliope

    >>> es = calliope.Model(f'{example_dir}/data/calliope/mwe/model.yaml')
    >>> es.run()

6. Confirm the expected output.

   >>> for loc in sorted(es.inputs.locs.data):
   ...     print(loc)
   Battery location
   Gas Station location
   Generator location
   Pipeline
   Powerline
   electricity_Demand location

   >>> for tech in sorted(es.inputs.techs.data):
   ...     print(tech)
   Battery
   Gas Station
   Generator
   electricity transmission
   electricity_Demand
   fuel transmission

7. For examples on how to extract result information out ouf the optimized
energy system using tessif, see :mod:`tessif.transform.es2mapping.cllp`
