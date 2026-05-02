#!/usr/bin/env Rscript
# Author: SheafSignal contributors
# Date: 2026-04-30
# Method reference: nichenetr::predict_ligand_activities using a transparent
# project-curated TME ligand-target prior matrix.
# Purpose: run an auditable NicheNet-engine mechanistic comparator on
# SheafSignal cell-type profiles.

suppressPackageStartupMessages({
  library(nichenetr)
})

parse_args <- function(args) {
  out <- list()
  i <- 1
  while (i <= length(args)) {
    key <- args[[i]]
    if (!startsWith(key, "--")) {
      stop("Unexpected positional argument: ", key, call. = FALSE)
    }
    name <- sub("^--", "", key)
    if (i == length(args) || startsWith(args[[i + 1]], "--")) {
      out[[name]] <- TRUE
      i <- i + 1
    } else {
      out[[name]] <- args[[i + 1]]
      i <- i + 2
    }
  }
  out
}

arg_value <- function(args, name, default = NULL) {
  value <- args[[name]]
  if (is.null(value)) {
    return(default)
  }
  value
}

atomic_write_csv <- function(table, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp")
  write.csv(table, tmp, row.names = FALSE)
  if (file.exists(path)) {
    unlink(path)
  }
  file.rename(tmp, path)
}

atomic_write_json <- function(payload, path) {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("jsonlite is required for metadata output.", call. = FALSE)
  }
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp")
  writeLines(jsonlite::toJSON(payload, auto_unbox = TRUE, pretty = TRUE), tmp)
  if (file.exists(path)) {
    unlink(path)
  }
  file.rename(tmp, path)
}

load_profiles <- function(path) {
  if (!file.exists(path)) {
    stop("Missing profile table: ", path, call. = FALSE)
  }
  profiles <- read.csv(path, check.names = FALSE)
  cell_type_col <- if ("cell_type" %in% colnames(profiles)) {
    "cell_type"
  } else {
    colnames(profiles)[[1]]
  }
  rownames(profiles) <- as.character(profiles[[cell_type_col]])
  profiles[[cell_type_col]] <- NULL
  profiles[] <- lapply(profiles, function(x) as.numeric(as.character(x)))
  profiles[is.na(profiles)] <- 0
  as.matrix(profiles)
}

load_lr_db <- function(path) {
  lr_db <- read.csv(path, check.names = FALSE)
  required <- c("ligand", "receptor")
  missing <- setdiff(required, colnames(lr_db))
  if (length(missing) > 0) {
    stop("LR database missing columns: ", paste(missing, collapse = ","), call. = FALSE)
  }
  if (!"weight" %in% colnames(lr_db)) {
    lr_db$weight <- 1
  }
  lr_db$ligand <- as.character(lr_db$ligand)
  lr_db$receptor <- as.character(lr_db$receptor)
  lr_db$weight <- as.numeric(lr_db$weight)
  lr_db$weight[is.na(lr_db$weight)] <- 1
  lr_db
}

load_prior <- function(path) {
  prior <- read.csv(path, check.names = FALSE)
  required <- c("ligand", "target", "weight")
  missing <- setdiff(required, colnames(prior))
  if (length(missing) > 0) {
    stop("Ligand-target prior missing columns: ", paste(missing, collapse = ","), call. = FALSE)
  }
  prior$ligand <- as.character(prior$ligand)
  prior$target <- as.character(prior$target)
  prior$weight <- as.numeric(prior$weight)
  prior$weight[is.na(prior$weight)] <- 0
  prior
}

prior_to_matrix <- function(prior) {
  ligands <- sort(unique(prior$ligand))
  targets <- sort(unique(prior$target))
  mat <- matrix(0, nrow = length(targets), ncol = length(ligands))
  rownames(mat) <- targets
  colnames(mat) <- ligands
  for (i in seq_len(nrow(prior))) {
    mat[prior$target[[i]], prior$ligand[[i]]] <- max(
      mat[prior$target[[i]], prior$ligand[[i]]],
      prior$weight[[i]]
    )
  }
  mat
}

