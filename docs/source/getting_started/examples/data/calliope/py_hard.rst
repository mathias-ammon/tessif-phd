.. _examples_data_calliope_pyhard:

.. currentmodule:: tessif.examples.data.calliope.py_hard


.. rubric:: Minimum Working Examples
.. autosummary::
   :nosignatures:

   create_mwe
   create_fpwe
   create_chp_expansion

py - hardcoded
==============
.. note::
    Calliope model data usually is stored in yaml and csv files which is also the main
    usage of calliope inside tessif. So the amount of py_hard coded examples is hold to a minimum.

    Tests passing the timeseries as pandas dataframe did not work so reading from csv is used.
    But dataframes should work too. Most likely there has been done some mistakes with indexing it correctly.

    The energysystem to_csv function in calliope does not work if file already exists.
    If changes are done and the csv is wanted to be saved, either another directory should be used,
    or the existing one being deleted.

.. automodule:: tessif.examples.data.calliope.py_hard
   :members:
