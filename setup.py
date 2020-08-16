#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages


setup(
    name="dataclass_serializer",
    version="1.3.2",
    description="Dataclass serializer supports nested instances.",
    license="MIT",
    author="Sho Yoshida",
    author_email="nya060@gmail.com",
    url="https://github.com/yoshiso/dataclass_serializer.git",
    keywords="",
    packages=find_packages(exclude=("tests")),
    python_requires='>=3.7',
    install_requires=[],
    tests_require=["pytest", "pytest-cov", "pytz", "black", "numpy"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
