# Repository and Pages publication evidence

Verified 2026-11-17 UTC from live GitHub API, HTTP and Chromium.

Public repository: https://github.com/howlcipher/howlspeaker

Project page: https://howlcipher.github.io/howlspeaker/

Review PR: https://github.com/howlcipher/howlspeaker/pull/1

Repository visibility PUBLIC, application license MIT, default branch main.
Initial signed foundation backup on main: ac5841e. Export API/CLI and static page
are backed up on feature/wav-export-and-project-page, with PR #1 OPEN for review.
No merge is claimed. The feature branch must be retained while the page's command
examples and guide link reference it; update those links when integrating to main.

Deployed static source revision: 7ae3b750c2e0a2f29a44a7edd1cb4c92a0db30cc.
Pages workflow succeeded (13 sec):
https://github.com/howlcipher/howlspeaker/actions/runs/43999693088

PR CI succeeded on Python 3.12 (15 sec):
https://github.com/howlcipher/howlspeaker/actions/runs/43999692809

CI runs all 147 lightweight tests, flake8, wheel build and CLI help. Local Python
3.14.4 full regression also passes: 147 passed, 0 failed, 0 skipped. Wheel-installed
export CLI acceptance used one-second generated silent PCM, not a real voice.
No inference is part of CI. Later documentation-only commits have their own PR CI
runs; use the PR checks for the final head rather than assuming this run covers it.

Public page and CSS/JS/favicon returned HTTP 200. Chromium rendered the deployed
page with expected content and no JS errors. Local desktop/mobile checks passed:
1440x1000 and 375x812, no horizontal page overflow, theme persistence, ecosystem
menu Escape/focus and screenshot inspection. No formal accessibility certification.

Pages uses workflow deployment and publishes site/ only. The new github-pages
environment permits main and the named review branch; no existing user policy was
removed. The public static site has no file upload, inference endpoint, analytics,
remote fonts or third-party scripts. No audio, model, secrets or private context
library was published. A credential-pattern scan found no credentials in the
foundation commit. This limited scan is not a full M6 security audit.

Git's inherited credential helper pointed to a missing executable. A repository-
local helper now calls the existing /usr/bin/gh; no global Git configuration was
changed and no credential values were written to source or logs.

M1 remains BLOCKED for real synthesis. No weights downloaded or inference run.

## 2026-11-17 audio/video preparation update

Deployed source db1dd0b3d3d9827a7bbe99c98625492471d115d1 includes recording-script
and local audio/video preparation instructions. Pages run 44006468922 succeeded:
https://github.com/howlcipher/howlspeaker/actions/runs/44006468922

CI for that source succeeded on Python 3.12 (191 tests plus lint/package checks):
https://github.com/howlcipher/howlspeaker/actions/runs/44006476706

Public HTTP 200 content includes sample-script/prepare-sample, and mobile Chromium
render has no horizontal page overflow or JS errors. Desktop/mobile local checks
also pass. Installed wheel CLI reading-script and real guarded WAV preparation
passed. The opt-in synthetic MP3/MP4 and timeout smoke evidence is in media_smoke.json.
No user footage, models or generated narration were uploaded to the repository or
site. Local recordings and common media formats are now ignored by Git. PR #1
remains open; no merge or real synthesis completion is claimed. Later docs-only
head checks are visible in that PR.
