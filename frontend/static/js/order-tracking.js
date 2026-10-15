(() => {
  "use strict";

  const form = document.getElementById("tracking-form");
  const message = document.getElementById("tracking-message");
  const result = document.getElementById("tracking-result");
  const submit = document.getElementById("tracking-submit");
  if (!form || !message || !result || !submit) return;

  const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);

  const money = value => new Intl.NumberFormat("en-NP", {
    style: "currency", currency: "NPR", maximumFractionDigits: 2
  }).format(Number(value) || 0);

  const steps = ["pending", "confirmed", "processing", "shipped", "delivered"];

  function renderOrder(order) {
    const status = String(order.status || "pending").toLowerCase();
    const cancelled = status === "cancelled";
    const current = steps.indexOf(status);
    const date = order.created_at
      ? new Date(order.created_at).toLocaleString("en-NP", { dateStyle: "medium", timeStyle: "short" })
      : "Date unavailable";

    const timeline = cancelled
      ? `<div class="tracking-cancelled"><strong>Order cancelled</strong><p>Please contact EVA Atelier if you need assistance.</p></div>`
      : `<ol class="tracking-steps">${steps.map((step, index) => {
          const complete = current >= index;
          return `<li class="${complete ? "is-complete" : ""} ${current === index ? "is-current" : ""}">
            <span class="tracking-step-dot">${complete ? "✓" : index + 1}</span>
            <span class="tracking-step-label">${step.charAt(0).toUpperCase() + step.slice(1)}</span>
          </li>`;
        }).join("")}</ol>`;

    const items = Array.isArray(order.items) ? order.items : [];
    result.innerHTML = `
      <div class="tracking-result-heading">
        <div><p class="eyebrow">ORDER REFERENCE</p><h2>${escapeHTML(order.order_number)}</h2></div>
        <span class="tracking-status">${escapeHTML(status.replaceAll("_", " "))}</span>
      </div>
      <p class="tracking-date">Placed ${escapeHTML(date)}</p>
      <div class="tracking-timeline-wrap">
        <h3>Order progress</h3>${timeline}
      </div>
      <div class="tracking-summary">
        <h3>Order summary</h3>
        ${items.map(item => `<div class="tracking-item">
          <span>${escapeHTML(item.product_name)} <span class="tracking-quantity">× ${Number(item.quantity) || 0}</span></span>
          <strong>${money(item.line_total)}</strong>
        </div>`).join("")}
        <div class="tracking-item tracking-total"><span>Total</span><strong>${money(order.total)}</strong></div>
        <div class="tracking-item"><span>Payment status</span><strong>${escapeHTML(order.payment_status || "Unavailable")}</strong></div>
      </div>`;

    result.hidden = false;
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    result.hidden = true;
    message.textContent = "Verifying your order…";
    message.classList.remove("is-error");
    submit.disabled = true;
    submit.textContent = "CHECKING…";

    try {
      const response = await fetch(`${window.location.origin}/orders/track`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_number: form.elements.order_number.value.trim(),
          customer_phone: form.elements.customer_phone.value.trim()
        })
      });
      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(body.detail || "We couldn't verify that order. Check your details and try again.");
      }

      message.textContent = "Your order details are verified.";
      renderOrder(body);
    } catch (error) {
      message.textContent = error.message || "A network error occurred. Please try again.";
      message.classList.add("is-error");
    } finally {
      submit.disabled = false;
      submit.innerHTML = "TRACK MY ORDER <span>→</span>";
    }
  });
})();
