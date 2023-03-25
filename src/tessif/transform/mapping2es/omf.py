# tessif/transform/mapping2es/omf.py
"""
:mod:`~tessif.transform.mapping2es.omf` is a :mod:`tessif` module to transform
energy system data represented as `mapping
<https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_ like it
is returned by ie: :mod:`~tessif.parse`.

"""
import pandas as pd
import numpy as np
from oemof import solph
from tessif.frused import namedtuples as nt
from tessif.frused import resolutions, spellings, configurations
from tessif.frused.defaults import energy_system_nodes as esn
from tessif.write import log
import logging
import dutils

logger = logging.getLogger(__name__)


def parse_ideal_flow_params(es_object):
    """ Transform an energy system object dict into a ready to pass ideal flow
    parameter dict.

    Read-in the dictionary representation of an energy system object to
    extract ideal optimization flow parameters and transform them into a
    keyword argument dictionary ready to provide to
    :class:`oemof.solph.network.Flow`.

    A flow is regarded as 'ideal' in this context as a flow that has no
    'physical' restriction, i.e. no gradient, no maximum, no minimum, etc.
    Available ideal flow parameters are the following:
    (see also :class:`oemof.solph.network.Flow`)

        - :paramref:`oemof.solph.network.Flow.variable_costs`
        - emissions

    Note
    ----
    An ideal flow can still be subject to an 'expansion_plan' problem.
    The respective parsing however is handled in
    :func:`parse_invest_flow_params`.

    Parameters
    ----------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside an energy system dictionary which is usually returned by
        one of the :mod:`tessif.parse` functionalities)

    Return
    ------
    ideal_flow_parameters: dict
        Dictionary having keyword-value pairings ready to pass to
        :class:`oemof.solph.network.Flow`.
    """
    return {
        'variable_costs': spellings.get_from(
            es_object, smth_like='flow_costs', dflt=esn['flow_costs']),
        'emissions': spellings.get_from(
            es_object, smth_like='emissions', dflt=esn['emissions'])}


def parse_linear_flow_params(es_object):
    """ Transform an energy system object dict into a ready to pass linear flow
    parameter dict.

    Read-in the dictionary representation of an energy system object to
    extract linear optimization flow parameters and transform them into a
    keyword argument dictionary ready to provide to
    :class:`oemof.solph.network.Flow`.

    A flow is regarded as 'linear' in this context as a flow that only has
    linear 'physical' restriction, ie. gradient, maximum, minimum, and is
    otherwise characterized by b actual or nominal values. Available
    linear flow parameters are the following:
    (see also :class:`oemof.solph.network.Flow`)

        - :paramref:`oemof.solph.network.Flow.nominal_value`
        - :paramref:`oemof.solph.network.Flow.summed_min`
        - :paramref:`oemof.solph.network.Flow.summed_max`
        - :paramref:`oemof.solph.network.Flow.min`
        - :paramref:`oemof.solph.network.Flow.max`
        - :paramref:`oemof.solph.network.Flow.positive_gradient`
        - :paramref:`oemof.solph.network.Flow.negative_gradient`
        - :paramref:`oemof.solph.network.Flow.nominal_value`

    Note
    ----
    A linear flow can still be subject to an 'expansion_plan' problem.
    The respective parsing however is handled in
    :func:`parse_invest_flow_params`.

    Parameters
    ----------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside an energy system dictionary which is usually returned by
        one of the :mod:`tessif.parse` functionalities)

    Return
    ------
    linear_flow_parameters: dict
        Dictionary having keyword-value pairings ready to pass to
        :class:`oemof.solph.network.Flow`.
    """

    parsed_linear_flow_params = {

        'nominal_value': spellings.get_from(
            es_object, smth_like='nominal_value',
            dflt=esn['installed_capacity']),

        # nominal_value * summed_min >= sum(resulting_flow, t)
        'summed_min': spellings.get_from(
            es_object, smth_like='accumulated_minimum',
            dflt=esn['accumulated_minimum']),
        # nominal_value * summed_min <= sum(resulting_flow, t)
        'summed_max': spellings.get_from(
            es_object, smth_like='accumulated_maximum',
            dflt=esn['accumulated_maximum']),

        # exogenously set lower bound for each timestep
        # if fixed: min <= actual_value <= max
        'min': solph.sequence(spellings.get_from(
            es_object, smth_like='minimum', dflt=esn['minimum'])),
        # exogenously set upper bound for each timestep
        # if fixed: min <= actual_value <= max
        'max': solph.sequence(spellings.get_from(
            es_object, smth_like='maximum', dflt=esn['maximum'])),

        # positive_gradient*nominal_value<=flow(t)-flow(t-1)
        'positive_gradient':
        {'ub': spellings.get_from(
            es_object, smth_like='positive_gradient',
            dflt=esn['positive_gradient']),
         'costs': spellings.get_from(
             es_object, smth_like='positive_gradient_costs',
             dflt=esn['positive_gradient_costs'])},
        # negative_gradient*nominal_value<=flow(t)-flow(t-1)
        'negative_gradient':
        {'ub': spellings.get_from(
            es_object, smth_like='negative_gradient',
            dflt=esn['negative_gradient']),
         'costs': spellings.get_from(
             es_object, smth_like='negative_gradient_costs',
             dflt=esn['negative_gradient_costs'])}
    }

    # Oemof can't handle infinity max, so translate it to None
    if parsed_linear_flow_params['summed_max'] == float('+inf'):
        parsed_linear_flow_params['summed_max'] = None

    return parsed_linear_flow_params


