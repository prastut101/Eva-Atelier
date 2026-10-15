(() => {
  "use strict";

  const KEY = "eva_atelier_wishlist_v1";
  const API = window.location.origin;

  function getIds() {
    try {
      const value = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(value)
        ? [...new Set(value.map(Number).filter(id => Number.isInteger(id) && id > 0))]
        : [];
    } catch {
      return [];
    }
  }

  function saveIds(ids) {
    localStorage.setItem(KEY, JSON.stringify([...new Set(ids)]));
    document.dispatchEvent(new CustomEvent("eva:wishlist-changed"));
  }

  function toggle(id) {
    const ids = getIds();
    saveIds(ids.includes(Number(id))
      ? ids.filter(item => item !== Number(id))
      : [...ids, Number(id)]);
    return getIds().includes(Number(id));
  }

  function remove(id) {
    saveIds(getIds().filter(item => item !== Number(id)));
  }

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[c]);
  }

  function imageAddress(path) {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;
    return `${API}${path.startsWith("/") ? path : `/${path}`}`;
  }

  function money(value) {
    return new Intl.NumberFormat("en-NP", {
      style: "currency", currency: "NPR", maximumFractionDigits: 0
    }).format(Number(value) || 0);
  }

  async function renderPage() {
    const grid = document.getElementById("wishlist-grid");
    const message = document.getElementById("wishlist-message");
    if (!grid || !message) return;

    const ids = getIds();
    if (!ids.length) {
      grid.innerHTML = "";
      message.innerHTML = `Your wishlist is currently empty. <a href="/#collection">Explore the collection</a> and save the pieces that speak to you.`;
      return;
    }

    try {
      const response = await fetch(`${API}/products/`);
      if (!response.ok) throw new Error("Could not load products.");
      const products = await response.json();
      const saved = ids.map(id => products.find(p => Number(p.id) === id)).filter(Boolean);

      if (!saved.length) {
        grid.innerHTML = "";
        message.innerHTML = `No saved pieces are available right now. <a href="/#collection">Return to the collection</a>.`;
        return;
      }

      message.textContent = `${saved.length} saved ${saved.length === 1 ? "piece" : "pieces"}`;
      grid.innerHTML = saved.map(product => {
        const image = imageAddress(product.image_url);
        return `
          <article class="feature-product">
            <a class="feature-product-image" href="/product/${Number(product.id)}">
              ${image
                ? `<img src="${escapeHTML(image)}" alt="${escapeHTML(product.name)}" loading="lazy">`
                : `<span class="feature-image-fallback">EVA ATELIER</span>`}
            </a>
            <div class="feature-product-info">
              <p class="eyebrow">${escapeHTML(product.category?.name || "EVA ATELIER")}</p>
              <h2><a href="/product/${Number(product.id)}">${escapeHTML(product.name)}</a></h2>
              <p class="feature-product-price">${money(product.price)}</p>
              <div class="feature-product-actions">
                <button type="button" class="feature-button"
                  data-wishlist-add="${Number(product.id)}"
                  ${product.in_stock ? "" : "disabled"}>
                  ${product.in_stock ? "ADD TO BAG" : "SOLD OUT"}
                </button>
                <button type="button" class="feature-text-button"
                  data-wishlist-remove="${Number(product.id)}">REMOVE</button>
              </div>
            </div>
          </article>`;
      }).join("");
    } catch (error) {
      console.error(error);
      message.textContent = "We couldn't load your saved pieces. Please refresh and try again.";
    }
  }

  document.addEventListener("click", event => {
    const removeButton = event.target.closest("[data-wishlist-remove]");
    if (removeButton) {
      remove(Number(removeButton.dataset.wishlistRemove));
      renderPage();
      return;
    }

    const addButton = event.target.closest("[data-wishlist-add]");
    if (addButton) {
      const id = Number(addButton.dataset.wishlistAdd);
      const productId = id;
      fetch(`${API}/products/${productId}`)
        .then(response => {
          if (!response.ok) throw new Error("Product is unavailable.");
          return response.json();
        })
        .then(product => {
          if (!window.EVA_CART) throw new Error("Shopping bag is not ready. Refresh and try again.");
          window.EVA_CART.add(product);
        })
        .catch(error => {
          alert(error.message || "Couldn't add this piece to your bag.");
        });
      return;
    }

    const heart = event.target.closest("[data-wishlist-toggle]");
    if (heart) {
      const saved = toggle(Number(heart.dataset.wishlistToggle));
      heart.setAttribute("aria-pressed", String(saved));
      heart.textContent = saved ? "♥" : "♡";
      heart.setAttribute("aria-label", saved ? "Remove from wishlist" : "Save to wishlist");
    }
  });

  window.EVA_WISHLIST = {
    getIds,
    toggle,
    isSaved: id => getIds().includes(Number(id))
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderPage, { once: true });
  } else {
    renderPage();
  }
})();
