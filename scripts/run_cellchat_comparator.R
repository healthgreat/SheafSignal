#!/usr/bin/env Rscript
# Run CellChat comparator from SheafSignal processed expression/metadata.
#
# This script is intentionally sidecar-only: it writes CellChat outputs under
# benchmarks/results/<dataset>/comparators/cellchat_run/ and does not modify
# SheafSignal core results. Install CellChat in an isolated R environment before
# running this script.

args <- commandArgs(trailingOnly = TRUE)
dataset_id <- ifelse(length(args) >= 1, args[[1]], "gse154778_pdac_scrna")
processed_dir <- ifelse(length(args) >= 2, args[[2]], file.path("data", "processed", dataset_id))
output_dir <- ifelse(
  length(args) >= 3,
  args[[3]],
  file.path("benchmarks", "results", dataset_id, "comparators", "cellchat_run")
)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

metadata_path <- file.path(processed_dir, "metadata.csv")
expression_path <- file.path(processed_dir, "expression.csv")
metadata <- read.csv(metadata_path, check.names = FALSE)
expression <- read.csv(expression_path, check.names = FALSE)
rownames(expression) <- expression$cell_id
expression$cell_id <- NULL
expression <- t(as.matrix(expression))
metadata <- metadata[match(colnames(expression), metadata$cell_id), , drop = FALSE]
rownames(metadata) <- metadata$cell_id
if (!"samples" %in% colnames(metadata)) {
  metadata$samples <- if ("sample_id" %in% colnames(metadata)) metadata$sample_id else "sample1"
}

if (!requireNamespace("CellChat", quietly = TRUE)) {
  writeLines(
    c(
      "status\tmissing_dependency",
      "required_package\tCellChat",
      "action\tInstall CellChat in an isolated R environment, then rerun this script."
    ),
    file.path(output_dir, "cellchat_run_status.tsv")
  )
  quit(status = 0)
}

library(CellChat)
cellchat <- createCellChat(object = expression, meta = metadata, group.by = "cell_type")
cellchat@DB <- CellChatDB.human
cellchat <- subsetData(cellchat)
cellchat <- identifyOverExpressedGenes(cellchat, do.fast = FALSE)
cellchat <- identifyOverExpressedInteractions(cellchat)
cellchat <- computeCommunProb(cellchat)
cellchat <- filterCommunication(cellchat, min.cells = 10)
cellchat <- computeCommunProbPathway(cellchat)
cellchat <- aggregateNet(cellchat)

communication <- subsetCommunication(cellchat)
write.csv(communication, file.path(output_dir, "cellchat_communication.csv"), row.names = FALSE)
saveRDS(cellchat, file.path(output_dir, "cellchat_object.rds"))
writeLines(
  c("status\tcompleted", paste0("n_rows\t", nrow(communication))),
  file.path(output_dir, "cellchat_run_status.tsv")
)
