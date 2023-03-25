# tessif/examples/data/fine/py_hard.py
"""
:mod:`~tessif.examples.data.fine.py_hard` is a :mod:`tessif` module for giving
examples on how to create an :class:`fine energy system
<fine.energySystemModel>`.

It collects minimum working examples, meaningful working
examples and full fledged use case wrappers for common scenarios.
"""

# 1.) Handle imports:
# standard library
import pathlib
import os

# third party
import shutil
import FINE as fn
import pandas as pd
import numpy as np
# local imports
import tessif.frused.namedtuples as nts
from tessif.frused.paths import write_dir
import tessif.write.tools as write_tools


def create_mwe(directory=None, filename=None, save=False):
    r"""
    Create a minimum working example using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory` as

    :paramref:`~create_mwe.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/mwe will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``mwe_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.

    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": "GW_el", "gas": "GW_CH4"}
    commodities = {"Electricity", "gas", }

    numberOfTimeSteps = 4
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')

    uids = dict()
    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        verboseLogLevel=2,
    )

    # 2.) Adding Commodity Transmission to esM (not necessary for mwe)
    uid = nts.Uid(
        name='PowerLine', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 2.) Adding Commodity Transmission to esM (not necessary for mwe)
    uid = nts.Uid(
        name='CBET', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='gas-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 3.) Adding Commodity Sink to esM representing the Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10] * numberOfTimeSteps})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )
    # 4.) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({uid.region: [1, 1, 0, 1]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
            capacityMax=10,
            opexPerOperation=1,
            investPerCapacity=1,
        )
    )

    # 6.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='Gas Station', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='gas import')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 5.) Adding Commodity Conversion: gas -> elec
    uid = nts.Uid(
        name='Transformer', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})

    # Transformer capacities are always related to inflow
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={"gas": -1, "Electricity": 0.42},
            opexPerOperation=2,
        )
    )

    # 8.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 9.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "mwe_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'mwe')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 9b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 9c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 10.) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 11.) Return the mwe_FINE energy system
    return esM


def create_expansion_example(directory=None, filename=None, save=False):
    r"""
        Create an expansion example using :mod:`fine`.

        Creates a simple energy system simulation to potentially
        store it on disc in :paramref:`~expansion_example.directory` as

        :paramref:`~expansion_example.filename`

        Parameters
        ----------
        directory : str, default=None
            String path the created energy system is stored in.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/fine/expansion_example will be the chosen
            directory.

        filename : str, default=None
            String name of the file the results are stored in.

            If set to ``None`` (default) filename will be ``expansion_example_FINE``.

        save : boolean, default=False
            Specifies if the data should be stored to an excel spreadsheet`.

        Return
        ------
        optimized_es : fine energy system model
            Energy system carrying the optimization results.
        """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el", "emissions": r'CO2/unit_Energy',
                         'electricity.unlimitted': 'MW_unlimitted'}
    commodities = {"Electricity", "emissions", "electricity.unlimitted", }

    numberOfTimeSteps = 4
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')
    simLimit = 20
    yearlyLimit = 8760 * simLimit / numberOfTimeSteps

    uids = dict()
    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        verboseLogLevel=2,
    )

    # 2.) Adding Commodity Transmission to esM (not necessary for mwe)
    uid = nts.Uid(
        name='PowerLine', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 3.) Adding Commodity Sink to esM representing the Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10] * numberOfTimeSteps})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4a.) Adding Commodity Source to esM representing capped source with given bounds
    uid = nts.Uid(
        name='Capped Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            capacityMax=4,
            capacityMin=2,
            opexPerOperation=2,
            investPerCapacity=1,
            interestRate=0,
            economicLifetime=numberOfTimeSteps / 8760
        )
    )
    # 4b.) Adding Commodity Source to esM representing uncapped source but with invest costs if built
    uid = nts.Uid(
        name='Uncapped Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [1/3, 2/3, 3/3, 1/3]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
            capacityMin=3,
            investPerCapacity=2,
            opexPerOperation=2,
            interestRate=0,
            economicLifetime=numberOfTimeSteps / 8760
        )
    )
    # 5b.) Adding unlimitted Commodity Source to enable emission and commodity production in transformer
    # this commodity is not any part in tessifs post processing, just that the transformer can do its job representing
    # a source
    esM.add(
        fn.Source(
            esM=esM,
            name='Emitting Source.unlimitted',
            commodity='electricity.unlimitted',
            hasCapacityVariable=True,
        )
    )

    # 5a.) Adding Commodity Conversion representing unlimitted source converting into commodity and emission
    uid = nts.Uid(
        name='Emitting Source', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='electricity',
        component='Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit="GW_el",
            commodityConversionFactors={
                "electricity.unlimitted": -1, 'Electricity': 1, "emissions": 1},
            hasCapacityVariable=True,
            capacityMax=None,
            interestRate=0,
            economicLifetime=numberOfTimeSteps / 8760
        )
    )

    # 6.) Adding global constraint for CO2, when a yearly limit is set
    if yearlyLimit > 0:
        esM.add(
            fn.Sink(
                esM=esM,
                name='emissions',
                commodity='emissions',
                hasCapacityVariable=False,
                commodityLimitID='emissions',
                yearlyLimit=yearlyLimit
            )
        )

    # 7.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 8.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "expansion_example_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'expansion_example')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 8b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 8c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 9.) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 10.) Return the mwe_FINE energy system
    return esM


def emission_objective(directory=None, filename=None, save=False):
    r"""
    Create an emission constrain example using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~emission_objective.directory` as

    :paramref:`~emission_objective.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/emission_objective will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``emission_objective_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el",
                         "gas": r"GW_CH4", 'CO2': r'CO2/unit_Energy'}
    commodities = {"Electricity", "gas", "CO2"}
    numberOfTimeSteps = 4
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')
    simLimit = 30
    yearlyLimit = 8760 * simLimit / numberOfTimeSteps

    uids = dict()

    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,
    )

    # 2a.) Adding Commodity Transmission to esM for electricity
    uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )

    # 2b.) Adding Commodity Transmission to esM for electricity
    uid = nts.Uid(
        name='CBET', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='Gas-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 3.) Adding Commodity Sink to esM representing the Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 10, 10, 10]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='CBE', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 5a.) Adding Commodity Conversion: gas -> elec
    uid = nts.Uid(
        name='Transformer', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_el",
            commodityConversionFactors={
                "Electricity": 0.42, 'CO2': 1, "gas": -1},
            hasCapacityVariable=True,
            capacityMax=10 / 0.42,
            opexPerOperation=2
        )
    )
    # 6.) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})

    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            opexPerOperation=5,
        )
    )
    # 7.) Adding global constraint for CO2, when a yearly limit is set
    if yearlyLimit > 0:
        esM.add(
            fn.Sink(
                esM=esM,
                name='emission',
                commodity='CO2',
                hasCapacityVariable=False,
                commodityLimitID='emission',
                yearlyLimit=yearlyLimit
            )
        )

    # 7.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 8.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "emission_objective_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'emission_objective')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 8b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 8c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 9.a) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 9.b) Return the energy system
    return esM


def chp_example(directory=None, filename=None, save=False):
    r"""
    Create a combined heat and power example using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_chp.directory` as

    :paramref:`~create_chp.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/chp will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``chp_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el",
                         "gas": r"GW_CH4", 'Heat': r"GW_Heat", }
    commodities = {"Electricity", "gas", "Heat"}
    numberOfTimeSteps = 4
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')

    uids = dict()

    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,

    )

    # 2a.) Adding Commodity Electricity Transmission to esM
    uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 2b.) Adding Commodity Heat Transmission to esM
    uid = nts.Uid(
        name='Heat Grid', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 2c.) Adding Commodity Gas Transmission to esM
    uid = nts.Uid(
        name='Gas Grid', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 3a.) Adding Commodity Sink to esM representing the Electricity Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 10, 10, 10]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )
    # 3b.) Adding Commodity Sink to esM representing the Heat Demand
    uid = nts.Uid(
        name='Heat Demand', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Sink', node_type='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 10, 10, 10]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4a.) Adding Commodity Source to esM representing external back up
    uid = nts.Uid(
        name='Backup Power', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            opexPerOperation=10,
        )
    )

    # 4b.) Adding Commodity Source to esM representing external back up
    uid = nts.Uid(
        name='Backup Heat', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Source', node_type='Heat-Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            opexPerOperation=10,
        )
    )

    # 4c.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='Gas Source', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 5a.) Adding Commodity Conversion: gas -> Electricity + Heat
    uid = nts.Uid(
        name='CHP', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "gas": -1, "Electricity": 0.3, "Heat": 0.2},
            hasCapacityVariable=True,
            opexPerOperation=5 * 0.3 + 5 * 0.2
        )
    )

    # 6.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 7.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "chp_example_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'chp_example')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 7b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 7c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 8.) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 9.) Return the energy system
    return esM


def storage_example(directory=None, filename=None, save=False):
    r"""
    Create a storage example using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~storage_example.directory` as

    :paramref:`~storage_example.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/storage_example will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``storage_example_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el"}
    commodities = {"Electricity"}
    numberOfTimeSteps = 5
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')

    uids = dict()

    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,

    )

    # 2.) Adding Commodity Electricity Transmission to esM
    uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 3.) Adding Commodity Sink to esM representing the Electricity Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 10, 7, 10, 10]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4.) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Generator', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({uid.region: [1, 1, 0, 1, 0]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
            opexPerOperation=2,
        )
    )

    # 5.) Adding storage to esM representing a battery
    uid = nts.Uid(
        name='Storage', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Storage', node_type='AC-AC-Storage')
    uids.update({str(uid): uid})
    esM.add(
        fn.Storage(
            # Required Parameters
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            opexPerDischargeOperation=1,
        )
    )

    # 6.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 7a.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "storage_example_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'storage_example')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 7b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 8c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 9.) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 10.) Return the energy system
    return esM


def double_transformer_emission_objective(directory=None, filename=None, save=False):
    r"""
    Create a example with two transformer components using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~double_chp_objective.directory` as

    :paramref:`~double_chp_objective.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/double_chp_objective will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``double_chp_objective_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el",
                         "gas": r"GW_CH4", 'CO2': r'CO2/unit_Energy'}
    commodities = {"Electricity", "gas", "CO2"}
    numberOfTimeSteps = 4
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')
    simLimit = 30
    yearlyLimit = 8760 * simLimit / numberOfTimeSteps

    uids = dict()

    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,
    )

    # 2a.) Adding Commodity Transmission to esM for electricity
    uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )

    # 2b.) Adding Commodity Transmission to esM for gas
    uid = nts.Uid(
        name='CBET', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='Gas-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 3.) Adding Commodity Sink to esM representing the Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [15, 15, 15, 15]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='CBE', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 5a.) Adding Commodity Conversion: gas -> elec
    uid = nts.Uid(
        name='Transformer1', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "Electricity": 0.42, 'CO2': 0.5, "gas": -1},
            hasCapacityVariable=True,
            capacityMax=5 / 0.42,
            # capacityMin=12,
            opexPerOperation=2,
            yearlyFullLoadHoursMin=4
        )
    )
    # 5b.) Adding Commodity Conversion: gas -> elec
    uid = nts.Uid(
        name='Transformer2', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "Electricity": 0.42, 'CO2': 0.5, "gas": -1},
            hasCapacityVariable=True,
            capacityMax=5 / 0.42,
            opexPerOperation=2,
            yearlyFullLoadHoursMin=4
        )
    )
    # 6.) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            opexPerOperation=5,
        )
    )
    # 6.) Adding global constraint for CO2, when a yearly limit is set
    if yearlyLimit > 0:
        esM.add(
            fn.Sink(
                esM=esM,
                name='CO2_output',
                commodity='CO2',
                hasCapacityVariable=False,
                commodityLimitID='CO2_cap',
                yearlyLimit=yearlyLimit
            )
        )

    # 7.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 8.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "double_chp_obj_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'double_chp_objective')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 8b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 8c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 9.) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 10.) Return the energy system
    return esM


def create_multicommodity(directory=None, filename=None, save=False):
    r"""
    Create a multi flow grid example using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~multi_com.directory` as

    :paramref:`~multi_com.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/multi_commodity will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``multi_commodity_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el", "gas": r"GW_CH4", 'CO2': r'CO2/unit_Energy', 'Heat': r"GW_Heat",
                         'H2': r'GW_H2'}
    commodities = {"Electricity", "gas", "CO2", "Heat", "H2"}
    numberOfTimeSteps = 4
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')
    simLimit = 30
    yearlyLimit = 8760 * simLimit / numberOfTimeSteps
    uids = dict()

    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,

    )

    # 2a.) Adding Commodity Electricity Transmission to esM
    uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 2b.) Adding Commodity Heat Transmission to esM
    uid = nts.Uid(
        name='Heat Grid', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 2c.) Adding Commodity H2 Transmission to esM
    uid = nts.Uid(
        name='H2 Grid', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='H2',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 2d.) Adding Commodity Heat Transmission to esM
    uid = nts.Uid(
        name='Gas Grid', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 3a.) Adding Commodity Sink to esM representing the Electricity Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [6, 24, 10, 16]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )
    # 3b.) Adding Commodity Sink to esM representing the Heat Demand
    uid = nts.Uid(
        name='Heat Demand', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Sink', node_type='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 12, 6, 12]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )
    # 3c.) Adding Commodity Sink to esM representing the Heat Demand
    uid = nts.Uid(
        name='H2 Demand', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='H2',
        component='Sink', node_type='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 50, 6, 15]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )
    # 3b.) Adding Commodity Sink to esM representing the Heat Demand
    uid = nts.Uid(
        name='Gas Demand', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='gas',
        component='Sink', node_type='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 12, 6, 12]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )
    # 4a.) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({uid.region: [0.8, 0.4, 0.6, 1]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
            capacityMax=30,
            opexPerOperation=5,
        )
    )
    # 4b.) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Back-up Heat', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Source', node_type='Heat-Source')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({uid.region: [0.8, 0.4, 0.6, 1]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
            capacityMax=10,
            opexPerOperation=5,
        )
    )
    # 4c.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='Gas Import', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 4d.) Adding Commodity Source to esM representing a Heat import
    uid = nts.Uid(
        name='Industry Heat', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({uid.region: [0, 0.8, 1, 0]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            capacityMax=7.5,
            operationRateMax=data_frame,
        )
    )
    # 4e.) Adding Commodity Source to esM representing a H2 import
    uid = nts.Uid(
        name='H2 Import', latitude=53, longitude=10,
        region='Germany', sector='Multi', carrier='H2',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({uid.region: [1, 0, 1, 1]})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
        )
    )

    # 5a.) Adding Commodity Conversion: gas -> Electricity + Heat
    uid = nts.Uid(
        name='CHP', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "gas": -1, "Electricity": 0.42, "Heat": 0.42, "CO2": 2},
            hasCapacityVariable=True,
            capacityMax=10 / 0.42,
            opexPerOperation=10
        )
    )
    # 5b.) Adding Commodity Conversion: H2 -> Electricity + Heat
    uid = nts.Uid(
        name='H2-CHP', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='H2',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "H2": -1, "Electricity": 0.8, "Heat": 0.4, "CO2": 0.1},
            hasCapacityVariable=True,
            opexPerOperation=20
        )
    )
    # 5c.) Adding Commodity Conversion: H2 -> Electricity + Heat
    uid = nts.Uid(
        name='Electrolyzer', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='H2',
        component='Transformer', node_type='H2-Electrolyzer')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_H2",
            commodityConversionFactors={"Electricity": -1, "H2": 0.5},
            hasCapacityVariable=True,
            opexPerOperation=10
        )
    )
    # 6a.) Storage components for electricity
    uid = nts.Uid(
        name='Batteries', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Storage', node_type='AC-AC-Storage')
    uids.update({str(uid): uid})
    esM.add(
        fn.Storage(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            opexPerDischargeOperation=3
        )
    )
    # 6b.) Storage components for H2
    uid = nts.Uid(
        name='H2-Caverns', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='H2',
        component='Storage', node_type='AC-H2-Storage')
    uids.update({str(uid): uid})
    esM.add(
        fn.Storage(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            capacityMax=30,
            opexPerDischargeOperation=1

        )
    )

    # 7.) Adding global constraint for CO2, when a yearly limit is set
    if yearlyLimit > 0:
        esM.add(
            fn.Sink(
                esM=esM,
                name='co2_limit',
                commodity='CO2',
                hasCapacityVariable=False,
                commodityLimitID='CO2 limit',
                yearlyLimit=yearlyLimit
            )
        )

    # 8.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 9.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "multi_commodity_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'multi_commodity')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 9b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 9c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 10.a) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 10.b) Return the energy system
    return esM


def single_chp_emission_objective(directory=None, filename=None, save=False):
    r"""
    Create a single combined heat and power example with emissions constrained using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~single_chp_obj.directory` as

    :paramref:`~single_chp_obj.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/single_chp_obj will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``single_chp_obj``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet`.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el", "gas": r"GW_CH4",
                         'Heat': r"GW_Heat", 'CO2': r'CO2/unit_Energy'}
    commodities = {"Electricity", "gas", "Heat", "CO2"}
    numberOfTimeSteps = 2
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')
    simLimit = 30
    yearlyLimit = 8760 * simLimit / numberOfTimeSteps

    uids = dict()

    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,

    )

    # 2a.) Adding commodity electricity transmission to esM
    uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 2b.) Adding commodity heat transmission to esM
    uid = nts.Uid(
        name='Heat Grid', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )
    # 2c.) Adding commodity gas transmission to esM
    uid = nts.Uid(
        name='Gas Grid', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
        )
    )
    # 3a.) Adding commodity sink to esM representing the electricity Demand
    uid = nts.Uid(
        name='Power Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 10]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 3b.) Adding commodity sink to esM representing the heat demand
    uid = nts.Uid(
        name='Heat Demand', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Sink', node_type='Sink')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame({"Germany": [10, 10]})
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4a.) Adding commodity source to esM representing renewable energy
    uid = nts.Uid(
        name='Backup Power', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            capacityMax=10,
            opexPerOperation=10,
        )
    )
    # 4b.) Adding commodity source to esM representing renewable energy
    uid = nts.Uid(
        name='Backup Heat', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Heat',
        component='Source', node_type='Heat-Source')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            capacityMax=10,
            opexPerOperation=10,
        )
    )
    # 4c.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='Gas Source', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 5a.) Adding Commodity Conversion: gas -> Electricity + Heat
    uid = nts.Uid(
        name='CHP', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "gas": -1, "Electricity": 0.3, "Heat": 0.5, "CO2": 1},
            hasCapacityVariable=True,
            opexPerOperation=2
        )
    )

    # 6.) Adding limiting constraint as sink
    if yearlyLimit > 0:
        esM.add(
            fn.Sink(
                esM=esM,
                name='CO2_output',
                commodity='CO2',
                hasCapacityVariable=False,
                commodityLimitID='CO2_cap',
                yearlyLimit=yearlyLimit
            )
        )
    # 7.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    with write_tools.HideStdoutPrinting():
        esM.optimize(solver='cbc')

    # 8.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            f = "single_chp_obj_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            d = os.path.join(write_dir, 'fine', 'single_chp_obj')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 9b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 9c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 11.a) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 11.b) Return the energy system
    return esM


