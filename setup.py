from setuptools import setup


install_requires = [
    'SQLAlchemy>=1.0.0',
    'simplejson',
]

setup(
    name='versionalchemy',
    version='0.1.0',
    packages=['versionalchemy', 'versionalchemy/api', 'versionalchemy/models'],
    install_requires=install_requires,
    include_package_data=True,
    author='Akshay Nanavati',
    author_email='akshay@nerdwallet.com',
    license='MIT License',
    description='Versioning library for relational data',
    long_description='',
    url='https://github.com/NerdWallet/versionalchemy',
)
