document.addEventListener("DOMContentLoaded", () => {
  const state = {
    session: {
      authenticated: false,
      role: "consultant",
      display_name: "Consultant self-service",
      practice_areas: [],
    },
  };

  const capabilitiesList = document.getElementById("capabilities-list");
  const capabilitySelect = document.getElementById("capability");
  const registerForm = document.getElementById("register-form");
  const messageDiv = document.getElementById("message");
  const workflowTitle = document.getElementById("workflow-title");
  const workflowDescription = document.getElementById("workflow-description");
  const workflowNote = document.getElementById("workflow-note");
  const submitButton = document.getElementById("submit-button");
  const authStatus = document.getElementById("auth-status");
  const loginButton = document.getElementById("login-button");
  const logoutButton = document.getElementById("logout-button");
  const loginModal = document.getElementById("login-modal");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const cancelLoginButton = document.getElementById("cancel-login");
  const modalBackdrop = document.getElementById("modal-backdrop");
  const auditPanel = document.getElementById("audit-panel");
  const auditList = document.getElementById("audit-list");

  function showMessage(target, text, kind) {
    target.textContent = text;
    target.className = kind;
    target.classList.remove("hidden");
  }

  function hideMessage(target) {
    target.classList.add("hidden");
  }

  function canManage(details) {
    const practiceAreas = state.session.practice_areas || [];
    return state.session.authenticated && (practiceAreas.includes("*") || practiceAreas.includes(details.practice_area));
  }

  function updateWorkflowText() {
    if (state.session.authenticated) {
      workflowTitle.textContent = "Register or Review Consultants";
      workflowDescription.textContent = "Practice leads can register consultants directly, approve pending requests, and remove assignments for permitted practice areas.";
      workflowNote.textContent = "Pending requests appear on each capability card, and all management actions are written to the audit activity feed.";
      submitButton.textContent = "Register Consultant";
      authStatus.textContent = `${state.session.display_name} signed in as Practice Lead`;
      loginButton.classList.add("hidden");
      logoutButton.classList.remove("hidden");
      auditPanel.classList.remove("hidden");
    } else {
      workflowTitle.textContent = "Request Capability Access";
      workflowDescription.textContent = "Consultants can submit access requests for a practice lead to review. Direct capability changes require practice lead sign-in.";
      workflowNote.textContent = "Sign in as a practice lead to approve pending requests and manage consultant assignments.";
      submitButton.textContent = "Submit Access Request";
      authStatus.textContent = "Consultant self-service mode";
      loginButton.classList.remove("hidden");
      logoutButton.classList.add("hidden");
      auditPanel.classList.add("hidden");
    }
  }

  function populateCapabilitySelect(capabilities) {
    capabilitySelect.innerHTML = '<option value="">-- Select a capability --</option>';

    Object.keys(capabilities).forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      capabilitySelect.appendChild(option);
    });
  }

  function renderAuditLog(entries) {
    if (!entries.length) {
      auditList.innerHTML = "<li>No audit activity recorded yet.</li>";
      return;
    }

    auditList.innerHTML = entries
      .map((entry) => {
        const capabilityLabel = entry.capability_name ? ` on ${entry.capability_name}` : "";
        const consultantLabel = entry.consultant_email ? ` for ${entry.consultant_email}` : "";
        return `<li><strong>${entry.action.replaceAll("_", " ")}</strong> by ${entry.actor}${consultantLabel}${capabilityLabel}<span>${new Date(entry.timestamp).toLocaleString()}</span></li>`;
      })
      .join("");
  }

  function renderCapabilities(capabilities) {
    capabilitiesList.innerHTML = "";

    Object.entries(capabilities).forEach(([name, details]) => {
      const capabilityCard = document.createElement("div");
      capabilityCard.className = "capability-card";

      const consultantsHTML = details.consultants.length
        ? `<div class="consultants-section">
            <h5>Registered Consultants</h5>
            <ul class="consultants-list">
              ${details.consultants
                .map((email) => {
                  const actionButton = canManage(details)
                    ? `<button class="delete-btn" data-action="unregister" data-capability="${name}" data-email="${email}">Remove</button>`
                    : "";
                  return `<li><span class="consultant-email">${email}</span>${actionButton}</li>`;
                })
                .join("")}
            </ul>
          </div>`
        : "<p><em>No consultants registered yet</em></p>";

      const pendingHTML = canManage(details) && details.pending_requests.length
        ? `<div class="pending-section">
            <h5>Pending Requests</h5>
            <ul class="consultants-list pending-list">
              ${details.pending_requests
                .map(
                  (email) => `<li><span class="consultant-email">${email}</span><button class="approve-btn" data-action="approve" data-capability="${name}" data-email="${email}">Approve</button></li>`
                )
                .join("")}
            </ul>
          </div>`
        : "";

      const managementBadge = canManage(details)
        ? '<span class="management-badge">Practice lead access</span>'
        : "";

      capabilityCard.innerHTML = `
        <div class="card-header">
          <h4>${name}</h4>
          ${managementBadge}
        </div>
        <p>${details.description}</p>
        <p><strong>Practice Area:</strong> ${details.practice_area}</p>
        <p><strong>Industry Verticals:</strong> ${details.industry_verticals.join(", ")}</p>
        <p><strong>Capacity:</strong> ${details.capacity} hours/week available</p>
        <p><strong>Current Team:</strong> ${details.consultants.length} consultants</p>
        <div class="consultants-container">
          ${consultantsHTML}
          ${pendingHTML}
        </div>
      `;

      capabilitiesList.appendChild(capabilityCard);
    });
  }

  async function fetchSession() {
    const response = await fetch("/auth/session", { credentials: "same-origin" });
    state.session = await response.json();
    updateWorkflowText();
  }

  async function fetchCapabilities() {
    try {
      const response = await fetch("/capabilities", { credentials: "same-origin" });
      const capabilities = await response.json();
      populateCapabilitySelect(capabilities);
      renderCapabilities(capabilities);
    } catch (error) {
      capabilitiesList.innerHTML = "<p>Failed to load capabilities. Please try again later.</p>";
      console.error("Error fetching capabilities:", error);
    }
  }

  async function fetchAuditLog() {
    if (!state.session.authenticated) {
      return;
    }

    try {
      const response = await fetch("/audit-log", { credentials: "same-origin" });
      const entries = await response.json();
      renderAuditLog(entries);
    } catch (error) {
      auditList.innerHTML = "<li>Unable to load audit activity.</li>";
      console.error("Error fetching audit log:", error);
    }
  }

  async function refreshApp() {
    await fetchSession();
    await fetchCapabilities();
    if (state.session.authenticated) {
      await fetchAuditLog();
    }
  }

  async function handleCapabilityAction(event) {
    const button = event.target.closest("button[data-action]");
    if (!button) {
      return;
    }

    const capability = button.getAttribute("data-capability");
    const email = button.getAttribute("data-email");
    const action = button.getAttribute("data-action");

    try {
      let response;

      if (action === "unregister") {
        response = await fetch(
          `/capabilities/${encodeURIComponent(capability)}/unregister?email=${encodeURIComponent(email)}`,
          {
            method: "DELETE",
            credentials: "same-origin",
          }
        );
      } else if (action === "approve") {
        response = await fetch(`/capabilities/${encodeURIComponent(capability)}/approve-request`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email }),
        });
      }

      const result = await response.json();

      if (response.ok) {
        showMessage(messageDiv, result.message, "success");
        await refreshApp();
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "The requested change could not be completed.", "error");
      console.error("Capability action failed:", error);
    }
  }

  function openLoginModal() {
    loginModal.classList.remove("hidden");
    loginModal.setAttribute("aria-hidden", "false");
    hideMessage(loginMessage);
  }

  function closeLoginModal() {
    loginModal.classList.add("hidden");
    loginModal.setAttribute("aria-hidden", "true");
    loginForm.reset();
    hideMessage(loginMessage);
  }

  capabilitiesList.addEventListener("click", handleCapabilityAction);

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const capability = capabilitySelect.value;
    const endpoint = state.session.authenticated ? "register" : "request-access";

    try {
      const response = await fetch(`/capabilities/${encodeURIComponent(capability)}/${endpoint}`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();
      if (response.ok) {
        showMessage(messageDiv, result.message, "success");
        registerForm.reset();
        await refreshApp();
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "Failed to submit the request.", "error");
      console.error("Form submission failed:", error);
    }
  });

  loginButton.addEventListener("click", openLoginModal);
  cancelLoginButton.addEventListener("click", closeLoginModal);
  modalBackdrop.addEventListener("click", closeLoginModal);

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();
      if (response.ok) {
        closeLoginModal();
        showMessage(messageDiv, result.message, "success");
        await refreshApp();
      } else {
        showMessage(loginMessage, result.detail || "Sign in failed", "error");
      }
    } catch (error) {
      showMessage(loginMessage, "Sign in failed. Please try again.", "error");
      console.error("Login failed:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });
      const result = await response.json();
      showMessage(messageDiv, result.message, "success");
      await refreshApp();
    } catch (error) {
      showMessage(messageDiv, "Sign out failed. Please try again.", "error");
      console.error("Logout failed:", error);
    }
  });

  refreshApp();
});
