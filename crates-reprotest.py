#!/usr/bin/env python3
from collections import defaultdict
import csv
from enum import Enum
import io
import subprocess
import sys
import tarfile
from typing import Set, List
import urllib.request

TOP_CRATES_COUNT = 20
CRATES_IO_DUMP_URL = "https://static.crates.io/db-dump.tar.gz"


def get_top_crates(skip: Set[str] = set()) -> List[str]:
    csv.field_size_limit(sys.maxsize)
    print(f"Downloading and extracting crates.io DB dump...")
    # with open("db-dump.tar.gz", "rb") as response:
    with urllib.request.urlopen(CRATES_IO_DUMP_URL) as response:
        archive = tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:gz")
        crates_info = next(
            filter(
                lambda info: info.name.endswith("data/crates.csv"), archive.getmembers()
            )
        )
        if not crates_info:
            raise RuntimeError("cannot find data/crates.csv")
        crates_file = io.TextIOWrapper(archive.extractfile(crates_info))
        crates = list(csv.DictReader(crates_file))

    # fields: created_at,description,documentation,downloads,homepage,id,max_upload_size,name,readme,repository,updated_at
    print(f"Extracted crates.io dump with {len(crates)} crates")

    crates.sort(key=lambda r: int(r["downloads"]), reverse=True)

    not_in_skip = filter(lambda crate: crate["name"] not in skip, crates)
    top = list(next(not_in_skip) for _ in range(TOP_CRATES_COUNT))
    return top


class ReproStatus(Enum):
    SUCCESS = 1  # Successful reproduction
    NON_REPRODUCTION = 2  # Differences found
    FORBIDDEN = 3  # Hit a build script or proc macro
    BUILD_FAILED = 4  # Other build failures


def run_reprotest(name: str, repository: str, reprotest_args: List[str]) -> ReproStatus:
    with subprocess.Popen(
        ["git", "clone", "--depth", "1", repository, name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as git:
        for line in git.stdout:
            print(line)

        if git.wait() != 0:
            return ReproStatus.BUILD_FAILED

    with subprocess.Popen(
        ["reprotest", "-s", name, *reprotest_args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as reprotest:
        for line in reprotest.stdout:
            print(line)

        if reprotest.wait() == 0:
            return ReproStatus.SUCCESS
        elif "MEAN-RUSTC-FORBID" in reprotest.stdout:
            return ReproStatus.FORBIDDEN
        elif "---" in reprotest.stdout and "+++" in reprotest.stdout:
            # we don't really have a better way to detect the failure was from diffoscope
            return ReproStatus.NON_REPRODUCTION
        else:
            return ReproStatus.BUILD_FAILED


RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

if __name__ == "__main__":
    reprotest_args = sys.argv[1:]

    with open("skip-list.txt", "r") as f:
        skip = set(f)

    top = get_top_crates(skip)
    print(f"Selecting top {TOP_CRATES_COUNT} packages not in skip list")

    statuses = defaultdict(list)

    for crate in top:
        status = run_reprotest(crate["name"], crate["repository"], reprotest_args)
        statuses[status].append(crate["name"])
        if status == ReproStatus.SUCCESS:
            print(
                f"{GREEN}++++++++++ {crate['name']} REPRODUCTION SUCCESSFUL++++++++++ {RESET}"
            )
        elif status == ReproStatus.NON_REPRODUCTION:
            print(
                f"{RED}!!!!!!!!!! {crate['name']} BUILD IS NOT REPRODUCIBLE!!!!!!!!!! {RESET}"
            )
        elif status == ReproStatus.FORBIDDEN:
            print(
                f"{YELLOW}########## {crate['name']} RUNS THIRD-PARTY CODE AT COMPILE TIME########## {RESET}"
            )
        else:
            print(f"{MAGENTA}?????????? {crate['name']} BUILD FAILED?????????? {RESET}")

    print("#" * 64)
    print(f"Out of {TOP_CRATES_COUNT} packages:")
    print(f"\t{len(statuses[ReproStatus.SUCCESS])} are reproducible,")
    print(f"\t{len(statuses[ReproStatus.NON_REPRODUCTION])} are not reproducible,")
    print(f"\t{len(statuses[ReproStatus.BUILD_FAILED])} cannot be built, these are:")
    print("\t\t" + "\n".join(statuses[ReproStatus.BUILD_FAILED]))
    print(f"\tand,")
    print(
        f"\t{len(statuses[ReproStatus.FORBIDDEN])} runs forbidden third-party code at compile time, these are:"
    )
    print("\t\t" + "\n".join(statuses[ReproStatus.FORBIDDEN]))

    sys.exit(len(statuses[ReproStatus.NON_REPRODUCTION]) == 0)
