.. _Models_FINE:

*****
FINE
*****

Following sections give detailed instructions on how to create ready-to-use
energy systems using `FINE Energy System Model <https://vsa-fine.readthedocs.io/en/latest/energySystemModelDoc.html>`__

.. contents:: Contents
   :local:
   :backlinks: top


Concept
*******
`FINE <https://vsa-fine.readthedocs.io/en/latest/index.html>`__ aims to be a free software toolbox
simulating and optimizing energy supply systems with multiple regions, commodities and time steps.
Using the time series aggregation module
`TSAM <https://vsa-fine.readthedocs.io/en/latest/index.html>`__ ,
the time series under investigation can be divided into periods to reduce the memory requirement and computation
time. This is particularly useful for larger amounts of data under investigation.

It is developed by the
`Forschungszentrum Jülich
<https://www.fz-juelich.de/portal/DE/Home/home_node.html>`_
with the
`Helmholtz Association <https://www.helmholtz.de/en/>`_ as partner in the context of
`Energy System 2050 - Central platform of the Research Field Energy
<https://www.helmholtz.de/en/research/energy/energy-system-2050/>`_.
    

Purpose
*******
Within the context of tessif, `FINE <https://vsa-fine.readthedocs.io/en/latest/index.html>`_ serves
another pyomo solver interface. The goal of optimization it's is to minimize the costs
incurred by the energy system. Thereby it is possible to formulate emission restrictions, that will be respected.


Using `FINE <https://vsa-fine.readthedocs.io/en/latest/index.html>`_ through tessif is somewhat of a challenge
The clear technical parameterization allows an efficient transformation of the energy system
from Tessif to `FINE <https://vsa-fine.readthedocs.io/en/latest/index.html>`_.
In addition, the components are designed in order to allow flexible use.
This enables components to be implemented that are not actually part of the predefined
`FINE structure <https://vsa-fine.readthedocs.io/en/latest/structureOfFINEDoc.html>`_ .




Examples
********
               
.. _Models_FINE_Examples_Mwe:

Minimum Working Example
=======================

.. note::
   The exact same energy system can be accessed using
   :meth:`tessif.examples.data.fine.py_hard.create_mwe`.

1. Import the needed packages::

    # standard library
    import os
    import pathlib

    # third party
    import FINE as fn

    # local
    import tessif.frused.namedtuples as nts
    from tessif.frused.paths import write_dir
    import tessif.write.tools as write_tools



2. Create an energy system model instance ::
     
    esM = fine.energySystemModel.EnergySystemModel(
            locations={"Germany"},
            commodities={"Electricity", "gas"},
            numberOfTimeSteps=2,
            commodityUnitsDict={"Electricity": "GW_el", "gas": "GW_CH4"},
            hoursPerTimeStep=1,
            costUnit="€",)

3. Add an :class:`~tessif.frused.namedtuples.Uid` container to the energy system model for utilizing :ref:`Tessif's Labeling Concept <Labeling_Concept>`::

    setattr(esM, 'uid_dict', dict())

4. Do the modular arrangement of all components:

- Add a :class:`Transmission <https://vsa-fine.readthedocs.io/en/latest/transmissionClassDoc.html>` as ideal power line with predefined UID::

        # create uid
        transmission_uid = nts.Uid(
                    name='Power Line', latitude=53, longitude=10,
                    region='Germany', sector='Power', carrier='Electricity',
                    component='Bus', node_type='AC_Bus')

        # create component
        esM.add(
        fn.Transmission(
            esM=esM,
            hasCapacityVariable=True,
            name=str(transmission_uid),
            commodity=transmission_uid.carrier,)
            )

        # add the UID to the container:
        esM.uid_dict.update({str(transmission_uid): transmission_uid})

- Add a :class:`Transmission <https://vsa-fine.readthedocs.io/en/latest/transmissionClassDoc.html>` as ideal chemical bound energy transmission with predefined UID::

        # create uid
        gas_transmission_uid = nts.Uid(
            name='CBET', latitude=53, longitude=10,
            region='Germany', sector='Power', carrier='gas',
            component='Bus', node_type='gas-Bus')

        # create component
        esM.add(
        fn.Transmission(
            esM=esM,
            hasCapacityVariable=True,
            name=str(gas_transmission_uid),
            commodity=gas_transmission_uid.carrier,)
            )

        # add the UID to the container:
        esM.uid_dict.update({str(gas_transmission_uid): gas_transmission_uid})

