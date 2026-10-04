---
title: "Self-Hosting Planner: What VPS Do You Actually Need?"
date: 2026-10-04
description: "Select the apps you want to self-host and instantly get a recommended RAM, CPU, and disk size, an estimated monthly cost, and reputable VPS providers to buy from."
---

Trying to self-host and not sure how much server you need? Don't buy a 16 GB machine to run your first app, and don't get stuck with a 1 GB box that crashes the moment Jellyfin starts transcoding. Pick the apps you actually plan to run below, and the planner will estimate the right size and point you at sane places to buy it.

{{< selfhost-planner >}}

## How the estimate works

Each app has a typical RAM and CPU footprint. The planner adds them up, applies a small multiplier for the number of users, adds a base amount for the operating system and Docker, then rounds up to the nearest common VPS size. Media storage is added on top because photos and video dominate disk usage on almost every setup.

The goal is a **sane starting point**, not a guarantee. If you are unsure, size up one tier &mdash; running out of RAM is painful, while a slightly larger VPS just costs a couple more dollars a month.

## How to read the result

- **RAM** is the number that most often limits self-hosting. Most crashes and "killed" containers come from running out of memory, not CPU.
- **vCPU cores** matter for transcoding, OCR (Paperless), and heavy background jobs. Light apps mostly idle.
- **Disk** is a minimum. Media libraries grow forever, so pick a provider that lets you attach or expand storage cheaply.

## Frequently asked questions

### Can I run everything on one small VPS?

Yes, for light apps. Vaultwarden, AdGuard Home, Uptime Kuma, ntfy and similar tools can all share a 1 GB or 2 GB VPS without trouble. Media servers and photo apps are the ones that push you into bigger plans.

### Is 1 GB of RAM enough?

For a couple of tiny services, yes. For almost anything with a database and a web UI under regular use, 2 GB is a much more comfortable floor in 2026.

### Do I need hardware transcoding?

Only if you stream video to devices that can't play the original format directly. If you do, budget for an Intel CPU with Quick Sync, which most budget VPS providers do not offer &mdash; a small home server is often cheaper than a transcoding VPS.

### VPS, dedicated server, or a home server?

Start with a VPS if you want low upfront cost and don't need much storage. Move to a home server (or a storage-focused box) once your media library or photo collection outgrows cheap VPS storage.