def parse_invest_flow_params(es_object):
    """ Transform an energy system object dict into a ready to pass invest flow
    parameter dict.

    Read-in the dictionary representation of an energy system object to
    extract investment optimization flow parameters and transform them into a
    keyword argument dictionary ready to provide to
    :class:`oemof.solph.network.Flow`.

    A flow is regarded as 'investment' in this context as a flow that has no
    nominal value (aka installed capacity) given as input. But rather one of
    which the installed capacity is subject to the optimization problem.
    Available investment flow parameters are the following:
    (see also :class:`oemof.solph.options.Investment`)

        - :paramref:`oemof.solph.options.Investment.maximum`
        - :paramref:`oemof.solph.options.Investment.minimum`
        - :paramref:`oemof.solph.options.Investment.ep_costs`
        - :paramref:`oemof.solph.options.Investment.existing`

    Note
    ----
    Any non-convex flow can be subject to an investment flow.

    Parameters
    ----------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside an energy system dictionary which is usually returned by
        one of the :mod:`tessif.parse` functionalities)

    Return
    ------
    investment_flow_parameters: dict
        Dictionary having keyword-value pairings ready to pass to
        :class:`oemof.solph.network.Flow`.
    """
    return {
        'nominal_value': None,
        'investment': solph.Investment(
            maximum=spellings.get_from(
                es_object, smth_like='maximum_expansion',
                dflt=esn['maximum_expansion']),
            minimum=spellings.get_from(
                es_object, smth_like='minimum_expansion',
                dflt=esn['minimum_expansion']),
            ep_costs=spellings.get_from(
                es_object, smth_like='expansion_costs',
                dflt=esn['expansion_costs']),
            existing=spellings.get_from(
                es_object, smth_like='already_installed',
                dflt=esn['already_installed']))}


def parse_nonconvex_flow_params(es_object):
    """Transform an energy system object dict into a ready to pass NonConvex
     flow parameter dict.

    Read-in the dictionary representation of an energy system object to
    extract NonConvex optimization flow parameters and transform them into a
    keyword argument dictionary ready to provide to
    :class:`oemof.solph.network.Flow`.

    A flow is regarded as 'NonConvex' in this context as a flow that has
    mixed integer linear 'physical' restrictions i.e, able to turn 'off',
    but having a minimum greater than 0.
    Available nonconvex flow parameters are the following:
    (see also :class:`oemof.solph.options.NonConvex`)

        - :paramref:`oemof.solph.options.NonConvex.startup_costs`
        - :paramref:`oemof.solph.options.NonConvex.shutdown_costs`
        - :paramref:`oemof.solph.options.NonConvex.activity_costs`
        - :paramref:`oemof.solph.options.NonConvex.minimum_uptime`
        - :paramref:`oemof.solph.options.NonConvex.minimum_downtime`
        - :paramref:`oemof.solph.options.NonConvex.maximum_startups`
        - :paramref:`oemof.solph.options.NonConvex.maximum_shutdowns'`
        - :paramref:`oemof.solph.options.NonConvex.initial_status`

    Note
    ----
    Any non investment flow can be subject to a nonconvex flow.

    Parameters
    ----------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside an energy system dictionary which is usually returned by
        one of the :mod:`tessif.parse` functionalities)

    Return
    ------
    nonconvex_flow_parameters: dict
        Dictionary having keyword-value pairings ready to pass to
        :class:`oemof.solph.network.Flow`.
    """
    return {
        'nonconvex': solph.NonConvex(
            startup_costs=spellings.get_from(
                es_object, smth_like='startup_costs',
                dflt=esn['startup_costs']),
            shutdown_costs=spellings.get_from(
                es_object, smth_like='shutdown_costs',
                dflt=esn['shutdown_costs']),
            activity_costs=spellings.get_from(
                es_object, smth_like='costs_for_being_active',
                dflt=esn['costs_for_being_active']),
            minimum_uptime=spellings.get_from(
                es_object, smth_like='minimum_uptime',
                dflt=esn['minimum_uptime']),
            minimum_downtime=spellings.get_from(
                es_object, smth_like='minimum_downtime',
                dflt=esn['minimum_downtime']),
            maximum_startups=spellings.get_from(
                es_object, smth_like='maximum_startups',
                dflt=esn['maximum_startups']),
            maximum_shutdowns=spellings.get_from(
                es_object, smth_like='maximum_shutdowns',
                dflt=esn['maximum_shutdowns']),
            initial_status=spellings.get_from(
                es_object, smth_like='initial_status',
                dflt=esn['initial_status'])
        )}


def parse_fixed_flow_params(es_object):
    r""" Transform an energy system object dict into a ready to pass fixed flow
    parameter dict.

    Read-in the dictionary representation of an energy system object to
    extract fixed flow parameters and transform them into a keyword argument
    dictionary ready to provide to :class:`oemof.solph.network.Flow`.

    A flow is regarded as 'fixed' in this context as a flow that is set
    outside of the optimization flow problem, i.e the value(s) for
    :paramref:`oemof.solph.network.Flow.fix` are read-in/hardcoded
    before the actual Flow object initialization takes place. During the
    optimization the flow is then fixed to ``fix`` :math:`\cdot`
    ``nominal_value``.

    Available ideal flow parameters are the following:
    (see also :class:`oemof.solph.network.Flow`)

        - :paramref:`oemof.solph.network.Flow.fix`
        - emissions

    Note
    ----
    A fixed flow can still be subject to an 'expansion_plan' problem.
    The respective parsing however is handled in
    :func:`parse_invest_flow_params`.

    Parameters
    ----------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside an energy system dictionary which is usually returned by
        one of the :mod:`tessif.parse` functionalities.

    Return
    ------
    fixed_flow_parameters: dict
        Dictionary having keyword-value pairings ready to pass to
        :class:`oemof.solph.network.Flow`.
    """
    return {
        'fix': spellings.get_from(
            es_object, smth_like='exogenously_set_value',
            dflt=esn['exogenously_set_value'])}


