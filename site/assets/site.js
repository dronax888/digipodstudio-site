/* Digipod Studio — site behaviour. No dependencies. */
(function () {
  'use strict';
  var ROOT = document.documentElement.getAttribute('data-root') || '/';
  var EXT = document.documentElement.getAttribute('data-ext') || '';
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var href = function (path) { return ROOT + path + EXT; };
  var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.documentElement.classList.add('js');

  /* ---------- toast ---------- */
  var toastEl;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'toast'; toastEl.setAttribute('role', 'status'); document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('show');
    clearTimeout(toast.t); toast.t = setTimeout(function () { toastEl.classList.remove('show'); }, 2200);
  }

  /* ---------- mobile menu ---------- */
  var mb = $('.menu-btn'), nav = $('.nav');
  if (mb && nav) mb.addEventListener('click', function () {
    var open = nav.classList.toggle('open'); mb.setAttribute('aria-expanded', open);
  });

  /* ---------- product index (lazy) ---------- */
  var products = null, loading = null;
  function getProducts() {
    if (products) return Promise.resolve(products);
    if (!loading) loading = fetch(ROOT + 'assets/products.json').then(function (r) { return r.json(); }).then(function (d) { products = d; return d; });
    return loading;
  }

  /* ---------- party list (favourites) ---------- */
  var KEY = 'digipod-party-list';
  function readList() { try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; } }
  function writeList(l) { try { localStorage.setItem(KEY, JSON.stringify(l)); } catch (e) {} updateCount(); }
  function updateCount() {
    var n = readList().length;
    $$('.count').forEach(function (c) { c.textContent = n; c.hidden = n === 0; });
  }
  function syncFavs() {
    var l = readList();
    $$('.fav').forEach(function (b) {
      var on = l.indexOf(b.dataset.id) > -1;
      b.setAttribute('aria-pressed', on);
      b.setAttribute('aria-label', (on ? 'Remove from' : 'Save to') + ' party list');
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.fav'); if (!b) return;
    e.preventDefault();
    var l = readList(), id = b.dataset.id, i = l.indexOf(id);
    if (i > -1) { l.splice(i, 1); toast('Removed from your party list'); } else { l.push(id); toast('Saved to your party list'); }
    writeList(l); syncFavs();
    if (document.body.dataset.page === 'party-list') renderParty();
  });
  updateCount(); syncFavs();

  function cardHTML(p) {
    return '<li class="card"><button class="fav" type="button" data-id="' + p.id + '" aria-pressed="false" aria-label="Save to party list">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 20.5s-7.5-4.6-9.3-9.1C1.4 8 3.5 4.5 7 4.5c2 0 3.6 1.1 5 2.9 1.4-1.8 3-2.9 5-2.9 3.5 0 5.6 3.5 4.3 6.9-1.8 4.5-9.3 9.1-9.3 9.1z"/></svg></button>' +
      '<a class="cover" href="' + href('templates/' + p.slug + '/') + '"><img loading="lazy" src="' + esc(p.img) + '" alt="' + esc(p.name) + '" width="340" height="270"></a>' +
      '<h3><a href="' + href('templates/' + p.slug + '/') + '">' + esc(p.name) + '</a></h3>' +
      '<div class="meta"><span>' + esc(p.type_name) + '</span><span class="price">$' + p.price.toFixed(2) + '</span></div></li>';
  }

  /* party list page */
  function renderParty() {
    var box = $('#party'); if (!box) return;
    var q = new URLSearchParams(location.search).get('ids');
    var shared = q ? q.split(',').filter(Boolean) : null;
    var ids = shared || readList();
    getProducts().then(function (all) {
      var pick = ids.map(function (id) { return all.filter(function (p) { return p.id === id; })[0]; }).filter(Boolean);
      $('#party-title').textContent = shared ? 'A party list shared with you' : 'Your party list';
      if (!pick.length) {
        box.innerHTML = '<div class="empty party-empty"><p><strong>Nothing saved yet.</strong></p><p>Tap the heart on any template to keep it here, then share the list with your quinceañera, partner or planner.</p><a class="btn btn-primary" href="' + href('shop/') + '">Browse templates</a></div>';
        $('#party-share').hidden = true; return;
      }
      var total = pick.reduce(function (s, p) { return s + p.price; }, 0);
      $('#party-sum').textContent = pick.length + (pick.length === 1 ? ' template' : ' templates') + ', $' + total.toFixed(2) + ' in total on Etsy';
      box.innerHTML = '<ul class="grid" style="list-style:none;padding:0;margin:0">' + pick.map(cardHTML).join('') + '</ul>';
      $('#party-share').hidden = false;
      if (shared) {
        var keep = $('#party-keep'); keep.hidden = false;
        keep.onclick = function () { var l = readList(); shared.forEach(function (id) { if (l.indexOf(id) < 0) l.push(id); }); writeList(l); toast('Added to your party list'); };
      }
      syncFavs();
    });
  }
  if (document.body.dataset.page === 'party-list') {
    renderParty();
    var share = $('#party-copy');
    if (share) share.addEventListener('click', function () {
      var ids = (new URLSearchParams(location.search).get('ids') || readList().join(','));
      var url = location.origin + location.pathname + '?ids=' + ids;
      if (navigator.share) { navigator.share({ title: 'Our party list from Digipod Studio', url: url }).catch(function () {}); return; }
      (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { toast('Link copied. Send it to anyone.'); }, function () { prompt('Copy this link', url); });
    });
  }

  /* ---------- hero: venue screen slideshow + colour ribbon ---------- */
  var screen = $('#screen');
  if (screen) {
    var DUR = 5200, idx = 0, timer = null, paused = false;
    var slidesBox = $('#slides'), barsBox = $('#bars'), label = $('#now-l');
    var labelBase = 'Now playing, best seller no. ';
    function show(n) {
      var sl = $$('.slide', slidesBox), bs = $$('.bar', barsBox);
      if (!sl.length) return;
      idx = (n + sl.length) % sl.length;
      sl.forEach(function (s, i) { s.classList.toggle('is-on', i === idx); s.tabIndex = i === idx ? 0 : -1; });
      bs.forEach(function (b, i) {
        b.classList.remove('is-on'); b.classList.toggle('done', i < idx);
        if (i === idx) { void b.offsetWidth; b.classList.add('is-on'); }
      });
      var cur = sl[idx], a = $('#now-link');
      a.textContent = cur.dataset.name; a.href = cur.getAttribute('href');
      $('#now-meta').textContent = cur.dataset.type + ', ' + cur.dataset.price;
      label.textContent = labelBase.indexOf('best seller') > -1 ? labelBase + (idx + 1) : labelBase;
      schedule();
    }
    function schedule() { clearTimeout(timer); if (!paused && !REDUCED) timer = setTimeout(function () { show(idx + 1); }, DUR); }
    screen.style.setProperty('--dur', DUR + 'ms');
    barsBox.addEventListener('click', function (e) { var b = e.target.closest('.bar'); if (b) show($$('.bar', barsBox).indexOf(b)); });
    $('#screen-pause').addEventListener('click', function () {
      paused = !paused; screen.classList.toggle('paused', paused);
      this.setAttribute('aria-label', paused ? 'Play slideshow' : 'Pause slideshow'); schedule();
    });
    screen.addEventListener('mouseenter', function () { if (!paused) { clearTimeout(timer); screen.classList.add('paused'); } });
    screen.addEventListener('mouseleave', function () { if (!paused) { screen.classList.remove('paused'); schedule(); } });
    document.addEventListener('visibilitychange', function () { if (document.hidden) clearTimeout(timer); else schedule(); });
    if (REDUCED) { paused = true; screen.classList.add('paused'); }
    show(0);

    var ribbon = $('#ribbon');
    if (ribbon) ribbon.addEventListener('click', function (e) {
      var b = e.target.closest('.swatch'); if (!b) return;
      var c = b.dataset.colour, was = b.getAttribute('aria-pressed') === 'true';
      $$('.swatch', ribbon).forEach(function (s) { s.setAttribute('aria-pressed', 'false'); });
      getProducts().then(function (all) {
        var pool = all.filter(function (p) { return p.occasion === 'quinceanera-sweet-16'; });
        if (!was) { b.setAttribute('aria-pressed', 'true'); pool = pool.filter(function (p) { return p.colours.indexOf(c) > -1; }); }
        var feats = {}; try { feats = JSON.parse(ribbon.getAttribute('data-features') || '{}'); } catch (x) {}
        var mix = [], types = {};
        if (!was && feats[c]) {  /* the shop's chosen design for this colour plays first */
          var f = all.filter(function (p) { return p.id === feats[c]; })[0];
          if (f) { mix.push(f); types[f.type] = 1; pool = pool.filter(function (p) { return p.id !== f.id; }); }
        }
        pool.forEach(function (p) { if (mix.length < 6 && (types[p.type] || 0) < 2) { mix.push(p); types[p.type] = (types[p.type] || 0) + 1; } });
        pool.forEach(function (p) { if (mix.length < 6 && mix.indexOf(p) < 0) mix.push(p); });
        slidesBox.innerHTML = mix.map(function (p) {
          return '<a class="slide" href="' + href('templates/' + p.slug + '/') + '" data-name="' + esc(p.name) + '" data-price="$' + p.price.toFixed(2) + '" data-type="' + esc(p.type_name) + '"><img src="' + esc(p.img_lg) + '" alt="' + esc(p.name) + '"></a>';
        }).join('');
        barsBox.innerHTML = mix.map(function (p, i) { return '<button type="button" class="bar" aria-label="Show design ' + (i + 1) + '"><i></i></button>'; }).join('');
        labelBase = was ? 'Now playing, best seller no. ' : 'Now playing, ' + b.textContent.trim().toLowerCase() + ' designs';
        show(0);
      });
    });
  }

  /* ---------- header turns solid after the dark hero ---------- */
  var top = $('.top');
  if (top && document.body.dataset.page === 'home') {
    var onScroll = function () { top.classList.toggle('scrolled', window.scrollY > 40); };
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  /* ---------- best sellers carousel ---------- */
  $$('[data-carousel]').forEach(function (track) {
    var sec = track.closest('section'), auto = null, user = false;
    var step = function () { var c = track.querySelector('li'); return c ? c.getBoundingClientRect().width + 24 : 300; };
    function go(dir) {
      var max = track.scrollWidth - track.clientWidth - 4;
      if (dir > 0 && track.scrollLeft >= max) track.scrollTo({ left: 0 });
      else if (dir < 0 && track.scrollLeft <= 4) track.scrollTo({ left: max });
      else track.scrollBy({ left: dir * step() });
    }
    var prev = sec && $('[data-car-prev]', sec), next = sec && $('[data-car-next]', sec);
    if (prev) prev.addEventListener('click', function () { user = true; go(-1); });
    if (next) next.addEventListener('click', function () { user = true; go(1); });
    track.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') { user = true; go(1); } if (e.key === 'ArrowLeft') { user = true; go(-1); } });
    ['pointerdown', 'wheel', 'touchstart', 'focusin'].forEach(function (ev) { track.addEventListener(ev, function () { user = true; }, { passive: true }); });
    if (!REDUCED && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (en) {
        clearInterval(auto);
        if (en[0].isIntersecting) auto = setInterval(function () { if (!user && !track.matches(':hover')) go(1); }, 3800);
      }, { threshold: .4 }).observe(track);
    }
  });

  /* ---------- scroll reveal ---------- */
  var rev = $$('[data-reveal]');
  if (rev.length && 'IntersectionObserver' in window && !REDUCED) {
    var groups = new Map();
    rev.forEach(function (el) { var p = el.parentElement; var n = groups.get(p) || 0; el.style.setProperty('--d', (Math.min(n, 5) * 0.08) + 's'); groups.set(p, n + 1); });
    var io = new IntersectionObserver(function (en) { en.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); } }); }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    rev.forEach(function (el) { io.observe(el); });
  } else rev.forEach(function (el) { el.classList.add('in'); });

  /* ---------- shop filters ---------- */
  var shop = $('#shop-grid');
  if (shop) {
    var cards = $$('.card', shop), form = $('#filters'), qIn = $('#q'), sortSel = $('#sort'), countEl = $('#shown');
    var params = new URLSearchParams(location.search);
    ['occasion', 'type', 'colour', 'theme', 'price'].forEach(function (k) {
      params.getAll(k).forEach(function (v) { var i = form.querySelector('input[name="' + k + '"][value="' + v + '"]'); if (i) i.checked = true; });
    });
    if (params.get('q')) qIn.value = params.get('q');
    function apply() {
      var sel = {};
      $$('input:checked', form).forEach(function (i) { (sel[i.name] = sel[i.name] || []).push(i.value); });
      var q = qIn.value.trim().toLowerCase(), shown = 0;
      cards.forEach(function (c) {
        var d = c.dataset, ok = true;
        if (sel.occasion && sel.occasion.indexOf(d.occasion) < 0) ok = false;
        if (ok && sel.type && sel.type.indexOf(d.type) < 0) ok = false;
        if (ok && sel.colour && !sel.colour.some(function (v) { return (' ' + d.colours + ' ').indexOf(' ' + v + ' ') > -1; })) ok = false;
        if (ok && sel.theme && !sel.theme.some(function (v) { return (' ' + d.themes + ' ').indexOf(' ' + v + ' ') > -1; })) ok = false;
        if (ok && sel.price) {
          var p = +d.price; ok = sel.price.some(function (r) { var a = r.split('-'); return p >= +a[0] && p <= +a[1]; });
        }
        if (ok && q) ok = d.search.indexOf(q) > -1;
        c.hidden = !ok; if (ok) shown++;
      });
      countEl.textContent = shown + (shown === 1 ? ' template' : ' templates');
      $('#shop-empty').hidden = shown > 0;
      var s = sortSel.value, list = cards.slice();
      list.sort(function (a, b) {
        if (s === 'price-asc') return a.dataset.price - b.dataset.price;
        if (s === 'price-desc') return b.dataset.price - a.dataset.price;
        if (s === 'new') return b.dataset.newness - a.dataset.newness;
        return a.dataset.rank - b.dataset.rank;
      });
      list.forEach(function (c) { shop.appendChild(c); });
      var u = new URLSearchParams();
      Object.keys(sel).forEach(function (k) { sel[k].forEach(function (v) { u.append(k, v); }); });
      if (q) u.set('q', q);
      history.replaceState(null, '', location.pathname + (u.toString() ? '?' + u : ''));
    }
    form.addEventListener('change', apply); sortSel.addEventListener('change', apply);
    qIn.addEventListener('input', function () { clearTimeout(apply.t); apply.t = setTimeout(apply, 120); });
    $('#clear').addEventListener('click', function () { $$('input:checked', form).forEach(function (i) { i.checked = false; }); qIn.value = ''; apply(); });
    var ft = $('.filters-toggle'); if (ft) ft.addEventListener('click', function () { var o = form.classList.toggle('open'); ft.setAttribute('aria-expanded', o); });
    apply();
  }

  /* ---------- search overlay ---------- */
  var sOpen = $$('[data-open-search]'), sBox = $('#search'), sIn = $('#search-q'), sRes = $('#search-results');
  function closeSearch() { sBox.classList.remove('open'); document.body.style.overflow = ''; }
  sOpen.forEach(function (b) { b.addEventListener('click', function () { sBox.classList.add('open'); document.body.style.overflow = 'hidden'; sIn.focus(); getProducts(); }); });
  if (sBox) {
    sBox.addEventListener('click', function (e) { if (e.target === sBox) closeSearch(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sBox.classList.contains('open')) closeSearch();
      if (e.key === '/' && !/input|textarea|select/i.test(document.activeElement.tagName)) { e.preventDefault(); sOpen[0] && sOpen[0].click(); }
    });
    sIn.addEventListener('input', function () {
      var q = sIn.value.trim().toLowerCase();
      if (q.length < 2) { sRes.innerHTML = ''; return; }
      getProducts().then(function (all) {
        var words = q.split(/\s+/);
        var hit = all.filter(function (p) { return words.every(function (w) { return p.search.indexOf(w) > -1; }); }).slice(0, 12);
        sRes.innerHTML = hit.length ? hit.map(function (p) {
          return '<a href="' + href('templates/' + p.slug + '/') + '"><img src="' + esc(p.img) + '" alt=""><span>' + esc(p.name) + '<small>' + esc(p.occasion_name + ', ' + p.type_name) + '</small></span><b>$' + p.price.toFixed(2) + '</b></a>';
        }).join('') + '<p style="padding:8px"><a class="textlink" href="' + href('shop/') + '?q=' + encodeURIComponent(q) + '">See every match in the shop</a></p>'
          : '<p style="padding:12px">No templates match "' + esc(q) + '". Try a color, like pink, or an event, like wedding.</p>';
      });
    });
  }

  /* ---------- planner ---------- */
  var pl = $('#planner');
  if (pl) {
    var PLANS = {
      quince: { label: 'quinceañera or sweet 16', items: [
        [26, 'Send your save the date', 'Six months out gives family time to book travel.', 'quinceanera-sweet-16/save-the-dates/'],
        [12, 'Publish your website invitation', 'One link with the schedule, venue map, dress code and RSVP.', 'quinceanera-sweet-16/website-invitations/'],
        [8, 'Send the video invitation', 'Text it to the family group chat and post it to your stories.', 'quinceanera-sweet-16/video-invitations/'],
        [6, 'Collect photos for the slideshow', 'Ask grandparents and padrinos for baby pictures now.', null],
        [3, 'RSVP deadline', 'Give your venue and caterer a final head count.', null],
        [2, 'Finish the slideshow', 'Edit in Canva, then download the MP4.', 'quinceanera-sweet-16/slideshows/'],
        [1, 'Test the slideshow on the venue screen', 'Bring it on a USB drive and on your phone as a backup.', null],
        [0, 'Celebrate', 'Enjoy every minute.', null]
      ]},
      wedding: { label: 'wedding', items: [
        [32, 'Send your save the date', 'Eight months out, earlier for a destination wedding.', 'wedding-anniversary/save-the-dates/'],
        [12, 'Publish your wedding website invitation', 'Share travel details, registry and RSVP in one link.', 'wedding-anniversary/website-invitations/'],
        [8, 'Send invitations', 'Six to eight weeks before is the usual window.', 'wedding-anniversary/video-invitations/'],
        [4, 'RSVP deadline', 'Leaves time to chase late replies and finish seating.', null],
        [3, 'Build your love story slideshow', 'Gather photos from both families.', 'wedding-anniversary/slideshows/'],
        [0, 'Wedding day', 'Congratulations.', null]
      ]},
      birthday: { label: 'birthday or first birthday', items: [
        [5, 'Send the invitation', 'Four to five weeks ahead works for most birthdays.', 'birthday-baby/'],
        [3, 'Collect photos for the slideshow', 'For a first birthday, pick one photo for each month.', null],
        [2, 'RSVP deadline', 'Confirm the head count for food and favors.', null],
        [1, 'Finish the slideshow', 'Download the MP4 and test it on the screen you will use.', 'birthday-baby/slideshows/'],
        [0, 'Party day', 'Have the best time.', null]
      ]},
      mitzvah: { label: 'bat or bar mitzvah', items: [
        [26, 'Send your save the date', 'Six months out, earlier if guests travel.', 'bat-bar-mitzvah/'],
        [8, 'Send invitations', 'Six to eight weeks before the service.', 'bat-bar-mitzvah/invitations-save-the-dates/'],
        [3, 'RSVP deadline', 'Final numbers for the celebration.', null],
        [2, 'Finish the montage slideshow', 'Edit in Canva and download the MP4.', 'bat-bar-mitzvah/slideshows/'],
        [0, 'Mitzvah day', 'Mazel tov.', null]
      ]},
      graduation: { label: 'graduation party', items: [
        [5, 'Send the invitation', 'Graduation season is busy, so invite early.', 'graduation/'],
        [2, 'RSVP deadline', 'Confirm the head count.', null],
        [0, 'Party day', 'Congratulations, graduate.', null]
      ]}
    };
    var fmt = function (d) { return d.toLocaleDateString('en-US', { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' }); };
    var ymd = function (d) { return d.toISOString().slice(0, 10).replace(/-/g, ''); };
    var evSel = $('#p-event'), dIn = $('#p-date'), out = $('#p-out');
    var qp = new URLSearchParams(location.search);
    if (qp.get('event') && PLANS[qp.get('event')]) evSel.value = qp.get('event');
    if (qp.get('date')) dIn.value = qp.get('date');
    function plan() {
      if (!dIn.value) { out.innerHTML = '<p class="muted">Pick your date to see your timeline.</p>'; $('#p-ics').hidden = true; return; }
      var day = new Date(dIn.value + 'T12:00:00'), today = new Date(), P = PLANS[evSel.value], nextDone = false;
      var rows = P.items.map(function (it) {
        var d = new Date(day); d.setDate(d.getDate() - it[0] * 7);
        var past = d < today && it[0] > 0, cls = past ? 'past' : '';
        var tag = '';
        if (!past && !nextDone) { cls = 'next'; nextDone = true; tag = '<span class="tag-next">Next</span>'; }
        var when = it[0] === 0 ? 'The big day' : (it[0] >= 8 && it[0] % 4 === 0 ? (it[0] / 4) + ' months before' : it[0] + (it[0] === 1 ? ' week' : ' weeks') + ' before');
        if (it[0] >= 26) when = Math.round(it[0] / 4.33) + ' months before';
        return { d: d, html: '<li class="' + cls + '"><time datetime="' + d.toISOString().slice(0, 10) + '">' + fmt(d) + '</time>' + tag +
          '<span class="when">' + when + (past ? ', date has passed: do this as soon as you can' : '') + '</span><div><strong>' + it[1] + '.</strong> ' + it[2] +
          (it[3] ? ' <a href="' + href(it[3]) + '">See templates</a>' : '') + '</div></li>', t: it[1], n: it[2] };
      });
      out.innerHTML = '<h2 style="font-size:var(--step-2);margin-top:8px">Your ' + P.label + ' timeline</h2><ol class="timeline">' + rows.map(function (r) { return r.html; }).join('') + '</ol>';
      var ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Digipod Studio//Party Planner//EN'];
      rows.forEach(function (r, i) {
        var e = new Date(r.d); e.setDate(e.getDate() + 1);
        ics.push('BEGIN:VEVENT', 'UID:dp-' + ymd(r.d) + '-' + i + '@digipodstudio.com', 'DTSTAMP:' + ymd(new Date()) + 'T000000Z', 'DTSTART;VALUE=DATE:' + ymd(r.d), 'DTEND;VALUE=DATE:' + ymd(e), 'SUMMARY:' + r.t, 'DESCRIPTION:' + r.n.replace(/,/g, '\\,'), 'END:VEVENT');
      });
      ics.push('END:VCALENDAR');
      var a = $('#p-ics'); a.hidden = false;
      a.href = URL.createObjectURL(new Blob([ics.join('\r\n')], { type: 'text/calendar' }));
      history.replaceState(null, '', location.pathname + '?event=' + evSel.value + '&date=' + dIn.value);
    }
    evSel.addEventListener('change', plan); dIn.addEventListener('change', plan); dIn.addEventListener('input', plan);
    plan();
  }

  /* ---------- email sign-up (posts to a Google Form; responses land in a Google Sheet) ---------- */
  var cfgRaw = document.documentElement.getAttribute('data-signup');
  if (cfgRaw) {
    var cfg = JSON.parse(cfgRaw);
    $$('form[data-signup]').forEach(function (f) {
      f.addEventListener('submit', function (ev) {
        ev.preventDefault();
        var k = function (n) { return f.querySelector('[data-k="' + n + '"]'); };
        var err = $('.su-error', f), email = k('email').value.trim();
        if (k('company').value) return;  /* bot trap */
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { err.textContent = document.documentElement.lang === 'es' ? 'Escribe un correo válido, por ejemplo nombre@gmail.com' : 'Enter a valid email address, like name@gmail.com'; err.hidden = false; k('email').focus(); return; }
        err.hidden = true;
        var fd = new FormData(), F = cfg.fields;
        fd.append(F.email, email); fd.append(F.celebration, k('celebration').value);
        if (k('date').value && F.date) fd.append(F.date, k('date').value);
        if (F.lang) fd.append(F.lang, document.documentElement.lang);
        if (F.page) fd.append(F.page, location.pathname);
        var btn = $('button[type=submit]', f); btn.disabled = true;
        fetch(cfg.action, { method: 'POST', mode: 'no-cors', body: fd }).then(function () {
          $('.su-fields', f).hidden = true; $('.su-done', f).hidden = false;
          var plan = $('.su-plan', f);
          if (plan && k('date').value) plan.href = href('planner/') + '?event=' + (k('celebration').value === 'other' ? 'quince' : k('celebration').value) + '&date=' + k('date').value;
          try { localStorage.setItem('digipod-signed-up', '1'); } catch (e) {}
        }).catch(function () {
          btn.disabled = false; err.textContent = 'That did not go through. Check your connection and try again.'; err.hidden = false;
        });
      });
    });
  }

  /* teaser form on home sends people to the planner with their date */
  var tf = $('#planner-teaser');
  if (tf) tf.addEventListener('submit', function (e) {
    e.preventDefault();
    location.href = href('planner/') + '?event=' + $('#t-event', tf).value + '&date=' + $('#t-date', tf).value;
  });
})();
