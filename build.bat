@echo off
REM Copyright 2014 Christoph Reiter
REM
REM This library is free software; you can redistribute it and/or
REM modify it under the terms of the GNU Lesser General Public
REM License as published by the Free Software Foundation; either
REM version 2.1 of the License, or (at your option) any later version.

python pgi-docgen.py -f _docs %* && python pgi-docgen-build.py _docs/_build _docs
