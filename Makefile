make deps:
	@pip install -U -r test-requirements.txt

maek test: deps
	@python setup.py test
	@flake8 tsuru
