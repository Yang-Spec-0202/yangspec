---
title: "Hosting a 2 TB Immich Library: Home, Cloud and the Whole Cost"
shortTitle: "Two terabytes need more than a server."
guideLabel: "PHOTOS / FIELD GUIDE"
date: 2026-10-05
lastmod: 2026-10-05
description: "Plan a 2 TB Immich library with usable storage, a local database, an independent backup and honest home or cloud costs."
summary: "A worked capacity estimate and a dated cloud cost example, with a home-server worksheet and a recovery checklist."
tags: ["self-hosting", "immich", "storage", "cost"]
---

**For 2 TB of original photos and videos, plan the disks and recovery before choosing a host.** Our example estimates 2.904 TB of primary capacity and 2.42 TB for one full backup copy. A small VPS disk cannot hold this library; a home machine or NAS may be worth comparing if you can operate it and restore it.

This is a planning example, not an Immich deployment benchmark or an installation tutorial. Official requirements and public USD rates were checked **October 5, 2026**. Your workload, region, hardware and final checkout still need verification.

[Open the 2 TB Immich example](/tools/selfhost-planner/?preset=photos-2tb), then replace the library size and quotes with your own.

## What the 2 TB estimate includes

Assume Immich alone, one user and machine learning enabled. YangSpec uses **decimal storage: 1 TB = 1,000 GB**. The planner returns an **8 GB RAM / 4-core target**, not a measured import speed or concurrency limit.

| Component | Planning amount | What it means |
|---|---|---|
| Original photo and video library | 2,000 GB | Your input; exclude duplicate counting of the same originals |
| Generated files | 400 GB | Our 20% allowance for thumbnails and encoded video |
| Application/data allowance | 20 GB | Our estimate for app data; monitor database, logs and container usage |
| Estimated data to copy | 2,420 GB | Originals + generated files + app allowance |
| Spare primary capacity | 484 GB | 20% of estimated data; empty space is not backed up |
| Primary capacity target | **2,904 GB** | About 2.9 TB as displayed by the planner |
| One full backup copy | **2,420 GB** | 2.42 TB before extra versions, exports or backup overhead |

