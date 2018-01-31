#!/usr/bin/env python

from distutils.core import setup

setup(
    name="turboactivate",
    version="4.0.1",
    description="Python bindings for TurboActivate",
    url="https://github.com/develersrl/python-turboactivate/",
    author="Develer S.r.L",
    author_email="info@develer.com",
    maintainer="Lorenzo Villani",
    maintainer_email="lvillani@develer.com",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=["turboactivate"],
    data_files=["README.rst"],
    long_description=open("README.rst").read())
