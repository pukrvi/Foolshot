# Capture notes — how this sweep read X (22 November 2026)

The handoff's `xgrab.sh` clipboard path was written for the previous session. In this session the environment changed in two ways, so the working path is different. Keep this file with `xgrab.sh`; use whichever path the current machine allows.

## What was true on 22 Nov 2026

| Capability | State |
|---|---|
| Safari, signed in to X | Works. One window, X in tab 8, `@unhype.ai` session. |
| AppleScript to Safari (`get URL`, `set URL of tab`) | Works. `do JavaScript` fails: "Allow JavaScript from Apple Events" is off. |
| `osascript` → System Events keystrokes | **Denied**: "osascript is not allowed to send keystrokes". The clipboard steps in `xgrab.sh` fail for this reason. |
| CUA plugin (`cua.getApp`, `pressKey`, `getAccessibilityTree`) | Works. Accessibility and Screen Recording permissions reported true; app-level keyboard only. |
| Shell `screencapture -x -o file.png` | Works (one transient "could not create image from display" before the display woke; retry succeeded). |
| CUA window screenshot | Failed with `WINDOW_CHANGED` (display and AX bounds disagreed). Use shell `screencapture`. |
| `pbpaste` / clipboard | Works. Back up first (`pbpaste > /tmp/clip-backup2.txt`) and restore at the end. |

## Working recipe

1. **Initialize the CUA bridge once** (inside a `run_code` program; variables survive between calls unless the program times out):

```js
var cuaMod = await import("file:///Applications/DeepSeek%20Harness.app/Contents/Resources/app.asar/dsh/node_modules/@deepseek-ai/dsh-cua/lib/bridge.js");
var cua = cuaMod.connectCua(() => tools.cua, () => {});
var safari = await cua.getApp("Safari", { emit: false });
await safari.activate({ emit: false }); // Safari must be frontmost for keystrokes
```

2. **Navigate with AppleScript**, not keystrokes (tab 8 is the X tab):

```sh
osascript -e 'tell application "Safari" to set URL of tab 8 of front window to "https://x.com/search?q=...&src=typed_query&f=live"'
```

3. **Read the page as an accessibility tree.** Pick the wide window, not a sheet: windows with `bounds.width > 900`, then `win.getAccessibilityTree({ emit: false, maxElements: 9000, maxDepth: 80 })`. The tree contains one `AXGroup subrole=AXDocumentArticle` per post, with the full text, author, timestamp and the numeric `status/<id>` permalink. This is richer than the clipboard: it yields IDs, reply/like/view counts and the exact text.

4. **Scroll with the app-level keyboard**, then re-read the tree:

```js
await safari.pressKey("PageDown", [], { emit: false }); await sleep(2400);
```

3–6 PageDowns gave 5–27 unique posts per query in this sweep. Deduplicate by `status/<id>`.

5. **Long posts are truncated in the AX label.** The page splits long text across several AX nodes. For verbatim copies, fetch the mirror page for that post ID and strip the HTML:

```js
var wf = await tools.web_fetch({ url: "https://teapawt.net/<handle>/status/<id>" });
// strip script/style, replace <br> and block ends with newlines, strip tags, decode entities
```

Mirror copies are saved under `../snapshots/mirrors/<handle>-<id>.txt`. Match posts by numeric ID, not host: `x.com`, `twitter.com`, `teapawt.net` and `nitter.cf` can all point at the same post. teapawt/nitter search is behind Turnstile; individual pages render fine.

6. **Clipboard path still works through CUA** if a copy is needed: `safari.pressKey("a", ["command"])`, `safari.pressKey("c", ["command"])`, then `pbpaste > file` from bash. Safari must be frontmost; otherwise the copy goes to the DSH GUI. Do not call `cua.getApp("DeepSeek Harness")` while driving Safari — selecting that app can raise its window over Safari.

## Failure modes and fixes

- **X search "Something went wrong. Try reloading."** Two queries hit it once each; both answered on a later retry. Reload once, wait, retry; if it persists, wait 10–15 minutes (the handoff's rate-limit guidance still stands). Record `ERR: true` in the search snapshot header if a query never renders.
- **`osascript` keystrokes denied** is a permissions change, not a temporary error. Switch to CUA `pressKey`; do not keep retrying System Events.
- **Wrong window selected** (a small sheet instead of the browser): filter windows by width > 900 before reading AX.
- **Clipboard unchanged after Cmd+A/Cmd+C**: Safari was not frontmost. Re-activate Safari, confirm with `screencapture`, then retry.
- **Search date operators** are unreliable on Latest — see `../notes/search-log.md`. Add a keyword to `from:` queries.

## Files this recipe produced

- `../snapshots/search/qNN.txt` (plus `.json` for later runs): raw page text per query; the header carries the exact query, URL, tab, error flag and count.
- `../snapshots/posts/<topic>/`: `tree.txt` (raw AX dump), `thread.txt` (article text), `posts.json` (parsed articles).
- `../snapshots/mirrors/`: full-text mirror copies for long posts.
- `../snapshots/_all-search-posts.json`, `../snapshots/_fulltexts.json`: aggregate indexes.
