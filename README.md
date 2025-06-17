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

    git clone [https://github.com/jdom1824/Bitcoin-TxTypes.git](https://github.com/jdom1824/Bitcoin-TxTypes)
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

This framework allows you to extract and classify UTXO outputs from the Bitcoin blockchain 
using either direct RPC access or by scanning blk*.dat files.

──────────────────────────────────────────────
🔁 OPTION 1: RPC Mode (Fastest and Most Accurate)
──────────────────────────────────────────────

Connects directly to a running Bitcoin Core node via RPC.

✅ Requirements:
- Fully synchronized Bitcoin Core node.
- Enabled RPC server in `bitcoin.conf`, e.g.:

    server=1
    rpcuser=user
    rpcpassword=password

🧪 Example:
    `bt-extract \
      --rpc \
      --rpc-url "http://user:password@127.0.0.1:8332" \
      --start-height 100000 \
      --end-height   100000 \
      --output utxos \
      --chunk-size 50000`

🧩 Option Details:

| Option           | Description                                                   |
|------------------|---------------------------------------------------------------|
| --rpc            | Enables RPC mode.                                             |
| --rpc-url        | Full RPC URL with user, password, host, and port.             |
| --start-height   | Starting block height (inclusive).                            |
| --end-height     | Ending block height (inclusive).                              |
| --output         | Output prefix for .parquet files.                             |
| --chunk-size     | Number of blocks per .parquet file (splits the output).       |


──────────────────────────────────────────────
📂 OPTION 2: Local blk*.dat Files (Manual Scanning)
──────────────────────────────────────────────

Reads directly from blk*.dat files (default Bitcoin storage format).

⚠️ Notes:
- Slower: must scan the full file structure to locate blocks by height.
- Useful if you have block files but no live node.

🧪 Example:
    `bt-extract \
      --blk-dir /path/to/bitcoin/blocks \
      --start-height 100000 \
      --end-height 100000 \
      --output utxos \
      --chunk-size 50000`

🧩 Option Details:

| Option           | Description                                                   |
|------------------|---------------------------------------------------------------|
| --blk-dir        | Path to local blk*.dat directory.                             |
| --start-height   | Starting block height (inclusive).                            |
| --end-height     | Ending block height (inclusive).                              |
| --output         | Output prefix for .parquet files.                             |
| --chunk-size     | Number of blocks per .parquet file. 

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

The script will produce `.parquet` files with columns:

- height: block height
- tx_id: transaction ID
- vout: output index
- value: value in satoshis
- type: output type (e.g., COINBASE, P2PKH, P2SH, NULLDATA, MULTISIG, UNKNOW, P2WPKH, P2WSH, etc.)

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

