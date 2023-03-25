*************
Temporal Data
*************

In Tessif temporal data is considered to be the timframe and the resolution of
any given simulation task.

In theory there is no limit to either of these quantities. But since tessif
aims primarily to be used for energy supply system simulation applications a
default of yearly timeframes with hourly resolutions is assumed.

Following sections provide an overview and further references on how to supply
temporal data, configure tessif's temporal resolution as well as how to provide
data bound to certain points in time.

.. contents::
   :local:
   :depth: 1
   

Supply
******
Temporal data is supplied by using the ``timeframe`` key at the upper most
level inside the :ref:`provided energy system mapping
<SupportedDataFormats_Concept>`.

The value stored behind this key can be

   1. A :class:`pandas.DatetimeIndex` created by :meth:`pandas.daterange`
      (when using a
      :ref:`pure python mapping <SupportedDataFormats_PurePythonMappings>`, 
      as for example found
      :ref:`here <Examples_Tsf_PyMapping_Data>`)
      
   2. A column of singular datetime stamps
      (when using a :ref:`Spreadsheet <SupportedDataFormats_Spreadsheet>`, 
      as for example found
      :ref:`here <Examples_Omf_Xlsx_Timeframe>`)
      
   3. A mapping of respective values with which a
      :class:`pandas.DatetimeIndex` can be created
      (when using another kind of mapping, as for example found
      :ref:`here <Examples_Tsf_Cfg_Flat>`)

Configuration
*************
When using temporal resolutions other than hourly
:attr:`tessif's default configuration
<tessif.frused.configurations.temporal_resolution>` needs to be altered as in::

   >>> import tessif.frused.configurations as configurations
   >>> from tessif.frused.resolutions import temporals
   >>> configurations.temporal_resolution = temporals['s']



Timeseries Values
*****************
Throughout :mod:`tessif` ``timeseries values`` are considered externaly set
constraints bound to a specific point in (simulated) time.

Providing timeseries values for energy system components prior to optimization
is a common task when performing energy system simulations.

Following sections provide examples for how the different
models support providing timeseries values prior to optimization.

tessif
======
To bind an :ref:`energy system component's <Models_Tessif_Concept_ESC>`
parameter to a timeseries, the
:paramref:`~tessif.model.components.Source.timeseries` keyword is used in
conjunction with the parameter that is to be bound (usually the
:paramref:`~tessif.model.components.Source.flow_rate`)::

   timeseries = {'input_bus': MinMax(min=0, max=[10, 42, 15, 42])}

Although a litte more verbose during initialization this solution offers convenient post processing of an optimized energy system in regard to figure out which values were set prior to optimization, even if the original input data was not accessible.

If - like in the example above - the parameter is represented as a
:class:`~typing.NamedTuple` then of course all of the tuple fields can be subject
to timeseries bound values::

   timeseries = {'input_bus': MinMax(
       min=[10, 42, 15, 42], max=[10, 42, 15, 42])}

If - not like in the example above - the ``min`` and ``max`` values would
differ, the solver would try to find an optimum solution for the formulated
problem, respecting the different min/max constraints at any given point in
time.  

.. note::
   See :ref:`this example <Examples_Tessif_Config_Flat>` for how the timeseries
   keyword can be utilized.


oemof
=====
To bind an :mod:`energy system component's <oemof.solph.network>`
parameter to a timeseries, the respecitve series is simply bound to the
desired parameter (of :class:`oemof.solph.network.Flow`)::

   solph.Flow(max=[10, 42, 15, 42])

To fix a value to a certain amount the :paramref:`oemof.solph.Flow.fix`
parameter has to be used::
  
   renewable = solph.Source(
       label=nts.Uid('Renewable', 53, 10, 'Germany',
                     'Power', 'Electricity', 'Source'),
       outputs={power_line: solph.Flow(
           nominal_value=10, fix=[0.8, 0.2],
           variable_costs=9)})
