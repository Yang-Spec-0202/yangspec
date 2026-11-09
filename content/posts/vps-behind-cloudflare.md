---
title: "在 VPS 上跑一个小服务，前面放 Cloudflare"
date: 2026-11-09
description: "用一台小 VPS 和 Cloudflare 反代，把自托管服务挂到域名上：选型、DNS、反代与证书的实操笔记。"
---

这是一篇实操笔记，不是选购排行。假设你已经有一台能 SSH 登录的 Linux VPS，以及一个托管在 Cloudflare 的域名。目标只有一个：让外面访问 `app.example.com` 时，流量先过 Cloudflare，再落到你机器上的某个 HTTP 服务。

下文出现的厂商链接目前指向官网。我加入对应联盟计划后，会把 `hugo.toml` 里的 `[params.affiliates]` 换成带推荐码的地址。**本页含推荐链接意向；是否下单、选哪家，以你自己的需求和对方官网当时条款为准。**

## 先想清楚跑什么

自托管最容易踩的坑，不是装不上，而是装完之后不知道自己要维护什么。动手前先写下三件事：

1. 这个服务对谁开放：只有自己，还是也给朋友用。
2. 丢了数据能不能接受：能不能接受重装；若不能，备份落在哪里。
3. 机器挂了你怎么知道：至少要有一种你平时会看到的告警方式，哪怕只是自己定时 curl。

内存和磁盘按官方文档留余量。照片库、媒体转码和文档同步不是同一类负载；不要用“别人 1 GB 也能跑”当依据。

## 机器怎么选

我自己用过国内可直连的线路机，也试过常见的海外云。选型时我只看这几项，不看营销口号：

| 要核对的 | 为什么 |
| --- | --- |
| 机房位置与到你网络的延迟 | 自己用的话，延迟比标称带宽更影响体感 |
| 内存、磁盘是否可升级 | 装完才发现不够，迁移成本通常高于升级 |
| 流量与超售规则 | 看清楚含多少流量、超了怎么计费 |
| 续费价是否等于首年价 | 把促销价和续费价分开记 |
| 快照 / 备份是否另计 | 同机快照不等于异地备份 |

需要买机器或换机器时，可以先看这几家的公开页面（顺序不代表推荐）：

- {{< aff liuliuyun "六六云" >}}：国内用户常买的线路机，中文面板；我目前也在用。
- {{< aff bandwagon "搬瓦工（BandwagonHost）" >}}：老牌海外 VPS，中文社区资料多。
- {{< aff racknerd "RackNerd" >}}：常有促销的 KVM VPS。
- {{< aff vultr "Vultr" >}}：按小时计费，适合先试再决定是否长留。

域名如果还没有，{{< aff namecheap "Namecheap" >}} 和 Porkbun 都是常见选择；解析最终仍建议放进 Cloudflare，方便开代理与证书。

## 拓扑

最简单、也最不容易把自己绕晕的结构是：

```text
访客 → Cloudflare（代理开启）→ 你的 VPS:443 → 本机反代 → 127.0.0.1:应用端口
```

要点：

- DNS 记录开橙色云（Proxied），让访客只看到 Cloudflare 的地址。
- 源站只允许 Cloudflare 的 IP 段访问 80/443，或至少不要把应用端口直接暴露到公网。
- 应用监听在 `127.0.0.1`，由 Caddy / Nginx / Traefik 之一反代。

## 最小步骤

下面用 Caddy 举例，因为它默认处理 HTTPS。你也可以换成自己熟悉的反代。

### 1. DNS

在 Cloudflare 给子域加一条 A 或 AAAA，指向 VPS 公网 IP，代理状态设为 Proxied。

### 2. 防火墙

只放行 SSH（建议改端口或加密钥登录）、以及 443。若源站证书交给 Cloudflare 的 Full（strict），还要保证源站能出示有效证书；用 Caddy 向 Let's Encrypt 要证时，需要 80 也短暂可达，或改用 DNS-01 / Cloudflare Origin Certificate。

更省事的做法：在 Cloudflare 签发 [Origin CA 证书](https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/)，装到 Caddy / Nginx，SSL 模式选 Full (strict)。这样源站不依赖公网 80 挑战。

### 3. 反代

假设应用已经在 `127.0.0.1:8080` 监听，Caddyfile 可以是：

```caddy
app.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

若使用 Origin CA，按 Caddy 文档挂上证书与密钥路径即可。

### 4. 验证

- 浏览器打开 `https://app.example.com`，确认证书由 Cloudflare 出示。
- 在 VPS 上 `curl -I http://127.0.0.1:8080`，确认本机服务正常。
- 用手机流量（非家里的 Wi-Fi）再访问一次，避免只测到了内网幻觉。

## 别忘了的三件事

1. **备份**：至少把配置和应用数据定期拷到另一台机器或对象存储；同盘快照不够。
2. **更新**：系统与容器镜像要有固定的更新节奏；“以后再说”通常等于不更新。
3. **退出路径**：记下如何导出数据、如何改 DNS 指向别处。服务商可以换，数据应该跟得走。

## 和这个站的关系

本站本身跑在 Cloudflare Pages 上，不占用 VPS。VPS 更适合放需要长驻进程、本地磁盘或特定网络环境的东西。两者可以共用同一个域名：Pages 管静态站，VPS 管子域上的应用。

若你卡在某一步，欢迎写邮件到[联系页]({{< relref "/contact" >}})里的地址。若需要我远程帮你搭，也可以看[服务]({{< relref "/services" >}})页。

占位说明（给站长自己看）：替换联盟链接时，改 `hugo.toml` 的 `params.affiliates.liuliuyun` / `bandwagon` / `racknerd` / `vultr` / `namecheap`，对应占位名 `AFFILIATE_666CLOUDS`、`AFFILIATE_BANDWAGON`、`AFFILIATE_RACKNERD`、`AFFILIATE_VULTR`、`AFFILIATE_NAMECHEAP`。
