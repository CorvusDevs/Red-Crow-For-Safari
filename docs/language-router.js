/* Corvus Pages language router v1 */
(function () {
  'use strict';

  var script = document.currentScript;
  if (!script || !script.src) return;
  var scriptURL = new URL(script.src, location.href);
  var siteRoot = scriptURL.pathname.slice(0, -'language-router.js'.length);
  var storageKey = 'corvus-pages-language:' + siteRoot;
  var links = Array.prototype.slice.call(
    document.querySelectorAll('link[rel~="alternate"][hreflang][href]')
  );
  var alternates = new Map();
  links.forEach(function (link) {
    var code = link.getAttribute('hreflang');
    if (code && code.toLowerCase() !== 'x-default') {
      alternates.set(code.toLowerCase(), { code: code, href: link.href });
    }
  });
  if (!alternates.has('en') || alternates.size < 2) return;

  function normalize(tag) {
    if (!tag) return null;
    var value = String(tag).replace(/_/g, '-').toLowerCase();
    if (alternates.has(value)) return alternates.get(value).code;
    var parts = value.split('-');
    var base = parts[0];
    if (base === 'zh') {
      var traditional = parts.some(function (part) {
        return part === 'hant' || part === 'tw' || part === 'hk' || part === 'mo';
      });
      var chinese = traditional ? 'zh-hant' : 'zh-hans';
      if (alternates.has(chinese)) return alternates.get(chinese).code;
    }
    if (base === 'no' && alternates.has('nb')) return alternates.get('nb').code;
    if (alternates.has(base)) return alternates.get(base).code;
    var variant = Array.from(alternates.keys()).find(function (code) {
      return code.indexOf(base + '-') === 0;
    });
    return variant ? alternates.get(variant).code : null;
  }

  function readPreference() {
    try { return localStorage.getItem(storageKey); } catch (_) { return null; }
  }
  function writePreference(value) {
    try {
      if (value === 'auto') localStorage.removeItem(storageKey);
      else localStorage.setItem(storageKey, value);
    } catch (_) {}
  }
  function browserPreference() {
    var requested = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || 'en'];
    for (var i = 0; i < requested.length; i += 1) {
      var match = normalize(requested[i]);
      if (match) return match;
    }
    return 'en';
  }
  function isLocalizedPath() {
    var relative = location.pathname.indexOf(siteRoot) === 0
      ? location.pathname.slice(siteRoot.length)
      : location.pathname;
    return /^i18n\/[^/]+(?:\/|$)/i.test(relative);
  }
  function targetFor(language) {
    var entry = alternates.get(String(language).toLowerCase());
    return entry ? new URL(entry.href, location.href) : null;
  }
  function sameLocation(target) {
    return target.origin === location.origin &&
      target.pathname === location.pathname &&
      target.search === location.search &&
      target.hash === location.hash;
  }

  var current = new URL(location.href);
  var requested = current.searchParams.get('lang');
  var choice = null;
  if (requested === 'auto') {
    writePreference('auto');
    choice = browserPreference();
  } else if (requested) {
    choice = normalize(requested) || 'en';
    writePreference(choice);
  } else {
    choice = normalize(readPreference()) || browserPreference();
  }

  if (!isLocalizedPath() && choice !== 'en') {
    var target = targetFor(choice);
    if (target) {
      current.searchParams.delete('lang');
      current.searchParams.forEach(function (value, key) {
        if (!target.searchParams.has(key)) target.searchParams.set(key, value);
      });
      target.hash = current.hash;
      if (!sameLocation(target)) {
        location.replace(target.href);
        return;
      }
    }
  } else if (requested && choice === 'en') {
    current.searchParams.delete('lang');
    history.replaceState(null, '', current.pathname + current.search + current.hash);
  }

  document.addEventListener('click', function (event) {
    var control = event.target.closest('a[lang], a[data-lang], button[data-lang], .lang-menu a[href]');
    if (!control) return;
    var value = control.getAttribute('data-lang') || control.getAttribute('lang');
    if (!value && control.href) {
      var selected = new URL(control.href, location.href);
      alternates.forEach(function (entry) {
        var candidate = new URL(entry.href, location.href);
        if (candidate.pathname === selected.pathname && candidate.search === selected.search) {
          value = entry.code;
        }
      });
    }
    if (!value) return;
    if (value === 'auto') writePreference('auto');
    else writePreference(normalize(value) || 'en');
  }, true);
})();
