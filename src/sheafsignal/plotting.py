from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def plot_communication_network(
    edges: pd.DataFrame,
    node_scores: pd.DataFrame,
    output_pdf: str | Path,
    max_edges: int = 80,
) -> Path:
    """Draw a compact directed network colored by curl magnitude."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    nodes = sorted(set(edges["sender"]).union(edges["receiver"]))
    n_nodes = len(nodes)
    if n_nodes == 0:
        raise ValueError("Cannot plot an empty graph.")

    angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
    pos = {node: np.array([np.cos(angle), np.sin(angle)]) for node, angle in zip(nodes, angles)}
    score_map = node_scores.set_index("cell_type")["frustration_score"].to_dict()

    edge_plot = edges.sort_values("sheaf_energy", ascending=False).head(max_edges).copy()
    curl_abs = np.abs(edge_plot.get("curl_component", 0.0).to_numpy(dtype=float))
    curl_max = float(curl_abs.max()) if curl_abs.size else 0.0
    flow_max = float(edge_plot["communication_flow"].max()) if not edge_plot.empty else 1.0
    if flow_max <= 0:
        flow_max = 1.0

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_aspect("equal")
    ax.axis("off")

    cmap = plt.cm.plasma
    for row in edge_plot.itertuples(index=False):
        start = pos[str(row.sender)]
        end = pos[str(row.receiver)]
        direction = end - start
        start2 = start + 0.12 * direction
        end2 = end - 0.12 * direction
        curl_value = abs(float(getattr(row, "curl_component", 0.0)))
        color = cmap(curl_value / curl_max) if curl_max > 0 else cmap(0.1)
        width = 0.5 + 3.0 * float(row.communication_flow) / flow_max
        arrow = FancyArrowPatch(
            start2,
            end2,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=width,
            color=color,
            alpha=0.65,
            connectionstyle="arc3,rad=0.12",
        )
        ax.add_patch(arrow)

    for node in nodes:
        xy = pos[node]
        score = float(score_map.get(node, 0.0))
        size = 700 + 2800 * score
        ax.scatter([xy[0]], [xy[1]], s=size, c="#F7F7F7", edgecolors="#222222", linewidths=1.2, zorder=3)
        ax.text(xy[0], xy[1], node, ha="center", va="center", fontsize=10, zorder=4)

    ax.set_title("SheafSignal communication curl network", fontsize=13)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max(curl_max, 1e-9)))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("|curl component|")
    fig.tight_layout()
    fig.savefig(output_pdf)
    plt.close(fig)
    return output_pdf
