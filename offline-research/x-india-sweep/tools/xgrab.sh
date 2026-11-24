#!/bin/zsh
#
# NOTE (22 Nov 2026): the System Events keystroke steps below are DENIED in this
# environment ("osascript is not allowed to send keystrokes"), so this script no
# longer works as written. The working path that replaced it is documented in
# capture-notes.md next to this file: AppleScript sets the tab URL, the CUA
# plugin's accessibility tree reads the page, and a mirror fetch fills in long
# posts. Keep this script for machines where Accessibility for osascript is
# granted; otherwise use capture-notes.md.
#
# Read the text of a page in the user's logged-in Safari session.
#
# Why this exists: the in-app browser tool is disconnected, and Safari's
# "Allow JavaScript from Apple Events" is off, so the DOM cannot be read
# directly. This script activates Safari, loads a URL in a dedicated tab,
# selects the page, copies it, and writes the clipboard to a file.
#
# Requirements: macOS Accessibility permission for the process that runs
# this script (already granted), Safari running and signed in to X.
#
# usage: xgrab.sh <url> <outfile> [tab_index] [wait_seconds]

set -u
URL="$1"
OUT="$2"
TAB="${3:-8}"
WAIT="${4:-7}"

osascript <<APPLESCRIPT
tell application "Safari"
  activate
  set w to front window
  set current tab of w to tab $TAB of w
  set URL of tab $TAB of w to "$URL"
end tell
APPLESCRIPT

sleep "$WAIT"

# X sometimes renders an error panel after programmatic navigation.
# Reload once, then give the feed time to paint.
osascript -e 'tell application "System Events" to keystroke "r" using command down'
sleep 5

osascript -e 'tell application "System Events" to keystroke "a" using command down'
sleep 0.4
osascript -e 'tell application "System Events" to keystroke "c" using command down'
sleep 2

pbpaste > "$OUT"
wc -c "$OUT"
