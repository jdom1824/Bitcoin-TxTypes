from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable, List

from tqdm import tqdm
from bitcoin.core import CBlock, CTransaction, b2lx

from .classifier import StandardClassifier


def _deserialize_block(raw_block: bytes) -> List[str]:
    """Deserializa y convierte a lista de transacciones hex."""
    block = CBlock.deserialize(raw_block)
    return [tx.serialize().hex() for tx in block.vtx]


def extract(
    source: Iterable[dict],
    classifier: StandardClassifier,
    *,
    processes: int = 4,
):
    """Extrae bloques desde `source` y produce UTXO clasificados."""
    pool = ProcessPoolExecutor(max_workers=processes)
    futures = []
    bar = tqdm(desc="BLKS", unit="blk", dynamic_ncols=True)

    for blk in source:
        if "txs" in blk:  # ← viene desde RpcSource
            bar.update(1)
            yield from _yield_utxos(blk, classifier)
        else:  # ← viene desde blkfile
            fut = pool.submit(_deserialize_block, blk["raw"])
            futures.append((fut, blk))
        if bar.total is not None:
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
    height = blk["height"]

    for tx_hex in blk["txs"]:
        tx = CTransaction.deserialize(bytes.fromhex(tx_hex))
        is_coinbase = (
            len(tx.vin) == 0
            or (
                tx.vin[0].prevout.hash == b"\x00" * 32
                and tx.vin[0].prevout.n == 0xFFFFFFFF
            )
        )
        txid = b2lx(tx.GetTxid())
        total_out = sum(o.nValue for o in tx.vout) or 1

        for idx, out in enumerate(tx.vout):
            yield {
                "height": height,
                "tx_id": txid,
                "vout": idx,
                "value": out.nValue,
                "type": classifier.classify(out.scriptPubKey.hex(), coinbase=is_coinbase),
            }
