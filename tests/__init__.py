# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest


def do_test(filter_, exitfirst):
    loader = unittest.TestLoader()
    current_dir = os.path.join(os.path.dirname(__file__))
    suite = loader.discover(os.path.join(current_dir))

    def flatten(x):
        l = []
        try:
            for s in x:
                l.extend(flatten(s))
        except TypeError:
            l.append(x)
        return l

    suites = [t for t in flatten(suite)]
    if filter_ is not None:
        suites = [t for t in suites if filter_ in type(t).__name__]

    run = unittest.TextTestRunner(
        verbosity=2, failfast=exitfirst).run(unittest.TestSuite(suites))
    return len(run.failures) + len(run.errors)
