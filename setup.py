from __future__ import absolute_import

from setuptools import setup

install_requires = [
    "six>=1.12.0",
    "SQLAlchemy>=1.0",
]
dev_requires = [
    "autopep8>=1.4.4",
    "coverage",
    "flake8",
    "ipdb",
    "ipython",
    "isort>=4.3.21",
    'mock;python_version=="2.7"',
    "nose",
    "pip-tools",
    "pylint",
    "sphinx",
    "sphinx-rtd-theme<0.2",
]

with open("VERSION") as version_fd:
    version = version_fd.read().strip()
with open("README.rst") as f:
    long_description = f.read()
url = "https://github.com/NerdWalletOSS/versionalchemy"
download_url = "{}/tarball/v{}".format(url, version)
classifiers = """
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: SQL
Topic :: Database
Topic :: Database :: Front-Ends
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: OS Independent
"""

setup(
    name='versionalchemy',
    version=version,
    author='Akshay Nanavati',
    author_email='akshay@nerdwallet.com',
    maintainer="Jeremy Lewis",
    maintainer_email="jlewis@nerdwallet.com",
    url=url,
    description='Versioning library for relational data',
    long_description=long_description,
    download_url=download_url,
    classifiers=[c for c in classifiers.split("\n") if c],
    license='MIT License',
    packages=['versionalchemy', 'versionalchemy/api', 'versionalchemy/models'],
    install_requires=install_requires,
    extras_require={"dev": dev_requires},
    # Currently `versionalchemy` supports Python 2.7, and Python 3.6+
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",
    include_package_data=True,
)
