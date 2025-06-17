# framework_bt/viewer.py
"""
bt-view  ─ visor rápido de archivos Parquet de bt-extract

Uso:
    bt-view                    # detecta utxos_*.parquet en cwd
    bt-view --prefix foo       # busca foo_*.parquet
    bt-view --head 20          # muestra las primeras 20 filas
"""

from pathlib import Path
import click
import pyarrow.parquet as pq
import pandas as pd

SATOSHI = 100_000_000  # para convertir a BTC


@click.command()
@click.option("--prefix", default="utxos", show_default=True,
              help="Prefijo de los archivos Parquet a listar")
@click.option("--head", default=10, show_default=True,
              help="Número de filas a imprimir")
def main(prefix: str, head: int):
    files = sorted(Path(".").glob(f"{prefix}_*.parquet"))
    if not files:
        click.echo(f"No se encontraron archivos {prefix}_*.parquet en el directorio.")
        return

    click.echo("Archivos encontrados:")
    for idx, f in enumerate(files, 1):
        size_mb = f.stat().st_size / 1_048_576
        click.echo(f"  [{idx}] {f.name:<30} {size_mb:6.1f} MB")

    choice = click.prompt("Seleccione un número", type=click.IntRange(1, len(files)))
    sel = files[choice - 1]

    click.echo(f"\nAbriendo {sel.name} …")
    table = pq.read_table(sel)
    df = table.to_pandas()

    # vista rápida
    click.echo(df.head(head).to_string(index=False))

    # ── resumen ─────────────────────────────────────────────
    total_rows   = len(df)
    total_value  = df["value"].sum() / SATOSHI        # → BTC
    size_mb      = sel.stat().st_size / 1_048_576

    click.echo("\nResumen:")
    click.echo(f"  ▸ filas totales         : {total_rows:,}")
    click.echo(f"  ▸ valor total           : {total_value:,.8f} BTC")
    click.echo(f"  ▸ tamaño archivo        : {size_mb:.1f} MB")

    # distribución por tipo
    click.echo("\n  Distribución por 'type':")
    dist = (
        df.groupby("type")
          .agg(count=("type", "size"), sats=("value", "sum"))
          .sort_values("count", ascending=False)
    )
    dist["btc"] = dist["sats"] / SATOSHI
    dist = dist.drop(columns="sats")
    click.echo(dist.to_string())

    click.echo("\nFin.")


if __name__ == "__main__":
    main()