- Add a :class:`Demand <https://vsa-fine.readthedocs.io/en/latest/sourceSinkClassDoc.html>` as sink needing 10 energy units per timestep::

        # create uid
        demand_uid = nts.Uid(
            name='Demand', latitude=53, longitude=10,
            region='Germany', sector='Power', carrier='Electricity',
            component='Sink', node_type='Sink')

        # create component
        esM.add(
            fn.Sink(
                esM=esM,
                hasCapacityVariable=False,
                name=str(demand_uid),
                commodity=demand_uid.carrier,
                operationRateFix=pd.DataFrame({"Germany": [10, 10]}),
            )
        )

        # add the UID to the container:
        esM.uid_dict.update({str(demand_uid): demand_uid})


- Add a renewable :class:`Source <https://vsa-fine.readthedocs.io/en/latest/sourceSinkClassDoc.html>` producing 8 and 2 energy units with a cost of 9::

        # create uid
        renewable_uid = nts.Uid(
                name='Renewable', latitude=53, longitude=10,
                region='Germany', sector='Power', carrier='Electricity',
                component='Source', node_type='AC-Source')

        # create component
        esM.add(
            fn.Source(
                esM=esM,
                name=str(renewable_uid),
                commodity=renewable_uid.carrier,
                hasCapacityVariable=True,
                operationRateMax=pd.DataFrame({'Germany': [0.8, 0.2]}),
                capacityMax=10,
                opexPerOperation=9,
            )
        )

        # add the UID to the container:
        esM.uid_dict.update({str(conversion_uid): conversion_uid})

- Add a chemical bound energy source :class:`Source <https://vsa-fine.readthedocs.io/en/latest/sourceSinkClassDoc.html>`::

        # create uid
        CBE_uid = nts.Uid(
            name='Gas Station', latitude=53, longitude=10,
            region='Germany', sector='Power', carrier='gas',
            component='Source', node_type='gas import')

        # create component
        esM.add(
            fn.Source(
                esM=esM,
                name=str(CBE_uid),
                commodity=CBE_uid.carrier,
                hasCapacityVariable=True,
            )
        )

        # add the UID to the container:
        esM.uid_dict.update({str(conversion_uid): conversion_uid})

- Add a conventional engergy :class:`Conversion <https://vsa-fine.readthedocs.io/en/latest/conversionClassDoc.html>` producing up to 10 energy units for a cost of 10::

        # create uid
        conversion_uid = nts.Uid(
            name='Transformer', latitude=53, longitude=10,
            region='Germany', sector='Power', carrier='gas',
            component='Transformer', node_type='gas-powerplant'
        )

        # create component
        # Transformer parameters are related to inflow -> devide outflow related params with efficiency
        esM.add(
            fn.Conversion(
                esM=esM,
                name=str(conversion_uid),
                physicalUnit="GW_el",
                commodityConversionFactors={"gas": -1, "Electricity": 0.42},
                opexPerOperation=10/0.42,
            )
        )

    # add the UID to the container:
    esM.uid_dict.update({str(conversion_uid): conversion_uid})

5. Optimize the energy system model instance::

    esM.optimize()

6. Store the energy system into ``tessif/src/tessf/write/fine/mwe``::
       
    import os
    import pathlib

    from tessif.frused.paths import write_dir

    # Use fine to save the data into an excel spreadsheet
    fn.writeOptimizationOutputToExcel(esM=esM, outputFileName=f, optSumOutputLevel=0)

    # Moving the file to the correct destination in the tessif write dir
    src = os.getcwd()  # source folder
    f = f + ".xlsx"  # exact file name with ending
    shutil.move(os.path.join(src, f), os.path.join(d, f))
         


7. Using this newly generated energy system in a different python context by
   importing it:
   
.. note::
   The code of steps 1 to 5 is wrapped in a
   :meth:`~tessif.examples.data.fine.py_hard.create_mwe` function for
   convenience meaning it is copy pastable.

..


  a. Import the wrapper functionality:

     >>> from tessif.examples.data.fine.py_hard import create_mwe
     >>> esys = create_mwe()

  b. Confirm the expected output:

     >>> for model in esys.componentModelingDict:
     ...    for node in esys.componentModelingDict[model].componentsDict:
     ...        print(node)
     PowerLine
     CBET
     Demand
     Renewable
     Gas Station
     Transformer

8. For examples on how to extract result information out ouf the optimized
   energy system using tessif, see :mod:`tessif.transform.es2mapping.fine`
