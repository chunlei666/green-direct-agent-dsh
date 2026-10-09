/**
 * 绿电直连智能体 · 项目工作台 — 宿主半。
 *
 * 两个角色：
 * 1. `gdWizardState` 服务（普通 Service）：会话级向导状态存储。
 *    green-direct-workbench-tools（预设行）通过 inject 写入，
 *    Remote 方法读出给浏览器轮询。
 * 2. `gdWorkbench` Remote 服务（SRC 直连模式）：磁盘产物读取
 *    （listProjects / getProject）+ 向导状态查询（wizardState）。
 *
 * 方法标记通过伪造装饰器上下文手动施加（本包为手写 plain JS，
 * 不经过 typert 编译器，网关会按 SRC 标记动态发现端点）。
 */
import { Service } from "@deepseek-ai/cordis";
import { Remote, TypertRemoteService } from "@deepseek-ai/dsh-typert-protocol";

// 引擎根目录：优先 GD_HOME 环境变量；默认按 README 推荐安装位置解析。
import os from "node:os";
import path from "node:path";
const GD_HOME = process.env.GD_HOME || path.join(os.homedir(), "green-direct-agent", "green-direct");

/** 深度净化：负零归一、非有限值置 null、跳过 undefined（保证无损 JSON）。 */
function sanitize(value) {
	if (value === null) return null;
	const t = typeof value;
	if (t === "string") return value;
	if (t === "boolean") return value;
	if (t === "number") {
		if (!isFinite(value)) return null;
		return value === 0 ? 0 : value;
	}
	if (Array.isArray(value)) {
		const out = [];
		for (let i = 0; i < value.length; i++) out.push(sanitize(value[i]));
		return out;
	}
	if (t === "object") {
		const out = {};
		for (const k in value) {
			if (!Object.prototype.hasOwnProperty.call(value, k)) continue;
			const v = value[k];
			if (v === undefined) continue;
			out[k] = sanitize(v);
		}
		return out;
	}
	return null;
}

/** 带引号感知的极简 CSV 解析。 */
function parseCsv(text) {
	if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
	const rows = [];
	let row = [];
	let field = "";
	let inQ = false;
	for (let i = 0; i < text.length; i++) {
		const c = text.charAt(i);
		if (inQ) {
			if (c === '"') {
				if (text.charAt(i + 1) === '"') { field += '"'; i++; } else { inQ = false; }
			} else { field += c; }
		} else if (c === '"') { inQ = true; }
		else if (c === ",") { row.push(field); field = ""; }
		else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
		else if (c !== "\r") { field += c; }
	}
	if (field !== "" || row.length > 0) { row.push(field); rows.push(row); }
	return rows;
}

function parseJson(text) {
	try { return JSON.parse(text); } catch (e) { return undefined; }
}

/** 汇总 CSV 的最后一行数据 → 对象。 */
function csvRowObject(text) {
	const rows = parseCsv(text);
	if (rows.length < 2) return undefined;
	const header = rows[0];
	const data = rows[rows.length - 1];
	const obj = {};
	for (let i = 0; i < header.length && i < data.length; i++) obj[header[i]] = data[i];
	return obj;
}

/** 8760 小时表 → 24 小时典型日（按 hour_index % 24 分桶平均）。 */
function computeTypicalDay(text) {
	const rows = parseCsv(text);
	if (rows.length < 2) return null;
	const header = rows[0];
	const idx = {};
	for (let i = 0; i < header.length; i++) idx[header[i]] = i;
	const names = ["load", "wind_generation", "pv_generation", "biomass_generation", "diesel_to_load", "grid_to_load", "storage_to_load"];
	const sums = {};
	for (let n = 0; n < names.length; n++) {
		const z = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
		sums[names[n]] = z;
	}
	const counts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
	for (let r = 1; r < rows.length; r++) {
		const row = rows[r];
		const h0 = parseFloat(row[idx["hour_index"]]);
		if (!isFinite(h0)) continue;
		const h = Math.floor(h0) % 24;
		counts[h]++;
		for (let n = 0; n < names.length; n++) {
			const v = parseFloat(row[idx[names[n]]]);
			if (isFinite(v)) sums[names[n]][h] += v;
		}
	}
	const series = {};
	for (let n = 0; n < names.length; n++) {
		const arr = [];
		for (let h = 0; h < 24; h++) arr.push(counts[h] > 0 ? sums[names[n]][h] / counts[h] : 0);
		series[names[n]] = arr;
	}
	return series;
}

