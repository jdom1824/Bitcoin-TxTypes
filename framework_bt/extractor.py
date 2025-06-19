from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable, List, Optional

from tqdm import tqdm
from bitcoin.core import CBlock, CTransaction, b2lx

from .classifier import StandardClassifier


def _analyze_tx_metadata(tx: CTransaction) -> dict:
    """
    Analyze a transaction to extract SegWit status, sizes and weight.
    Uses safe fallback in case base size cannot be calculated.
    """
    try:
        raw_total = tx.serialize()

        # Check if transaction has witness data
        is_segwit = hasattr(tx, "wit") and tx.wit and not tx.wit.is_null()

        # Try to estimate base size by clearing witness
        try:
            tx_no_wit = tx.copy()
            tx_no_wit.wit = None
            raw_base = tx_no_wit.serialize()
            base_size = len(raw_base)
        except Exception:
            base_size = len(raw_total)  # fallback

        total_size = len(raw_total)
        weight = base_size * 3 + total_size

        return {
            "is_segwit": is_segwit,
            "base_size": base_size,
            "total_size": total_size,
            "weight": weight,
        }

    except Exception:
        return {
            "is_segwit": None,
            "base_size": None,
            "total_size": None,
            "weight": None,
        }


def _deserialize_block(raw_block: bytes) -> List[str]:
    """Deserialize and convert to a list of transaction hex strings."""
    block = CBlock.deserialize(raw_block)
    return [tx.serialize().hex() for tx in block.vtx]


def extract(
    source: Iterable[dict],
    classifier: StandardClassifier,
    *,
    processes: int = 4,
    start_height: Optional[int] = None,
    end_height: Optional[int] = None,
):
    """
    Extract blocks from `source` and produce classified UTXOs.

    :param source: iterable of dicts with block data (must include 'raw' or 'txs')
    :param classifier: an instance of StandardClassifier to determine script type
    :param processes: number of processes to use in parallel for deserialization
    :param start_height: optional lower bound for block height
    :param end_height: optional upper bound for block height
    """
    pool = ProcessPoolExecutor(max_workers=processes)
    futures = []
    bar = tqdm(total=0, desc="BLKS", unit="blk", dynamic_ncols=True)

    for blk in source:
        if start_height is not None and blk["height"] < start_height:
            continue
        if end_height is not None and blk["height"] > end_height:
            continue

        if "txs" in blk:
            bar.update(1)
            yield from _yield_utxos(blk, classifier)
        else:
            fut = pool.submit(_deserialize_block, blk["raw"])
            futures.append((fut, blk))
            bar.total += 1
            bar.refresh()

    for fut, meta in futures:
        txs_hex = fut.result()
        meta["txs"] = txs_hex
        bar.update(1)
        yield from _yield_utxos(meta, classifier)

    bar.close()
    pool.shutdown()


def _yield_utxos(blk: dict, classifier: StandardClassifier):
    """
    Extract UTXOs from a block and classify their output types,
    including SegWit and weight metadata at transaction level.
    """
    height = blk["height"]

    for tx_hex in blk["txs"]:
        tx = CTransaction.deserialize(bytes.fromhex(tx_hex))
        txid = b2lx(tx.GetTxid())

        is_coinbase = (
            len(tx.vin) == 0
            or (
                tx.vin[0].prevout.hash == b"\\x00" * 32
                and tx.vin[0].prevout.n == 0xFFFFFFFF
            )
        )

        tx_meta = _analyze_tx_metadata(tx)

        for idx, out in enumerate(tx.vout):
            yield {
                "height": height,
                "tx_id": txid,
                "vout": idx,
                "value": out.nValue,
                "type": classifier.classify(out.scriptPubKey.hex(), coinbase=is_coinbase),
                **tx_meta
            }