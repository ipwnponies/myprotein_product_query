.DEFAULT_GOAL := help

.PHONY: help
help: ## Print help
	@grep -E '^[^.]\w+( \w+)*:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: run
run: venv ## Run script with default setting
	venv/bin/python ./myprotein.py --whey --creatine --vouchers

.PHONY: test
test: venv ## Run tests
	venv/bin/pytest *_test.py
	venv/bin/pre-commit run
	venv/bin/mypy *.py

.PHONY: venv
venv: requirements.txt requirements-dev.txt ## Create virtualenv
	bin/venv-update \
		venv= -p python3 venv --quiet \
		install= -r requirements-dev.txt -r requirements.txt --quiet \
		bootstrap-deps= -r requirements-bootstrap.txt --quiet
	venv/bin/pre-commit install

.PHONY: clean
clean: ## Clean working directory
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./venv
