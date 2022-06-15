# lotus
<p align="center">
  予獨愛蓮之出淤泥而不染，濯清漣而不妖<sup><a href="https://zh.wikisource.org/wiki/%E6%84%9B%E8%93%AE%E8%AA%AA">[1]</a></sup>
  <br/>
  "Lotus were stemmed from mud yet unsullied, were rinsed with dew yet unassuming"
</p>

Rust build reproducibility testing.

This repo contains a daily workflow run which tests if the nightly Rust and Cargo toolchain is capable of reproducibly building popular packages
from crates.io.

Only non-reproductions of packages that do not run any third-party code at build time (using proc macros or build scripts) are recorded
as a Rust or Cargo issue. Packages whose transitive dependencies contain proc macros or build scripts are still tested and recorded
as reproducible, if they are, although the onus is on them to ensure determinism in their build time code.

Environment variation and output checks are done using Debian's [reprotest](https://salsa.debian.org/reproducible-builds/reprotest) tool. A wide range
of variations are exercised, such as home directory, build path, locales, and timezones. A full list of variations can be found [here](https://salsa.debian.org/reproducible-builds/reprotest/-/blob/master/reprotest/build.py#L516-535).

## What are these files for?

### [`crates-reprotest.py`](https://github.com/cbeuw/lotus/blob/master/crates-reprotest.py)
The main entry point of the tests. Downloads top packages listed on crates.io and tests build reproducibility on them.
Exits with non-zero status if any package is non-reproducible due to a Rust or Cargo issue.

### [`mean-rustc`](https://github.com/cbeuw/lotus/blob/master/mean-rustc)
Used as `RUSTC_WRAPPER` to print a line starting with `MEAN-RUSTC-WARN` if build scripts or proc macros are being compiled.

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
An abridged version of `data/crates.csv` from [crates.io db dump](https://crates.io/data-access) containing only name, downloads, and repository columns.