def parse_flow_parameters(es_object=dict(), timeseries={}):
    """Transform an energy system object dict into a ready to pass flow
    parameter dict.

    Read-in the dictionary representation of an energy system object to
    extract fixed flow parameters and transform them into a keyword argument
    dictionary ready to provide to :class:`oemof.solph.network.Flow`.

    Parameters
    ---------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside an energy system dictionary which is usually returned by
        one of the :mod:`tessif.parse` functionalities)

    timeseries: dict
        Dictionary containing a string of the represented kind of timeseries
        (i.e. ``min``, ``max``, ``fix``, ``variable_cost`` see
        :class:`oemof.solph.network.Flow`) as key and the corresponding
        timeseries as sequence as value.

    Return
    ------
    parsed_flow_parameters: dict
        Dictionary having keyword-value pairings ready to pass to
        :class:`oemof.solph.network.Flow`.
    """

    # parsed flow parameter dictionary
    parsed_flow_params = dict()

    # parse 'ideal' part of the flow parameters
    parsed_flow_params.update(parse_ideal_flow_params(es_object))

    # if flow is requested to be 'ideal', parsing ends here:
    if spellings.get_from(es_object, smth_like='ideal',
                          dflt=esn['ideal']):

        return parsed_flow_params

    # add linear flow parameters if flow is not requested to be ideal:
    parsed_flow_params.update(parse_linear_flow_params(es_object))

    # Remove 'min' and 'max' parameters if the 'fix' parameter is given:
    if spellings.get_from(es_object, smth_like='exogenously_set_value',
                          dflt=esn['exogenously_set_value']):
        parsed_flow_params.pop('min')
        parsed_flow_params.pop('max')

    # Add expansion_problem flow parameters if requested:
    if spellings.get_from(es_object, smth_like='expansion_problem',
                          dflt=esn['expandable']) == 1:

        parsed_flow_params.pop('positive_gradient')
        parsed_flow_params.pop('negative_gradient')

        parsed_flow_params.update(parse_invest_flow_params(es_object))

    # Add nonconvex (milp) flow parameters:
    if spellings.get_from(es_object, smth_like='milp',
                          dflt=esn['milp']) == 1:

        parsed_flow_params.update(parse_nonconvex_flow_params(es_object))

    # Add fixed flow parameters if requested:
    if spellings.get_from(es_object, smth_like='exogenously_set',
                          dflt=['exogenously_set']) == 1:

        parsed_flow_params.update(parse_fixed_flow_params(es_object))

    # Add timeseries values if object requests to have one:
    if timeseries:
        # note: the error 'numpy.float' object is not iterable, means,
        # that the timeseries parsing inside tessif.parse was not succesfull
        parsed_flow_params.update(timeseries)

    return parsed_flow_params


def parse_timeseries(es_object, energy_system_dict):
    """
    Create a timeseries mapping for the
    :paramref:`~parse_timeseries.es_object` by looking up
    its data inside the :paramref:`~parse_timeseries.energy_system_dict`.

    Note
    ----
    Timeseries data is expected to be string keyed like::

        {ES_OBJECT}{SEPERATOR}{TIMESERIES_PARAMETER}.

    So for example::

        PV.max
        Onshore.fix

    Where SEPERATOR is the
    :attr:`~tessif.frused.configurations.timeseries_seperator`.

    Parameters
    ----------
    es_object: :class:`pandas.Series`
        Series representation of the energy system node
        of which the timeseries is to be parsed.

        (Usually accessed by string keying the columns of
        a :class:`pandas.DataFrame` which in themselves are keyed by a
        :attr:`timeseries-like <tessif.frused.spellings.timeseries>` key
        inside the :paramref:`~parse_timeseries.energy_system_dict`.

    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    Return
    ------
    timeseries: dict
        Dictionary containing a string of the represented kind of timeseries
        (i.e. ``min``, ``max``, ``fix``, ``variable_cost`` see
        :class:`oemof.solph.network.Flow`) as key and the corresponding
        timeseries as sequence as value.
    """

    return es_object['timeseries']
    # timeseries = {}
    # # check if es object requests to be linked to a timeseries:
    # if spellings.get_from(es_object, smth_like='timeframe',
    #                       dflt=esn['timeseries']):

    #     print('hi')
    #     # ... yes, so extract respective timeseries
    #     # check if the provided energy system dict has an entry for timeindex:
    #     if spellings.get_from(energy_system_dict, smth_like='timeframe',
    #                           dflt=esn['timeseries']) is not None:

    #         print('there')
    #         # iterate through DataFrame columns to ...
    #         for col in spellings.get_from(
    #                 energy_system_dict, smth_like='timeindex').columns.values:

    #             print('whats')
    #             print(col)
    #             # see if there is an entry for the es object
    #             if col.split(configurations.timeseries_seperator)[
    #                     0] == spellings.get_from(
    #                         es_object, smth_like='name',
    #                         dflt=esn['name']):

    #                 # yes there is so create a timeseries mapping:
    #                 # value to replace (min/max/actual)
    #                 represented_value = col.split(
    #                     configurations.timeseries_seperator)[1]
    #                 series = list(
    #                     spellings.get_from(
    #                         energy_system_dict, smth_like='timeframe')[
    #                             col].values)

    #                 timeseries.update({str(represented_value): series})

    #         # was there any entry for the requested timeseries object ?
    #         if timeseries is not None:
    #             return timeseries

    #         # no there was not, so throw an error:
    #         else:
    #             logger.error(
    #                 '{} was requested to be linked '.format(
    #                     spellings.get_from(es_object, smth_like='name')) +
    #                 'to a timeseries, but no respective entry was found ' +
    #                 'in {}.'.format(list(spellings.get_from(
    #                     energy_system_dict, smth_like='timeseries').columns)))
    #             raise KeyError("No 'Uid-like' key found in {}".format(
    #                 list(spellings.get_from(
    #                     energy_system_dict, smth_like='timeseries').columns)))

    #     # no it has not, so throw an error:
    #     else:
    #         logger.error(
    #             "{} was requested to be characterized ".format(
    #                 spellings.get_from(es_object, smth_like='name')) +
    #             "by a timeseries, but a 'timeframe'-like key was not " +
    #             'found in {}'.format(energy_system_dict.keys()))
    #         raise KeyError(
    #             "No 'timeframe'-like key found in {}".format(
    #                 energy_system_dict.keys()))

    # # no, es object is not requested to be linked to a timeseries
    # else:
    #     return None


@log.timings
def generate_busses(energy_system_dict):
    """
    Generate :class:`~oemof.solph.network.Bus` objects out of the
    :paramref:`~generate_busses.energy_system_dict`.

    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    Return
    ------
    generated_busses: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`bus objects <oemof.solph.network.Bus>`.

    """
    busses = spellings.get_from(energy_system_dict, smth_like='bus',
                                dflt=pd.DataFrame())

    for row, bus in busses.iterrows():
        # check active switch, but assume user forgot adding one
        # and meant to add all entries listed
        if spellings.get_from(bus, smth_like='active', dflt=esn['active']):

            yield solph.Bus(
                label=nt.Uid(
                    name=spellings.get_from(
                        bus, smth_like='name',
                        dflt=esn['name']),
                    latitude=spellings.get_from(
                        bus, smth_like='latitude',
                        dflt=esn['latitude']),
                    longitude=spellings.get_from(
                        bus, smth_like='longitude',
                        dflt=esn['longitude']),
                    region=spellings.get_from(
                        bus, smth_like='region',
                        dflt=esn['region']),
                    sector=spellings.get_from(
                        bus, smth_like='sector',
                        dflt=esn['sector']),
                    carrier=spellings.get_from(
                        bus, smth_like='carrier',
                        dflt=esn['carrier']),
                    node_type=spellings.get_from(
                        bus, smth_like='node_type',
                        dflt=esn['node_type'])))


