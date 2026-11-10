// Original cartoon characters for the demo video (inline SVG, no external assets).
// Papa (the parent), the Scammer (a faceless hooded figure), and Shieldy (the Scam Shield mascot).
(function () {
  const ink = '#1d1e1d';

  function papa(mood) {
    mood = mood || 'calm';
    const mouth = mood === 'happy' || mood === 'chai'
      ? '<path d="M84 121 Q100 138 116 121 Z" fill="#7a3b22" stroke="#5a2e1a" stroke-width="3" stroke-linejoin="round"/>'
      : '<path d="M87 124 Q100 131 113 124" stroke="#5a2e1a" stroke-width="4" fill="none" stroke-linecap="round"/>';
    const chai = mood === 'chai' ? `
      <g class="chai">
        <path class="steam" d="M150 168 q-7 -9 0 -18 t0 -18" stroke="#bfae96" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <path class="steam s2" d="M162 168 q-7 -9 0 -18 t0 -18" stroke="#bfae96" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <path d="M140 176 h32 v18 a12 12 0 0 1 -12 12 h-8 a12 12 0 0 1 -12 -12z" fill="#fff" stroke="#d6c3a0" stroke-width="3"/>
        <path d="M172 181 q11 0 11 8 t-11 8" fill="none" stroke="#d6c3a0" stroke-width="3"/>
        <rect x="141" y="178" width="30" height="7" fill="#c9905a"/>
        <circle cx="146" cy="204" r="11" fill="#c98b62"/>
      </g>` : '';
    return `<svg viewBox="0 0 200 240" class="ch papa" aria-hidden="true"><g class="breathe">
      <path d="M26 240 Q30 166 100 158 Q170 166 174 240Z" fill="#f4e7cf"/>
      <path d="M84 160 L100 192 L116 160" fill="none" stroke="#d8c4a0" stroke-width="4" stroke-linejoin="round"/>
      <circle cx="100" cy="204" r="3" fill="#d8c4a0"/><circle cx="100" cy="220" r="3" fill="#d8c4a0"/>
      <rect x="88" y="130" width="24" height="32" rx="9" fill="#b97a55"/>
      <circle cx="53" cy="96" r="10" fill="#b97a55"/><circle cx="147" cy="96" r="10" fill="#b97a55"/>
      <circle cx="100" cy="90" r="48" fill="#c98b62"/>
      <ellipse cx="58" cy="76" rx="13" ry="19" fill="#efefef"/><ellipse cx="142" cy="76" rx="13" ry="19" fill="#efefef"/>
      <path d="M71 74 Q81 67 92 74" stroke="#f3f3f3" stroke-width="6" fill="none" stroke-linecap="round"/>
      <path d="M108 74 Q119 67 129 74" stroke="#f3f3f3" stroke-width="6" fill="none" stroke-linecap="round"/>
      <g class="blink"><circle cx="82" cy="94" r="4.5" fill="${ink}"/><circle cx="118" cy="94" r="4.5" fill="${ink}"/></g>
      <g fill="rgba(255,255,255,.22)" stroke="#2b2b2b" stroke-width="3.5"><circle cx="82" cy="94" r="14"/><circle cx="118" cy="94" r="14"/></g>
      <path d="M96 93 H104" stroke="#2b2b2b" stroke-width="3.5"/>
      <path d="M100 98 Q95 109 102 111" stroke="#a46a47" stroke-width="3" fill="none" stroke-linecap="round"/>
      <path d="M78 116 Q89 108 100 115 Q111 108 122 116 Q111 125 100 119 Q89 125 78 116Z" fill="#f2f2f2"/>
      ${mouth}
      <ellipse cx="70" cy="112" rx="7" ry="4" fill="#e39a86" opacity=".5"/><ellipse cx="130" cy="112" rx="7" ry="4" fill="#e39a86" opacity=".5"/>
      ${chai}
    </g></svg>`;
  }

  function scammer(mood) {
    mood = mood || 'smirk';
    const angry = mood === 'angry', sad = mood === 'sad';
    const brows = angry
      ? '<path d="M70 86 L94 96" stroke="#f0f0f0" stroke-width="5" stroke-linecap="round"/><path d="M130 86 L106 96" stroke="#f0f0f0" stroke-width="5" stroke-linecap="round"/>'
      : sad ? '<path d="M72 94 L92 88" stroke="#f0f0f0" stroke-width="4" stroke-linecap="round"/><path d="M128 94 L108 88" stroke="#f0f0f0" stroke-width="4" stroke-linecap="round"/>'
      : '<path d="M72 90 Q82 84 92 90" stroke="#f0f0f0" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M108 86 Q118 80 128 86" stroke="#f0f0f0" stroke-width="4" fill="none" stroke-linecap="round"/>';
    const px = mood === 'smirk' || mood === 'talk' ? 4 : 0;
    const mouth = angry ? '<path d="M84 134 Q100 122 116 134" stroke="#f0f0f0" stroke-width="5" fill="none" stroke-linecap="round"/>'
      : sad ? '<path d="M88 136 Q100 128 112 136" stroke="#f0f0f0" stroke-width="4" fill="none" stroke-linecap="round"/>'
      : mood === 'talk' ? '<ellipse class="talk" cx="102" cy="130" rx="9" ry="6" fill="#f0f0f0"/>'
      : '<path d="M84 128 Q104 140 120 122" stroke="#f0f0f0" stroke-width="5" fill="none" stroke-linecap="round"/>';
    const extra = angry ? `<g class="fume"><text x="150" y="44" font-size="30" font-weight="800" fill="#ff5a5f" font-family="Arial, sans-serif">#@!</text></g>`
      : sad ? `<path class="drop" d="M142 70 q6 10 0 14 q-6 -4 0 -14z" fill="#8ab4ff"/>` : '';
    const phone = sad ? '' : `<g class="${mood === 'talk' || mood === 'smirk' ? 'ring' : ''}"><rect x="142" y="78" width="22" height="42" rx="6" fill="#111" stroke="#777" stroke-width="2"/><rect x="146" y="84" width="14" height="26" rx="2" fill="#5ad1ff" opacity=".7"/><circle cx="150" cy="124" r="12" fill="#474d5b"/></g>`;
    return `<svg viewBox="0 0 200 240" class="ch scammer" aria-hidden="true"><g class="breathe">
      <path d="M24 240 Q28 160 100 150 Q172 160 176 240Z" fill="#363b46"/>
      <path d="M86 156 L100 200 L114 156" fill="none" stroke="#2a2e37" stroke-width="5"/>
      <path d="M40 118 Q40 34 100 30 Q160 34 160 118 Q160 162 100 166 Q40 162 40 118Z" fill="#454b59"/>
      <ellipse cx="100" cy="106" rx="42" ry="46" fill="#1e2129"/>
      <g class="blink"><ellipse cx="${82 + px}" cy="100" rx="8" ry="6" fill="#f0f0f0"/><ellipse cx="${118 + px}" cy="100" rx="8" ry="6" fill="#f0f0f0"/>
        <circle cx="${84 + px}" cy="101" r="3.4" fill="${ink}"/><circle cx="${120 + px}" cy="101" r="3.4" fill="${ink}"/></g>
      ${brows}${mouth}${phone}${extra}
    </g></svg>`;
  }

  function shieldy(mood) {
    mood = mood || 'happy';
    const alert = mood === 'alert';
    const eyes = alert
      ? '<ellipse cx="78" cy="98" rx="12" ry="15" fill="#fff"/><ellipse cx="122" cy="98" rx="12" ry="15" fill="#fff"/><circle cx="78" cy="98" r="7" fill="#1d1e1d"/><circle cx="122" cy="98" r="7" fill="#1d1e1d"/><path d="M64 78 L90 84" stroke="#1d1e1d" stroke-width="5" stroke-linecap="round"/><path d="M136 78 L110 84" stroke="#1d1e1d" stroke-width="5" stroke-linecap="round"/>'
      : '<g class="blink"><ellipse cx="78" cy="98" rx="11" ry="14" fill="#fff"/><ellipse cx="122" cy="98" rx="11" ry="14" fill="#fff"/><circle cx="80" cy="101" r="6.5" fill="#1d1e1d"/><circle cx="124" cy="101" r="6.5" fill="#1d1e1d"/><circle cx="82" cy="98" r="2" fill="#fff"/><circle cx="126" cy="98" r="2" fill="#fff"/></g>';
    const mouth = alert ? '<path d="M86 140 H114" stroke="#1d1e1d" stroke-width="5" stroke-linecap="round"/>'
      : '<path d="M80 134 Q100 156 120 134 Z" fill="#1d1e1d"/><path d="M90 146 Q100 152 110 146" stroke="#ff8a7a" stroke-width="5" fill="none" stroke-linecap="round"/>';
    return `<svg viewBox="0 0 200 240" class="ch shieldy" aria-hidden="true">
      <defs><linearGradient id="shg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fd904b"/><stop offset="1" stop-color="#a99cf0"/></linearGradient></defs>
      <g class="bob">
        <path d="M100 22 L168 46 V110 Q168 178 100 218 Q32 178 32 110 V46Z" fill="url(#shg)" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>
        <path d="M54 96 Q54 42 100 42 Q146 42 146 96" stroke="#1d1e1d" stroke-width="6" fill="none"/>
        <rect x="42" y="86" width="16" height="28" rx="7" fill="#1d1e1d"/><rect x="142" y="86" width="16" height="28" rx="7" fill="#1d1e1d"/>
        <path d="M50 112 Q56 146 84 148" stroke="#1d1e1d" stroke-width="4" fill="none"/><circle cx="86" cy="148" r="5.5" fill="#1d1e1d"/>
        ${eyes}
        <ellipse cx="66" cy="124" rx="9" ry="5" fill="#ff8a7a" opacity=".55"/><ellipse cx="134" cy="124" rx="9" ry="5" fill="#ff8a7a" opacity=".55"/>
        ${mouth}
      </g></svg>`;
  }

  window.Characters = {papa, scammer, shieldy, gena: shieldy, render: (who, mood) => ({papa, scammer, shieldy, gena: shieldy}[who] || shieldy)(mood)};
})();
