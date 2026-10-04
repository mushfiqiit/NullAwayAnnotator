#!/usr/bin/env python3
#
# Copyright (c) 2024 University of California, Riverside.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""Removes the annotations NullAwayAnnotator injects to suppress NullAway errors it could not fix,
so NullAway reports every remaining error again:

  - @NullUnmarked (and its import), added on methods and classes (-sre)
  - "NullAway" and "NullAway.Init" values of @SuppressWarnings, added on fields. Other values are
    kept, e.g. @SuppressWarnings({ "unchecked", "NullAway" }) becomes @SuppressWarnings("unchecked").

Usage: ./remove-suppressions.py [--dry-run] [SRC_DIR]
SRC_DIR defaults to $JUNIT4_SRC, or to junit4's src/main/java used by the other scripts.
"""

import os
import re
import sys

DEFAULT_SRC = "/Users/mushfiqurrahmanchowdhury/Documents/junit4/src/main/java"
ENCODING = "ISO-8859-1"  # junit4's source encoding; maps every byte, so files round-trip unchanged

# @NullUnmarked, simple or fully qualified, with the spaces that follow it on the same line.
NULL_UNMARKED = re.compile(r"@(?:org\.jspecify\.annotations\.)?NullUnmarked\b(?![.\w])[ \t]*")
NULL_UNMARKED_IMPORT = re.compile(
    r"^[ \t]*import[ \t]+org\.jspecify\.annotations\.NullUnmarked[ \t]*;[ \t]*$")
# @SuppressWarnings("x") or @SuppressWarnings({"x", "y"}), optionally with "value =".
SUPPRESS_WARNINGS = re.compile(
    r"(@(?:java\.lang\.)?SuppressWarnings)\s*\(\s*(?:value\s*=\s*)?(\{[^}]*\}|\"[^\"]*\")\s*\)([ \t]*)")
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')


def is_nullaway_value(value):
    return value == "NullAway" or value.startswith("NullAway.")


class Counts:
    def __init__(self):
        self.null_unmarked = 0
        self.suppress_warnings = 0

    def total(self):
        return self.null_unmarked + self.suppress_warnings


def rewrite_suppress_warnings(match, counts):
    name, members, trailing = match.group(1), match.group(2), match.group(3)
    values = STRING.findall(members)
    kept = [v for v in values if not is_nullaway_value(v)]
    if len(kept) == len(values):
        return match.group(0)  # no NullAway value: leave it exactly as it is
    counts.suppress_warnings += len(values) - len(kept)
    if not kept:
        return ""
    if len(kept) == 1:
        return f'{name}("{kept[0]}"){trailing}'
    return name + "({" + ", ".join(f'"{v}"' for v in kept) + "})" + trailing


def strip_file(text, counts):
    out = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if NULL_UNMARKED_IMPORT.match(body):
            continue
        new_body, n = NULL_UNMARKED.subn("", body)
        counts.null_unmarked += n
        new_body = SUPPRESS_WARNINGS.sub(lambda m: rewrite_suppress_warnings(m, counts), new_body)
        if new_body != body and not new_body.strip():
            continue  # the line held only removed annotations: drop it
        out.append(new_body + ending if new_body != body else line)
    return "".join(out)


def main(argv):
    dry_run = "--dry-run" in argv
    args = [a for a in argv if a != "--dry-run"]
    src = args[0] if args else os.environ.get("JUNIT4_SRC", DEFAULT_SRC)
    if not os.path.isdir(src):
        sys.exit(f"Source directory not found: {src} (pass it as an argument or set JUNIT4_SRC)")

    total = Counts()
    files = 0
    print("@NullUnmarked  @SuppressWarnings(NullAway*)  file")
    for root, _, names in os.walk(src):
        for name in sorted(names):
            if not name.endswith(".java"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding=ENCODING, newline="") as f:
                text = f.read()
            counts = Counts()
            new_text = strip_file(text, counts)
            if new_text == text:
                continue
            files += 1
            total.null_unmarked += counts.null_unmarked
            total.suppress_warnings += counts.suppress_warnings
            print(f"{counts.null_unmarked:13d}  {counts.suppress_warnings:27d}  "
                  f"{os.path.relpath(path, src)}")
            if not dry_run:
                with open(path, "w", encoding=ENCODING, newline="") as f:
                    f.write(new_text)

    action = "Would remove" if dry_run else "Removed"
    print(f"{action} {total.null_unmarked} @NullUnmarked and {total.suppress_warnings} "
          f"NullAway @SuppressWarnings value(s) in {files} file(s) under {src}")


if __name__ == "__main__":
    main(sys.argv[1:])
