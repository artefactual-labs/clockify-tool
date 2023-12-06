#!/bin/bash
CURRENT_TAG=`git describe --abbrev=0`
CURRENT_VERSION="${CURRENT_TAG:1}"

echo "Current version: $CURRENT_VERSION"
echo

echo "Bump type [patch|minor|major, default: patch]?"
read BUMPTYPE

if [ -z "$BUMPTYPE" ]
then
  BUMPTYPE="patch"
fi

echo "Bump type: $BUMPTYPE"
echo

bumpversion --current-version $CURRENT_VERSION $BUMPTYPE --commit --tag --tag-message="Release {new_version}"  clockifytool/__init__.py setup.py

echo "Pushing commit..."
git push

echo "Pushing new tag..."
NEW_TAG=`git describe --abbrev=0`
git push origin $NEW_TAG

echo "Packaging..."
rm dist/*
python3 setup.py sdist bdist_wheel

echo "Publishing..."
twine upload dist/*
