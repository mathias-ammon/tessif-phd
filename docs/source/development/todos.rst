Todos
=====

Major implementations the lead author deems helpfull for advancing the helpfullness and usefullness of tessif are listed below:

.. contents::
   :local:
      
Reworking the logging concept
-----------------------------
One of the very early ideas of comparing the computing time necessary was to log needed amounts of time for each of the computational and transforming steps occuring in tessif. In retrospective this was a very problematic idea, since:

  1. It clutters the logging output
  2. The purspose of debuging, reporting and warning the user gets mixed up
     with the task of measuring computatonal efforts
  3. Compared to the actual optimization, tessif's computational overhang is
     most likely to be negligable

Consequently the logging concept of tessif is currently quite the mess. Is still holds a lot of time measurement parts, and it also does not log all the things worth logging. Not even close actually. What actually needs to be logged is also not quite clear. In the lead authors opinion at least all the transformation info should be added to logging, since one of major questions users face is how the parameters utilized in tessif actually influence the target model parameterization. In cases like pypsa and fine for example it is really not quite obvious, since a lot of effort was taken, to somewhat unify the parameterizations among models.
 

Unifying the to-data-type export of tessif energy system
--------------------------------------------------------
Currently a tessif energy system can be exported to:

  - :func:`binary (pickle) <tessif.model.energy_system.AbstractEnergySystem.dump>`
  - :func:`hdf5 <tessif.model.energy_system.AbstractEnergySystem.to_hdf5>`
  - :func:`xml <tessif.model.energy_system.AbstractEnergySystem.to_xml>`

Wishfull addendums would probaby be:

  - `rst <https://en.wikipedia.org/wiki/ReStructuredText>`_
  - xlsx
  - `netCDF <https://www.unidata.ucar.edu/software/netcdf/docs/index.html>`_; 
    `possible-to-nest? <https://stackoverflow.com/questions/34434723/saving-python-dictionary-to-netcdf4-file>`_

And idealy this would all be accesible via a method that looks like::

  def export(to, **kwargs):

      # map file types to functionalities present in tessif.write.tsf2file
      ftype_to_function_mapping = {
          'hdf5': 'hdf5',
          'netcdf': 'netcdf',
          'rst': 'rst',
          'tsf': 'pickle'
          'xlsx': 'xl-like',
          'xml': 'xml',
      }

      # Some path figuring out has probably to be added

      fname, ftype = *to.split('.')

      export_utility = getattr(
          tessif.write.tsf2file, ftype_to_function_mapping[ftype],
          **kwargs)

      
Which implies adding a another subpackage to the 'write' package called
tsf2file in which all the export functions are at home.

This declutters the AbstractEnergySystem class allows for easy expansion and
maintainability.
      
  

Implementing es2tsf modules in the es2tsf package
-------------------------------------------------
A major addition to tessif would be the capability of parsing a supported
energy system model into a tessif model, so it can be utilized using other
of tessif's supported models.

Each of the 'model2tsf' (i.e. 'omf2tsf') cluster of functionalities should
reside in its own module, part of a subpackage called 'es2tsf' insdie the
'transform' package. The current 'es2es' subpackage should be renamed to
'tsf2es'.

Respect the optimization vs modelling vs simulation differentation
------------------------------------------------------------------
Part of the literature research done by Cedric Körber as part of his bachelor
thesis revealed, that there actually exists some literature that recommends
the differentitation between the terms:

  - simulation
  - optimization

Which revealed to the lead author, that he has fundamentally ignored this
differentiation and to make it worse, mixed up the term simulation and
modelling. This is reflected not only in Körber's thesis title, but also in
the current state of the introduction. This needs to be fixed.


Include a PyPSA-Link capex test
-------------------------------
In the works of :ref:`Examples_Application_Components` it was found, that the link expansion capex calculations were off. At the same time no test failed. In order to prevent future uncertainties, a test and example should be created in :ref:`examples_auto_comparison` named 'expandable chp', which schould build on a tessif hardcoded example called 'create_expandable_chp'.
