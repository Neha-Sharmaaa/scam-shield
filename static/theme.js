// Colour theme switcher shared by all pages. Load in <head> (sets the theme before first paint).
(function () {
  try { localStorage.removeItem('ss-theme'); } catch (e) {}   // drop the old permanent preference
  var THEMES = [
    {id: 'gnani', name: 'Gnani Daylight', note: 'Warm and light', sw: ['#fcf7f2', '#fe914b', '#6c62ed']},
    {id: 'midnight', name: 'Midnight', note: 'Same look, dark', sw: ['#0d0e14', '#fe914b', '#a7a1f4']}
  ];
  // Gnani Daylight is the default on every new visit; a picked theme lasts only for this browsing session.
  var KEY = 'ss-theme-session', root = document.documentElement, current;
  try { current = sessionStorage.getItem(KEY); } catch (e) {}
  if (!THEMES.some(function (t) { return t.id === current; })) current = 'gnani';
  root.setAttribute('data-theme', current);

  function dots(sw) { return '<span class="sw">' + sw.map(function (c) { return '<i style="background:' + c + '"></i>'; }).join('') + '</span>'; }

  function build() {
    var box = document.createElement('div');
    box.className = 'ss-theme';
    box.innerHTML = '<button type="button" aria-haspopup="true" aria-expanded="false" title="Change display colours"></button>' +
      '<div class="menu" role="menu"><div class="t">Display colours</div>' +
      THEMES.map(function (t) {
        return '<button type="button" class="opt" role="menuitemradio" data-id="' + t.id + '">' + dots(t.sw) +
          '<span>' + t.name + '<small>' + t.note + '</small></span><span class="ck">✓</span></button>';
      }).join('') + '</div>';
    document.body.appendChild(box);
    var toggle = box.firstChild;

    function paint() {
      var t = THEMES.filter(function (x) { return x.id === current; })[0];
      toggle.innerHTML = '🎨 ' + dots(t.sw) + '<span class="lbl">' + t.name + '</span>';
      box.querySelectorAll('.opt').forEach(function (o) {
        var on = o.getAttribute('data-id') === current;
        o.classList.toggle('on', on); o.setAttribute('aria-checked', on);
      });
    }
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = box.classList.toggle('open'); toggle.setAttribute('aria-expanded', open);
    });
    box.querySelector('.menu').addEventListener('click', function (e) {
      var o = e.target.closest('.opt'); if (!o) return;
      current = o.getAttribute('data-id');
      root.setAttribute('data-theme', current);
      try { sessionStorage.setItem(KEY, current); } catch (err) {}
      paint(); box.classList.remove('open'); toggle.setAttribute('aria-expanded', false);
    });
    document.addEventListener('click', function (e) { if (!box.contains(e.target)) box.classList.remove('open'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') box.classList.remove('open'); });
    paint();
  }
  if (window.self !== window.top) return;   // no picker inside embedded frames (demo recording)
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();
