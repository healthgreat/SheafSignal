# Install CellChat comparator dependencies for SheafSignal.
#
# Author: SheafSignal contributors
# Date: 2026-05-01
# Method reference: CellChat v2 official GitHub repository
# https://github.com/jinworks/CellChat
# Purpose: reproduce the R sidecar environment used by
# scripts/run_cellchat_comparator.R.

options(repos = c(CRAN = "https://cloud.r-project.org"))

if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager")
}

BiocManager::install(
  c("BiocNeighbors"),
  ask = FALSE,
  update = FALSE
)

if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes")
}

remotes::install_github(
  "jinworks/CellChat",
  upgrade = "never",
  dependencies = TRUE
)
