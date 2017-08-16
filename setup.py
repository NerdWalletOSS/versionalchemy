from setuptools import setup


VERSION = '0.1.3'
DOWNLOAD_URL = 'https://github.com/NerdWalletOSS/versionalchemy/tarball/v{}'.format(VERSION)
with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='versionalchemy',
    version=VERSION,
    packages=['versionalchemy', 'versionalchemy/api', 'versionalchemy/models'],
    install_requires=[
        'SQLAlchemy>=1.0.0',
        'simplejson',
    ],
    include_package_data=True,
    author='Akshay Nanavati',
    author_email='akshay@nerdwallet.com',
    license='MIT License',
    description='Versioning library for relational data',
    url='https://github.com/NerdWalletOSS/versionalchemy',
    download_url=DOWNLOAD_URL,
    long_description=LONG_DESCRIPTION,
)
