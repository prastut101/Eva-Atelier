(() => {
  "use strict";

  const STORAGE_KEY = "eva_atelier_cart_v1";
  const API = window.location.origin;

  let cart = [];
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    cart = Array.isArray(saved)
      ? saved.filter(item =>
          Number.isInteger(Number(item.id)) &&
          Number(item.id) > 0 &&
          Number.isInteger(Number(item.quantity)) &&
          Number(item.quantity) > 0
        )
      : [];
  } catch {
    cart = [];
  }

  const money = value => new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 2
  }).format(Number(value) || 0);

  const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[c]);

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
    updateCount();
  }

  function count() {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  }

  function total() {
    return cart.reduce(
      (sum, item) => sum + Number(item.price || 0) * item.quantity,
      0
    );
  }

  function updateCount() {
    const badge = document.getElementById("eva-cart-count");
    if (badge) badge.textContent = count();
    const button = document.getElementById("eva-cart-open");
    if (button) button.setAttribute("aria-label", `Open shopping bag, ${count()} items`);
  }

  function ensureUI() {
    if (document.getElementById("eva-cart-overlay")) return;

    document.body.insertAdjacentHTML("beforeend", `
      <button type="button" id="eva-cart-open" class="eva-cart-floating">
        BAG <span id="eva-cart-count">0</span>
      </button>

      <div id="eva-cart-overlay" class="eva-cart-overlay" hidden>
        <section class="eva-cart-panel" role="dialog"
          aria-modal="true" aria-labelledby="eva-cart-title">
          <div class="eva-cart-heading">
            <div>
              <p class="eva-cart-eyebrow">EVA ATELIER</p>
              <h2 id="eva-cart-title">Your bag</h2>
            </div>
            <button type="button" id="eva-cart-close"
              class="eva-cart-close" aria-label="Close bag">×</button>
          </div>

          <div id="eva-cart-items" class="eva-cart-items"></div>

          <div class="eva-cart-summary">
            <div class="eva-cart-total">
              <span>Subtotal</span>
              <strong id="eva-cart-subtotal">NPR 0</strong>
            </div>
            <p class="eva-cart-shipping">
              Delivery fees, if applicable, are confirmed at checkout.
            </p>
            <button type="button" id="eva-checkout-open"
              class="eva-cart-primary">PROCEED TO CHECKOUT</button>
          </div>

          <form id="eva-checkout-form" class="eva-checkout-form" hidden>
            <button type="button" id="eva-checkout-back"
              class="eva-checkout-back">← Back to bag</button>
            <p class="eva-cart-eyebrow">ALMOST YOURS</p>
            <h3>Delivery details</h3>

            <label for="eva-customer-name">Full name *</label>
            <input id="eva-customer-name" name="customer_name"
              autocomplete="name" minlength="2" maxlength="150" required>

            <label for="eva-customer-phone">Phone number *</label>
            <input id="eva-customer-phone" name="customer_phone"
              autocomplete="tel" type="tel" minlength="7" maxlength="30" required>

            <label for="eva-customer-email">Email address</label>
            <input id="eva-customer-email" name="customer_email"
              autocomplete="email" type="email" maxlength="254">

            <label for="eva-shipping-address">Delivery address *</label>
            <textarea id="eva-shipping-address" name="shipping_address"
              autocomplete="street-address" minlength="10" maxlength="2000"
              rows="3" required></textarea>

            <label for="eva-order-notes">Order notes (optional)</label>
            <textarea id="eva-order-notes" name="notes"
              maxlength="1000" rows="2"></textarea>

            <label for="eva-payment-method">Payment method *</label>
            <select id="eva-payment-method" name="payment_method" required>
              <option value="cod">Cash on Delivery</option>
              <option value="khalti">Khalti</option>
            </select>

            <div class="eva-cart-total eva-checkout-total">
              <span>Order total</span>
              <strong id="eva-checkout-total">NPR 0</strong>
            </div>

            <p id="eva-checkout-message" class="eva-checkout-message"
              role="status" aria-live="polite"></p>

            <button type="submit" id="eva-checkout-submit"
              class="eva-cart-primary">PLACE ORDER</button>

            <p class="eva-checkout-legal">
              Your order total is calculated by EVA Atelier's server.
            </p>
          </form>
        </section>
      </div>
    `);

    document.getElementById("eva-cart-open").addEventListener("click", open);
    document.getElementById("eva-cart-close").addEventListener("click", close);
    document.getElementById("eva-cart-overlay").addEventListener("click", event => {
      if (event.target.id === "eva-cart-overlay") close();
    });

    document.getElementById("eva-checkout-open").addEventListener("click", () => {
      if (!cart.length) return;
      document.getElementById("eva-cart-items").hidden = true;
      document.querySelector(".eva-cart-summary").hidden = true;
      document.getElementById("eva-checkout-form").hidden = false;
      document.getElementById("eva-checkout-total").textContent = money(total());
      document.getElementById("eva-checkout-message").textContent = "";
    });

    document.getElementById("eva-checkout-back").addEventListener("click", () => {
      document.getElementById("eva-checkout-form").hidden = true;
      document.getElementById("eva-cart-items").hidden = false;
      document.querySelector(".eva-cart-summary").hidden = false;
    });

    document.getElementById("eva-cart-items").addEventListener("click", event => {
      const button = event.target.closest("[data-cart-action]");
      if (!button) return;

      const id = Number(button.dataset.id);
      const item = cart.find(entry => Number(entry.id) === id);
      if (!item) return;

      const action = button.dataset.cartAction;
      if (action === "increase" && item.quantity < 20) item.quantity++;
      if (action === "decrease") item.quantity--;
      if (action === "remove") item.quantity = 0;

      cart = cart.filter(entry => entry.quantity > 0);
      save();
      render();
    });

    document.getElementById("eva-checkout-form").addEventListener("submit", submitOrder);

    document.addEventListener("keydown", event => {
      if (event.key === "Escape") close();
    });

    updateCount();
    render();
  }

  function open() {
    ensureUI();
    document.getElementById("eva-cart-overlay").hidden = false;
    render();
  }

  function close() {
    const overlay = document.getElementById("eva-cart-overlay");
    if (overlay) overlay.hidden = true;
  }

  function add(product) {
    if (!product || !Number.isInteger(Number(product.id))) {
      alert("This product could not be added. Please refresh and try again.");
      return;
    }

    if (product.in_stock === false) {
      alert("This piece is currently unavailable.");
      return;
    }

    const existing = cart.find(item => Number(item.id) === Number(product.id));

    if (existing) {
      if (existing.quantity >= 20) {
        alert("The maximum quantity per item is 20.");
        return;
      }
      existing.quantity++;
    } else {
      cart.push({
        id: Number(product.id),
        name: String(product.name || "EVA Atelier piece"),
        price: Number(product.price) || 0,
        image_url: String(product.image_url || ""),
        quantity: 1
      });
    }

    save();
    render();
    open();
  }

  function render() {
    const container = document.getElementById("eva-cart-items");
    if (!container) return;

    if (!cart.length) {
      container.innerHTML = `
        <div class="eva-cart-empty">
          <p>Your bag is waiting for something special.</p>
          <button type="button" id="eva-continue-shopping"
            class="eva-cart-secondary">CONTINUE SHOPPING</button>
        </div>`;
      document.getElementById("eva-continue-shopping").addEventListener("click", close);
    } else {
      container.innerHTML = cart.map(item => {
        const image = item.image_url
          ? (/^https?:\/\//i.test(item.image_url)
              ? item.image_url
              : `${API}${item.image_url.startsWith("/") ? "" : "/"}${item.image_url}`)
          : "";

        return `
          <article class="eva-cart-item">
            ${image
              ? `<img src="${escapeHTML(image)}" alt="" class="eva-cart-thumb">`
              : `<div class="eva-cart-thumb eva-cart-thumb-empty">EVA</div>`}
            <div class="eva-cart-item-info">
              <h3>${escapeHTML(item.name)}</h3>
              <p>${money(item.price)}</p>
              <div class="eva-cart-quantity">
                <button type="button" data-cart-action="decrease"
                  data-id="${item.id}" aria-label="Decrease quantity">−</button>
                <span>${item.quantity}</span>
                <button type="button" data-cart-action="increase"
                  data-id="${item.id}" aria-label="Increase quantity"
                  ${item.quantity >= 20 ? "disabled" : ""}>+</button>
                <button type="button" data-cart-action="remove"
                  data-id="${item.id}" class="eva-cart-remove">Remove</button>
              </div>
            </div>
            <strong class="eva-cart-line-total">
              ${money(item.price * item.quantity)}
            </strong>
          </article>`;
      }).join("");
    }

    document.getElementById("eva-cart-subtotal").textContent = money(total());
    document.getElementById("eva-checkout-total").textContent = money(total());
    updateCount();
  }

  async function submitOrder(event) {
    event.preventDefault();

    if (!cart.length) {
      showMessage("Your bag is empty.", true);
      return;
    }

    const form = event.currentTarget;
    if (!form.reportValidity()) return;

    const submit = document.getElementById("eva-checkout-submit");
    const method = document.getElementById("eva-payment-method").value;

    const payload = {
      customer_name: form.elements.customer_name.value.trim(),
      customer_phone: form.elements.customer_phone.value.trim(),
      customer_email: form.elements.customer_email.value.trim() || null,
      shipping_address: form.elements.shipping_address.value.trim(),
      notes: form.elements.notes.value.trim() || null,
      payment_method: method,
      items: cart.map(item => ({
        product_id: Number(item.id),
        quantity: Number(item.quantity)
      }))
    };

    submit.disabled = true;
    submit.textContent = "PROCESSING…";
    showMessage("Submitting your order securely…", false);

    try {
      const response = await fetch(`${API}/orders/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "We couldn't place your order. Please review your details and try again."
        );
      }

      // The server has saved the order. Do not resubmit it just because
      // Khalti initiation failed, as that could create a duplicate order.
      cart = [];
      save();
      render();

      if (method === "khalti" && body.payment_url) {
        showMessage("Order saved. Redirecting to Khalti…", false);
        window.location.assign(body.payment_url);
        return;
      }

      if (method === "khalti" && body.payment_error) {
        showMessage(
          `Order ${body.order_number} was saved, but payment could not start. ${body.payment_error}`,
          true
        );
        return;
      }

      form.reset();
      showMessage(
        `Thank you. Your order ${body.order_number} has been placed successfully.`,
        false
      );
    } catch (error) {
      showMessage(error.message || "A network error occurred. Please try again.", true);
    } finally {
      submit.disabled = false;
      submit.textContent = "PLACE ORDER";
    }
  }

  function showMessage(message, isError) {
    const element = document.getElementById("eva-checkout-message");
    if (!element) return;
    element.textContent = message;
    element.classList.toggle("is-error", Boolean(isError));
  }

  window.EVA_CART = { add, open, close };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureUI, { once: true });
  } else {
    ensureUI();
  }
})();
