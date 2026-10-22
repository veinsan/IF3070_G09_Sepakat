"""Model data persoalan: kendaraan, kapal (geladak), dan instance persoalan.

Instance dibaca dari JSON dengan format:

    {
      "ships":    [{"id": "Deck-1", "width": 10, "length": 20, "max_capacity": 500}],
      "vehicles": [{"id": "V01", "width": 2, "length": 4, "shipping_fee": 60,
                    "weight": 5, "eta": 3}]
    }

Key lain (misalnya "meta" atau "type") diabaikan, sehingga instance dari pihak lain tetap bisa dibaca.
Semua pemeriksaan input dilakukan di sini. Modul lain boleh berasumsi `Problem` sudah valid.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Vehicle:
    """Kendaraan berukuran `width` x `length` grid (orientasi horizontal)."""

    id: str
    width: int
    length: int
    shipping_fee: float
    weight: float
    eta: int

    @property
    def area(self) -> int:
        return self.width * self.length


@dataclass(frozen=True, slots=True)
class Ship:
    """Geladak kapal: grid `width` kolom (sumbu x) x `length` baris (sumbu y)."""

    id: str
    width: int
    length: int
    max_capacity: float

    @property
    def area(self) -> int:
        return self.width * self.length


@dataclass(frozen=True, slots=True)
class Problem:
    """Satu instance persoalan. Urutan `vehicles` tetap dan menjadi index gene pada state."""

    ships: tuple[Ship, ...]
    vehicles: tuple[Vehicle, ...]
    name: str = ""


def load_problem(path: str | Path) -> Problem:
    """Baca dan validasi instance dari file JSON. Melempar `ValueError` bila tidak valid."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path}: JSON tidak valid ({e})") from e
    return parse_problem(data, name=path.stem)


def parse_problem(data: Any, name: str = "") -> Problem:
    """Validasi dict hasil `json.load` lalu ubah menjadi `Problem`."""
    if not isinstance(data, dict):
        raise ValueError("root JSON harus berupa object")
    ships = tuple(_parse_ship(s, f"ships[{i}]") for i, s in enumerate(_non_empty_list(data, "ships")))
    vehicles = tuple(
        _parse_vehicle(v, f"vehicles[{i}]") for i, v in enumerate(_non_empty_list(data, "vehicles"))
    )
    _check_unique_ids(ships, "ships")
    _check_unique_ids(vehicles, "vehicles")
    return Problem(ships=ships, vehicles=vehicles, name=name)


def _parse_ship(raw: Any, where: str) -> Ship:
    obj = _object(raw, where)
    return Ship(
        id=_id(obj, where),
        width=_int(obj, "width", where, minimum=1),
        length=_int(obj, "length", where, minimum=1),
        max_capacity=_positive_number(obj, "max_capacity", where),
    )


def _parse_vehicle(raw: Any, where: str) -> Vehicle:
    obj = _object(raw, where)
    fee = _number(obj, "shipping_fee", where)
    if fee < 0:
        raise ValueError(f"{where}.shipping_fee: tidak boleh negatif")
    return Vehicle(
        id=_id(obj, where),
        width=_int(obj, "width", where, minimum=1),
        length=_int(obj, "length", where, minimum=1),
        shipping_fee=fee,
        weight=_positive_number(obj, "weight", where),
        eta=_int(obj, "eta", where, minimum=0),
    )


def _non_empty_list(data: dict, key: str) -> list:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"'{key}' harus berupa list yang tidak kosong")
    return value


def _object(raw: Any, where: str) -> dict:
    if not isinstance(raw, dict):
        raise ValueError(f"{where}: harus berupa object")
    return raw


def _field(obj: dict, key: str, where: str) -> Any:
    if key not in obj:
        raise ValueError(f"{where}: field '{key}' wajib ada")
    return obj[key]


def _id(obj: dict, where: str) -> str:
    value = _field(obj, "id", where)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.id: harus string yang tidak kosong")
    return value


def _number(obj: dict, key: str, where: str) -> float:
    value = _field(obj, key, where)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}.{key}: harus berupa angka")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{where}.{key}: harus berupa angka finite")
    return value


def _positive_number(obj: dict, key: str, where: str) -> float:
    value = _number(obj, key, where)
    if value <= 0:
        raise ValueError(f"{where}.{key}: harus > 0")
    return value


def _int(obj: dict, key: str, where: str, minimum: int) -> int:
    value = _number(obj, key, where)
    if not isinstance(value, int) or value < minimum:
        raise ValueError(f"{where}.{key}: harus bilangan bulat >= {minimum}")
    return value


def _check_unique_ids(items: tuple[Ship, ...] | tuple[Vehicle, ...], key: str) -> None:
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            raise ValueError(f"{key}: id '{item.id}' duplikat")
        seen.add(item.id)
