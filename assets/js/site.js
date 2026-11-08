(() => {
  'use strict';

  // Pending resources are plain, non-interactive text until a URL is provided.
  document.querySelectorAll('[data-resource]').forEach((placeholder) => {
    const url = window.LPG_LINKS?.[placeholder.dataset.resource];
    if (!url) return;
    let parsed;
    try { parsed = new URL(url, document.baseURI); } catch { return; }
    if (!['https:', 'http:'].includes(parsed.protocol)) return;
    const link = document.createElement('a');
    link.className = 'resource available';
    link.href = parsed.href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.dataset.resource = placeholder.dataset.resource;
    [...placeholder.children].filter((child) => child.tagName !== 'SMALL')
      .forEach((child) => link.append(child.cloneNode(true)));
    placeholder.replaceWith(link);
  });

  const tabList = document.querySelector('.scenario-tabs');
  const tabs = [...tabList.querySelectorAll('button')];
  const panels = [...document.querySelectorAll('.scenario-panel')];
  function selectScenario(tab, focus = false) {
    tabs.forEach((item) => {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
    });
    panels.forEach((panel) => { panel.hidden = panel.id !== `panel-${tab.dataset.scenario}`; });
    if (focus) tab.focus();
  }
  if (tabs.length && panels.length === tabs.length) {
    tabList.setAttribute('role', 'tablist');
    tabs.forEach((tab) => {
      const panel = document.getElementById(`panel-${tab.dataset.scenario}`);
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', panel.id);
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tab.id);
      panel.tabIndex = 0;
      tab.addEventListener('click', () => selectScenario(tab));
    });
    tabList.addEventListener('keydown', (event) => {
      const index = tabs.indexOf(document.activeElement);
      if (index < 0) return;
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      selectScenario(tabs[next], true);
    });
    selectScenario(tabs[0]);
    document.getElementById('results').classList.add('tabs-ready');
    tabList.hidden = false;
  }

  // Keep ordinary image links working if dialog support or JavaScript is absent.
  const viewer = document.getElementById('figure-dialog');
  const viewerImage = document.getElementById('viewer-image');
  const viewerCaption = document.getElementById('viewer-caption');
  const closeViewer = document.getElementById('close-viewer');
  if (typeof viewer.showModal === 'function') {
    let opener;
    document.querySelectorAll('[data-lightbox]').forEach((link) => {
      link.addEventListener('click', (event) => {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        opener = link;
        viewerImage.src = link.href;
        viewerImage.alt = link.querySelector('img')?.alt || 'Research figure';
        viewerCaption.textContent = link.dataset.caption || viewerImage.alt;
        document.getElementById('viewer-original').href = link.href;
        viewer.showModal();
        document.body.classList.add('viewer-open');
      });
    });
    closeViewer.addEventListener('click', () => viewer.close());
    viewer.addEventListener('click', (event) => {
      if (event.target !== viewer) return;
      const bounds = viewer.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom) viewer.close();
    });
    viewer.addEventListener('close', () => {
      document.body.classList.remove('viewer-open');
      opener?.focus({ preventScroll: true });
    });
  }

  const copyButton = document.getElementById('copy-citation');
  const copyStatus = document.getElementById('copy-status');
  copyButton.hidden = false;
  copyButton.addEventListener('click', async () => {
    const citation = document.getElementById('bibtex').textContent.trim();
    let copied = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(citation);
        copied = true;
      }
    } catch { /* Try the selection-based fallback, including local file previews. */ }
    if (!copied) {
      const textarea = document.createElement('textarea');
      textarea.value = citation;
      textarea.style.cssText = 'position:fixed;top:0;left:-9999px';
      document.body.append(textarea);
      textarea.select();
      try { copied = document.execCommand('copy'); } catch { /* Manual copy remains available. */ }
      textarea.remove();
      copyButton.focus({ preventScroll: true });
    }
    copyStatus.textContent = copied ? 'Citation copied to clipboard.' : 'Select the citation above and copy it manually.';
    copyButton.querySelector('span').textContent = copied ? 'Copied!' : 'Copy citation';
    clearTimeout(copyButton.resetTimer);
    copyButton.resetTimer = setTimeout(() => { copyButton.querySelector('span').textContent = 'Copy citation'; }, 2500);
  });

  const menu = document.querySelector('.more-menu');
  document.addEventListener('click', (event) => {
    if (menu.open && !menu.contains(event.target)) menu.open = false;
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });

  const navLinks = [...document.querySelectorAll('.desktop-nav a')];
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      const current = entries.filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!current) return;
      navLinks.forEach((link) => {
        if (link.hash === `#${current.target.id}`) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin: '-10% 0px -55% 0px' });
    ['top', 'abstract', 'method', 'results', 'analysis', 'citation'].forEach((id) => observer.observe(document.getElementById(id)));
  }
})();