@log.timings
def generate_sources(energy_system_dict, bus_dict):
    """
    Generate :class:`~oemof.solph.network.Source` objects out of the
    :paramref:`~generate_sources.energy_system_dict` connecting to the
    :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_sources.bus_dict`

    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    Return
    ------
    generated_sources: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`source objects <oemof.solph.network.Source>`.

    """
    kinds_of_sources = [
        spellings.get_from(
            energy_system_dict, smth_like='renewables', dflt=pd.DataFrame()),
        spellings.get_from(
            energy_system_dict, smth_like='commodity', dflt=pd.DataFrame()),
        spellings.get_from(
            energy_system_dict, smth_like='import', dflt=pd.DataFrame()),
        spellings.get_from(
            energy_system_dict, smth_like='backup', dflt=pd.DataFrame()), ]

    for sources in kinds_of_sources:

        # iterate though energy system object (= data sheet rows)
        for row, source in sources.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(source, smth_like='active', dflt=1):

                yield solph.Source(
                    label=nt.Uid(
                        name=spellings.get_from(
                            source, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            source, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            source, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            source, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            source, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            source, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            source, smth_like='node_type',
                            dflt=esn['node_type'])),
                    outputs={
                        bus_dict[spellings.get_from(
                            source, smth_like='output',
                            dflt=esn['output'])]:
                        solph.Flow(
                            **parse_flow_parameters(
                                es_object=source,
                                timeseries=parse_timeseries(
                                    source, energy_system_dict))
                        )})


@log.timings
def generate_sinks(energy_system_dict, bus_dict):
    """
    Generate :class:`~oemof.solph.network.Sink` objects out of the
    :paramref:`~generate_sinks.energy_system_dict` connecting to the
    :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_sinks.bus_dict`

    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    Return
    ------
    generated_sinks: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`sink objects <oemof.solph.network.Sink>`.

    """
    kinds_of_sinks = [
        spellings.get_from(
            energy_system_dict, smth_like='demand', dflt=pd.DataFrame()),
        spellings.get_from(
            energy_system_dict, smth_like='export', dflt=pd.DataFrame()),
        spellings.get_from(
            energy_system_dict, smth_like='excess', dflt=pd.DataFrame()),
    ]

    for sinks in kinds_of_sinks:

        # iterate though energy system object (= data sheet rows)
        for row, sink in sinks.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(sink, smth_like='active',
                                  dflt=esn['active']):

                yield solph.Sink(
                    label=nt.Uid(
                        name=spellings.get_from(
                            sink, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            sink, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            sink, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            sink, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            sink, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            sink, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            sink, smth_like='node_type',
                            dflt=esn['node_type'])),
                    inputs={
                        bus_dict[spellings.get_from(
                            sink, smth_like='input',
                            dflt=esn['input'])]:
                        solph.Flow(
                            **parse_flow_parameters(
                                es_object=sink,
                                timeseries=parse_timeseries(
                                    sink, energy_system_dict))
                        )})


@log.timings
def generate_mimo_transformers(energy_system_dict, bus_dict):
    """
    Generate multiple-input multiple output
    :class:`~oemof.solph.network.Transformer` objects out of the
    :paramref:`~generate_mimo_transformers.energy_system_dict` connecting to
    the :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_mimo_transformers.bus_dict`

    Note
    ----
    Mimo transformer parsing assumes `zero-based numbering
    <https://en.wikipedia.org/wiki/Zero-based_numbering>`_! and are parsed
    based on respective :mod:`~tessif.frused.spellings`.

    Notably:

        - :attr:`~tessif.frused.spellings.inputN`
        - :attr:`~tessif.frused.spellings.inflow_costsN`
        - :attr:`~tessif.frused.spellings.inflow_emissionsN`
        - :attr:`~tessif.frused.spellings.fractionN`

        - :attr:`~tessif.frused.spellings.outputN`
        - :attr:`~tessif.frused.spellings.outflow_costsN`
        - :attr:`~tessif.frused.spellings.outflow_emissionsN`
        - :attr:`~tessif.frused.spellings.efficiencyN`


    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    Return
    ------
    generated_transformers: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`transformer objects <oemof.solph.network.Transformer>`.

    """
    kinds_of_transformers = [
        spellings.get_from(
            energy_system_dict, smth_like='mimo_transformer',
            dflt=pd.DataFrame()),
    ]

    for transformers in kinds_of_transformers:

        # iterate though energy system object (= data sheet rows)
        for row, transformer in transformers.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(transformer, smth_like='active',
                                  dflt=esn['active']):

                inputs, outputs, conversions = {}, {}, {}
                inbusses, fractions, inflow_costs, = [], [], []
                inflow_emissions, outflow_costs = [], []
                outflow_emissions = []
                outbusses, efficiencies = [], []

                for i in range(
                        spellings.get_from(
                            transformer, smth_like='number_of_connections',
                            dflt=esn['number_of_connections'])):

                    # figure out all the input busses
                    for variation in spellings.inputN:
                        if variation in transformer and str(i) in variation:
                            inbusses.append(transformer[variation])

                    # figure out all the input flow costs
                    for variation in spellings.inflow_costsN:
                        if variation in transformer and str(i) in variation:
                            inflow_costs.append(transformer[variation])

                    # figure out all the input dependent emissions
                    for variation in spellings.inflow_emissionsN:
                        if variation in transformer and str(i) in variation:
                            inflow_emissions.append(transformer[variation])

                    # figure out how the input flows are distributed
                    for variation in spellings.fractionN:
                        if variation in transformer and str(i) in variation:
                            fractions.append(transformer[variation])

                    # find out all the output busses
                    for variation in spellings.outputN:
                        if variation in transformer and str(i) in variation:
                            outbusses.append(transformer[variation])

                    # figure out all the output flow costs
                    for variation in spellings.outflow_costsN:
                        if variation in transformer and str(i) in variation:
                            outflow_costs.append(transformer[variation])

                    # figure out all the output dependent emissions
                    for variation in spellings.outflow_emissionsN:
                        if variation in transformer and str(i) in variation:
                            outflow_emissions.append(
                                transformer[variation])

                    # find out all the conversion efficiencies
                    for variation in spellings.efficiencyN:
                        if variation in transformer and str(i) in variation:
                            efficiencies.append(transformer[variation])

                # create an inputs dictionary ready to pass
                inputs.update({bus_dict[bus]: solph.Flow(
                    variable_costs=costs,
                    emissions=emissions)
                    for bus, costs, emissions in zip(
                        inbusses, inflow_costs, inflow_emissions)})

                # create an outputs dictionary ready to pass
                for i, bus in enumerate(outbusses):

                    parameters = {}
                    # output 0 is treated as 'characteristic solph flow'
                    if i == 0:
                        parameters = parse_flow_parameters(transformer)
                        parameters.update({
                            'characteristic_flow_target': bus_dict[
                                outbusses[0]]})

                    parameters.update({
                        'variable_costs': outflow_costs[i],
                        'emissions': outflow_emissions[i]})

                    outputs.update({bus_dict[bus]: solph.Flow(**parameters)})

                # create a conversions dictionary ready to pass
                # map inflows and their fraction
                conversions.update(
                    {bus_dict[bus]: fraction
                     for bus, fraction in zip(
                        inbusses, fractions)})

                # map outflows and their efficiencies
                conversions.update(
                    {bus_dict[bus]: efficiency
                     for bus, efficiency in zip(
                        outbusses, efficiencies)})

                yield solph.Transformer(
                    label=nt.Uid(
                        name=spellings.get_from(
                            transformer, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            transformer, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            transformer, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            transformer, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            transformer, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            transformer, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            transformer, smth_like='node_type',
                            dflt=esn['node_type'])),
                    outputs=outputs,
                    inputs=inputs,
                    conversion_factors=conversions,
                )


