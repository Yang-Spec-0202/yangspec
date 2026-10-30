---
title: "Choosing a VPS for Self-Hosting: What to Check Before Buying"
shortTitle: "Choose a host, not a headline price."
guideLabel: "BUYING / FIELD GUIDE"
date: 2026-10-04
lastmod: 2026-10-04
description: "A practical checklist for capacity, location, usable storage, network limits, renewals and a separate backup."
summary: "Compare the plan that fits your workload, including storage and renewal costs, without relying on an unverified provider ranking."
tags: ["VPS", "self-hosting", "hosting"]
---

**Choose the smallest plan that fits your verified requirements and your recovery plan.** The cheapest headline rate is not enough to make a decision. Region, usable storage, network limits, renewal, hardware access and backup options can change the real cost.

This page is a buying checklist. We have not benchmarked these providers or established a universal “best” ranking. Pricing references below are ordinary links in this version; they are not verified matches for a planner result. Any future affiliate link will be disclosed and will not determine suitability.

## Take a capacity target with you

Use the [Self-Hosting Planner](/tools/selfhost-planner/) to organize your apps, library and a separate backup. Read the source conditions for photo indexing and video playback. The number of users is not the number of simultaneous transcodes or OCR jobs.

A shared vCPU count does not guarantee a particular throughput. Match architecture, device support and application requirements before comparing prices.

## Seven things to put beside the price

1. **Location and connectivity.** Choose an available location suitable for your users and test latency where possible. Check IPv4/IPv6 and the cost of addresses you need.
2. **Memory and CPU terms.** Check whether resources are shared or dedicated, the architecture, fair-use conditions and how upgrades work.
3. **Usable primary storage.** Confirm included disk, additional volumes, minimum billing sizes, filesystem compatibility and expansion limits. Object storage is not interchangeable with a database's local disk.
4. **Transfer and egress.** Read included allowances, overage rates, port limits and any difference between traffic types or locations.
5. **The actual renewal bill.** Record currency, tax, billing interval, minimum term, setup fees and the price after any promotion.
6. **Backup and recovery.** Quote a separate destination and sufficient retention. Check restore procedure and time; a snapshot in the same failure domain may not be enough.
7. **Support and exit.** Read current support, cancellation, export and acceptable-use terms. An SLA credit is not the same as your application remaining available.

## Current pricing references

Visit a provider's own pricing page for the exact plan and location. Record the quote date and conditions. These links help you gather quotes; listing a provider does not establish reliability, value or support for your particular workload.

| Provider | Official reference | What to record |
|---|---|---|
| Hetzner Cloud | [Cloud plans](https://www.hetzner.com/cloud/) | Location, architecture, included disk/transfer, extra volumes and addresses |
| Contabo | [VPS plans](https://contabo.com/en/vps/) | Exact plan, location, contract period, setup and renewal terms |
| DigitalOcean | [Pricing](https://www.digitalocean.com/pricing) | Droplet class, additional storage, backups and outbound transfer |
| Vultr | [Pricing](https://www.vultr.com/pricing/) | Product class, location, storage, transfer and addresses |
| Hostinger | [VPS plans](https://www.hostinger.com/vps-hosting) | Initial term, renewal bill, storage, transfer and management scope |

We intentionally do not reuse generic $5/$12/$24 compute estimates as total costs for large libraries. Put the complete quote into the planner and keep unknown costs visible.

## When a standard VPS needs another look

For hardware video conversion, confirm a compatible device and access to it; a larger CPU-only plan does not establish GPU support. For terabytes of photos or films, compare attached volumes with storage-focused, dedicated or home-server options. Verify a photo app's database and filesystem requirements as well.

A small home machine still needs electricity, backups, updates and enough upload bandwidth for remote access. Compare it using [the full-cost worksheet](/posts/self-hosting-vs-cloud-cost/), rather than assuming either location is always cheaper.

## Keep a record you can revisit

Save the quoted plan name, location, date, recurring bill, resource limits and backup procedure. After setup, compare the first busy week and the first bill with your plan. That evidence is more useful than an unqualified “best provider” label.
