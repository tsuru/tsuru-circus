clean:
	@find . -name "*.pyc" -delete

deps:
	@pip install -r test-requirements.txt

test: clean deps
	@python setup.py test
	@flake8 tsuru --max-line-length 110
