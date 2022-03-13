
import sys


def fatal(*args, **kwargs):
    print("{}: \033[0;31mfatal\033[0m:".format(sys.argv[0]), *args,
          file=sys.stderr, **kwargs)

    sys.exit(1)


def info(*args, **kwargs):
    print("{}: \033[0;32minfo\033[0m:".format(sys.argv[0]), *args,
          file=sys.stderr, **kwargs)


def warn(*args, **kwargs):
    print("{}: \033[0;33mwarn\033[0m:".format(sys.argv[0]), *args,
          file=sys.stderr, **kwargs)

