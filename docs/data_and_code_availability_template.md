# Data and code availability template

Use this as a starting point for the manuscript.

## Code availability

The SheafSignal source code, command-line interface, tests, documentation, and
reproduction scripts are available at:

```text
https://github.com/TBD/SheafSignal
```

The archived release used for the manuscript is available at:

```text
https://doi.org/TBD
```

## Data availability

All public datasets used in this study are listed in
`metadata/datasets.tsv`, including accession numbers, download URLs, licenses
or terms, local file paths, and SHA256 checksums where applicable.

Large processed benchmark objects are deposited at:

```text
Zenodo/Figshare/GEO/SRA DOI or accession: TBD
```

No protected human participant data are distributed through GitHub. Any human
data used in controlled-access analyses must follow the corresponding data-use
agreement and IRB/ethics approval.

## Reproducibility

The main analyses can be reproduced with:

```bash
git clone https://github.com/TBD/SheafSignal.git
cd SheafSignal
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/download_public_datasets.py --validate-only
python scripts/download_public_datasets.py --dry-run
python scripts/prepare_public_datasets.py --include-demo
python scripts/run_tme_benchmark.py --include-demo
python scripts/make_publication_figures.py
snakemake -s workflow/Snakefile --cores 4
```

Permutation-tested demo:

```bash
sheafsignal run \
  --expression examples/demo_expression.csv \
  --metadata examples/demo_metadata.csv \
  --lr-db examples/demo_ligand_receptor.csv \
  --gene-set examples/demo_pathway_genes.txt \
  --project-dir . \
  --n-permutations 1000 \
  --random-seed 1
```

For multi-sample analyses:

```bash
sheafsignal run \
  --expression expression.csv \
  --metadata metadata.csv \
  --lr-db ligand_receptor.csv \
  --gene-set pathway_genes.txt \
  --project-dir . \
  --n-permutations 1000 \
  --permutation-strata-col sample_id \
  --random-seed 1
```

First public PDAC benchmark:

```bash
python scripts/download_public_datasets.py --dataset-id gse154778_pdac_scrna
python scripts/prepare_public_datasets.py \
  --dataset-id gse154778_pdac_scrna \
  --profile-only \
  --force \
  --marker-margin 0
python scripts/run_tme_benchmark.py
python scripts/qc_gse154778_annotation.py
```
