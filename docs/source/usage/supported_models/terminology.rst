.. _Model_Terminology:

Model Terminology
=================

Goal of this section is to disambiguate the term ``Model``.

In the context of :mod:`Tessif <tessif>`, the term ``Model`` is used to
describe an ``Energy Supply System Model`` or ``System Model``.
In the context of  :mod:`Tessif <tessif>`, this describes a set of distinct
lines of code aiming to calculate the amount of
energy transferred between components of an energy supply system for each
timestep of a predetermined amount of timesteps. Thus, the results of these
calculation must be interpretable by tessif as energy flows between energy
system components for each of these timesteps.

The beformentioned definition implies the following:

   1. It must be possible to display the system model's optimisation results as a network
      comprised of nodes respresenting the energy system compnents and edges
      representing the amount of energy flowing as well as their flow direction
      for each timestep.

   2. The programming language with which the system model was created is of secondary meaning as long as it is possible
      to control and access the system model's data flow using a python interface.

   3. Tessif works independently of a system model's underlying set of equation used to obtain
      the results. Hence all sorts of energy supply system simulation methods
      can be used. Meaning tessif does not know whether the results were
      obtained using differntial equations, solving a linear optimization
      problem or a mixed integer linear optimization problem. As long as point
      ``2`` holds, a set of lines of code can be utilized as one of tessif's
      supported software tools. Currently, however, Tessif only
      comprises of energy supply system modelling and optimisation software tols
      (ESSMOS tools), written in python.



.. note::

   Currently Tessif only supports energy supply system modelling and
   **optimisation** software tols (ESSMOS tools), written in python.
   Conceptually, however, Tessif can be used for any energy supply
   system modeling tool.      
      


