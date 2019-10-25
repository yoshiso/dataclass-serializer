test:
	pytest . --cov=dataclass_serializer/ --cov-report=term-missing

lint:
	black --check
	mypy -p dataclass_serializer

clean:
	rm -rf dist/

release:
	python setup.py bdist_wheel
	twine upload dist/*