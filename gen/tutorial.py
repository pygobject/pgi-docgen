# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import shutil
import subprocess

from . import util


class TutorialGenerator(util.Generator):
    TUTORIAL_DIR = "tutorial"

    def __init__(self, dest):
        self._dest = dest

    def is_empty(self):
        return False

    def get_name(self):
        return "tutorial/index"

    def write(self):
        tutorial_dest = os.path.join(self._dest, self.TUTORIAL_DIR)
        shutil.copytree(self.TUTORIAL_DIR, tutorial_dest)

        examples_path = os.path.join(tutorial_dest, "examples")
        images_path = os.path.join(tutorial_dest, "images")
        os.mkdir(images_path)

        this_dir = os.path.dirname(os.path.realpath(__file__))
        script = os.path.join(this_dir, "make_screenshots.py")

        subprocess.check_call(["python", script, examples_path, images_path])
