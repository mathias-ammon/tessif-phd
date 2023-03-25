# tessif/transform/es2mapping/fine.py
"""
:mod:`~tessif.transform.es2mapping.fine` is a :mod:`tessif` module holding
:class:`fine.Network` transformer classes for postprocessing results and
providing a tessif uniform interface.
"""
import logging
from collections import defaultdict, abc
import pandas as pd
import numpy as np

import tessif.transform.es2mapping.base as base
import tessif.write.log as log
from tessif.frused import namedtuples as nts
from tessif.frused.defaults import energy_system_nodes as esn_defaults
from tessif.frused import spellings as spl

logger = logging.getLogger(__name__)


class FINEResultier(base.Resultier):
    """ Transform nodes and edges into their name representation. Child of
       :class:`~tessif.transform.es2mapping.base.Resultier` and mother of all
       fine Resultiers.

       Parameters
       ----------
       optimized_es: fine energy system model
           An optimized fine energy system containing its results
    """

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_nodes(self, optimized_es):
        """ Return a list of node uids."""
        # node uids are directly produced while creating the esM with fine
        nodes = list()
        for node in optimized_es.uid_dict:
            nodes.append(node)

        return nodes

    @log.timings
    def _map_node_uids(self, optimized_es):
        """ Return a list of node uids."""

        cmp_input = self._cmp_input(optimized_es)
        _uid_nodes = dict()

        pre_uids = dict(optimized_es.uid_dict)

        for node in self.nodes:
            prelim_uid = pre_uids[node]
            uid_dict = prelim_uid._asdict()
            if pre_uids[node].component is None:
                if cmp_input[node].dimension == '2dim':
                    uid_dict['component'] = 'bus'

                if hasattr(cmp_input[node], 'sign'):
                    if cmp_input[node].sign == 1:
                        uid_dict['component'] = 'source'
                    elif cmp_input[node].sign == -1:
                        uid_dict['component'] = 'sink'

                if hasattr(cmp_input[node], 'commodityConversionFactors'):
                    # If str unlimitted is in cmp, it is an emitting source
                    if node + '.unlimitted' in cmp_input or '.unlimitted' in node:
                        uid_dict['component'] = 'source'

                    # If str reverse is in cmp, it is a connector
                    elif node + '.reverse' in cmp_input or '.reverse' in node:
                        uid_dict['component'] = 'connector'

                    else:
                        uid_dict['component'] = 'transformer'

                if 'StorageModel' in optimized_es.componentModelingDict:
                    if node in optimized_es.componentModelingDict['StorageModel'].componentsDict:
                        uid_dict['component'] = 'storage'
                uid = nts.Uid(**uid_dict)
            else:
                uid = prelim_uid

            _uid_nodes[str(node)] = uid

        return _uid_nodes

    @log.timings
    def _map_edges(self, optimized_es):
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)
        edges = list()
        for node in cmp_input:
            # Start: determine the cmp source specific variables: dimension, commodity and sign
            dim = getattr(cmp_input[node], 'dimension')
            # 2d -> indicator for transmission component. 1d indicator for edge component
            if hasattr(cmp_input[node], 'commodity'):
                # commodity is not part of e.g conversion (multiple commodities)
                com = getattr(cmp_input[node], 'commodity')
            else:
                com = 'none'  # If the cmp has no commodity its defined as none for error handling
            if hasattr(cmp_input[node], 'sign'):
                # sign is not part of e.g storage (two way)
                sign = getattr(cmp_input[node], 'sign')
            else:
                sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling

            # indicator for link of the specific commodity (grid cmp)
            if dim == '2dim':
                source = node
                for target in cmp_input:
                    # Determine target specific variables (DIM, SIGN and COMMODITY)
                    target_dim = getattr(cmp_input[target], 'dimension')
                    if hasattr(cmp_input[target], 'commodity'):
                        # commodity is not part of e.g conversion (two commodities)
                        target_com = getattr(cmp_input[target], 'commodity')
                    else:
                        target_com = 'none'  # If the cmp has no commodity its defined as none for error handling
                    if hasattr(cmp_input[target], 'sign'):
                        # sign is +1 for Source and -1 for Sink (one way)
                        target_sign = getattr(cmp_input[target], 'sign')
                    else:
                        target_sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling
                    # Source adding to edges for each commodity
                    if target_com == com and target_sign == 1 and target_dim == '1dim':
                        edges.append(nts.Edge(str(target), str(source)))
                    # Sink adding to edges for each commodity
                    if target_com == com and target_sign == -1:
                        edges.append(nts.Edge(str(source), str(target)))
                    # Storage adding to edges (indicator: no sign cause two way use)
                    if target_com == com and target_dim == '1dim' and target_sign == 0:
                        # Grid loading the storage
                        edges.append(nts.Edge(str(source), str(target)))
                        # Storage feed in grid
                        edges.append(nts.Edge(str(target), str(source)))

            # Conversion needs to be added in both ways and beforehand determined what is inflow commodity
            if dim == '1dim' and com == 'none' and sign == 0:
                source = node
                if '.reverse' in source:
                    source = source.partition('.')[0]
                # Conversion specific variables (whats goes in and what comes out)
                commodity_factors = getattr(
                    cmp_input[node], 'commodityConversionFactors')
                # Checking which commodity is set negative -> representing inflow for conversion
                inflows, outflows = _parse_commodity_factors(
                    commodity_factors)

                # inflows = dict((k, v)
                #                for k, v in commodity_factors.items() if v < 0)
                # outflows = dict((k, v)
                #                 for k, v in commodity_factors.items() if v > 0)

                for target in cmp_input:
                    if '.reverse' in target:
                        target = target.partition('.')[0]
                    # Determine target specific variables (DIM, SIGN and COMMODITY)
                    target_dim = getattr(cmp_input[target], 'dimension')
                    if hasattr(cmp_input[target], 'sign'):
                        target_sign = getattr(cmp_input[target], 'sign')
                    else:
                        target_sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling
                    if hasattr(cmp_input[target], 'commodity'):
                        target_com = getattr(cmp_input[target], 'commodity')
                    else:
                        # commodity is not part of conversion (multiple commodities)
                        target_com = 'none'  # If the cmp has no commodity its defined as none for error handling

                    # Conversion of commodity producing energy unit and feed it into grid with same commodity
                    for outflow in outflows:
                        if target_dim == '2dim' and target_sign == 0 and target_com == outflow:
                            edges.append(nts.Edge(str(source), str(target)))
                    # Conversion needs to be feed by specific commodity from a 2dim grid which is then transformed
                    for inflow in inflows:
                        if target_dim == '2dim' and target_sign == 0 and target_com == inflow:
                            edges.append(nts.Edge(str(target), str(source)))
        return edges

    @log.timings
    def _map_edge_uids(self, optimized_es):
        """
        Return string representation of (inflow, node) labels as :class:`list`
        """
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)

        edges_uid = list()
        for node in cmp_input:
            # Start: determine the cmp source specific variables: dimension, commodity and sign
            dim = getattr(cmp_input[node], 'dimension')
            # 2d -> indicator for transmission component. 1d indicator for edge component
            if hasattr(cmp_input[node], 'commodity'):
                # commodity is not part of e.g conversion (multiple commodities)
                com = getattr(cmp_input[node], 'commodity')
            else:
                com = 'none'  # If the cmp has no commodity its defined as none for error handling
            if hasattr(cmp_input[node], 'sign'):
                # sign is not part of e.g storage (two way)
                sign = getattr(cmp_input[node], 'sign')
            else:
                sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling

            # indicator for link of the specific commodity (grid cmp)
            if dim == '2dim':
                source = node
                for target in cmp_input:
                    # Determine target specific variables (DIM, SIGN and COMMODITY)
                    target_dim = getattr(cmp_input[target], 'dimension')
                    if hasattr(cmp_input[target], 'commodity'):
                        # commodity is not part of e.g conversion (two commodities)
                        target_com = getattr(cmp_input[target], 'commodity')
                    else:
                        target_com = 'none'  # If the cmp has no commodity its defined as none for error handling
                    if hasattr(cmp_input[target], 'sign'):
                        # sign is +1 for Source and -1 for Sink (one way)
                        target_sign = getattr(cmp_input[target], 'sign')
                    else:
                        target_sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling
                    # Source adding to edges_uid for each commodity
                    if target_com == com and target_sign == 1 and target_dim == '1dim':
                        edges_uid.append(
                            nts.Edge(optimized_es.uid_dict[target], optimized_es.uid_dict[source]))
                    # Sink adding to edges_uid for each commodity
                    if target_com == com and target_sign == -1:
                        edges_uid.append(
                            nts.Edge(optimized_es.uid_dict[source], optimized_es.uid_dict[target]))
                    # Storage adding to edges_uid (indicator: no sign cause two way use in and out of the grid)
                    if target_com == com and target_dim == '1dim' and target_sign == 0:
                        # Grid loading the storage
                        edges_uid.append(
                            nts.Edge(optimized_es.uid_dict[source], optimized_es.uid_dict[target]))
                        # Storage feed in grid
                        edges_uid.append(
                            nts.Edge(optimized_es.uid_dict[target], optimized_es.uid_dict[source]))

            # Conversion needs to be added in both ways and beforehand determined what is inflow commodity
            if dim == '1dim' and com == 'none' and sign == 0:
                source = node
                # Conversion specific variables (whats goes in and what come out)
                commodity_factors = getattr(
                    cmp_input[node], 'commodityConversionFactors')
                # Checking which commodity is set negative -> representing inflow for conversion
                inflows = dict((k, v)
                               for k, v in commodity_factors.items() if v < 0)
                outflows = dict((k, v)
                                for k, v in commodity_factors.items() if v > 0)

                for target in cmp_input:
                    # Determine target specific variables (DIM, SIGN and COMMODITY)
                    target_dim = getattr(cmp_input[target], 'dimension')
                    if hasattr(cmp_input[target], 'sign'):
                        target_sign = getattr(cmp_input[target], 'sign')
                    else:
                        target_sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling
                    if hasattr(cmp_input[target], 'commodity'):
                        target_com = getattr(cmp_input[target], 'commodity')
                    else:
                        # commodity is not part of conversion (multiple commodities)
                        target_com = 'none'  # If the cmp has no commodity its defined as none for error handling

                    # Conversion of commodity producing energy unit and feed it into grid with same commodity
                    for outflow in outflows:
                        if target_dim == '2dim' and target_sign == 0 and target_com == outflow:
                            edges_uid.append(
                                nts.Edge(optimized_es.uid_dict[source], optimized_es.uid_dict[target]))
                    # Conversion needs to be feed by specific commodity which is then transformed
                    for inflow in inflows:
                        if target_dim == '2dim' and target_sign == 0 and target_com == inflow:
                            edges_uid.append(
                                nts.Edge(optimized_es.uid_dict[target], optimized_es.uid_dict[source]))
        edges = edges_uid
        return edges

    @staticmethod
    def _cmp_input(optimized_es):
        """
        Returns the component specific values, defined by fine as DataFrame containing all relevant informations. The
        component input dataframe is a usefull gathering of all relevant informations of a single node and all existing
        nodes of an energy system.
        """
        es = optimized_es
        cmp_input = dict()
        for mtype in es.componentModelingDict:
            for node in es.componentNames:
                Node = getattr(
                    es.componentModelingDict[mtype], 'componentsDict').get(node)
                if Node is not None:
                    cmp_input.update({node: Node})
        return cmp_input

    def _re_indexing(self, optimized_es):
        """
        Return the optimized energy system with concrete timeframe as index of in all later on used results.
        """
        es = optimized_es

        for mtype in es.componentModelingDict:
            if hasattr(es.componentModelingDict[mtype], 'operationVariablesOptimum'):
                if getattr(es.componentModelingDict[mtype], 'operationVariablesOptimum') is not None:
                    indexing = getattr(
                        es.componentModelingDict[mtype], 'operationVariablesOptimum')
                    indexing.columns = es.timesteps
            if hasattr(es.componentModelingDict[mtype], 'chargeOperationVariablesOptimum'):
                if getattr(es.componentModelingDict[mtype], 'chargeOperationVariablesOptimum') is not None:
                    indexing = getattr(
                        es.componentModelingDict[mtype], 'chargeOperationVariablesOptimum')
                    indexing.columns = es.timesteps
            if hasattr(es.componentModelingDict[mtype], 'dischargeOperationVariablesOptimum'):
                if getattr(es.componentModelingDict[mtype], 'dischargeOperationVariablesOptimum') is not None:
                    indexing = getattr(
                        es.componentModelingDict[mtype], 'dischargeOperationVariablesOptimum')
                    indexing.columns = es.timesteps
            if hasattr(es.componentModelingDict[mtype], 'stateOfChargeOperationVariablesOptimum'):
                if getattr(es.componentModelingDict[mtype], 'stateOfChargeOperationVariablesOptimum') is not None:
                    indexing = getattr(
                        es.componentModelingDict[mtype], 'stateOfChargeOperationVariablesOptimum')
                    indexing.columns = es.timesteps

        # This fragment is crucial if the actual used storages do have any emissions
        # -> if conversion components added to the es which charge/discharge the storage.
        # Storage commodity is renamed due to precise formulation for the optimization process -> name it back
        # conversion input/output need to be deleted for post processing capabillities
        for node in es.componentNames:
            if '.input' in node or '.output' in node:
                storage = node.partition('.')[0]
                com = es.componentModelingDict['StorageModel'].componentsDict[storage].commodity.partition(
                    '+')[0]
                es.componentModelingDict['StorageModel'].componentsDict[storage].commodity = com
                if node in es.componentModelingDict['ConversionModel'].componentsDict:
                    del [es.componentModelingDict['ConversionModel'].componentsDict[node]]

        return es

    def _ts_results(self, optimized_es):
        """
        Time series results is a gatherer for all relevant results within the fine energy system. It is iterating
        through the result series of the ES, bringing them all in one and start reforming the values to tessifs shape.
        """
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(optimized_es)

        time_series_results = pd.DataFrame()
        for mtype in es.componentModelingDict:
            index_list = list()
            model_series_results = pd.DataFrame()
            if hasattr(es.componentModelingDict[mtype], 'operationVariablesOptimum'):
                # Grabbing SourceSink + Conversion + Storage Dataframe from results representing the loads + CO2
                model_series_results = getattr(es.componentModelingDict[mtype], 'operationVariablesOptimum',
                                               pd.DataFrame())
                if model_series_results is not None:
                    # Renaming the indexes of the modelresults to delete the location within the header
                    for index_double in model_series_results.index:
                        # Cut header to one level (avoid cutting to one letter with if statement)
                        if len(index_double) == 2:
                            index_list.append(str(index_double[0]))
                        else:
                            index_list.append(str(index_double))
                    model_series_results.index = index_list
                    time_series_results = time_series_results.append(
                        model_series_results)
            if hasattr(es.componentModelingDict[mtype], 'chargeOperationVariablesOptimum'):
                # Grabbing Storage Dataframe from results
                if getattr(es.componentModelingDict[mtype], 'chargeOperationVariablesOptimum') is not None:
                    charge = (getattr(es.componentModelingDict[mtype], 'chargeOperationVariablesOptimum',
                                      pd.DataFrame())).abs()
                    discharge = (getattr(es.componentModelingDict[mtype], 'dischargeOperationVariablesOptimum',
                                         pd.DataFrame())).abs()
                    # Adding Suffix Charge/Discharge to Storage Inflow/Outflow
                    [charge.rename(index={row: row + ' Charge'}, level=0, inplace=True) for row in
                     charge.index.levels[0]]
                    [discharge.rename(index={row: row + ' Discharge'}, level=0, inplace=True) for row in
                     discharge.index.levels[0]]

                    model_series_results = pd.concat(
                        [charge, discharge], axis='index')
                    if model_series_results is not None:
                        for index_double in model_series_results.index:
                            # Cut header to one level (avoid cutting to one letter with if statement)
                            if len(index_double) == 2:
                                index_list.append(str(index_double[0]))
                            else:
                                index_list.append(str(index_double))
                        model_series_results.index = index_list
                        time_series_results = time_series_results.append(
                            model_series_results)

        # when there are components which have no true design variable the processed timeseries has to be the result
        # df = pd.DataFrame()
        for cmp in cmp_input:
            if cmp not in time_series_results.index:
                if cmp not in es.componentModelingDict['TransmissionModel'].componentsDict:
                    if hasattr(cmp_input[cmp], 'processedOperationRateFix'):
                        if cmp_input[cmp].processedOperationRateFix is not None:
                            df = cmp_input[cmp].processedOperationRateFix
                            df.rename(
                                columns={'Default Region': cmp}, inplace=True)
                            df = df.transpose()
                            # reconstruct non multiindex data frame
                            df = pd.DataFrame(df.values.tolist(), index=(
                                cmp,), columns=time_series_results.columns)
                            time_series_results = time_series_results.append(
                                df)
                    if hasattr(cmp_input[cmp], 'processedOperationRateMax'):
                        if cmp_input[cmp].processedOperationRateMax is not None:
                            cap = cmp_input[cmp].capacityMax
                            df = cmp_input[cmp].processedOperationRateMax * cap
                            df.rename(
                                columns={'Default Region': cmp}, inplace=True)
                            df = df.transpose()
                            # reconstruct non multiindex data frame
                            df = pd.DataFrame(df.values.tolist(), index=(
                                cmp,), columns=time_series_results.columns)
                            time_series_results = time_series_results.append(
                                df)

        # Adding Zero Lines for Components that are not calculated in the ESM but taking place
        for cmp in cmp_input:
            if cmp not in time_series_results.index:
                if hasattr(es.componentModelingDict, 'StorageModel'):
                    if cmp in es.componentModelingDict['StorageModel'].componentsDict:
                        if cmp + ' Charge' not in time_series_results.index:
                            time_series_results.loc[cmp + ' Charge'] = 0
                        if cmp + ' Discharge' not in time_series_results.index:
                            time_series_results.loc[cmp + ' Discharge'] = 0
                else:
                    if cmp not in es.componentModelingDict['TransmissionModel'].componentsDict:
                        time_series_results.loc[cmp] = 0

        # fine simulating 0 values sometime to negative very small float, which have to be set as 0
        time_series_results[time_series_results < 0] = 0
        # Transposing Time Series Results to get tessifs shape
        time_series_results = time_series_results.transpose()
        time_series_results.round(decimals=3)
        # Adding the given ESM timeseries as index to work with
        time_series_results.index = es.timesteps

        for node in time_series_results.columns:
            if '.input' in node or '.output' in node:
                time_series_results.drop(node, axis='columns', inplace=True)

        return time_series_results


