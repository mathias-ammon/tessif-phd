.. _Models_Pypsa:

*****
PyPSA
*****

Following sections give detailed instructions on how to create ready-to-use
energy systems using :class:`pypsa.Network` objects.

.. contents:: Contents
   :local:
   :backlinks: top


Concept
*******
`PyPSA <https://pypsa.org/#sec-1>`__ aims to be a free software toolbox
simulating and optimizing energy supply systems with the focus on electrical
power flow expecially on large scale networks and timeframes.

It is developed by a small, dedicated development team formerly at the
`Frankfurt Institute for Advanced Studies (FIAS, german)
<https://fias.news/aktuelles/forschung-zu-energienetzwerken/>`_ now at the
`Karlsruhe Institut of Technologie (KIT)
<https://www.iai.kit.edu/english/esm.php>`_. 

It does NOT try to be as open as possible in the sense of making it easy for
the community to take part in developing. Meaning there is no dedicated
``Development`` section inside `PyPSA's docuemntation
<https://pypsa.readthedocs.io/en/latest/index.html>`_ (although a very small
`Contributing <https://pypsa.readthedocs.io/en/latest/contributing.html>`_
entry exists, ''Welcoming anyone interested in contributing to this project'')
and there is API style documentation like in :ref:`Tessif <api>` or `Oemof
<https://oemof-solph.readthedocs.io/en/latest/reference/oemof.solph.html>`__.
    

Purpose
*******
Within the context of tessif, `PyPSA <https://pypsa.org/>`_ serves as yet
another pyomo solver interface but with a focus on electrical energy flows,
respecting electrical constraints like direct or alternating current, voltage
angles and magnitudes and more.

`PyPSA <https://pypsa.org/>`_ also allows optimizing an energy system using their own optimizer which supposedly works much faster and needs much less memory (see :meth:`pypsa.Network.lopf`; Parameter ``pyomo``).

Using `PyPSA <https://pypsa.org/>`_ through tessif is somewhat of a challenge
especially regarding specific electrical constraints. Since `PyPSA
<https://pypsa.org/>`_ was not build to be hackable/accessible via other
interfaces like i.e `Oemof <https://oemof.org/>`_ or :mod:`Tessif
<tessif.model.energy_system>` are, but rather focuses on tabular interfaces, direct
use and low overhead.

Specialized problem constraints (like the beforenamed elictrical constraints) however, will be implemented in the near future through :ref:`tessif's energy system components <Models_Tessif_Concept_ESC>`. The respective parameters will be marked and it will be stated which models can make use of them.


Examples
********
               
.. _Models_Pypsa_Examples_Mwe:

Minimum Working Example
=======================

.. note::
   The exaxt same energy system can be accessed using
   :meth:`tessif.examples.data.pypsa.py_hard.create_mwe`.

1. Import the needed packages::

    # standard library
    import os
    import pathlib

    # third pary
    import pypsa

    # local
    import tessif.frused.namedtuples as nts
    from tessif.frused.paths import write_dir
    import tessif.write.tools as write_tools

2. Create a simulation time frame of two timesteps (`PyPSA assumes hourly resolution by default
   <https://pypsa.readthedocs.io/en/latest/design.html#unit-conventions>`_,
   altough it actually only cares about the number of timesteps not about their
   difference in real-time)::

    timesteps = range(2)

3. Create an energy system / network object::
     
    es = pypsa.Network()

   - Enforce the number of timesteps::
     
      es.set_snapshots(timesteps)

   - Add the main power bus :class:`~tessif.frused.namedtuples.Uid` for
     utilizing :ref:`Tessif's Labeling Concept <Labeling_Concept>`::

        power_bus_uid = nts.Uid(
            name='Power Line', latitude=53, longitude=10,
            region='Germany', sector='Power', carrier='Electricity',
            component='Bus', node_type='AC_Bus')

   - Add a :class:`Bus <https://pypsa.readthedocs.io/en/latest/components.html#bus>`
     as ideal power line::
         
        es.add(class_name='Bus',
            # tessif's uid representation
            name=power_bus_uid,
            # pypsa's representation:
            x=10, y=53, carrier='AC'
            )

    - Add a :class:`Demand <https://pypsa.readthedocs.io/en/latest/components.html#load>`
      needing 10 energy units per timestep::
      
         es.add(class_name='Load',
             bus=str(power_bus_uid),
             name=nts.Uid(
                 name='Demand', latitude=53, longitude=10,
                 region='Germany', sector='Power', carrier='Electricity',
                 component='Sink', node_type='AC_Sink'),
             p_set=10,
           )

    - Add a renewable :class:`source <https://pypsa.readthedocs.io/en/latest/components.html#generator>`
       producing 8 and 2 energy units with a cost of 9::

         es.add(class_name='Generator',
             bus=str(power_bus_uid),
             name=nts.Uid(
                 name='Renewable', latitude=53, longitude=10,
                 region='Germany', sector='Power', carrier='Electricity',
                 component='Source', node_type='AC_Source'),
             p_nom=10, p_max_pu=[0.8, 0.2], marginal_cost=9
           )

    - Add a conventional engergy :class:`transformer
      <https://pypsa.readthedocs.io/en/latest/components.html#generator>`
      producing up to 10 energy units for a cost of 10::
    
         es.add(
             class_name='Generator',
             bus=str(power_bus_uid),
             name=nts.Uid(
                 name='Gas Generator', latitude=53, longitude=10,
                 region='Germany', sector='Power', carrier='gas',
                 component='Transformer', node_type='gas_powerplant'),
             p_nom=10, marginal_cost=10)

4. Optimize model::

    es.lopf()

5. Store the energy system into ``tessif/src/tessf/write/pypsa/mwe``::
       
    import os
    import pathlib

    from tessif.frused.paths import write_dir
       
    d = os.path.join(write_dir, 'pypsa', 'mwe')
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)
    es.export_to_csv_folder(d)
         


6. Using this newly generated energy system in a different python context by
   importing it:
   
.. note::
   The code of steps 1 to 5 is wrapped in a
   :meth:`~tessif.examples.data.pypsa.py_hard.create_mwe` function for
   convenience meaning it is copy pastable.

..


  a. Import the wrapper functionality:

     >>> from tessif.examples.data.pypsa.py_hard import create_mwe
     >>> esys = create_mwe()

  b. Confirm the expected output:

     >>> pypsa_nodes = [
     ...     *esys.buses.index,
     ...     *esys.generators.index,
     ...     *esys.lines.index,
     ...     *esys.links.index,
     ...     *esys.loads.index,
     ...     *esys.storage_units.index,
     ...     *esys.stores.index,
     ... ]
     >>> for node in pypsa_nodes:
     ...     print(node)
     Power Line
     Renewable
     Gas Generator
     Demand

7. For examples on how to extract result information out ouf the optimized
   energy system using tessif, see :mod:`tessif.transform.es2mapping.pypsa`     
