.. _Introduction:

************
Introduction
************

Tessif can be comprehended much like a toolbox designed for handling :ref:`energy system simulation <Introduction_FirstSteps_EnergySupplySystemsSimulation>` tasks. Each tool (corresponding to tessif's :ref:`toplevel submodules and subpackages <api>`) serves a specific task. While these tasks may vary a lot between tools (e.g. like they do for a saw and a pencil) it still makes sense to understand both: how each tool works on its own and to how they synergize with each other. Reusing the toolbox example this transtales to understanding how different saws and pencils work on their own, but also how to draw lines on workpieces you want to cut to length.


Following sections give a detailed guide line on how to approach tessif as a project.

.. contents::
   :local:

.. _Introduction_Goals:

Goals
*****
Tessif aims to be an easy to use energy system simulations handling tool. It tries to present a consice and uniform interface to numerous free open source energy system simulation tools. This serves two main purposes:

  1. Lowering the threshold for engineers to use free and open source energy system simulation tools, by using multiple tools through one interface.

  2. Conveniently allow comparing multiple tools to find out which tools may be suited best for a certain application and or what range of results is to be expected by using different tools.


.. _Introduction_Purpose:

Purpose
*******
There are numerous free open source energy supply system simulation frameworks available today that are written in python:

   - pypsa (`homepage <https://pypsa.org/>`_ , `code_repository <https://github.com/PyPSA/PyPSA>`_, `paper <http://openresearchsoftware.metajnl.com/articles/10.5334/jors.188/galley/289/download/>`_)
   - oemof (`homepage <https://oemof.org/>`__, `code_repositories <https://github.com/oemof>`_, `paper <https://www.preprints.org/manuscript/201706.0093/v2/download>`__)
   - | urbs (`reference page <https://wiki.openmod-initiative.org/wiki/URBS>`_, `code_repository <https://github.com/tum-ens/urbs>`__, `paper <http://dx.doi.org/10.1016/j.esr.2020.100486>`__)     
     | rivus (`code_repository <https://github.com/tum-ens/rivus>`__, `presentation <http://mediatum.ub.tum.de/doc/1296524/6085207224.pdf>`_)

These modeling frameworks allow the virtual simulation and modeling of energy supply systems. Each framework is or was under development by different organisations or groups of people. During the major concept phase of these tools there was little to no coordination between developers. Leading to various potentially redundant functionalities as well as data parsing overhead when trying to solve the same problem using different tools. To counteract this the `open_MODEX <https://reiner-lemoine-institut.de/open_modex/>`_ project was initiated with the goal to find and utilize potential `synergies <https://www.isea.rwth-aachen.de/cms/ISEA/Die-Organisationseinheit/Neuigkeiten/~xexj/open-MODEX-Open-Source-Forschungsprojek/>`_.
While this will help researchers to find out which tool or even which set of tools might be best for which task it somewhat fails to address the core issues when trying to use more than just one of these tools:

   1. No common data input:

      Each framework uses its own model(s) expecting specifically tailored datasets. This of course stems from the fact that each model specialises in different aspects of energy supply system simulation.

   2. No common data output:

      Although any energy supply system might be considered as a `graph <https://en.wikipedia.org/wiki/Graph_theory>`_ there is yet no universally applicable graph like representation among the models.
      
      (`PyPSA utilizes a graph <https://github.com/PyPSA/PyPSA/blob/master/pypsa/graph.py>`__ constructed out of its own data set and `oemof only uses <https://github.com/oemof/oemof.network/blob/dev/src/oemof/network/graph.py>`_  it for a simplay it had one until version 0.3.2)

      Apart from load data analysis which can be considered an essential in energy system engineering there is no common post processing and especially no common, abstract data representation present among the models.

Making the comparision between models so difficult an entire research project (`open_MODEX <https://reiner-lemoine-institut.de/open_modex/>`_) had to be deployed.

Tessif tries to help the free open source energy supply system simulation community by addressing the beforenamed issues in order to advance open research and thus accumulating easy accessible knowledge for ultimately managing the "Energiewende" succesfully.

.. _Introduction_Questions:

Question Tessif Helps to Answer
*******************************
As laid out in :ref:`Introduction_Goals` and :ref:`Models_Tessif_Purpose`
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
      
.. _Introduction_Structure:

Structure
*********

Tessif has 4 main functionality clusters:

    - 1. :mod:`Parse<tessif.parse>`/:mod:`Write<tessif.write>` - Tesssif strives
      to be able to read and write all commonly used data formats for
      representing energy systems.
      
    - 2. :mod:`Simulate<tessif.simulate>` - Tessif provides simple simulation
      wrappers to demonstrate how the supported simulation tools expect to be
      used and to generate a minimum working example. This offers great bug
      fixing and doctesting capabilites. It also allows for a powerfull in-depth,
      low-hassle comparision between enrgy system simulation models.
      
    - 3. :mod:`Transform<tessif.transform>` - Tessif transforms all data sets to
      :class:`collections.Mapping` objects of different flavors. This allows for
      rapid and robust data conversions depending on the task. Crazy things like
      reading in json data, simulating them with one tool, generating an energy
      system mapping for another tool and writing that back to disk become
      simple API call chains with tessif. Adding entries to the list of supported
      energy system simulation tools is straight forward, well documented and
      examplified. Go add data crunchers for the tool you've written (which you
      have done anyways cause somehow you need to acces this tool) and take
      advantage of what tessif has to offer!
      
    - 4. :mod:`Visualize<tessif.visualize>` - Since transforming is what tessif
      is all about, transforming energy system data sets to be understandable
      for visualizing tools is a breeze. There are already a lot of built in
      visualizing modules, but there is of course no limit in what can be done.
      Expanding what is already there is simple and well documented.

      