class IntegratedGlobalResultier(FINEResultier, base.IntegratedGlobalResultier):
    """
    Global Results
    Extracting the integrated global results out of the energy system and
    conveniently aggregating them (rounded to unit place) inside a dictionairy
    keyed by result name.

    Integrated global results (IGR) mapped by result name.

    Integrated global results currently consist of meta and non-meta
    results. the **meta** results are handled by the :mod:`~tessif.analyze`
    module (see :attr:`tessif.analyze.Comparatier.integrated_global_results`)
    and consist of:

        - ``time``
        - ``memory``

    results. whereas the **non-meta** results usually consist of:

        - ``emissions``
        - ``costs``

    results, which are handled here. Tessif's energy system, however, allow to
    formulate a number of
    :attr:`~tessif.model.energy_system.AbstractEnergySystem.global_constraints`
    which then would automatically be post processed here.

    The befornamed strings serve as key inside the mapping.

    Note
    ----
    Capacity costs calculated within the optimizing process in fine are related to the overall capacities
    which are installed in the energy system and not only to the new build capacity of the component.
    This results in differences in simulated costs compared to the post processed costs.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.IntegratedGlobalResultier>`.

    Examples
    --------

    1. Accessing the global results, containing simulated costs and emissions,
    as well as post processed flow and capacity costs:

        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> resultier = post_process_fine.IntegratedGlobalResultier(
        ...     coded_fine_examples.create_expansion_example())
        >>> print(resultier.global_results)
        {'emissions (sim)': 20.0, 'costs (sim)': 41.0, 'opex (ppcd)': 40.0, 'capex (ppcd)': 1.0}

    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_global_results(self, optimized_es):
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)
        load_res = LoadResultier(es)
        cap_res = CapacityResultier(es)
        flow_res = FlowResultier(es)
        ts_results = self._ts_results(es)

        # Simulated overall costs
        total_costs = float('+inf')
        if hasattr(es, 'objectiveValue'):
            if getattr(es, 'objectiveValue') is not None:
                total_costs = es.objectiveValue * es.numberOfYears
                # ---------- CAPEX - Recalculation -------------
                # If the value investPerCapacity is available, the already installed capacities of the component are
                # also included in the total costs of the simulation. these must be subsequently calculated out in order
                # to ensure comparability.
                for node in self.nodes:
                    if node in ts_results:
                        initial_capacity = cap_res.node_original_capacity[node]
                        final_capacity = cap_res.node_installed_capacity[node]
                        expansion_cost = float(
                            getattr(cmp_input[node], 'investPerCapacity').values)
                        # expansion_cost = cap_res.node_expansion_costs[node]

                        # The so far installed capacity costs need to be deducted if they are used in the fine esm
                        if getattr(cmp_input[node], 'capacityMin') is not None:
                            if getattr(cmp_input[node], 'capacityMin').values != 0.0:
                                capacityMin = float(
                                    getattr(cmp_input[node], 'capacityMin').values)
                                initial_cost = capacityMin * expansion_cost
                                total_costs -= initial_cost

        total_emissions = float('+inf')
        if hasattr(es, 'emission_default'):
            emission_default = es.emission_default
            if emission_default in ts_results:
                total_emissions = sum(ts_results[emission_default])
        else:
            for limit in cmp_input:
                if hasattr(cmp_input[limit], 'yearlyLimit'):
                    if getattr(cmp_input[limit], 'yearlyLimit') is not None:
                        simLimit = cmp_input[limit].yearlyLimit * \
                            es.numberOfYears
                        total_emissions = sum(ts_results[limit])
                        if simLimit < total_emissions:
                            print('constrained wrong')

        emissions_ppcd = 0.0
        for edge in flow_res.edges:
            edge_emission_ppcd = flow_res.edge_specific_emissions[edge] * \
                flow_res.edge_net_energy_flow[edge]
            emissions_ppcd += edge_emission_ppcd

        # Outflow based post-processed  OPEX results
        opex_ppcd = dict()
        for edge in self.edges:
            opex_ppcd[edge] = float(
                flow_res.edge_specific_flow_costs[edge] * flow_res.edge_net_energy_flow[edge])
        flow_costs = sum(opex_ppcd.values())

        # Capex post-processed
        capital_costs = 0.0
        for node in self.nodes:
            if getattr(cmp_input[node], 'investPerCapacity').values != 0:
                initial_capacity = pd.Series(
                    cap_res.node_original_capacity[node])
                final_capacity = pd.Series(
                    cap_res.node_installed_capacity[node])
                # expansion_cost = float(getattr(cmp_input[node], 'investPerCapacity').values)
                expansion_cost = cap_res.node_expansion_costs[node]

                if not any([cap is None for cap in (final_capacity, initial_capacity)]):
                    node_expansion_costs = (
                        (final_capacity - initial_capacity) * expansion_cost)
                else:
                    node_expansion_costs = 0.0

                if isinstance(initial_capacity, pd.Series):
                    node_expansion_costs = sum(node_expansion_costs)

                # If the actual used capacity in the esM is smaller than the initially one negative expansion costs occur
                # to avoid negative capital costs, smaller than zero costs are capped to zero
                if node_expansion_costs < 0:
                    node_expansion_costs = 0.0

                capital_costs += node_expansion_costs

        return {
            'emissions (sim)': round(total_emissions, 0),
            'costs (sim)': round(total_costs, 0),
            'opex (ppcd)': round(flow_costs, 0),
            'capex (ppcd)': round(capital_costs, 0),
        }


class ScaleResultier(FINEResultier, base.ScaleResultier):
    """
    Extract number of constraints and store them as int.

    Parameters
    ----------
    optimized_es:
        :ref:`Model <SupportedModels>` specific, optimized energy system
        containing its results.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.ScaleResultier>`.

    Examples
    --------
    1. Call and optimize a FINE energy system model.
    >>> # import post fine processing and example modules:
    >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
    >>> import tessif.transform.es2mapping.fine as post_process_fine

    >>> # optimize the energy system:
    >>> fine_es = coded_fine_examples.create_mwe()

    >>> # post process the capacity results:
    >>> resultier = post_process_fine.ScaleResultier(fine_es)

    2. Access the number of constraints.

    >>> print(resultier.number_of_constraints)
    27
    """
    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    def _map_number_of_constraints(self, optimized_es):
        """Interface to extract the number of constraints out of the
        :ref:`model <SupportedModels>` specific, optimized energy system.
        """
        optimized_es.pyM.compute_statistics()
        return optimized_es.pyM.statistics.number_of_constraints


class LoadResultier(FINEResultier, base.LoadResultier):
    """
    Loads2mapping
    Transforming flow results into dictionairies keyed by node uid string
    representation.

    Parameters
    ----------
    optimized_es: fine energy system model
       An optimized fine energy system containing its results

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.LoadResultier>`.

    Examples
    --------
    1. Accessing a node's outflows as positive numbers and a node's inflows as
       negative numbers:
       (See :attr:`tessif.transform.es2mapping.base.LoadResultier.node_load`
       for more documentation):

        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> resultier = post_process_fine.LoadResultier(
        ...     coded_fine_examples.chp_example())
        >>> print(resultier.node_load['CHP'])
        CHP                   Gas Grid  Heat Grid  Power Line
        1990-07-13 00:00:00 -33.333333   6.666667        10.0
        1990-07-13 01:00:00 -33.333333   6.666667        10.0
        1990-07-13 02:00:00 -33.333333   6.666667        10.0
        1990-07-13 03:00:00 -33.333333   6.666667        10.0

    2. Accessing a node's inflows as positive numbers
       (See :attr:`tessif.transform.es2mapping.base.LoadResultier.node_inflows`
       for more documentation):

        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> resultier = post_process_fine.LoadResultier(
        ...     coded_fine_examples.chp_example())
        >>> print(resultier.node_inflows['CHP'])
        CHP                   Gas Grid
        1990-07-13 00:00:00  33.333333
        1990-07-13 01:00:00  33.333333
        1990-07-13 02:00:00  33.333333
        1990-07-13 03:00:00  33.333333

    3. Accessing a node's outflows as positive numbers (See
       :attr:`tessif.transform.es2mapping.base.LoadResultier.node_outflows`
       for more documentation):

        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> resultier = post_process_fine.LoadResultier(
        ...     coded_fine_examples.chp_example())
        >>> print(resultier.node_outflows['CHP'])
        CHP                  Heat Grid  Power Line
        1990-07-13 00:00:00   6.666667        10.0
        1990-07-13 01:00:00   6.666667        10.0
        1990-07-13 02:00:00   6.666667        10.0
        1990-07-13 03:00:00   6.666667        10.0

    4. Accessing a node's summed inflows as positive numbers (in case it is
       of component
       :attr:`sink <tessif.frused.defaults.registered_component_types>`)
       or a node's summed outflows (in case it is not a sink).
       (See
       :attr:`tessif.transform.es2mapping.base.LoadResultier.node_summed_loads`
       for more documentation):

        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> resultier = post_process_fine.LoadResultier(coded_fine_examples.chp_example())
        >>> print(resultier.node_summed_loads['CHP'])
        1990-07-13 00:00:00    16.666667
        1990-07-13 01:00:00    16.666667
        1990-07-13 02:00:00    16.666667
        1990-07-13 03:00:00    16.666667
        Freq: H, dtype: float64
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_loads(self, optimized_es):
        """ Map loads to node labels"""
        time_series_results = self._ts_results(optimized_es)
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)

        # Use defaultdict of empty DataFrame as loads container:
        _loads = defaultdict(lambda: pd.DataFrame())
        for node in self.nodes:
            inflows = pd.DataFrame()
            outflows = pd.DataFrame()
            for ntype in self.nodes:
                if ntype != node:
                    # Declaring node specific variables
                    node_dim = getattr(cmp_input[node], 'dimension')
                    if hasattr(cmp_input[node], 'commodity'):
                        # commodity is not part of e.g conversion (multiple commodities)
                        node_com = getattr(cmp_input[node], 'commodity')
                    else:
                        node_com = 'none'
                    if hasattr(cmp_input[node], 'sign'):
                        # sign is +1 for Source and -1 for Sink (one way)
                        node_sign = getattr(cmp_input[node], 'sign')
                    else:
                        node_sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling

                    # Declaring ntype specific variables
                    type_dim = getattr(cmp_input[ntype], 'dimension')
                    if hasattr(cmp_input[ntype], 'commodity'):
                        # commodity is not part of e.g conversion (two commodities)
                        type_com = getattr(cmp_input[ntype], 'commodity')
                    else:
                        type_com = 'none'  # If the cmp has no commodity its defined as none for error handling
                    if hasattr(cmp_input[ntype], 'sign'):
                        type_sign = getattr(cmp_input[ntype], 'sign')
                    else:
                        type_sign = 0  # If the cmp has no sign +1/-1 its defined as 0 for error handling

                    # Actual Mapping starts here:
                    # Adding Grid Component with all loads included which show in/out
                    if node_dim == '2dim':
                        # Defining Node/Type and Target/Load to assign dim, sign and com for both
                        target, load = node, ntype
                        target_dim, target_com, target_sign = node_dim, node_com, node_sign
                        load_dim, load_com, load_sign = type_dim, type_com, type_sign
                        # Adding Source and Sinks as loads of the Grid
                        # Source is inflow
                        if load_com == target_com and load_dim == '1dim' and load_sign == 1:
                            col_name = [col for col in time_series_results.columns
                                        if load in col and len(col) == len(load)]
                            inflows = pd.concat(
                                [inflows, time_series_results[col_name].multiply(-1)], axis='columns')
                        # Sink is outflow
                        if load_com == target_com and load_dim == '1dim' and load_sign == -1:
                            col_name = [col for col in time_series_results.columns
                                        if load in col and len(col) == len(load)]
                            outflows = pd.concat(
                                [outflows, time_series_results[col_name]], axis='columns')
                        # Conversion is tricky: Results represent the outflow -> recalculate the inflow from that
                        if load_com == 'none':
                            col_name = [col for col in time_series_results.columns
                                        if load in col and len(col) == len(load)]
                            # Feed stands for the results feed from the Conversion-ModelingDict
                            conv_feed = pd.DataFrame(
                                time_series_results[col_name])
                            # Next step is determining the inflow and outflow factors for recalculating
                            commodity_factors = getattr(
                                cmp_input[load], 'commodityConversionFactors')

                            conv_in_com, conv_out_com = _parse_commodity_factors(
                                commodity_factors)

                            # conv_in_com = dict(
                            #     (k, v) for k, v in commodity_factors.items() if v < 0)
                            # conv_out_com = dict(
                            #     (k, v) for k, v in commodity_factors.items() if v > 0)

                            # If the target commodity equals the factor name which is identical to the commodity names
                            # the for-loop declares the inflow for the grid and multiply it with the
                            # conversion factor (=efficiency)
                            for factor_out in conv_out_com:
                                if factor_out == target_com:
                                    conv_factor = conv_out_com[factor_out]

                                    if isinstance(conv_factor, pd.Series):
                                        conv_outflow = inflows.apply(
                                            lambda x: np.asarray(x) * np.asarray(conv_factor))
                                    else:
                                        conv_outflow = conv_feed.multiply(
                                            conv_factor)

                                    # conv_outflow = conv_feed.multiply(
                                    #     conv_factor)
                                    # From sight of Grid the Transformer is signed as inflow
                                    inflows = pd.concat(
                                        [inflows, conv_outflow.multiply(-1)], axis='columns')

                                    # Adding Connector Outflows to Grid results
                                    if load+'.reverse' in cmp_input:
                                        outflows = pd.concat(
                                            [outflows, time_series_results[load+'.reverse']], axis='columns')
                                        outflows.rename(
                                            columns={load+'.reverse': load.partition('.')[0]}, inplace=True)

                            # Same procedure for the inflows of the trfo representing the outflows of the grid component
                            # no conversion factor is needed due to the efficiency is related to elec. production
                            for factor_in in conv_in_com:
                                if factor_in == target_com:
                                    # From sight of grid the Transformer is signed as outflow
                                    outflows = pd.concat(
                                        [outflows, conv_feed], axis='columns')

                                    # Adding Connector Inflows to Grid results
                                    if load+'.reverse' in cmp_input:
                                        rev_conv = getattr(
                                            cmp_input[load+'.reverse'], 'commodityConversionFactors')
                                        inflows = pd.concat(
                                            [inflows, time_series_results[load+'.reverse'].multiply(-rev_conv[factor_in])], axis='columns')
                                        inflows.rename(
                                            columns={load+'.reverse': load.partition('.')[0]}, inplace=True)

                        # Adding Storage for both ways in and out grid
                        if target_com == load_com and target_sign == 0 and load_sign == 0:
                            # Charge from Grid to Sto -> Outflow
                            col_name = [col for col in time_series_results.columns
                                        if str(load + ' Charge') in col and len(col) == len(load + ' Charge')]
                            outflows = pd.concat(
                                [outflows, time_series_results[col_name]], axis='columns')
                            outflows.rename(
                                columns={load + ' Charge': load}, inplace=True)
                            # Discharge from Sto to Grid -> Inflow
                            col_name = [col for col in time_series_results.columns
                                        if str(load + ' Discharge') in col and len(col) == len(load + ' Discharge')]
                            inflows = pd.concat(
                                [inflows, time_series_results[col_name].multiply(-1)], axis='columns')
                            inflows.rename(
                                columns={load + ' Discharge': load}, inplace=True)

                        # Handling generated data and storing it in loads
                        if not outflows.empty or not inflows.empty:
                            inflows = inflows.replace(
                                {float(0): -float(0), float(0): -float(0)})
                            outflows = outflows.replace({-float(0): float(0)})
                            temp_df = pd.concat(
                                [inflows, outflows], axis='columns')
                            temp_df.columns.name = str(node)
                            _loads[str(node)] = temp_df

                    # Adding Source, Sink and Conversion as Target and generating load values
                    if node_dim == '1dim':  # Indicator for single attached nodes by loads
                        # Defining Node/Type and Target/Load to assign dim, sign and com for both
                        target, load = ntype, node
                        target_dim, target_com, target_sign = type_dim, type_com, type_sign
                        load_dim, load_com, load_sign = node_dim, node_com, node_sign

                        # Target to which the load flows
                        # Adding Sources and its loads -> inflows
                        if load_com == target_com and load_sign == 1 and target_dim == '2dim':
                            col_name = [col for col in time_series_results.columns
                                        if load in col and len(col) == len(load)]
                            outflows = pd.concat(
                                [outflows, time_series_results[col_name]], axis='columns')
                            outflows.rename(
                                columns={load: target}, inplace=True)
                        # Adding Sinks and its loads -> outflow
                        if load_com == target_com and load_sign == -1 and target_dim == '2dim':
                            col_name = [col for col in time_series_results.columns
                                        if load in col and len(col) == len(load)]
                            inflows = pd.concat(
                                [inflows, time_series_results[col_name]], axis='columns').multiply(-1)
                            inflows.rename(
                                columns={load: target}, inplace=True)

                        # Adding Storages and its loads
                        if load_com == target_com and load_sign == 0 and target_dim == '2dim':
                            # Charge from Grid to Sto -> Outflow
                            col_name = [col for col in time_series_results.columns
                                        if str(load + ' Discharge') in col and len(col) == len(load + ' Discharge')]
                            outflows = pd.concat(
                                [outflows, time_series_results[col_name]], axis='columns')
                            outflows.rename(
                                columns={load + ' Discharge': target}, inplace=True)
                            # Discharge from Sto to Grid -> Inflow
                            col_name = [col for col in time_series_results.columns
                                        if str(load + ' Charge') in col and len(col) == len(load + ' Charge')]
                            inflows = pd.concat(
                                [inflows, time_series_results[col_name].multiply(-1)], axis='columns')
                            inflows.rename(
                                columns={load + ' Charge': target}, inplace=True)

                        # Handling generated data and storing it in loads
                        if not outflows.empty or not inflows.empty:
                            # inflows = inflows.multiply(-1)
                            inflows = inflows.replace(
                                {0: -float(0), float(0): -float(0)})
                            outflows = outflows.replace({-float(0): float(0)})
                            temp_df = pd.concat(
                                [inflows, outflows], axis='columns')
                            temp_df.columns.name = str(node)
                            _loads[str(node)] = temp_df
                            break

                    # Adding Conversion as target and its loads to/from grid
                    if node_com == 'none':
                        target, load = node, ntype
                        target_dim, target_com, target_sign = node_dim, node_com, node_sign
                        load_dim, load_com, load_sign = type_dim, type_com, type_sign
                        if load_dim == '2dim':
                            # Finding inflow of Transformer representing the outflow from the grid
                            col_name = [col for col in time_series_results.columns
                                        if target in col and len(col) == len(target)]
                            inflows = pd.concat(
                                [inflows, time_series_results[col_name]], axis='columns')
                            # Finding outflow of Transformer and the correct grid commodity
                            commodity_factors = getattr(
                                cmp_input[node], 'commodityConversionFactors')

                            conv_in, conv_out = _parse_commodity_factors(
                                commodity_factors)
                            # conv_in = dict(
                            #     (k, v) for k, v in commodity_factors.items() if v < 0)
                            # conv_out = dict(
                            #     (k, v) for k, v in commodity_factors.items() if v > 0)

                            for factor_out in conv_out:
                                # if factor_out == load_com:
                                conv_factor = conv_out[factor_out]

                                if isinstance(conv_factor, pd.Series):
                                    outflow = inflows.apply(
                                        lambda x: np.asarray(x) * np.asarray(conv_factor))
                                else:
                                    outflow = inflows.multiply(conv_factor)
                                # Next step is to define which product flows into which grid and create the outflows
                                for grid in es.componentModelingDict['TransmissionModel'].componentsDict:
                                    grid_com = getattr(
                                        cmp_input[grid], 'commodity')
                                    if grid_com == factor_out:
                                        outflow.rename(
                                            columns={target: grid}, inplace=True)
                                        outflows = pd.concat(
                                            [outflows, outflow], axis='columns')
                            # Renaming: Grid Finder -> search for the correct transmission component
                            for key in conv_in.keys():
                                for grid in self.nodes:
                                    grid_dim = getattr(
                                        cmp_input[grid], 'dimension')
                                    if grid_dim == '2dim':
                                        grid_com = getattr(
                                            cmp_input[grid], 'commodity')
                                        if grid_com == key:
                                            inflows.rename(
                                                columns={target: grid}, inplace=True)

                        # Handling generated data and storing it in loads
                        if not outflows.empty or not inflows.empty:
                            inflows = inflows.multiply(-1)
                            inflows = inflows.replace(
                                {0: -float(0), float(0): -float(0)})
                            outflows = outflows.replace({-float(0): float(0)})
                            temp_df = pd.concat(
                                [inflows, outflows], axis='columns')
                            # If emitting Source is added as transformer -> delete "inflow" from unlimitted source
                            if node in temp_df.columns:
                                temp_df.drop([node], axis=1, inplace=True)
                            temp_df.columns.name = str(node)
                            _loads[str(node)] = temp_df
                            break

        # Connector component is present as two transformers -> combine them:
        _loads = _loads
        for node in cmp_input:
            if '.reverse' in node:

                connector = node.partition('.')[0]
                commodity_factors = getattr(
                    cmp_input[connector], 'commodityConversionFactors')
                conv_out = dict((k, v)
                                for k, v in commodity_factors.items() if v > 0)
                for conv in conv_out:
                    # Conversion Factor is related to the reverse grid
                    grid_rev = conv.partition('.')[0]
                    value = float(conv_out[conv])

                connector_rev = node
                commodity_factors_rev = getattr(
                    cmp_input[connector_rev], 'commodityConversionFactors')
                conv_out_rev = dict(
                    (k, v) for k, v in commodity_factors_rev.items() if v > 0)
                for conv_rev in conv_out_rev:
                    # related to the original grid
                    grid = conv_rev.partition('.')[0]
                    value_rev = float(conv_out_rev[conv_rev])

                # Inflows representing the first connector way 1 -> 2
                inflows = pd.concat(
                    [time_series_results[connector], time_series_results[connector_rev]], axis='columns')
                inflows.rename(columns={connector: grid}, inplace=True)
                inflows.rename(columns={connector_rev: grid_rev}, inplace=True)
                inflows = inflows.multiply(-1)
                inflows = inflows.replace({0: -float(0), float(0): -float(0)})

                # Outflows representing the second connector way 2 -> 1
                outflows = pd.concat([time_series_results[connector_rev]*value_rev,
                                      time_series_results[connector]*value], axis='columns')
                outflows.rename(columns={connector: grid_rev}, inplace=True)
                outflows.rename(columns={connector_rev: grid}, inplace=True)

                temp_df = pd.concat([inflows, outflows], axis='columns')
                _loads.pop(connector)
                # _loads.pop(connector_rev)
                _loads[str(connector)] = temp_df

        return dict(_loads)


