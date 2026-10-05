---
title: "Choosing a VPS for Self-Hosting: What to Check Before Buying"
shortTitle: "Choose a host, not a headline price."
guideLabel: "BUYING / FIELD GUIDE"
date: 2026-10-04
lastmod: 2026-10-05
description: "Compare four small VPS plans, their billing terms, optional backups and the costs still missing from the whole bill."
summary: "A sourced 2 GB / 4 GB comparison for light personal apps, with monthly caps, backup limits and unknown costs kept visible."
tags: ["VPS", "self-hosting", "hosting"]
---

**A 2 GB VPS can be a planning target for a small personal stack; it is not a default for every app.** Compare a plan that meets your requirements, then price recovery and the rest of the bill. The four public plans below give you a starting comparison, not a complete purchase quote.

Checked **October 5, 2026**. Scope: the **US market, billed in USD**, with the **New York area** as the deployment target to check (DigitalOcean NYC3; Vultr New York Area). Prices are public catalogue rates before applicable tax, without promotional credits. We have not verified live regional stock or a logged-in order quote. Vultr explicitly warns that location prices can differ; its New York quote remains **unknown**. These are ordinary official links. We have not benchmarked either provider and do not rank them by performance or affiliate commission.

## Decide whether this small-stack comparison applies

The [Self-Hosting Planner](/tools/selfhost-planner/) has a **Start small** preset: Vaultwarden, AdGuard Home and Uptime Kuma. At its default light personal-use settings, the model gives a **2 GB / 1-vCPU target**. Its allowances and spare capacity are estimates, not official minima or measured throughput. Read [how we budget RAM](/posts/how-much-ram-to-self-host/) before relying on that target.