select_receiver_geneset <- function(receiver_profile, background_genes, min_geneset_size) {
  expr <- receiver_profile[background_genes]
  positive <- expr[expr > 0]
  if (length(positive) == 0) {
    return(character(0))
  }
  threshold <- as.numeric(stats::quantile(positive, probs = 0.75, names = FALSE))
  geneset <- names(expr)[expr >= threshold & expr > 0]
  if (length(geneset) < min_geneset_size) {
    ordered <- names(sort(expr, decreasing = TRUE))
    geneset <- ordered[seq_len(min(length(ordered), min_geneset_size))]
  }
  geneset
}

score_edges <- function(profiles, lr_db, prior_matrix, sheaf_edges, min_background_genes, min_geneset_size) {
  rows <- list()
  row_idx <- 1
  for (edge_i in seq_len(nrow(sheaf_edges))) {
    sender <- as.character(sheaf_edges$sender[[edge_i]])
    receiver <- as.character(sheaf_edges$receiver[[edge_i]])
    if (!sender %in% rownames(profiles) || !receiver %in% rownames(profiles)) {
      next
    }
    sender_profile <- profiles[sender, ]
    receiver_profile <- profiles[receiver, ]
    background_genes <- intersect(rownames(prior_matrix), names(receiver_profile)[receiver_profile > 0])
    if (length(background_genes) < min_background_genes) {
      background_genes <- intersect(rownames(prior_matrix), colnames(profiles))
    }
    if (length(background_genes) < min_background_genes) {
      next
    }
    geneset <- select_receiver_geneset(receiver_profile, background_genes, min_geneset_size)
    if (length(geneset) < 2) {
      next
    }

    candidate_lr <- lr_db[
      lr_db$ligand %in% colnames(prior_matrix) &
        lr_db$ligand %in% names(sender_profile) &
        lr_db$receptor %in% names(receiver_profile) &
        sender_profile[lr_db$ligand] > 0 &
        receiver_profile[lr_db$receptor] > 0,
      ,
      drop = FALSE
    ]
    potential_ligands <- unique(candidate_lr$ligand)
    if (length(potential_ligands) == 0) {
      next
    }

    activities <- tryCatch(
      {
        nichenetr::predict_ligand_activities(
          geneset = geneset,
          background_expressed_genes = background_genes,
          ligand_target_matrix = prior_matrix,
          potential_ligands = potential_ligands
        )
      },
      error = function(e) {
        NULL
      }
    )
    if (is.null(activities) || nrow(activities) == 0) {
      next
    }
    activities <- as.data.frame(activities)
    for (lr_i in seq_len(nrow(candidate_lr))) {
      ligand <- candidate_lr$ligand[[lr_i]]
      receptor <- candidate_lr$receptor[[lr_i]]
      activity <- activities[activities$test_ligand == ligand, , drop = FALSE]
      if (nrow(activity) == 0) {
        next
      }
      pearson <- as.numeric(activity$pearson[[1]])
      aupr_corrected <- as.numeric(activity$aupr_corrected[[1]])
      activity_score <- max(0, pearson, aupr_corrected, na.rm = TRUE)
      ligand_expr <- as.numeric(sender_profile[[ligand]])
      receptor_expr <- as.numeric(receiver_profile[[receptor]])
      lr_weight <- as.numeric(candidate_lr$weight[[lr_i]])
      score <- activity_score * ligand_expr * receptor_expr * lr_weight
      if (!is.finite(score) || score <= 0) {
        next
      }
      rows[[row_idx]] <- data.frame(
        sender = sender,
        receiver = receiver,
        ligand = ligand,
        receptor = receptor,
        score = score,
        nichenet_activity_score = activity_score,
        nichenet_pearson = pearson,
        nichenet_aupr = as.numeric(activity$aupr[[1]]),
        nichenet_aupr_corrected = aupr_corrected,
        nichenet_auroc = as.numeric(activity$auroc[[1]]),
        sender_ligand_expression = ligand_expr,
        receiver_receptor_expression = receptor_expr,
        lr_weight = lr_weight,
        n_background_genes = length(background_genes),
        n_geneset = length(geneset),
        geneset = paste(geneset, collapse = ";"),
        notes = "nichenetr::predict_ligand_activities with project-curated TME prior matrix",
        stringsAsFactors = FALSE
      )
      row_idx <- row_idx + 1
    }
  }
  if (length(rows) == 0) {
    stop("No positive NicheNet-prior edge scores were produced.", call. = FALSE)
  }
  out <- do.call(rbind, rows)
  out[order(-out$score, out$sender, out$receiver, out$ligand, out$receptor), ]
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  dataset_id <- arg_value(args, "dataset-id")
  if (is.null(dataset_id)) {
    stop("--dataset-id is required.", call. = FALSE)
  }
  processed_dir <- arg_value(args, "processed-dir", file.path("data", "processed", dataset_id))
  benchmark_dir <- arg_value(args, "benchmark-dir", file.path("benchmarks", "results", dataset_id))
  lr_db_path <- arg_value(args, "lr-db", file.path("metadata", "tme_ligand_receptor.csv"))
  prior_path <- arg_value(args, "ligand-target-prior", file.path("metadata", "tme_ligand_target_prior.csv"))
  output_dir <- arg_value(
    args,
    "output-dir",
    file.path(benchmark_dir, "comparators", "nichenet_prior_run")
  )
  min_background_genes <- as.integer(arg_value(args, "min-background-genes", "5"))
  min_geneset_size <- as.integer(arg_value(args, "min-geneset-size", "2"))

  profiles <- load_profiles(file.path(processed_dir, "profiles.csv"))
  lr_db <- load_lr_db(lr_db_path)
  prior <- load_prior(prior_path)
  prior_matrix <- prior_to_matrix(prior)
  sheaf_path <- file.path(benchmark_dir, "results", "sheaf_energy_by_edge.csv")
  if (!file.exists(sheaf_path)) {
    stop("Missing SheafSignal edge table: ", sheaf_path, call. = FALSE)
  }
  sheaf_edges <- read.csv(sheaf_path, check.names = FALSE)
  raw <- score_edges(
    profiles = profiles,
    lr_db = lr_db,
    prior_matrix = prior_matrix,
    sheaf_edges = sheaf_edges,
    min_background_genes = min_background_genes,
    min_geneset_size = min_geneset_size
  )

  raw_path <- file.path(output_dir, "nichenet_prior_raw_edges.csv")
  metadata_path <- file.path(output_dir, "nichenet_prior_metadata.json")
  atomic_write_csv(raw, raw_path)
  atomic_write_json(
    list(
      dataset_id = dataset_id,
      tool = "NicheNet",
      nichenetr_version = as.character(utils::packageVersion("nichenetr")),
      processed_dir = processed_dir,
      lr_db_path = lr_db_path,
      ligand_target_prior_path = prior_path,
      min_background_genes = min_background_genes,
      min_geneset_size = min_geneset_size,
      n_profiles = nrow(profiles),
      n_profile_genes = ncol(profiles),
      n_lr_pairs = nrow(lr_db),
      n_prior_rows = nrow(prior),
      n_raw_scored_rows = nrow(raw),
      claim_boundary = paste(
        "Official nichenetr scoring engine with project-curated TME prior matrix;",
        "not the full pretrained NicheNet model."
      )
    ),
    metadata_path
  )
  cat("wrote", normalizePath(raw_path, winslash = "\\", mustWork = FALSE), "\n")
  cat("wrote", normalizePath(metadata_path, winslash = "\\", mustWork = FALSE), "\n")
}

main()
