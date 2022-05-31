#!/bin/bash

set -e

lc=$(wc -l < $1)
if [ $((lc % 2)) == 0 ]; then
   lc=$((lc + 1))
fi
lc=$((lc / 2))
cat $1 | split -l $lc - $2chunk_
