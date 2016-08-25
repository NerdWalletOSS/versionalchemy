from setuptools import setup


VERSION = '0.1.0'
INSTALL_REQUIRES = [
    'SQLAlchemy>=1.0.0',
    'simplejson',
]

setup(
    name='versionalchemy',
    version=VERSION,
    packages=['versionalchemy', 'versionalchemy/api', 'versionalchemy/models'],
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
    author='Akshay Nanavati',
    author_email='akshay@nerdwallet.com',
    license='MIT License',
    description='Versioning library for relational data',
    long_description='',
    url='https://github.com/NerdWallet/versionalchemy',
    download_url='https://github.com/NerdWallet/versionalchemy/tarball/{}'.format(VERSION),
)
