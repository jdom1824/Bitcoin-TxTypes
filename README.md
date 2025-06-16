Framework-Bitcoin-TxTypes
==========================

Lightweight framework to extract and classify UTXO transaction output types from the Bitcoin blockchain, 
using either blk*.dat files or an RPC connection to a full node.

✔ Compatible with Python 3.10+
✔ No BlockSci dependency
✔ Supports writing to multiple .parquet output files
✔ Friendly CLI (`bt-extract`)
✔ Ideal for studying output types (P2PKH, P2SH, etc.)

------------------------------------------------------------
INSTALLATION
------------------------------------------------------------

1. Clone this repository:

    git clone https://github.com/your_user/Framework-Bitcoin-TxTypes.git
    cd Framework-Bitcoin-TxTypes

2. Create and activate a virtual environment (recommended):

    python3 -m venv venv
    source venv/bin/activate

3. Install the framework in editable mode:

    pip install -e .

------------------------------------------------------------
REQUIREMENTS
------------------------------------------------------------

- Bitcoin Core node (fully synced)
- Python >= 3.10
- Dependencies:

    pip install pyarrow pandas tqdm python-bitcoinlib python-bitcoinrpc click

------------------------------------------------------------
USAGE
------------------------------------------------------------

🔁 OPTION 1: RPC mode (fastest and most accurate)

    bt-extract \
      --rpc \
      --rpc-url "http://user:password@127.0.0.1:8332" \
      --start-height 100000 \
      --end-height   100000 \
      --output utxos \
      --chunk-size 50000

📂 OPTION 2: Local blk*.dat files (requires manual scanning)

    bt-extract \
      --blk-dir /path/to/bitcoin/blocks \
      --start-height 100000 \
      --end-height 100000 \
      --output utxos \
      --chunk-size 50000

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

The script will produce `.parquet` files with columns:

- height: block height
- tx_id: transaction ID
- vout: output index
- value: value in satoshis
- type: output type (e.g., COINBASE, P2PKH, P2SH, etc.)

Sample generated files:

    utxos_0001.parquet
    utxos_0002.parquet
    ...

To read with `pandas`:

    import pandas as pd
    df = pd.read_parquet("utxos_0001.parquet")
    print(df.head())

------------------------------------------------------------
TESTING
------------------------------------------------------------

To run the tests:

    python3 -m pytest -v

------------------------------------------------------------
LICENSE
------------------------------------------------------------

MIT. Free for academic and commercial use.

