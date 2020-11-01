#!/usr/bin/env python
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from distutils.core import setup, Command


class TestCommand(Command):
    description = "run unit tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import pytest

        status = pytest.main(["tests"])
        if status != 0:
            raise SystemExit(status)


setup(name='pgi-docgen',
      version="0.0.1",
      description='Docs Generator for PGI/PyGObject',
      author='Christoph Reiter',
      author_email='reiter.christoph@gmail.com',
      url='https://github.com/pygobject/pgi-docgen',
      scripts=['pgi-docgen'],
      packages=[
          'pgidocgen',
          'pgidocgen.gen',
          'pgidocgen.update',
      ],
      package_data={'pgidocgen': ['data/*', 'data/*/*', 'data/*/*/*']},
      license='LGPL-2.1+',
      cmdclass={
          'test': TestCommand,
      })
