import sys
import os
from tessif.frused.paths import root_dir, doc_dir

try:
    import nose
except ImportError:
    raise ImportError("Please install nosetest to use this script.")


def nose_tessif():
    """You can just execute this function to run the tessif nosetests and
    doctests. Nosetests has to be installed.
    """

    # add directories of restructured text files including doctests here
    doc_dirs = [
        os.path.join(doc_dir, 'source', 'usage'),
        os.path.join(doc_dir, 'source', 'usage', 'supported_models'),
        os.path.join(doc_dir, 'source', 'getting_started',
                     'examples', 'data', 'tsf'),
        os.path.join(doc_dir, 'source', 'getting_started',
                     'examples', 'data', 'tsf', 'cfg'),
        os.path.join(doc_dir, 'source', 'getting_started',
                     'examples', 'data', 'omf'),
        os.path.join(doc_dir, 'source', 'getting_started',
                     'examples', 'transformation'),
        os.path.join(doc_dir, 'source', 'getting_started',
                     'examples', 'transformation', 'auto_comparison'),
    ]

    test_dir = root_dir

    argv = sys.argv[:]
    argv.insert(1, "--with-doctest")
    argv.insert(1, "--logging-clear-handlers")
    argv.insert(1, "--doctest-extension=rst")
    argv.insert(1, "-vv")
    argv.insert(1, "--logging-level=WARNING")
    # argv.insert(1, "--nologcapture")
    # argv.insert(1, "--nocapture")
    # argv.insert(1, "--stop")

    argv.insert(1, test_dir)
    for d in doc_dirs:
        if os.path.isdir(d):
            argv.insert(1, d)
    nose.run(argv=argv)


if __name__ == "__main__":
    nose_tessif()
