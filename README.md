# BRANDSTUDIO — Public Instagram Content Store

This repository is the public archive and media host for approved BRANDSTUDIO Instagram content.

- Account: @brandsstudio11
- Platform: Instagram only
- Buffer channel: `brandsstudio11`
- Default branch: `main`

## Folder layout

Each publishing date has its own folder:

`YYYY-MM-DD/`
- `feed.jpg` — one single-image feed post
- `carousel-01.jpg` … `carousel-05.jpg` — five slides in reading order
- `reel.mp4` — one vertical Reel
- `post-manifest.json` — captions, alt text, source notes, asset paths, raw URLs, QA and Buffer post IDs/status

The daily task must preserve the approved BRANDSTUDIO output counts and may add a separate SEO article to its website workflow; website articles are not Instagram assets.

## Publishing rules

1. Store only final, approved, publicly shareable Instagram media and the corresponding public post manifest. This repository is public; everything committed here can be accessed by anyone.
2. Do not upload credentials, private client data, draft artwork, private production files, full ZIP packages, editable source projects, or unlicensed third-party assets.
3. Use unique dated paths. Keep previously published media and manifests as an archive; do not delete files after Buffer has sent a post.
4. Buffer may receive only direct, anonymously downloadable raw GitHub HTTPS file URLs. Verify each URL returns the actual non-empty binary media with the expected media type before scheduling it. A GitHub page URL, preview page, placeholder, source-code file, or guessed URL is not a valid media asset.
5. Use Buffer's connected Instagram Business channel for @brandsstudio11 only. Queue using automatic publishing; verify every returned post ID in Buffer. A queued post is not yet published.
6. Record the Buffer ID, scheduling/publishing status, sent time (if any), asset paths and verification results in the dated manifest and root `content-index.json`.
7. If a media binary cannot be transferred exactly to this repository or its raw URL cannot be verified, do not submit that item to Buffer. Keep the content task enabled and record the specific blocker.

## Content index

`content-index.json` is the persistent machine-readable index of dated content packages. Append new entries; never replace or truncate the history.
