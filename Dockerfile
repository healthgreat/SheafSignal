FROM python:3.11-slim

WORKDIR /opt/sheafsignal
COPY . /opt/sheafsignal

RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

CMD ["sheafsignal", "run", "--expression", "examples/demo_expression.csv", "--metadata", "examples/demo_metadata.csv", "--lr-db", "examples/demo_ligand_receptor.csv", "--gene-set", "examples/demo_pathway_genes.txt", "--project-dir", "."]