class CapacityResultier(base.CapacityResultier, LoadResultier):
    """
    Capacities2mapping
    Transforming installed capacity results dictionairies keyed by node.

    Parameters
    ----------
    optimized_es: fine energy system model
       An optimized fine energy system containing its results

    Examples
    --------
    1. Accessing the installed capacities and the characteristic values of the
       :attr:`minimum working example
       <tessif.examples.data.fine.create_mwe>`

       (See
       :attr:`tessif.transform.es2mapping.base.CapacityResultier.node_installed_capacity`
       for more documentation):

        >>> # import post fine processing and example modules:
        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine

        >>> # optimize the energy system:
        >>> fine_es = coded_fine_examples.create_mwe()

        >>> # post process the capacity results:
        >>> resultier = post_process_fine.CapacityResultier(fine_es)

        >>> # access the capacity results:
        >>> for node, capacity in resultier.node_installed_capacity.items():
        ...     print(f'{node}: {capacity}')
        PowerLine: None
        CBET: None
        Demand: 10.0
        Renewable: 10.0
        Gas Station: 23.81
        Transformer: 10.0

        >>> # acces the characteristic value results:
        >>> for node, cv in resultier.node_characteristic_value.items():
        ...     if cv is not None:
        ...         cv = round(cv, 2)
        ...     print(f'{node}: {cv}')
        PowerLine: None
        CBET: None
        Demand: 1.0
        Renewable: 0.75
        Gas Station: 0.25
        Transformer: 0.25

    2. Accessing the installed capacities and the characteristic value of the
       :attr:`Storage Example
       <tessif.examples.data.fine.storage_example>`

        >>> # import  fine postprocessing and example modules:
        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine

        >>> # optimize the energy system:
        >>> fine_es = coded_fine_examples.storage_example()

        >>> # post process the capacity results:
        >>> resultier = post_process_fine.CapacityResultier(fine_es)

        >>> # access the capacity results:
        >>> for node, capacity in resultier.node_installed_capacity.items():
        ...     print(f'{node}: {capacity}')
        Power Line: None
        Demand: 10.0
        Generator: 20.0
        Storage: 10.0

        >>> # acces the characteristic value results:
        >>> for node, cv in resultier.node_characteristic_value.items():
        ...     if cv is not None:
        ...         cv = round(cv, 2)
        ...     print(f'{node}: {cv}')
        Power Line: None
        Demand: 0.94
        Generator: 0.47
        Storage: 0.34
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @property
    def node_characteristic_value(self):
        return self._characteristic_values

    @log.timings
    def _map_installed_capacities(self, optimized_es):
        """
        Values are continuously stored over. e.g. Renewable: Have a variable operation rate, but a maximum capacity
        has been set.
        Therefore the op-rate is overstored. If a variable capacity was calculated by fine in order to find an optimum,
        the initially defined op-rate is also stored over here. The logical order is:
        OperationRateFix (e.g Demand) -> capacityVariableOptimum (e.g Gas Import restricted by Transformer)
        -> capacityMax (e.g Renewable set by User and based on fluctuating data).
        """
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)

        _installed_capacities = defaultdict(float)

        for mtype in es.componentModelingDict:
            for node in es.componentModelingDict[mtype].componentsDict:
                if node in self.nodes:
                    # Make sure all busses have installed capacity of 'variable_capacity'
                    if getattr(cmp_input[node], 'dimension') == '2dim':
                        value = esn_defaults['variable_capacity']
                    else:
                        # Start with default for every node
                        value = esn_defaults['installed_capacity']

                    # Getting variable capacities from component Modeling dicts as dataframe
                    if getattr(es.componentModelingDict[mtype], 'capacityVariablesOptimum') is not None:
                        cap = getattr(
                            es.componentModelingDict[mtype], 'capacityVariablesOptimum')
                        value = esn_defaults['installed_capacity']
                        for cmp in cap.index:
                            if node == cmp:
                                value = round(float(cap.loc[node]), 3)

                        # Transformer capacity is yet related to input
                        if mtype == 'ConversionDynamicModel' or mtype == 'ConversionModel':
                            cap = value
                            commodity_factors = getattr(
                                cmp_input[node], 'commodityConversionFactors')
                            # conv_out = dict(
                            #     (k, v) for k, v in commodity_factors.items() if v > 0 and k not in spl.emissions)
                            conv_in, conv_out = _parse_commodity_factors(
                                commodity_factors)
                            conv_out = dict(
                                (key, value) for key, value in conv_out.copy().items()
                                if key not in spl.emissions)

                            # distinguish between multiple or single outflows
                            if len(conv_out) > 1:
                                value = dict()
                                for outflow in conv_out:
                                    temp_cap = round(
                                        cap * conv_out[outflow], 3)
                                    # Finding Grid:
                                    for grid in cmp_input:
                                        if cmp_input[grid].dimension == '2dim' and cmp_input[grid].commodity == outflow:
                                            value.update({grid: temp_cap})
                                value = pd.Series(value)
                            else:

                                grid = self.outbounds[node][0]
                                grid_com = cmp_input[grid].commodity
                                # check for time varying efficiency transformers:
                                if isinstance(conv_out[grid_com], pd.Series):
                                    value = round(
                                        cap * min(conv_out[grid_com]))
                                else:
                                    value = round(cap * conv_out[grid_com], 3)

                    # Sinks do not have a capacity bound, so the installed capacity is taken from the operation rate
                    if hasattr(cmp_input[node], 'operationRateFix'):
                        if getattr(cmp_input[node], 'operationRateFix') is not None:
                            cap = getattr(cmp_input[node], 'operationRateFix')
                            value = round(float(cap.values.max()), 3)

                    # Storing capacity
                    _installed_capacities[node] = value

        # Connector support
        # Connectors do not have a fixed installed capacity why they are always in the variables
        for node in self.nodes:
            if '.reverse' in node:
                temp_df = dict()
                connector_reverse = node
                connector = node.partition('.')[0]
                for grid in self.outbounds:
                    if connector in self.outbounds[grid]:
                        temp_df.update(
                            {grid: _installed_capacities[connector]})
                    if connector_reverse in self.outbounds[grid]:
                        temp_df.update(
                            {grid: _installed_capacities[connector_reverse]})
                _installed_capacities.pop(connector)
                _installed_capacities.pop(connector_reverse)
                _installed_capacities[connector] = temp_df

        # Check if the processed capacity is zero and an initial capacity is
        # given- set initital as installed
        for node in _installed_capacities:
            if isinstance(_installed_capacities[node], abc.Iterable):
                if all(_installed_capacities[node]) == 0.0:
                    _installed_capacities[node] = pd.Series(
                        self._map_original_capacities(optimized_es)[node])
            else:
                if _installed_capacities[node] == 0.0:
                    _installed_capacities[
                        node] = self._map_original_capacities(optimized_es)[
                            node]

        return dict(_installed_capacities)

    def _map_original_capacities(self, optimized_es):
        """
        Mapping of the previously set capacities before the actual optimisation.

        Similar to capacity mapping,
        but without the fine param: capacityVariablesOptimum.
        """
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)
        ts_results = self._ts_results(es)

        _installed_capacities = defaultdict(float)

        for node in self.nodes:
            cap_min = 0.0
            if cmp_input[node].capacityMin is not None:
                cap_min = round(
                    float((getattr(cmp_input[node], 'capacityMin')).values), 3)
            elif cmp_input[node].capacityMax is not None:
                cap_min = round(
                    float((getattr(cmp_input[node], 'capacityMax')).values), 3)

            if cap_min == 0:
                if cmp_input[node].capacityMax is not None:
                    cap_min = float(
                        (getattr(cmp_input[node], 'capacityMax')).values)

            if hasattr(cmp_input[node], 'commodityConversionFactors'):
                value = cap_min
                commodity_factors = getattr(
                    cmp_input[node], 'commodityConversionFactors')
                # conv_out = dict((k, v) for k, v in commodity_factors.items(
                # ) if v > 0 and k not in spl.emissions)

                conv_in, conv_out = _parse_commodity_factors(
                    commodity_factors)
                conv_out = dict(
                    (key, value) for key, value in conv_out.copy().items()
                    if key not in spl.emissions)

                if len(conv_out) > 1:
                    value = dict()
                    for conv in conv_out:
                        for grid in cmp_input:
                            if cmp_input[grid].dimension == '2dim' and cmp_input[grid].commodity == conv:
                                value.update(
                                    {grid: (cap_min * conv_out[conv])})
                    value = pd.Series(value)
                else:
                    grid_com = cmp_input[self.outbounds[node][0]].commodity

                    # check for time varying efficiency transformers:
                    if isinstance(conv_out[grid_com], pd.Series):
                        value = cap_min * min(conv_out[grid_com])
                    else:
                        value = cap_min * conv_out[grid_com]
                cap_min = value

            _installed_capacities[node] = cap_min

            # Add the maximum used energy by any sink as installed capacity
            if hasattr(cmp_input[node], 'sign'):
                if getattr(cmp_input[node], 'sign') == -1:
                    _installed_capacities[node] = round(
                        max(ts_results[node]), 3)

            # Add maximum from operation rate as installed capacity if the component is fixed
            if cmp_input[node].hasCapacityVariable is False:
                if hasattr(cmp_input[node], 'operationRateFix'):
                    value = max(ts_results[node])
                    _installed_capacities[node] = round(value, 3)

        # Check if all nodes are existend and set if missing original cap to zero
        for node in self.nodes:
            if node not in _installed_capacities:
                _installed_capacities[node] = esn_defaults['installed_capacity']

        return dict(_installed_capacities)

    def _map_expansion_costs(self, optimized_es):
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)
        expansion_costs = dict()

        if hasattr(es, 'expansion_costs'):
            expansion_costs = es.expansion_costs
        else:
            for node in self.nodes:
                if getattr(cmp_input[node], 'investPerCapacity').values != 0:

                    costs = float(
                        getattr(cmp_input[node], 'investPerCapacity').values)
                else:
                    costs = esn_defaults['expansion_costs']
                expansion_costs[node] = costs

        return expansion_costs

    @log.timings
    def _map_characteristic_values(self, optimized_es):
        """Map node uid string representation to characteristic value."""
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)

        _characteristic_values = defaultdict(float)
        for node in es.uid_dict:
            node_dim = getattr(cmp_input[node], 'dimension')
            if node_dim == '2dim':  # Indicator for Grid which is always variable
                _characteristic_values[node] = esn_defaults['characteristic_value']
            else:
                node_installed_capacities = self.node_installed_capacity[node]

                if isinstance(node_installed_capacities, abc.Iterable):
                    multi_char_val = dict()
                    for cap in node_installed_capacities.index:
                        if node_installed_capacities[cap] > 0:
                            # print(self.node_outflows)
                            # print(node_installed_capacities[cap])
                            # print("node:", node)
                            # print("cap:", cap)
                            temp_value = self.node_outflows[node][cap].mean(axis='index') / node_installed_capacities[
                                cap]
                            multi_char_val.update({cap: round(temp_value, 2)})
                        else:
                            multi_char_val.update({cap: 0.0})

                    _characteristic_values[node] = pd.Series(multi_char_val)

                else:
                    if node_installed_capacities != 0:
                        char_mean = abs(
                            self.node_summed_loads[node].mean(axis='index'))
                        _characteristic_values[node] = round(
                            char_mean / node_installed_capacities, 2)
                        if _characteristic_values[node] > 1.0:
                            _characteristic_values[node] = 1.0
                    else:
                        _characteristic_values[node] = 0.0

                if 'StorageModel' in es.componentModelingDict:
                    if node in es.componentModelingDict['StorageModel'].componentsDict:
                        if node_installed_capacities != 0:
                            char_mean = abs(StorageResultier(
                                es).node_soc[node].mean(axis='index'))
                            _characteristic_values[node] = round(
                                char_mean / node_installed_capacities, 2)
                        else:
                            _characteristic_values[node] = 0.0

        return dict(_characteristic_values)


class StorageResultier(FINEResultier, base.StorageResultier):
    r""" Transforming storage results into dictionairies keyed by node.

    Parameters
    ----------
    optimized_es: fine energy system
        An optimized fine energy system containing its results

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.StorageResultier>`.

    Examples
    --------

    1.  Display a storage-node's capacity:

        Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
        logging level to debug for decluttering doctest output:

        >>> from tessif.frused import configurations
        >>> configurations.spellings_logging_level = 'debug'

        Actual Example:

        >>> # import post fine processing and example modules:
        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine

        >>> # optimize the energy system:
        >>> fine_es = coded_fine_examples.storage_example()

        >>> # post process the capacity results:
        >>> resultier = post_process_fine.StorageResultier(fine_es)

        >>> print(post_process_fine.StorageResultier(fine_es).node_soc['Storage'])
        1990-07-13 00:00:00     0.0
        1990-07-13 01:00:00     0.0
        1990-07-13 02:00:00     7.0
        1990-07-13 03:00:00     0.0
        1990-07-13 04:00:00    10.0
        Freq: H, Name: Storage, dtype: float64
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_states_of_charge(self, optimized_es):
        """ Map storage labels to their states of charge. The present value for the SOC calculated by fine,
        describes the pure time sequence of charging and discharging and can therefore not be determined from
        the operation variable optimum values. Example can be seen if the Storage example is simulated

        --------
        Examples
        >>> # import post fine processing and example modules:
        >>> import tessif.examples.data.fine.py_hard as coded_fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine

        >>> # optimize the energy system:
        >>> fine_es = coded_fine_examples.storage_example()

        >>> print(post_process_fine.StorageResultier(fine_es).node_soc['Storage'])
        1990-07-13 00:00:00     0.0
        1990-07-13 01:00:00     0.0
        1990-07-13 02:00:00     7.0
        1990-07-13 03:00:00     0.0
        1990-07-13 04:00:00    10.0
        Freq: H, Name: Storage, dtype: float64
        >>> print(post_process_fine.LoadResultier(fine_es).node_load['Storage'])
        Storage              Power Line  Power Line
        1990-07-13 00:00:00        -0.0         0.0
        1990-07-13 01:00:00        -7.0         0.0
        1990-07-13 02:00:00        -0.0         7.0
        1990-07-13 03:00:00       -10.0         0.0
        1990-07-13 04:00:00        -0.0        10.0
    """
        es = self._re_indexing(optimized_es)
        _socs = dict()
        es_soc = dict()
        index_list = list()

        for mtype in es.componentModelingDict:
            if mtype == 'StorageModel':
                if hasattr(es.componentModelingDict[mtype], 'stateOfChargeOperationVariablesOptimum'):
                    if getattr(es.componentModelingDict[mtype],
                               'stateOfChargeOperationVariablesOptimum') is not None:
                        es_soc = getattr(
                            es.componentModelingDict[mtype], 'stateOfChargeOperationVariablesOptimum')

                        # Region Deleter:
                        for index_double in es_soc.index:
                            # Cut header to one level (avoid cutting to one letter with if statement)
                            if len(index_double) == 2:
                                index_list.append(str(index_double[0]))
                            else:
                                index_list.append(str(index_double))
                        es_soc.index = index_list

                        for sto_type in es_soc.index:
                            df = es_soc.loc[sto_type]

                            _socs[sto_type] = df

        for k, v in _socs.items():
            _socs[k] = round(v, 4)
        return dict(_socs)


class NodeCategorizer(FINEResultier, base.NodeCategorizer):
    """
    Categorizing the nodes of an optimized fine energy system.

    Categorization utilizes :attr:`~tessif.frused.namedtuples.Uid`.

    Nodes are categorized by:

        - Energy :paramref:`component
          <tessif.frused.namedtuples.Uid.component>`
          (One of the  'Bus', 'Sink', etc..)

        - Energy :paramref:`sector <tessif.frused.namedtuples.Uid.sector>`
          ('power', 'heat', 'mobility', 'coupled')

        - :paramref:`Region <tessif.frused.namedtuples.Uid.region>`
          ('arbitrary label')

        - :paramref:`Coordinates <tessif.frused.namedtuples.Uid.latitude>`
          (latitude, longitude in degree)

        - Energy :paramref:`carrier <tessif.frused.namedtuples.Uid.carrier>`
          ('solar', 'wind', 'electricity', 'steam' ...)

        - :paramref:`Node type <tessif.frused.namedtuples.Uid.node_type>`
          ('arbitrary label')

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.NodeCategorizer>`.

    Examples
    --------

    1. Display the energy system component's
       :paramref:`Coordinates <tessif.frused.namedtuples.Uid.latitude>`:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.create_mwe())
        >>> pprint.pprint(resultier.node_coordinates)
        {'CBET': Coordinates(latitude=53, longitude=10),
         'Demand': Coordinates(latitude=53, longitude=10),
         'Gas Station': Coordinates(latitude=53, longitude=10),
         'PowerLine': Coordinates(latitude=53, longitude=10),
         'Renewable': Coordinates(latitude=53, longitude=10),
         'Transformer': Coordinates(latitude=53, longitude=10)}

    2. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.region`:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.create_mwe())
        >>> pprint.pprint(resultier.node_region_grouped)
        {'Germany': ['PowerLine',
                     'CBET',
                     'Demand',
                     'Renewable',
                     'Gas Station',
                     'Transformer']}

    3. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.sector`

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.create_mwe())
        >>> pprint.pprint(resultier.node_sector_grouped)
        {'Power': ['PowerLine',
                   'CBET',
                   'Demand',
                   'Renewable',
                   'Gas Station',
                   'Transformer']}

    4. Group energy system components by their
       :paramref:`~tessif.frused.namedtuples.Uid.node_type`:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.create_mwe())
        >>> pprint.pprint(resultier.node_type_grouped)
        {'AC-bus': ['PowerLine'],
         'AC-source': ['Renewable'],
         'Gas import': ['Gas Station'],
         'Gas-bus': ['CBET'],
         'Gas-powerplant': ['Transformer'],
         'Sink': ['Demand']}

    5. Group energy system components by their energy
       :paramref:`~tessif.frused.namedtuples.Uid.carrier`:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.create_mwe())
        >>> pprint.pprint(resultier.node_carrier_grouped)
        {'Electricity': ['PowerLine', 'Demand', 'Renewable'],
         'Gas': ['CBET', 'Gas Station', 'Transformer']}

    6. Map the `node uid representation <Labeling_Concept>` of each component
       of the energy system to their energy
       :paramref:`~tessif.frused.namedtuples.Uid.carrier` :

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.create_mwe())
        >>> pprint.pprint(resultier.node_energy_carriers)
        {'CBET': 'gas',
         'Demand': 'Electricity',
         'Gas Station': 'gas',
         'PowerLine': 'Electricity',
         'Renewable': 'Electricity',
         'Transformer': 'gas'}

    7. Map the `node uid representation <Labeling_Concept>` of each component
       of the energy system to their
       :paramref:`~tessif.frused.namedtuples.Uid.component`:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.NodeCategorizer(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.node_components)
        {'Bus': ['Power Line', 'CBET'],
         'Sink': ['Demand'],
         'Source': ['CBE', 'Renewable'],
         'Transformer': ['Transformer']}
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)

    @log.timings
    def _map_node_components(self, optimized_es):
        es = self._re_indexing(optimized_es)
        _component_nodes = defaultdict(list)
        # Map the respective sectors:
        for node in es.uid_dict:
            if hasattr(optimized_es.uid_dict[node], 'component'):
                cmp = getattr(optimized_es.uid_dict[node], 'component')
                _component_nodes[cmp.lower().capitalize()].append(str(node))
            # Node has no component attributed in node
            else:
                _component_nodes['Unspecified'].append(str(node))

        return dict(_component_nodes)

    @log.timings
    def _map_node_sectors(self, optimized_es):
        es = self._re_indexing(optimized_es)
        _sectored_nodes = defaultdict(list)
        # Map the respective sectors:
        for node in es.uid_dict:
            if hasattr(optimized_es.uid_dict[node], 'sector'):
                sec = getattr(optimized_es.uid_dict[node], 'sector')
                _sectored_nodes[sec].append(str(node))
            # Node has no sector attributed in node
            else:
                _sectored_nodes['Unspecified'].append(str(node))

        return dict(_sectored_nodes)

    @log.timings
    def _map_node_regions(self, optimized_es):
        es = self._re_indexing(optimized_es)
        _regionalized_nodes = defaultdict(list)
        # Map the respective regions:
        for node in es.uid_dict:
            if hasattr(optimized_es.uid_dict[node], 'region'):
                cmp = getattr(optimized_es.uid_dict[node], 'region')
                _regionalized_nodes[cmp.lower().capitalize()].append(str(node))
            # Node has no region attributed in node
            else:
                _regionalized_nodes['Unspecified'].append(str(node))

        return dict(_regionalized_nodes)

    # noinspection PyTypeChecker
    @log.timings
    def _map_node_coordinates(self, optimized_es):
        es = self._re_indexing(optimized_es)
        # Use default dict as lat/lon strings container
        _coordinates = defaultdict(list)
        # Map the respective latitudes:
        for node in es.uid_dict:
            if hasattr(optimized_es.uid_dict[node], 'latitude') and hasattr(optimized_es.uid_dict[node], 'longitude'):
                lat = getattr(optimized_es.uid_dict[node], 'latitude')
                lon = getattr(optimized_es.uid_dict[node], 'longitude')
                _coordinates[str(node)] = nts.Coordinates(lat, lon)
            # Node has no lat/lon attributed in node.label
            else:
                _coordinates['Unspecified'].append(str(node))

        return dict(_coordinates)

    @log.timings
    def _map_node_energy_carriers(self, optimized_es):
        es = self._re_indexing(optimized_es)
        # Use default dict as carrier strings container
        _carrier_grouped_nodes = defaultdict(list)
        _node_energy_carriers = defaultdict(str)
        # Map the respective carriers:
        for node in es.uid_dict:
            if hasattr(optimized_es.uid_dict[node], 'carrier'):
                car = getattr(optimized_es.uid_dict[node], 'carrier')
                _carrier_grouped_nodes[car.lower(
                ).capitalize()].append(str(node))
            # Node has no carrier attributed in node
            else:
                _carrier_grouped_nodes['Unspecified'].append(str(node))
                _node_energy_carriers[str(node.label)] = 'Unspecified'

        return dict(_carrier_grouped_nodes), dict(_node_energy_carriers)

    @log.timings
    def _map_node_types(self, optimized_es):
        es = self._re_indexing(optimized_es)
        _typed_nodes = defaultdict(list)
        # Map the respective types:
        for node in es.uid_dict:
            if hasattr(optimized_es.uid_dict[node], 'node_type'):
                ntype = getattr(optimized_es.uid_dict[node], 'node_type')
                _typed_nodes[ntype].append(str(node))
            # Node has no type attributed in node
            else:
                _typed_nodes['Unspecified'].append(str(node))

        return dict(_typed_nodes)


