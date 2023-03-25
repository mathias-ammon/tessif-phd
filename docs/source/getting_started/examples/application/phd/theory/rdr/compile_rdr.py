import pandas as pd

import importlib


def compile_result_data_representation(optimized_es, software, node):
    """
    Convenience wrapper to compile result data representation.

    Explicitly reproduces the result data representation table as stated in the
    lead author's phd thesis in
    'Theory' -> 'Graph Theory Tools' -> 'Result Data Representation'

    Parameters
    ----------
    optimized_es: software_specific_optimized_energy_system
        An optimized energy system containing its results as in tessif.simulate
    software: str
       String naming the
       :attr:`~tessif.frused.defaults.registered_models` representing tessif's
       :ref:`supported energy supply system simulation models<SupportedModels>`
    node: str
       String representing the node's
       :class:`uids <tessif.frused.namedtuples.Uid>` of which the result data
       representation is to be compiled.
    """
    requested_model_result_parsing_module = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))

    resultier = requested_model_result_parsing_module.AllResultier(
        optimized_es)

    # compile first three straight forward result datas:
    result_data = [
        ('installed capacity', '$P_{cap}$',
         _compile_node_from_res(resultier, 'node_installed_capacity', node)),
        ('original capacity', '$P_{origcap}$',
         _compile_node_from_res(resultier, 'node_original_capacity', node)),
        ('characteristic value', '$cv$',
         _compile_node_from_res(resultier, 'node_characteristic_value', node)),
    ]

    # check if SOC(t) is applicable:
    if node in resultier.node_soc:
        result_data.append(
            ('current SOC', '$SOC(t)$', resultier.node_soc[node])
        )

    # continue compiling the rest of the node data:
    result_data.extend(
        [
            ('energy carrier', '-', resultier.uid_nodes[node].carrier),
            ('energy sector', '-', resultier.uid_nodes[node].sector),
            ('region', '-', resultier.uid_nodes[node].region),
            ('component', '-', resultier.uid_nodes[node].component),
            ('node_type', '-', resultier.uid_nodes[node].node_type),
            ('latitude', '-', resultier.uid_nodes[node].latitude),
            ('longitude', '-', resultier.uid_nodes[node].longitude),
        ],
    )

    # compile edge data
    node_outflows = resultier.outbounds[node]

    net_energy_flows = dict()
    specific_costs = dict()
    specific_emissions = dict()

    for outflow in node_outflows:
        net_energy_flows[outflow] = resultier.edge_net_energy_flow[(
            node, outflow)]
        specific_costs[outflow] = resultier.edge_specific_flow_costs[(
            node, outflow)]
        specific_emissions[outflow] = resultier.edge_specific_emissions[(
            node, outflow)]

    result_data.extend(
        [
            ('load', '$P(t)$', _compile_node_from_res(
                resultier, 'node_load', node)),
            ('net energy flow', '$\\sum_t P(t)$', net_energy_flows),
            ('specific costs', '$c_{flow}$', specific_costs),
            ('specific emissions', '$e_{flow}$', specific_emissions),
        ],
    )

    # print(result_data)

    # create a Pandas DataFrame to increase readability and math thesis layout:

    result_df = pd.DataFrame(result_data, columns=['Label', 'Symbol', 'Value'])
    result_df = result_df.set_index('Label')

    return result_df


def _compile_node_from_res(resultier, attribute, node):
    result = getattr(resultier, attribute)[node]

    if attribute == "node_load":
        new_result = dict()
        for col in result.columns:
            new_result[col] = result[col].values.tolist()
        return new_result

    if isinstance(result, pd.DataFrame):
        return dict(result)
    else:
        return result
