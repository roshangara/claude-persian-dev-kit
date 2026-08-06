
/* ===== BEGIN fa-bidi-patch ===== */
/* CSS `unicode-bidi: plaintext` picks a block's direction from its FIRST strong
   character, so a mostly-Persian paragraph that opens with an English term
   ("Agentless. روی سرور ...") is laid out left-to-right and becomes hard to
   read. CSS cannot count characters, so decide direction by majority here and
   write an explicit dir attribute; the stylesheet switches any [dir] block from
   plaintext to isolate so this wins.

   The live composer is deliberately left on plaintext -- re-deciding direction
   from a majority while you are still typing would flip the layout mid-sentence.

   Remove everything from the BEGIN marker down to undo. */
;(() => {
  /* Containers (ul/ol/table) are measured too, not just the text blocks inside
     them: the list marker and the indent hang off the container's direction, so
     a right-aligned Persian item under a left-to-right <ul> puts the bullet on
     one side and the indent on the other. Same for table column order. */
  const TEXTY = 'p,li,blockquote,td,th,h1,h2,h3,h4,h5,h6,dd,dt,summary,label,button,figcaption,legend';
  const BLOCKS = TEXTY + ',ul,ol,table';

  /* UI outside the markdown renderer: the permission/question dialog, tool
     headers, todo rows. These are plain divs, so nothing above matches them and
     they were left in first-strong order. Handled separately because most of
     them are flex boxes, where `direction` reorders the children instead of the
     words -- see applyLoose for the guard. */
  const LOOSE = 'div,span,section,article,header,footer,aside,main';

  const SKIP = 'pre,code,kbd,samp,.monaco-editor,[class*="messageInput_"],[class*="mentionMirror_"]';

  const isRTL = (c) =>
    (c >= 0x0590 && c <= 0x08ff && !(c >= 0x0660 && c <= 0x0669) && !(c >= 0x06f0 && c <= 0x06f9)) ||
    (c >= 0xfb1d && c <= 0xfdff) ||
    (c >= 0xfe70 && c <= 0xfeff);

  const isLTR = (c) =>
    (c >= 0x41 && c <= 0x5a) || (c >= 0x61 && c <= 0x7a) ||
    (c >= 0x00c0 && c <= 0x024f) || (c >= 0x1e00 && c <= 0x1eff);

  /* Count strong characters in prose only. Inline code is skipped: identifiers
     like network_cli or python3 are not evidence that a sentence is English. */
  const countStrong = (el) => {
    let rtl = 0, ltr = 0;
    const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) =>
        n.parentElement && n.parentElement.closest(SKIP)
          ? NodeFilter.FILTER_REJECT
          : NodeFilter.FILTER_ACCEPT,
    });
    for (let n = walk.nextNode(); n; n = walk.nextNode()) {
      const t = n.nodeValue;
      for (let i = 0; i < t.length; i++) {
        const c = t.charCodeAt(i);
        if (isRTL(c)) rtl++;
        else if (isLTR(c)) ltr++;
      }
    }
    return [rtl, ltr];
  };

  /* What the enclosing block already decided. Ancestors are always measured
     before their descendants (querySelectorAll returns document order), so by
     the time a list item is examined its list has a verdict. */
  const context = (el) => {
    const p = el.parentElement;
    const anc = p && p.closest('[data-fa-dir]');
    return anc ? anc.getAttribute('data-fa-dir') : null;
  };

  const decide = (el) => {
    const [rtl, ltr] = countStrong(el);
    const ctx = context(el);

    /* Nothing measurable -- a list item that is only a command, say. Judged
       alone it falls back to first-strong, goes ltr, and drifts to the far edge
       of an otherwise right-to-left list. Follow the enclosing block instead. */
    if (!rtl && !ltr) return ctx;

    /* No Persian of its own. Inside a Persian block it still belongs with its
       neighbours ("Forgejo روی CT 120" is a Persian bullet, not an English
       one); anywhere else, leave it alone. */
    if (!rtl) return ctx === 'rtl' ? 'rtl' : null;

    /* Some Persian, and it sits inside a block already judged Persian: that
       settles it. Ratios are the wrong tool here -- a bullet made mostly of
       product names would lose a count it should win. */
    if (ctx === 'rtl') return 'rtl';

    /* Standalone block. Not a plain majority: Persian technical prose carries a
       lot of English, so `rtl > ltr` decides headings like "Variables و
       اولویت‌شان" by a single character. Persian wins unless English outweighs
       it better than two to one; a real English sentence with a Persian aside
       still lands on ltr. */
    return rtl * 2 > ltr ? 'rtl' : 'ltr';
  };

  const apply = (el) => {
    if (el.closest(SKIP)) return;
    const dir = decide(el);
    if (!dir) return;
    if (el.getAttribute('data-fa-dir') === dir) return;
    el.setAttribute('data-fa-dir', dir);
    el.setAttribute('dir', dir);
    /* Inline, and !important, rather than a stylesheet rule. The app ships
       `.root_x :-webkit-any(p,li,h1,...){unicode-bidi:plaintext}` and Blink
       gives :-webkit-any() pseudo-class weight, so that selector scores (0,2,0)
       and beats any `li[dir]`-style rule (0,1,1) we could append. An inline
       !important declaration outranks the whole stylesheet, so the measured
       direction wins no matter what the app does next. */
    el.style.setProperty('direction', dir, 'important');
    el.style.setProperty('unicode-bidi', 'isolate', 'important');
    el.style.setProperty('text-align', 'start', 'important');
  };

  const hasOwnText = (el) => {
    for (let n = el.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === Node.TEXT_NODE && /\S/.test(n.nodeValue)) return true;
    }
    return false;
  };

  /* A generic element only gets a direction if it carries text itself and is not
     a layout box. On a flex or grid container `direction: rtl` reverses the
     order of the children -- it would turn the question dialog inside out
     instead of making its sentences readable. Checks are ordered cheapest
     first; getComputedStyle runs for the few candidates that survive. */
  const applyLoose = (el) => {
    if (!hasOwnText(el)) return;
    if (el.closest(SKIP)) return;
    /* Already governed by an enclosing text block -- a <span> inside a <p>
       follows the paragraph rather than deciding for itself. */
    if (el.parentElement && el.parentElement.closest(TEXTY)) return;
    const display = getComputedStyle(el).display;
    if (display === 'flex' || display === 'inline-flex' ||
        display === 'grid' || display === 'inline-grid') return;
    apply(el);
  };

  const pending = new Set();
  let queued = false;

  const flush = () => {
    queued = false;
    const batch = [...pending];
    pending.clear();
    for (const node of batch) {
      if (!node.isConnected) continue;
      if (!node.querySelectorAll) continue;
      /* Text blocks first: they set data-fa-dir, which the loose pass and any
         nested block read as their context. */
      if (node.matches(BLOCKS)) apply(node);
      node.querySelectorAll(BLOCKS).forEach(apply);
      if (node.matches(LOOSE)) applyLoose(node);
      node.querySelectorAll(LOOSE).forEach(applyLoose);
    }
  };

  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(flush);
  };

  /* Streaming responses mutate the DOM on every token, so collect the affected
     blocks and re-measure once per frame rather than per mutation. */
  const observer = new MutationObserver((records) => {
    for (const r of records) {
      let t = r.target;
      if (t.nodeType === Node.TEXT_NODE) t = t.parentElement;
      if (!t || !t.closest) continue;
      pending.add(t.closest(BLOCKS) || t);
      if (r.type === 'childList') {
        for (let i = 0; i < r.addedNodes.length; i++) {
          const n = r.addedNodes[i];
          if (n.nodeType === Node.ELEMENT_NODE) pending.add(n);
        }
      }
    }
    if (pending.size) schedule();
  });

  const start = () => {
    const root = document.body || document.documentElement;
    if (!root) return;
    pending.add(root);
    schedule();
    observer.observe(root, { childList: true, subtree: true, characterData: true });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
/* ===== END fa-bidi-patch ===== */
