#!/bin/bash

# Configuración
START=0
END=870400
STEP=10000
OUTDIR="utxos_blk"
BLKDIR="/media/jdom-sas/node/Bitcoin/blocks"

mkdir -p "$OUTDIR"

for (( HEIGHT=$START; HEIGHT<=$END; HEIGHT+=$STEP ))
do
    FROM=$HEIGHT
    TO=$(( HEIGHT + STEP - 1 ))
    if [ $TO -gt $END ]; then
        TO=$END
    fi

    echo "Procesando bloques $FROM a $TO..."

    bt-extract \
      --blk-dir "$BLKDIR" \
      --start-height "$FROM" \
      --end-height "$TO" \
      --output "$OUTDIR/utxos_${FROM}_${TO}"

    # Puedes agregar una pausa si necesitas evitar saturación de I/O o CPU
    # sleep 1
done
