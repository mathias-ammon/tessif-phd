.. _Simulating_Through_Tessif:

Simulating Through Tessif
=========================
Carrying out simulations through :mod:`tessif` is handled by the
:mod:`~tessif.simulate` module. It provides simulation wrappers for all of the
supported models. Following sections provide detailed information on how to use
them.

.. note::
   The current support of the various simulation capabilities can be
   gauged and expanded using the :mod:`tessif.simulate` module.

.. contents::
   :local:

Fundamentally all simulation wrappers work the same way:

   1. They read in a data source provided via the parameter ``path``
   2. They parse the data according to the parser provided via the parameter ``parser``
   3. They simulate the read-in and parsed energy system using additonal arguments provided by the parameters qualifying as `kwargs
      <http://docs.python.org/tutorial/controlflow.html#arbitrary-argument-lists>`_


.. _Subpackages_Simulate_Omf:

omf
---
omf stands for `oemof <https://oemof.org/>`_ and is one of the 3rd party libraries usable via tessif. It's :meth:`simulation wrapper <tessif.simulate.omf>` can be accessed via::
  
  from tessif.simulate import omf as simulate_oemof

A simple example can be realized using tessif's `example hub <Examples>`_
(utilizing an Excel-Spreadsheet as source and tessif's corresponding parser)::

  from tessif.simulate import omf as simulate_oemof
  from tessif.parse import xl_like
  from tessif.frused.paths import example_dir
  import os
  es = simulate_oemof(
      path=os.path.join(example_dir,
                        'data', 'omf', 'xlsx', 'energy_system.xlsx'),
      parser=xl_like)

tsf
---
tsf stands for :mod:`tessif <tessif>` and represents tessif's built-in energy system simulation capabilities.

It's :meth:`simulation wrapper <tessif.simulate.tsf>` can be accessed via::
  
  from tessif.simulate import tsf as simulate_tsf

A simple example can be realized using tessif's `example hub <Examples>`_
(utilizing a folder of `config files <https://en.wikipedia.org/wiki/Configuration_file#Unix_and_Unix-like_operating_systems>`_
as source and tessif's corresponding parser)::

  from tessif.simulate import tsf as simulate_tessif
  from tessif.parse import flat_config_folder
  from tessif.frused.paths import example_dir
  import os
  es = simulate_tessif(
      path=os.path.join(example_dir, 'tsf', 'cfg', 'flat', 'basic'),
      parser=flat_config_folder)

