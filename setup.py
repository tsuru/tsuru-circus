# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from setuptools import setup, find_packages
from tsuru import __version__


setup(
    name="tsuru-circus",
    url="https://github.com/tsuru/tsuru-circus",
    version=__version__,
    packages=find_packages(),
    description="Circus extensions for tsuru.",
    author="timeredbull",
    author_email="timeredbull@corp.globo.com",
    include_package_data=True,
    install_requires=["circus>=0.11.1", "requests", "honcho==0.2.0", "PyYAML==3.10", "tsuru-unit-agent"],
    tests_require=["nose", "mock"],
    test_suite="nose.collector"
)
