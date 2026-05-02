# Publication strategy for SheafSignal

## Reality check

Publishing in journals with impact factor above 50 usually requires more than a
new computational score. The method must solve an important biological problem,
show clear advantage over accepted tools, and produce a discovery that changes
how readers interpret real tissue biology.

For SheafSignal, the publishable claim should not be:

> We apply sheaf theory and Hodge decomposition to cell-cell communication.

The stronger, submission-safe claim after Round2 hardening is:

> Cell-cell communication networks contain measurable inconsistency between
> ligand-receptor evidence and pathway-state structure; SheafSignal quantifies
> this computational mismatch as a graph-level readout that complements
> edge-level ligand-receptor methods.

## Target paper shape

Primary target: Nature Methods. The working claim is:

> SheafSignal maps sheaf-valued communication inconsistency in public tumor
> microenvironment benchmarks.

The publication track uses public TME datasets only, with Nature Biotechnology
as a secondary target if the software and benchmark resource become broad
enough.

### Core innovation

- Define cell-cell communication as a sheaf-valued flow over a biological graph.
- Quantify local inconsistency as `sheaf_energy`.
- Decompose net communication flow into `gradient`, `curl`, and `harmonic`
  components.
- Rank cell types by `frustration_score` as computational contributors to
  local communication mismatch, not as validated biological drivers.

### Evidence package required

✅ Mathematical validity:

- prove or derive the decomposition used by the algorithm
- show identifiability and edge cases
- define when curl/harmonic scores are meaningful

✅ Simulation:

- generate graphs with known gradient, curl, and harmonic signals
- test recovery under dropout, noise, missing LR pairs, batch effects, and cell
  annotation errors
- compare against simpler graph metrics

✅ Benchmark against existing tools:

- CellChat
- CellPhoneDB
- NicheNet
- LIANA
- niche-DE for differential niche association

The benchmark should show that SheafSignal answers a different question rather
than claiming all older tools are wrong.

Current implementation status:

- `LRProductBaseline` is complete as the internal LR-intensity baseline.
- Full LIANA imports are complete for GSE154778, GSE72056, and GSE176078.
- `MechanisticTargetPrior` is complete for those three scRNA-seq datasets.
- NicheNet/nichenetr-engine imports are complete for those three datasets using
  the project-curated TME ligand-target prior matrix.
- GitHub/Zenodo release manifests and SHA256 checksum files are generated under
  `release/`; the remaining reproducibility blocker is minting and inserting an
  actual Zenodo DOI.
- CellChat, CellPhoneDB, and niche-DE remain optional expansion comparators;
  do not write broad CCC-tool-superiority claims without either adding them or
  narrowing the claim to the completed tools.

✅ Real data:

- GSE72056 melanoma scRNA-seq
- GSE154778 PDAC scRNA-seq
- GSE176078 breast cancer scRNA-seq
- 10x Genomics human breast cancer Visium
- ideally one disease system with known multicellular feedback biology

✅ Biological validation:

- independent cohort replication
- literature-supported mechanism
- perturbation data if available
- experimental validation if the target journal requires a strong biological
  claim

## Minimum GitHub standard

The public repository should include:

- installable Python package
- CLI and documented API
- demo data that can run in CI
- data manifest with accession/DOI/checksum
- scripts to download all public data
- complete reproduction workflow
- environment file and Dockerfile
- tests and GitHub Actions
- license and citation metadata
- clear data privacy policy

## Data release standard

GitHub should contain code, small demo data, metadata, and scripts. Large public
datasets should be hosted in a stable external repository:

- GEO/SRA/ArrayExpress for raw omics data
- Zenodo/Figshare/OSF for processed benchmark matrices and frozen outputs
- institutional repository when required by data-use agreements

Do not upload protected clinical data to GitHub unless it is explicitly allowed
by consent, IRB/ethics approval, institutional rules, and data license.

## Decision gates

### Gate 1: Method correctness

Pass when:

- Hodge decomposition tests cover tree, triangle, and harmonic examples
- sheaf energy has clear behavior in controlled simulations
- outputs are stable under random seeds

### Gate 2: Biological usefulness

Pass when:

- at least one real dataset shows a high-frustration cell type that standard
  LR tools do not clearly identify
- the signal is replicated in an independent dataset
- the finding is interpretable from known biology or perturbation evidence

### Gate 3: Publication readiness

Pass when:

- all figures can be reproduced from one command
- all datasets have accession/DOI and checksums
- CI passes on a clean machine
- manuscript claims match the evidence
