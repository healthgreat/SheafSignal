# Contributing to SheafSignal

## Development setup

```bash
cd /mnt/e/4实验数据/10新算法/SheafSignal
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## Pull request rules

- Add tests for new numerical behavior.
- Keep public APIs documented in `README.md` or `docs/`.
- Do not commit protected clinical data, raw sequencing files, private
  metadata, tokens, or credentials.
- Large public datasets should be referenced through `metadata/datasets.tsv`
  and downloaded by scripts rather than committed directly.

## Data privacy

Any human participant data must be de-identified and released only when allowed
by consent, IRB/ethics approval, institutional policy, and the original data
license. When in doubt, do not upload the data.
