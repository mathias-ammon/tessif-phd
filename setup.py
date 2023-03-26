# setup.py
import setuptools
from os.path import abspath, dirname, join
from glob import glob
from os.path import basename
from os.path import splitext


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()


setuptools.setup(
    name='tessif-phd',
    version='0.0.1alpha',
    description='Transforming Energy Supply System modell I ng Framework',
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Dictionary :: Utilities :: Library',
    ],
    keywords='tessif framework energy_system_simulation tZE',
    url='http://collaborating.tuhh.de/ietma/tessif',
    author='Mathias Ammon',
    author_email='tz3ma.coding@use.startmail.com',
    license='MIT',
    # use_scm_version={
    #     'write_to': 'src/tessif/version.py',
    #     'write_to_template': '__version__ = "{version}"\n',
    #     'tag_regex': r'^(?P<prefix>v)?(?P<version>[^\+]+)(?P<suffix>.*)?$',
    #     'local_scheme': 'node-and-timestamp',
    # },
    # setup_requires=['setuptools_scm'],
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        'docs': ['*.rst'],
        '': ['xlsx/*', 'basic/*.cfg', 'objectives/*.cfg', 'nested/*.cfg',
             'xml/*.xml', 'hdf5/*.hdf5', 'load_profiles/*.csv'],
    },
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    install_requires=[

        # oemof is also incompatible with the newest version of numpy/pandas
        # 'pyutilib<6.0.0',
        # 'numpy<1.18,>=1.7.0',
        # 'pandas<0.26,>=0.18.0',

        # used primarily for signals (engineering kinds of signals)
        "numpy==1.23.1",
        'scipy',

        # used for graphs graph plotting
        'dash',
        'dash-cytoscape',
        'werkzeug==2.2.0',  # pin for dissertation
        'matplotlib',
        'networkx',
        'pygraphviz',
        'pyqt5',
        'seaborn',

        # used for pandas reading in excels and odfs
        'xlrd',
        'odfpy',

        # used to read and write hdf5 files
        'h5py',

        # energy system model toolboxes
        'oemof.solph==0.4.4',  # pin for dissertation
        'pypsa==0.19.3',  # pin for dissertation
        'FINE==2.2.1',  # pin for dissertation
        'calliope==0.6.6.post1',  # pin for dissertation

        # used for time series aggregation in FINE to reduce optimization time
        'tsam',

        # auxilliary tools
        "dcttools",
        "strutils",
        "ittools",
    ],
    extras_require={
        'dev': [
            # used for building the documentation
            'colorspacious',
            'sphinx',
            'easydev',
            'openpyxl',
            'sphinx-paramlinks',
            'sphinx_rtd_theme',
        ],
    },
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "tessif = tessif.__main__:main",
        ],
    }
)
