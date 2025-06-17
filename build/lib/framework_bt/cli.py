"""
cli.py
======
Interfaz de línea de comandos del framework.
Instalado como `bt-extract` mediante pyproject.toml.
Soporta extracción por RPC o por archivos blk*.dat y escritura en chunks.
"""

import os
import math
import click
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .rpcsource import RpcSource
from .blkfile import BlkFileSource
from .classifier import StandardClassifier
from .extractor import extract


@click.command()
@click.option("--blk-dir", type=click.Path(exists=True, file_okay=False), help="Directorio con archivos blk*.dat")
@click.option("--rpc", is_flag=True, help="Usar conexión RPC en lugar de archivos blk*.dat")
@click.option("--rpc-url", type=str, help="URL RPC completa, ej: http://user:pass@127.0.0.1:8332")
@click.option("--start-height", type=int, required=True, help="Altura inicial (inclusive)")
@click.option("--end-height", type=int, required=True, help="Altura final (inclusive)")
@click.option("--output", type=str, default="utxos", show_default=True, help="Prefijo de archivos Parquet")
@click.option("--chunk-size", type=int, default=100_000, show_default=True, help="UTXOs por archivo Parquet")
@click.option("--processes", type=int, default=4, show_default=True, help="Número de procesos paralelos")
def main(blk_dir, rpc, rpc_url, start_height, end_height, output, chunk_size, processes):
    """Extrae UTXO clasificados y los guarda en archivos Parquet por partes."""
    # Fuente de bloques
    if rpc:
        if not rpc_url:
            raise click.UsageError("Debe proporcionar --rpc-url si usa --rpc.")
        source = RpcSource(rpc_url, start_height=start_height, end_height=end_height)
    elif blk_dir:
        source = BlkFileSource(blk_dir, start_height=start_height, end_height=end_height)
    else:
        raise click.UsageError("Debe proporcionar --blk-dir o usar --rpc.")

    # Clasificador
    classifier = StandardClassifier()
    buffer = []
    chunk_idx = 1
    total_utxos = 0

    # Extracción
    for utxo in extract(source, classifier, processes=processes):
        buffer.append(utxo)
        if len(buffer) >= chunk_size:
            _write_chunk(buffer, output, chunk_idx)
            total_utxos += len(buffer)
            buffer.clear()
            chunk_idx += 1

    # Último fragmento
    if buffer:
        _write_chunk(buffer, output, chunk_idx)
        total_utxos += len(buffer)

    click.echo(f"[✓] {total_utxos} UTXO guardados en {chunk_idx} archivo(s) .parquet")


def _write_chunk(buffer, output_prefix, idx):
    df = pd.DataFrame(buffer)
    table = pa.Table.from_pandas(df)
    fname = f"{output_prefix}_{idx:04d}.parquet"
    pq.write_table(table, fname)
    click.echo(f"[→] {len(buffer)} UTXO → {fname}")


if __name__ == "__main__":
    main()
