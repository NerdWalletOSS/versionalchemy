Changelog
=========

# 1.0.0

First major version release! Major changes:
* Added support for Python 3.6+:
  * Use `six` to write Python 2/3 compatible code
  * Dropped `simplejson` dependency in favor of std lib `json` module
  * Updated to build a universal wheel
  * Added tests against Python 3.6 and 3.7 in Travis CI
* Improved dev tooling:
  * Updated local venv to use Python 3.7
  * Added `make deps` for regenerating `requirements.txt`
  * Added `make format` for auto-formatting code
  * Updated `make lint` to check Python 2/3 compatibility, import sorting
* Improved packaging:
  * Moved dev requirements into `extras_require[dev]`
  * Added classifiers, maintainer, `python_requires`
  * Moved version into its own `VERSION` file