Consider 4 GB when your selected stack needs more memory, you want spare capacity for updates and backup jobs, or measurements show pressure. More RAM will not fix sustained CPU demand, a growing disk or slow connectivity. Check the actual container architecture and current app requirements; these plans use shared x86 CPU resources, not dedicated cores or a promised GPU. DigitalOcean documents [Basic as shared CPU](https://docs.digitalocean.com/products/droplets/details/features/); Vultr describes Regular Performance as shared Intel CPU on its [pricing page](https://www.vultr.com/pricing/#cloud-compute).

**Use a different comparison for these workloads:**

- **Immich with machine learning:** current [official requirements](https://docs.immich.app/install/requirements/) call for 6 GB / 2 cores minimum and recommend 8 GB / 4 cores. Its 4 GB exception requires ML disabled in the application. None of these is our default ML-enabled Immich choice.
- **A 2 TB photo or video library:** the included disks below are far smaller than the library, even before generated files, OS space and backups. Quote suitable primary storage and a separate backup; do not treat object storage as a database disk.
- **Hardware video conversion:** confirm a compatible GPU or media device and access to it. Extra shared vCPUs do not establish hardware transcoding. Consult [Jellyfin's hardware guidance](https://jellyfin.org/docs/general/administration/hardware-selection/); software conversion also needs workload-specific measurements.
- **Heavy OCR, CI builds, federated chat or many concurrent jobs:** estimate those workloads separately. A count of users does not establish the number of simultaneous jobs.

## Four public plans to compare

All rows are **unmanaged Linux server plans**: you handle updates, security, applications and recovery. Disk is the advertised included capacity, not free space after installation. Keep the provider's units: DigitalOcean lists GiB; Vultr lists GB and TB. Those labels are not interchangeable.

| Exact public plan | RAM / shared vCPU | Included SSD | Monthly compute cap, USD |
|---|---|---|---|
| [DigitalOcean Basic — Regular, 2 GiB / 1 vCPU](https://www.digitalocean.com/pricing/droplets) | 2 GiB / 1 | 50 GiB | $12.00 |
| [DigitalOcean Basic — Regular, 4 GiB / 2 vCPUs](https://www.digitalocean.com/pricing/droplets) | 4 GiB / 2 | 80 GiB | $24.00 |
| [Vultr Cloud Compute — Regular Performance, 2 GB / 1 vCPU](https://www.vultr.com/pricing/#cloud-compute) | 2 GB / 1 | 55 GB | $10.00 catalogue; regional quote unknown |
| [Vultr Cloud Compute — Regular Performance, 4 GB / 2 vCPUs](https://www.vultr.com/pricing/#cloud-compute) | 4 GB / 2 | 80 GB | $20.00 catalogue; regional quote unknown |

For the same listed memory tier, Vultr's catalogue compute cap is lower. That is a price observation, not proof of a lower complete bill or better service. At 2 GB, also compare the different disk allowances. At 4 GB, compare transfer and your recovery design. Check latency from your users, available stock, support and exit procedures before deciding.

### Network and address terms

| Plan | Listed full-month outbound allowance | Address / overage condition |
|---|---|---|
| DigitalOcean 2 GiB | 2,000 GiB | One public IPv4 included in this bundled plan; extra services separate |
| DigitalOcean 4 GiB | 4,000 GiB | Same bundled IPv4 condition |
| Vultr 2 GB | 2.00 TB | Standard public-network plan, not the small IPv6-only offer; confirm IPv4 charge in regional quote |
| Vultr 4 GB | 3.00 TB | Same address check; final address charge not independently quoted |

DigitalOcean charges **$0.01/GiB** for outbound traffic above the team's accrued pool; inbound is free. Allowance accrues while a Droplet exists, so a short test does not receive a whole month's allowance. See its [bandwidth rules](https://docs.digitalocean.com/platform/billing/bandwidth/). Vultr states **$0.01/GB** outbound overage in its [Cloud Compute FAQ](https://www.vultr.com/resources/faq/#rpc_billing); confirm the accrued allowance and public-network rules for your chosen location. Backup uploads and restores need their own traffic budget.

### First month, later months and stopping

These rows use ongoing usage rates, not an introductory multi-year discount. At the checked rates, a full month's compute cap is the same for the first and later full months; future prices and your final quote can change. No annual prepayment is assumed, and the billing minimum is not a requirement to keep a server for a month. Setup or account-specific fees have not been independently quoted.

- **DigitalOcean bundled Basic:** [per-second billing](https://docs.digitalocean.com/products/droplets/details/pricing/), with a minimum of 60 seconds or $0.01, whichever is higher; capped at 672 hours per monthly cycle. The displayed hourly equivalents for these two rows are $0.01786 and $0.03571. This cap does not describe its separate v5 configurations.
- **Vultr Regular Performance:** [hourly billing](https://www.vultr.com/resources/faq/#billingoverview), one-hour minimum and a 672-hour monthly cap. The two catalogue hourly rates are $0.015 and $0.03. This is not the billing model for every Vultr product.

Both providers continue charging for an instance that is merely powered off. Before destroying a server to stop its compute charge, export what you need and test a restore. Check separate volumes, stored backups and other resources for continuing charges.

## What is still missing from the bill?

**The complete monthly total is unknown for all four rows.** The compute caps include the listed disk and transfer allowance; do not charge those items again. Neither the table nor an optional server image backup prices an independent recovery plan.

| Cost item | How to account for it |
|---|---|
| Extra primary storage | Add only capacity you actually buy beyond the included disk. DigitalOcean [volumes](https://docs.digitalocean.com/products/volumes/details/pricing/) cost $0.10/GiB/month, billed hourly, from 1 GiB. An extra 20 GiB would be $2.00/month before tax. Vultr extra-volume quote: unknown here. |
| Independent backup | Choose a destination outside the server's failure domain, capacity, versions and retention. Price storage, requests, upload/restore traffic and any minimum charge. No independent destination or retained capacity is quoted here: **unknown**. |
| Extra network / addresses | Add expected transfer overage and any extra or reserved address charges. A provider's allowance is not unlimited transfer. Usage-dependent amount: **unknown**. |
| Domain and licences | Add a domain's renewal rate if you need one and any paid software or control panel. Quote these separately; a Linux VPS rate does not establish their cost. **Unknown until selected.** |
| Tax and payment costs | Check billing location and applicable rules, not just server location. [DigitalOcean taxes](https://docs.digitalocean.com/platform/billing/taxes/) and [Vultr taxes](https://docs.vultr.com/support/platform/billing/does-vultr-collect-vat-or-sales-tax) are account-dependent. Tax and currency/payment charges: **unknown**. |
| Management | Your own maintenance and restore time is still a cost. Paid administration is not included in these self-managed plans; if required, its quote is **unknown**. |

For a stack that fits the included disk, **no extra volume is selected** in this comparison. That is not a promise that future growth is free. Confirm a $0 extra-storage line only after checking your own capacity. An empty quote is unknown, not zero.

### Optional provider backups: a partial subtotal

For a full month at the catalogue rates, the following arithmetic adds only the specified server backup. It excludes the missing items above.

| Plan | Optional server backup | Compute + that backup, USD/month |
|---|---|---|
| DigitalOcean 2 GiB | Weekly percentage plan: $2.40 | **$14.40 partial subtotal** |
| DigitalOcean 4 GiB | Weekly percentage plan: $4.80 | **$28.80 partial subtotal** |
| Vultr 2 GB | Automatic backup: $2.00 at catalogue rate | **$12.00 illustrative subtotal**; regional quote unknown |
| Vultr 4 GB | Automatic backup: $4.00 at catalogue rate | **$24.00 illustrative subtotal**; regional quote unknown |

[DigitalOcean's weekly percentage backup](https://docs.digitalocean.com/products/backups/details/pricing/) adds 20% of Droplet cost; its daily percentage option is 30%, and usage-based plans use different rates. [Vultr automatic backup](https://docs.vultr.com/vps-automatic-backups) adds 20%, stores the two latest backups in the same datacenter on separate storage, and excludes attached block volumes. Database consistency also needs attention. A same-provider server image is not automatically an independent off-site copy, and a weekly schedule may lose more changes than you can accept. Select recovery frequency and retention before treating either option as sufficient.

## Take the comparison to your own plan

1. Open the [planner](/tools/selfhost-planner/), choose your actual apps and library, and inspect the capacity explanation. If your workload falls outside this guide, return to sizing before shopping.
2. Confirm the exact region, architecture, plan and available capacity on the official order page. Record its quote date, first-period charge, ongoing rate, minimum billing unit and cancellation terms. Resolve the unknown regional and address charges before choosing on price.
3. Put the **server quote** in the server field. Put **additional** primary storage, independent backup and other recurring quotes in their respective fields. If your server quote already bundles a chosen backup, do not add that same backup again; still account for a separate recovery copy if required.
4. Keep missing quotes blank. Enter 0 only for a confirmed zero cost. Use [the whole-cost worksheet](/posts/self-hosting-vs-cloud-cost/) for maintenance and home-server alternatives. After deployment, revisit actual disk use, busy periods, the first invoice and a restore test.

A useful next step is a complete quote and a recovery procedure you can execute. These four compute prices alone do not establish a complete monthly budget.