function entryName(e) {
	if (typeof e === "string") return e;
	if (e && typeof e === "object") {
		if (typeof e.name === "string") return e.name;
		if (typeof e.path === "string") return e.path.split("/").pop();
	}
	return "";
}

/** 绑定 fs 服务的读取器（闭包持有 fs，避免每层传递）。 */
function createReader(fs) {
	async function tryReadText(rel) {
		try {
			const target = await fs.resolve(GD_HOME + "/" + rel);
			const text = await fs.readText(target);
			return typeof text === "string" ? text : undefined;
		} catch (e) { return undefined; }
	}

	async function listDirNames(rel) {
		try {
			const target = await fs.resolve(rel === "" ? GD_HOME : GD_HOME + "/" + rel);
			const entries = await fs.listDir(target);
			if (!Array.isArray(entries)) return [];
			const names = [];
			for (let i = 0; i < entries.length; i++) {
				const n = entryName(entries[i]);
				if (n && n.charAt(0) !== ".") names.push(n);
			}
			return names;
		} catch (e) { return []; }
	}

	/** 目录本体 → 目录/outputs 双尝试读取三类产物。 */
	async function readArtifacts(dirRel) {
		let resultText = await tryReadText(dirRel + "/agent_result.json");
		let summaryText = await tryReadText(dirRel + "/green_direct_summary_results.csv");
		let validationText = await tryReadText(dirRel + "/validation_report.json");
		if (resultText === undefined && summaryText === undefined && validationText === undefined) {
			const sub = dirRel + "/outputs";
			resultText = await tryReadText(sub + "/agent_result.json");
			summaryText = await tryReadText(sub + "/green_direct_summary_results.csv");
			validationText = await tryReadText(sub + "/validation_report.json");
		}
		return { resultText: resultText, summaryText: summaryText, validationText: validationText };
	}

	async function collectProjects() {
		const top = await listDirNames("");
		const candidates = [];
		for (let i = 0; i < top.length; i++) {
			if (top[i] === "projects") continue;
			candidates.push({ rel: top[i], label: top[i] });
		}
		if (top.indexOf("projects") >= 0) {
			const subs = await listDirNames("projects");
			for (let i = 0; i < subs.length; i++) candidates.push({ rel: "projects/" + subs[i], label: subs[i] });
		}
		const projects = [];
		const seen = {};
		for (let i = 0; i < candidates.length; i++) {
			const cand = candidates[i];
			const a = await readArtifacts(cand.rel);
			if (a.resultText === undefined && a.summaryText === undefined && a.validationText === undefined) continue;
			const result = a.resultText !== undefined ? parseJson(a.resultText) : undefined;
			const summary = a.summaryText !== undefined ? csvRowObject(a.summaryText) : undefined;
			const validation = a.validationText !== undefined ? parseJson(a.validationText) : undefined;
			const configSource = (result && typeof result.config_source === "string")
				? result.config_source
				: (cand.rel.indexOf("projects/") === 0 ? cand.rel + "/config.json" : null);
			let hasConfig = false;
			if (configSource !== null) {
				const cfgText = await tryReadText(configSource);
				hasConfig = cfgText !== undefined && parseJson(cfgText) !== undefined;
			}
			let objective = null;
			if (result && typeof result.objective_value === "number") objective = result.objective_value;
			else if (summary) { const v = parseFloat(summary["objective_value"]); if (isFinite(v)) objective = v; }
			if (seen[cand.label]) continue;
			seen[cand.label] = true;
			projects.push({
				name: cand.label,
				dir: cand.rel,
				hasSolve: !!(result || summary),
				hasValidation: !!validation,
				validationPassed: !!(validation && validation.passed === true),
				projectType: (result && result.project_type) || (summary && summary["project_type"]) || "",
				solveStatus: (result && result.status) || "",
				objectiveValue: objective,
				configSource: configSource,
				hasConfig: hasConfig,
			});
		}
		return projects;
	}

	async function buildDetail(name) {
		const projects = await collectProjects();
		let found = null;
		for (let i = 0; i < projects.length; i++) { if (projects[i].name === name) { found = projects[i]; break } }
		if (found === null) return { error: "未找到项目：" + name };
		const a = await readArtifacts(found.dir);
		const result = a.resultText !== undefined ? parseJson(a.resultText) : null;
		const summary = a.summaryText !== undefined ? csvRowObject(a.summaryText) : null;
		const validation = a.validationText !== undefined ? parseJson(a.validationText) : null;
		let config = null;
		if (found.configSource !== null) {
			const cfgText = await tryReadText(found.configSource);
			const parsed = cfgText !== undefined ? parseJson(cfgText) : undefined;
			config = parsed || null;
		}
		let typicalDay = null;
		let hourlyRel = (result && result.outputs && typeof result.outputs.hourly_csv === "string") ? result.outputs.hourly_csv : null;
		if (hourlyRel === null) hourlyRel = found.dir + "/green_direct_hourly_results.csv";
		let hourlyText = await tryReadText(hourlyRel);
		if (hourlyText === undefined) hourlyText = await tryReadText(found.dir + "/outputs/green_direct_hourly_results.csv");
		if (typeof hourlyText === "string") typicalDay = computeTypicalDay(hourlyText);
		return {
			project: found,
			result: result,
			summary: summary,
			validation: validation,
			config: config,
			typicalDay: typicalDay,
		};
	}

	return { collectProjects: collectProjects, buildDetail: buildDetail };
}

