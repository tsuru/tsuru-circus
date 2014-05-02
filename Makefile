deps:
	@pip install -r test-requirements.txt

test:
	@python setup.py test
	@flake8 tsuru
