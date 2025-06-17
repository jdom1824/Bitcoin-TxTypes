import pandas as pd

df = pd.read_parquet("utxos_0017.parquet")

print(df.to_string(index=False))  # Muestra todo
print(f"\nTotal UTXOs: {len(df)}")
print("\nTipos encontrados:\n", df["type"].value_counts())
