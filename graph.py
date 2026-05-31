import argparse
import pandas as pd
import matplotlib.pyplot as plt


def show_bar_graph(df, x_column, y_column):
    plt.figure(figsize=(10, 6))

    plt.bar(df[x_column], df[y_column])

    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(f"{y_column} par {x_column}")

    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()


def run_graph_mode():
    parser = argparse.ArgumentParser()

    parser.add_argument("--graph", action="store_true")
    parser.add_argument("--bar", action="store_true")

    parser.add_argument(
        "--x",
        default="ia_name",
        help="Colonne utilisée pour l'axe X"
    )

    parser.add_argument(
        "--y",
        default="generation",
        help="Colonne utilisée pour l'axe Y"
    )

    args = parser.parse_args()

    df = pd.read_csv("data.csv")

    if args.bar:
        show_bar_graph(
            df,
            args.x,
            args.y,
        )