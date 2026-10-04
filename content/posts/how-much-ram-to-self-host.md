---
title: "How Much RAM Do You Need to Self-Host? (2026 Guide)"
date: 2026-10-04
description: "A straightforward guide to how much RAM popular self-hosted apps actually use, how much headroom to leave, and how to avoid the most common mistake: running out of memory."
tags: ["RAM", "self-hosting", "hardware"]
---

Out of every mistake new self-hosters make, running out of RAM is the one that causes the most pain. It rarely shows up as a clean error message. Instead a container gets silently killed, the web UI stops responding, or the whole server becomes unresponsive and you cannot even SSH in to see why.

This guide gives you realistic RAM numbers for popular apps and a simple way to add them up.

## The rule of thumb

Add up your apps, then add headroom. Docker images, a reverse proxy, and the operating system itself all take a slice. A practical formula:

**Total RAM = 0.5 GB (OS + Docker) + sum of app footprints + 25% headroom**

Then round up to the next plan size. Running out of memory causes crashes and data corruption; having a little spare RAM costs almost nothing.

## Typical RAM use by app

These are working numbers for light personal use, not benchmarks. Real usage depends on user count and load.

| App | Typical RAM | Notes |
|---|---|---|
| Vaultwarden | ~100–300 MB | Tiny, runs great on the smallest VPS |
| AdGuard Home / Pi-hole | ~100–300 MB | Very light |
| Uptime Kuma | ~100–300 MB | Monitoring; near-zero CPU |
| ntfy | ~100–300 MB | Push notifications |
| Home Assistant | ~600 MB–1 GB | Grows with add-ons |
| Forgejo / Gitea | ~300–600 MB | Git hosting |
| Syncthing | ~300–600 MB | File sync |
| Nextcloud | ~1–1.5 GB | Database + PHP; wants more if busy |
| n8n | ~1 GB | Automation workflows |
| Paperless-ngx | ~2 GB | OCR is memory-hungry |
| Nextcloud + Collabora | ~2–3 GB | Office editing adds a lot |
| Matrix (Synapse) | ~2 GB | Databases and federation |
| Grafana + Prometheus | ~2 GB | Metrics retention uses RAM |
| Immich | ~4 GB | Machine-learning photo indexing |
| Jellyfin / Plex (no transcode) | ~1–2 GB | Direct play is cheap |
| Jellyfin / Plex (transcoding) | ~2–4 GB + | Needs a capable CPU/GPU |

## The three classic mistakes

### 1. Buying an 8 GB box to run two light apps

Vaultwarden, AdGuard Home and Uptime Kuma together use well under 1 GB. A 1–2 GB VPS handles them fine. Buying huge "to be safe" just wastes money every month.

### 2. Trying to run Immich on a 2 GB VPS

Immich's machine-learning step for photo and face recognition needs several gigabytes. On a small box it will thrash, get killed, or crawl. Either give it 4 GB or disable the ML features.

### 3. Forgetting about transcoding

Plex and Jellyfin play video cheaply when the client supports the format directly ("direct play"). The moment they must convert ("transcode"), they need real CPU power, and budget VPS providers usually do not offer hardware transcoding. If transcoding is a requirement, a small home server with an Intel Quick Sync CPU is often the better buy.

## Add it up automatically

Rather than eyeball it, use the [Self-Hosting Planner](/tools/selfhost-planner/). Select the apps you want, set the number of users, and it adds up the RAM, CPU and disk and recommends a VPS size — with places to buy one.

## Bottom line

For a first self-hosted stack of light tools, **2 GB** is a good starting point. Add media or photo apps and plan on **4 GB or more**. Leave at least 25% free headroom, and size up one step if you are unsure. RAM is cheap; outages are not.
