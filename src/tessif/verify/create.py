# tessif/verify/create.py
"""The verify create module holds the ScenarioJuggler class.

It simpliefies and somewhat automates the creation of verification scenarios.

The main access point of this class is designed to be the verify __init__
module, i.e. ``tessif.verify.ScenarioJuggler``.
"""
import pandas as pd
import os

from tessif.frused.paths import example_dir
import tessif.frused.namedtuples as nts
from tessif.transform.mapping2es import tsf
from tessif import parse


class ScenarioJuggler:
    """
    A nice description with examples and stuff
    """

    def __init__(self, constraint_types=('linear',), components=('source',)):
        self._all_constraint_types = ('linear', 'expansion', 'milp')
        self._all_components = (
            'source', 'sink', 'connector', 'transformer', 'storage')
        self.constraint_types = constraint_types
        self.components = components
        self.scenarios = (self.components, self.constraint_types)

    @property
    def constraint_types(self):
        return self._constraint_types

    @constraint_types.setter
    def constraint_types(self, tuple_of_strings):
        if tuple_of_strings == 'all':
            self._constraint_types = self._all_constraint_types
        elif not isinstance(tuple_of_strings, tuple):
            raise TypeError(
                '%s is not a tuple (filled with strings containing the wanted constraint types \
                "linear", "expansion" or "milp")' % (
                    tuple_of_strings))
        # if argument is a tuple and not 'all' [...]
        elif not tuple_of_strings == 'all':
            self._constraint_types = tuple_of_strings

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, tuple_of_strings):
        if tuple_of_strings == 'all':
            self._components = self._all_components
        elif not isinstance(tuple_of_strings, tuple):
            raise TypeError(
                '%s is not a tuple (filled with strings containing the wanted components \
                "source", "sink", "connector", "transformer" or "storage")' % (
                    tuple_of_strings))
        elif not tuple_of_strings == 'all':
            self._components = tuple_of_strings

    @property
    def scenarios(self):
        return self._scenarios

    # "Main"-Property of the class. Contains all Scenarios as AbstracedEnergySystem sorted in a Mapping ready for
    # proceeding in methods.
    @scenarios.setter
    def scenarios(self, components_and_constraints_tuple):
        components, constraints = components_and_constraints_tuple
        self._scenarios = {
            'connector': {
                'linear': None,
                'expansion': None,
                'milp': None,
            },
            'source': {
                'linear': None,
                'expansion': None,
                'milp': None,
            },
            'sink': {
                'linear': None,
                'expansion': None,
                'milp': None,
            },
            'transformer': {
                'linear': None,
                'expansion': None,
                'milp': None,
            },
            'storage': {
                'linear': None,
                'expansion': None,
                'milp': None,
            },
        }
        print(
            f'\n\n|--- SecenarioJuggler initiated with components=[{components}] and constraints=[{constraints}]')
        # Uses the _create_default_scenario function from <find good place!!!> to fill the property "scenarios" with
        # default scenarios
        for comp in components:
            for cons in constraints:
                for key in self._scenarios.keys():
                    if comp == key:
                        for key2 in self._scenarios[key]:
                            if cons == key2:
                                self._scenarios[key][key2] = _create_default_scenario(
                                    str(key), str(key2))
                                print(f'|--- successfully loaded scenario [{comp}][{cons}]')

    def save_scenario(self, component=('all',), constraint=('all',),
                      path=None):
        """
        Utility for saving created scenarios.

        Stores scenarios found in :attr:`ScenarioJuggler.scenarios`.

        Parameters
        ----------
        path: str, Path, None, default=None
            Path or string representation of a Path the scenario is saved at.
            If ``None`` (default) ``application/verification`` inside
            :attr:`~tessif.frused.paths.example_dir` is used.
        """

        if path is None:
            path = os.path.join(example_dir, "application",
                                "verification_scenarios_jug")

        print('\n|----- Saving process started\n')
        # Check if arguments are of correct type
        if not type(component) is tuple:
            raise SyntaxError(
                'argument (component) <%s> need to be of type tuple' % component)
        if not type(constraint) is tuple:
            raise SyntaxError(
                'Argument (constraint) <%s> need to be of type tuple' % constraint)
        if not type(self) is ScenarioJuggler:
            raise SyntaxError(
                'This method can only be used on entities of type \"VerificationScenarioJuggler\"')
        # Code block for saving all scenarios as xml to example dir
        # +++ THIS SECTION NEEDS TO BE OVERWORKED SO IT WORKS FOR ALL COMBINATIONS OF MIXED ARGUMENTS +++
        if component == ('all',) and constraint == ('all',):
            print('Saving all scenarios from instance...\n\n'
                  '[component]-[constraint]')
            for comp in self._all_components:
                p_comp = os.path.join(path, comp)
                for cons in self._all_constraint_types:
                    p_cons = os.path.join(p_comp, cons)
                    if not self.scenarios[comp][cons]:
                        print('[%s]-[%s]:   not defined in instance of object \'%s\'' % (
                            comp, cons, self.__class__.__name__))
                        continue
                    else:
                        with open(os.path.join(p_cons, 'test.xml'), 'w') as save:
                            save.write('some stuff')
                            print('%s-%s:   saved in %s' %
                                  (comp, cons, p_cons))
        # Code block for saving specific scenarios as xml to example dir
        else:
            # check if arguments are spelled correctly
            for comp in component:
                if comp not in self._all_components:
                    raise SyntaxError('argument %s need to be (a) valid component(s): \
                    (\'source\', \'sink\', \'connector\', \'transformer\', \'storage\' or \'all\' for component and constraint)' % component)
                else:
                    continue
            for cons in constraint:
                if not cons in self._all_constraint_types:
                    raise SyntaxError('argument %s need to be (a) valid constraint(s): \
                    (\'linear\', \'expansion\', \'milp\' or \'all\' for component and constraint)' % constraint)
                else:
                    continue
            # save scenarios in right folder
            print('Saving specified scenarios from instance...\n\n'
                  '[component]-[constraint]')
            for comp in component:
                p_comp = os.path.join(path, comp)
                for cons in constraint:
                    p_cons = os.path.join(p_comp, cons)
                    if not self.scenarios[comp][cons]:
                        print(
                            '[%s]-[%s]:   not defined in instance of object \'%s\': You can\'t save a scenario, which wasn\'t generated during the instantiation or added afterwards' % (
                                comp, cons, self.__class__.__name__))
                        continue
                    else:
                        filename = cons + '_test.xml'
                        with open(p_cons + '\\' + filename, 'w') as save:
                            save.write(self.scenarios[comp][cons].to_xml())
                            print('[%s]-[%s]:   saved in %s' %
                                  (comp, cons, p_cons))
        print('\n|----- Saving process finished\n \n \n')


