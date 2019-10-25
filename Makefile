test:
	pytest . --cov=dataclass_serializer/ --cov-report=term-missing

lint:
	black --check
	mypy -p dataclass_serializer
