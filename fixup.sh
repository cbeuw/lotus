#!/usr/bin/env bash

# Cargo has an option to strip absolute path prefixes in dep info .d files
# But this only takes in one path so you can only strip either the working directory
# or cargo registry, but not both
# See https://doc.rust-lang.org/cargo/reference/config.html#builddep-info-basedir
find target/release -name "*.d" -delete

# The root-output file contains the absolute path to OUT_DIR, and cannot be
# remapped
find target/release -name "root-output" -delete

