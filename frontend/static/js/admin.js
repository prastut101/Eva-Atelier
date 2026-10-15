const API = window.location.origin;
const TOKEN_KEY = "eva_admin_token";

const $ = (id) => document.getElementById(id);
let token = sessionStorage.getItem(TOKEN_KEY);
let products = [];
let categories = [];

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;"
  })[char]);
}

function money(value) {
  return new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 2
  }).format(Number(value) || 0);
}

function imageURL(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${API}${path.startsWith("/") ? path : `/${path}`}`;
}

function setMessage(id, message, success = false) {
  const element = $(id);
  element.textContent = message;
  element.classList.toggle("success", success);
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});

  if (token) headers.set("Authorization", `Bearer ${token}`);

  // Do not set Content-Type for FormData: the browser sets its boundary.
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    logout();
    throw new Error("Your session has expired. Please sign in again.");
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(
      typeof detail === "string" ? detail : `Request failed (${response.status}).`
    );
  }

  return data;
}

function showDashboard() {
  $("login-screen").hidden = true;
  $("dashboard").hidden = false;
}

function showLogin() {
  $("login-screen").hidden = false;
  $("dashboard").hidden = true;
}

function logout() {
  token = null;
  sessionStorage.removeItem(TOKEN_KEY);
  showLogin();
}

async function login(event) {
  event.preventDefault();
  const button = $("login-form").querySelector("button[type=submit]");
  button.disabled = true;
  setMessage("login-message", "Signing in…");

  try {
    const form = new URLSearchParams();
    form.set("username", $("username").value.trim());
    form.set("password", $("password").value);

    const response = await fetch(`${API}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "Login failed. Check your credentials.");
    }

    if (!data.access_token) throw new Error("The server did not return a token.");

    token = data.access_token;
    sessionStorage.setItem(TOKEN_KEY, token);
    $("password").value = "";
    showDashboard();

    try {
      await initializeDashboard();
    } catch (error) {
      setMessage("inventory-message", error.message);
    }
  } catch (error) {
    setMessage("login-message", error.message);
  } finally {
    button.disabled = false;
  }
}

async function loadCategories() {
  categories = await request("/categories/");

  $("product-category").innerHTML =
    '<option value="">Uncategorised</option>' +
    categories.map(category =>
      `<option value="${category.id}">${escapeHTML(category.name)}</option>`
    ).join("");

  $("filter-category").innerHTML =
    '<option value="all">All collections</option>' +
    categories.map(category =>
      `<option value="${category.id}">${escapeHTML(category.name)}</option>`
    ).join("");
}

async function loadProducts() {
  $("product-table-body").innerHTML =
    '<tr><td colspan="6" class="empty-row">Loading inventory…</td></tr>';

  products = await request("/products/");
  updateStats();
  renderProducts();
}

function updateStats() {
  $("total-products").textContent = products.length;
  $("available-products").textContent =
    products.filter(product => product.in_stock).length;
  $("soldout-products").textContent =
    products.filter(product => !product.in_stock).length;
}

function renderProducts() {
  const search = $("search-products").value.trim().toLowerCase();
  const categoryFilter = $("filter-category").value;
  const stockFilter = $("filter-stock").value;

  const visible = products.filter(product => {
    const matchesSearch =
      product.name.toLowerCase().includes(search) ||
      product.sku.toLowerCase().includes(search);

    const matchesCategory = categoryFilter === "all" ||
      String(product.category_id) === categoryFilter;

    const matchesStock = stockFilter === "all" ||
      (stockFilter === "in" && product.in_stock) ||
      (stockFilter === "out" && !product.in_stock);

    return matchesSearch && matchesCategory && matchesStock;
  });

  if (!visible.length) {
    $("product-table-body").innerHTML =
      '<tr><td colspan="6" class="empty-row">No matching products found.</td></tr>';
    return;
  }

  $("product-table-body").innerHTML = visible.map(product => {
    const image = imageURL(product.image_url);
    const category = product.category?.name || "Uncategorised";

    return `
      <tr>
        <td>
          <div class="product-cell">
            ${image
              ? `<img class="product-thumb" src="${escapeHTML(image)}" alt=""
                     onerror="this.style.visibility='hidden'">`
              : '<div class="product-thumb"></div>'}
            <div>
              <div class="product-name">${escapeHTML(product.name)}</div>
              <div class="product-subtitle">#${product.id}</div>
            </div>
          </div>
        </td>
        <td>${escapeHTML(product.sku)}</td>
        <td>${money(product.price)}</td>
        <td>${escapeHTML(category)}</td>
        <td>
          <span class="stock-badge ${product.in_stock ? "stock-in" : "stock-out"}">
            ${product.in_stock ? "IN STOCK" : "SOLD OUT"}
          </span>
        </td>
        <td>
          <div class="actions">
            <button class="action-button" data-action="edit" data-id="${product.id}">Edit</button>
            <button class="action-button action-delete" data-action="delete" data-id="${product.id}">Delete</button>
          </div>
        </td>
      </tr>`;
  }).join("");
}

