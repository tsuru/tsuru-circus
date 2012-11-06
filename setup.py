from setuptools import setup, find_packages
from tsuru import __version__


setup(name="tsuru-circus",
    version=__version__,
    packages=find_packages(),
    description="Circus extensions for tsuru.",
    author="timeredbull",
    author_email="timeredbull@corp.globo.com",
    include_package_data=True,
    install_requires=["requests",],
    tests_require=["nose", "mock"],
    test_suite="nose.collector"
)