def tsa_one_year_example(directory=None, filename=None, save=False, tsa=False):
    r"""
    Create an one year timeseries example using :mod:`fine`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~one_year_mwe.directory` as

    :paramref:`~one_year.filename`

    Parameters
    ----------
    directory : str, default=None
        String path the created energy system is stored in.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/fine/one_year will be the chosen
        directory.

    filename : str, default=None
        String name of the file the results are stored in.

        If set to ``None`` (default) filename will be ``one_year_FINE``.

    save : boolean, default=False
        Specifies if the data should be stored to an excel spreadsheet.

    tsa : boolean, default=False
        Specifies if the data should be aggregated for faster optimization or not.

    Return
    ------
    optimized_es : fine energy system model
        Energy system carrying the optimization results.
    """
    # Specify the necessary parameters to create an energy system with fine
    locations = {"Germany"}
    commodityUnitDict = {"Electricity": r"GW_el",
                         "gas": r"GW_CH4", 'CO2': r'CO2/unit_Energy'}
    commodities = {"Electricity", "gas", "CO2"}
    numberOfTimeSteps = 8760
    hoursPerTimeStep = 1
    timesteps = pd.date_range('7/13/1990', periods=numberOfTimeSteps, freq='H')
    yearlyLimit = 5000

    uids = dict()
    # 1.) Creating an energy system model instance
    esM = fn.energySystemModel.EnergySystemModel(
        locations=locations,
        commodities=commodities,
        numberOfTimeSteps=numberOfTimeSteps,
        commodityUnitsDict=commodityUnitDict,
        hoursPerTimeStep=hoursPerTimeStep,
        costUnit="€",
        lengthUnit="km",
        verboseLogLevel=2,
    )

    # 2a.) Adding Commodity Transmission to esM for electricity
    uid = nts.Uid(
        name='Powerline', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 2b.) Adding Commodity Transmission to esM for electricity
    uid = nts.Uid(
        name='CBET', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Bus', node_type='Gas-Bus')
    uids.update({str(uid): uid})
    esM.add(
        fn.Transmission(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 3.) Adding Commodity Sink to esM representing the Demand
    uid = nts.Uid(
        name='Demand', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Sink', node_type='AC-Sink')
    uids.update({str(uid): uid})
    dailyProfileSimple = [0.6, 0.6, 0.6, 0.6, 0.6, 0.7, 0.9,
                          1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.9, 0.8]
    data_frame = pd.DataFrame([[(u + 0.1 * np.random.rand()) * 50] for day in range(365) for u in dailyProfileSimple],
                              index=range(8760), columns=['Germany']).round(2)
    esM.add(
        fn.Sink(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=False,
            operationRateFix=data_frame,
        )
    )

    # 4.) Adding Commodity Source to esM representing a gas import
    uid = nts.Uid(
        name='CBE', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Source', node_type='Pipeline')
    uids.update({str(uid): uid})
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
        )
    )

    # 5.) Adding Commodity Conversion: gas -> elec
    uid = nts.Uid(
        name='Transformer', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='gas',
        component='Transformer', node_type='gas-powerplant')
    uids.update({str(uid): uid})
    esM.add(
        fn.Conversion(
            esM=esM,
            name=str(uid),
            physicalUnit=r"GW_CH4",
            commodityConversionFactors={
                "Electricity": 0.63, 'CO2': 201 * 1e-6 / 0.63, "gas": -1},
            hasCapacityVariable=True,
            capacityMax=40 / 0.63,
            opexPerOperation=2,
        )
    )
    # 6) Adding Commodity Source to esM representing renewable energy
    uid = nts.Uid(
        name='Renewable', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Source', node_type='AC-Source')
    uids.update({str(uid): uid})
    data_frame = pd.DataFrame([[np.random.beta(a=2, b=5)] for t in range(8760)], index=range(8760),
                              columns=['Germany']).round(6)
    esM.add(
        fn.Source(
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            hasCapacityVariable=True,
            operationRateMax=data_frame,
            capacityMin=0,
            capacityMax=400,
            opexPerOperation=1,
        )
    )

    # 7.) Adding Storage to esM representing batteries
    uid = nts.Uid(
        name='Batteries', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Storage', node_type='AC-AC-Storage')
    uids.update({str(uid): uid})
    esM.add(
        fn.Storage(
            # Required Parameters
            esM=esM,
            name=str(uid),
            commodity=uid.carrier,
            opexPerDischargeOperation=0.000002,
        )
    )

    # 8.) Adding global constraint for CO2, when a yearly limit is set
    if yearlyLimit > 0:
        esM.add(
            fn.Sink(
                esM=esM,
                name='CO2',
                commodity='CO2',
                hasCapacityVariable=False,
                commodityLimitID='CO2',
                yearlyLimit=yearlyLimit
            )
        )

    # 9.) Optimizing the esM with the cbc solver (default:gurobi) and hide output
    # possible with or without time series aggregation
    with write_tools.HideStdoutPrinting():
        if tsa is True:
            esM.cluster()
            esM.optimize(timeSeriesAggregation=True, solver='cbc')
        else:
            esM.optimize(solver='cbc')

    # 10 a.) Store results pumped energy system:
    if save is True:
        # Set default filename if necessary
        if not filename:
            if tsa is True:
                f = "tsa_one_year_example_FINE"
            else:
                f = "one_year_example_FINE"
        else:
            f = filename
        # Set default directory name of necessary
        if not directory:
            if tsa is True:
                d = os.path.join(write_dir, 'fine', 'tsa_one_year_example')
            else:
                d = os.path.join(write_dir, 'fine', 'one_year_example')
        else:
            d = directory

        # See if the targeted directory exists- if not: produce it
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

        # 10 b.) Use fine to save the data into an excel spreadsheet
        fn.writeOptimizationOutputToExcel(
            esM=esM, outputFileName=f, optSumOutputLevel=0)

        # 10 c.) Moving the file to the correct destination in the tessif write dir
        src = os.getcwd()  # source folder
        f = f + ".xlsx"  # exact file name with ending
        shutil.move(os.path.join(src, f), os.path.join(d, f))

    # 11.a) Setting uids as additional attribute to esM to later use it
    setattr(esM, 'uid_dict', uids)
    setattr(esM, 'timesteps', timesteps)

    # 11.b) Return the energy system
    return esM