async function uploadImage(productId, file) {
  if (!file) return;

  const form = new FormData();
  form.append("file", file);

  await request(`/products/${productId}/image`, {
    method: "POST",
    body: form
  });
}

function resetProductForm() {
  $("product-form").reset();
  $("product-id").value = "";
  $("product-stock").checked = true;
  $("editor-title").textContent = "Add a new piece";
  $("save-product").textContent = "Save product";
  $("cancel-edit").hidden = true;
  $("current-image-wrap").hidden = true;
  $("current-image").removeAttribute("src");
  setMessage("form-message", "");
}

function editProduct(id) {
  const product = products.find(item => item.id === id);
  if (!product) return;

  $("product-id").value = product.id;
  $("product-name").value = product.name;
  $("product-sku").value = product.sku;
  $("product-price").value = product.price;
  $("product-description").value = product.description || "";
  $("product-category").value = product.category_id ?? "";
  $("product-stock").checked = product.in_stock;

  $("editor-title").textContent = `Edit product #${product.id}`;
  $("save-product").textContent = "Update product";
  $("cancel-edit").hidden = false;

  if (product.image_url) {
    $("current-image").src = imageURL(product.image_url);
    $("current-image-wrap").hidden = false;
  } else {
    $("current-image-wrap").hidden = true;
  }

  setMessage("form-message", "");
  $("product-editor").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function saveProduct(event) {
  event.preventDefault();

  const id = $("product-id").value;
  const file = $("product-image").files[0];

  if (file && file.size > 5 * 1024 * 1024) {
    setMessage("form-message", "Image must be 5 MB or smaller.");
    return;
  }

  const payload = {
    name: $("product-name").value.trim(),
    sku: $("product-sku").value.trim(),
    price: Number($("product-price").value),
    description: $("product-description").value.trim(),
    category_id: $("product-category").value
      ? Number($("product-category").value) : null,
    in_stock: $("product-stock").checked
  };

  const button = $("save-product");
  button.disabled = true;
  setMessage("form-message", id ? "Updating product…" : "Creating product…");

  try {
    let product;

    if (id) {
      product = await request(`/products/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
    } else {
      product = await request("/products/", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    if (file) {
      setMessage("form-message", "Product saved. Uploading image…");
      await uploadImage(product.id, file);
    }

    resetProductForm();
    await loadProducts();

    setMessage(
      "inventory-message",
      "Product saved successfully.",
      true
    );
  } catch (error) {
    setMessage("form-message", error.message);
  } finally {
    button.disabled = false;
  }
}

async function deleteProduct(id) {
  const product = products.find(item => item.id === id);
  if (!product) return;

  const confirmed = window.confirm(
    `Delete "${product.name}" permanently? This action cannot be undone.`
  );
  if (!confirmed) return;

  try {
    await request(`/products/${id}`, { method: "DELETE" });
    if ($("product-id").value === String(id)) resetProductForm();
    await loadProducts();
    setMessage("inventory-message", "Product deleted.", true);
  } catch (error) {
    setMessage("inventory-message", error.message);
  }
}

async function initializeDashboard() {
  setMessage("inventory-message", "Loading dashboard…");
  await loadCategories();
  await loadProducts();
  setMessage("inventory-message", "");
}

$("login-form").addEventListener("submit", login);
$("logout-button").addEventListener("click", logout);
$("product-form").addEventListener("submit", saveProduct);
$("cancel-edit").addEventListener("click", resetProductForm);
$("reset-form").addEventListener("click", resetProductForm);
$("refresh-products").addEventListener("click", async () => {
  try {
    await loadProducts();
    setMessage("inventory-message", "Inventory refreshed.", true);
  } catch (error) {
    setMessage("inventory-message", error.message);
  }
});

["search-products", "filter-category", "filter-stock"].forEach(id => {
  $(id).addEventListener("input", renderProducts);
  $(id).addEventListener("change", renderProducts);
});

$("product-table-body").addEventListener("click", event => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  const id = Number(button.dataset.id);
  if (button.dataset.action === "edit") editProduct(id);
  if (button.dataset.action === "delete") deleteProduct(id);
});

if (token) {
  showDashboard();
  initializeDashboard().catch(error => {
    setMessage("inventory-message", error.message);
  });
} else {
  showLogin();
}