@log.timings
def generate_sito_flex_transformers(energy_system_dict, bus_dict):
    """
    Generate single input two output
    :class:`~oemof.solph.components.ExtractionTurbineCHP` objects out of the
    :paramref:`~generate_sito_flex_transformers.energy_system_dict` connecting
    to the :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_sito_flex_transformers.bus_dict`

    Note
    ----
    Sito flex transformer parsing assumes `zero-based numbering
    <https://en.wikipedia.org/wiki/Zero-based_numbering>`_! for the outflows
    and are parsed based on respective :mod:`~tessif.frused.spellings`.

    Notably:

        - :attr:`~tessif.frused.spellings.outputN`
        - :attr:`~tessif.frused.spellings.outflow_costsN`
        - :attr:`~tessif.frused.spellings.outflow_emissionsN`
        - :attr:`~tessif.frused.spellings.efficiencyN`


    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    Return
    ------
    generated_sito_flex_transformers: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`Single Input Two Output Flexible Transformer objects
        <oemof.solph.components.ExtractionTurbineCHP>`.

    """
    kinds_of_sito_flex_transformers = [
        spellings.get_from(
            energy_system_dict, smth_like='sito_flex_transformer',
            dflt=pd.DataFrame()),
    ]

    for transformers in kinds_of_sito_flex_transformers:

        # iterate though energy system object (= data sheet rows)
        for row, transformer in transformers.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(transformer, smth_like='active',
                                  dflt=esn['active']):

                outputs, conversions = {}, {}
                outbusses, outflow_costs = [], []
                outflow_emissions, efficiencies = [], []

                for i in range(2):

                    # find out all the output busses
                    for variation in spellings.outputN:
                        if variation in transformer and str(i) in variation:
                            outbusses.append(transformer[variation])

                    # figure out all the output flow costs
                    for variation in spellings.outflow_costsN:
                        if variation in transformer and str(i) in variation:
                            outflow_costs.append(transformer[variation])

                    # figure out all the output dependent emissions
                    for variation in spellings.outflow_emissionsN:
                        if variation in transformer and str(i) in variation:
                            outflow_emissions.append(
                                transformer[variation])

                    # find out all the conversion efficiencies
                    for variation in spellings.efficiencyN:
                        if variation in transformer and str(i) in variation:
                            efficiencies.append(transformer[variation])

                # create an outputs dictionary ready to pass
                for i, bus in enumerate(outbusses):

                    parameters = {}
                    # output 0 is treated as 'characteristic solph flow'
                    if i == 0:
                        parameters = parse_flow_parameters(transformer)
                        parameters.update({
                            'characteristic_flow_target': bus_dict[
                                outbusses[0]]})

                    parameters.update({
                        'variable_costs': outflow_costs[i],
                        'emissions': outflow_emissions[i]})

                    outputs.update({bus_dict[bus]: solph.Flow(
                        **parameters)})

                # map outflows and their efficiencies
                conversions.update(
                    {bus_dict[bus]: efficiency
                     for bus, efficiency in zip(
                        outbusses, efficiencies)})

                yield solph.components.ExtractionTurbineCHP(
                    label=nt.Uid(
                        name=spellings.get_from(
                            transformer, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            transformer, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            transformer, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            transformer, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            transformer, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            transformer, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            transformer, smth_like='node_type',
                            dflt=esn['node_type'])),
                    inputs={
                        bus_dict[spellings.get_from(
                            transformer, smth_like='input',
                            dflt=esn['input'])]:
                        solph.Flow(
                            variable_costs=spellings.get_from(
                                transformer, smth_like='inflow_costs',
                                dflt=esn['flow_costs']),
                            emissions=spellings.get_from(
                                transformer, smth_like='emissions',
                                dflt=esn['emissions']))},
                    outputs=outputs,
                    conversion_factors=conversions,
                    conversion_factor_full_condensation={
                        bus_dict[outbusses[0]]:
                            spellings.get_from(
                                transformer, smth_like='efficiency',
                                dflt=esn['efficiency'])})


