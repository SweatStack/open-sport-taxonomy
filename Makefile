.PHONY: test build publish

test:
	PYTHONPATH=src uv run pytest tests/ -v

build:
	rm -rf dist
	uvx --from build pyproject-build --installer uv

publish: build
	uvx twine upload dist/*
