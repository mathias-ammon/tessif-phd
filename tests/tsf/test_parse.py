import unittest
import os
from tessif.frused.paths import example_dir
from tessif import parse
import collections
import tessif.frused.configurations as configurations
from tessif.examples.data.tsf.py_mapping import fpwe as fpwe


class TestTessifsParsing(unittest.TestCase):

    def setUp(self):
        pass

    def test_flat_config(self):
        esm = parse.flat_config_folder(
            folder=os.path.join(example_dir, 'data', 'tsf', 'cfg', 'flat',
                                'basic'))

        # test mapping type to be ordered dict
        self.assertEqual(isinstance(esm, collections.OrderedDict), True)

        # check for key consistency
        self.assertEqual(
            sorted(esm.keys()),
            ['bus', 'global_constraints', 'sink', 'source', 'storage',
             'timeframe', 'transformer'])

        # check for succesfull reordering
        configurations.spellings_logging_level = 'debug'
        self.assertEqual(
            list(parse.reorder_esm(esm).keys()),
            ['bus', 'sink', 'source', 'storage', 'transformer', 'timeframe'])

    def test_xllike(self):
        omf_esm = parse.xl_like(
            io=os.path.join(example_dir, 'data', 'omf', 'xlsx',
                            'energy_system.xlsx'))
        generic_chp_esm = parse.xl_like(
            io=os.path.join(example_dir, 'data', 'omf', 'xlsx',
                            'generic_chp.ods'),
            engine='odf')
        generic_storage_esm = parse.xl_like(
            io=os.path.join(example_dir, 'data', 'omf', 'xlsx',
                            'generic_storage.ods'),
            engine='odf')
        siso_nonlinear_transformer_esm = parse.xl_like(
            io=os.path.join(
                example_dir, 'data', 'omf', 'xlsx', 'offset_transformer.ods'),
            engine='odf')
        sito_flex_transformer_esm = parse.xl_like(
            io=os.path.join(
                example_dir, 'data', 'omf', 'xlsx',
                'sito_flex_transformer.ods'),
            engine='odf')

        # test mapping type to be ordered dict
        self.assertEqual(isinstance(omf_esm, collections.OrderedDict), True)
        self.assertEqual(isinstance(generic_chp_esm,
                                    collections.OrderedDict), True)
        self.assertEqual(isinstance(generic_storage_esm,
                                    collections.OrderedDict), True)
        self.assertEqual(isinstance(siso_nonlinear_transformer_esm,
                                    collections.OrderedDict), True)
        self.assertEqual(isinstance(sito_flex_transformer_esm,
                                    collections.OrderedDict), True)

        # check for key consistency
        self.assertEqual(
            sorted(omf_esm.keys()),
            ['Commodity', 'Demand', 'Grid', 'Info', 'Renewable',
             'global_constraints', 'mimo_transformers', 'timeframe'])
        self.assertEqual(
            sorted(generic_chp_esm.keys()),
            ['Commodity', 'Demand', 'Grid', 'Info',
             'generic_chp', 'global_constraints', 'timeframe'])
        self.assertEqual(
            sorted(generic_storage_esm.keys()),
            ['Commodity', 'Demand', 'Grid', 'Info', 'Renewable',
             'generic_storage', 'global_constraints', 'timeframe'])
        self.assertEqual(
            sorted(siso_nonlinear_transformer_esm.keys()),
            ['Commodity', 'Demand', 'Grid', 'Info',
             'global_constraints', 'siso_nonlinear_transformer', 'timeframe'])
        self.assertEqual(
            sorted(sito_flex_transformer_esm.keys()),
            ['Commodity', 'Demand', 'Grid', 'Info',
             'global_constraints', 'sito_flex_transformer', 'timeframe'])

        # check for succesfull reordering
        configurations.spellings_logging_level = 'debug'
        self.assertEqual(
            list(parse.reorder_esm(omf_esm).keys()),
            ['bus', 'sink', 'source', 'transformer', 'timeframe'])
        self.assertEqual(
            list(parse.reorder_esm(generic_chp_esm).keys()),
            ['bus', 'sink', 'source', 'generic_chp', 'timeframe'])
        self.assertEqual(
            list(parse.reorder_esm(generic_storage_esm).keys()),
            ['bus', 'sink', 'source', 'storage', 'timeframe'])
        self.assertEqual(
            list(parse.reorder_esm(siso_nonlinear_transformer_esm).keys()),
            ['bus', 'sink', 'source',
             'siso_nonlinear_transformer', 'timeframe'])
        self.assertEqual(
            list(parse.reorder_esm(sito_flex_transformer_esm).keys()),
            ['bus', 'sink', 'source', 'sito_flex_transformer', 'timeframe'])

    def test_python_mapping(self):
        esm = parse.python_mapping(fpwe.mapping)

        # test mapping type to be ordered dict
        self.assertEqual(isinstance(esm, collections.OrderedDict), True)

        # check for key consistency
        self.assertEqual(
            sorted(esm.keys()),
            ['busses', 'global_constraints', 'sinks', 'sources', 'storages',
             'timeframe', 'transformers'])

        # check for succesfull reordering
        configurations.spellings_logging_level = 'debug'
        self.assertEqual(
            list(parse.reorder_esm(esm).keys()),
            ['bus', 'sink', 'source', 'storage', 'transformer', 'timeframe'])


if __name__ == '__main__':
    unittest.main()