@log.timings
def generate_generic_chps(energy_system_dict, bus_dict, timeindex=None):
    """
    Generate single input two output
    :class:`~oemof.solph.components.GenericCHP` objects out of the
    :paramref:`~generate_generic_chps.energy_system_dict` connecting to
    the :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_generic_chps.bus_dict`

    Note
    ----
    This might become a convenience wrapper interface to parameterize
    the  objects more intuitively.

    Following mapping is used for parsing::

        parameter_name_mapping = {
            'minimum_fuelgas_losses': 'H_L_FG_share_min',
            'maximum_fuelgas_losses': 'H_L_FG_share_max',
            'maximum_power': 'P_max_woDH',
            'minimum_power': 'P_min_woDH',
            'maximum_efficiency': 'Eta_el_max_woDH',
            'minimum_efficiency': 'Eta_el_min_woDH',
            'minimum_heat': 'Q_CW_min',
            'power_loss_index': 'Beta',}

    Where the respective :mod:`~tessif.frused.spellings` (left hand side) are
    mapped to the :class:`~oemof.solph.components.GenericCHP` parameters
    (right hand side)


    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    timeindex: :class:`~pandas.DatetimeIndex`, default=None
        Representation of the time frame and resolution used in the simulation.
        If none, the timeindex is tried to be inferred from
        :paramref:`~generate_generic_chps.energy_system_dict` using
        :func:`infer_timeindex`.

    Return
    ------
    generated_generic_chps: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`generic chp objects <oemof.solph.components.GenericCHP>`.

    """
    parameter_name_mapping = {
        'minimum_fuelgas_losses': 'H_L_FG_share_min',
        'maximum_fuelgas_losses': 'H_L_FG_share_max',
        'maximum_power': 'P_max_woDH',
        'minimum_power': 'P_min_woDH',
        'maximum_efficiency': 'Eta_el_max_woDH',
        'minimum_efficiency': 'Eta_el_min_woDH',
        'minimum_heat': 'Q_CW_min',
        'power_loss_index': 'Beta',
    }

    if timeindex is None:
        timeindex = infer_timeindex(energy_system_dict)

    kinds_of_generic_chps = [
        spellings.get_from(
            energy_system_dict, smth_like='generic_chp',
            dflt=pd.DataFrame()),
    ]

    for transformers in kinds_of_generic_chps:

        # iterate though energy system object (= data sheet rows)
        for row, transformer in transformers.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(transformer, smth_like='active',
                                  dflt=esn['active']):

                timeseries_values = parse_timeseries(
                    transformer, energy_system_dict)

                parameters = {}

                # iterate through all parameters the generic chp expects:
                for parameter in parameter_name_mapping.keys():
                    if timeseries_values:
                        timeseries_value = spellings.get_from(
                            timeseries_values, smth_like=parameter,
                            dflt=esn['timeseries'])
                        if timeseries_value is not None:
                            parameters.update(
                                {parameter_name_mapping[
                                    parameter]: timeseries_value})
                    else:
                        fixed_value = spellings.get_from(
                            transformer, smth_like=parameter)
                        parameters.update(
                            {parameter_name_mapping[parameter]: [
                                fixed_value for i in range(len(timeindex))]})

                yield solph.components.GenericCHP(
                    label=nt.Uid(
                        name=spellings.get_from(
                            transformer, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            transformer, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            transformer, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            transformer, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            transformer, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            transformer, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            transformer, smth_like='node_type',
                            dflt=esn['node_type'])),
                    fuel_input={
                        bus_dict[spellings.get_from(
                            transformer, smth_like='fuel_in',
                            dflt=esn['input'])]:
                        solph.Flow(
                            H_L_FG_share_min=parameters['H_L_FG_share_min']
                            if not all(np.isnan(i) for i in parameters[
                                'H_L_FG_share_min']) else None,
                            H_L_FG_share_max=parameters['H_L_FG_share_max'],
                            installed_capacity=parameters['P_max_woDH'][0],
                            **parse_flow_parameters(
                                es_object=transformer,
                                timeseries=parse_timeseries(
                                    transformer, energy_system_dict)))},
                    electrical_output={
                        bus_dict[spellings.get_from(
                            transformer, smth_like='power_out',
                            dflt=esn['output'])]:
                        solph.Flow(
                            P_max_woDH=parameters['P_max_woDH'],
                            P_min_woDH=parameters['P_min_woDH'],
                            Eta_el_max_woDH=parameters['Eta_el_max_woDH'],
                            Eta_el_min_woDH=parameters['Eta_el_min_woDH'],
                            variable_costs=spellings.get_from(
                                transformer, smth_like='power_costs',
                                dflt=esn['flow_costs']),
                            emissions=spellings.get_from(
                                transformer, smth_like='power_emissions',
                                dflt=esn['emissions']),
                        )},
                    heat_output={
                        bus_dict[spellings.get_from(
                            transformer, smth_like='heat_out',
                            dflt=esn['output'])]:
                        solph.Flow(
                            Q_CW_min=parameters['Q_CW_min'],
                            variable_costs=spellings.get_from(
                                transformer, smth_like='heat_costs',
                                dflt=esn['flow_costs']),
                            emissions=spellings.get_from(
                                transformer, smth_like='heat_emissions',
                                dflt=esn['emissions']),
                        )},
                    Beta=parameters['Beta'],
                    back_pressure=spellings.get_from(
                        transformer, smth_like='back_pressure',
                        dflt=esn['back_pressure']))


