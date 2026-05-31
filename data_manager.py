import csv
import os

DATA_FILE = "data.csv"


def ensure_csv_exists():
    if os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "#",
            "ia_name",
            "circuit_name",
            "time",
            "gen_number"
        ])

def get_next_id():
    ensure_csv_exists()

    with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    return len(rows)

def add_run_result(
        ia_name,
        circuit_name,
        time_s,
        generation,
):
    ensure_csv_exists()

    if time_s is None:
        return

    run_id = get_next_id()

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            run_id,
            ia_name,
            circuit_name,
            round(time_s, 2),
            generation
        ])

    print(
        f"[DATA] Added result #{run_id}: "
        f"{ia_name} | {circuit_name} | "
        f"{time_s:.2f}s | Gen {generation}"
    )