test:
	pytest . --cov=dataclass_serializer/ --cov-report=term-missing

lint:
	black --check
	mypy --ignore-missing-imports dataclass_serializer/ tests/

clean:
	rm -rf dist/

release:
	python setup.py bdist_wheel
	twine upload dist/*