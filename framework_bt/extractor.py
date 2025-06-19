from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable, List, Optional

from tqdm import tqdm
from bitcoin.core import CBlock, CTransaction, b2lx

from .classifier import StandardClassifier


def analyze_transaction(tx: CTransaction) -> dict:

    raw_total = tx.serialize()  # Incluye testigo
    raw_base = tx.serialize_without_witness()  # Excluye testigo

    total_size = len(raw_total)
    base_size = len(raw_base)
    is_segwit = base_size != total_size
    weight = base_size * 3 + total_size

    return {
        "txid": tx.GetTxid().hex(),
        "is_segwit": is_segwit,
        "base_size": base_size,
        "total_size": total_size,
        "weight": weight,
    }


def _deserialize_block(raw_block: bytes) -> List[dict]:
    block = CBlock.deserialize(raw_block)
    return [analyze_transaction(tx) for tx in block.vtx]


def extract(
    source: Iterable[dict],
    classifier: StandardClassifier,
    *,
    processes: int = 4,
    start_height: Optional[int] = None,
    end_height: Optional[int] = None,
) -> List[dict]:
    data = []
    with ProcessPoolExecutor(max_workers=processes) as executor:
        futures = []
        for block in source:
            if "raw" not in block:
                continue
            futures.append(executor.submit(_deserialize_block, block["raw"]))

        for f in tqdm(futures, desc="Processing blocks"):
            try:
                data.extend(f.result())
            except Exception as e:
                print("Error in block processing:", e)

    return data
