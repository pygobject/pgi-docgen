#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import sys
import unittest
import argparse


def do_test(argv):
    parser = argparse.ArgumentParser(description='Run tests')
    parser.add_argument('-x', '--exitfirst', action='store_true',
                        help="exit instantly on first error or failed test")
    args = parser.parse_args(argv[1:])

    loader = unittest.TestLoader()
    current_dir = os.path.join(os.path.dirname(__file__))
    suites = loader.discover(os.path.join(current_dir, "tests"))

    run = unittest.TextTestRunner(
        verbosity=2, failfast=args.exitfirst).run(unittest.TestSuite(suites))
    return len(run.failures) + len(run.errors)


if __name__ == "__main__":
    exit(do_test(sys.argv) != 0)
