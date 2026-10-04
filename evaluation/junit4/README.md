# Evaluating NullAwayAnnotator on junit4

This directory holds a standalone Gradle build that compiles the main sources of
[junit4](https://github.com/junit-team/junit4) with NullAway, plus two scripts:

| Script | What it does |
|---|---|
| `run-nullaway.sh` | Runs NullAway on junit4 and writes `nullaway-warnings.txt` (every NullAway diagnostic) and `nullaway-report.txt` (totals by warning type and by file). |
| `run-annotator.sh` | Builds NullAwayAnnotator from this checkout, then runs it on junit4. **It edits the junit4 sources in place.** |
| `remove-suppressions.py` | Removes every suppression the annotator added for errors it could not fix: `@NullUnmarked` (and its import), `@SuppressWarnings("NullAway")` and `@SuppressWarnings("NullAway.Init")`, so NullAway reports all remaining errors again. junit4's own `@SuppressWarnings` values are kept. Also edits junit4 in place; `--dry-run` only lists what it would remove. |

junit4's own Maven build targets Java 5, which Error Prone does not support, so junit4 is
compiled here with `--release 21` instead, without changing junit4 itself.

## Requirements

- JDK 21. On macOS the scripts pick it up with `/usr/libexec/java_home -v 21`; elsewhere set `JAVA_HOME`.
- Python 3 for `remove-suppressions.py`.
- A junit4 checkout. By default the scripts read
  `/Users/mushfiqurrahmanchowdhury/Documents/junit4/src/main/java`; set `JUNIT4_SRC` to use another path.

## Steps

1. Put junit4 on its own branch, because the annotator modifies its sources:
   ```bash
   cd /path/to/junit4
   git checkout EvaluateNullAwayAnnotator
   git checkout -b annotator-run
   ```
2. Record the baseline NullAway errors:
   ```bash
   cd evaluation/junit4
   ./run-nullaway.sh
   cp nullaway-report.txt nullaway-report-before.txt
   ```
   Gradle ends with `BUILD FAILED` (exit code 1); that is expected, since NullAway reports errors.
3. Run the annotator:
   ```bash
   ./run-annotator.sh
   ```
   Its output is saved in `annotator-log.txt`; NullAway and scanner outputs go to `annotator-out/`.
4. Check the result:
   ```bash
   (cd /path/to/junit4 && git diff --stat)   # files the annotator changed
   ./run-nullaway.sh                         # remaining NullAway errors after annotation
   ```
5. To get the real number of errors remaining after annotation, remove the suppressions the
   annotator added and run NullAway again:
   ```bash
   (cd /path/to/junit4 && git commit -am "NullAwayAnnotator output")   # keep the annotated version
   ./remove-suppressions.py --dry-run   # list what would be removed
   ./remove-suppressions.py             # remove them
   ./run-nullaway.sh                    # all errors remaining after annotation
   ```
   The inferred `@Nullable` and `@Initializer` annotations are kept, since they are the
   annotator's fixes rather than suppressions.

## Configuration

- NullAway 0.14.1, Error Prone 2.42.0 and annotator-scanner from this repository
  (version from `gradle.properties`, published to `~/.m2` by `run-annotator.sh`).
- `NullAway:AnnotatedPackages` is `org.junit,junit`.
- The annotator runs with `-n javax.annotation.Nullable`,
  `-i com.uber.nullaway.annotations.Initializer`,
  `-sre org.jspecify.annotations.NullUnmarked` and `-ll 21`.
- The annotator's build command uses `--rerun-tasks` so that every build recompiles all
  files and NullAway re-reports every remaining error.

After annotation, junit4 imports `javax.annotation.Nullable` and
`org.jspecify.annotations.NullUnmarked`, which junit4's `pom.xml` does not depend on, so
junit4's own Maven build no longer compiles on that branch; this Gradle build still does.
