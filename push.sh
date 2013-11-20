#!/bin/sh

# after ./default.sh, call this to force push the build to github pages

cd _docs/_build
rm -rf .?*
git init
git checkout -b gh-pages
touch  .nojekyll
git add .
git commit -m "update"
git remote add origin https://github.com/lazka/pgi-docs.git
git push --force
