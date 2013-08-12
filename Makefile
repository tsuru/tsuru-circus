make deps:
	@pip install flake8

maek test: deps
	@python setup.py test
	@flake8 tsuru
