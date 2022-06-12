# lotus
<p align="center">
  予獨愛蓮之出淤泥而不染，濯清漣而不妖<sup><a href="https://zh.wikisource.org/wiki/%E6%84%9B%E8%93%AE%E8%AA%AA">[1]</a></sup>
  <br/>
  "Lotus were stemmed from mud yet unsullied, were rinsed with dew yet unassuming"
</p>

Rust build reproducibility testing.

This repo contains a daily workflow run which tests if the nightly Rust and Cargo toolchain is capable of reproducibly building popular packages
from crates.io. Packages and any of their dependencies requiring third-party code execution at build time (through build scripts or proc macros) are skipped,
unless the package is manually reviewed to be reproducible and exempted.

Environment variation and output checks are done using Debian's [reprotest](https://salsa.debian.org/reproducible-builds/reprotest) tool. A wide range
of variations are exercised, such as home directory, build path, locales, and timezones. A full list of variations can be found [here](https://salsa.debian.org/reproducible-builds/reprotest/-/blob/master/reprotest/build.py#L516-535).

## What are these files for?

### [`mean-rustc`](https://github.com/cbeuw/lotus/blob/master/mean-rustc)
Used as `RUSTC_WRAPPER` to detect if build scripts or proc macros are attempted to be built, and bail unless the package is manually allowed to do so.
This does not care if the package is root or a dependency; a package must be individually listed to be allowed.

Allowed build scripts:
  - [memchr](https://github.com/BurntSushi/memchr/blob/master/build.rs)

Allowed proc macros:
  - None

### [`cargo-build.sh`](https://github.com/cbeuw/lotus/blob/master/build.sh)
A helper script to setup environment variables and then run `cargo build --release`. This is needed primarily because toolchains are installed to the
local user by rustup, which cannot be found under reprotest's temporary build environments.

This script also sets path remapping flags to strip absolute paths in the outputs

### [`fixup.sh`](https://github.com/cbeuw/lotus/blob/master/fixup.sh)
Run after `cargo-build.sh` but before reprotest equality checks to remove files under `target` directory that are known to be non-reproducible. `target` contains
some files which don't really need to be reproducible, such as ones
containing the shell-expanded commmandline used to invoke cargo, but it's easier to remove these files and then ask reprotest to check everything under `target` than
trying to identify the files that matter.

### [`crates.csv`](https://github.com/cbeuw/lotus/blob/master/crates.csv)
An abridged version of `data/crates.csv` from [crates.io db dump](https://crates.io/data-access) containing only name, downloads, and repository columns, with subsequent
empty lines removed