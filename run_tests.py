import sys
import nose

if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['--include=tests', '--verbose'])
    nose.main(argv=argv)
