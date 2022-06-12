#!/usr/bin/env bash

# Usage: export RUSTUP_HOME=$(rustup show home); export RUSTC=$(command -v rustc); export CARGO=$(command -v cargo); export RUSTC_WRAPPER=[absolute path to mean-rustc]; export CARGO_HOME=$HOME/.cargo; build.sh

[[ -z "$RUSTUP_HOME" ]] && { echo "RUSTUP_HOME must be explicilty set"; exit 1; }
[[ -z "$CARGO" ]] && { echo "CARGO must be explicilty set to the absolute path to the cargo binary"; exit 1; }
[[ -z "$RUSTC" ]] && { echo "RUSTC must be explicilty set to the absolute path to the rustc binary"; exit 1; }
[[ -z "$RUSTC_WRAPPER" ]] && { echo "RUSTC_WRAPPER must be explicilty set to the absolute path to mean-rustc"; exit 1; }

if [[ "$CARGO_HOME" ]]; then
  HOST_CARGO_HOME=$CARGO_HOME
else
  echo "Warning: CARGO_HOME is not explicitly set, this will work but Cargo will attempt to download the crate index on each build"
fi

# This $HOME is varied by reprotest
export CARGO_HOME=$HOME/.cargo

# We try to copy the cargo index from the host environment to prevent Cargo from downloading it
# in the new environment
if [[ "$HOST_CARGO_HOME" ]] && [ -d "$HOST_CARGO_HOME/registry/index" ]; then
  mkdir -p "$CARGO_HOME/registry"
  cp -r "$HOST_CARGO_HOME/registry/index" "$CARGO_HOME/registry"
fi

# We don't want to worry about anything under incremental directory. Speeds up builds too
export CARGO_INCREMENTAL=0

export RUSTFLAGS="-Z remap-cwd-prefix=. --remap-path-prefix $CARGO_HOME=cargo_home"
$CARGO build --release