@log.timings
def generate_siso_nonlinear_transformers(energy_system_dict, bus_dict):
    """
    Generate :class:`~oemof.solph.components.OffsetTransformer` objects out of
    the  :paramref:`~generate_siso_nonlinear_transformers.energy_system_dict`
    connecting to the :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_siso_nonlinear_transformers.bus_dict`

    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    Return
    ------
    generated_siso_nonlinear_transformers: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`offset transformer objects
        <oemof.solph.components.OffsetTransformer>`.

    """
    kinds_of_transformers = [
        spellings.get_from(
            energy_system_dict, smth_like='siso_nonlinear_transformer',
            dflt=pd.DataFrame()),
    ]

    for transformers in kinds_of_transformers:

        # iterate though energy system object (= data sheet rows)
        for row, transformer in transformers.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(transformer, smth_like='active',
                                  dflt=esn['active']):

                output_max = spellings.get_from(
                    transformer, smth_like='output_maximum',
                    dflt=esn['maximum'])
                output_min = spellings.get_from(
                    transformer, smth_like='output_minimum',
                    dflt=esn['minimum'])
                input_max = output_max / spellings.get_from(
                    transformer, smth_like='maximum_efficiency',
                    dflt=esn['maximum_efficiency'])
                input_min = output_min / spellings.get_from(
                    transformer, smth_like='minimum_efficiency',
                    dflt=esn['minimum_efficiency'])

                # ((max-min)/(min-max))
                c1 = (output_max - output_min) / (input_max - input_min)
                c0 = output_max - c1 * input_max

                yield solph.components.OffsetTransformer(
                    label=nt.Uid(
                        name=spellings.get_from(
                            transformer, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            transformer, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            transformer, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            transformer, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            transformer, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            transformer, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            transformer, smth_like='node_type',
                            dflt=esn['node_type'])),
                    inputs={
                        bus_dict[spellings.get_from(
                            transformer, smth_like='input',
                            dflt=esn['input'])]:
                        solph.Flow(
                            **parse_flow_parameters(
                                es_object=transformer,
                                timeseries=parse_timeseries(
                                    transformer, energy_system_dict)))},
                    outputs={
                        bus_dict[spellings.get_from(
                            transformer, smth_like='output',
                            dflt=esn['output'])]:
                        solph.Flow(
                            variable_costs=spellings.get_from(
                                transformer, smth_like='outflow_costs',
                                dflt=esn['flow_costs']),
                            emissions=spellings.get_from(
                                transformer, smth_like='outflow_emissions',
                                dflt=esn['emissions']))},
                    coefficients=[c0, c1])


@log.timings
def generate_generic_storages(energy_system_dict, bus_dict):
    """
    Generate :class:`~oemof.solph.GenericStorage` objects out of
    the  :paramref:`~generate_generic_storages.energy_system_dict`
    connecting to the :class:`~oemof.solph.network.Bus` objects in
    :paramref:`~generate_generic_storages.bus_dict`

    Parameters
    ----------
    energy_system_dict: dict
        Dictionary of :class:`pandas.DataFrame` objects keyed by strings.
        With the key strings representing energy system components.
        Usually returned by something like the :mod:`tessif.parse`
        functionalities.

    bus_dict: dict
        Dictionary of :class:`~oemof.solph.network.Bus` objects keyed
        by their ``str(label)`` representation.

    Return
    ------
    generated_generic_storages: :class:`~collections.abc.Generator`
        Generator object yielding the parsed
        :class:`offset storage objects
        <oemof.solph.components.OffsetStorage>`.

    """
    kinds_of_storages = [
        spellings.get_from(
            energy_system_dict, smth_like='generic_storage',
            dflt=pd.DataFrame()),
    ]

    for storages in kinds_of_storages:

        # iterate though energy system object (= data sheet rows)
        for row, storage in storages.iterrows():

            # check active switch, but assume user forgot adding one
            # and meant to add all entries listed
            if spellings.get_from(storage, smth_like='active',
                                  dflt=esn['active']):

                # Get storage capacity
                nominal_storage_capacity = spellings.get_from(
                    storage, smth_like='storage_capacity',
                    dflt=esn['installed_capacity'])

                # change np.nan to None, cause oemof can't handle nan
                if np.isnan(nominal_storage_capacity):
                    nominal_storage_capacity = None

                # Find out if storage capacity itself is subject to investment
                # by filtering for 'storage_' included tags
                investment_parameters = dict(*dutils.kfrep(
                    dcts=dutils.kfltr(
                        dcts=[storage], fltr='storage_'),
                    fnd='storage_', rplc=''))

                # kick out nominal_storage_capacity
                for key in investment_parameters.copy().keys():
                    if 'capacity' in key:
                        investment_parameters.pop(key)

                # Check if capacity is indeed requested to be optimized
                if spellings.get_from(investment_parameters,
                                      smth_like='expansion_problem',
                                      dflt=esn['expandable']) == 1:
                    # if so parse the investment flow parameters
                    investment = parse_invest_flow_params(
                        investment_parameters)['investment']
                # if not, set the investment object None
                else:
                    investment = None

                yield solph.components.GenericStorage(
                    label=nt.Uid(
                        name=spellings.get_from(
                            storage, smth_like='name',
                            dflt=esn['name']),
                        latitude=spellings.get_from(
                            storage, smth_like='latitude',
                            dflt=esn['latitude']),
                        longitude=spellings.get_from(
                            storage, smth_like='longitude',
                            dflt=esn['longitude']),
                        region=spellings.get_from(
                            storage, smth_like='region',
                            dflt=esn['region']),
                        sector=spellings.get_from(
                            storage, smth_like='sector',
                            dflt=esn['sector']),
                        carrier=spellings.get_from(
                            storage, smth_like='carrier',
                            dflt=esn['carrier']),
                        node_type=spellings.get_from(
                            storage, smth_like='node_type',
                            dflt=esn['node_type'])),
                    loss_rate=spellings.get_from(
                        storage, smth_like='loss_rate',
                        dflt=esn['loss_rate']),
                    nominal_storage_capacity=nominal_storage_capacity,
                    inputs={
                        bus_dict[spellings.get_from(
                            storage, smth_like='input',
                            dflt=esn['input'])]:
                        solph.Flow(
                            **parse_flow_parameters(
                                *dutils.kfrep(
                                    dcts=dutils.kfltr(
                                        dcts=[storage], fltr='inflow_'),
                                    fnd='inflow_', rplc='')))},
                    outputs={
                        bus_dict[spellings.get_from(
                            storage, smth_like='output',
                            dflt=esn['output'])]:
                        solph.Flow(
                            **parse_flow_parameters(
                                *dutils.kfrep(
                                    dcts=dutils.kfltr(
                                        dcts=[storage], fltr='outflow_'),
                                    fnd='outflow_', rplc='')))},
                    inflow_conversion_factor=spellings.get_from(
                        storage, smth_like='inflow_efficiency',
                        dflt=esn['efficiency']),
                    outflow_conversion_factor=spellings.get_from(
                        storage, smth_like='outflow_efficiency',
                        dflt=esn['efficiency']),
                    investment=investment,
                    balanced=False)


