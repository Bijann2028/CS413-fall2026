/* View only: forward interactions and display controller state literally. */
"use strict";
const el = id => document.getElementById(id);
const editor = el("editor");
const labels = {lint: "Lint", interpret: "Interpret", typecheck: "Type-check", compile: "Compile", execute: "Execute"};
let state = null;
let sending = false;
let draftQueue = Promise.resolve();
let draftRequests = 0;
let polling = false;

function showError(message) {
  el("error").textContent = message || "";
  el("error").hidden = !message;
}

function render(next, updateEditor = false) {
  state = next;
  if (updateEditor) editor.value = state.draft;
  const dirty = state.manual_pending || editor.value !== (state.source || "");
  const waiting = sending || draftRequests > 0;
  const busy = Boolean(state.busy);
  editor.readOnly = busy || sending;
  el("source-menu").disabled = busy || waiting || dirty;
  el("source-file").disabled = busy || waiting || dirty;
  el("upload").disabled = busy || waiting || dirty;
  el("apply").disabled = busy || waiting || (!dirty && state.source !== null);
  el("discard").disabled = busy || waiting || !dirty;
  el("source-info").textContent = `${state.name} · revision ${state.revision}${state.source === null ? " · no applied source" : ""}`;
  el("edit-status").textContent = dirty ? "Unapplied changes: apply or discard to continue." : "No unapplied changes.";
  el("status").textContent = busy ? `Busy: ${labels[state.busy]}. Please wait.` : state.message;
  for (const button of document.querySelectorAll("[data-operation]")) {
    button.disabled = busy || waiting || dirty || state.source === null ||
      (button.dataset.operation === "execute" && !state.has_artifact);
  }
  const results = el("results");
  results.replaceChildren();
  if (!state.results.length) {
    const empty = document.createElement("p");
    empty.textContent = "No results for this revision.";
    results.append(empty);
  }
  for (const result of state.results) {
    const article = document.createElement("article");
    article.className = "result";
    const title = document.createElement("h3");
    title.textContent = `${labels[result.operation]} · revision ${result.revision} · ${result.outcome}`;
    const output = document.createElement("pre");
    output.textContent = result.text;
    article.append(title, output);
    results.append(article);
  }
  if (busy) poll();
}

async function send(url, payload, updateEditor = false) {
  try {
    const form = payload instanceof FormData;
    const response = await fetch(url, {
      method: "POST",
      headers: form ? {} : {"Content-Type": "application/json"},
      body: form ? payload : JSON.stringify(payload)
    });
    const body = await response.json();
    if (!response.ok) {
      showError(body.error || "Request failed. Your editor text is preserved.");
      if (body.state) render(body.state);
      return;
    }
    showError("");
    render(body, updateEditor);
  } catch (error) {
    showError("Connection failed. Your editor text is preserved. Check the server and retry.");
  }
}

async function action(url, payload, updateEditor = false) {
  sending = true;
  if (state) render(state);
  try {
    await draftQueue;
    await send(url, payload, updateEditor);
  } finally {
    sending = false;
    if (state) render(state);
  }
}

async function poll() {
  if (polling) return;
  polling = true;
  try {
    while (state && state.busy) {
      await new Promise(resolve => setTimeout(resolve, 100));
      try {
        const response = await fetch("/api/state");
        if (!response.ok) throw new Error("State unavailable");
        render(await response.json());
      } catch (error) {
        showError("Cannot fetch operation status. Reconnecting; source is preserved.");
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  } finally {
    polling = false;
  }
}

editor.addEventListener("input", () => {
  const draft = editor.value;
  draftRequests++;
  if (state) render(state);
  draftQueue = draftQueue.then(() => send("/api/source/draft", {draft})).finally(() => {
    draftRequests--;
    if (state) render(state);
  });
});

el("apply").addEventListener("click", () => action("/api/source/apply", {draft: editor.value}, true));
el("discard").addEventListener("click", () => action("/api/source/discard", {}, true));
el("source-menu").addEventListener("change", async event => {
  const choice = event.target.value;
  event.target.value = "";
  el("upload-panel").hidden = choice !== "file";
  if (choice && choice !== "file") {
    await action(`/api/source/${choice}`, {draft: editor.value}, true);
    if (choice === "manual") editor.focus();
  }
});
el("upload").addEventListener("click", async () => {
  const file = el("source-file").files[0];
  if (!file) return showError("Choose a UTF-8 text file.");
  const form = new FormData();
  form.append("file", file);
  form.append("draft", editor.value);
  await action("/api/source/upload", form, true);
});
for (const button of document.querySelectorAll("[data-operation]")) {
  button.addEventListener("click", () => action(`/api/action/${button.dataset.operation}`, {draft: editor.value}));
}
fetch("/api/state").then(response => response.json()).then(next => render(next, true))
  .catch(() => showError("Cannot load the application. Start the server and reload this page."));
