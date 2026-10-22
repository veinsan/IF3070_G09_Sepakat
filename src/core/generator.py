"""Generator instance persoalan acak (seeded) dalam format JSON yang dibaca `core.problem`.

Kendaraan diambil dari katalog tipe dengan ukuran tetap, sedangkan fee dan berat diacak dalam rentang
tiap tipe. Kapasitas kapal = `capacity_ratio` x berat yang dibutuhkan untuk mengisi penuh geladak
(luas geladak x rata-rata berat per sel). Dengan rasio < 1, geladak tidak bisa diisi penuh oleh sembarang
kendaraan, sehingga constraint berat ikut membatasi dan kendaraan ringan per sel menjadi menarik.

Bisa membuat satu kapal atau armada beberapa kapal (Bonus 3): `--width` dan `--length` menerima beberapa
nilai, pasangan ke-k adalah ukuran geladak kapal ke-k. Kapasitas tiap kapal dihitung dengan rumus di atas
berdasarkan luas geladaknya masing-masing.

Contoh (dari root repo):

    python src/core/generator.py --seed 1 --vehicles 30 --width 10 --length 20 --out dataset/main.json
    python src/core/generator.py --seed 1 --vehicles 40 --width 10 8 6 --length 12 10 8 --out dataset/multi.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Sequence
from pathlib import Path

VEHICLE_TYPES: dict[str, tuple[int, int, tuple[int, int], tuple[int, int]]] = {
    "motor": (1, 2, (5, 12), (1, 1)),
    "sedan": (2, 4, (30, 50), (4, 6)),
    "suv": (2, 5, (45, 70), (6, 8)),
    "pickup": (2, 6, (50, 80), (7, 10)),
    "truck": (3, 8, (90, 140), (15, 25)),
    "bus": (3, 10, (120, 180), (20, 30)),
}


def generate_instance(
    rng: random.Random,
    n_vehicles: int,
    decks: Sequence[tuple[int, int]],
    capacity_ratio: float = 0.8,
    types: list[str] | None = None,
    eta_range: tuple[int, int] = (1, 7),
) -> dict:
    """Buat dict instance dengan kapal berukuran `decks` (list `(width, length)`) dan `n_vehicles` kendaraan."""
    if not decks:
        raise ValueError("minimal satu kapal")
    types = types or list(VEHICLE_TYPES)
    unknown = set(types) - VEHICLE_TYPES.keys()
    if unknown:
        raise ValueError(f"tipe kendaraan tidak dikenal: {sorted(unknown)}")

    digits = len(str(n_vehicles))
    vehicles = []
    for i in range(1, n_vehicles + 1):
        vtype = rng.choice(types)
        width, length, fee_range, weight_range = VEHICLE_TYPES[vtype]
        vehicles.append(
            {
                "id": f"V{i:0{digits}d}",
                "type": vtype,
                "width": width,
                "length": length,
                "shipping_fee": rng.randint(*fee_range),
                "weight": rng.randint(*weight_range),
                "eta": rng.randint(*eta_range),
            }
        )

    weight_per_cell = sum(v["weight"] for v in vehicles) / sum(v["width"] * v["length"] for v in vehicles)
    ships = [
        {
            "id": f"Deck-{k}",
            "width": width,
            "length": length,
            "max_capacity": max(1, round(capacity_ratio * width * length * weight_per_cell)),
        }
        for k, (width, length) in enumerate(decks, start=1)
    ]
    return {"ships": ships, "vehicles": vehicles}


def summarize(instance: dict) -> str:
    """Ringkasan seberapa ketat instance: rasio luas dan berat terhadap total kapasitas armada."""
    ships = instance["ships"]
    vehicles = instance["vehicles"]
    area = sum(v["width"] * v["length"] for v in vehicles)
    weight = sum(v["weight"] for v in vehicles)
    deck_area = sum(s["width"] * s["length"] for s in ships)
    capacity = sum(s["max_capacity"] for s in ships)
    decks = ", ".join(f"{s['width']}x{s['length']} (C={s['max_capacity']})" for s in ships)
    return (
        f"{len(vehicles)} kendaraan, deck {decks} | "
        f"luas total {area}/{deck_area} ({area / deck_area:.2f}x) | "
        f"berat total {weight}/{capacity} ({weight / capacity:.2f}x) | "
        f"fee total {sum(v['shipping_fee'] for v in vehicles)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--vehicles", type=int, required=True, help="jumlah kendaraan")
    parser.add_argument("--width", type=int, nargs="+", required=True, help="lebar geladak tiap kapal (kolom)")
    parser.add_argument("--length", type=int, nargs="+", required=True, help="panjang geladak tiap kapal (baris)")
    parser.add_argument(
        "--capacity-ratio", type=float, default=0.8, help="kapasitas = rasio x berat untuk mengisi penuh geladak"
    )
    parser.add_argument("--types", nargs="+", choices=list(VEHICLE_TYPES), help="default: semua tipe")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if len(args.width) != len(args.length):
        parser.error("jumlah nilai --width dan --length harus sama (satu pasang per kapal)")

    decks = list(zip(args.width, args.length))
    instance = generate_instance(random.Random(args.seed), args.vehicles, decks, args.capacity_ratio, args.types)
    instance = {"meta": {"generator": "src/core/generator.py", **vars(args), "out": str(args.out)}, **instance}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(instance, indent=2) + "\n", encoding="utf-8")
    print(f"{args.out}: {summarize(instance)}")


if __name__ == "__main__":
    main()
