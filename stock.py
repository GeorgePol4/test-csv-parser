from pathlib import Path
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import csv

PATH_SOURCE = Path(__file__).parent
PATH_TRANS = PATH_SOURCE / 'invent_trans'
PATH_STOCK = PATH_SOURCE / 'stock'
CSV_SEPARATOR = ";"
CURRENT_STOCK_DATE = "2025-07-31"


def read_stock() -> dict:
    stock_files = list(PATH_STOCK.glob("*.csv"))

    if not stock_files:
        raise FileNotFoundError(
            f"В папке {PATH_STOCK} не найден файл начального остатка."
        )

    if len(stock_files) > 1:
        raise ValueError(
            f"В папке {PATH_STOCK} найдено больше одного файла остатков: "
            f"{[f.name for f in stock_files]}"
        )

    stock_file = stock_files[0]

    stock = defaultdict(lambda: {
        "qty": Decimal("0"),
        "cost_amount": Decimal("0"),
    })

    with stock_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=CSV_SEPARATOR)

        for row in reader:
            key = (
                row["item_id"],
                row["location_id"],
            )

            stock[key]["qty"] += Decimal(row["qty"])
            stock[key]["cost_amount"] += Decimal(row["cost_amount"])

    return stock


def read_transactions() -> dict:

    transactions = defaultdict(lambda: defaultdict(lambda: {
        "qty": Decimal("0"),
        "cost_amount": Decimal("0"),
    }))

    trans_files = sorted(
        PATH_TRANS.glob("*.csv")
    )

    if not trans_files:
        raise FileNotFoundError(
            f"В папке {PATH_TRANS} не найдены файлы движений."
        )

    for trans_file in trans_files:
        with trans_file.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter=CSV_SEPARATOR
            )

            for row in reader:
                trans_date = datetime.strptime(
                    row["trans_date"],
                    "%Y-%m-%d"
                )

                key = (
                    row["item_id"],
                    row["location_id"],
                )

                transactions[trans_date][key]["qty"] += Decimal(
                    row["qty"]
                )

                transactions[trans_date][key]["cost_amount"] += Decimal(
                    row["cost_amount"]
                )

    return transactions


def write_stock(stock: dict) -> None:

    output_file = PATH_STOCK / f"stock_{CURRENT_STOCK_DATE}.csv"

    with output_file.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.writer(
            file,
            delimiter=CSV_SEPARATOR
        )

        writer.writerow([
            "item_id",
            "location_id",
            "trans_date",
            "qty",
            "cost_amount",
        ])

        for (item_id, location_id), values in sorted(stock.items()):
            writer.writerow([
                item_id,
                location_id,
                CURRENT_STOCK_DATE,
                values["qty"],
                values["cost_amount"],
            ])


def main() -> None:
    stock = read_stock()
    transactions = read_transactions()

    # Применяем только движения ДО CURRENT_STOCK_DATE включительно.
    cutoff = datetime.strptime(CURRENT_STOCK_DATE, "%Y-%m-%d")

    for trans_date, movements in transactions.items():
        if trans_date > cutoff:
            continue

        for key, movement in movements.items():
            stock[key]["qty"] += movement["qty"]
            stock[key]["cost_amount"] += movement["cost_amount"]

    write_stock(stock)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Oops... Something wrong: {e}")
        raise
