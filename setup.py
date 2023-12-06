from setuptools import setup

# Get requirements
with open("requirements/base.txt") as f:
    requirements = f.read().splitlines()

# Get text of the README file
with open("README.md") as f:
    README = f.read()


setup(
    name="clockifytool",
    packages=["clockifytool"],
    version="0.1.0",
    license="MIT",
    description="Tool to list, create, and delete time entries in Clockify",
    author="Mike Cantelon",
    author_email="mcantelon@gmail.com",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/artefactual-labs/clockify-tool",
    keywords=["clockify"],
    install_requires=requirements,
    scripts=["bin/cft"],
)
