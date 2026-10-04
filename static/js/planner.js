(function () {
  var AFFILIATE = {
    hetzner: "https://www.hetzner.com/cloud",
    contabo: "https://contabo.com/en/vps/",
    digitalocean: "https://www.digitalocean.com/pricing",
    vultr: "https://www.vultr.com/pricing/",
    hostinger: "https://www.hostinger.com/vps-hosting",
    linode: "https://www.linode.com/pricing/"
  };

  var APPS = [
    { id: "jellyfin", name: "Jellyfin", desc: "Media streaming server", ram: 2048, cpu: 0.5, disk: 10, media: true },
    { id: "plex", name: "Plex", desc: "Media server (Plex Pass features)", ram: 2048, cpu: 0.5, disk: 10, media: true },
    { id: "immich", name: "Immich", desc: "Google Photos replacement", ram: 4096, cpu: 1.0, disk: 20, media: true },
    { id: "photoprism", name: "PhotoPrism", desc: "AI photo management", ram: 2048, cpu: 1.0, disk: 20, media: true },
    { id: "nextcloud", name: "Nextcloud", desc: "Files, calendar, office suite", ram: 1536, cpu: 0.5, disk: 30 },
    { id: "paperless", name: "Paperless-ngx", desc: "Document archive with OCR", ram: 2048, cpu: 1.0, disk: 20 },
    { id: "vaultwarden", name: "Vaultwarden", desc: "Password manager (Bitwarden API)", ram: 256, cpu: 0.25, disk: 2 },
    { id: "homeassistant", name: "Home Assistant", desc: "Smart home automation", ram: 1024, cpu: 0.25, disk: 16 },
    { id: "n8n", name: "n8n", desc: "Workflow automation", ram: 1024, cpu: 0.5, disk: 10 },
    { id: "matrix", name: "Matrix (Synapse)", desc: "Self-hosted chat", ram: 2048, cpu: 1.0, disk: 20 },
    { id: "forgejo", name: "Forgejo / Gitea", desc: "Self-hosted Git", ram: 512, cpu: 0.25, disk: 10 },
    { id: "syncthing", name: "Syncthing", desc: "Peer-to-peer file sync", ram: 512, cpu: 0.25, disk: 10 },
    { id: "grafana", name: "Grafana + Prometheus", desc: "Metrics and dashboards", ram: 2048, cpu: 0.5, disk: 20 },
    { id: "minio", name: "MinIO", desc: "S3-compatible object storage", ram: 1024, cpu: 0.5, disk: 20 },
    { id: "adguard", name: "AdGuard Home / Pi-hole", desc: "Network-wide ad blocking", ram: 256, cpu: 0.25, disk: 2 },
    { id: "uptimekuma", name: "Uptime Kuma", desc: "Uptime monitoring and alerts", ram: 256, cpu: 0.25, disk: 2 },
    { id: "ntfy", name: "ntfy", desc: "Self-hosted push notifications", ram: 256, cpu: 0.25, disk: 2 },
    { id: "wallos", name: "Wallos / Actual Budget", desc: "Budget and subscription tracking", ram: 256, cpu: 0.25, disk: 2 }
  ];

  var TIERS = [
    { ram: 1024, vcpu: 1, label: "1 GB RAM / 1 vCPU", price: 5 },
    { ram: 2048, vcpu: 1, label: "2 GB RAM / 1 vCPU", price: 7 },
    { ram: 4096, vcpu: 2, label: "4 GB RAM / 2 vCPU", price: 12 },
    { ram: 8192, vcpu: 4, label: "8 GB RAM / 4 vCPU", price: 24 },
    { ram: 16384, vcpu: 6, label: "16 GB RAM / 6 vCPU", price: 48 },
    { ram: 32768, vcpu: 8, label: "32 GB RAM / 8 vCPU", price: 90 }
  ];

  function providersFor(ram) {
    if (ram <= 2048) {
      return [
        { name: "Hetzner Cloud", meta: "Best price-to-performance in the EU", url: AFFILIATE.hetzner },
        { name: "Vultr", meta: "Fast global deployment, US locations", url: AFFILIATE.vultr },
        { name: "DigitalOcean", meta: "Best docs and beginner tooling", url: AFFILIATE.digitalocean }
      ];
    }
    if (ram <= 8192) {
      return [
        { name: "Hetzner Cloud", meta: "Great value for 4-8 GB workloads", url: AFFILIATE.hetzner },
        { name: "Contabo", meta: "Most RAM per dollar", url: AFFILIATE.contabo },
        { name: "Hostinger VPS", meta: "Beginner-friendly with AI assistant", url: AFFILIATE.hostinger }
      ];
    }
    return [
      { name: "Contabo", meta: "Cheapest large-RAM VPS", url: AFFILIATE.contabo },
      { name: "Hetzner Cloud", meta: "Strong CPU for the money", url: AFFILIATE.hetzner },
      { name: "Akamai / Linode", meta: "Reliable at scale", url: AFFILIATE.linode }
    ];
  }

  function fmtGB(gb) {
    if (gb >= 1024) return (gb / 1024).toFixed(gb % 1024 === 0 ? 0 : 1) + " TB";
    return gb + " GB";
  }

  var selected = {};
  var appGrid = document.getElementById("appGrid");
  var resultEl = document.getElementById("result");
  if (!appGrid || !resultEl) return;

  APPS.forEach(function (app) {
    var label = document.createElement("label");
    label.className = "app-item";
    label.innerHTML =
      '<input type="checkbox" data-app="' + app.id + '">' +
      '<span><span class="app-name">' + app.name + '</span><br>' +
      '<span class="app-desc">' + app.desc + '</span></span>';
    appGrid.appendChild(label);
  });

  var usersEl = document.getElementById("users");
  var mediaEl = document.getElementById("media");
  var mediaWrap = document.getElementById("mediaWrap");
  var transcodeEl = document.getElementById("transcode");

  function hasMediaApp() {
    return APPS.some(function (a) { return a.media && selected[a.id]; });
  }

  function compute() {
    var users = parseInt(usersEl.value, 10) || 1;
    var mediaTb = parseFloat(mediaEl.value) || 0;
    var transcode = transcodeEl.checked;

    var picked = APPS.filter(function (a) { return selected[a.id]; });

    if (picked.length === 0) {
      resultEl.innerHTML = '<p class="shp-sub" style="margin:0">Select at least one app above to see your recommended server.</p>';
      return;
    }

    var appScale = Math.min(1 + (users - 1) * 0.08, 2.0);

    var ram = 512;
    var cpu = 0;
    var disk = 0;

    picked.forEach(function (a) {
      ram += a.ram * appScale;
      cpu += a.cpu * appScale;
      disk += a.disk;
    });

    if (transcode && hasMediaApp()) {
      ram += 1024;
      cpu += 1.5;
    }

    disk += mediaTb * 1024;
    disk = Math.ceil(disk * 1.15);

    var cpuNeed = Math.max(1, Math.ceil(cpu));
    var ramNeed = Math.ceil(ram / 256) * 256;

    var tier = TIERS.find(function (t) { return t.ram >= ramNeed && t.vcpu >= cpuNeed; });
    var overkill = false;
    if (!tier) {
      tier = TIERS[TIERS.length - 1];
      overkill = true;
    }

    var providers = providersFor(tier.ram);
    var providerHtml = providers.map(function (p) {
      return '<div class="provider"><div><div class="p-name">' + p.name + '</div>' +
        '<div class="p-meta">' + p.meta + '</div></div>' +
        '<a class="shp-btn" href="' + p.url + '" target="_blank" rel="noopener nofollow sponsored">View plans</a></div>';
    }).join("");

    resultEl.innerHTML =
      '<p class="shp-headline">Recommended: ' + tier.label + '</p>' +
      '<p class="shp-sub">Based on ' + picked.length + ' app' + (picked.length > 1 ? 's' : '') +
      ', ' + users + ' user' + (users > 1 ? 's' : '') +
      (mediaTb > 0 ? ', ' + mediaTb + ' TB storage' : '') +
      (transcode ? ', hardware transcoding' : '') + '.</p>' +
      '<div class="stat-row">' +
        '<div class="stat"><div class="num">' + (tier.ram >= 1024 ? (tier.ram / 1024) + " GB" : tier.ram + " MB") + '</div><div class="lbl">RAM</div></div>' +
        '<div class="stat"><div class="num">' + tier.vcpu + '</div><div class="lbl">vCPU cores</div></div>' +
        '<div class="stat"><div class="num">' + fmtGB(disk) + '</div><div class="lbl">Disk (min.)</div></div>' +
      '</div>' +
      '<p class="shp-sub" style="margin-bottom:10px">Typical monthly price: <strong>~$' + tier.price + '/mo</strong>. Where to buy (prices approximate, varies by promo and region):</p>' +
      '<div class="provider-list">' + providerHtml + '</div>' +
      '<p class="shp-note">' + (overkill
        ? 'This workload is larger than a typical shared VPS. Consider a dedicated server or a homelab box.'
        : 'This is a baseline. Add 25-50% headroom if you expect heavy transcoding, big photo libraries, or many concurrent users.') +
      ' Storage figures exclude operating-system backups; plan a separate backup target.</p>' +
      '<p class="shp-note">Some links above may be affiliate links. They cost you nothing extra and help support this free tool.</p>';
  }

  appGrid.addEventListener("change", function (e) {
    if (e.target && e.target.dataset && e.target.dataset.app) {
      selected[e.target.dataset.app] = e.target.checked;
      if (mediaWrap) {
        mediaWrap.style.opacity = hasMediaApp() ? "1" : "0.5";
      }
      compute();
    }
  });

  [usersEl, mediaEl, transcodeEl].forEach(function (el) {
    if (el) { el.addEventListener("input", compute); el.addEventListener("change", compute); }
  });

  compute();
})();
