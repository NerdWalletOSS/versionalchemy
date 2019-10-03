NOSE_ARGS= -v \
	--cover-erase \
	--cover-branches \
	--with-coverage \
	--cover-package=api \
	--cover-package=models \
	--cover-package=versionalchemy
VENV_DIR=venv
VENV_BIN_DIR=$(VENV_DIR)/bin
VENV_PYTHON=$(VENV_BIN_DIR)/python
VENV_RUN=$(VENV_PYTHON) $(VENV_BIN_DIR)/
ISORT_ARGS=-rc -p versionalchemy -p tests .

default: clean install lint tests

# ---- Install ----
venv:
	# Create a local virtual environment in `venv/`
ifdef CI
	# Don't pin Python version in CI; instead, defer to Travis
	virtualenv --no-site-packages $(VENV_DIR)
else
	# Use Python 3.7 for local development
	virtualenv --no-site-packages --python=python3.7 $(VENV_DIR)
endif
install: venv
	# Install Python dev dependencies into local venv
	@$(VENV_RUN)pip install -r requirements.txt -e .[dev]
deps: install
	# Regenerate `requirements.txt` from `setup.py` using `pip-compile`
	@$(VENV_RUN)pip-compile --annotate --no-header --no-index --output-file requirements.txt
clean: clean-pyc
	@rm -fr $(VENV_DIR)
clean-pyc:
	@find ./ -name "*.pyc" -exec rm -rf {} \;

.PHONY: venv install deps clean clean-pyc

# --- Formatting ---
format: isort black autopep8
autopep8:
	@$(VENV_RUN)autopep8 --in-place --recursive --exclude=$(VENV_DIR) .
isort:
	@$(VENV_RUN)isort $(ISORT_ARGS)

.PHONY: format autopep8 isort

# ---- Tests ----
lint:
	# Check Python 2/3 compatibility
	@$(VENV_RUN)pylint --py3k .
	# Check Python style
	@$(VENV_RUN)flake8
	# Check import sorting
	@$(VENV_RUN)isort --check-only $(ISORT_ARGS)
tests:
	@cd versionalchemy; ../$(VENV_PYTHON) ../$(VENV_BIN_DIR)/nosetests $(NOSE_ARGS) tests 2>&1 | ../$(VENV_PYTHON) ../scripts/assert_full_coverage.py
assert-version-bump:
	@git fetch
	@git diff origin/master VERSION | grep "^+" || (echo "Bump VERSION!" && exit 1)

.PHONY: lint tests assert-version-bump

# ---- Executables ----
console:
	@$(VENV_RUN)ipython

.PHONY: console
