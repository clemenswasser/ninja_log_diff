#!/usr/bin/env python3

import argparse
import pathlib
import sys
from typing import Tuple
from operator import itemgetter


def extract_duration_from_log_line(line: str) -> Tuple[str, str, int]:
    start, end, _, name, cmdhash = line.strip().split('\t')
    time_delta = int(end) - int(start)
    file = name
    return (cmdhash, file, time_delta)


def parse_log(log_file: pathlib.Path) -> dict[str, int]:
    log_file_lines = log_file.read_text().splitlines()
    if log_file_lines[0] != "# ninja log v5":
        print(
            f"ERROR: The file \"{log_file_lines}\" is not a valid ninja log file v5", file=sys.stderr)
        sys.exit(-1)

    target_candidates = dict()

    for line in log_file_lines[1:]:
        cmdhash, file, time_delta = extract_duration_from_log_line(line)
        target_candidates.setdefault(cmdhash, list()).append((file, time_delta))
    
    targets = dict()

    for target_candidate in target_candidates.values():
        target_candidate = sorted(target_candidate, reverse=True)[0]
        targets[target_candidate[0]] = target_candidate[1]
    return targets


def main():
    parser = argparse.ArgumentParser(
        prog='ninja_log_diff',
        description='Diff .ninja_log files to track build speed changes for projects using the Ninja buildsystem')
    parser.add_argument('file_before')
    parser.add_argument('file_after')
    args = parser.parse_args()
    file_before = pathlib.Path(args.file_before)
    if not file_before.exists():
        print(
            f"ERROR: file_before: \"{file_before}\" does not exist", file=sys.stderr)
        sys.exit(-1)
    file_after = pathlib.Path(args.file_after)
    if not file_after.exists():
        print(
            f"ERROR: file_after: \"{file_after}\" does not exist", file=sys.stderr)
        sys.exit(-1)

    before_durations = parse_log(file_before)
    after_durations = parse_log(file_after)
    different_files = set(before_durations.keys(
    )).symmetric_difference(after_durations.keys())
    if len(different_files) != 0:
        print(
            f"WARNING: There are {len(different_files)} file differences", file=sys.stderr)

    file_intersection = set(before_durations.keys()
                            ).intersection(after_durations.keys())
    file_differences = list(map(lambda file: (
        file, after_durations[file] - before_durations[file]), file_intersection))
    file_differences.sort(key=itemgetter(1))
    print("The biggest differences in compile speed are:")
    for file_difference in file_differences:
        print(f"  {file_difference[1]}ms {file_difference[0]}")


if __name__ == "__main__":
    main()
