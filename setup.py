#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iSymPred (Insect Symbiont Predictor) - Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="i_sym_pred",
    version="0.1.0",
    author="iSymPred Development Team",
    description="Insect Symbiont Predictor - Predict symbiont functions from 16S or metagenomic data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/iSymPred",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pandas>=1.3.0",
        "biopython>=1.79",
        "numpy>=1.21.0",
    ],
    entry_points={
        "console_scripts": [
            "isympred=i_sym_pred.cli:main",
        ],
    },
)
