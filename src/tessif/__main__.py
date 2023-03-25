import argparse
import sys

from tessif import __version__
from tessif.frused.paths import root_dir, tests_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_install',
                        help="Run the tessif nosetests and doctests.",
                        action="store_true")
    args = parser.parse_args()

    # prints tessifs version and installation directory if no arg is given:
    if not len(sys.argv) > 1:
        print("tessif {} from {} (python {}.{})".format(
            __version__, root_dir, *sys.version_info,
        ))

    if args.test_install:
        sys.path.append(tests_dir)
        from nose_testing import nose_tessif

        sys.argv.remove("--test_install")
        # otherwise "--test_install" gets passed on to nose.
        nose_tessif()


if __name__ == '__main__':
    main()