def _create_default_scenario(component, constraint_type):
    scenario = None
    if component == 'source':
        if constraint_type == 'linear':
            source_linear_mapping = {
                'sources': {
                    's1': {
                        'name': 'source_1',
                        'outputs': ('electricity',),
                        'latitude': 42,
                        'longitude': 42,
                        'region': 'Here',
                        'sector': 'Power',
                        'carrier': 'Electricity',
                        'component': 'source',
                        'node_type': 'source',
                        'accumulated_amounts': {
                            'electricity': nts.MinMax(min=0, max=20)},
                        'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
                        'flow_costs': {'electricity': [1, 1, 2, 2]},
                        'flow_emissions': {'electricity': 3},
                        'flow_gradients': {
                            'electricity': nts.PositiveNegative(positive=100, negative=100)},
                        'gradient_costs': {
                            'electricity': nts.PositiveNegative(positive=0, negative=0)},
                        'timeseries': None,
                    },
                    's2': {
                        'name': 'source_2',
                        'outputs': ('electricity',),
                        'latitude': 42,
                        'longitude': 42,
                        'region': 'Here',
                        'sector': 'Power',
                        'carrier': 'Electricity',
                        'node_type': 'Renewable',
                        'component': 'source',
                        'accumulated_amounts': {
                            'electricity': nts.MinMax(min=0, max=20)},
                        'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
                        'flow_costs': {'electricity': 2},
                        'timeseries': None,
                    },
                },
                'transformers': {},
                'sinks': {
                    'sink': {
                        'name': 'sink',
                        'inputs': ('electricity',),
                        'latitude': 42,
                        'longitude': 42,
                        'region': 'Here',
                        'sector': 'Power',
                        'carrier': 'Electricity',
                        'node_type': 'sink',
                        'component': 'sink',
                        'accumulated_amounts': {
                            'electricity': nts.MinMax(
                                min=0, max=float('+inf'))},
                        'flow_rates': {
                            'electricity': nts.MinMax(min=10, max=10)},
                    },
                },
                'storages': {},
                'busses': {
                    'bus': {
                        'name': 'central_bus',
                        'inputs': (
                            'source_1.electricity',
                            'source_2.electricity',
                        ),
                        'outputs': ('sink.electricity',),
                        'latitude': 42,
                        'longitude': 42,
                        'region': 'Here',
                        'sector': 'Power',
                        'carrier': 'Electricity',
                        'node_type': 'central_bus',
                        'component': 'bus',
                    },
                },
                'timeframe': {
                    'primary': pd.date_range(
                        '01/01/2015', periods=4, freq='H'),
                    'secondary': pd.date_range(
                        '10/03/2019', periods=3, freq='H'),
                },
                'global_constraints': {
                    'primary': {'name': 'default',
                                'emissions': float('+inf'),
                                'material': float('+inf')},
                    'secondary': {'name': '80% Reduction',
                                  'emissions': 30,
                                  'material': float('+inf')},
                    'tertiary': {'name': '100% Reduction',
                                 'emissions': 0,
                                 'material': float('+inf')},
                    'quartiary': {'name': '100% Reduction - 50% Material',
                                  'emissions': 0,
                                  'resources': 20},
                },
            }  # minimum working example source - linear - flow_rate
            scenario = tsf.transform(
                parse.python_mapping(source_linear_mapping)
            )
    if not scenario:
        raise ValueError("A good error message")
    return scenario