class FlowResultier(base.FlowResultier, LoadResultier):
    """
    Flows2mapping
    Transforming flow results into dictionairies keyed by edges.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.FlowResultier>`.

    Examples
    --------

    1. Display the net energy flows of a small energy system:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.edge_net_energy_flow)
        {Edge(source='CBE', target='CBET'): 30.0,
         Edge(source='CBET', target='Transformer'): 30.0,
         Edge(source='Power Line', target='Demand'): 40.0,
         Edge(source='Renewable', target='Power Line'): 27.4,
         Edge(source='Transformer', target='Power Line'): 12.6}

    2. Display the total costs incurred sorted by edge/flow:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.edge_total_costs_incurred)
        {Edge(source='CBE', target='CBET'): 0.0,
         Edge(source='CBET', target='Transformer'): 0.0,
         Edge(source='Power Line', target='Demand'): 0.0,
         Edge(source='Renewable', target='Power Line'): 137.0,
         Edge(source='Transformer', target='Power Line'): 60.0}

    3. Display the total emissions caused sorted by edge/flow:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.edge_total_emissions_caused)
        {Edge(source='CBE', target='CBET'): 0.0,
         Edge(source='CBET', target='Transformer'): 0.0,
         Edge(source='Power Line', target='Demand'): 0.0,
         Edge(source='Renewable', target='Power Line'): 0.0,
         Edge(source='Transformer', target='Power Line'): 5.292}

    4. Display the specific flow costs of this energy system:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.edge_specific_flow_costs)
        {Edge(source='CBE', target='CBET'): 0.0,
         Edge(source='CBET', target='Transformer'): 0.0,
         Edge(source='Power Line', target='Demand'): 0.0,
         Edge(source='Renewable', target='Power Line'): 5.0,
         Edge(source='Transformer', target='Power Line'): 4.761904761904762}

    5. Display the specific emission of this energy system:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.edge_specific_emissions)
        {Edge(source='CBE', target='CBET'): 0.0,
         Edge(source='CBET', target='Transformer'): 0.0,
         Edge(source='Power Line', target='Demand'): 0.0,
         Edge(source='Renewable', target='Power Line'): 0.0,
         Edge(source='Transformer', target='Power Line'): 0.42}

    6. Show the caluclated edge weights of this energy system:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())
        >>> pprint.pprint(resultier.edge_weight)
        {Edge(source='CBE', target='CBET'): 0.1,
         Edge(source='CBET', target='Transformer'): 0.1,
         Edge(source='Power Line', target='Demand'): 0.1,
         Edge(source='Renewable', target='Power Line'): 1.0,
         Edge(source='Transformer', target='Power Line'): 0.9523809523809523}

    7. Access the reference emissions and net energy flow:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> resultier = fine.FlowResultier(fine_examples.emission_objective())

        >>> print(resultier.edge_reference_emissions)
        0.42

        >>> print(resultier.edge_reference_net_energy_flow)
        40.0
    """

    def __init__(self, optimized_es, **kwargs):

        super().__init__(optimized_es=optimized_es,
                         **kwargs)

    @log.timings
    def _map_specific_flow_costs(self, optimized_es):
        r"""Energy specific flow costs mapped to edges."""
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)
        _specific_flow_costs = defaultdict(float)

        if hasattr(es, 'flow_costs'):
            # Reshape flow costs and relate them to edges
            for flow in es.flow_costs:
                for edge in self.edges:
                    if flow == edge.source:
                        if isinstance(es.flow_costs[flow], abc.Iterable):
                            _specific_flow_costs[edge] = es.flow_costs[flow][edge.target]
                        else:
                            _specific_flow_costs[edge] = es.flow_costs[flow]
                    if flow == edge.target:
                        if edge.target in es.sinks:
                            _specific_flow_costs[edge] = es.flow_costs[flow]

        else:
            for mtype in es.componentModelingDict:
                for node in es.componentModelingDict[mtype].componentsDict:
                    if getattr(cmp_input[node], 'dimension') != '2dim':
                        if hasattr(cmp_input[node], 'opexPerOperation'):
                            factor = float(
                                getattr(cmp_input[node], 'opexPerOperation').values)
                            if hasattr(es.componentModelingDict[mtype].componentsDict[node],
                                       'commodityConversionFactors'):
                                commodity_factors = getattr(
                                    cmp_input[node], 'commodityConversionFactors')
                                conv_out = dict(
                                    (k, v) for k, v in commodity_factors.items() if v > 0 and k not in spl.emissions)
                                for grid in self.outbounds[node]:
                                    grid_com = cmp_input[grid].commodity
                                    if grid_com in conv_out:
                                        if len(conv_out) > 1:
                                            _specific_flow_costs[nts.Edge(node, grid)] = (float(factor) / (
                                                conv_out[grid_com])) / len(conv_out)
                                        else:
                                            _specific_flow_costs[nts.Edge(node, grid)] = float(factor) / conv_out[
                                                grid_com]
                            else:
                                for outflow in self.outbounds[node]:
                                    _specific_flow_costs[nts.Edge(
                                        node, outflow)] = float(factor)
                        elif hasattr(cmp_input[node], 'opexPerDischargeOperation'):
                            factor = getattr(
                                cmp_input[node], 'opexPerDischargeOperation').values
                            for outflow in self.outbounds[node]:
                                _specific_flow_costs[nts.Edge(
                                    node, outflow)] = float(factor)
                    else:
                        for edge in self.edges:
                            _specific_flow_costs[edge] = esn_defaults['flow_costs']

        return dict(_specific_flow_costs)

    @log.timings
    def _map_specific_emissions(self, optimized_es):
        r"""Energy specific emissions mapped to edges."""
        es = self._re_indexing(optimized_es)
        cmp_input = self._cmp_input(es)
        _specific_emissions = dict()
        limit_com = None

        if hasattr(es, 'flow_emissions'):
            # Reshape flow emissions and relate them to edges
            for emissions in es.flow_emissions:
                for edge in self.edges:
                    if emissions == edge.source:
                        if isinstance(es.flow_emissions[emissions], abc.Iterable):
                            _specific_emissions[edge] = es.flow_emissions[emissions][edge.target]
                        else:
                            _specific_emissions[edge] = es.flow_emissions[emissions]

        else:
            # Declare limiting commodity (string)
            if hasattr(es, 'emission_default'):
                limit_com = es.emission_default
            else:
                for limit in cmp_input:
                    if hasattr(cmp_input[limit], 'yearlyLimit'):
                        if getattr(cmp_input[limit], 'yearlyLimit') is not None:
                            limit_com = cmp_input[limit].commodity
            if limit_com:
                # Emissions are only stored in conversion components which can be an emitting source as well
                for node in self.nodes:
                    if hasattr(cmp_input[node], 'commodityConversionFactors'):
                        commodity_factors = getattr(
                            cmp_input[node], 'commodityConversionFactors')
                        for outflow in self.node_outflows[node]:
                            conv = cmp_input[outflow].commodity
                            _specific_emissions[nts.Edge(node, outflow)] = commodity_factors[limit_com] * \
                                commodity_factors[conv]

            for edge in self.edges:
                if edge not in _specific_emissions:
                    _specific_emissions[edge] = esn_defaults['emissions']

        return dict(_specific_emissions)


