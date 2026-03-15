const state = {
  semester: { semester_name: "", start_date: "", total_weeks: 16, periods_per_day: 10, working_days: [1, 2, 3, 4, 5], holidays: [] },
  theory_slots: [],
  labs: [],
  lab_tasks: [],
  schedule_result: { scheduled_items: [], unscheduled_items: [] },
};

function getById(id) { return document.getElementById(id); }

function setStatus(text, isError = false) {
  const el = getById("status_text");
  el.style.color = isError ? "#b91c1c" : "#0f766e";
  el.textContent = text;
}

function renderRows(tableId, htmlRows) {
  getById(tableId).innerHTML = htmlRows.join("");
}

function renderAll() {
  getById("semester_name").value = state.semester.semester_name || "";
  getById("start_date").value = state.semester.start_date || "";
  getById("total_weeks").value = state.semester.total_weeks || 16;
  getById("periods_per_day").value = state.semester.periods_per_day || 10;
  getById("working_days").value = (state.semester.working_days || []).join(",");

  renderRows("holiday_table", (state.semester.holidays || []).map((x, i) => `<tr><td>${x.date}</td><td>${x.name}</td><td><button data-type="holiday" data-idx="${i}">删除</button></td></tr>`));
  renderRows("theory_table", (state.theory_slots || []).map((x, i) => `<tr><td>${x.class_name}</td><td>${x.course_name}</td><td>${x.teacher}</td><td>${x.weekday}</td><td>${x.start_period}-${x.end_period}</td><td>${(x.weeks || []).join(",")}</td><td><button data-type="theory" data-idx="${i}">删除</button></td></tr>`));
  renderRows("lab_table", (state.labs || []).map((x, i) => `<tr><td>${x.lab_id}</td><td>${x.lab_name}</td><td>${x.capacity}</td><td>${x.campus || ""}</td><td>${(x.supported_courses || []).join(",")}</td><td><button data-type="lab" data-idx="${i}">删除</button></td></tr>`));
  renderRows("task_table", (state.lab_tasks || []).map((x, i) => `<tr><td>${x.task_id}</td><td>${x.class_name}</td><td>${x.course_name}</td><td>${x.project_name}</td><td>${x.student_count}</td><td>${x.expected_week || ""}/${x.expected_weekday || ""}</td><td><button data-type="task" data-idx="${i}">删除</button></td></tr>`));

  const scheduled = state.schedule_result?.scheduled_items || [];
  const unscheduled = state.schedule_result?.unscheduled_items || [];
  renderRows("scheduled_table", scheduled.map((x) => `<tr><td>${x.task_id}</td><td>${x.class_name}</td><td>${x.course_name}</td><td>${x.project_name}</td><td>${x.lab_name}</td><td>${x.week}</td><td>${x.weekday}</td><td>${x.start_period}-${x.end_period}</td><td>${x.teacher || ""}</td></tr>`));
  renderRows("unscheduled_table", unscheduled.map((x) => `<tr><td>${x.task_id}</td><td>${x.class_name}</td><td>${x.course_name}</td><td>${x.project_name}</td><td>${x.reason}</td></tr>`));
}

function collectSemester() {
  state.semester.semester_name = getById("semester_name").value.trim();
  state.semester.start_date = getById("start_date").value;
  state.semester.total_weeks = Number(getById("total_weeks").value || 0);
  state.semester.periods_per_day = Number(getById("periods_per_day").value || 0);
  state.semester.working_days = getById("working_days").value.split(",").map((x) => Number(x.trim())).filter((x) => !Number.isNaN(x));
}

async function loadConfig() {
  const resp = await fetch("/api/config");
  if (!resp.ok) throw new Error(`加载失败: ${resp.status}`);
  Object.assign(state, await resp.json());
  renderAll();
  setStatus("配置已加载");
}

async function saveConfig() {
  collectSemester();
  const resp = await fetch("/api/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(state) });
  if (!resp.ok) throw new Error(`保存失败: ${resp.status}`);
  setStatus("配置已保存");
}

async function importExcel(kind) {
  const input = getById(`import_${kind}`);
  if (!input.files?.length) throw new Error("请先选择 Excel 文件");
  const formData = new FormData();
  formData.append("file", input.files[0]);
  const resp = await fetch(`/api/import/${kind}`, { method: "POST", body: formData });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || `导入失败: ${resp.status}`);

  const lines = [
    `目标数据区: ${data.target}`,
    `读取条数: ${data.read_count}`,
    `缺失字段: ${(data.missing_fields || []).join(",") || "无"}`,
    `格式错误: ${(data.invalid_values || []).join(" | ") || "无"}`,
  ];
  getById("import_preview").textContent = lines.join("\n");

  await loadConfig();
}

async function runSchedule() {
  const resp = await fetch("/api/schedule/run", { method: "POST" });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || `排课失败: ${resp.status}`);

  state.schedule_result = {
    scheduled_items: data.scheduled_items || [],
    unscheduled_items: data.unscheduled_items || [],
  };
  renderAll();
  getById("schedule_summary").textContent = `已排课 ${data.scheduled_count} 条，未排课 ${data.unscheduled_count} 条`;
}

function bindEvents() {
  getById("add_holiday").addEventListener("click", () => {
    const date = getById("holiday_date").value;
    const name = getById("holiday_name").value.trim();
    if (!date || !name) return;
    state.semester.holidays.push({ date, name });
    renderAll();
  });

  document.body.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;

    if (target.dataset.import) {
      try { await importExcel(target.dataset.import); } catch (e) { setStatus(String(e), true); }
      return;
    }

    const type = target.getAttribute("data-type");
    const idx = Number(target.getAttribute("data-idx"));
    if (!Number.isNaN(idx)) {
      if (type === "holiday") state.semester.holidays.splice(idx, 1);
      if (type === "theory") state.theory_slots.splice(idx, 1);
      if (type === "lab") state.labs.splice(idx, 1);
      if (type === "task") state.lab_tasks.splice(idx, 1);
      renderAll();
    }
  });

  getById("load_btn").addEventListener("click", async () => { try { await loadConfig(); } catch (e) { setStatus(String(e), true); } });
  getById("save_btn").addEventListener("click", async () => { try { await saveConfig(); } catch (e) { setStatus(String(e), true); } });
  getById("run_schedule").addEventListener("click", async () => { try { await runSchedule(); } catch (e) { setStatus(String(e), true); } });
}

bindEvents();
loadConfig().catch((e) => setStatus(String(e), true));
