from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd


EPS = 1e-12


def _canonical_pair(a: str, b: str) -> tuple[str, str]:
    if a == b:
        raise ValueError("Self-loops are not valid for pairwise Hodge decomposition.")
    return (a, b) if str(a) < str(b) else (b, a)


def build_pairwise_net_flow(
    edges: pd.DataFrame,
    flow_col: str = "flow_z",
) -> pd.DataFrame:
    """Collapse anti-parallel directed edges into canonical pairwise net flow."""
    flows: dict[tuple[str, str], float] = {}
    for row in edges.itertuples(index=False):
        sender = str(getattr(row, "sender"))
        receiver = str(getattr(row, "receiver"))
        if sender == receiver:
            continue
        pair = _canonical_pair(sender, receiver)
        sign = 1.0 if (sender, receiver) == pair else -1.0
        flows[pair] = flows.get(pair, 0.0) + sign * float(getattr(row, flow_col))

    rows = [
        {"tail": tail, "head": head, "pair_flow": flow}
        for (tail, head), flow in flows.items()
    ]
    return pd.DataFrame(rows)


def _incidence_matrix(nodes: list[str], pairs: pd.DataFrame) -> np.ndarray:
    node_index = {node: i for i, node in enumerate(nodes)}
    b = np.zeros((len(nodes), len(pairs)), dtype=float)
    for edge_idx, row in enumerate(pairs.itertuples(index=False)):
        b[node_index[str(row.tail)], edge_idx] = -1.0
        b[node_index[str(row.head)], edge_idx] = 1.0
    return b


def _triangle_boundary_matrix(nodes: list[str], pairs: pd.DataFrame) -> np.ndarray:
    edge_index = {
        (str(row.tail), str(row.head)): idx for idx, row in enumerate(pairs.itertuples(index=False))
    }
    rows = []
    for a, b, c in combinations(nodes, 3):
        ab = _canonical_pair(a, b)
        bc = _canonical_pair(b, c)
        ac = _canonical_pair(a, c)
        if ab not in edge_index or bc not in edge_index or ac not in edge_index:
            continue

        row = np.zeros(len(pairs), dtype=float)
        row[edge_index[ab]] = 1.0
        row[edge_index[bc]] = 1.0
        row[edge_index[ac]] = -1.0
        rows.append(row)

    if not rows:
        return np.zeros((0, len(pairs)), dtype=float)
    return np.vstack(rows)


def hodge_decomposition(
    edges: pd.DataFrame,
    flow_col: str = "flow_z",
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Decompose pairwise net communication flow into gradient/curl/harmonic."""
    pairs = build_pairwise_net_flow(edges, flow_col=flow_col)
    if pairs.empty:
        scores = {
            "gradient_ratio": 0.0,
            "curl_ratio": 0.0,
            "harmonic_ratio": 0.0,
            "total_flow_energy": 0.0,
            "n_pair_edges": 0,
            "n_triangles": 0,
        }
        return pairs, scores

    nodes = sorted(set(pairs["tail"]).union(pairs["head"]))
    f = pairs["pair_flow"].to_numpy(dtype=float)
    total_energy = float(np.dot(f, f))

    if total_energy < EPS:
        pairs = pairs.copy()
        pairs["gradient_component"] = 0.0
        pairs["curl_component"] = 0.0
        pairs["harmonic_component"] = 0.0
        scores = {
            "gradient_ratio": 0.0,
            "curl_ratio": 0.0,
            "harmonic_ratio": 0.0,
            "total_flow_energy": 0.0,
            "n_pair_edges": int(len(pairs)),
            "n_triangles": 0,
        }
        return pairs, scores

    b = _incidence_matrix(nodes, pairs)
    laplacian = b @ b.T
    phi = np.linalg.pinv(laplacian) @ (b @ f)
    gradient = b.T @ phi
    residual = f - gradient

    c = _triangle_boundary_matrix(nodes, pairs)
    if c.shape[0] > 0:
        curl = c.T @ (np.linalg.pinv(c @ c.T) @ (c @ residual))
    else:
        curl = np.zeros_like(f)
    harmonic = residual - curl

    pairs = pairs.copy()
    pairs["gradient_component"] = gradient
    pairs["curl_component"] = curl
    pairs["harmonic_component"] = harmonic

    scores = {
        "gradient_ratio": float(np.dot(gradient, gradient) / total_energy),
        "curl_ratio": float(np.dot(curl, curl) / total_energy),
        "harmonic_ratio": float(np.dot(harmonic, harmonic) / total_energy),
        "total_flow_energy": total_energy,
        "n_pair_edges": int(len(pairs)),
        "n_triangles": int(c.shape[0]),
    }
    return pairs, scores


def attach_hodge_components(edges: pd.DataFrame, pair_components: pd.DataFrame) -> pd.DataFrame:
    """Map canonical pair Hodge components back to directed edges."""
    if pair_components.empty:
        out = edges.copy()
        out["pair_tail"] = ""
        out["pair_head"] = ""
        out["pair_net_flow"] = 0.0
        out["gradient_component"] = 0.0
        out["curl_component"] = 0.0
        out["harmonic_component"] = 0.0
        return out

    comp_map = {
        (str(row.tail), str(row.head)): row
        for row in pair_components.itertuples(index=False)
    }

    rows = []
    for row in edges.to_dict(orient="records"):
        sender = str(row["sender"])
        receiver = str(row["receiver"])
        if sender == receiver:
            row["pair_tail"] = sender
            row["pair_head"] = receiver
            row["pair_net_flow"] = 0.0
            row["gradient_component"] = 0.0
            row["curl_component"] = 0.0
            row["harmonic_component"] = 0.0
            rows.append(row)
            continue

        pair = _canonical_pair(sender, receiver)
        sign = 1.0 if (sender, receiver) == pair else -1.0
        comp = comp_map.get(pair)
        if comp is None:
            row["pair_tail"] = pair[0]
            row["pair_head"] = pair[1]
            row["pair_net_flow"] = 0.0
            row["gradient_component"] = 0.0
            row["curl_component"] = 0.0
            row["harmonic_component"] = 0.0
            rows.append(row)
            continue

        row["pair_tail"] = pair[0]
        row["pair_head"] = pair[1]
        row["pair_net_flow"] = float(comp.pair_flow)
        row["gradient_component"] = sign * float(comp.gradient_component)
        row["curl_component"] = sign * float(comp.curl_component)
        row["harmonic_component"] = sign * float(comp.harmonic_component)
        rows.append(row)

    return pd.DataFrame(rows)
