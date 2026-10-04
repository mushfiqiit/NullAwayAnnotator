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

"""Removes the @NullUnmarked annotations that NullAwayAnnotator injects (-sre) to suppress the
errors it could not fix, so NullAway reports those errors again.

Usage: ./remove-nullunmarked.py [--dry-run] [SRC_DIR]
SRC_DIR defaults to $JUNIT4_SRC, or to junit4's src/main/java used by the other scripts.
"""

import os
import re
import sys

DEFAULT_SRC = "/Users/mushfiqurrahmanchowdhury/Documents/junit4/src/main/java"
ENCODING = "ISO-8859-1"  # junit4's source encoding; maps every byte, so files round-trip unchanged

# The annotation, simple or fully qualified, with the spaces that follow it on the same line.
ANNOTATION = re.compile(r"@(?:org\.jspecify\.annotations\.)?NullUnmarked\b(?![.\w])[ \t]*")
IMPORT = re.compile(r"^[ \t]*import[ \t]+org\.jspecify\.annotations\.NullUnmarked[ \t]*;[ \t]*$")


def strip_file(text):
    """Returns (new_text, annotations_removed)."""
    removed = 0
    out = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if IMPORT.match(body):
            continue
        new_body, n = ANNOTATION.subn("", body)
        if n:
            removed += n
            if not new_body.strip():
                continue  # the annotation was alone on its line: drop the whole line
            out.append(new_body + ending)
        else:
            out.append(line)
    return "".join(out), removed


def main(argv):
    dry_run = "--dry-run" in argv
    args = [a for a in argv if a != "--dry-run"]
    src = args[0] if args else os.environ.get("JUNIT4_SRC", DEFAULT_SRC)
    if not os.path.isdir(src):
        sys.exit(f"Source directory not found: {src} (pass it as an argument or set JUNIT4_SRC)")

    total = files = 0
    for root, _, names in os.walk(src):
        for name in sorted(names):
            if not name.endswith(".java"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding=ENCODING, newline="") as f:
                text = f.read()
            new_text, removed = strip_file(text)
            if new_text == text:
                continue
            files += 1
            total += removed
            print(f"{removed:4d}  {os.path.relpath(path, src)}")
            if not dry_run:
                with open(path, "w", encoding=ENCODING, newline="") as f:
                    f.write(new_text)

    action = "Would remove" if dry_run else "Removed"
    print(f"{action} {total} @NullUnmarked annotation(s) in {files} file(s) under {src}")


if __name__ == "__main__":
    main(sys.argv[1:])
