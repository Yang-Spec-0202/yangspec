---
title: "Self-Hosting Planner: Size Your Apps, Storage and Budget"
date: 2026-10-04
lastmod: 2026-10-05
description: "Choose your apps, plan capacity and a separate backup, then add real quotes to understand the whole monthly cost."
planner: true
ShowToc: false
---

{{< selfhost-planner >}}

<h2 id="method">The method, without the mystery.</h2>

This planner is for **small personal stacks**, not production capacity certification. It combines transparent planning allowances with documented system guidance where we have verified it. The result is a capacity target to compare with a real machine or plan, not a package that we have tested or a provider recommendation.

### Memory and compute

Service memory allowances are added to 0.5 GB for the OS and runtime. We apply a personal-use multiplier of 8% for each additional user, capped at 2×, and add 25% memory headroom. These are **YangSpec assumptions**, not measured concurrency or vendor promises. Memory rounds up in 2 GB increments.

Documented whole-host guidance acts as a floor. [Immich](https://docs.immich.app/install/requirements/) currently lists 6 GB / 2 cores minimum and 8 GB / 4 cores recommended. Its 4 GB exception requires machine learning disabled. [PhotoPrism](https://docs.photoprism.app/getting-started/) calls for at least 3 GB physical RAM, 2 cores and 4 GB swap. [Jellyfin's hardware guide](https://jellyfin.org/docs/general/administration/hardware-selection/) recommends 8 GB system memory. A service allowance in our model is not the same thing as an official system requirement.

CPU figures are personal-use allowances, not performance benchmarks. More accounts do not tell us how many people will stream, import photos or run OCR at the same time. Beyond 32 GB or 8 cores we flag custom sizing rather than returning an insufficient final tier.

### Storage and a real backup

Storage uses **decimal units: 1 TB = 1,000 GB**. We add application/data allowances to your file library and reserve 20% spare capacity. When Immich is selected, we conservatively add 20% of the entered library for generated files; for mixed photo/video stacks, this applies to the whole library and may overestimate that overhead. Separate libraries and unusually large caches need manual adjustment.

The backup number is **one full copy of estimated data**, without spare capacity. It is not a retention policy. Historical versions, snapshots, database exports, requests, restore tests and a second destination can require more space or fees. [Immich's backup guide](https://docs.immich.app/administration/backup-and-restore/) is a useful example of why both files and the database matter.

### Costs come from your quotes

The planner does not attach a generic VPS price to a large disk requirement. Enter a recurring server quote, its included disk capacity, any extra primary storage rate, a separate backup rate, and monthly transfer, domain/license/tax and management fees. Costs above included capacity change with your library size.

An empty field is **unknown**, not zero. Until all cost items are priced, the total monthly cost stays unknown. The partial amount includes only the named priced items; storage and backup are not automatically covered by a server price. Enter the server's included disk capacity and a separate backup quote. Even a complete quote-based total is not a provider offer: tiered pricing, minimum volume sizes, billing increments and renewal terms may change the bill. For a home server, include electricity in other monthly costs; account for hardware purchases and your time separately.

### Playback changes the decision

- **Direct Play:** clients use the original video without conversion. Verify client and codec support.
- **Hardware transcoding:** confirm a compatible GPU/iGPU, codec support, drivers and device access. Additional vCPU cores do not establish GPU access on a VPS.
- **Software transcoding:** the planner deliberately leaves transcode capacity unsized. Resolution, codec, tone mapping and simultaneous streams require a workload test.

Read [Jellyfin's hardware selection guide](https://jellyfin.org/docs/general/administration/hardware-selection/) before choosing a media host. Immich ML on amd64 also requires a compatible CPU instruction set in its current v3 guidance.

For Jellyfin, use [our home-server and VPS decision guide](/posts/jellyfin-vps-or-home-server/) to distinguish Direct Play, audio conversion and video transcoding. It includes client, GPU-access and upload checks plus the existing [2 TB media example](/tools/selfhost-planner/?preset=media). Its base CPU allowance is not a transcode benchmark; complete host costs remain unknown without your quotes.

<h2 id="next-step">Take the plan to a real quote.</h2>

For light personal apps within the small-capacity scope, use our [2 GB / 4 GB VPS comparison](/posts/best-cheap-vps-for-self-hosting-2026/) to check location, usable disk, network limits, billing and backup options. For photos or larger file libraries, start with [storage and recovery](#storage-and-a-real-backup); for video, start with [playback compatibility](#playback-changes-the-decision). Compare a home server or dedicated/storage-focused host where needed. Workloads outside the starter range need separate sizing. We do not claim that an unverified provider package matches your plan.

For Immich, read [the 2 TB storage and cost example](/posts/immich-2tb-hosting-cost/) or [open that capacity scenario](/tools/selfhost-planner/?preset=photos-2tb). It compares home and cloud storage with a separate backup; adjust the example to your library. The Photos button above keeps its original 1 TB starting point.

You can also read [the RAM guide](/posts/how-much-ram-to-self-host/) and [the full-cost comparison](/posts/self-hosting-vs-cloud-cost/). Some links elsewhere on the site may earn a commission; commission does not enter this calculator's capacity or cost formulas.

Model version 1.0 · reviewed October 4, 2026. Deployment references explain how an app is hosted; they do not validate every allowance. We have not benchmarked these workloads.
