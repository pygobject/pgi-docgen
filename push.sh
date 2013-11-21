#!/bin/sh

# after ./default.sh, call this to force push the build to github pages

cd _docs/_build
rm -f README.rst
echo "This repository was created automatically using https://github.com/lazka/pgi-docgen\n" >> README.rst
echo "It contains a static website which can be viewed at http://lazka.github.io/pgi-docs/" >> README.rst
rm -rf .?*
git init
git checkout -b gh-pages
touch  .nojekyll
git add .
git commit -m "update"
git remote add origin https://github.com/lazka/pgi-docs.git
git push --force
