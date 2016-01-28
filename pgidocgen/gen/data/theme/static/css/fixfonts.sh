#!/bin/bash

# We take the rtd theme css as is but have to remove/replace fonts.
# Everything else can be adjusted using our own pgi.css
sed -i 's/Roboto Slab/Lato/g' theme.css
sed -i 's/Consolas/Source Code Pro/g' theme.css
sed -i 's/@font-face{[^}]*}//g' theme.css
