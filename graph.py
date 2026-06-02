import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


def show_bar_graph(df, x_column, y_column):
    plt.figure(figsize=(10, 6))

    bars = plt.bar(
        df[x_column],
        df[y_column],
        color="#CB1200"
    )

    for bar in bars:
        height = bar.get_height()

        plt.annotate(
            f"{height:}",
            (
                bar.get_x() + bar.get_width() / 2,
                height
            ),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center"
        )

    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(f"{y_column} per ai on the Monaco circuit")

    plt.grid(
        axis="y",
        linestyle="-",
        linewidth=0.5,
        alpha=0.4
    )

    plt.tight_layout()
    plt.show()

def show_line_graph(df, x_column, y_column):
    plt.figure(figsize=(10, 6))

    df = df.sort_values(by=x_column)

    plt.plot(
        df[x_column],
        df[y_column],
        marker="o",
        linewidth=2,
        color="#CB1200"
    )

    for x, y in zip(df[x_column], df[y_column]):
        plt.annotate(
            f"{y:.2f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center"
        )

    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(f"{y_column} evolution by {x_column}")

    #plt.ylabel("time (s)")
    #plt.title("time per turn - Monza Circuit")

    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(1))

    plt.grid(True)

    plt.tight_layout()
    plt.show()

def run_graph_mode():
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 18,
        "axes.labelsize": 18,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
    })

    parser = argparse.ArgumentParser()

    parser.add_argument("--graph", action="store_true")
    parser.add_argument("--bar", action="store_true")
    parser.add_argument("--line", action="store_true")

    parser.add_argument(
        "--x",
        default="ia_name",
        help="Column used for the X axis"
    )

    parser.add_argument(
        "--y",
        default="generation",
        help="Column used for the Y axis"
    )

    parser.add_argument(
        "--sort",
        default=None,
        help="Filter on the circuit/country"
    )

    args = parser.parse_args()

    df = pd.read_csv("data.csv")

    if args.sort:
        df = df[
            df["circuit_name"]
            .astype(str)
            .str.contains(args.sort, case=False, na=False)
        ]

    if args.bar:
        show_bar_graph(df, args.x, args.y)

    elif args.line:
        show_line_graph(df, args.x, args.y)