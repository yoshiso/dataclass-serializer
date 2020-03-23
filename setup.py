#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages


setup(
    name="dataclass_serializer",
    version="1.1.0",
    description="Dataclass serializer supports nested instances.",
    license="MIT",
    author="Sho Yoshida",
    author_email="nya060@gmail.com",
    url="https://github.com/yoshiso/dataclass_serializer.git",
    keywords="",
    packages=find_packages(exclude=("tests")),
    install_requires=[],
    tests_require=["pytest", "pytest-cov", "pytz", "black", "numpy"],
)
