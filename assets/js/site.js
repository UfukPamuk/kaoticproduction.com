/* Kaotic Production site: small progressive enhancements, no tracking.
   Everything works without this file (links, poster images, details/summary). */
(function () {
  "use strict";
  var doc = document;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- header: solid after scrolling, mobile menu ---- */
  var header = doc.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 24); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    var btn = header.querySelector(".menu-btn");
    var menu = header.querySelector(".mobile-nav");
    if (btn && menu) {
      btn.addEventListener("click", function () {
        var open = !menu.classList.contains("open");
        menu.classList.toggle("open", open);
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) header.classList.add("scrolled");
      });
      menu.addEventListener("click", function (e) {
        if (e.target.closest("a")) { menu.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }
      });
    }
  }

  /* ---- language hint: an English page opened by a Turkish browser ---- */
  var hint = doc.querySelector(".lang-hint");
  if (hint && doc.documentElement.lang === "en") {
    var dismissed = false;
    try { dismissed = sessionStorage.getItem("langHint") === "0"; } catch (e) {}
    var langs = navigator.languages || [navigator.language || ""];
    var wantsTr = false;
    for (var i = 0; i < langs.length && i < 2; i++) { if (/^tr\b/i.test(langs[i])) wantsTr = true; }
    if (wantsTr && !dismissed) hint.classList.add("show");
    var x = hint.querySelector("button");
    if (x) x.addEventListener("click", function () {
      hint.classList.remove("show");
      try { sessionStorage.setItem("langHint", "0"); } catch (e) {}
    });
  }

  /* ---- hero loop: muted, starts only when motion is welcome ---- */
  var video = doc.querySelector("video[data-hero]");
  if (video) {
    var ctl = doc.querySelector(".media-ctl");
    var label = ctl && ctl.querySelector(".lbl");
    var saveData = navigator.connection && navigator.connection.saveData;
    var userPaused = false;
    var setCtl = function (playing) {
      if (!ctl) return;
      ctl.hidden = false;
      ctl.setAttribute("aria-pressed", playing ? "false" : "true");
      var txt = playing ? ctl.dataset.pause : ctl.dataset.play;
      if (label) label.textContent = txt;
      ctl.title = txt;
      ctl.querySelector(".i-pause").style.display = playing ? "" : "none";
      ctl.querySelector(".i-play").style.display = playing ? "none" : "";
    };
    var load = function () {
      if (video.dataset.loaded) return;
      video.dataset.loaded = "1";
      // 1440p when the screen has >= 2200 device pixels across, 1080p from
      // 1200 css px, 720p on phones and tablets
      var px = window.innerWidth * (window.devicePixelRatio || 1);
      var base = window.innerWidth < 1200 ? video.dataset.small
        : (px >= 2200 && video.dataset.xl ? video.dataset.xl : video.dataset.large);
      [["webm", "video/webm"], ["mp4", "video/mp4"]].forEach(function (t) {
        var s = doc.createElement("source");
        s.src = base + "." + t[0];
        s.type = t[1];
        video.appendChild(s);
      });
      video.load();
    };
    var play = function () {
      load();
      var p = video.play();
      if (p && p.then) p.then(function () { video.classList.add("playing"); setCtl(true); }, function () { setCtl(false); });
      else { video.classList.add("playing"); setCtl(true); }
    };
    video.addEventListener("playing", function () { video.classList.add("playing"); setCtl(true); });
    if (!reduce && !saveData) play(); else setCtl(false);
    if (ctl) ctl.addEventListener("click", function () {
      if (video.paused) { userPaused = false; play(); }
      else { userPaused = true; video.pause(); setCtl(false); }
    });
    // pause while scrolled away (saves battery), resume if the user did not pause
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!video.dataset.loaded) return;
          if (!e.isIntersecting) video.pause();
          else if (!userPaused && !reduce) video.play().catch(function () {});
        });
      }, { threshold: 0.1 }).observe(video);
    }
  }

  /* ---- YouTube facade: nothing is requested from YouTube before the click ---- */
  doc.querySelectorAll(".trailer[data-yt]").forEach(function (box) {
    var b = box.querySelector("button");
    if (!b) return;
    b.addEventListener("click", function () {
      var f = doc.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(box.dataset.yt) +
        "?autoplay=1&rel=0&modestbranding=1&hl=" + (doc.documentElement.lang || "en");
      f.title = box.dataset.title || "Trailer";
      f.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen";
      f.allowFullscreen = true;
      f.referrerPolicy = "strict-origin-when-cross-origin";
      box.innerHTML = "";
      box.appendChild(f);
      f.focus();
    });
  });

  /* ---- gallery lightbox (keyboard, buttons, swipe) ---- */
  var links = Array.prototype.slice.call(doc.querySelectorAll("[data-lightbox] a"));
  var dlg = doc.querySelector("dialog.lightbox");
  if (links.length && dlg && typeof dlg.showModal === "function") {
    var img = dlg.querySelector(".stage img");
    var cap = dlg.querySelector(".lb-cap");
    var count = dlg.querySelector(".lb-count");
    var idx = 0, lastFocus = null;
    var show = function (n) {
      idx = (n + links.length) % links.length;
      var a = links[idx];
      var t = a.querySelector("img");
      img.src = a.dataset.full || a.href;
      img.alt = t ? t.alt : "";
      cap.textContent = t ? t.alt : "";
      count.textContent = (idx + 1) + " / " + links.length;
      // warm the neighbours
      [idx + 1, idx - 1].forEach(function (k) {
        var l = links[(k + links.length) % links.length];
        var p = new Image(); p.src = l.dataset.full || l.href;
      });
    };
    links.forEach(function (a, n) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        lastFocus = a;
        show(n);
        dlg.showModal();
        doc.body.style.overflow = "hidden";
        dlg.querySelector(".close").focus();
      });
    });
    dlg.querySelector(".prev").addEventListener("click", function () { show(idx - 1); });
    dlg.querySelector(".next").addEventListener("click", function () { show(idx + 1); });
    dlg.querySelector(".close").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("close", function () { doc.body.style.overflow = ""; if (lastFocus) lastFocus.focus(); });
    dlg.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); show(idx + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); show(idx - 1); }
      else if (e.key === "Home") { e.preventDefault(); show(0); }
      else if (e.key === "End") { e.preventDefault(); show(links.length - 1); }
    });
    // click on the dark area closes
    dlg.querySelector(".stage").addEventListener("click", function (e) { if (e.target === e.currentTarget) dlg.close(); });
    // swipe
    var sx = null, sy = null;
    dlg.addEventListener("touchstart", function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; }, { passive: true });
    dlg.addEventListener("touchend", function (e) {
      if (sx === null) return;
      var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) show(idx + (dx < 0 ? 1 : -1));
      else if (dy > 90 && Math.abs(dy) > Math.abs(dx) * 1.5) dlg.close();
      sx = sy = null;
    }, { passive: true });
  }
})();
