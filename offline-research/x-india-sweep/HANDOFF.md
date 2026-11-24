# Handoff prompt — Indian-market AI trading sweep

Copy the block below into a new session. It assumes the same machine, the same Foolshot folder, and Safari still signed in to X.

---

## Prompt

You are continuing a research sweep for **Foolshot**, a planned 90-day live experiment in which an AI agent trades a real ₹1,00,000 Indian brokerage account (Dhan, with Zerodha as fallback). The experiment scores net P&L after charges and operational reliability. Read `Foolshot_Project_Dossier.md` at the repo root before judging relevance.

**Working directory:** `/Users/vishmac/Documents/GitHub/Foolshot`

### What already exists — do not repeat

The first collection is in `offline-research/`. Read these before searching:

- `offline-research/README.md` — coverage table of the 10 saved bookmarks and what each became.
- `offline-research/threads/shivansh-mehendiratta.md` — five live Dhan sessions, verbatim text plus replies.
- `offline-research/threads/pranjal-soni.md` — Zerodha week, 16 failure paths, backtest audit.
- `offline-research/threads/resource-posts.md` — Haseeb's NSE data step, Claude Trading Skills, bodila, ludoonchart.
- `offline-research/strategy-notes.md` — every strategy already logged, with setup, evidence and source.
- `offline-research/resources/INDEX.md` — 21 repositories already reviewed. Five are kept (`tradermonty/claude-trading-skills`, `virattt/ai-hedge-fund`, `marketcalls/openalgo`, `nautechsystems/nautilus_trader`, `freqtrade/freqtrade`). Sixteen were rejected and their staging folder has since been deleted; the reasons remain in the register. **Never re-download a rejected repo unless new evidence addresses the recorded reason.**

Authors already covered: `@shivanshco`, `@pranjalsoni_`, `@hb_stocks`, `@chatgptricks`, `@51bodila`, `@ludoonchart`. Use `from:` queries only to catch their new follow-ups.

### Your working folder — keep it separate

Everything you produce goes in `offline-research/x-india-sweep/`. Do not edit the existing `offline-research/` files except to add a pointer at the end. This keeps the second sweep cleanly separable for a later cleanup.

Already created for you:

```
offline-research/x-india-sweep/
  QUERIES.md          # 25 ready X search strings, operators cheat sheet, sweep order
  tools/xgrab.sh      # reads a page from the logged-in Safari session
  threads/            # verbatim thread copies go here
  notes/              # learning.md, search-log.md
  snapshots/          # raw copied page text, one file per page
  repos/              # offline copies of new, useful repos + INDEX.md
```

### What to produce

1. **Search strings.** `QUERIES.md` already holds the v1 set. Run them, then refine: add any Indian vocabulary that produced hits, drop queries that only return recycled listicles. Append new variants with the date they worked.

2. **Verbatim journey threads.** When someone documents their own AI-trading run (setup, days, P&L, incidents), copy the thread **as it is**, the way Shivansh's file does: original wording, in order, with the source link and date. Do not paraphrase inside the verbatim block. Put commentary in a separate "Notes" section below it. File per author: `threads/<handle>-<topic>.md`.

3. **Learning document.** `notes/learning.md` — one row per strategy or operational lesson found, in the shape of `strategy-notes.md`: setup described, reported evidence, disclosed limits, source link. Mark author-reported claims as such. Add anything that changes a Foolshot decision (costs, stops, sizing, reconciliation, broker quirks, SEBI/NSE rules).

4. **Offline repos.** For every GitHub link that survives review:
   - Check `offline-research/resources/INDEX.md` first by `owner/repo`.
   - Review upstream README, license, and the one file that matters before downloading.
   - Download only if you can name the file or pattern Foolshot will use.
   - Keep the copy under `repos/<owner>/<repo>/` and log the decision in `repos/INDEX.md`: upstream link, discovery source, review date, decision, reason, license, file inspected.
   - Do not download a repo that duplicates a kept one or repeats a rejected one.

5. **Search log.** `notes/search-log.md` — date, exact query, tab (Top/Latest), result count, what was saved. This is what stops the next run repeating your work.

6. **README.** `x-india-sweep/README.md` — what the sweep covered, what was new versus already known, where each artifact lives, and open questions.

### How to read X — the working method

The in-app browser tool is **disconnected** in this session; do not retry it. Safari's "Allow JavaScript from Apple Events" is **off**, so `do JavaScript` fails. What works:

- AppleScript can read tab titles and URLs and set a tab's URL.
- macOS Accessibility is granted, so System Events can click and type.
- `Cmd+A`, `Cmd+C`, `pbpaste` returns the rendered page text. This is the reliable extraction path.

Use `tools/xgrab.sh <url> <outfile> [tab_index] [wait]`. It activates Safari, loads the URL in tab 8, reloads once, selects and copies the page, and writes the clipboard to a file.

Safari currently has one window, nine tabs; **tab 8 is X**, signed in as `@unhype.ai`. Back up the clipboard (`pbpaste > /tmp/clip-backup.txt`) before you start and restore it when done.

**Known blocker:** X search currently returns a panel reading "Something went wrong. Try reloading." after both URL navigation and typing in the search box. Workarounds, in order:

1. Press `Cmd+R` or click **Retry** and wait 10 seconds before copying.
2. Type the query into the search box with the keyboard and press Return, rather than setting the URL.
3. Wait 10–15 minutes — this is the usual shape of an X search rate limit on a logged-in session.
4. If search stays broken, fall back to: the X **bookmarks** page (`x.com/i/bookmarks`), **Lists**, profile timelines of Indian trading accounts, and Google/Bing `site:x.com` queries. Public mirrors (`teapawt.net`, `nitter.cf`) render profiles and single posts but their search is behind a Cloudflare Turnstile check, so they are not a search substitute.

Take a screenshot (`screencapture -x -o <path>`) whenever a page looks wrong; reading the image is faster than guessing.

### Guardrails

- Match posts by numeric X post ID, not by URL host; `x.com`, `twitter.com`, `teapawt.net` and `nitter.cf` can all point at the same post.
- Author-reported P&L stays labelled author-reported. Never present a replay as a live result.
- Keep the raw copied text in `snapshots/` so a later reviewer can check a paraphrase against the page.
- Do not install packages, connect a broker, or place orders. This is read-only research.
- Keep every new artifact inside `x-india-sweep/`.

### Definition of done

- Every Tier 1–2 query in `QUERIES.md` has a row in the search log with a result count.
- Every new journey thread is saved verbatim with its source and date.
- `notes/learning.md` holds every strategy or operational lesson that was not already in `strategy-notes.md`.
- Every repo mentioned in a saved post has a decision in `repos/INDEX.md`; useful ones are downloaded, duplicates and rejects are not.
- `x-india-sweep/README.md` lists the new findings, the duplicates skipped, and the open questions.

---

## Short version

> Continue the Foolshot X research sweep in `/Users/vishmac/Documents/GitHub/Foolshot`. Read `offline-research/README.md`, `strategy-notes.md` and `resources/INDEX.md` first so you do not repeat the 10 bookmarks, 21 repo reviews or 16 rejects. Work only inside `offline-research/x-india-sweep/`, using the search strings in `QUERIES.md` and `tools/xgrab.sh` to read the logged-in X tab in Safari (tab 8). Save journey threads verbatim, strategies in `notes/learning.md`, and new repos offline under `repos/` with a decision log. X search is currently rate-limited ("Something went wrong"); retry, wait, or fall back to bookmarks, lists and `site:x.com` web search. Log every query and keep author-reported claims labelled.
