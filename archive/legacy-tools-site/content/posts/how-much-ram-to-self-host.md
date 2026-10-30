---
title: "How Much RAM Do You Need to Self-Host?"
shortTitle: "Give your apps room to breathe."
guideLabel: "CAPACITY / FIELD GUIDE"
date: 2026-10-04
lastmod: 2026-10-04
description: "Separate official requirements from planning allowances, leave room for background jobs, and choose a sensible starting capacity."
summary: "How to separate official requirements, service allowances and headroom when sizing your own server."
tags: ["RAM", "self-hosting", "hardware"]
---

**Start with the requirements for the apps you will actually run.** A small stack of lightweight services can have a modest planning target. Photo indexing, document processing and media conversion are different workloads. A universal “4 GB is enough” answer is not reliable.

This guide explains our planning method. It contains no measured RAM benchmarks, and our allowances are not guarantees.

## Three numbers that should stay separate

| Number | What it tells you | What it does not tell you |
|---|---|---|
| Official system requirement | What the app's current documentation calls for, under its stated conditions | The complete needs of several other apps sharing that machine |
| Service allowance | A working budget for our small personal-use model | A measured footprint or an official minimum |
| Headroom | Spare capacity for overlap, imports and background work | Guaranteed throughput under a heavy concurrent workload |

Do not add every official whole-system recommendation together as though each were a single container's allocation. Do not replace official requirements with a smaller internet anecdote, either. Model the shared stack, respect documented guidance and measure the real workload after installation.

## What the current official guidance says

Checked October 4, 2026; requirements can change with versions and features.

| App | Official guidance | Condition to notice |
|---|---|---|
| [Immich](https://docs.immich.app/install/requirements/) | 6 GB RAM / 2 cores minimum; 8 GB / 4 cores recommended | Its 4 GB exception requires ML disabled. Current v3 ML on amd64 needs x86-64-v2. Database storage needs a supported local filesystem. |
| [PhotoPrism](https://docs.photoprism.app/getting-started/) | At least 3 GB physical RAM and 2 cores; 4 GB swap | Large images and indexing can require more; a hard memory cap can cause restarts. |
| [Jellyfin](https://jellyfin.org/docs/general/administration/hardware-selection/) | The current hardware guide recommends 8 GB system RAM | Codec, GPU and client compatibility determine transcoding; memory alone does not establish support. |
| [Nextcloud](https://docs.nextcloud.com/server/latest/admin_manual/installation/system_requirements.html) | Memory guidance is per PHP process | Budget separately for the database, worker count and optional apps. A per-process figure is not a server-size recommendation. |

These are system and deployment conditions, not a promise that all four run comfortably on one machine matching only the largest figure.

## Our personal-stack calculation

The [Self-Hosting Planner](/tools/selfhost-planner/) adds service allowances to 0.5 GB for the OS/runtime, applies a small user multiplier, then adds 25% memory headroom. The result rounds upward and respects documented whole-host guidance where available.

For example, its small essentials preset budgets 256 MB each for Vaultwarden, AdGuard Home and Uptime Kuma. With the shared base and headroom, that gives a **2 GB planning target**. Those 256 MB values are our allowances for light personal use, not official minima or measurements. Monitoring history, queries, backups and other work can change the result.

The photo preset uses an **8 GB / 4-core target** for Immich with ML enabled, following its documented recommendation. Turning ML off changes the model, but you must also disable it in the application. Adding other services or heavy imports needs more consideration.

## Jobs that overlap change the answer

A quiet dashboard is not the same as OCR, a large photo upload, a backup and media conversion happening together. Estimate a representative busy period, limit or schedule heavy work where practical, then monitor memory pressure and actual application behavior.

CPU cores on shared hosting also vary in available performance. A hardware transcode requirement needs an appropriate device and access to it; buying extra RAM is not a substitute.

## A capacity plan is only the first step

Check storage, backup, transfer and the full recurring quote before purchase. For a photo or media library, those costs can dominate compute. A spare home machine may be worth comparing with a VPS, but it still has electricity, replacement, availability and maintenance costs.

Build your own [capacity and cost plan](/tools/selfhost-planner/), inspect its assumptions, and compare it with a real offer. Revisit the plan after your first import or busy week, using measurements rather than treating the first estimate as permanent.