As well as following support structures:

    - 5. :mod:`Examples <tessif.examples>` - An example hub to quickly tryout,
      debug and reuse simulation cases.

    - 6. :mod:`Model <tessif.model>` - It's own data structure and solver
      interface for quickly transforming data between energy system simulation tools
      as well as providing an interface engineered for engineers.

    - 7. :mod:`Frused <tesssif.frused>` - All of tessif's presets as well as
      it's capabilities to understand a variety of different kinds of input.

First Steps
***********
Following sections provide a recommended approach to familiarize oneself with tessif.


.. _Introduction_FirstSteps_EnergySupplySystemsSimulation:

Energy Supply Systems Simulations
---------------------------------

Understanding the topic of simulating energy supply systems is the most logical first step.
There are a lot of kinds of energy systems. Hence there are also many different energy system simulation tools. Those mostly vary in detail, scope and focus of application. To understand the concept of tessif it helps to understand tessif's approach on energy supply systems.

.. _Introduction_FirstSteps_EnergySupplySystemsSimulation_TessifsInterpretation:

Tessif's Interpretation
^^^^^^^^^^^^^^^^^^^^^^^
In the context of tessif, an energy supply system is seen as a `graph <https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)>`__. Meaning it consists of nodes and directed edges,where nodes represent abstract or generic :ref:`energy system components <Models_Tessif_Concept_ESC>` (like a powerplant, a storage unit, a houshold demanding electricity, ...) and are characterized by a certain amount of fixed parameters describing these components. Whereas the edges are representing flows between those components. In general these flows are intepreted as energy flows, but that is not enforced and could be seen as any kind of flow. For a more detailed description on the components and their possible edges, please refer to the :ref:`technical documentation of tessif's energy system model <Models_Tessif>`

.. figure:: images/6n-graph.png
   :align: center
   :alt: Image showing a 6-Node, 7-Edge Graph; Taken from Wikipedia
   :scale: 80 %
           
   A 6-Node, 7-Edge Graph; Taken from `Wikipedia <https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)>`__   

This general approach implies, that tessif is suited best for modelling medium to large scale energy systems on a flow based description. Which is also what tessif's currently underlying :ref:`simulation models <SupportedModels>` are suited best for. Possible applications would range from optimizing a singular house hold's energy system up to something like the integrated European network.

.. figure:: ../usage/images/hhes_graph.png
   :align: center
   :alt: Image showing the hhes example es graph
   :scale: 40 %
           
   The visualized energy system, taken from the :ref:`Hamburg Energy System Example <AutoCompare_HH>`
   
On the most (sensible) level of detail, singular participants are represented by an individual node, like a power plant, a solar panel, a battery electric vehicle, etc. On the other end of scale it is also possible aggregating multiple individual participants into a single component, like for example the aggrgation of all german hard coal fired power plants into a single component (node). Which is a common technique in energy supply system simulations.

