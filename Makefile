.DEFAULT_GOAL := help

.PHONY: help
help: ## Print help
	@grep -E '^[^.]\w+( \w+)*:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: run
run: virtualenv_run ## Run script with default setting
	virtualenv_run/bin/python ./myprotein.py --whey --creatine --vouchers

.PHONY: test
test: virtualenv_run ## Run tests
	virtualenv_run/bin/pytest *_test.py
	virtualenv_run/bin/pre-commit run

virtualenv_run: requirements.txt requirements-dev.txt ## Create virtualenv
	bin/venv-update venv= -p python3.5 virtualenv_run install= -r requirements-dev.txt
	virtualenv_run/bin/pre-commit install

.PHONY: clean
clean: ## Clean working directory
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./virtualenv_run
