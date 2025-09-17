#!/usr/bin/env bats

# Basic non-destructive tests for mkvnmp4 shell script

setup() {
  # create a temp config and point HOME to tmp for the test
  TMPDIR=$(mktemp -d)
  export HOME="$TMPDIR"
  echo "/tmp" > "$TMPDIR/.mkvnmp4.conf"
}

teardown() {
  rm -rf "$TMPDIR"
}

@test "help prints usage" {
  # call the script from the repository root regardless of cwd in the runner
  run "$BATS_TEST_DIRNAME/../mkvnmp4" --help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Usage" || "$output" =~ "--send" || "$output" =~ "--rm" ]]
}

@test "dup runs (non-destructive)" {
  run "$BATS_TEST_DIRNAME/../mkvnmp4" --dup
  [ "$status" -eq 0 ]
}
