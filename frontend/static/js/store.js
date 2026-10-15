const API_BASE = window.location.origin;

const grid = document.getElementById("product-grid");
const categoriesContainer = document.getElementById("categories");
const categoryStatus = document.getElementById("category-status");
const productCount = document.getElementById("product-count");
const catalogError = document.getElementById("catalog-error");
const sortSelect = document.getElementById("sort-products");

let products = [];
let selectedCategory = "all";

document.getElementById("year").textContent = new Date().getFullYear();

function imageAddress(path) {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function formatPrice(price) {
  return new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 0
  }).format(price);
}

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function renderCategories(categories) {
  categoriesContainer.innerHTML = `
    <button class="category-chip active" data-category="all">ALL PIECES</button>
    ${categories.map(category => `
      <button class="category-chip" data-category="${category.id}">
        ${escapeHTML(category.name.toUpperCase())}
      </button>
    `).join("")}
  `;

  categoriesContainer.addEventListener("click", event => {
    const button = event.target.closest("[data-category]");
    if (!button) return;

    selectedCategory = button.dataset.category;
    categoriesContainer.querySelectorAll(".category-chip").forEach(chip => {
      chip.classList.toggle("active", chip === button);
    });
    renderProducts();
  });
}

function productCard(product) {
  const image = imageAddress(product.image_url);
  const category = product.category?.name || "EVA ATELIER";
  const isSaved = window.EVA_WISHLIST?.isSaved(product.id) || false;

  return `
    <article class="product-card">
      <div class="product-image-wrap">
        <a class="product-image-link" href="/product/${product.id}" aria-label="View ${escapeHTML(product.name)}">
          ${image
            ? `<img src="${escapeHTML(image)}" alt="${escapeHTML(product.name)}" loading="lazy"
                 onerror="this.style.display='none';this.nextElementSibling.hidden=false">`
            : ""}
          <div class="image-fallback" ${image ? "hidden" : ""}>
            <span>EVA ATELIER</span>
            <span>THE EVERYDAY EDIT</span>
          </div>
        </a>

        ${!product.in_stock ? '<span class="stock-label">SOLD OUT</span>' : ""}

        <button type="button" class="wishlist-toggle"
          data-wishlist-toggle="${Number(product.id)}"
          aria-label="${isSaved ? "Remove from wishlist" : "Save to wishlist"}"
          aria-pressed="${isSaved}" title="${isSaved ? "Remove from wishlist" : "Save to wishlist"}">
          ${isSaved ? "♥" : "♡"}
        </button>
      </div>

      <div class="product-info">
        <div>
          <p class="product-category">${escapeHTML(category)}</p>
          <h3><a href="/product/${product.id}">${escapeHTML(product.name)}</a></h3>
        </div>
        <span class="product-price">${formatPrice(product.price)}</span>
      </div>

      <p class="product-description">${escapeHTML(product.description || "")}</p>

      <button type="button" class="eva-add-to-bag"
        data-add-product="${product.id}" ${!product.in_stock ? "disabled" : ""}>
        ${product.in_stock ? "ADD TO CART" : "CURRENTLY UNAVAILABLE"}
      </button>
    </article>
  `;
}

function renderProducts() {
  const sort = sortSelect.value;
  let visible = products.filter(product =>
    selectedCategory === "all" ||
    String(product.category_id) === String(selectedCategory)
  );

  if (sort === "price-low") visible.sort((a, b) => a.price - b.price);
  if (sort === "price-high") visible.sort((a, b) => b.price - a.price);
  if (sort === "name") visible.sort((a, b) => a.name.localeCompare(b.name));

  productCount.textContent = `${visible.length} ${visible.length === 1 ? "PIECE" : "PIECES"}`;

  if (!visible.length) {
    grid.innerHTML = `<p class="empty-state">No pieces in this collection just yet.</p>`;
    return;
  }

  grid.innerHTML = visible.map(productCard).join("");
}

async function loadStore() {
  try {
    const [productsResponse, categoriesResponse] = await Promise.all([
      fetch(`${API_BASE}/products/`),
      fetch(`${API_BASE}/categories/`)
    ]);

    if (!productsResponse.ok || !categoriesResponse.ok) {
      throw new Error("The store API returned an error.");
    }

    products = await productsResponse.json();
    const categories = await categoriesResponse.json();

    renderCategories(categories);
    renderProducts();
    categoryStatus?.remove();
  } catch (error) {
    console.error("Could not load EVA Atelier catalog:", error);
    grid.innerHTML = "";
    catalogError.hidden = false;
    catalogError.textContent =
      "We couldn't load the collection. Please check that the EVA Atelier server is running and try again.";
    categoryStatus.textContent = "Categories are temporarily unavailable.";
  }
}

sortSelect.addEventListener("change", renderProducts);

document.querySelectorAll("[data-category-link]").forEach(link => {
  link.addEventListener("click", () => {
    selectedCategory = link.dataset.categoryLink;
    document.querySelectorAll(".category-chip").forEach(chip => {
      chip.classList.toggle("active", chip.dataset.category === selectedCategory);
    });
    renderProducts();
    document.getElementById("collection").scrollIntoView({ behavior: "smooth" });
  });
});

document.getElementById("menu-toggle").addEventListener("click", () => {
  document.getElementById("main-nav").classList.toggle("nav-open");
});

loadStore();


document.addEventListener("click", event => {
  const button = event.target.closest("[data-add-product]");
  if (!button) return;

  const product = products.find(
    item => Number(item.id) === Number(button.dataset.addProduct)
  );

  if (product && window.EVA_CART) {
    window.EVA_CART.add(product);
  }
});
