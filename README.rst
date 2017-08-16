VersionAlchemy
==============
A library built on top of the SQLAlchemy ORM for versioning 
row changes to relational SQL tables.

Authors: `Ryan Kirkman <https://www.github.com/ryankirkman/>`_ and
`Akshay Nanavati <https://www.github.com/akshaynanavati/>`_

Build Status
------------
.. image:: https://travis-ci.org/NerdWalletOSS/versionalchemy.svg?branch=master
    :target: https://travis-ci.org/NerdWalletOSS/versionalchemy
    
.. image:: https://readthedocs.org/projects/versionalchemy/badge/?version=latest
    :target: http://versionalchemy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Useful Links
------------
- `Developer Documentation <http://versionalchemy.readthedocs.io/en/latest/>`_
- `Blog Post <https://www.nerdwallet.com/blog/engineering/versionalchemy-tracking-row-changes/>`_
  with more in depth design decisions

Latency
-------
We used `benchmark.py <https://gist.github.com/akshaynanavati/f1e816596d100a33e4b4a9c48099a8b7>`_ to
benchmark the performance of versionalchemy. It times the performance of the SQLAlchemy core, ORM
without VersionAclehmy and ORM with VersionAlchemy for ``n`` inserts (where ``n`` was variable). Some
results are below.

+--------+-----------+----------+----------+
| n      | Core Time | ORM Time | VA Time  |
+========+===========+==========+==========+
| 10000  | 9.81 s    | 16.04 s  | 36.13    |
+--------+-----------+----------+----------+
| 100000 | 98.78 s   | 158.87 s | 350.84 s |
+--------+-----------+----------+----------+

VersionAlchemy performs roughly 2 times as bad as the ORM, which makes sense as we are doing roughly one
additional insert per orm insert into the archive table.

Getting Started
---------------

.. code-block:: bash

  $ pip install versionalchemy
  
Sample Usage
~~~~~~~~~~~~

.. code-block:: python
    
    import sqlalchemy as sa
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.schema import UniqueConstraint
    
    import versionalchemy as va
    from versionalchemy.models import VAModelMixin, VALogMixin

    MY_SQL_URL = '<insert mysql url here>'
    engine = create_engine(MY_SQL_URL)
    Base = declarative_base(bind=engine)

    class Example(Base, VAModelMixin):
        __tablename__ = 'example'
        va_version_columns = ['id']
        id = sa.Column(sa.Integer, primary_key=True)
        value = sa.Column(sa.String(128))


    class ExampleArchive(Base, VALogMixin):
        __tablename__ = 'example_archive'
        __table_args__ = (
            UniqueConstraint('id', 'va_version'),
        )
        id = sa.Column(sa.Integer)
        user_id = sa.Column(sa.Integer)
    
    va.init()  # Only call this once
    Example.register(ExampleArchive, engine)  # Call this once per engine, AFTER va.init
  
Contributing
------------
- Make sure you have `pip <https://pypi.python.org/pypi/pip>`_ 
  and `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ on your dev machine
- Fork the repository and make the desired changes
- Run ``make install`` to install all required dependencies
- Run ``make lint tests`` to ensure the code is pep8 compliant and  all tests pass.
  Note that the tests require 100% branch coverage to be considered passing
- Open a pull request with a detailed explaination of the bug or feature
- Respond to any comments. The PR will be merged if the travis CI build passes and 
  the code changes are deemed sufficient by the admin

Style
~~~~~
- Follow PEP8 with a line length of 100 characters
- Prefer parenthesis to ``\`` for line breaks

License
-------
`MIT License <https://github.com/NerdWalletOSS/versionalchemy/blob/master/LICENSE>`_