These allowances are model assumptions. [Immich's requirements](https://docs.immich.app/install/requirements/) describe generated files as averaging another 10–20%; that is not an upper bound. They list 6 GB / 2 cores minimum and 8 GB / 4 cores recommended. The 4 GB exception needs ML disabled. Use a compatible 64-bit host; current v3 ML on amd64 requires x86-64-v2. PostgreSQL should ideally use a local SSD and must not use a network share. Media needs a filesystem with Unix ownership and permissions. Check the actual CPU and filesystem before buying.

## Home machine or NAS versus cloud

| Decision | Home machine or NAS | Cloud VM with attached storage |
|---|---|---|
| Primary disk | Check usable space after mirrors, formatting, reserves and other apps | Quote a media volume separately from the boot/database disk |
| Availability | Depends on your power, internet and maintenance | Depends on the selected service and your software operations |
| Remote access | Check upload speed, ISP conditions and your access method | Check region latency, transfer allowance and secure access |
| Recovery | Need replacement hardware and an independent copy | Need replacement compute/storage and an independent copy |
| Cost information still needed | Equipment, power rate, internet changes and backup | Compatible plan, storage, transfer, tax and backup retention |

A hypothetical two-drive mirror using two 4 TB drives provides roughly **4 TB nominal capacity**, before filesystem overhead and reserves. It does not provide 8 TB usable space. Check that the remaining usable capacity exceeds your target. A mirror helps with a drive failure; deletion, theft and damage to the whole machine can still affect both drives. Budget a separate backup destination.

For a home setup, use **measured average watts ÷ 1,000 × running hours × your electricity rate**. An illustrative 30 W setup over 720 hours uses **21.6 kWh**. Its dollar cost is unknown until you supply a rate. Include the drives and relevant networking equipment in the measurement.

Compare equipment cost divided by your chosen ownership months, while keeping the upfront cash purchase visible. Add replacement drives, any extra internet charge, backup and maintenance time. Equipment already owned still has a replacement cost. No local electricity tariff or hardware price is assumed here.

## A dated cloud cost example

Use DigitalOcean's **Basic Regular 8 GiB / 4 shared vCPU** bundled plan as a public-rate example, with NYC3 as the intended region. This is not a verified purchase or a claim that this is the cheapest option. Confirm plan availability, CPU instructions and volume compatibility in that region before ordering.

Place the database and app files on the included boot SSD; place originals and generated media on a separately mounted, compatible filesystem. In this illustrative split, app data plus spare capacity is **24 GB** on the boot disk. Media plus spare capacity is **2,880 GB** on the media volume. Together they match the model's 2,904 GB target. Monitor actual OS/container use as well as these allowances.

For comparison, select a **3,000 GiB** volume, approximately **3,221 GB decimal**, above the media target. This is an example purchase size, not a measured minimum. Check free space after formatting. DigitalOcean's [volume documentation](https://docs.digitalocean.com/products/volumes/details/features/) describes network-attached block storage that can be formatted and mounted; it is a separate resource from the boot disk.

| Quoted component | Public rate / example amount | Coverage and exclusions |
|---|---|---|
| [Basic Regular VM](https://www.digitalocean.com/pricing/droplets) | **$48/month** cap; $0.07143/hour equivalent | 8 GiB RAM, 4 shared vCPU, 160 GiB SSD and 5,000 GiB transfer; no separate backup in this amount |
| [Attached volume](https://docs.digitalocean.com/products/volumes/details/pricing/) | **$0.10/GiB/month × 3,000 = $300/month** | Purchased capacity, not bytes used; accrues hourly while the volume exists, even detached |
| Known VM + primary storage amount | **$348 at monthly rates; complete monthly total unknown** | Covers only the two lines above |
| [B2 backup storage](https://www.backblaze.com/cloud-storage/pricing) | **$6.95/TB/30 days**, billed by byte-hours | One 2.42 TB copy scales to about **$16.82 per 30 days**, before the first 10 GB free allowance; no compression assumed |
| Transfer, retained versions, other fees and management | **Not fully quoted** | Usage, recovery frequency, domain/license/tax and paid operations still need prices |

The B2 scaling example treats TB as decimal and assumes that amount is stored for all 30 days; verify the provider's byte-based estimate for your actual data. It is storage-only, not a backup-service or full hosting quote. Calendar length, upload timing and retained versions change the bill. [B2 charges for stored duplicate files and old versions](https://www.backblaze.com/docs/cloud-storage-files).

This comparison uses recurring public rates, with no introductory discount or annual commitment. First-month upload and partial-month storage differ from later months; future rates are not locked. Tax treatment and your final checkout amount are unverified. [Bundled Droplets](https://docs.digitalocean.com/products/droplets/details/pricing/) have a 672-hour monthly cap; powering one off does not stop billing. The separately priced v5 configuration is a different product and is outside this example.

### Transfer is part of the bill

DigitalOcean documents free inbound transfer and **$0.01/GiB** outbound overage. Public outbound traffic, including backup uploads and remote viewing, consumes the team's pooled allowance; inspect the accrued allowance and usage rather than assuming the full listed quota is available in a short first month. B2 includes egress up to three times average monthly stored data, then **$0.01/GB**; Class A/B/C calls are free, while Class D calls have their own allowance and fee. Those conditions do not establish that your transfer or request bill is zero. See the linked [transfer billing](https://docs.digitalocean.com/platform/billing/bandwidth/) and [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) pages.

The attached volume dominates this example's known bill. Compare a storage-focused host and a home setup using the same capacity, compatibility and recovery requirements. We have not quoted or tested those alternatives, so their complete costs remain unknown.

## Keep a backup that can actually restore Immich

[Immich's backup instructions](https://docs.immich.app/administration/backup-and-restore/) require **both media files and the database**. An automatic database export does not back up the photos, and an export left beside the originals is not an independent destination. Include external-library paths if used.

One possible destination is B2 US West, separate from a primary server in New York. [Backblaze's region guidance](https://www.backblaze.com/docs/cloud-storage-data-regions) says the account region is selected at creation. A different provider and region reduces shared infrastructure exposure; access controls, retention and a tested restore still matter. Object storage is a target for backup software, not a substitute for the application's live filesystem or database disk. A same-provider snapshot can help recovery but does not by itself protect against losing access to that provider account.

Before relying on the copy:

1. Save a consistent database export and matching files. Immich recommends stopping its server while backing up; if that is impractical, export the database before copying files.
2. Copy to an independent destination, with restricted backup access and a chosen retention policy. Allow extra storage for history and exports; the planner's 2.42 TB is one-copy data only.
3. Keep the Compose configuration, version record and required recovery secrets securely recoverable. Use the official restore instructions for the version you run.
4. Restore onto a separate test instance. Check original downloads, albums, metadata and a new upload; record how long the recovery takes. We have not performed this deployment or restore test.

## Take the estimate to your own quote

Start from [the 2 TB planner example](/tools/selfhost-planner/?preset=photos-2tb). The ordinary Photos button still starts at 1 TB. Neither entry fills prices or matches a provider package.

The calculator treats included disk and extra storage as aggregate capacity. It does not allocate mount points: **unused boot-disk space cannot automatically reduce a separately mounted media volume**. DigitalOcean bills in GiB while the planner uses decimal GB; $0.10/GiB is approximately $0.09313/decimal GB. Billing increments, a fixed purchased volume, retained backup versions and byte-hour/free allowances need a separate invoice worksheet. Do not expect the simple calculator to reproduce this provider bill exactly.

For installation, follow the current [official Docker Compose guide](https://docs.immich.app/install/docker-compose/). Set `UPLOAD_LOCATION` to the intended media path and `DB_DATA_LOCATION` to suitable local storage; keep configuration private and record the deployed version. Begin with a small test library before importing the only copy of your originals.

Get a complete quote for primary capacity, an independent backup with retention, ordinary traffic and a restore, taxes and any paid management. Compare your upfront home costs and time separately using [the whole-cost worksheet](/posts/self-hosting-vs-cloud-cost/). If you change apps or users, revisit [the sizing limits](/posts/how-much-ram-to-self-host/). A capacity estimate and a readable price table do not establish operational readiness.
