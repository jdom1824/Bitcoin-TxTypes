# extractor.py
# ───────────────────────────────────────────────────────────────────
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable, List, Optional

from tqdm import tqdm
from bitcoin.core import CBlock, CTransaction, b2lx

from .classifier import StandardClassifier


# ───────────────────────────────────────────────────────────────────
#  Utilidades de metadatos de transacción
# ───────────────────────────────────────────────────────────────────
def _analyze_tx_metadata(tx: CTransaction) -> dict:
    """
    Devuelve:
        - is_segwit   : bool
        - base_size   : bytes sin testigo
        - total_size  : bytes totales
        - weight      : weight units (= base*3 + total)
    """
    try:
        raw_total = tx.serialize()

        # ¿Tiene datos de testigo?
        is_segwit = hasattr(tx, "wit") and tx.wit and not tx.wit.is_null()

        # Base size = tamaño sin el campo witness
        try:
            tx_no_wit = tx.copy()
            tx_no_wit.wit = None
            raw_base = tx_no_wit.serialize()
            base_size = len(raw_base)
        except Exception:
            base_size = len(raw_total)  # Fallback

        total_size = len(raw_total)
        weight = base_size * 3 + total_size

        return {
            "is_segwit": is_segwit,
            "base_size": base_size,
            "total_size": total_size,
            "weight": weight,
        }

    except Exception:
        # Algo fue mal al serializar → devolvemos None
        return {
            "is_segwit": None,
            "base_size": None,
            "total_size": None,
            "weight": None,
        }


# ───────────────────────────────────────────────────────────────────
#  Deserialización de bloques en paralelo
# ───────────────────────────────────────────────────────────────────
def _deserialize_block(raw_block: bytes) -> List[str]:
    """Convierte un bloque bruto en lista de transacciones hex."""
    block = CBlock.deserialize(raw_block)
    return {
        "txs": [tx.serialize().hex() for tx in block.vtx],
        "time": block.nTime  # ← timestamp UNIX del bloque
    }

# ───────────────────────────────────────────────────────────────────
#  Función pública: extract(...)
# ───────────────────────────────────────────────────────────────────
def extract(
    source: Iterable[dict],
    classifier: StandardClassifier,
    *,
    processes: int = 4,
    start_height: Optional[int] = None,
    end_height:   Optional[int] = None,
):
    """
    Recorre un iterador de bloques y produce UTXOs clasificados.

    Cada elemento `blk` de `source` debe contener:
        - 'height' : int
        - 'raw'    : bytes  (bloque bruto)     O  'txs': list[str] (hex txs)

    Devuelve un generador de dicts con:
        height, tx_id, vout, value,
        vin_count, type,
        is_segwit, base_size, total_size, weight
    """
    pool: ProcessPoolExecutor | None = None
    if processes > 1:
        pool = ProcessPoolExecutor(max_workers=processes)

    futures = []
    bar = tqdm(total=0, desc="BLKS", unit="blk", dynamic_ncols=True)

    for blk in source:
        h = blk["height"]
        if start_height is not None and h < start_height:
            continue
        if end_height   is not None and h > end_height:
            continue

        if "txs" in blk:
            bar.update(1)
            yield from _yield_utxos(blk, classifier)
        else:
            # Deserializar en otro proceso
            fut = pool.submit(_deserialize_block, blk["raw"])
            futures.append((fut, blk))
            bar.total += 1
            bar.refresh()

    # Recolectar los resultados pendientes
    for fut, meta in futures:
        result = fut.result()
        meta["txs"]  = result["txs"]
        meta["time"] = result["time"]   # ← aquí guardamos timestamp
        bar.update(1)
        yield from _yield_utxos(meta, classifier)

    bar.close()
    if pool:
        pool.shutdown()


# ───────────────────────────────────────────────────────────────────
#  Produce UTXOs de un bloque (incluye vin_count)
# ───────────────────────────────────────────────────────────────────
def _yield_utxos(blk: dict, classifier: StandardClassifier):
    """
    Extrae todas las salidas (UTXOs) de un bloque y las clasifica.
    Añade:
        - vin_count : número de entradas de la transacción
        - time      : timestamp UNIX del bloque
    """
    height = blk["height"]
    blk_time = blk.get("time")   # ← timestamp ya disponible

    for tx_hex in blk["txs"]:
        tx  = CTransaction.deserialize(bytes.fromhex(tx_hex))
        txid = b2lx(tx.GetTxid())

        is_coinbase = (
            len(tx.vin) == 0
            or (
                tx.vin[0].prevout.hash == b"\x00" * 32
                and tx.vin[0].prevout.n == 0xFFFFFFFF
            )
        )

        tx_meta   = _analyze_tx_metadata(tx)
        vin_count = len(tx.vin)

        for idx, out in enumerate(tx.vout):
            yield {
                "height":   height,
                "time":     blk_time,      # ← lo incluimos aquí
                "tx_id":    txid,
                "vout":     idx,
                "value":    out.nValue,
                "vin_count": vin_count,
                "type":     classifier.classify(out.scriptPubKey.hex(),
                                               coinbase=is_coinbase),
                **tx_meta
            }
