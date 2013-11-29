#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest


def do_test():
    loader = unittest.TestLoader()
    current_dir = os.path.join(os.path.dirname(__file__))
    suites = loader.discover(os.path.join(current_dir, "tests"))

    run = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))
    return len(run.failures) + len(run.errors)


if __name__ == "__main__":
    exit(do_test() != 0)
