#!/usr/bin/python
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from distutils.core import setup, Command


class TestCommand(Command):
    description = "run unit tests"
    user_options = [
        ("filter=", None, "regexp for filter classes"),
        ("exitfirst", "x", "exit instantly on first error or failed test"),
    ]

    def initialize_options(self):
        self.filter = ""
        self.exitfirst = False

    def finalize_options(self):
        self.filter = str(self.filter)
        self.exitfirst = bool(self.exitfirst)

    def run(self):
        from tests import do_test
        exit(do_test(self.filter, self.exitfirst) != 0)


setup(name='pgidocgen',
      version="0.0.1",
      description='Docs Generator for PGI/PyGObject',
      author='Christoph Reiter',
      author_email='reiter.christoph@gmail.com',
      url='https://github.com/lazka/pgi-docgen',
      scripts=['pgi-docgen.py', 'pgi-docgen-build.py'],
      packages=[
          'pgidocgen',
          'pgidocgen.gen',
      ],
      package_data={'pgidocgen': ['data/*', 'data/*/*', 'data/*/*/*']},
      license='LGPL-2.1+',
      cmdclass={
          'test': TestCommand,
      })
