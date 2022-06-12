#!/usr/bin/env bash

# Usage: export RUSTUP_HOME=$(rustup show home); export RUSTC=$(command -v rustc); export CARGO=$(command -v cargo); export CARGO_HOME=$HOME/.cargo; build.sh

[[ -z "$RUSTUP_HOME" ]] && { echo "RUSTUP_HOME must be explicilty set"; exit 1; }
[[ -z "$CARGO" ]] && { echo "CARGO must be explicilty set to the absolute path to the cargo binary"; exit 1; }
[[ -z "$RUSTC" ]] && { echo "RUSTC must be explicilty set to the absolute path to the rustc binary"; exit 1; }

if [[ -z "$CARGO_HOME" ]]; then
  echo "Warning: CARGO_HOME is not explicitly set, this will work but Cargo will attempt to download the crate index on each build"
  CARGO_HOME=$HOME/.cargo
fi

# Forbid the building and execution of build scripts and proc macros
export RUSTC_WRAPPER=/root/mean-rustc

# So that we don't need to worry about anything under incremental directory. Speeds up builds too
export CARGO_INCREMENTAL=0

export RUSTFLAGS="-Z remap-cwd-prefix=. --remap-path-prefix $CARGO_HOME=cargo_home"
$CARGO build --release

