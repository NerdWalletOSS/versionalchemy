NOSE_ARGS= -v \
	--cover-erase \
	--cover-branches \
	--with-coverage \
	--cover-package=api \
	--cover-package=models \
	--cover-package=versionalchemy

default: clean install lint tests

# ---- Install ----
venv/bin/activate:
	@virtualenv venv
install: venv/bin/activate
	@test -d venv || virtualenv venv
	@. venv/bin/activate; pip install -r requirements.txt
clean: clean-pyc
	@rm -rf venv
clean-pyc:
	@ find ./versionalchemy -name "*.pyc" -exec rm -rf {} \;

# ---- Tests ----
lint:
	@. venv/bin/activate; flake8
tests:
	@. venv/bin/activate; cd versionalchemy; nosetests $(NOSE_ARGS) tests 2>&1 | python ../scripts/assert_full_coverage.py
assert-version-bump:
	@git fetch
	@git diff origin/master setup.py | grep "\+.*version=" || (echo "Bump version in setup.py!" && exit 1)

# ---- Executables ----
console:
	@. venv/bin/activate; ipython

.PHONY: install clean clean-pyc lint tests assert-version-bump console