Although possible, it does not really make sense, to model complex electromechanical systems, like i.e. a micro-chp. Because the currently :ref:`SupportedModels` (which are actually conducting the optimization) are not made for this.

Optimization in this context usually means trying to anwer one or both of the following questions:

  1. Which of the available and controllable components is used when and how much to fullfill a certain amount of energy demand, while minimizing costs and respecting component and energy transportation constraints as well as potential secondary objectives like an emission-goal? These kind of problems are roughly desribed as `unit commitment problem <https://en.wikipedia.org/wiki/Unit_commitment_problem_in_electrical_power_production>`_ or short ``commitment problem``.

  2. Which of the available or new components have to be expanded to reach certain secondary objectives like an emission goal, whil minimizing the costs to do so, as well as respecting given component and transportation constraints, while still meeting all the energy demands? These kind of problems can described as `expansion planning <https://en.wikipedia.org/wiki/Generation_expansion_planning>`_ or ``expansion problem``.

For additional information on typical use cases of energy supply system simulations see the guide on :ref:`Visualization`. The use cases are discussed there, showing the python code (using tessif) with which they were created as well as how their results can be visualized (again using tessif). A brief exaplanation on how and why those topics are of interest preceeds each of the use cases.

As mentioned in :ref:`the section describing tessif's purpose <Introduction_Purpose>`, tessif itself actually focuses on creating a framework (much like a common ground), rather than on energy supply system simulations themselves. It's main focus lies on data in- and output unifications as well as data transformation, to provide a unifrom, powerfull and engineer's friendly interface to conduct energy supply system simulation and :ref:`compare <Comparison>` popular free open source models addressing this task. For more details, on data handling, please refer to the user guide (see navigation bar to the left).

Further Readings
^^^^^^^^^^^^^^^^
Apart from the approach desribed :ref:`above <Introduction_FirstSteps_EnergySupplySystemsSimulation_TessifsInterpretation>`, there are of course a lot of different takes on this topic. To deepen the understanding of tessif's interpretation, as well so to distinguish it from others, a small collection of valuable readings is listed below:

- The `Wikipedia Arcticle <https://en.wikipedia.org/wiki/Energy_modeling>`_
- `PyPSA's approach <https://pypsa.readthedocs.io/en/latest/index.html>`_
- Oemofs scientific
  `abstract <https://www.sciencedirect.com/science/article/pii/S2211467X18300609>`_
- One of oemofs scientific
  `use case example <https://www.mdpi.com/1996-1073/12/22/4298/htm>`_
- Very basic understanding of
  `energy forms and transformation <https://phet.colorado.edu/sims/html/energy-forms-and-changes/latest/energy-forms-and-changes_de.html>`_
- ESI ITI GmbH's
  `explanation <https://www.simulationx.com/industries/applications/energy-systems.html>`_

Code Base
---------
Given a basic comprehension of energy supply system simulations it is recommended
to start exploring tessif's code base. A sensible approach can be:

   1. Not getting overwhelmed by a flull fledged code base
   2. Learning about tessif's workhorses, it's :ref:`SupportedModels`

      a. Starting out with :ref:`Models_Tessif`
      b. Continuing with :ref:`Models_Oemof`


Examples
--------
Given a rudimentary understanding of tessif's code base, it is advised to examine
the different kinds of :ref:`Examples`.


*One Button to Push* Simulations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Tessif incorporates a :mod:`tessif.simulate` module for  wrapping everything
needed for successfull simulations. It's an advisable first coding step to
create a seperate file, importing one of these wrappers and excecuting it.

Data Inputs
^^^^^^^^^^^
Tessif supports a wide range of different data formats. To find, understand
and use one for a chosen task :mod:`tessif.examples.data` can be referred to.

Data Transformations
^^^^^^^^^^^^^^^^^^^^
Tessif supports various free open source energy supply system simulation models.
(:ref:`list of supported models <SupportedModels>`) To understand how tessif
feeds in data to it's supported models it is recommended to look at the
:ref:`User Guide for Transformation <Transformation>` and for more in depth
development info at one of the examples found in
:mod:`tessif.examples.transformation`.
              
Applications
^^^^^^^^^^^^
Real use case applications of utilizing tessif from data read in to visualizing
the output can be found in :mod:`tessif.examples.application`.
