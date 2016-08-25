.. image:: https://travis-ci.org/NerdWallet/versionalchemy.svg?branch=master
    :target: https://travis-ci.org/NerdWallet/versionalchemy
VersionAlchemy
==============
A library built on top of the SQLAlchemy ORM for versioning 
row changes to relational SQL tables.

Authors: `Ryan Kirkman <https://www.github.com/ryankirkman/>`_ and
`Akshay Nanavati <https://www.github.com/akshaynanavati/>`_

Useful Links
------------
- `Developer Documentation <http:/TODO.com>`_
  - TODO fill in with public doc link
- `Blog Post <https://www.nerdwallet.com/blog/engineering/versionalchemy-tracking-row-changes/>`_
  with more in depth design decisions

Getting Started
---------------

  $ pip install versionalchemy
  
TODO - any examples?
  
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

License
-------
`MIT License <https://github.com/NerdWallet/versionalchemy/blob/master/LICENSE>`_
