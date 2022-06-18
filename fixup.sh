#!/usr/bin/env bash

# Cargo has an option to strip absolute path prefixes in dep info .d files
# But this only takes in one path so you can only strip either the working directory
# or cargo registry, but not both
# See https://doc.rust-lang.org/cargo/reference/config.html#builddep-info-basedir
find target -name "*.d" -delete

# The root-output file contains the absolute path to OUT_DIR, and cannot be remapped
find target -name "root-output" -delete

# Files under .fingerprint contains commandlines used to invoke rustc
# We cannot yet guarantee that this is deterministic since we need to pass in local
# paths to --remap-path-prefix
# This may be fixed once we do sanitisation by default
find target -wholename "*/.fingerprint/*" -delete
