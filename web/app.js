const STORAGE_KEY = "maintenance_projects_v1";
const FLOW = ["审核中", "已派工", "执行中", "待验收", "待结算", "已归档"];

const form = document.getElementById("projectForm");
const rowsEl = document.getElementById("projectRows");
const metricsEl = document.getElementById("metrics");

const readProjects = () => JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
const saveProjects = (data) => localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

function genProjectNo(type) {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const code = ({ "故障维修": "REP", "定期维保": "MNT", "巡检改造": "INS", "应急抢修": "EMR", "寄修返厂": "RET" })[type] || "GEN";
  const seed = Math.floor(Math.random() * 9000 + 1000);
  return `${y}${m}${code}${seed}`;
}

function approvalNodeText(amount) {
  if (amount <= 10000) return "主管审核";
  if (amount <= 50000) return "主管+技术负责人审核";
  return "主管+技术+财务+总经理审核";
}

function renderMetrics(data) {
  const total = data.length;
  const active = data.filter(x => x.status !== "已归档").length;
  const done = data.filter(x => x.status === "已归档").length;
  const urgent = data.filter(x => x.priority === "紧急").length;
  metricsEl.innerHTML = `
    <div class="metric">项目总数：<b>${total}</b></div>
    <div class="metric">进行中：<b>${active}</b></div>
    <div class="metric">已归档：<b>${done}</b></div>
    <div class="metric">紧急项目：<b>${urgent}</b></div>
  `;
}

function render() {
  const data = readProjects();
  renderMetrics(data);
  rowsEl.innerHTML = "";
  data.forEach((p, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.projectNo}</td>
      <td>${p.name}<br><small style="color:#5f6b7a">${p.approvalHint}</small></td>
      <td>${p.type}</td>
      <td>${p.priority}</td>
      <td>¥${Number(p.amount).toFixed(2)}</td>
      <td><span class="badge status-${p.status}">${p.status}</span></td>
      <td>
        <div class="actions">
          <button data-action="next" data-idx="${idx}">推进流程</button>
          <button data-action="delete" class="danger" data-idx="${idx}">删除</button>
        </div>
      </td>
    `;
    rowsEl.appendChild(tr);
  });
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  const item = {
    id: crypto.randomUUID(),
    projectNo: genProjectNo(fd.get("type")),
    name: fd.get("name"),
    customerCode: fd.get("customerCode"),
    equipmentCode: fd.get("equipmentCode"),
    type: fd.get("type"),
    priority: fd.get("priority"),
    amount: Number(fd.get("amount")),
    issue: fd.get("issue"),
    status: FLOW[0],
    approvalHint: approvalNodeText(Number(fd.get("amount"))),
    createdAt: new Date().toISOString()
  };
  const data = readProjects();
  data.unshift(item);
  saveProjects(data);
  form.reset();
  render();
});

rowsEl.addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const idx = Number(btn.dataset.idx);
  const action = btn.dataset.action;
  const data = readProjects();

  if (action === "delete") {
    data.splice(idx, 1);
  }

  if (action === "next") {
    const now = data[idx].status;
    const i = FLOW.indexOf(now);
    data[idx].status = FLOW[Math.min(i + 1, FLOW.length - 1)];
  }

  saveProjects(data);
  render();
});

render();
