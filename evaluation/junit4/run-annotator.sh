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

# Builds NullAwayAnnotator from this repository and runs it on junit4.
# NOTE: the annotator edits the junit4 source files in place; run it on a separate junit4 branch.
# Usage: ./run-annotator.sh   (or JUNIT4_SRC=/path/to/src/main/java ./run-annotator.sh)
set -eu
cd "$(dirname "$0")"
HERE="$(pwd)"
REPO="$(cd ../.. && pwd)"

# Use JDK 21 for Gradle and the annotator (macOS helper; otherwise the existing JAVA_HOME is used)
if [ -x /usr/libexec/java_home ] && JH=$(/usr/libexec/java_home -v 21 2>/dev/null); then
  export JAVA_HOME="$JH"
fi
if [ -n "${JAVA_HOME:-}" ]; then export PATH="$JAVA_HOME/bin:$PATH"; fi
echo "Using JAVA_HOME=${JAVA_HOME:-<not set>}"

# junit4 sources to analyze
JUNIT4_SRC="${JUNIT4_SRC:-/Users/mushfiqurrahmanchowdhury/Documents/junit4/src/main/java}"
[ -d "$JUNIT4_SRC" ] || { echo "junit4 sources not found: $JUNIT4_SRC (set JUNIT4_SRC)"; exit 1; }

# 1) Build annotator-core and publish annotator-scanner to ~/.m2 from this checkout
VERSION="$(grep '^VERSION_NAME=' "$REPO/gradle.properties" | cut -d= -f2)"
(cd "$REPO" && ./gradlew :annotator-core:shadowJar :annotator-scanner:publishToMavenLocal)
ANNOTATOR_JAR="$REPO/annotator-core/build/libs/annotator-core-$VERSION.jar"
[ -f "$ANNOTATOR_JAR" ] || { echo "Annotator jar not found: $ANNOTATOR_JAR"; exit 1; }

# 2) The output directory must start EMPTY
OUT="$HERE/annotator-out"
rm -rf "$OUT" && mkdir -p "$OUT"
printf '%s\t%s\n' "$OUT/nullaway.xml" "$OUT/scanner.xml" > "$OUT/paths.tsv"

# 3) Run the annotator. --rerun-tasks makes every build recompile ALL files,
#    so NullAway re-reports every remaining error each time.
./gradlew --stop > /dev/null 2>&1 || true
BUILD_CMD="cd '$HERE' && ./gradlew compileJava --rerun-tasks -Pannotator=true -PannotatorVersion='$VERSION' -PsrcDir='$JUNIT4_SRC'"

java -jar "$ANNOTATOR_JAR" \
    -bc "$BUILD_CMD" \
    -d "$OUT" \
    -cp "$OUT/paths.tsv" \
    -cn NULLAWAY \
    -n javax.annotation.Nullable \
    -i com.uber.nullaway.annotations.Initializer \
    -sre org.jspecify.annotations.NullUnmarked \
    -ll 21 \
    2>&1 | tee annotator-log.txt
