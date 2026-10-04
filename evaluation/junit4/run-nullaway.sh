#!/bin/bash
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

# Runs NullAway on junit4 and writes nullaway-warnings.txt and nullaway-report.txt
# into this directory. Usage: ./run-nullaway.sh   (or JUNIT4_SRC=/path/to/src/main/java ./run-nullaway.sh)
set -u
cd "$(dirname "$0")"

# Use JDK 21 for Gradle and the annotator (macOS helper; otherwise the existing JAVA_HOME is used)
if [ -x /usr/libexec/java_home ] && JH=$(/usr/libexec/java_home -v 21 2>/dev/null); then
  export JAVA_HOME="$JH"
fi
if [ -n "${JAVA_HOME:-}" ]; then export PATH="$JAVA_HOME/bin:$PATH"; fi
echo "Using JAVA_HOME=${JAVA_HOME:-<not set>}"

# junit4 sources to analyze
JUNIT4_SRC="${JUNIT4_SRC:-/Users/mushfiqurrahmanchowdhury/Documents/junit4/src/main/java}"
[ -d "$JUNIT4_SRC" ] || { echo "junit4 sources not found: $JUNIT4_SRC (set JUNIT4_SRC)"; exit 1; }
./gradlew --stop > /dev/null 2>&1   # discard daemons started with another JDK

./gradlew compileJava --rerun-tasks -PsrcDir="$JUNIT4_SRC" > build-output.txt 2>&1
echo "gradle exit code: $? (1 is expected when NullAway reports errors)"

# 1) Every NullAway diagnostic with its source line and caret
awk '/^[^ ].*\.java:[0-9]+: (warning|error):/{p=/\[NullAway\]/} /^(Note:|[0-9]+ (warning|error)s?$|> Task|BUILD|$)/{p=0} p' \
    build-output.txt > nullaway-warnings.txt

# 2) Summary report
{
  echo "NullAway report for: $JUNIT4_SRC"
  echo "Generated: $(date)"
  echo
  echo "Total NullAway warnings: $(grep -c '\[NullAway\]' build-output.txt)"
  echo
  echo "== By warning type =="
  grep -o '\[NullAway\] [^:(]*' build-output.txt | sed "s/\[NullAway\] //; s/'[^']*'/'X'/g" | sort | uniq -c | sort -rn
  echo
  echo "== By file =="
  grep '\[NullAway\]' build-output.txt | sed -E 's#^.*/src/main/java/##; s#:[0-9]+:.*##' | sort | uniq -c | sort -rn
} > nullaway-report.txt

echo "Wrote $(pwd)/nullaway-warnings.txt and $(pwd)/nullaway-report.txt"
grep -m1 '^Total' nullaway-report.txt
