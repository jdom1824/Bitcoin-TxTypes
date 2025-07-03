#!/bin/bash

# Configuración
START=0
END=870400
STEP=1000 # recommended for 16GB RAM
OUTDIR="utxos_blk"
BLKDIR="path/to/blocks"  # change this to your actual blocks directory
PROCESSES=10  # Número de procesos a usar

mkdir -p "$OUTDIR"

for (( HEIGHT=$START; HEIGHT<=$END; HEIGHT+=$STEP ))
do
    FROM=$HEIGHT
    TO=$(( HEIGHT + STEP - 1 ))
    if [ $TO -gt $END ]; then
        TO=$END
    fi

    echo "Processing blocks $FROM a $TO..."

    bt-extract \
      --blk-dir "$BLKDIR" \
      --start-height "$FROM" \
      --end-height "$TO" \
      --output "$OUTDIR/utxos_${FROM}_${TO}" \
      --processes "$PROCESSES"
done
