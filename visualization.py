import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter

from autobidder import AutobiddingBudget


def save_gif(game, frames, path, title, fps=5):
    """Each frame contains a multiplier list and a caption."""
    colors = ["#2563eb", "#ea580c", "#16a34a", "#9333ea"]
    labels = [f"Advertiser {i + 1}" for i in range(game.n_players)]
    positions = list(range(game.n_players))
    payment_max = max(
        [1] + game.budgets + [
            row[1]
            for multipliers, _ in frames
            for row in game.bid_outcome(multipliers)[1]
        ]
    )
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.5))
    fig.subplots_adjust(top=0.77, bottom=0.20, hspace=0.55)
    fig.suptitle(title, fontsize=17, y=0.97)
    caption_text = fig.text(0.5, 0.88, "", ha="center", va="center", fontsize=11)
    allocation_text = fig.text(0.08, 0.09, "", fontsize=11)
    value_text = fig.text(0.08, 0.045, "", fontsize=11)
    writer = PillowWriter(fps=fps)

    try:
        with writer.saving(fig, str(path), dpi=100):
            for multipliers, caption in frames:
                outcomes, totals = game.bid_outcome(multipliers)
                for ax in axes:
                    ax.clear()
                    ax.set_xticks(positions, labels)
                    ax.set_xlim(-0.7, game.n_players - 0.3)
                    ax.spines[["top", "right"]].set_visible(False)

                axes[0].bar(positions, multipliers, color=colors[:game.n_players], width=0.55)
                axes[0].set_ylim(0, 1.15)
                axes[0].set_ylabel("Multiplier")
                for i, multiplier in enumerate(multipliers):
                    axes[0].text(i, multiplier + 0.04, f"{multiplier:.3f}", ha="center")

                payments = [row[1] for row in totals]
                payment_colors = [
                    "#dc2626" if payment > budget else colors[i]
                    for i, (payment, budget) in enumerate(zip(payments, game.budgets))
                ]
                axes[1].bar(positions, payments, color=payment_colors, width=0.55)
                axes[1].set_ylim(0, payment_max * 1.3)
                axes[1].set_ylabel("Actual payment")
                for i, (payment, budget) in enumerate(zip(payments, game.budgets)):
                    axes[1].hlines(budget, i - 0.3, i + 0.3, colors="black", linestyles="--")
                    axes[1].annotate(f"{payment:.2f}", (i, payment),
                                     xytext=(0, 4), textcoords="offset points", ha="center")
                    axes[1].text(i + 0.34, budget, f"Budget {budget:g}", va="center", fontsize=10)

                caption_text.set_text(caption)
                allocation_text.set_text("Allocation: " + "; ".join(
                    f"q{item + 1}: A{winner + 1}" for item, _, _, winner in outcomes
                ))
                value_text.set_text("Value won: " + "; ".join(
                    f"A{i + 1} = {row[0]:g}" for i, row in enumerate(totals)
                ))
                writer.grab_frame()

            # Hold the final result long enough to read it in a presentation.
            for _ in range(fps * 2):
                writer.grab_frame()
    finally:
        plt.close(fig)


def create_gifs(game, output_dir="output/gifs", sample_every=50):
    """Animate the existing grid search, then one unilateral deviation."""
    search_frames = []
    checked = 0

    def record_candidate(multipliers, is_equilibrium):
        nonlocal checked
        checked += 1
        if checked == 1 or checked % sample_every == 0 or is_equilibrium:
            _, totals = game.bid_outcome(multipliers)
            if is_equilibrium:
                status = "Equilibrium found: budgets hold; no profitable uniform deviation within [0, 1]"
            elif any(row[1] > game.budgets[i] for i, row in enumerate(totals)):
                status = "Rejected: a budget is exceeded"
            else:
                status = "Rejected: a feasible, profitable deviation exists"
            search_frames.append((multipliers.copy(), f"Candidate {checked:,}\n{status}"))

    equilibrium = next(game.find_equilibria(on_candidate=record_candidate), None)
    if equilibrium is None:
        raise ValueError("No equilibrium was found on the 0.01 grid.")

    _, baseline_totals = game.bid_outcome(equilibrium)
    # Choose a bidder who could win more value by increasing to the upper bound.
    bidder = min(range(game.n_players), key=lambda i: equilibrium[i])
    for i in range(game.n_players):
        trial = equilibrium.copy()
        trial[i] = 1.0
        _, totals = game.bid_outcome(trial)
        if totals[i][0] > baseline_totals[i][0]:
            bidder = i
            break

    deviation_frames = []
    fixed = "; ".join(
        f"A{i + 1} stays at {multiplier:.3f}"
        for i, multiplier in enumerate(equilibrium) if i != bidder
    )
    for step in range(31):
        # Always start from the same verified equilibrium; change only this bidder.
        trial = equilibrium.copy()
        trial[bidder] += (1.0 - equilibrium[bidder]) * step / 30
        _, totals = game.bid_outcome(trial)
        value, payment = totals[bidder]
        if step == 0:
            status = "Start at the verified equilibrium"
        elif value > baseline_totals[bidder][0]:
            if payment <= game.budgets[bidder]:
                raise AssertionError("The selected profile has a profitable deviation.")
            status = (f"More value, but payment {payment:.2f} > budget {game.budgets[bidder]:g}: "
                      "deviation is infeasible")
        else:
            status = "No increase in value won"
        deviation_frames.append((trial, f"A{bidder + 1} increases its multiplier; {fixed}\n{status}"))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    search_path = output_dir / "equilibrium-search.gif"
    deviation_path = output_dir / "equilibrium-deviation.gif"
    save_gif(game, search_frames, search_path, "1. Grid search for an equilibrium")
    save_gif(game, deviation_frames, deviation_path,
             "2. One advertiser tries to win more value")
    return equilibrium, checked, search_path, deviation_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create two auction GIFs using the paper's valuations.")
    parser.add_argument("--budgets", type=float, nargs=2, default=[20, 49])
    args = parser.parse_args()
    game = AutobiddingBudget(
        n_players=2, n_queries=4,
        valuations=[[2.1, 40, 30, 20], [1, 20, 25, 100]],
        budgets=args.budgets,
    )
    equilibrium, checked, search_path, deviation_path = create_gifs(game)
    print(f"Equilibrium: {equilibrium}; candidates checked: {checked:,}")
    print(f"Search GIF: {search_path}")
    print(f"Deviation GIF: {deviation_path}")
