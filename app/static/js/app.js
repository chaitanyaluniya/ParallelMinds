const form = document.getElementById("chat-form");
const queryInput = document.getElementById("query");
const filesInput = document.getElementById("files");
const fileNames = document.getElementById("file-names");
const messagesEl = document.getElementById("messages");
const extractedPanel = document.getElementById("extracted-panel");
const extractedText = document.getElementById("extracted-text");
const planPanel = document.getElementById("plan-panel");
const planTrace = document.getElementById("plan-trace");
const submitBtn = document.getElementById("submit-btn");

filesInput.addEventListener("change", () => {
  const names = Array.from(filesInput.files).map((f) => f.name);
  fileNames.textContent = names.length ? names.join(", ") : "";
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  const files = filesInput.files;

  if (!query && files.length === 0) return;

  appendMessage("user", query || `(uploaded ${files.length} file(s))`);
  submitBtn.disabled = true;

  const formData = new FormData();
  formData.append("query", query);
  for (const file of files) {
    formData.append("files", file);
  }

  try {
    const res = await fetch("/api/chat", { method: "POST", body: formData });
    const data = await res.json();

    if (data.needs_clarification) {
      appendMessage("agent clarification", data.clarification_question);
    } else {
      appendMessage("agent", data.final_answer);
    }

    renderExtracted(data.extracted_contents);
    renderPlanTrace(data.plan_trace);
  } catch (err) {
    appendMessage("agent", `Error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    queryInput.value = "";
    filesInput.value = "";
    fileNames.textContent = "";
  }
});

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function renderExtracted(contents) {
  if (!contents?.length) {
    extractedPanel.classList.add("hidden");
    return;
  }
  extractedPanel.classList.remove("hidden");
  extractedText.textContent = contents
    .map((c) => `[${c.input_type}] ${c.filename || "query"}\n${c.text}`)
    .join("\n\n---\n\n");
}

function renderPlanTrace(steps) {
  if (!steps?.length) {
    planPanel.classList.add("hidden");
    return;
  }
  planPanel.classList.remove("hidden");
  planTrace.innerHTML = steps
    .map(
      (s) =>
        `<li><strong>${s.tool_name}</strong>: ${s.description}
         <span class="status">[${s.status}]</span></li>`
    )
    .join("");
}
