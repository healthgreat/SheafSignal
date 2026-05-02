.PHONY: install test demo manifest benchmark figures clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

demo:
	sheafsignal run \
		--expression examples/demo_expression.csv \
		--metadata examples/demo_metadata.csv \
		--lr-db examples/demo_ligand_receptor.csv \
		--gene-set examples/demo_pathway_genes.txt \
		--project-dir .

manifest:
	python scripts/download_public_datasets.py --validate-only
	python scripts/download_public_datasets.py --dry-run

benchmark:
	python scripts/prepare_public_datasets.py --include-demo
	python scripts/run_tme_benchmark.py --include-demo

figures:
	python scripts/make_publication_figures.py

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
