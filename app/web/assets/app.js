(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const routes = {
    dashboard: "generator",
    generator: "generator",
    history: "history",
    guide: "guide",
    settings: "settings",
    about: "about",
  };
  const state = {
    password: "",
    visible: false,
    history: [],
    toastTimer: 0,
    busy: false,
  };

  const elements = {
    output: $("#password-output"),
    generate: $("#generate-password"),
    regenerate: $("#regenerate-password"),
    copy: $("#copy-password"),
    toggle: $("#toggle-password"),
    slider: $("#length-slider"),
    lengthValue: $("#length-value"),
    settingsSlider: $("#settings-length"),
    settingsLengthValue: $("#settings-length-value"),
    categories: $$('input[name="category"]'),
    settingsCategories: $$('input[name="category-setting"]'),
    excludeAmbiguous: $("#exclude-ambiguous"),
    settingsExcludeAmbiguous: $("#settings-exclude-ambiguous"),
    warning: $("#category-warning"),
    strengthLabel: $("#strength-label"),
    strengthTrack: $("#strength-track"),
    strengthFill: $("#strength-fill"),
    strengthMessage: $("#strength-message"),
    recentList: $("#recent-list"),
    historyList: $("#full-history-list"),
    historyCount: $("#history-count"),
    toast: $("#toast"),
    toastMessage: $("#toast-message"),
    sidebar: $("#sidebar"),
    mobileMenu: $("#mobile-menu"),
    breadcrumb: $("#breadcrumb-current"),
  };

  const svgIcon = (name) =>
    `<svg aria-hidden="true"><use href="#i-${name}"></use></svg>`;

  function showToast(message, kind = "success") {
    window.clearTimeout(state.toastTimer);
    elements.toastMessage.textContent = message;
    elements.toast.classList.toggle("error", kind === "error");
    elements.toast.classList.add("show");
    state.toastTimer = window.setTimeout(
      () => elements.toast.classList.remove("show"),
      3200,
    );
  }

  function updateLength() {
    const length = Number(elements.slider.value);
    const progress =
      ((length - Number(elements.slider.min)) /
        (Number(elements.slider.max) - Number(elements.slider.min))) *
      100;
    elements.lengthValue.value = `${length} characters`;
    elements.lengthValue.textContent = `${length} characters`;
    if (elements.settingsSlider && elements.settingsLengthValue) {
      elements.settingsSlider.value = String(length);
      elements.settingsLengthValue.value = `${length} characters`;
      elements.settingsLengthValue.textContent = `${length} characters`;
      elements.settingsSlider.style.setProperty("--range-progress", `${progress}%`);
    }
    elements.slider.style.setProperty("--range-progress", `${progress}%`);
  }

  function selectedCategories() {
    return elements.categories
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value);
  }

  function updateCategoryValidation() {
    const isValid = selectedCategories().length >= 2;
    elements.warning.hidden = isValid;
    elements.categories.forEach((checkbox) => {
      checkbox.setAttribute("aria-invalid", String(!isValid));
    });
    elements.settingsCategories.forEach((checkbox) => {
      const source = elements.categories.find(
        (category) => category.value === checkbox.value,
      );
      checkbox.checked = Boolean(source?.checked);
    });
    if (elements.settingsExcludeAmbiguous) {
      elements.settingsExcludeAmbiguous.checked = elements.excludeAmbiguous.checked;
    }
    elements.generate.disabled = !isValid || state.busy;
    elements.regenerate.disabled = !isValid || state.busy;
  }

  function setPasswordVisibility(visible) {
    state.visible = visible;
    elements.output.type = visible ? "text" : "password";
    elements.toggle.setAttribute("aria-pressed", String(visible));
    elements.toggle.setAttribute(
      "aria-label",
      visible ? "Hide password" : "Show password",
    );
  }

  function updateStrength(strength) {
    const colors = {
      WEAK: "#f47e73",
      MEDIUM: "#d5a846",
      STRONG: "#63b995",
    };
    const label = strength?.label || "NOT YET";
    const color = colors[label] || "#b7b3bd";
    elements.strengthLabel.textContent = label;
    elements.strengthLabel.style.color = color;
    elements.strengthLabel.style.backgroundColor = `${color}20`;
    elements.strengthFill.style.width = `${Math.max(
      0,
      Math.min(100, strength?.score || 0),
    )}%`;
    elements.strengthFill.style.backgroundColor = color;
    elements.strengthTrack.setAttribute(
      "aria-valuenow",
      String(strength?.score || 0),
    );
    elements.strengthMessage.textContent =
      strength?.message || "Make a password to see a little strength check.";
  }

  function formatTimestamp(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Just now";
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date);
  }

  async function copyPassword(password, feedback = true) {
    if (!password) {
      showToast("Make a password before copying it.", "error");
      return false;
    }
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("Clipboard access is unavailable in this browser.");
      }
      await navigator.clipboard.writeText(password);
      if (feedback) showToast("Copied. You're all set.");
      return true;
    } catch (error) {
      showToast(
        "Clipboard access was blocked. Select and copy the password instead.",
        "error",
      );
      return false;
    }
  }

  function renderHistory(target, entries, compact = false) {
    target.replaceChildren();
    if (entries.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML = `<span class="empty-icon">${svgIcon("spark")}</span><p>No passwords just yet.</p><small>Generate one and it will appear here for this session.</small>`;
      target.append(empty);
      return;
    }

    entries.forEach((entry, index) => {
      const row = document.createElement("article");
      row.className = "history-row";
      row.style.animationDelay = `${Math.min(index * 35, 175)}ms`;

      const main = document.createElement("div");
      main.className = "history-main";
      const password = document.createElement("input");
      password.className = "history-password";
      password.type = entry.visible ? "text" : "password";
      password.readOnly = true;
      password.value = entry.password;
      password.setAttribute("aria-label", "Password history item");
      const time = document.createElement("time");
      time.className = "history-time";
      time.dateTime = entry.generated_at;
      time.textContent = formatTimestamp(entry.generated_at);
      main.append(password, time);

      const actions = document.createElement("div");
      actions.className = "history-actions";
      const visibility = document.createElement("button");
      visibility.type = "button";
      visibility.className = "history-action";
      visibility.setAttribute(
        "aria-label",
        entry.visible ? "Hide this password" : "Show this password",
      );
      visibility.innerHTML = svgIcon(entry.visible ? "eye-off" : "eye");
      visibility.addEventListener("click", () => {
        entry.visible = !entry.visible;
        renderHistory(target, entries, compact);
      });

      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "history-action copy";
      copy.setAttribute("aria-label", "Copy this password");
      copy.innerHTML = svgIcon("copy");
      copy.addEventListener("click", () => copyPassword(entry.password));
      actions.append(visibility, copy);
      row.append(main, actions);
      target.append(row);
    });
  }

  function renderAllHistory() {
    const latest = state.history.slice(0, 5);
    elements.historyCount.textContent = String(latest.length);
    renderHistory(elements.recentList, latest.slice(0, 3), true);
    renderHistory(elements.historyList, latest);
    $("#clear-history").disabled = latest.length === 0;
  }

  async function requestJson(path, options = {}) {
    const response = await fetch(path, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
    let data;
    try {
      data = await response.json();
    } catch (error) {
      throw new Error("The local app returned an unreadable response.");
    }
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  async function loadHistory() {
    try {
      const data = await requestJson("/api/history");
      state.history = data.entries.map((entry) => ({ ...entry, visible: false }));
      renderAllHistory();
    } catch (error) {
      showToast("Couldn't load this session's history. Refresh to try again.", "error");
    }
  }

  async function generatePassword() {
    if (state.busy) return;
    const categories = selectedCategories();
    if (categories.length < 2) {
      updateCategoryValidation();
      showToast("Choose at least two character groups.", "error");
      return;
    }

    state.busy = true;
    elements.generate.disabled = true;
    elements.regenerate.disabled = true;
    elements.generate.classList.add("loading");
    elements.generate.setAttribute("aria-busy", "true");
    try {
      const data = await requestJson("/api/generate", {
        method: "POST",
        body: JSON.stringify({
          length: Number(elements.slider.value),
          categories,
          exclude_ambiguous: elements.excludeAmbiguous.checked,
        }),
      });
      state.password = data.password;
      elements.output.value = state.password;
      setPasswordVisibility(true);
      state.history = [
        { password: data.password, generated_at: data.generated_at, visible: false },
        ...state.history.filter((entry) => entry.password !== data.password),
      ].slice(0, 5);
      updateStrength(data.strength);
      renderAllHistory();
      navigate("generator", false);

      const copied = await copyPassword(state.password, false);
      showToast(
        copied
          ? "Your new password is ready and copied."
          : "Password ready. Clipboard permission wasn't available.",
        copied ? "success" : "error",
      );
    } catch (error) {
      showToast(error.message || "Couldn't make a password. Please try again.", "error");
    } finally {
      state.busy = false;
      elements.generate.classList.remove("loading");
      elements.generate.removeAttribute("aria-busy");
      updateCategoryValidation();
    }
  }

  async function clearHistory() {
    const button = $("#clear-history");
    if (button.disabled) return;
    button.disabled = true;
    try {
      await requestJson("/api/history", { method: "DELETE" });
      state.history = [];
      renderAllHistory();
      showToast("Session history cleared.");
    } catch (error) {
      button.disabled = false;
      showToast(error.message || "Couldn't clear the history.", "error");
    }
  }

  function navigate(route, updateHash = true) {
    const view = routes[route] || "generator";
    if (updateHash && window.location.hash !== `#${route}`) {
      window.history.pushState({ route }, "", `#${route}`);
    }
    $$(".view").forEach((section) => {
      const active = section.dataset.view === view;
      section.classList.toggle("active", active);
      section.hidden = !active;
    });
    $$(".nav-link").forEach((link) => {
      const active =
        link.dataset.route === route ||
        (route === "dashboard" && link.dataset.route === "generator");
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    elements.breadcrumb.textContent = {
      dashboard: "DASHBOARD",
      generator: "GENERATOR",
      history: "PASSWORD HISTORY",
      guide: "SECURITY GUIDE",
      settings: "SETTINGS",
      about: "ABOUT",
    }[route] || "GENERATOR";
    elements.sidebar.classList.remove("open");
    elements.mobileMenu.setAttribute("aria-expanded", "false");
    elements.mobileMenu.setAttribute("aria-label", "Open navigation");
    document.body.classList.remove("nav-open");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function setupReveal() {
    const revealItems = $$(".reveal");
    if (!("IntersectionObserver" in window)) {
      revealItems.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 },
    );
    revealItems.forEach((item) => observer.observe(item));
  }

  elements.slider.addEventListener("input", updateLength);
  elements.settingsSlider.addEventListener("input", () => {
    elements.slider.value = elements.settingsSlider.value;
    updateLength();
  });
  elements.categories.forEach((checkbox) =>
    checkbox.addEventListener("change", updateCategoryValidation),
  );
  elements.settingsCategories.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const source = elements.categories.find(
        (category) => category.value === checkbox.value,
      );
      if (source) source.checked = checkbox.checked;
      updateCategoryValidation();
    });
  });
  elements.settingsExcludeAmbiguous.addEventListener("change", () => {
    elements.excludeAmbiguous.checked = elements.settingsExcludeAmbiguous.checked;
  });
  elements.excludeAmbiguous.addEventListener("change", () => {
    elements.settingsExcludeAmbiguous.checked = elements.excludeAmbiguous.checked;
  });
  elements.generate.addEventListener("click", generatePassword);
  elements.regenerate.addEventListener("click", generatePassword);
  elements.copy.addEventListener("click", () => copyPassword(state.password));
  elements.toggle.addEventListener("click", () =>
    setPasswordVisibility(!state.visible),
  );
  $("#view-history").addEventListener("click", () => navigate("history"));
  $("#clear-history").addEventListener("click", clearHistory);
  elements.mobileMenu.addEventListener("click", () => {
    const open = !elements.sidebar.classList.contains("open");
    elements.sidebar.classList.toggle("open", open);
    elements.mobileMenu.setAttribute("aria-expanded", String(open));
    elements.mobileMenu.setAttribute(
      "aria-label",
      open ? "Close navigation" : "Open navigation",
    );
    document.body.classList.toggle("nav-open", open);
  });
  document.addEventListener("click", (event) => {
    const routeLink = event.target.closest("[data-route]");
    if (routeLink) {
      event.preventDefault();
      navigate(routeLink.dataset.route);
    } else if (
      elements.sidebar.classList.contains("open") &&
      !event.target.closest("#sidebar") &&
      !event.target.closest("#mobile-menu")
    ) {
      elements.sidebar.classList.remove("open");
      elements.mobileMenu.setAttribute("aria-expanded", "false");
      elements.mobileMenu.setAttribute("aria-label", "Open navigation");
      document.body.classList.remove("nav-open");
    }
  });
  window.addEventListener("popstate", () =>
    navigate(window.location.hash.slice(1) || "generator", false),
  );
  window.addEventListener("keydown", (event) => {
    if (
      event.key === "Enter" &&
      !event.repeat &&
      !["INPUT", "BUTTON", "A"].includes(document.activeElement?.tagName)
    ) {
      event.preventDefault();
      generatePassword();
    }
    if (event.key === "Escape" && elements.sidebar.classList.contains("open")) {
      elements.sidebar.classList.remove("open");
      elements.mobileMenu.setAttribute("aria-expanded", "false");
      elements.mobileMenu.setAttribute("aria-label", "Open navigation");
      document.body.classList.remove("nav-open");
      elements.mobileMenu.focus();
    }
  });

  updateLength();
  updateCategoryValidation();
  setupReveal();
  navigate(window.location.hash.slice(1) || "generator", false);
  loadHistory();
})();
