# tests: flake8 pylint-fail-under unittests behave

flake8:
	poetry run flake8

pylint:
	find . -name "*.py" -not -path '*/\.*' -exec poetry run pylint --rcfile=.pylintrc '{}' +

pylint-fail-under:
	find . -name "*.py" -not -path '*/\.*' -exec poetry run pylint-fail-under --fail_under 9.5 --rcfile=.pylintrc '{}' +

behave:
	export NO_ASYNCPG=true && export PYTHONPATH=${PYTHONPATH}:./:./anon_api && poetry run behave tests/behave

behave-debug:
	poetry run behave tests/behave --logging-level=DEBUG --no-logcapture

unittests:
	PYTHONPATH=${PYTHONPATH}:./:./matching:./anon_api poetry run pytest --cov=./anon_api .

isort:
	poetry run isort ./**/*.py
