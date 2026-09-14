'use strict';

(() => {
  const $ = (id) => document.getElementById(id);
  const grid = $('photo-grid');
  const destinations = $('destinations-grid');
  const status = $('gallery-status');
  const dialog = $('lightbox');
  const viewerImage = $('viewer-image');
  let catalogue;
  let visiblePhotos = [];
  let currentPhoto = 0;
  let openingButton;
  let touchStart = null;

  function photoImage(photo, sizes, lazy = true) {
    const image = document.createElement('img');
    image.alt = photo.alt;
    image.width = photo.width;
    image.height = photo.height;
    image.loading = lazy ? 'lazy' : 'eager';
    image.decoding = 'async';
    image.sizes = sizes;
    image.srcset = [...photo.variants, { src: photo.src, width: photo.width }]
      .map((variant) => `${variant.src} ${variant.width}w`).join(', ');
    image.src = photo.variants[0]?.src || photo.src;
    return image;
  }

  function showStatus(message) {
    status.replaceChildren();
    status.textContent = message;
    status.hidden = !message;
  }

  function routeTo(hash) {
    if (location.hash === hash) renderRoute();
    else location.hash = hash;
    $('gallery').scrollIntoView({ behavior: 'instant' });
  }

  function renderRoute() {
    if (!catalogue) return;
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); }
    catch { hash = ''; }
    const isCountry = hash.startsWith('country=');
    const country = isCountry ? hash.slice(8) : '';
    const destinationPage = document.body.dataset.page === 'destinations';
    const view = destinationPage ? (isCountry ? 'country' : 'destinations') : 'selected';
    // Section anchor navigation should not replace the collection being browsed.
    if (['home', 'about', 'gallery'].includes(hash) && grid.childElementCount + destinations.childElementCount > 0) return;
    grid.replaceChildren();
    destinations.replaceChildren();
    grid.hidden = view === 'destinations';
    destinations.hidden = view !== 'destinations';
    $('collection-toolbar').hidden = view !== 'country';
    $('empty-state').hidden = true;
    $('selected-button').toggleAttribute('aria-current', view === 'selected');
    $('countries-button').toggleAttribute('aria-current', view !== 'selected');
    (view === 'selected' ? $('selected-button') : $('countries-button')).setAttribute('aria-current', 'page');
    showStatus('');

    if (view === 'destinations') {
      $('gallery-title').textContent = 'The destinations.';
      $('gallery-description').textContent = 'Different places. A thousand ways of seeing.';
      renderDestinations();
      showStatus(`${catalogue.countries.length} destinations to explore.`);
      return;
    }

    visiblePhotos = catalogue.photos.filter((photo) => view === 'country' ? photo.country === country : photo.selected);
    $('gallery-title').textContent = view === 'country' ? country || 'Destination' : 'Highlights.';
    $('gallery-description').textContent = view === 'country' ? `A collection of moments from ${country || 'the journey'}.` : 'A few moments I keep coming back to.';
    $('collection-count').textContent = `${visiblePhotos.length} photographs`;
    if (view === 'country' && !catalogue.countries.includes(country)) {
      showStatus('This destination is not in the collection. Explore all destinations using the link above.');
      return;
    }
    if (!visiblePhotos.length) {
      $('empty-state').hidden = false;
      showStatus('No photographs in this collection yet.');
    } else {
      renderPhotos();
    }
  }

  function renderPhotos() {
    const fragment = document.createDocumentFragment();
    for (let index = 0; index < visiblePhotos.length; index += 1) {
      const photo = visiblePhotos[index];
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'photo-item';
      button.setAttribute('aria-label', `View ${photo.title || photo.alt}, photograph ${index + 1} of ${visiblePhotos.length}`);
      const image = photoImage(photo, '(max-width: 600px) 88vw, (max-width: 900px) 44vw, 29vw');
      image.addEventListener('error', () => {
        button.classList.add('failed');
        button.textContent = 'Photograph unavailable — open to retry';
      }, { once: true });
      const hint = document.createElement('span');
      hint.className = 'photo-hint';
      hint.setAttribute('aria-hidden', 'true');
      hint.textContent = '↗';
      button.append(image, hint);
      button.addEventListener('click', () => openViewer(index, button));
      fragment.append(button);
    }
    grid.append(fragment);

  }

  function renderDestinations() {
    const fragment = document.createDocumentFragment();
    for (const country of catalogue.countries) {
      const photos = catalogue.photos.filter((photo) => photo.country === country);
      const cover = photos.find((photo) => photo.id === catalogue.covers[country]) || photos[0];
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'destination';
      button.setAttribute('aria-label', `${country}, ${photos.length ? `${photos.length} photographs` : 'photographs coming soon'}`);
      const frame = document.createElement('div');
      frame.className = cover ? 'destination-image' : 'destination-empty';
      if (cover) {
        const image = photoImage(cover, '(max-width: 900px) 44vw, 29vw');
        image.alt = '';
        image.addEventListener('error', () => { image.hidden = true; }, { once: true });
        frame.append(image);
      } else {
        const note = document.createElement('span');
        note.textContent = 'Coming soon';
        frame.append(note);
      }
      const meta = document.createElement('div');
      meta.className = 'destination-meta';
      const title = document.createElement('h3');
      title.textContent = country;
      const count = document.createElement('span');
      count.textContent = photos.length ? `${photos.length} photographs ↗` : 'A story still to come';
      meta.append(title, count);
      button.append(frame, meta);
      button.addEventListener('click', () => routeTo(`#country=${encodeURIComponent(country)}`));
      fragment.append(button);
    }
    destinations.append(fragment);
  }

  function updateViewer() {
    const photo = visiblePhotos[currentPhoto];
    if (!photo) return;
    $('viewer-error').hidden = true;
    viewerImage.classList.add('loading');
    viewerImage.alt = photo.alt;
    viewerImage.src = photo.src;
    $('viewer-caption').textContent = photo.title || photo.country || 'Highlights';
    $('viewer-counter').textContent = `${String(currentPhoto + 1).padStart(2, '0')} / ${visiblePhotos.length}`;
    $('viewer-previous').hidden = visiblePhotos.length < 2;
    $('viewer-next').hidden = visiblePhotos.length < 2;
  }

  function openViewer(index, button) {
    currentPhoto = index;
    openingButton = button;
    updateViewer();
    dialog.showModal();
    document.body.classList.add('viewer-open');
  }

  function stepViewer(amount) {
    currentPhoto = (currentPhoto + amount + visiblePhotos.length) % visiblePhotos.length;
    updateViewer();
  }

  viewerImage.addEventListener('load', () => viewerImage.classList.remove('loading'));
  viewerImage.addEventListener('error', () => {
    viewerImage.classList.remove('loading');
    $('viewer-error').hidden = false;
  });
  $('viewer-close').addEventListener('click', () => dialog.close());
  $('viewer-previous').addEventListener('click', () => stepViewer(-1));
  $('viewer-next').addEventListener('click', () => stepViewer(1));
  dialog.addEventListener('close', () => {
    document.body.classList.remove('viewer-open');
    viewerImage.removeAttribute('src');
    openingButton?.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog || event.target.classList.contains('viewer-stage')) dialog.close();
  });
  dialog.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      stepViewer(event.key === 'ArrowRight' ? 1 : -1);
    }
  });
  dialog.addEventListener('touchstart', (event) => {
    touchStart = event.touches.length === 1 ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
  }, { passive: true });
  dialog.addEventListener('touchend', (event) => {
    if (!touchStart || !event.changedTouches.length) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5 && (window.visualViewport?.scale || 1) <= 1) stepViewer(dx < 0 ? 1 : -1);
    touchStart = null;
  }, { passive: true });

  $('back-button').addEventListener('click', () => routeTo('#destinations'));
  $('empty-back').addEventListener('click', () => routeTo('#destinations'));
  window.addEventListener('hashchange', () => {
    if (dialog.open) dialog.close();
    renderRoute();
  });
  const observer = new IntersectionObserver(([entry]) => {
    $('site-header').classList.toggle('scrolled', !entry.isIntersecting);
  }, { rootMargin: '-85px 0px 0px 0px' });
  if ($('home')) observer.observe($('home'));
  else $('site-header').classList.add('scrolled');
  $('copyright-year').textContent = new Date().getFullYear();

  async function loadCatalogue() {
    showStatus('Loading the photographs…');
    try {
      const response = await fetch('data/photos.json');
      if (!response.ok) throw new Error(`Catalogue request failed: ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.photos) || !Array.isArray(data.countries)) throw new Error('Invalid photo catalogue');
      catalogue = data;
      for (const role of ['hero', 'portrait']) {
        const photo = catalogue.photos.find((item) => item.id === catalogue[role]);
        const image = $(`${role}-image`);
        if (photo && image && !image.getAttribute('src')) {
          image.src = photo.src;
          image.width = photo.width;
          image.height = photo.height;
        }
      }
      renderRoute();
      if (location.hash === '#destinations' || location.hash.startsWith('#country=') || location.hash === '#selected') $('gallery').scrollIntoView({ behavior: 'instant' });
      else if (['#about', '#gallery', '#travelbook'].includes(location.hash)) document.querySelector(location.hash)?.scrollIntoView({ behavior: 'instant' });
    } catch (error) {
      showStatus('The collection couldn’t load. Please try again.');
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'retry-button';
      retry.textContent = 'Retry';
      retry.addEventListener('click', loadCatalogue, { once: true });
      status.append(retry);
      console.error(error);
    }
  }
  loadCatalogue();
})();
