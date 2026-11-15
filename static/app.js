const REVIEWED_STORAGE_KEY = "local-pr-viewer:reviewed-commits";

const state = {
  repoInfo: null,
  prs: [],
  base: "",
  head: "HEAD",
  commits: [],
  selectedSha: null,
  diffMode: "side-by-side",
  ignoreWhitespace: false,
  reviewedMap: loadReviewedMap(),
};

function loadReviewedMap() {
  try {
    const raw = window.localStorage.getItem(REVIEWED_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveReviewedMap() {
  try {
    window.localStorage.setItem(REVIEWED_STORAGE_KEY, JSON.stringify(state.reviewedMap));
  } catch {
    // Ignore storage quota or private mode errors
  }
}

function getBadgeMeta(changeType) {
  if (changeType === "command") {
    return { label: "🤖 Command", className: "badge-command" };
  }
  if (changeType === "test") {
    return { label: "✅ Test", className: "badge-test" };
  }
  return { label: "✍️ Manual", className: "badge-manual" };
}

const els = {
  repoName: document.getElementById("repo-name"),
  currentBranch: document.getElementById("current-branch"),
  prSelect: document.getElementById("pr-select"),
  prStatus: document.getElementById("pr-status"),
  baseSelect: document.getElementById("base-branch-select"),
  headSelect: document.getElementById("head-branch-select"),
  reloadBtn: document.getElementById("reload-btn"),
  globalError: document.getElementById("global-error"),
  commitList: document.getElementById("commit-list"),
  reviewProgress: document.getElementById("review-progress"),
  commitSummary: document.getElementById("commit-summary"),
};

function showError(message) {
  if (!message) {
    els.globalError.hidden = true;
    els.globalError.textContent = "";
    return;
  }
  els.globalError.textContent = message;
  els.globalError.hidden = false;
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

function populateBranchSelect(selectEl, branches, selectedValue) {
  selectEl.innerHTML = "";
  const options = [...branches];
  if (selectedValue && !options.includes(selectedValue)) {
    options.unshift(selectedValue);
  }
  for (const branch of options) {
    const opt = document.createElement("option");
    opt.value = branch;
    opt.textContent = branch;
    if (branch === selectedValue) {
      opt.selected = true;
    }
    selectEl.appendChild(opt);
  }
}

function populatePrSelect(prs, fallback, reason) {
  els.prSelect.innerHTML = "";
  const localOpt = document.createElement("option");
  localOpt.value = "";
  localOpt.textContent = "ローカルブランチ比較";
  els.prSelect.appendChild(localOpt);

  for (const pr of prs) {
    const opt = document.createElement("option");
    opt.value = String(pr.number);
    opt.textContent = `#${pr.number} ${pr.title} (${pr.baseRefName} ← ${pr.headRefName})`;
    opt.dataset.base = pr.baseRefName;
    opt.dataset.head = pr.headRefName;
    els.prSelect.appendChild(opt);
  }

  if (fallback) {
    els.prStatus.textContent = reason ? `Local mode (${reason})` : "Local mode";
    els.prStatus.hidden = false;
  } else {
    els.prStatus.hidden = true;
  }
}

function updateReviewProgress() {
  const total = state.commits.length;
  const reviewedCount = state.commits.filter((c) => Boolean(state.reviewedMap[c.sha])).length;
  els.reviewProgress.textContent = `${reviewedCount} / ${total} Reviewed`;
}

function toggleReviewed(sha) {
  if (!sha) {
    return;
  }
  if (state.reviewedMap[sha]) {
    delete state.reviewedMap[sha];
  } else {
    state.reviewedMap[sha] = true;
  }
  saveReviewedMap();
  renderCommitList();
}

function selectCommit(sha) {
  state.selectedSha = sha;
  renderCommitList();
  const commit = state.commits.find((c) => c.sha === sha);
  if (commit) {
    els.commitSummary.textContent = `${commit.short_sha}: ${commit.subject}`;
  }
}

function selectCommitByOffset(delta) {
  if (state.commits.length === 0) {
    return;
  }
  const currentIndex = state.commits.findIndex((c) => c.sha === state.selectedSha);
  const baseIndex = currentIndex === -1 ? 0 : currentIndex;
  const nextIndex = Math.max(0, Math.min(state.commits.length - 1, baseIndex + delta));
  if (nextIndex !== currentIndex || currentIndex === -1) {
    selectCommit(state.commits[nextIndex].sha);
  }
}

function renderCommitList() {
  els.commitList.innerHTML = "";
  updateReviewProgress();

  if (state.commits.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.style.padding = "14px";
    empty.textContent = `${state.base}..${state.head} にコミットはありません。`;
    els.commitList.appendChild(empty);
    els.commitSummary.innerHTML = '<p class="empty-state">表示するコミットがありません。</p>';
    return;
  }

  for (const commit of state.commits) {
    const isSelected = commit.sha === state.selectedSha;
    const isReviewed = Boolean(state.reviewedMap[commit.sha]);
    const badge = getBadgeMeta(commit.change_type);

    const li = document.createElement("li");
    li.className = `commit-item${isSelected ? " active" : ""}${isReviewed ? " reviewed" : ""}`;
    li.dataset.sha = commit.sha;
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", String(isSelected));

    const topRow = document.createElement("div");
    topRow.className = "commit-item-top";

    const badgesWrap = document.createElement("div");
    badgesWrap.className = "commit-badges";

    const badgeSpan = document.createElement("span");
    badgeSpan.className = `change-badge ${badge.className}`;
    badgeSpan.textContent = badge.label;
    badgesWrap.appendChild(badgeSpan);

    for (const taskId of commit.task_ids || []) {
      const taskSpan = document.createElement("span");
      taskSpan.className = "task-pill";
      taskSpan.textContent = taskId;
      badgesWrap.appendChild(taskSpan);
    }

    const reviewLabel = document.createElement("label");
    reviewLabel.className = "reviewed-toggle";
    reviewLabel.addEventListener("click", (e) => e.stopPropagation());

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = isReviewed;
    checkbox.setAttribute("aria-label", `Mark ${commit.short_sha} as reviewed`);
    checkbox.addEventListener("change", () => toggleReviewed(commit.sha));

    const reviewText = document.createElement("span");
    reviewText.textContent = "Reviewed";
    reviewLabel.append(checkbox, reviewText);

    topRow.append(badgesWrap, reviewLabel);

    const subjectEl = document.createElement("div");
    subjectEl.className = "commit-subject";
    subjectEl.textContent = commit.subject;

    const metaEl = document.createElement("div");
    metaEl.className = "commit-meta-line";
    const shaSpan = document.createElement("span");
    shaSpan.className = "commit-sha";
    shaSpan.textContent = commit.short_sha;
    const authorSpan = document.createElement("span");
    authorSpan.textContent = commit.author;
    metaEl.append(shaSpan, authorSpan);

    li.append(topRow, subjectEl, metaEl);
    li.addEventListener("click", () => selectCommit(commit.sha));
    els.commitList.appendChild(li);

    if (isSelected && typeof li.scrollIntoView === "function") {
      li.scrollIntoView({ block: "nearest" });
    }
  }
}

async function loadCommits() {
  if (!state.base || !state.head) {
    return;
  }
  showError("");
  try {
    const params = new URLSearchParams({ base: state.base, head: state.head });
    const data = await fetchJson(`/api/commits?${params.toString()}`);
    state.commits = data.commits || [];
    state.selectedSha = state.commits.length > 0 ? state.commits[0].sha : null;
    renderCommitList();
    if (state.selectedSha) {
      selectCommit(state.selectedSha);
    }
  } catch (err) {
    showError(err.message);
  }
}

async function init() {
  showError("");
  try {
    const [repoInfo, prData] = await Promise.all([
      fetchJson("/api/repo-info"),
      fetchJson("/api/prs"),
    ]);
    state.repoInfo = repoInfo;
    state.prs = prData.prs || [];
    state.base = prData.default_base || repoInfo.default_base || "main";
    state.head = prData.default_head || repoInfo.current_branch || "HEAD";

    els.repoName.textContent = repoInfo.repo_name;
    els.currentBranch.textContent = repoInfo.current_branch;

    const branches = repoInfo.branches || [];
    populateBranchSelect(els.baseSelect, branches, state.base);
    populateBranchSelect(els.headSelect, ["HEAD", ...branches], state.head);
    populatePrSelect(state.prs, prData.fallback, prData.reason);

    await loadCommits();
  } catch (err) {
    showError(err.message);
  }
}

els.prSelect.addEventListener("change", () => {
  const selected = els.prSelect.selectedOptions[0];
  if (selected && selected.value) {
    state.base = selected.dataset.base || state.base;
    state.head = selected.dataset.head || state.head;
    populateBranchSelect(els.baseSelect, state.repoInfo?.branches || [], state.base);
    populateBranchSelect(els.headSelect, ["HEAD", ...(state.repoInfo?.branches || [])], state.head);
  }
  loadCommits();
});

els.baseSelect.addEventListener("change", () => {
  els.prSelect.value = "";
  state.base = els.baseSelect.value;
  loadCommits();
});

els.headSelect.addEventListener("change", () => {
  els.prSelect.value = "";
  state.head = els.headSelect.value;
  loadCommits();
});

els.reloadBtn.addEventListener("click", () => {
  init();
});

document.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) {
    return;
  }
  const target = event.target;
  if (
    target &&
    (target.isContentEditable ||
      target.tagName === "SELECT" ||
      target.tagName === "TEXTAREA" ||
      (target.tagName === "INPUT" && target.type !== "checkbox"))
  ) {
    return;
  }

  if (event.key === "j" || event.key === "ArrowDown") {
    event.preventDefault();
    selectCommitByOffset(1);
  } else if (event.key === "k" || event.key === "ArrowUp") {
    event.preventDefault();
    selectCommitByOffset(-1);
  } else if (event.key === "r") {
    event.preventDefault();
    toggleReviewed(state.selectedSha);
  }
});

init();
