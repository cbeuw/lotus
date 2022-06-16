#!/usr/bin/env python3
from collections import defaultdict
import csv
from enum import Enum
import os
import shutil
import subprocess
import sys
from typing import Set, List


def get_top_crates(count: int, skip: Set[str] = set()) -> List[str]:
    csv.field_size_limit(sys.maxsize)
    print(f"Extracting crates.io DB dump...")
    with open("crates.csv", "r") as csvfile:
        crates = list(csv.DictReader(csvfile))

    # fields: downloads,name,repository
    print(f"Extracted crates.io dump with {len(crates)} crates")

    crates.sort(key=lambda r: int(r["downloads"]), reverse=True)

    not_in_skip = filter(
        lambda crate: crate["name"] not in skip and crate["repository"], crates
    )
    top = list(next(not_in_skip) for _ in range(count))
    return top


class ReproStatus(Enum):
    # Successful reproduction
    SUCCESS = 1
    # Differences found
    NON_REPRODUCTION = 2
    # Differences found but the package uses build script or proc macro
    NON_REPRODUCTION_WITH_THIRD_PARTY_BUILD_CODE = 3
    # Other build failures
    BUILD_FAILED = 4


def run_reprotest(name: str, repository: str, reprotest_args: List[str]) -> ReproStatus:
    with subprocess.Popen(
        ["git", "clone", "--depth", "1", repository, name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as git:
        for line in git.stdout:
            print(line, end="")

        if git.wait() != 0:
            return ReproStatus.BUILD_FAILED

    output = []
    with subprocess.Popen(
        ["reprotest", "-s", name, *reprotest_args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as reprotest:
        for line in reprotest.stdout:
            print(line, end="")
            output.append(line)

        if reprotest.wait() == 0:
            status = ReproStatus.SUCCESS
        elif any(line.lstrip().startswith("---") for line in output) and any(
            line.lstrip().startswith("+++") for line in output
        ):
            # we don't really have a better way to detect the failure was from diffoscope
            if any(line.startswith("MEAN-RUSTC-WARN") for line in output):
                status = ReproStatus.NON_REPRODUCTION_WITH_THIRD_PARTY_BUILD_CODE
            else:
                status = ReproStatus.NON_REPRODUCTION
        else:
            status = ReproStatus.BUILD_FAILED

    shutil.rmtree(name)
    return status


RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

if __name__ == "__main__":
    reprotest_args = sys.argv[1:]
    crates_count = int(os.environ.get("CRATES_COUNT")) or 10

    with open("skip-list.txt", "r") as f:
        skip = set(f)

    top = get_top_crates(crates_count, skip)
    print(f"Selecting top {crates_count} packages not in skip list")

    statuses = defaultdict(list)

    for crate in top:
        status = run_reprotest(crate["name"], crate["repository"], reprotest_args)
        statuses[status].append(crate["name"])
        if status == ReproStatus.SUCCESS:
            print(
                f"{GREEN}++++++++++ {crate['name']} REPRODUCTION SUCCESSFUL ++++++++++ {RESET}"
            )
        elif status == ReproStatus.NON_REPRODUCTION:
            print(
                f"{RED}!!!!!!!!!! {crate['name']} BUILD IS NOT REPRODUCIBLE !!!!!!!!!! {RESET}"
            )
        elif status == ReproStatus.NON_REPRODUCTION_WITH_THIRD_PARTY_BUILD_CODE:
            print(
                f"{YELLOW}########## {crate['name']} BUILD IS NOT REPRODUCIBLE but also runs third party code at compile time ########## {RESET}"
            )
        else:
            print(
                f"{MAGENTA}?????????? {crate['name']} BUILD FAILED ?????????? {RESET}"
            )

    indented_newline = "\n        "
    print("#" * 64)
    print(
        f"""
Out of {crates_count}
    {len(statuses[ReproStatus.SUCCESS])} are reproducible,
    {len(statuses[ReproStatus.NON_REPRODUCTION])} are not reproducible due to Cargo or Rust, these are:
        {indented_newline.join(statuses[ReproStatus.NON_REPRODUCTION])}
    {len(statuses[ReproStatus.NON_REPRODUCTION_WITH_THIRD_PARTY_BUILD_CODE])} are not reproducible but could be due to third-party proc macro or build scripts, these are:
        {indented_newline.join(statuses[ReproStatus.NON_REPRODUCTION_WITH_THIRD_PARTY_BUILD_CODE])}
    and,
    {len(statuses[ReproStatus.BUILD_FAILED])} cannot be built, these are:
        {indented_newline.join(statuses[ReproStatus.BUILD_FAILED])}
"""
    )

    sys.exit(0 if len(statuses[ReproStatus.NON_REPRODUCTION]) == 0 else 1)