@log.timings
def create_nodes(
        es_object_types,
        info_tag='Info', bus_tag='Grid', renewables_tag='Renewable',
        chp_tag='CHP', powerplant_tag='PowerPlant', heatplant_tag='HeatPlant',
        commodity_tag='Commodity', demand_tag='Demand',
        timeseries_tag='Timeseries'):
    """
    Create the energy system nodes.
    """

    # 1.) Clean up dict:
    # 1.1.) Remove info entry:
    if info_tag in es_object_types:
        es_object_types.pop(info_tag)

    # 2.) Create
    # list of nodes to create the energy system
    es_nodes = list(generate_busses(es_object_types))
    # bus dictionary for creating non-bus energy system objects
    bus_dict = dict({str(v.label): v for v in es_nodes})

    # add sources to the energy system nodes i.e
    # (renewables, commodities, imports, backups ...)
    for source in generate_sources(es_object_types, bus_dict):
        es_nodes.append(source)

    # add sink to the energy system nodes i.e
    # (demands, excess nodes, exports, ...)
    for sink in generate_sinks(es_object_types, bus_dict):
        es_nodes.append(sink)

    # add multiple input multiple output transformers
    for transformer in generate_mimo_transformers(es_object_types, bus_dict):
        es_nodes.append(transformer)

    # add single input two outputs generic chps
    for generic_chp in generate_generic_chps(es_object_types, bus_dict):
        es_nodes.append(generic_chp)

    # add single input two outputs sito flex transformers
    for sito_flex_transformer in generate_sito_flex_transformers(
            es_object_types, bus_dict):
        es_nodes.append(sito_flex_transformer)

    # add single input single output offset transformers
    for transformer in generate_siso_nonlinear_transformers(
            es_object_types, bus_dict):
        es_nodes.append(transformer)

    # add generic storages
    for storage in generate_generic_storages(es_object_types, bus_dict):
        es_nodes.append(storage)

    return es_nodes


@log.timings
def infer_timeindex(energy_system_dictionary):
    """
    Try inferring the timeindex from the energy system dictionairy.

    The timeframe to be simulated is referred to here as "timeindex".

    Parameters
    ----------
    energy_system_dictionary: dict
        Dictionairy containing the energy system data. Typically returned by
        one of the :mod:`tessif.parse` functionalities

    Return
    ------
    timeindex: :class:`~pandas.DatetimeIndex`
        The time frame inferred from the energy system dictionairy.

    Example
    -------
    Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
    logging level to debug for decluttering doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Read in the oemof standard energy system and transform it:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> from tessif.parse import xl_like
    >>> import tessif.transform.mapping2es.omf as tomf
    >>> idx = tomf.infer_timeindex(xl_like(
    ...     os.path.join(
    ...         example_dir, 'data', 'omf', 'xlsx', 'energy_system.xlsx')))
    >>> print(idx)
    DatetimeIndex(['2016-01-01 00:00:00', '2016-01-01 01:00:00',
                   '2016-01-01 02:00:00', '2016-01-01 03:00:00',
                   '2016-01-01 04:00:00'],
                  dtype='datetime64[ns]', freq='H')
    """
    # find out which expression of 'Timeseries' was used
    ts_key = [variant for variant in spellings.timeframe
              if variant in energy_system_dictionary.keys()][0]

    # find out which expression of 'Timeindex' was used
    idx_key = [variant for variant in spellings.timeindex
               if variant in energy_system_dictionary[ts_key].columns][0]

    # Extract the time index
    timeindex = pd.DatetimeIndex(
        energy_system_dictionary[ts_key][idx_key].values, freq='infer')

    # Round to time index according to temporal resolution settings to...
    # correct rounding errors of the input source due to time format display
    timeindex = timeindex.round(
        resolutions.temporal_rounding_map[configurations.temporal_resolution])

    # Reinfer frequency from newly round time index
    timeindex = pd.DatetimeIndex(timeindex, freq='infer')

    return timeindex


@log.timings
def transform(energy_system_dictionary, **kwargs):
    """
    Transform an ES dict to an oemof :class:`~oemof.energy_system.EnergySystem`

    Parameters
    ----------
    energy_system_dictionary: dict
        Dictionairy containing the energy system data. Typically returned by
        one of the :mod:`tessif.parse` functionalities

    timeindex: :class:`~pandas.DatetimeIndex`, default=None
        Representation of the time frame and resolution
        If not stated it is tried to be :meth:`inferred<infer_timeindex>`.

    global_constraints: dict, default={'emissions': float('+inf')}
        Dictionairy of constraint values mapped to constraint names.

    kwargs:
        Key word arguments are passed to
        :meth:`~oemof.energy_system.EnergySystem.add`

    Return
    ------
    energy_system: :class:`~oemof.energy_system.EnergySystem`
        The dictionairy transformed oemof energy system, ready for simulation.

    Example
    -------
    Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
    logging level to debug for decluttering doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Read in the oemof standard energy system and transform it:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> from tessif.parse import xl_like
    >>> import tessif.transform.mapping2es.omf as tomf
    >>> es = tomf.transform(xl_like(
    ...     os.path.join(
    ...         example_dir, 'data', 'omf', 'xlsx', 'energy_system.xlsx')))
    >>> print(type(es))
    <class 'oemof.solph.network.energy_system.EnergySystem'>

    >>> print(*[node for node in es.nodes if str(node.label) == 'Power Grid'])
    Power Grid

    Read in an ods version instead:

    >>> es = tomf.transform(xl_like(
    ...     os.path.join(
    ...         example_dir, 'data', 'omf', 'xlsx', 'energy_system.ods'),
    ...     engine='odf'))
    """

    # get/default global constraints
    global_constraints = kwargs.pop(
        'global_constraints',
        energy_system_dictionary.get(
            'global_constraints',
            {'emissions': float('+inf')}))

    # get/infer timeindex
    timeindex = kwargs.pop(
        'timeindex', infer_timeindex(energy_system_dictionary))

    nodes = create_nodes(energy_system_dictionary)

    # Create energy system object
    energy_system = solph.EnergySystem(timeindex=timeindex)

    # Adding the read in nodes to the energy system:
    energy_system.add(*nodes, **kwargs)

    # Add the global constraints:
    energy_system.global_constraints = global_constraints

    return energy_system