//#region 向导状态服务

/** 一个会话的向导状态初始结构。 */
function freshWizardState() {
	return {
		open: false,
		stage: 1,
		project: "",
		note: "",
		stages: {},
		updatedAt: 0,
	};
}

/**
 * 会话级向导状态存储：workbench 工具（预设行）写入，浏览器经
 * gdWorkbench.wizardState 轮询读出。状态本身是纯展示数据，
 * 不承载任何业务事实——数值事实永远来自磁盘产物与引擎输出。
 */
class GdWizardStateService extends Service {
	constructor(ctx) {
		super(ctx, "gdWizardState");
		this.states = new Map();
	}

	/** 打开工作台（阶段①）。meta: {projectName, note} */
	open(sessionId, meta) {
		const st = this.ensure(sessionId);
		st.open = true;
		if (meta && typeof meta.projectName === "string" && meta.projectName !== "") st.project = meta.projectName;
		if (meta && typeof meta.note === "string" && meta.note !== "") st.note = meta.note;
		st.updatedAt = Date.now();
		return true;
	}

	/** 更新某阶段的结构化载荷并推进当前阶段。 */
	update(sessionId, stage, payload) {
		const st = this.ensure(sessionId);
		st.open = true;
		if (typeof payload.project === "string" && payload.project !== "") st.project = payload.project;
		st.stages[String(stage)] = payload;
		// 阶段跟随推送：正向推进取已推送阶段的最大值；智能体重推旧阶段
		// 即为明确的「恢复到该阶段」，工作台一并跳回（v7）。
		let max = 0;
		for (const k in st.stages) {
			const n = parseInt(k, 10);
			if (n > max) max = n;
		}
		const cur = parseInt(stage, 10);
		st.stage = cur >= 1 && cur <= max ? cur : max;
		st.updatedAt = Date.now();
		return true;
	}

	/** 读取（不存在返回 null，客户端据此不显示标签页）。 */
	read(sessionId) {
		return this.states.get(sessionId) || null;
	}

