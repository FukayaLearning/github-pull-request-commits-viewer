const state = {
  repoInfo: null,
  prs: [],
  base: "",
  head: "HEAD",
  commits: [],
  selectedSha: null,
  diffMode: "side-by-side",
  ignoreWhitespace: false,
};

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

function renderCommitListBasic() {
  els.commitList.innerHTML = "";
  els.reviewProgress.textContent = `0 / ${state.commits.length} Reviewed`;

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
    const li = document.createElement("li");
    li.dataset.sha = commit.sha;
    li.style.padding = "10px 14px";
    li.style.borderBottom = "1px solid var(--border-default)";
    li.style.cursor = "pointer";
    if (commit.sha === state.selectedSha) {
      li.style.background = "var(--bg-elevated)";
    }
    li.textContent = `${commit.short_sha} ${commit.subject}`;
    li.addEventListener("click", () => {
      state.selectedSha = commit.sha;
      renderCommitListBasic();
      els.commitSummary.textContent = `${commit.short_sha}: ${commit.subject}`;
    });
    els.commitList.appendChild(li);
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
    renderCommitListBasic();
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

init();
