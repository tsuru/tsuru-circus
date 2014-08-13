deps:
	@pip install -r test-requirements.txt

test: deps
	@python setup.py test
	@flake8 tsuru
