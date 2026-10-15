const API = window.location.origin;
const productId = window.location.pathname.split("/").filter(Boolean).pop();
const $ = id => document.getElementById(id);

function formatPrice(value) {
  return new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 2
  }).format(Number(value) || 0);
}

async function loadProduct() {
  try {
    const response = await fetch(
      `${API}/products/${encodeURIComponent(productId)}`
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("This product could not be found.");
      }
      throw new Error("We couldn't load this product. Please try again.");
    }

    const product = await response.json();

    document.title = `${product.name} | EVA Atelier`;
    $("breadcrumb-name").textContent = product.name;
    $("detail-category").textContent = product.category?.name || "EVA ATELIER";
    $("detail-name").textContent = product.name;
    $("detail-sku").textContent = `PRODUCT CODE · ${product.sku}`;
    $("detail-price").textContent = formatPrice(product.price);
    $("detail-description").textContent =
      product.description || "A considered piece from EVA Atelier.";

    $("detail-stock").textContent = product.in_stock
      ? "Available"
      : "Currently out of stock";
    $("detail-stock").classList.toggle("out-of-stock", !product.in_stock);

    if (product.image_url) {
      const imagePath = /^https?:\/\//i.test(product.image_url)
        ? product.image_url
        : `${API}${product.image_url.startsWith("/") ? "" : "/"}${product.image_url}`;

      $("detail-image").src = imagePath;
      $("detail-image").alt = product.name;
      $("detail-image").addEventListener("error", () => {
        $("detail-image").hidden = true;
        $("detail-image-fallback").hidden = false;
      }, { once: true });
    } else {
      $("detail-image").hidden = true;
      $("detail-image-fallback").hidden = false;
    }

    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.className = "button button-dark detail-add-to-bag";
    addButton.textContent = product.in_stock ? "ADD TO CART" : "CURRENTLY UNAVAILABLE";
    addButton.disabled = !product.in_stock;
    addButton.addEventListener("click", () => {
      if (window.EVA_CART) {
        window.EVA_CART.add(product);
      } else {
        alert("The shopping bag is still loading. Please try again.");
      }
    });

    $("detail-add-to-bag")?.remove();
    addButton.id = "detail-add-to-bag";

    const backLink = document.querySelector(".detail-back");
    backLink.parentNode.insertBefore(addButton, backLink);

    $("loading-message").hidden = true;
    $("product-detail").hidden = false;
  } catch (error) {
    $("loading-message").hidden = true;
    $("error-message").textContent = error.message;
    $("error-message").hidden = false;
  }
}

loadProduct();