class AllResultier(CapacityResultier, FlowResultier, StorageResultier,
                   ScaleResultier):
    r"""
    Transform energy system results into a dictionary keyed by attribute.

    Incorporates all the functionalities from its bases.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    Note
    ----
    This class allows interfacing with **ALL** framework processing utilities.
    It extracts every bit of info the author ever needed in his postprocessing.

    It is meant to be a "one fits all" solution for small energy systems.
    Perfectly fit for showing "proof of concepts" or debugging energy system
    components.

    **Not** meant to be used with **large energy systems**.
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)


class LabelFormatier(base.LabelFormatier, FlowResultier, CapacityResultier):
    r"""
    Generate component summaries as multiline label dictionairy entries.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.LabelFormatier>`.

    Examples
    --------

    1. Compile and display a node's summary:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.LabelFormatier(fine_examples.create_mwe())
        >>> pprint.pprint(formatier.node_summaries['Demand'])
        {'Demand': 'Demand\n10 MW\ncf: 1.0'}

    2. Compile and display an edge's summary:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.LabelFormatier(fine_examples.create_mwe())
        >>> pprint.pprint(formatier.edge_summaries[
        ...     ('Renewable', 'PowerLine')])
        {('Renewable', 'PowerLine'): '30 MWh\n1.0 €/MWh\n0.0 t/MWh'}
    """

    def __init__(self, optimized_es, **kwargs):
        super().__init__(optimized_es=optimized_es, **kwargs)


class NodeFormatier(base.NodeFormatier, CapacityResultier):
    r"""Transforming energy system results into node visuals.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results.`

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrer', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionairy.

    drawutil: str, default='nx'
        Which drawuing utility backend to format node size, fil_size and
        shape to. ``'dc'`` for :mod:`plotly-dash-cytoscape
        <tessif.visualize.dcgrph>` or ``'nx'`` for
        :mod:`networkx-matplotlib <tessif.visualize.nxgrph>`.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.NodeFormatier>`.

    Examples
    --------

    1. Generate and display a small energy system's node shape mapping:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.NodeFormatier(fine_examples.create_mwe())
        >>> pprint.pprint(formatier.node_shape)
        {'CBET': 'o',
         'Demand': '8',
         'Gas Station': 'o',
         'PowerLine': 'o',
         'Renewable': 'o',
         'Transformer': '8'}

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready shapes:

        >>> formatier = fine.NodeFormatier(
        ...     fine_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(formatier.node_shape)
        {'CBET': 'ellipse',
         'Demand': 'ellipse',
         'Gas Station': 'round-rectangle',
         'PowerLine': 'ellipse',
         'Renewable': 'round-rectangle',
         'Transformer': 'round-octagon'}

    2. Generate and display a small energy system's node size mapping:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.NodeFormatier(fine_examples.create_mwe())
        >>> pprint.pprint(formatier.node_size)
        {'CBET': 'variable',
         'Demand': 1260,
         'Gas Station': 3000,
         'PowerLine': 'variable',
         'Renewable': 1260,
         'Transformer': 1260}

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready sizes scaled
        to a different default node size:

        >>> formatier = fine.NodeFormatier(
        ...     fine_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(formatier.node_size)
        {'CBET': 'variable',
         'Demand': 38,
         'Gas Station': 90,
         'PowerLine': 'variable',
         'Renewable': 38,
         'Transformer': 38}


    3. Generate and display a small energy system's node fill size mapping:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.NodeFormatier(fine_examples.create_mwe())
        >>> pprint.pprint(formatier.node_fill_size)
        {'CBET': None,
         'Demand': 1260.0,
         'Gas Station': 750.0,
         'PowerLine': None,
         'Renewable': 945.0,
         'Transformer': 315.0}

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready sizes scaled
        to a different default node size:

        >>> formatier = fine.NodeFormatier(
        ...     fine_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(formatier.node_fill_size)
        {'CBET': None,
         'Demand': 38.0,
         'Gas Station': 22.0,
         'PowerLine': None,
         'Renewable': 28.0,
         'Transformer': 10.0}


    4. Generate and display a small energy system's node color mapping basd on
       the grouping:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.NodeFormatier(
        ...     fine_examples.create_mwe(), cgrp='all')
        >>> pprint.pprint(formatier.node_color.name)
        {'CBET': '#AFAFAF',
         'Demand': '#330099',
         'Gas Station': '#336666',
         'PowerLine': '#ffff33',
         'Renewable': '#AFAFAF',
         'Transformer': '#9999ff'}

        >>> pprint.pprint(formatier.node_color.carrier)
        {'CBET': '#336666',
         'Demand': '#FFD700',
         'Gas Station': '#336666',
         'PowerLine': '#FFD700',
         'Renewable': '#FFD700',
         'Transformer': '#336666'}

         >>> pprint.pprint(formatier.node_color.sector)
         {'CBET': '#ffff33',
          'Demand': '#ffff33',
          'Gas Station': '#ffff33',
          'PowerLine': '#ffff33',
          'Renewable': '#ffff33',
          'Transformer': '#ffff33'}

    5. Generate and display a small energy system's node color map (colors
       that are cycled through for each component type) mapping basd on the
       grouping:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> from tessif.transform.es2mapping import fine
        >>> import pprint
        >>> formatier = fine.NodeFormatier(
        ...     fine_examples.create_mwe(), cgrp='all')
        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.name.items()})
        {'CBET': <class 'str'>,
         'Demand': <class 'str'>,
         'Gas Station': <class 'str'>,
         'PowerLine': <class 'str'>,
         'Renewable': <class 'str'>,
         'Transformer': <class 'str'>}
        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.carrier.items()})
        {'CBET': <class 'str'>,
         'Demand': <class 'str'>,
         'Gas Station': <class 'str'>,
         'PowerLine': <class 'str'>,
         'Renewable': <class 'str'>,
         'Transformer': <class 'str'>}
        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_color_maps.sector.items()})
        {'CBET': <class 'str'>,
         'Demand': <class 'str'>,
         'Gas Station': <class 'str'>,
         'PowerLine': <class 'str'>,
         'Renewable': <class 'str'>,
         'Transformer': <class 'str'>}

        (Hint for devs: Which color string is mapped depends on order of
        mapping. Therefore only the type is printed and not its string value
        since it may differ from doctest to doctest.)
    """

    def __init__(self, optimized_es, cgrp='name', drawutil='nx', **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            cgrp=cgrp,
            drawutil=drawutil,
            **kwargs)


class MplLegendFormatier(base.MplLegendFormatier, CapacityResultier):
    r"""
    Generating visually enhanced matplotlib legends for nodes and edges.

    Parameters
    ----------
    optimized_es: fine energy system
        An optimized fine energy system containing its results.`

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrier', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionairy.

    markers: str, default='formatier'
        What marker to use for legend entries. Either ``'formatier'`` or
        one of the :any:`matplotlib.markers`.

        If ``'formatier'`` is used, markers will be inferred from
        :attr:`NodeFormatier.node_shape`.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.MplLegendFormatier>`.

    Examples
    --------

    0. Handle the imports of the following examples and simulate the
       energy system:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> import pprint

    1. Generate and display name grouped legend labels of a small energy
       system:

        >>> formatier = post_process_fine.MplLegendFormatier(
        ...     fine_examples.create_mwe(), cgrp='all')
        >>> pprint.pprint(formatier.node_legend.name['legend_labels'])
        ['CBET', 'Demand', 'Gas Station', 'PowerLine', 'Renewable', 'Transformer']


    2. Generate and display matplotlib legend attributes to describe
       :paramref:`fency node styles
       <tessif.visualize.nxgrph.draw_nodes.draw_fency_nodes>`. Fency as in:

            - variable node size being outer fading circles
            - cycle filling being proportional capacity factors
            - outer diameter being proportional installed capacities

        >>> formatier = post_process_fine.MplLegendFormatier(
        ...     fine_examples.create_mwe(), cgrp='all')
        >>> pprint.pprint({k: type(v)
        ...     for k,v in formatier.node_style_legend.items()})
        {'legend_bbox_to_anchor': <class 'tuple'>,
         'legend_borderaxespad': <class 'int'>,
         'legend_handles': <class 'list'>,
         'legend_labels': <class 'list'>,
         'legend_labelspacing': <class 'int'>,
         'legend_loc': <class 'str'>,
         'legend_title': <class 'str'>}

        """

    def __init__(self, optimized_es, cgrp='all',
                 markers='formatier', **kwargs):
        # needed transformers

        # mpl legend formatier is the only class needing an extra formatier
        # instead of just inheriting it. This allows bundeling as done in the
        # AllFormatier with its specific color group (cgrp) and still be able
        # to map the legends for all colors

        # a different plausible approach would be to only map the bundled
        # color, and implement some if clauses to only map the legend
        # requested. This also implies chaning the bahaviour of
        # MplLegendFormatier.node_legend
        self._nformats = NodeFormatier(
            optimized_es, drawutil='nx', cgrp='all')

        super().__init__(optimized_es=optimized_es, cgrp='all',
                         markers=markers, **kwargs)


class EdgeFormatier(base.EdgeFormatier, FlowResultier):
    r"""Transforming energy system results into edge visuals.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    drawutil: str, default='nx'
        Which drawuing utility backend to format node size, fil_size and
        shape to. ``'dc'`` for :mod:`plotly-dash-cytoscape
        <tessif.visualize.dcgrph>` or ``'nx'`` for
        :mod:`networkx-matplotlib <tessif.visualize.nxgrph>`.

    cls: tuple, default=None
        2-Tuple / :attr:`CLS namedtuple <tessif.frused.namedtuples.CLS>`
        defining the relative flow cost thresholds and the respective style
        specifications. Used to map specific flow costs to edge line style
        representations.

        If  ``None``, default implementation is used based on
        :paramref:`~EdgeFormatier.drawutil`.

        For ``drawutil='nx'``
        `Networkx-Matplotlib
        <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_linestyle>`_::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        For ``drawutil='dc'``
        `Dash-Cytoscape <https://js.cytoscape.org/#style/edge-line>`_ styles
        are used::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        Translating to all edges of relative specific flows costs, between
        ``0`` and ``.33`` are correlated to have a ``':'``/``'dotted'``
        linestyle.

    See also
    --------
    For functionality documentation see the respective :class:`base class
    <tessif.transform.es2mapping.base.EdgeFormatier>`.

    Examples
    --------

    0. Handle the imports:

        >>> import tessif.examples.data.fine.py_hard as fine_examples
        >>> import tessif.transform.es2mapping.fine as post_process_fine
        >>> import pprint

    1. Generate and display a small energy system's edge withs:

        >>> formatier = post_process_fine.EdgeFormatier(
        ...     fine_examples.create_mwe())
        >>> pprint.pprint(list(sorted(formatier.edge_width.items())))
        [(Edge(source='CBET', target='Transformer'), 0.6),
         (Edge(source='Gas Station', target='CBET'), 0.6),
         (Edge(source='PowerLine', target='Demand'), 1.0),
         (Edge(source='Renewable', target='PowerLine'), 0.75),
         (Edge(source='Transformer', target='PowerLine'), 0.25)]

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready widths,
        scaled to a different default edge width:

        >>> formatier = post_process_fine.EdgeFormatier(
        ...     fine_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(list(sorted(formatier.edge_width.items())))
        [(Edge(source='CBET', target='Transformer'), 4.17),
         (Edge(source='Gas Station', target='CBET'), 4.17),
         (Edge(source='PowerLine', target='Demand'), 7.0),
         (Edge(source='Renewable', target='PowerLine'), 5.25),
         (Edge(source='Transformer', target='PowerLine'), 1.75)]

    2. Generate and display a small energy system's edge colors:

        >>> formatier = post_process_fine.EdgeFormatier(
        ...     fine_examples.create_mwe())
        >>> pprint.pprint(list(sorted(formatier.edge_color.items())))
        [(Edge(source='CBET', target='Transformer'), [0.15]),
         (Edge(source='Gas Station', target='CBET'), [0.15]),
         (Edge(source='PowerLine', target='Demand'), [0.15]),
         (Edge(source='Renewable', target='PowerLine'), [0.15]),
         (Edge(source='Transformer', target='PowerLine'), [0.15])]

        (:func:`~networkx.drawing.nx_pylab.draw_networkx_edges` expects
        iterable of floats when using a colormap)

        Compare these to the :mod:`~tessif.visualize.dcgrph` ready colors,
        directly scaling the relativ specific emissions to a hex-color value.

        >>> formatier = post_process_fine.EdgeFormatier(
        ...     fine_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(list(sorted(formatier.edge_color.items())))
        [(Edge(source='CBET', target='Transformer'), '#d8d8d8'),
         (Edge(source='Gas Station', target='CBET'), '#d8d8d8'),
         (Edge(source='PowerLine', target='Demand'), '#d8d8d8'),
         (Edge(source='Renewable', target='PowerLine'), '#d8d8d8'),
         (Edge(source='Transformer', target='PowerLine'), '#d8d8d8')]


    3. Generate and display a small energy system's edge line styles:

        >>> formatier = post_process_fine.EdgeFormatier(
        ...     fine_examples.create_mwe())
        >>> pprint.pprint(list(sorted(formatier.edge_linestyle.items())))
        [(Edge(source='CBET', target='Transformer'), ':'),
         (Edge(source='Gas Station', target='CBET'), ':'),
         (Edge(source='PowerLine', target='Demand'), ':'),
         (Edge(source='Renewable', target='PowerLine'), ':'),
         (Edge(source='Transformer', target='PowerLine'), '-')]


        Compare these to the :mod:`~tessif.visualize.dcgrph` ready styles,
        using different specifiers:

        >>> formatier = post_process_fine.EdgeFormatier(
        ...     fine_examples.create_mwe(),
        ...     drawutil='dc')
        >>> pprint.pprint(list(sorted(formatier.edge_linestyle.items())))
        [(Edge(source='CBET', target='Transformer'), 'dotted'),
         (Edge(source='Gas Station', target='CBET'), 'dotted'),
         (Edge(source='PowerLine', target='Demand'), 'dotted'),
         (Edge(source='Renewable', target='PowerLine'), 'dotted'),
         (Edge(source='Transformer', target='PowerLine'), 'solid')]

    """

    def __init__(self, optimized_es, drawutil='nx', cls=None, **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            drawutil=drawutil,
            cls=cls,
            **kwargs)


class AllFormatier(
        LabelFormatier, MplLegendFormatier, NodeFormatier, EdgeFormatier):
    r"""
    Transforming ES results into visual expression dicts keyed by attribute.
    Incorperates all the functionalities from its
    parents.

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    cgrp: str, default='name'
        Which group of color attribute(s) to return. One of::

            {'name', 'carrer', 'sector'}

        Color related attributes are grouped by
        :class:`tessif.frused.namedtuples.NodeColorGroupings` and are thus
        returned as a :class:`typing.NamedTuple`. Certain api functionalities
        expect those attributes to be dicts. (Usually those working only
        on :class:`~tessif.transform.es2mapping.base.ESTransformer` input).
        Use this parameter on Formatier creation to provide the expected
        dictionairy.

        Used by :class:`NodeFormatier` and :class:`MplLegendFormatier`

    markers: str, default='formatier'
        What marker to use for legend entries. Either ``'formatier'`` or
        one of the :any:`matplotlib.markers`.

        If ``'formatier'`` is used, markers will be inferred from
        :attr:`NodeFormatier.node_shape`.

        Used by :class:`MplLegendFormatier`

    drawutil: str, default='nx'
        Which drawuing utility backend to format node size, fil_size and
        shape to. ``'dc'`` for :mod:`plotly-dash-cytoscape
        <tessif.visualize.dcgrph>` or ``'nx'`` for
        :mod:`networkx-matplotlib <tessif.visualize.nxgrph>`.

    cls: tuple, default=None
        2-Tuple / :attr:`CLS namedtuple <tessif.frused.namedtuples.CLS>`
        defining the relative flow cost thresholds and the respective style
        specifications. Used to map specific flow costs to edge line style
        representations.

        If  ``None``, default implementation is used based on
        :paramref:`~EdgeFormatier.drawutil`.

        For ``drawutil='nx'``
        `Networkx-Matplotlib
        <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_linestyle>`_::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        For ``drawutil='dc'``
        `Dash-Cytoscape <https://js.cytoscape.org/#style/edge-line>`_ styles
        are used::

            cls = ([0, .33, .66], ['dotted', 'dashed', 'solid'])

        Translating to all edges of relative specific flows costs, between
        ``0`` and ``.33`` are correlated to have a ``':'``/``'dotted'``
        linestyle.

    Note
    ----
    This class allows interfacing with **ALL** framework processing utilities.
    It extracts every bit of info the author ever needed in his postprocessing.

    It is meant to be a "one fits all" solution for small energy systems.
    Perfectly fit for showing "proof of concepts" or debugging energy system
    components.

    **Not** meant to be used with **large energy systems**.
    """

    def __init__(self, optimized_es, cgrp='all',
                 markers='formatier',
                 drawutil='nx',
                 cls=None,
                 **kwargs):

        super().__init__(
            optimized_es=optimized_es,
            cgrp=cgrp, markers=markers, drawutil=drawutil, **kwargs)

        # initializing edge formatier seperately, because of differing
        # init signature causing a wierd unrespecting of drawutl
        super(EdgeFormatier, self).__init__(
            optimized_es=optimized_es,
            drawutil=drawutil,
            cls=cls,
            **kwargs)


class ICRHybridier(FINEResultier, base.ICRHybridier):
    """
    Aggregate numerical and visual information for visualizing
    the :ref:`Integrated_Component_Results` (ICR).

    Parameters
    ----------
    optimized_es: fine energy system model
        An optimized fine energy system containing its results

    See also
    --------
    For non :ref:`model <SupportedModels>` specific attributes see
    the respective :class:`base class
    <tessif.transform.es2mapping.base.ICRHybridier>`.
    """

    def __init__(self, optimized_es, colored_by='name', **kwargs):
        base.ICRHybridier.__init__(
            self,
            optimized_es=optimized_es,
            node_formatier=NodeFormatier(optimized_es, cgrp=colored_by),
            edge_formatier=EdgeFormatier(optimized_es),
            mpl_legend_formatier=MplLegendFormatier(optimized_es),
            **kwargs)

    @property
    def node_characteristic_value(self):
        r"""Map node label to characteristic value.

        Components of variable size have a characteristic value of ``None``.

        The **node fillsize** of :ref:`integrated compnent results graphs
        <Integrated_Component_Results>` scales with the
        **characteristic value**.
        If no capacity is defined (i.e for nodes of variable size, like busses
        or excess sources and sinks, node size is set to it's default (
        :attr:`nxgrph_visualize_defaults[node_fill_size]
        <tessif.frused.defaults.nxgrph_visualize_defaults>`).
        """
        return self._caps.node_characteristic_value


def _parse_commodity_factors(commodity_factors):
    inflows, outflows = {}, {}
    for key, value in commodity_factors.items():
        if isinstance(value, abc.Iterable):
            if any(entry < 0 for entry in value):
                inflows[key] = value
            else:
                outflows[key] = value
        else:
            if value < 0:
                inflows[key] = value
            else:
                outflows[key] = value

    return inflows, outflows
