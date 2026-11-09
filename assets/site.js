(() => {
  const pl = document.documentElement.lang === "pl";
  const copy = pl
    ? {
        required: "Uzupełnij to pole.",
        email: "Podaj poprawny adres e-mail.",
        sending: "Wysyłanie…",
        success: "Dziękuję. Wiadomość została wysłana.",
        failure:
          "Nie udało się wysłać wiadomości. Twoja treść pozostała w formularzu — spróbuj ponownie.",
      }
    : {
        required: "Please complete this field.",
        email: "Please enter a valid email address.",
        sending: "Sending…",
        success: "Thank you. Your message has been sent.",
        failure:
          "Your message could not be sent. Your text is still in the form — please try again.",
      };
  document.querySelector("#year").textContent = new Date().getFullYear();
  const dialog = document.querySelector("#mobileMenu");
  const trigger = document.querySelector("#menuBtn");
  const close = () => dialog.close();
  trigger.addEventListener("click", () => {
    dialog.showModal();
    trigger.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  });
  dialog.querySelector("button").addEventListener("click", close);
  dialog
    .querySelectorAll("a")
    .forEach((link) => link.addEventListener("click", close));
  dialog.addEventListener("close", () => {
    trigger.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    trigger.focus();
  });
  dialog.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    const items = [...dialog.querySelectorAll("a[href], button")];
    const first = items[0],
      last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
  matchMedia("(min-width: 900px)").addEventListener("change", (event) => {
    if (event.matches && dialog.open) close();
  });
  const form = document.querySelector("#contactForm");
  if (!form) return;
  const status = document.querySelector("#formStatus");
  const button = form.querySelector("[type=submit]");
  const idleContent = [...button.childNodes].map((node) =>
    node.cloneNode(true),
  );
  const fields = [...form.querySelectorAll("input, textarea")];
  const validate = (field) => {
    field.setCustomValidity("");
    if (!field.value.trim()) field.setCustomValidity(copy.required);
    else if (field.validity.typeMismatch) field.setCustomValidity(copy.email);
  };
  fields.forEach((field) =>
    field.addEventListener("input", () => {
      field.setCustomValidity("");
      field.removeAttribute("aria-invalid");
    }),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (form.getAttribute("aria-busy") === "true") return;
    fields.forEach((field) => {
      validate(field);
      field.setAttribute("aria-invalid", String(!field.validity.valid));
    });
    if (!form.reportValidity()) return;
    form.setAttribute("aria-busy", "true");
    button.disabled = true;
    button.textContent = copy.sending;
    status.textContent = copy.sending;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Submission rejected");
      status.textContent = copy.success;
      form.reset();
      fields.forEach((field) => field.removeAttribute("aria-invalid"));
    } catch {
      status.textContent = copy.failure;
    } finally {
      clearTimeout(timeout);
      form.removeAttribute("aria-busy");
      button.disabled = false;
      button.replaceChildren(
        ...idleContent.map((node) => node.cloneNode(true)),
      );
    }
  });
  // Keep native HTML validation available when JavaScript is unavailable.
  form.noValidate = true;
})();
