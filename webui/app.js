const state = {
  semester: {
    semester_name: "",
    start_date: "",
    total_weeks: 16,
    periods_per_day: 10,
    working_days: [1, 2, 3, 4, 5],
    holidays: [],
  },
  theory_slots: [],
  labs: [],
};

function parseWeeks(text) {
  if (!text) return [];
  const normalized = text.replaceAll("，", ",").replaceAll("；", ",");
  const output = [];
  normalized.split(",").forEach((part) => {
    const value = part.trim();
    if (!value) return;
    if (value.includes("-")) {
      const [s, e] = value.split("-").map((x) => Number(x.trim()));
      const start = Math.min(s, e);
      const end = Math.max(s, e);
      for (let i = start; i <= end; i += 1) output.push(i);
    } else {
      output.push(Number(value));
    }
  });
  return [...new Set(output)].filter((x) => !Number.isNaN(x)).sort((a, b) => a - b);
}

function getById(id) { return document.getElementById(id); }

function renderHolidays() {
  const tbody = getById("holiday_table");
  tbody.innerHTML = "";
  state.semester.holidays.forEach((item, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${item.date}</td><td>${item.name}</td><td><button data-type="holiday" data-idx="${idx}">删除</button></td>`;
    tbody.appendChild(tr);
  });
}

function renderTheory() {
  const tbody = getById("theory_table");
  tbody.innerHTML = "";
  state.theory_slots.forEach((item, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.class_name}</td>
      <td>${item.course_name}</td>
      <td>${item.teacher}</td>
      <td>${item.weekday}</td>
      <td>${item.start_period}-${item.end_period}</td>
      <td>${(item.weeks || []).join(",")}</td>
      <td><button data-type="theory" data-idx="${idx}">删除</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderLabs() {
  const tbody = getById("lab_table");
  tbody.innerHTML = "";
  state.labs.forEach((item, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.lab_id}</td>
      <td>${item.lab_name}</td>
      <td>${item.capacity}</td>
      <td>${item.campus || ""}</td>
      <td>${(item.supported_courses || []).join(",")}</td>
      <td><button data-type="lab" data-idx="${idx}">删除</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderAll() {
  getById("semester_name").value = state.semester.semester_name || "";
  getById("start_date").value = state.semester.start_date || "";
  getById("total_weeks").value = state.semester.total_weeks || 16;
  getById("periods_per_day").value = state.semester.periods_per_day || 10;
  getById("working_days").value = (state.semester.working_days || []).join(",");
  renderHolidays();
  renderTheory();
  renderLabs();
}

function collectSemester() {
  state.semester.semester_name = getById("semester_name").value.trim();
  state.semester.start_date = getById("start_date").value;
  state.semester.total_weeks = Number(getById("total_weeks").value || 0);
  state.semester.periods_per_day = Number(getById("periods_per_day").value || 0);
  state.semester.working_days = getById("working_days").value
    .split(",")
    .map((x) => Number(x.trim()))
    .filter((x) => !Number.isNaN(x));
}

function setStatus(text, isError = false) {
  const el = getById("status_text");
  el.style.color = isError ? "#b91c1c" : "#0f766e";
  el.textContent = text;
}

async function loadConfig() {
  const resp = await fetch("/api/config");
  if (!resp.ok) throw new Error(`加载失败: ${resp.status}`);
  const data = await resp.json();
  state.semester = data.semester || state.semester;
  state.theory_slots = data.theory_slots || [];
  state.labs = data.labs || [];
  renderAll();
  setStatus("配置已加载");
}

async function saveConfig() {
  collectSemester();
  const resp = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  if (!resp.ok) throw new Error(`保存失败: ${resp.status}`);
  setStatus("配置已保存");
}

function bindEvents() {
  getById("add_holiday").addEventListener("click", () => {
    const date = getById("holiday_date").value;
    const name = getById("holiday_name").value.trim();
    if (!date || !name) return;
    state.semester.holidays.push({ date, name });
    renderHolidays();
    getById("holiday_name").value = "";
  });

  getById("add_theory").addEventListener("click", () => {
    const class_name = getById("th_class_name").value.trim();
    const course_name = getById("th_course_name").value.trim();
    const teacher = getById("th_teacher").value.trim();
    if (!class_name || !course_name || !teacher) return;

    state.theory_slots.push({
      class_name,
      course_name,
      teacher,
      weekday: Number(getById("th_weekday").value || 0),
      start_period: Number(getById("th_start_period").value || 0),
      end_period: Number(getById("th_end_period").value || 0),
      weeks: parseWeeks(getById("th_weeks").value),
      semester: getById("th_semester").value.trim() || null,
    });
    renderTheory();
  });

  getById("add_lab").addEventListener("click", () => {
    const lab_id = getById("lab_id").value.trim();
    const lab_name = getById("lab_name").value.trim();
    if (!lab_id || !lab_name) return;

    state.labs.push({
      lab_id,
      lab_name,
      capacity: Number(getById("lab_capacity").value || 0),
      campus: getById("lab_campus").value.trim() || null,
      supported_courses: getById("lab_courses").value
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean),
    });
    renderLabs();
  });

  document.body.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const type = target.getAttribute("data-type");
    const idx = Number(target.getAttribute("data-idx"));
    if (Number.isNaN(idx)) return;

    if (type === "holiday") state.semester.holidays.splice(idx, 1);
    if (type === "theory") state.theory_slots.splice(idx, 1);
    if (type === "lab") state.labs.splice(idx, 1);
    renderAll();
  });

  getById("load_btn").addEventListener("click", async () => {
    try { await loadConfig(); } catch (e) { setStatus(String(e), true); }
  });
  getById("save_btn").addEventListener("click", async () => {
    try { await saveConfig(); } catch (e) { setStatus(String(e), true); }
  });
}

bindEvents();
loadConfig().catch((e) => setStatus(String(e), true));
