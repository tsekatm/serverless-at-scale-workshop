"""Loads the (fictional) supplier master data that ships with every function."""
import json
from pathlib import Path

_DATA = json.loads((Path(__file__).parent / "suppliers.json").read_text())
SUPPLIERS = {s["supplier_id"]: s for s in _DATA["suppliers"]}


class UnknownSupplierError(Exception):
    pass


def get_supplier(supplier_id):
    try:
        return SUPPLIERS[supplier_id]
    except KeyError:
        raise UnknownSupplierError(f"Unknown supplier: {supplier_id}") from None
