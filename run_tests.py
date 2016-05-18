import sys
import nose


if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['--include=tests', '--with-doctest', '--verbose'])
    nose.main(argv=argv)