	/**
	 * 重置：清空该会话的全部向导状态（阶段、项目名、阶段载荷）。
	 * 两条入口共用：工作台「重置流程」按钮（gdWorkbench.resetWizard
	 * RPC）与智能体工具 workbench_reset。旧项目的磁盘产物不受影响，
	 * 档案库仍保留全部历史。
	 */
	reset(sessionId) {
		this.states.delete(sessionId);
		return true;
	}

	/** 恢复到某阶段（工作台「调整参数重算」即时回退用）：只拨阶段指针，不清空载荷。 */
	restore(sessionId, stage) {
		const st = this.states.get(sessionId);
		if (st === undefined || !st.open) return false;
		let max = 0;
		for (const k in st.stages) {
			const n = parseInt(k, 10);
			if (n > max) max = n;
		}
		const n = parseInt(stage, 10);
		if (!(n >= 1 && n <= max)) return false;
		st.stage = n;
		st.updatedAt = Date.now();
		return true;
	}

	ensure(sessionId) {
		let st = this.states.get(sessionId);
		if (st === undefined) {
			st = freshWizardState();
			this.states.set(sessionId, st);
		}
		return st;
	}
}

//#endregion

/**
 * 工作台数据服务：浏览器经 connection.rpc.call("/api", "gdWorkbench/<method>")
 * 直接调用。注意：方法参数必须是简单标识符（网关解析 Function.prototype.toString），
 * 返回值统一过 sanitize 保证无损 JSON。
 */
class GdWorkbenchService extends TypertRemoteService {
	constructor(ctx, wizard) {
		super(ctx, "gdWorkbench");
		this.wizard = wizard;
	}

	async listProjects() {
		const fs = this.ctx.get("fs");
		if (fs === undefined) return [];
		const reader = createReader(fs);
		return sanitize(await reader.collectProjects());
	}

	async getProject(name) {
		const fs = this.ctx.get("fs");
		if (fs === undefined) return { error: "fs 服务不可用" };
		const reader = createReader(fs);
		return sanitize(await reader.buildDetail(typeof name === "string" ? name : ""));
	}

	async wizardState(sessionId) {
		if (this.wizard === undefined || this.wizard === null) return null;
		const key = typeof sessionId === "string" ? sessionId : "";
		return sanitize(this.wizard.read(key));
	}

	/** 重置当前会话的工作台流程（清空向导状态，回到阶段①待命）。 */
	async resetWizard(sessionId) {
		if (this.wizard === undefined || this.wizard === null) return { ok: false };
		const key = typeof sessionId === "string" ? sessionId : "";
		this.wizard.reset(key);
		return { ok: true };
	}

	/** 「调整参数重算」等按钮的即时回退：把向导拨回 stage（不清空载荷）。 */
	async restoreStage(sessionId, stage) {
		if (this.wizard === undefined || this.wizard === null) return { ok: false, stage: null };
		const key = typeof sessionId === "string" ? sessionId : "";
		const done = this.wizard.restore(key, typeof stage === "number" ? stage : parseInt(stage, 10));
		return sanitize({ ok: done === true, stage: done === true ? parseInt(stage, 10) : null });
	}
}

/** 在无装饰器环境手动施加 Remote 标记（网关按 SRC 模式动态发现端点）。 */
function markRemoteMethod(prototype, methodName) {
	const stub = Object.create(prototype);
	Remote(methodName)(prototype[methodName], {
		private: false,
		static: false,
		name: methodName,
		addInitializer: (fn) => fn.call(stub),
	});
}
markRemoteMethod(GdWorkbenchService.prototype, "listProjects");
markRemoteMethod(GdWorkbenchService.prototype, "getProject");
markRemoteMethod(GdWorkbenchService.prototype, "wizardState");
markRemoteMethod(GdWorkbenchService.prototype, "resetWizard");
markRemoteMethod(GdWorkbenchService.prototype, "restoreStage");

function apply(ctx) {
	ctx.inject(["fs"], (fsCtx) => {
		const wizard = new GdWizardStateService(fsCtx);
		new GdWorkbenchService(fsCtx, wizard);
	});
}

export { apply };
