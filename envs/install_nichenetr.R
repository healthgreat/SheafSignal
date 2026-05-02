#!/usr/bin/env Rscript
# Author: SheafSignal contributors
# Date: 2026-04-30
# Purpose: install the R-side NicheNet comparator dependency in a reproducible
# D-/user-library friendly way. Run from the repository root.

options(repos = c(CRAN = "https://cloud.r-project.org"))

if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes")
}

if (!requireNamespace("jsonlite", quietly = TRUE)) {
  install.packages("jsonlite")
}

remotes::install_github(
  "saeyslab/nichenetr@2d5c1ab",
  upgrade = "never",
  dependencies = TRUE
)

message("nichenetr version: ", as.character(utils::packageVersion("nichenetr")))
