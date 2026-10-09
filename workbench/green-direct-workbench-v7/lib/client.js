window.__ModuleLoader__.load({
	id: "green-direct-workbench-v7",
	factory: (require) => {
		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
		let react = require("react");

		const React = react;
		const el = React.createElement;
		/** apply() 时填充：真实插件上下文（服务与 interval 都从这里取）。 */
		let appCtx = null;
		/** 请求代际令牌：旧请求回来时丢弃，避免覆盖新选择。 */
		let latestDetailToken = 0;

		const CSS_LEGACY = [
			// ── 档案视图（沿用 gdw-*） ─────────────────────────────────
			".gdw-root { height: 100%; min-height: 320px; box-sizing: border-box; display: flex; flex-direction: column; gap: 12px; padding: 16px 18px; overflow: auto; background: var(--dsw-alias-bg-base); color: var(--dsw-alias-label-primary); font-size: 13px; line-height: 1.5; }",
			".gdw-head { display: flex; align-items: baseline; gap: 10px; flex: none; }",
			".gdw-title { font-size: 16px; font-weight: 700; }",
			".gdw-sub { color: var(--dsw-alias-label-secondary); font-size: 12px; }",
			".gdw-btn { margin-left: auto; border: 1px solid var(--dsw-alias-border-l2); background: var(--dsw-alias-bg-layer-1); color: var(--dsw-alias-label-primary); border-radius: 8px; padding: 4px 12px; cursor: pointer; font-size: 12px; }",
			".gdw-btn:hover { border-color: var(--dsw-alias-brand-primary); }",
			".gdw-pipe { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; flex: none; }",
			".gdw-stage { display: flex; align-items: center; gap: 6px; }",
			".gdw-dot { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-secondary); }",
			".gdw-stage.done .gdw-dot { background: var(--dsw-alias-state-success-primary); color: #fff; }",
			".gdw-stage.active .gdw-dot { background: var(--dsw-alias-brand-primary); color: #fff; }",
			".gdw-slabel { font-size: 12px; color: var(--dsw-alias-label-secondary); }",
			".gdw-stage.done .gdw-slabel, .gdw-stage.active .gdw-slabel { color: var(--dsw-alias-label-primary); font-weight: 600; }",
			".gdw-line { width: 22px; height: 2px; background: var(--dsw-alias-border-l1); }",
			".gdw-line.done { background: var(--dsw-alias-state-success-primary); }",
			".gdw-body { display: flex; gap: 12px; flex: 1; min-height: 0; }",
			".gdw-list { width: 235px; flex: none; display: flex; flex-direction: column; gap: 8px; overflow: auto; }",
			".gdw-pcard { border: 1px solid var(--dsw-alias-border-l1); background: var(--dsw-alias-bg-layer-1); border-radius: 10px; padding: 10px 12px; cursor: pointer; }",
			".gdw-pcard:hover { border-color: var(--dsw-alias-border-l2); }",
			".gdw-pcard.sel { border-color: var(--dsw-alias-brand-primary); box-shadow: 0 0 0 1px var(--dsw-alias-brand-primary); }",
			".gdw-pcard-top { display: flex; align-items: center; gap: 6px; }",
			".gdw-pname { font-weight: 600; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdw-badge { font-size: 10px; padding: 1px 6px; border-radius: 999px; border: 1px solid; flex: none; }",
			".gdw-badge.grid { color: #3b82f6; border-color: #60a5fa; }",
			".gdw-badge.off { color: #b45309; border-color: #d97706; }",
			".gdw-chip { display: inline-block; font-size: 11px; margin-top: 6px; }",
			".gdw-chip.ok { color: var(--dsw-alias-state-success-primary); }",
			".gdw-chip.bad { color: var(--dsw-alias-state-error-primary); }",
			".gdw-chip.mid { color: var(--dsw-alias-label-secondary); }",
			".gdw-pcard-npv { margin-top: 4px; font-size: 12px; color: var(--dsw-alias-label-secondary); }",
			".gdw-detail { flex: 1; min-width: 0; border: 1px solid var(--dsw-alias-border-l1); background: var(--dsw-alias-bg-layer-1); border-radius: 12px; padding: 14px 16px; overflow: auto; }",
			".gdw-tabs { display: flex; align-items: center; gap: 4px; margin-bottom: 12px; }",
			".gdw-tab { border: none; background: none; color: var(--dsw-alias-label-secondary); padding: 5px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; }",
			".gdw-tab:hover { color: var(--dsw-alias-label-primary); }",
			".gdw-tab.on { background: var(--dsw-alias-brand-primary); color: #fff; font-weight: 600; }",
			".gdw-tabs-fill { flex: 1; }",
			".gdw-dpath { font-size: 11px; color: var(--dsw-alias-label-secondary); font-family: monospace; }",
			".gdw-kpis { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-bottom: 12px; }",
			".gdw-kpi { background: var(--dsw-alias-bg-layer-2); border-radius: 10px; padding: 10px 12px; }",
			".gdw-kpi .k { font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdw-kpi .v { font-size: 17px; font-weight: 700; margin-top: 2px; }",
			".gdw-kpi .s { font-size: 11px; color: var(--dsw-alias-label-secondary); margin-top: 2px; }",
			".gdw-panel { border: 1px solid var(--dsw-alias-border-l1); border-radius: 10px; padding: 12px; margin-bottom: 12px; }",
			".gdw-panel-title { font-size: 12px; font-weight: 600; color: var(--dsw-alias-label-secondary); margin-bottom: 10px; }",
			".gdw-caps { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }",
			".gdw-cap { background: var(--dsw-alias-bg-layer-2); border-radius: 10px; padding: 8px 10px; border-left: 3px solid; }",
			".gdw-cap .n { font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdw-cap .v { font-size: 15px; font-weight: 700; margin-top: 2px; }",
			".gdw-cap.dim { opacity: 0.45; }",
			".gdw-cap .u { font-size: 10px; color: var(--dsw-alias-label-secondary); font-weight: 400; }",
			".gdw-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }",
			".gdw-bar-label { width: 140px; flex: none; font-size: 12px; color: var(--dsw-alias-label-secondary); text-align: right; }",
			".gdw-bar-track { flex: 1; height: 8px; border-radius: 4px; background: var(--dsw-alias-bg-layer-2); overflow: hidden; }",
			".gdw-bar-fill { height: 100%; border-radius: 4px; }",
			".gdw-bar-val { width: 110px; flex: none; font-size: 12px; font-variant-numeric: tabular-nums; }",
			".gdw-ratios { display: flex; gap: 14px; flex-wrap: wrap; }",
			".gdw-donut { display: flex; align-items: center; gap: 8px; }",
			".gdw-donut-label { font-size: 12px; color: var(--dsw-alias-label-secondary); max-width: 120px; }",
			".gdw-donut-label b { color: var(--dsw-alias-label-primary); }",
			".gdw-legend { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }",
			".gdw-lg { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdw-lg i { width: 10px; height: 3px; border-radius: 2px; display: inline-block; }",
			".gdw-kv { display: grid; grid-template-columns: 170px 1fr; gap: 4px 12px; font-size: 12.5px; }",
			".gdw-kv .k { color: var(--dsw-alias-label-secondary); }",
			".gdw-kv .v { font-variant-numeric: tabular-nums; word-break: break-all; }",
			".gdw-guide { padding: 30px; text-align: center; color: var(--dsw-alias-label-secondary); }",
			".gdw-guide b { color: var(--dsw-alias-label-primary); display: block; margin-top: 8px; font-size: 14px; }",
			".gdw-vok { font-size: 20px; font-weight: 700; color: var(--dsw-alias-state-success-primary); margin: 8px 0; }",
			".gdw-vbad { font-size: 20px; font-weight: 700; color: var(--dsw-alias-state-error-primary); margin: 8px 0; }",
			".gdw-fail { border: 1px solid var(--dsw-alias-state-error-primary); border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; font-size: 12px; }",
			".gdw-loading { padding: 40px; text-align: center; color: var(--dsw-alias-label-secondary); }",
			// ── 向导视图（gdwz-*） ───────────────────────────────────
			".gdwz-root { height: 100%; min-height: 320px; box-sizing: border-box; display: flex; flex-direction: column; gap: 10px; padding: 14px 18px 10px; overflow: hidden; background: var(--dsw-alias-bg-base); color: var(--dsw-alias-label-primary); font-size: 13px; line-height: 1.5; }",
			".gdwz-head { display: flex; align-items: baseline; gap: 10px; flex: none; }",
			".gdwz-title { font-size: 15px; font-weight: 700; }",
			".gdwz-sub { color: var(--dsw-alias-label-secondary); font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdwz-modes { display: flex; gap: 2px; background: var(--dsw-alias-bg-layer-2); border-radius: 8px; padding: 2px; }",
			".gdwz-mode { border: none; background: none; color: var(--dsw-alias-label-secondary); padding: 3px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; }",
			".gdwz-mode.on { background: var(--dsw-alias-bg-layer-1); color: var(--dsw-alias-label-primary); font-weight: 600; }",
			".gdwz-stepper { display: flex; align-items: center; gap: 0; flex: none; padding: 2px 0 6px; border-bottom: 1px solid var(--dsw-alias-border-l1); }",
			".gdwz-step { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 2px 4px; border-radius: 6px; }",
			".gdwz-dot { width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-secondary); transition: all .2s; }",
			".gdwz-step.done .gdwz-dot { background: var(--dsw-alias-state-success-primary); color: #fff; }",
			".gdwz-step.active .gdwz-dot { background: var(--dsw-alias-brand-primary); color: #fff; animation: gdwz-pulse 1.6s ease-in-out infinite; }",
			"@keyframes gdwz-pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(59,130,246,.35); } 50% { box-shadow: 0 0 0 5px rgba(59,130,246,0); } }",
			".gdwz-sl { font-size: 11.5px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-step.done .gdwz-sl, .gdwz-step.active .gdwz-sl { color: var(--dsw-alias-label-primary); font-weight: 600; }",
			".gdwz-seg { flex: 1; height: 2px; min-width: 14px; background: var(--dsw-alias-border-l1); margin: 0 6px; }",
			".gdwz-seg.done { background: var(--dsw-alias-state-success-primary); }",
			".gdwz-main { flex: 1; min-height: 0; overflow: auto; padding-right: 4px; }",
			".gdwz-jump { display: flex; align-items: center; gap: 8px; padding: 6px 10px; margin-bottom: 10px; border: 1px dashed var(--dsw-alias-brand-primary); border-radius: 8px; color: var(--dsw-alias-brand-primary); font-size: 12px; }",
			".gdwz-jump button { margin-left: auto; }",
			".gdwz-cta-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--dsw-alias-border-l1); }",
			".gdwz-cta { border: none; background: var(--dsw-alias-brand-primary); color: #fff; font-size: 14px; font-weight: 600; border-radius: 10px; padding: 9px 22px; cursor: pointer; }",
			".gdwz-cta:hover { filter: brightness(1.08); }",
			".gdwz-cta:disabled { opacity: .45; cursor: not-allowed; }",
			".gdwz-cta2 { border: 1px solid var(--dsw-alias-border-l2); background: var(--dsw-alias-bg-layer-1); color: var(--dsw-alias-label-primary); font-size: 13px; border-radius: 10px; padding: 8px 16px; cursor: pointer; }",
			".gdwz-cta2:hover { border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-check { display: flex; gap: 8px; align-items: baseline; padding: 6px 10px; border-radius: 8px; margin-bottom: 4px; background: var(--dsw-alias-bg-layer-1); }",
			".gdwz-check .ic { flex: none; font-weight: 700; }",
			".gdwz-check.ok .ic { color: var(--dsw-alias-state-success-primary); }",
			".gdwz-check.bad .ic { color: var(--dsw-alias-state-error-primary); }",
			".gdwz-check .nm { font-weight: 600; flex: none; }",
			".gdwz-check .dt { color: var(--dsw-alias-label-secondary); font-size: 12px; }",
			".gdwz-group { border: 1px solid var(--dsw-alias-border-l1); border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; }",
			".gdwz-group-title { font-size: 12px; font-weight: 600; color: var(--dsw-alias-label-secondary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }",
			".gdwz-field { display: flex; align-items: center; gap: 10px; padding: 5px 4px; border-radius: 6px; }",
			".gdwz-field:hover { background: var(--dsw-alias-bg-layer-1); }",
			".gdwz-field.chg { background: rgba(59,130,246,.08); }",
			".gdwz-fl { width: 190px; flex: none; font-size: 12.5px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-field input[type=number], .gdwz-field input[type=text], .gdwz-field select { flex: 1; min-width: 0; border: 1px solid var(--dsw-alias-border-l2); border-radius: 6px; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-primary); padding: 5px 8px; font-size: 13px; font-variant-numeric: tabular-nums; }",
			".gdwz-field input:focus { outline: none; border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-field input[type=checkbox] { width: 16px; height: 16px; accent-color: var(--dsw-alias-brand-primary); }",
			".gdwz-fv { flex: 1; }",
			".gdwz-old { font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-hl { display: flex; gap: 8px; padding: 7px 10px; border-radius: 8px; background: var(--dsw-alias-bg-layer-1); margin-bottom: 6px; }",
			".gdwz-hl .ic { color: var(--dsw-alias-brand-primary); flex: none; }",
			".gdwz-mini { display: flex; gap: 8px; flex: none; padding-top: 8px; border-top: 1px solid var(--dsw-alias-border-l1); }",
			".gdwz-mini input { flex: 1; border: 1px solid var(--dsw-alias-border-l2); border-radius: 10px; background: var(--dsw-alias-bg-layer-1); color: var(--dsw-alias-label-primary); padding: 8px 12px; font-size: 13px; }",
			".gdwz-mini input:focus { outline: none; border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-mini button { flex: none; border: none; background: var(--dsw-alias-brand-primary); color: #fff; border-radius: 10px; padding: 8px 16px; cursor: pointer; font-size: 13px; }",
			".gdwz-spin { width: 26px; height: 26px; border: 3px solid var(--dsw-alias-border-l2); border-top-color: var(--dsw-alias-brand-primary); border-radius: 50%; animation: gdwz-rot .9s linear infinite; margin: 0 auto 12px; }",
			"@keyframes gdwz-rot { to { transform: rotate(360deg); } }",
			".gdwz-center { text-align: center; color: var(--dsw-alias-label-secondary); padding: 34px 10px; }",
			".gdwz-center b { color: var(--dsw-alias-label-primary); display: block; margin: 8px 0 2px; font-size: 15px; }",
			// ── 工作台页签激活期间隐藏基础输入框（ViewGate 挂载时给
			//    [data-composer-seat] 打 data-gd-workbench 标记，卸载即恢复） ──
			"[data-composer-seat][data-gd-workbench] { display: none !important; }",
			// ── 机器宠物：把与智能体的对话实时反馈进工作台 ──
			".gdwz-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }",
			".gdwz-pet { display: flex; align-items: flex-end; gap: 10px; flex: none; padding-top: 8px; }",
			".gdwz-bot { position: relative; width: 34px; height: 38px; flex: none; margin-top: -2px; }",
			".gdwz-bot-ant { position: absolute; top: 0; left: 50%; width: 2px; height: 8px; margin-left: -1px; background: var(--dsw-alias-border-l2); }",
			".gdwz-bot-ant::after { content: \"\"; position: absolute; top: -4px; left: 50%; width: 6px; height: 6px; margin-left: -3px; border-radius: 50%; background: var(--dsw-alias-label-secondary); }",
			".gdwz-bot-head { position: absolute; top: 10px; bottom: 0; left: 2px; right: 2px; border-radius: 10px 10px 8px 8px; background: var(--dsw-alias-bg-layer-2); border: 1px solid var(--dsw-alias-border-l2); display: flex; align-items: center; justify-content: center; gap: 6px; }",
			".gdwz-bot-eye { width: 5px; height: 5px; border-radius: 50%; background: var(--dsw-alias-label-secondary); animation: gdwz-blink 4.5s infinite; }",
			".gdwz-bot-mouth { position: absolute; bottom: 6px; left: 50%; transform: translateX(-50%); width: 8px; height: 2px; border-radius: 1px; background: var(--dsw-alias-label-secondary); }",
			"@keyframes gdwz-blink { 0%, 92%, 100% { transform: scaleY(1); } 95% { transform: scaleY(.1); } }",
			"@keyframes gdwz-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-2px); } }",
			"@keyframes gdwz-talk { from { width: 4px; } to { width: 13px; } }",
			".gdwz-bot.idle { animation: gdwz-float 3.2s ease-in-out infinite; }",
			".gdwz-bot.think .gdwz-bot-eye { animation: gdwz-blink 1.4s infinite; }",
			".gdwz-bot.think .gdwz-bot-ant::after { background: var(--dsw-alias-state-warn-primary); animation: gdwz-pulse 1.2s ease-in-out infinite; }",
			".gdwz-bot.work .gdwz-bot-ant::after { background: var(--dsw-alias-brand-primary); animation: gdwz-pulse .8s ease-in-out infinite; }",
			".gdwz-bot.work .gdwz-bot-head { border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-bot.speak .gdwz-bot-eye { background: var(--dsw-alias-brand-primary); }",
			".gdwz-bot.speak .gdwz-bot-mouth { animation: gdwz-talk .5s ease-in-out infinite alternate; }",
			".gdwz-bubble { flex: 1; min-width: 0; background: var(--dsw-alias-bg-layer-1); border: 1px solid var(--dsw-alias-border-l1); border-radius: 10px; padding: 5px 10px; font-size: 12px; line-height: 1.55; color: var(--dsw-alias-label-secondary); cursor: pointer; max-height: 58px; overflow: hidden; }",
			".gdwz-bubble:hover { border-color: var(--dsw-alias-border-l2); }",
			".gdwz-bubble.exp { max-height: 180px; overflow-y: auto; color: var(--dsw-alias-label-primary); white-space: pre-wrap; }",
			".gdwz-bubble .src { color: var(--dsw-alias-label-tertiary); font-size: 11px; margin-bottom: 1px; }",
			".gdwz-pet-u { color: var(--dsw-alias-label-tertiary); font-size: 11.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdwz-pet-a { color: var(--dsw-alias-label-secondary); overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }",
			".gdwz-bubble.exp .gdwz-pet-u { white-space: pre-wrap; }",
			".gdwz-bubble.exp .gdwz-pet-a { display: block; -webkit-line-clamp: unset; }",
			".gdwz-pet-tag { flex: none; font-size: 11px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--dsw-alias-border-l2); color: var(--dsw-alias-label-secondary); }",
			".gdwz-pet-tag.think { color: var(--dsw-alias-state-warn-primary); border-color: var(--dsw-alias-state-warn-primary); }",
			".gdwz-pet-tag.work { color: var(--dsw-alias-brand-primary); border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-pet-tag.speak { color: var(--dsw-alias-state-success-primary); border-color: var(--dsw-alias-state-success-primary); }",
			".gdwz-pet-tag.ask { color: var(--dsw-alias-state-warn-primary); border-color: var(--dsw-alias-state-warn-primary); }",
			".gdwz-bot.ask .gdwz-bot-ant::after { background: var(--dsw-alias-state-warn-primary); animation: gdwz-pulse 1.6s ease-in-out infinite; }",
			".gdwz-bot.ask .gdwz-bot-head { border-color: var(--dsw-alias-state-warn-primary); }",
			".gdwz-note { border: 1px dashed var(--dsw-alias-border-l2); border-radius: 8px; padding: 10px 12px; color: var(--dsw-alias-label-secondary); font-size: 12.5px; margin-bottom: 12px; }",
			// ── 挂起交互卡（提问 / 权限确认） ──
			".gdwz-qwrap { flex: none; display: flex; flex-direction: column; gap: 8px; }",
			".gdwz-q { border: 1px solid var(--dsw-alias-state-warn-secondary); background: var(--dsw-alias-bg-layer-1); border-radius: 12px; padding: 10px 14px; flex: none; }",
			".gdwz-q-strip { display: flex; align-items: center; gap: 8px; color: var(--dsw-alias-state-warn-primary); font-size: 12.5px; font-weight: 600; margin-bottom: 4px; }",
			".gdwz-q-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--dsw-alias-state-warn-primary); animation: gdwz-pulse 1.6s ease-in-out infinite; flex: none; }",
			".gdwz-q-item { margin-bottom: 8px; }",
			".gdwz-q-eyebrow { color: var(--dsw-alias-label-tertiary); font-size: 11px; margin-top: 4px; }",
			".gdwz-q-question { font-size: 13.5px; font-weight: 600; margin: 2px 0 2px; }",
			".gdwz-q-detail { font-size: 12px; color: var(--dsw-alias-label-secondary); margin-bottom: 6px; white-space: pre-wrap; }",
			".gdwz-q-opts { display: flex; flex-direction: column; gap: 4px; }",
			".gdwz-q-opt { display: flex; align-items: flex-start; gap: 8px; text-align: left; border: 1px solid transparent; background: none; border-radius: 10px; padding: 7px 10px; cursor: pointer; color: var(--dsw-alias-label-primary); font-size: 13px; }",
			".gdwz-q-opt:hover:not(:disabled) { background: var(--dsw-alias-interactive-bg-hover); }",
			".gdwz-q-opt.sel { border-color: var(--dsw-alias-border-l2); background: var(--dsw-alias-interactive-bg-hover); }",
			".gdwz-q-opt:disabled { opacity: .5; cursor: default; }",
			".gdwz-q-opt .box { flex: none; width: 16px; height: 16px; margin-top: 3px; border: 1px solid var(--dsw-alias-border-l4); border-radius: 50%; display: grid; place-items: center; font-size: 10px; color: var(--dsw-alias-brand-primary); }",
			".gdwz-q-opt.sel .box { border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-q-label { font-weight: 600; }",
			".gdwz-q-desc { display: block; font-size: 12px; color: var(--dsw-alias-label-secondary); font-weight: 400; margin-top: 1px; }",
			".gdwz-q-custom { margin-top: 6px; }",
			".gdwz-q-custom input { width: 100%; box-sizing: border-box; border: 1px solid var(--dsw-alias-border-l2); border-radius: 8px; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-primary); padding: 6px 10px; font-size: 13px; }",
			".gdwz-q-custom input:focus { outline: none; border-color: var(--dsw-alias-brand-primary); }",
			".gdwz-q-skip { border: none; background: none; color: var(--dsw-alias-label-tertiary); font-size: 11.5px; cursor: pointer; padding: 2px 0; margin-top: 4px; text-decoration: underline dotted; }",
			".gdwz-q-skip:hover { color: var(--dsw-alias-label-secondary); }",
			".gdwz-q-actions { display: flex; align-items: center; gap: 10px; margin-top: 8px; }",
			".gdwz-q-err { color: var(--dsw-alias-state-error-primary); font-size: 12px; flex: 1; }",
			".gdwz-q-submit { border: none; background: var(--dsw-alias-brand-primary); color: #fff; border-radius: 10px; padding: 7px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }",
			".gdwz-q-submit:disabled { opacity: .45; cursor: not-allowed; }",
			".gdwz-q-hint { flex: 1; font-size: 11.5px; color: var(--dsw-alias-label-tertiary); }",
			// ── 项目未开始空态 ──
			".gdwz-empty { text-align: center; padding: 34px 16px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-empty b { color: var(--dsw-alias-label-primary); display: block; font-size: 15px; margin: 8px 0 4px; }",
		].join("\n");

		// ═══ 科技感主题（CSS）：青绿→电蓝渐变主色、网格底纹、光晕边框、
		// 等宽数字、呼吸动效。全部基于主题令牌（明暗自适应），color-mix
		// 由现代 Chromium 支持。类名与组件严格对应。 ═══
		const CSS_LIGHTTHEME = [
			// ── 设计令牌（两个视图根共用） ──
			".gdw-root, .gdwz-root { --gd-a: var(--dsw-alias-state-success-primary); --gd-b: var(--dsw-alias-state-business-primary); --gd-grad: linear-gradient(135deg, var(--gd-a), var(--gd-b)); --gd-line: color-mix(in srgb, var(--gd-b) 30%, transparent); --gd-glow: 0 0 16px color-mix(in srgb, var(--gd-b) 22%, transparent); --gd-mono: var(--ds-font-family-code, ui-monospace, monospace); }",
			// ── 通用卡：半透明描边 + 顶部渐变发丝线 ──
			".gd-card { position: relative; border: 1px solid var(--gd-line); border-radius: 14px; background: color-mix(in srgb, var(--dsw-alias-bg-layer-1) 90%, transparent); box-shadow: var(--gd-glow); }",
			".gd-card::before { content: \"\"; position: absolute; left: 14px; right: 14px; top: 0; height: 1.5px; border-radius: 2px; background: var(--gd-grad); opacity: .65; pointer-events: none; }",
			".gd-eyebrow { font-family: var(--gd-mono); font-size: 10px; letter-spacing: .18em; color: color-mix(in srgb, var(--gd-b) 75%, var(--dsw-alias-label-secondary)); text-transform: uppercase; }",
			// ── 档案视图（gdw-*） ──
			".gdw-root { height: 100%; min-height: 320px; box-sizing: border-box; display: flex; flex-direction: column; gap: 12px; padding: 16px 18px; overflow: auto; color: var(--dsw-alias-label-primary); font-size: 13px; line-height: 1.5; background: radial-gradient(1100px 280px at 75% -8%, color-mix(in srgb, var(--gd-b) 9%, transparent), transparent), radial-gradient(800px 240px at 8% -8%, color-mix(in srgb, var(--gd-a) 8%, transparent), transparent), linear-gradient(color-mix(in srgb, var(--dsw-alias-label-primary) 3.5%, transparent) 1px, transparent 1px), linear-gradient(90deg, color-mix(in srgb, var(--dsw-alias-label-primary) 3.5%, transparent) 1px, transparent 1px); background-color: var(--dsw-alias-bg-base); background-size: auto, auto, 30px 30px, 30px 30px; }",
			".gdw-head { display: flex; align-items: flex-end; gap: 10px; flex: none; }",
			".gdw-title { font-size: 16px; font-weight: 700; background: var(--gd-grad); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }",
			".gdw-sub { color: var(--dsw-alias-label-secondary); font-size: 12px; flex: 1; }",
			".gdw-btn { border: 1px solid var(--gd-line); background: color-mix(in srgb, var(--gd-b) 10%, var(--dsw-alias-bg-layer-1)); color: var(--dsw-alias-label-primary); border-radius: 9px; padding: 4px 12px; cursor: pointer; font-size: 12px; transition: box-shadow .15s, border-color .15s; }",
			".gdw-btn:hover { border-color: var(--gd-b); box-shadow: var(--gd-glow); }",
			".gdw-body { display: flex; gap: 12px; flex: 1; min-height: 0; }",
			".gdw-list { width: 240px; flex: none; display: flex; flex-direction: column; gap: 8px; overflow: auto; padding-right: 2px; }",
			".gdw-pcard { border: 1px solid var(--gd-line); background: color-mix(in srgb, var(--dsw-alias-bg-layer-1) 90%, transparent); border-radius: 12px; padding: 10px 12px; cursor: pointer; transition: transform .15s, box-shadow .15s, border-color .15s; }",
			".gdw-pcard:hover { transform: translateY(-2px); box-shadow: var(--gd-glow); border-color: color-mix(in srgb, var(--gd-b) 55%, transparent); }",
			".gdw-pcard.sel { border-color: var(--gd-b); box-shadow: 0 0 0 1px var(--gd-b), var(--gd-glow); background: color-mix(in srgb, var(--gd-b) 7%, var(--dsw-alias-bg-layer-1)); }",
			".gdw-pcard-top { display: flex; align-items: center; gap: 6px; }",
			".gdw-pname { font-weight: 600; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdw-badge { font-size: 10px; padding: 1px 6px; border-radius: 999px; border: 1px solid; flex: none; font-family: var(--gd-mono); letter-spacing: .05em; }",
			".gdw-badge.grid { color: #3b82f6; border-color: #60a5fa; }",
			".gdw-badge.off { color: #b45309; border-color: #d97706; }",
			".gdw-chip { display: inline-block; font-size: 11px; margin-top: 6px; }",
			".gdw-chip.ok { color: var(--dsw-alias-state-success-primary); }",
			".gdw-chip.bad { color: var(--dsw-alias-state-error-primary); }",
			".gdw-chip.mid { color: var(--dsw-alias-label-secondary); }",
			".gdw-pcard-npv { margin-top: 4px; font-size: 12px; color: var(--dsw-alias-label-secondary); font-variant-numeric: tabular-nums; font-family: var(--gd-mono); }",
			".gdw-detail { flex: 1; min-width: 0; border: 1px solid var(--gd-line); background: color-mix(in srgb, var(--dsw-alias-bg-layer-1) 90%, transparent); border-radius: 14px; padding: 14px 16px; overflow: auto; box-shadow: var(--gd-glow); }",
			".gdw-tabs { display: flex; align-items: center; gap: 4px; margin-bottom: 12px; }",
			".gdw-tab { border: none; background: none; color: var(--dsw-alias-label-secondary); padding: 5px 12px; border-radius: 9px; cursor: pointer; font-size: 13px; transition: color .15s, background .15s; }",
			".gdw-tab:hover { color: var(--dsw-alias-label-primary); }",
			".gdw-tab.on { background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-primary); font-weight: 600; box-shadow: inset 0 -2px 0 var(--gd-b); }",
			".gdw-tabs-fill { flex: 1; }",
			".gdw-dpath { font-size: 11px; color: var(--dsw-alias-label-tertiary); font-family: var(--gd-mono); }",
			".gdw-kpis { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-bottom: 12px; }",
			".gdw-kpi { background: color-mix(in srgb, var(--gd-b) 6%, var(--dsw-alias-bg-layer-2)); border-radius: 10px; padding: 10px 12px; border: 1px solid color-mix(in srgb, var(--gd-b) 14%, transparent); }",
			".gdw-kpi .k { font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdw-kpi .v { font-size: 17px; font-weight: 700; margin-top: 2px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); background: var(--gd-grad); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }",
			".gdw-kpi .s { font-size: 11px; color: var(--dsw-alias-label-secondary); margin-top: 2px; }",
			".gdw-panel { border: 1px solid var(--gd-line); border-radius: 12px; padding: 12px; margin-bottom: 12px; background: color-mix(in srgb, var(--dsw-alias-bg-layer-1) 60%, transparent); }",
			".gdw-panel-title { font-size: 12px; font-weight: 600; color: var(--dsw-alias-label-secondary); margin-bottom: 10px; letter-spacing: .04em; }",
			".gdw-caps { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }",
			".gdw-cap { background: color-mix(in srgb, var(--gd-b) 5%, var(--dsw-alias-bg-layer-2)); border-radius: 10px; padding: 8px 10px; border-left: 3px solid; }",
			".gdw-cap .n { font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdw-cap .v { font-size: 15px; font-weight: 700; margin-top: 2px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); }",
			".gdw-cap.dim { opacity: 0.45; }",
			".gdw-cap .u { font-size: 10px; color: var(--dsw-alias-label-secondary); font-weight: 400; }",
			".gdw-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }",
			".gdw-bar-label { width: 140px; flex: none; font-size: 12px; color: var(--dsw-alias-label-secondary); text-align: right; }",
			".gdw-bar-track { flex: 1; height: 7px; border-radius: 4px; background: var(--dsw-alias-bg-layer-2); overflow: hidden; }",
			".gdw-bar-fill { height: 100%; border-radius: 4px; }",
			".gdw-bar-val { width: 110px; flex: none; font-size: 12px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); }",
			".gdw-ratios { display: flex; gap: 14px; flex-wrap: wrap; }",
			".gdw-donut { display: flex; align-items: center; gap: 8px; }",
			".gdw-donut-label { font-size: 12px; color: var(--dsw-alias-label-secondary); max-width: 120px; }",
			".gdw-donut-label b { color: var(--dsw-alias-label-primary); }",
			".gdw-legend { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }",
			".gdw-lg { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdw-lg i { width: 10px; height: 3px; border-radius: 2px; display: inline-block; }",
			".gdw-kv { display: grid; grid-template-columns: 170px 1fr; gap: 4px 12px; font-size: 12.5px; }",
			".gdw-kv .k { color: var(--dsw-alias-label-secondary); }",
			".gdw-kv .v { font-variant-numeric: tabular-nums; font-family: var(--gd-mono); word-break: break-all; }",
			".gdw-guide { padding: 30px; text-align: center; color: var(--dsw-alias-label-secondary); }",
			".gdw-guide b { color: var(--dsw-alias-label-primary); display: block; margin-top: 8px; font-size: 14px; }",
			".gdw-vok { font-size: 20px; font-weight: 700; color: var(--dsw-alias-state-success-primary); margin: 8px 0; }",
			".gdw-vbad { font-size: 20px; font-weight: 700; color: var(--dsw-alias-state-error-primary); margin: 8px 0; }",
			".gdw-fail { border: 1px solid var(--dsw-alias-state-error-primary); border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; font-size: 12px; }",
			".gdw-loading { padding: 40px; text-align: center; color: var(--dsw-alias-label-secondary); }",
			// ── 向导视图（gdwz-*） ──
			".gdwz-root { height: 100%; min-height: 320px; box-sizing: border-box; display: flex; flex-direction: column; gap: 10px; padding: 14px 18px 10px; overflow: hidden; color: var(--dsw-alias-label-primary); font-size: 13px; line-height: 1.5; background: radial-gradient(1100px 280px at 75% -8%, color-mix(in srgb, var(--gd-b) 9%, transparent), transparent), radial-gradient(800px 240px at 8% -8%, color-mix(in srgb, var(--gd-a) 8%, transparent), transparent), linear-gradient(color-mix(in srgb, var(--dsw-alias-label-primary) 3.5%, transparent) 1px, transparent 1px), linear-gradient(90deg, color-mix(in srgb, var(--dsw-alias-label-primary) 3.5%, transparent) 1px, transparent 1px); background-color: var(--dsw-alias-bg-base); background-size: auto, auto, 30px 30px, 30px 30px; }",
			".gdwz-head { display: flex; align-items: flex-end; gap: 12px; flex: none; }",
			".gdwz-headL { min-width: 0; }",
			".gdwz-title { font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; }",
			".gdwz-title .leaf { filter: drop-shadow(0 0 6px color-mix(in srgb, var(--gd-a) 60%, transparent)); }",
			".gdwz-proj { font-size: 12px; font-weight: 500; font-family: var(--gd-mono); color: var(--gd-b); border: 1px solid var(--gd-line); background: color-mix(in srgb, var(--gd-b) 8%, transparent); border-radius: 999px; padding: 2px 10px; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdwz-sub { color: var(--dsw-alias-label-secondary); font-size: 12px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdwz-modes { display: flex; gap: 2px; background: var(--dsw-alias-bg-layer-2); border: 1px solid var(--gd-line); border-radius: 10px; padding: 2px; margin-left: auto; flex: none; }",
			".gdwz-mode { border: none; background: none; color: var(--dsw-alias-label-secondary); padding: 3px 12px; border-radius: 7px; cursor: pointer; font-size: 12px; transition: all .15s; }",
			".gdwz-mode.on { background: var(--gd-grad); color: #fff; font-weight: 600; box-shadow: var(--gd-glow); }",
			".gdwz-stepper { display: flex; align-items: center; gap: 0; flex: none; padding: 8px 6px 10px; }",
			".gdwz-step { display: flex; align-items: center; gap: 7px; cursor: pointer; padding: 3px 6px; border-radius: 8px; transition: background .15s; }",
			".gdwz-step:hover { background: var(--dsw-alias-interactive-bg-hover); }",
			".gdwz-dot { width: 24px; height: 24px; border-radius: 8px; display: grid; place-items: center; font-size: 11px; font-weight: 700; font-family: var(--gd-mono); background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-secondary); border: 1px solid var(--dsw-alias-border-l1); transition: all .25s; }",
			".gdwz-step.done .gdwz-dot { background: var(--gd-grad); color: #fff; border-color: transparent; }",
			".gdwz-step.active .gdwz-dot { background: var(--gd-grad); color: #fff; border-color: transparent; animation: gdwz-ring 1.8s ease-out infinite; }",
			".gdwz-step.viewed .gdwz-dot { box-shadow: 0 0 0 2px color-mix(in srgb, var(--gd-b) 45%, transparent); }",
			"@keyframes gdwz-ring { 0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--gd-b) 55%, transparent); } 100% { box-shadow: 0 0 0 9px transparent; } }",
			".gdwz-sl { font-size: 11.5px; color: var(--dsw-alias-label-secondary); letter-spacing: .02em; }",
			".gdwz-step.done .gdwz-sl, .gdwz-step.active .gdwz-sl { color: var(--dsw-alias-label-primary); font-weight: 600; }",
			".gdwz-seg { flex: 1; height: 2px; min-width: 16px; background: var(--dsw-alias-border-l1); margin: 0 7px; border-radius: 2px; position: relative; overflow: hidden; }",
			".gdwz-seg.done { background: var(--gd-grad); opacity: .8; }",
			".gdwz-main { flex: 1; min-height: 0; overflow: auto; padding: 2px 6px 6px 0; }",
			".gdwz-main::-webkit-scrollbar, .gdwz-log::-webkit-scrollbar, .gdw-list::-webkit-scrollbar, .gdw-detail::-webkit-scrollbar { width: 6px; }",
			".gdwz-main::-webkit-scrollbar-thumb, .gdwz-log::-webkit-scrollbar-thumb, .gdw-list::-webkit-scrollbar-thumb, .gdw-detail::-webkit-scrollbar-thumb { background: color-mix(in srgb, var(--gd-b) 35%, transparent); border-radius: 3px; }",
			".gdwz-stagecard { padding: 14px 16px; }",
			".gdwz-jump { display: flex; align-items: center; gap: 8px; padding: 7px 12px; margin-bottom: 10px; border: 1px solid var(--gd-line); border-radius: 10px; color: var(--gd-b); font-size: 12px; background: color-mix(in srgb, var(--gd-b) 6%, transparent); }",
			".gdwz-jump button { margin-left: auto; }",
			".gdwz-cta-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--gd-line); }",
			".gdwz-cta { border: none; background: var(--gd-grad); color: #fff; font-size: 14px; font-weight: 600; border-radius: 11px; padding: 9px 22px; cursor: pointer; box-shadow: var(--gd-glow); transition: transform .15s, filter .15s; }",
			".gdwz-cta:hover { filter: brightness(1.1); transform: translateY(-1px); }",
			".gdwz-cta:disabled { opacity: .45; cursor: not-allowed; transform: none; }",
			".gdwz-cta2 { border: 1px solid var(--gd-line); background: color-mix(in srgb, var(--gd-b) 8%, var(--dsw-alias-bg-layer-1)); color: var(--dsw-alias-label-primary); font-size: 13px; border-radius: 11px; padding: 8px 16px; cursor: pointer; transition: all .15s; }",
			".gdwz-cta2:hover { border-color: var(--gd-b); box-shadow: var(--gd-glow); }",
			".gdwz-check { display: flex; gap: 8px; align-items: baseline; padding: 7px 11px; border-radius: 9px; margin-bottom: 5px; background: color-mix(in srgb, var(--dsw-alias-bg-layer-1) 70%, transparent); border: 1px solid color-mix(in srgb, var(--gd-b) 10%, transparent); }",
			".gdwz-check .ic { flex: none; font-weight: 700; }",
			".gdwz-check.ok .ic { color: var(--dsw-alias-state-success-primary); }",
			".gdwz-check.bad .ic { color: var(--dsw-alias-state-error-primary); }",
			".gdwz-check .nm { font-weight: 600; flex: none; }",
			".gdwz-check .dt { color: var(--dsw-alias-label-secondary); font-size: 12px; }",
			".gdwz-group { border: 1px solid var(--gd-line); border-radius: 11px; padding: 10px 12px; margin-bottom: 10px; background: color-mix(in srgb, var(--dsw-alias-bg-layer-1) 55%, transparent); }",
			".gdwz-group-title { font-size: 12px; font-weight: 600; color: var(--dsw-alias-label-secondary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; letter-spacing: .04em; }",
			".gdwz-field { display: flex; align-items: center; gap: 10px; padding: 5px 6px; border-radius: 7px; }",
			".gdwz-field:hover { background: var(--dsw-alias-interactive-bg-hover); }",
			".gdwz-field.chg { background: color-mix(in srgb, var(--gd-a) 10%, transparent); }",
			".gdwz-fl { width: 190px; flex: none; font-size: 12.5px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-field input[type=number], .gdwz-field input[type=text], .gdwz-field select { flex: 1; min-width: 0; border: 1px solid var(--gd-line); border-radius: 7px; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-primary); padding: 5px 9px; font-size: 13px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); transition: border-color .15s, box-shadow .15s; }",
			".gdwz-field input:focus { outline: none; border-color: var(--gd-b); box-shadow: 0 0 0 3px color-mix(in srgb, var(--gd-b) 18%, transparent); }",
			".gdwz-field input[type=checkbox] { width: 16px; height: 16px; accent-color: var(--gd-b); }",
			".gdwz-fv { flex: 1; }",
			".gdwz-old { font-size: 11px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-hl { display: flex; gap: 8px; padding: 8px 11px; border-radius: 9px; background: color-mix(in srgb, var(--gd-b) 6%, var(--dsw-alias-bg-layer-1)); border: 1px solid color-mix(in srgb, var(--gd-b) 16%, transparent); margin-bottom: 6px; }",
			".gdwz-hl .ic { color: var(--gd-b); flex: none; }",
			".gdwz-spin { width: 26px; height: 26px; border: 3px solid var(--gd-line); border-top-color: var(--gd-b); border-radius: 50%; animation: gdwz-rot .9s linear infinite; margin: 0 auto 12px; }",
			"@keyframes gdwz-rot { to { transform: rotate(360deg); } }",
			".gdwz-center { text-align: center; color: var(--dsw-alias-label-secondary); padding: 34px 10px; }",
			".gdwz-center b { color: var(--dsw-alias-label-primary); display: block; margin: 8px 0 2px; font-size: 15px; }",
			".gdwz-note { border: 1px dashed var(--gd-line); border-radius: 9px; padding: 10px 12px; color: var(--dsw-alias-label-secondary); font-size: 12.5px; margin-bottom: 12px; }",
			".gdwz-empty { text-align: center; padding: 40px 16px 30px; color: var(--dsw-alias-label-secondary); }",
			".gdwz-empty .big { font-size: 30px; display: inline-block; filter: drop-shadow(0 0 12px color-mix(in srgb, var(--gd-a) 65%, transparent)); animation: gdwz-float 3.2s ease-in-out infinite; }",
			".gdwz-empty b { color: var(--dsw-alias-label-primary); display: block; font-size: 15px; margin: 10px 0 6px; }",
			// 工作台页签激活期间隐藏基础输入框（DOM 标记 + CSS，卸载即恢复）
			"[data-composer-seat][data-gd-workbench] { display: none !important; }",
			// ── 实时对话台（完整对话展示 + 指令输入） ──
			".gdwz-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }",
			".gdwz-console { flex: none; display: flex; flex-direction: column; }",
			".gdwz-console.ask { border-color: color-mix(in srgb, var(--dsw-alias-state-warn-primary) 45%, transparent); }",
			".gdwz-console.ask::before { background: linear-gradient(135deg, var(--dsw-alias-state-warn-primary), var(--gd-b)); }",
			".gdwz-console-head { display: flex; align-items: center; gap: 10px; padding: 6px 12px 4px; }",
			".gdwz-console-tt { min-width: 0; flex: 1; }",
			".gdwz-console-name { font-size: 12.5px; font-weight: 700; letter-spacing: .03em; }",
			".gdwz-console-sub { font-size: 10.5px; color: var(--dsw-alias-label-tertiary); font-family: var(--gd-mono); letter-spacing: .06em; }",
			".gdwz-log { max-height: 208px; min-height: 56px; overflow-y: auto; overscroll-behavior: contain; padding: 4px 12px 6px; display: flex; flex-direction: column; gap: 6px; }",
			".gdwz-log-empty { color: var(--dsw-alias-label-tertiary); font-size: 12px; padding: 8px 2px; }",
			".gdwz-msg { display: flex; gap: 8px; align-items: flex-start; }",
			".gdwz-msg-chip { flex: none; font-size: 10px; font-weight: 700; font-family: var(--gd-mono); letter-spacing: .08em; border-radius: 6px; padding: 2px 7px; margin-top: 1px; }",
			".gdwz-msg-chip.user { background: var(--gd-grad); color: #fff; }",
			".gdwz-msg-chip.ai { color: var(--gd-a); border: 1px solid color-mix(in srgb, var(--gd-a) 45%, transparent); background: color-mix(in srgb, var(--gd-a) 8%, transparent); }",
			".gdwz-msg-chip.sys { color: var(--dsw-alias-label-secondary); border: 1px dashed var(--gd-line); }",
			".gdwz-msg-text { flex: 1; min-width: 0; font-size: 12.5px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: var(--dsw-alias-label-primary); }",
			".gdwz-msg.user .gdwz-msg-text { color: var(--dsw-alias-label-primary); background: color-mix(in srgb, var(--gd-b) 6%, transparent); border-radius: 0 10px 10px 0; padding: 3px 10px 3px 8px; border-left: 2px solid color-mix(in srgb, var(--gd-b) 55%, transparent); }",
			".gdwz-msg.ai .gdwz-msg-text { color: var(--dsw-alias-label-primary); }",
			".gdwz-msg.sys .gdwz-msg-text { color: var(--dsw-alias-label-secondary); font-size: 12px; font-family: var(--gd-mono); }",
			".gdwz-msg.live .gdwz-msg-text::after { content: \"▍\"; color: var(--gd-a); animation: gdwz-caret 1s steps(1) infinite; }",
			"@keyframes gdwz-caret { 50% { opacity: 0; } }",
			".gdwz-console-input { display: flex; gap: 8px; padding: 6px 12px 10px; }",
			".gdwz-console-input input { flex: 1; min-width: 0; border: 1px solid var(--gd-line); border-radius: 10px; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-primary); padding: 8px 12px; font-size: 13px; transition: border-color .15s, box-shadow .15s; }",
			".gdwz-console-input input::placeholder { color: var(--dsw-alias-label-tertiary); }",
			".gdwz-console-input input:focus { outline: none; border-color: var(--gd-b); box-shadow: 0 0 0 3px color-mix(in srgb, var(--gd-b) 18%, transparent); }",
			".gdwz-console-input button { flex: none; border: none; background: var(--gd-grad); color: #fff; border-radius: 10px; padding: 8px 18px; cursor: pointer; font-size: 13px; font-weight: 600; box-shadow: var(--gd-glow); transition: filter .15s, transform .15s; }",
			".gdwz-console-input button:hover:not(:disabled) { filter: brightness(1.1); transform: translateY(-1px); }",
			".gdwz-console-input button:disabled { opacity: .45; cursor: not-allowed; }",
			// ── 机器宠物（对话台状态化身） ──
			".gdwz-bot { position: relative; width: 30px; height: 34px; flex: none; }",
			".gdwz-bot-ant { position: absolute; top: 0; left: 50%; width: 2px; height: 7px; margin-left: -1px; background: var(--gd-line); }",
			".gdwz-bot-ant::after { content: \"\"; position: absolute; top: -4px; left: 50%; width: 6px; height: 6px; margin-left: -3px; border-radius: 50%; background: var(--dsw-alias-label-secondary); }",
			".gdwz-bot-head { position: absolute; top: 9px; bottom: 0; left: 2px; right: 2px; border-radius: 10px 10px 8px 8px; background: var(--dsw-alias-bg-layer-2); border: 1px solid var(--gd-line); display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: inset 0 0 8px color-mix(in srgb, var(--gd-b) 12%, transparent); }",
			".gdwz-bot-eye { width: 5px; height: 5px; border-radius: 50%; background: var(--gd-b); box-shadow: 0 0 6px var(--gd-b); animation: gdwz-blink 4.5s infinite; }",
			".gdwz-bot-mouth { position: absolute; bottom: 6px; left: 50%; transform: translateX(-50%); width: 8px; height: 2px; border-radius: 1px; background: var(--dsw-alias-label-secondary); }",
			"@keyframes gdwz-blink { 0%, 92%, 100% { transform: scaleY(1); } 95% { transform: scaleY(.1); } }",
			"@keyframes gdwz-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }",
			"@keyframes gdwz-talk { from { width: 4px; } to { width: 13px; } }",
			".gdwz-bot.idle { animation: gdwz-float 3.2s ease-in-out infinite; }",
			".gdwz-bot.think .gdwz-bot-eye { animation: gdwz-blink 1.4s infinite; }",
			".gdwz-bot.think .gdwz-bot-ant::after { background: var(--dsw-alias-state-warn-primary); animation: gdwz-ring 1.2s ease-out infinite; }",
			".gdwz-bot.work .gdwz-bot-ant::after { background: var(--gd-b); animation: gdwz-ring .8s ease-out infinite; }",
			".gdwz-bot.work .gdwz-bot-head { border-color: var(--gd-b); }",
			".gdwz-bot.speak .gdwz-bot-eye { background: var(--gd-a); box-shadow: 0 0 8px var(--gd-a); }",
			".gdwz-bot.speak .gdwz-bot-mouth { animation: gdwz-talk .5s ease-in-out infinite alternate; }",
			".gdwz-bot.ask .gdwz-bot-ant::after { background: var(--dsw-alias-state-warn-primary); animation: gdwz-ring 1.6s ease-out infinite; }",
			".gdwz-bot.ask .gdwz-bot-head { border-color: var(--dsw-alias-state-warn-primary); }",
			".gdwz-pet-tag { flex: none; font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; border: 1px solid var(--gd-line); color: var(--dsw-alias-label-secondary); font-family: var(--gd-mono); }",
			".gdwz-pet-tag.think { color: var(--dsw-alias-state-warn-primary); border-color: var(--dsw-alias-state-warn-primary); }",
			".gdwz-pet-tag.work { color: var(--gd-b); border-color: var(--gd-b); box-shadow: 0 0 10px color-mix(in srgb, var(--gd-b) 25%, transparent); }",
			".gdwz-pet-tag.speak { color: var(--gd-a); border-color: var(--gd-a); }",
			".gdwz-pet-tag.ask { color: var(--dsw-alias-state-warn-primary); border-color: var(--dsw-alias-state-warn-primary); animation: gdwz-caret 1.2s steps(1) infinite; }",
			// ── 挂起交互卡（提问 / 权限确认） ──
			".gdwz-qwrap { flex: none; display: flex; flex-direction: column; gap: 8px; }",
			".gdwz-q { border: 1px solid color-mix(in srgb, var(--dsw-alias-state-warn-primary) 45%, transparent); background: color-mix(in srgb, var(--dsw-alias-state-warn-primary) 5%, var(--dsw-alias-bg-layer-1)); border-radius: 13px; padding: 10px 14px; flex: none; box-shadow: 0 0 14px color-mix(in srgb, var(--dsw-alias-state-warn-primary) 18%, transparent); }",
			".gdwz-q-strip { display: flex; align-items: center; gap: 8px; color: var(--dsw-alias-state-warn-primary); font-size: 12.5px; font-weight: 700; margin-bottom: 4px; }",
			".gdwz-q-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--dsw-alias-state-warn-primary); box-shadow: 0 0 8px var(--dsw-alias-state-warn-primary); animation: gdwz-caret 1.2s steps(1) infinite; flex: none; }",
			".gdwz-q-item { margin-bottom: 8px; }",
			".gdwz-q-eyebrow { color: var(--dsw-alias-label-tertiary); font-size: 11px; margin-top: 4px; font-family: var(--gd-mono); letter-spacing: .05em; }",
			".gdwz-q-question { font-size: 13.5px; font-weight: 700; margin: 2px 0 2px; }",
			".gdwz-q-detail { font-size: 12px; color: var(--dsw-alias-label-secondary); margin-bottom: 6px; white-space: pre-wrap; }",
			".gdwz-q-opts { display: flex; flex-direction: column; gap: 4px; }",
			".gdwz-q-opt { display: flex; align-items: flex-start; gap: 8px; text-align: left; border: 1px solid transparent; background: none; border-radius: 10px; padding: 7px 10px; cursor: pointer; color: var(--dsw-alias-label-primary); font-size: 13px; transition: border-color .15s, background .15s; }",
			".gdwz-q-opt:hover:not(:disabled) { background: var(--dsw-alias-interactive-bg-hover); border-color: var(--gd-line); }",
			".gdwz-q-opt.sel { border-color: var(--gd-b); background: color-mix(in srgb, var(--gd-b) 9%, transparent); box-shadow: var(--gd-glow); }",
			".gdwz-q-opt:disabled { opacity: .5; cursor: default; }",
			".gdwz-q-opt .box { flex: none; width: 16px; height: 16px; margin-top: 3px; border: 1px solid var(--dsw-alias-border-l4); border-radius: 50%; display: grid; place-items: center; font-size: 10px; color: var(--gd-b); }",
			".gdwz-q-opt.sel .box { border-color: var(--gd-b); box-shadow: 0 0 6px color-mix(in srgb, var(--gd-b) 40%, transparent); }",
			".gdwz-q-label { font-weight: 600; }",
			".gdwz-q-desc { display: block; font-size: 12px; color: var(--dsw-alias-label-secondary); font-weight: 400; margin-top: 1px; }",
			".gdwz-q-custom { margin-top: 6px; }",
			".gdwz-q-custom input { width: 100%; box-sizing: border-box; border: 1px solid var(--gd-line); border-radius: 9px; background: var(--dsw-alias-bg-layer-2); color: var(--dsw-alias-label-primary); padding: 6px 10px; font-size: 13px; transition: border-color .15s, box-shadow .15s; }",
			".gdwz-q-custom input:focus { outline: none; border-color: var(--gd-b); box-shadow: 0 0 0 3px color-mix(in srgb, var(--gd-b) 18%, transparent); }",
			".gdwz-q-skip { border: none; background: none; color: var(--dsw-alias-label-tertiary); font-size: 11.5px; cursor: pointer; padding: 2px 0; margin-top: 4px; text-decoration: underline dotted; }",
			".gdwz-q-skip:hover { color: var(--dsw-alias-label-secondary); }",
			".gdwz-q-actions { display: flex; align-items: center; gap: 10px; margin-top: 8px; }",
			".gdwz-q-err { color: var(--dsw-alias-state-error-primary); font-size: 12px; flex: 1; }",
			".gdwz-q-submit { border: none; background: var(--dsw-alias-state-warn-primary); color: #fff; border-radius: 10px; padding: 7px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }",
			".gdwz-q-submit:disabled { opacity: .45; cursor: not-allowed; }",
			".gdwz-q-hint { flex: 1; font-size: 11.5px; color: var(--dsw-alias-label-tertiary); }",
		].join("\n");

		// ═══ 深空任务控制台主题（生效版）：固定深空底 + 荧光青/翠绿 HUD、
		// 网格底纹、辉光边框、等宽数据字体、能量流动效。只作用于工作台
		// 子树（gdw-*/gdwz-*/gd-* 前缀类），聊天界面与全局主题不受影响。 ═══
		const CSS = [
			// ── 深空设计令牌 ──
			".gdw-root, .gdwz-root { --gd-a: #34d399; --gd-b: #22d3ee; --gd-grad: linear-gradient(135deg, #34d399, #22d3ee); --gd-line: rgba(34,211,238,.24); --gd-line2: rgba(34,211,238,.5); --gd-glow: 0 0 18px rgba(34,211,238,.15); --gd-txt: #dcf1ff; --gd-sub: #8ea9cc; --gd-dim: #5c7699; --gd-panel: #0b1522; --gd-panel2: #0a121e; --gd-warn: #fbbf24; --gd-err: #fb7185; --gd-mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; color: var(--gd-txt); }",
			// ── 通用 HUD 卡：渐变面板 + 顶部荧光发丝线 + 右下折角 ──
			".gd-card { position: relative; border: 1px solid var(--gd-line); border-radius: 14px; background: linear-gradient(180deg, rgba(34,211,238,.07), rgba(34,211,238,.02) 40%, transparent), var(--gd-panel); box-shadow: var(--gd-glow), inset 0 1px 0 rgba(220,241,255,.06); }",
			".gd-card::before { content: \"\"; position: absolute; left: 12px; right: 12px; top: 0; height: 1.5px; border-radius: 2px; background: var(--gd-grad); opacity: .7; pointer-events: none; }",
			".gd-card::after { content: \"\"; position: absolute; right: 6px; bottom: 6px; width: 13px; height: 13px; border-right: 2px solid var(--gd-line2); border-bottom: 2px solid var(--gd-line2); border-radius: 0 0 9px 0; pointer-events: none; }",
			".gd-eyebrow { font-family: var(--gd-mono); font-size: 10px; letter-spacing: .22em; color: var(--gd-b); text-transform: uppercase; text-shadow: 0 0 10px rgba(34,211,238,.55); }",
			".gd-hint { color: var(--gd-sub); font-size: 12px; }",
			// ── 档案视图（gdw-*） ──
			".gdw-root { height: 100%; min-height: 320px; box-sizing: border-box; display: flex; flex-direction: column; gap: 12px; padding: 16px 18px; overflow: auto; font-size: 13px; line-height: 1.5; color: var(--gd-txt); background: radial-gradient(900px 320px at 75% -10%, rgba(34,211,238,.10), transparent 60%), radial-gradient(700px 260px at 5% -8%, rgba(52,211,153,.09), transparent 60%), radial-gradient(1200px 500px at 50% 120%, rgba(34,211,238,.06), transparent 60%), linear-gradient(rgba(34,211,238,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,.045) 1px, transparent 1px); background-color: #04070c; background-size: auto, auto, auto, 32px 32px, 32px 32px; }",
			".gdw-head { display: flex; align-items: flex-end; gap: 10px; flex: none; }",
			".gdw-title { font-size: 16px; font-weight: 700; color: #f2fbff; text-shadow: 0 0 14px rgba(34,211,238,.35); }",
			".gdw-sub { color: var(--gd-sub); font-size: 12px; flex: 1; }",
			".gdw-btn { border: 1px solid var(--gd-line); background: rgba(34,211,238,.08); color: var(--gd-txt); border-radius: 9px; padding: 4px 12px; cursor: pointer; font-size: 12px; transition: all .15s; }",
			".gdw-btn:hover { border-color: var(--gd-b); box-shadow: 0 0 14px rgba(34,211,238,.3); }",
			".gdw-body { display: flex; gap: 12px; flex: 1; min-height: 0; }",
			".gdw-list { width: 245px; flex: none; display: flex; flex-direction: column; gap: 8px; overflow: auto; padding-right: 2px; }",
			".gdw-pcard { border: 1px solid var(--gd-line); background: linear-gradient(180deg, rgba(34,211,238,.05), transparent), var(--gd-panel2); border-radius: 12px; padding: 10px 12px; cursor: pointer; transition: transform .15s, box-shadow .15s, border-color .15s; }",
			".gdw-pcard:hover { transform: translateY(-2px); box-shadow: 0 0 16px rgba(34,211,238,.22); border-color: var(--gd-line2); }",
			".gdw-pcard.sel { border-color: var(--gd-b); box-shadow: 0 0 0 1px var(--gd-b), 0 0 18px rgba(34,211,238,.3); background: linear-gradient(180deg, rgba(34,211,238,.12), transparent), var(--gd-panel); }",
			".gdw-pcard-top { display: flex; align-items: center; gap: 6px; }",
			".gdw-pname { font-weight: 600; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--gd-txt); }",
			".gdw-badge { font-size: 10px; padding: 1px 6px; border-radius: 999px; border: 1px solid; flex: none; font-family: var(--gd-mono); letter-spacing: .05em; }",
			".gdw-badge.grid { color: #38bdf8; border-color: rgba(56,189,248,.55); background: rgba(56,189,248,.08); }",
			".gdw-badge.off { color: var(--gd-warn); border-color: rgba(251,191,36,.55); background: rgba(251,191,36,.08); }",
			".gdw-chip { display: inline-block; font-size: 11px; margin-top: 6px; font-family: var(--gd-mono); }",
			".gdw-chip.ok { color: var(--gd-a); text-shadow: 0 0 8px rgba(52,211,153,.5); }",
			".gdw-chip.bad { color: var(--gd-err); text-shadow: 0 0 8px rgba(251,113,133,.5); }",
			".gdw-chip.mid { color: var(--gd-sub); }",
			".gdw-pcard-npv { margin-top: 4px; font-size: 12px; color: var(--gd-sub); font-variant-numeric: tabular-nums; font-family: var(--gd-mono); }",
			".gdw-detail { flex: 1; min-width: 0; border: 1px solid var(--gd-line); background: var(--gd-panel); border-radius: 14px; padding: 14px 16px; overflow: auto; box-shadow: var(--gd-glow); position: relative; }",
			".gdw-detail::before { content: \"\"; position: absolute; left: 12px; right: 12px; top: 0; height: 1.5px; background: var(--gd-grad); opacity: .6; pointer-events: none; }",
			".gdw-tabs { display: flex; align-items: center; gap: 4px; margin-bottom: 12px; }",
			".gdw-tab { border: none; background: none; color: var(--gd-sub); padding: 5px 12px; border-radius: 9px; cursor: pointer; font-size: 13px; transition: all .15s; }",
			".gdw-tab:hover { color: var(--gd-txt); }",
			".gdw-tab.on { background: rgba(34,211,238,.14); color: var(--gd-b); font-weight: 700; box-shadow: inset 0 -2px 0 var(--gd-b), 0 0 10px rgba(34,211,238,.18); }",
			".gdw-tabs-fill { flex: 1; }",
			".gdw-dpath { font-size: 11px; color: var(--gd-dim); font-family: var(--gd-mono); }",
			".gdw-kpis { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-bottom: 12px; }",
			".gdw-kpi { background: linear-gradient(180deg, rgba(34,211,238,.09), rgba(34,211,238,.02)), var(--gd-panel2); border-radius: 10px; padding: 10px 12px; border: 1px solid var(--gd-line); }",
			".gdw-kpi .k { font-size: 11px; color: var(--gd-sub); }",
			".gdw-kpi .v { font-size: 17px; font-weight: 700; margin-top: 2px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); color: var(--gd-b); text-shadow: 0 0 12px rgba(34,211,238,.55); }",
			".gdw-kpi .s { font-size: 11px; color: var(--gd-dim); margin-top: 2px; }",
			".gdw-panel { border: 1px solid var(--gd-line); border-radius: 12px; padding: 12px; margin-bottom: 12px; background: rgba(34,211,238,.03); }",
			".gdw-panel-title { font-size: 12px; font-weight: 700; color: var(--gd-sub); margin-bottom: 10px; letter-spacing: .06em; font-family: var(--gd-mono); }",
			".gdw-caps { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }",
			".gdw-cap { background: var(--gd-panel2); border-radius: 10px; padding: 8px 10px; border-left: 3px solid var(--gd-b); }",
			".gdw-cap .n { font-size: 11px; color: var(--gd-sub); }",
			".gdw-cap .v { font-size: 15px; font-weight: 700; margin-top: 2px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); color: var(--gd-a); text-shadow: 0 0 10px rgba(52,211,153,.45); }",
			".gdw-cap.dim { opacity: 0.45; }",
			".gdw-cap .u { font-size: 10px; color: var(--gd-dim); font-weight: 400; }",
			".gdw-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }",
			".gdw-bar-label { width: 140px; flex: none; font-size: 12px; color: var(--gd-sub); text-align: right; }",
			".gdw-bar-track { flex: 1; height: 7px; border-radius: 4px; background: rgba(34,211,238,.1); overflow: hidden; }",
			".gdw-bar-fill { height: 100%; border-radius: 4px; box-shadow: 0 0 8px rgba(34,211,238,.5); }",
			".gdw-bar-val { width: 110px; flex: none; font-size: 12px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); color: var(--gd-txt); }",
			".gdw-ratios { display: flex; gap: 14px; flex-wrap: wrap; }",
			".gdw-donut { display: flex; align-items: center; gap: 8px; }",
			".gdw-donut-label { font-size: 12px; color: var(--gd-sub); max-width: 120px; }",
			".gdw-donut-label b { color: var(--gd-txt); }",
			".gdw-legend { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }",
			".gdw-lg { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--gd-sub); }",
			".gdw-lg i { width: 10px; height: 3px; border-radius: 2px; display: inline-block; }",
			".gdw-kv { display: grid; grid-template-columns: 170px 1fr; gap: 4px 12px; font-size: 12.5px; }",
			".gdw-kv .k { color: var(--gd-sub); }",
			".gdw-kv .v { font-variant-numeric: tabular-nums; font-family: var(--gd-mono); word-break: break-all; color: var(--gd-txt); }",
			".gdw-guide { padding: 30px; text-align: center; color: var(--gd-sub); }",
			".gdw-guide b { color: var(--gd-txt); display: block; margin-top: 8px; font-size: 14px; }",
			".gdw-vok { font-size: 20px; font-weight: 700; color: var(--gd-a); margin: 8px 0; text-shadow: 0 0 16px rgba(52,211,153,.6); }",
			".gdw-vbad { font-size: 20px; font-weight: 700; color: var(--gd-err); margin: 8px 0; text-shadow: 0 0 16px rgba(251,113,133,.6); }",
			".gdw-fail { border: 1px solid rgba(251,113,133,.5); background: rgba(251,113,133,.07); border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; font-size: 12px; color: var(--gd-err); }",
			".gdw-loading { padding: 40px; text-align: center; color: var(--gd-sub); }",
			// ── 向导视图（gdwz-*） ──
			".gdwz-root { height: 100%; min-height: 320px; box-sizing: border-box; display: flex; flex-direction: column; gap: 10px; padding: 14px 18px 10px; overflow: hidden; font-size: 13px; line-height: 1.5; color: var(--gd-txt); background: radial-gradient(900px 320px at 75% -10%, rgba(34,211,238,.10), transparent 60%), radial-gradient(700px 260px at 5% -8%, rgba(52,211,153,.09), transparent 60%), radial-gradient(1200px 500px at 50% 120%, rgba(34,211,238,.06), transparent 60%), linear-gradient(rgba(34,211,238,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,.045) 1px, transparent 1px); background-color: #04070c; background-size: auto, auto, auto, 32px 32px, 32px 32px; }",
			".gdwz-head { display: flex; align-items: flex-end; gap: 12px; flex: none; }",
			".gdwz-headL { min-width: 0; }",
			".gdwz-title { font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; color: #f2fbff; text-shadow: 0 0 16px rgba(34,211,238,.4); }",
			".gdwz-title .leaf { filter: drop-shadow(0 0 8px rgba(52,211,153,.75)); }",
			".gdwz-proj { font-size: 12px; font-weight: 600; font-family: var(--gd-mono); color: var(--gd-b); border: 1px solid var(--gd-line2); background: rgba(34,211,238,.1); border-radius: 999px; padding: 2px 10px; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdwz-sub { color: var(--gd-sub); font-size: 12px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
			".gdwz-modes { display: flex; gap: 2px; background: rgba(34,211,238,.06); border: 1px solid var(--gd-line); border-radius: 10px; padding: 2px; margin-left: auto; flex: none; }",
			".gdwz-mode { border: none; background: none; color: var(--gd-sub); padding: 3px 12px; border-radius: 7px; cursor: pointer; font-size: 12px; transition: all .15s; }",
			".gdwz-mode.on { background: var(--gd-grad); color: #04202b; font-weight: 700; box-shadow: 0 0 12px rgba(52,211,153,.4); }",
			".gdwz-stepper { display: flex; align-items: center; gap: 0; flex: none; padding: 8px 6px 10px; }",
			".gdwz-step { display: flex; align-items: center; gap: 7px; cursor: pointer; padding: 3px 6px; border-radius: 8px; transition: background .15s; }",
			".gdwz-step:hover { background: rgba(34,211,238,.08); }",
			".gdwz-dot { width: 24px; height: 24px; border-radius: 8px; display: grid; place-items: center; font-size: 11px; font-weight: 700; font-family: var(--gd-mono); background: var(--gd-panel2); color: var(--gd-dim); border: 1px solid var(--gd-line); box-shadow: inset 0 0 8px rgba(34,211,238,.1); transition: all .25s; }",
			".gdwz-step.done .gdwz-dot { background: var(--gd-grad); color: #04202b; border-color: transparent; box-shadow: 0 0 12px rgba(52,211,153,.45); }",
			".gdwz-step.active .gdwz-dot { background: var(--gd-grad); color: #04202b; border-color: transparent; animation: gd-ring 1.8s ease-out infinite; }",
			".gdwz-step.viewed .gdwz-dot { box-shadow: 0 0 0 2px rgba(34,211,238,.55); }",
			"@keyframes gd-ring { 0% { box-shadow: 0 0 0 0 rgba(34,211,238,.65); } 100% { box-shadow: 0 0 0 10px transparent; } }",
			".gdwz-sl { font-size: 11.5px; color: var(--gd-sub); letter-spacing: .03em; }",
			".gdwz-step.done .gdwz-sl, .gdwz-step.active .gdwz-sl { color: var(--gd-txt); font-weight: 700; }",
			".gdwz-seg { flex: 1; height: 2px; min-width: 16px; background: rgba(34,211,238,.14); margin: 0 7px; border-radius: 2px; overflow: hidden; }",
			".gdwz-seg.done { background: linear-gradient(90deg, transparent, rgba(52,211,153,.95), transparent); background-size: 200% 100%; animation: gd-flow 2.6s linear infinite; }",
			"@keyframes gd-flow { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }",
			".gdwz-main { flex: 1; min-height: 0; overflow: auto; padding: 2px 6px 6px 0; }",
			".gdwz-main::-webkit-scrollbar, .gdwz-log::-webkit-scrollbar, .gdw-list::-webkit-scrollbar, .gdw-detail::-webkit-scrollbar { width: 6px; }",
			".gdwz-main::-webkit-scrollbar-thumb, .gdwz-log::-webkit-scrollbar-thumb, .gdw-list::-webkit-scrollbar-thumb, .gdw-detail::-webkit-scrollbar-thumb { background: rgba(34,211,238,.3); border-radius: 3px; }",
			".gdwz-main::-webkit-scrollbar-track, .gdwz-log::-webkit-scrollbar-track { background: rgba(34,211,238,.05); }",
			".gdwz-stagecard { padding: 14px 16px; }",
			".gdwz-jump { display: flex; align-items: center; gap: 8px; padding: 7px 12px; margin-bottom: 10px; border: 1px solid var(--gd-line2); border-radius: 10px; color: var(--gd-b); font-size: 12px; background: rgba(34,211,238,.07); box-shadow: 0 0 12px rgba(34,211,238,.15); }",
			".gdwz-jump button { margin-left: auto; }",
			".gdwz-cta-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--gd-line); }",
			".gdwz-cta { border: none; background: var(--gd-grad); color: #04202b; font-size: 14px; font-weight: 700; border-radius: 11px; padding: 9px 22px; cursor: pointer; box-shadow: 0 0 16px rgba(52,211,153,.35); transition: all .15s; }",
			".gdwz-cta:hover { filter: brightness(1.12); transform: translateY(-1px); box-shadow: 0 0 26px rgba(52,211,153,.55); }",
			".gdwz-cta:disabled { opacity: .4; cursor: not-allowed; transform: none; box-shadow: none; }",
			".gdwz-cta2 { border: 1px solid var(--gd-line); background: rgba(34,211,238,.07); color: var(--gd-txt); font-size: 13px; border-radius: 11px; padding: 8px 16px; cursor: pointer; transition: all .15s; }",
			".gdwz-cta2:hover { border-color: var(--gd-b); box-shadow: 0 0 14px rgba(34,211,238,.28); }",
			".gdwz-check { display: flex; gap: 8px; align-items: baseline; padding: 7px 11px; border-radius: 9px; margin-bottom: 5px; background: rgba(34,211,238,.04); border: 1px solid rgba(34,211,238,.12); }",
			".gdwz-check .ic { flex: none; font-weight: 700; }",
			".gdwz-check.ok .ic { color: var(--gd-a); text-shadow: 0 0 8px rgba(52,211,153,.5); }",
			".gdwz-check.bad .ic { color: var(--gd-err); text-shadow: 0 0 8px rgba(251,113,133,.5); }",
			".gdwz-check .nm { font-weight: 600; flex: none; color: var(--gd-txt); }",
			".gdwz-check .dt { color: var(--gd-sub); font-size: 12px; }",
			".gdwz-group { border: 1px solid rgba(34,211,238,.16); border-radius: 11px; padding: 10px 12px; margin-bottom: 10px; background: rgba(34,211,238,.03); }",
			".gdwz-group-title { font-size: 12px; font-weight: 700; color: var(--gd-sub); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; letter-spacing: .05em; font-family: var(--gd-mono); }",
			".gdwz-field { display: flex; align-items: center; gap: 10px; padding: 5px 6px; border-radius: 7px; }",
			".gdwz-field:hover { background: rgba(34,211,238,.07); }",
			".gdwz-field.chg { background: rgba(52,211,153,.1); }",
			".gdwz-fl { width: 190px; flex: none; font-size: 12.5px; color: var(--gd-sub); }",
			".gdwz-field input[type=number], .gdwz-field input[type=text], .gdwz-field select { flex: 1; min-width: 0; border: 1px solid var(--gd-line); border-radius: 7px; background: var(--gd-panel2); color: var(--gd-txt); padding: 5px 9px; font-size: 13px; font-variant-numeric: tabular-nums; font-family: var(--gd-mono); transition: all .15s; }",
			".gdwz-field input:focus { outline: none; border-color: var(--gd-b); box-shadow: 0 0 0 3px rgba(34,211,238,.18), 0 0 12px rgba(34,211,238,.25); }",
			".gdwz-field input[type=checkbox] { width: 16px; height: 16px; accent-color: #22d3ee; }",
			".gdwz-fv { flex: 1; }",
			".gdwz-old { font-size: 11px; color: var(--gd-dim); }",
			".gdwz-hl { display: flex; gap: 8px; padding: 8px 11px; border-radius: 9px; background: rgba(34,211,238,.06); border: 1px solid rgba(34,211,238,.18); margin-bottom: 6px; }",
			".gdwz-hl .ic { color: var(--gd-b); flex: none; text-shadow: 0 0 8px rgba(34,211,238,.5); }",
			".gdwz-spin { width: 26px; height: 26px; border: 3px solid rgba(34,211,238,.2); border-top-color: var(--gd-b); border-radius: 50%; animation: gdwz-rot .9s linear infinite; margin: 0 auto 12px; }",
			"@keyframes gdwz-rot { to { transform: rotate(360deg); } }",
			".gdwz-center { text-align: center; color: var(--gd-sub); padding: 34px 10px; }",
			".gdwz-center b { color: var(--gd-txt); display: block; margin: 8px 0 2px; font-size: 15px; }",
			".gdwz-note { border: 1px dashed var(--gd-line2); border-radius: 9px; padding: 10px 12px; color: var(--gd-sub); font-size: 12.5px; margin-bottom: 12px; background: rgba(34,211,238,.04); }",
			".gdwz-empty { text-align: center; padding: 40px 16px 30px; color: var(--gd-sub); }",
			".gdwz-empty .big { font-size: 30px; display: inline-block; filter: drop-shadow(0 0 16px rgba(52,211,153,.85)); animation: gdwz-float 3.2s ease-in-out infinite; }",
			".gdwz-empty b { color: var(--gd-txt); display: block; font-size: 15px; margin: 10px 0 6px; }",
			// 工作台页签激活期间隐藏基础输入框（DOM 标记 + CSS，卸载即恢复）
			"[data-composer-seat][data-gd-workbench] { display: none !important; }",
			// ── 实时对话台 ──
			".gdwz-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }",
			".gdwz-console { flex: none; display: flex; flex-direction: column; }",
			".gdwz-console.ask { border-color: rgba(251,191,36,.55); }",
			".gdwz-console.ask::before { background: linear-gradient(135deg, #fbbf24, #22d3ee); }",
			".gdwz-console-head { display: flex; align-items: center; gap: 10px; padding: 6px 12px 4px; }",
			".gdwz-console-tt { min-width: 0; flex: 1; }",
			".gdwz-console-name { font-size: 12.5px; font-weight: 700; letter-spacing: .04em; color: var(--gd-txt); }",
			".gdwz-console-sub { font-size: 10.5px; color: var(--gd-dim); font-family: var(--gd-mono); letter-spacing: .1em; }",
			".gdwz-log { max-height: 208px; min-height: 56px; overflow-y: auto; overscroll-behavior: contain; padding: 4px 12px 6px; display: flex; flex-direction: column; gap: 6px; }",
			".gdwz-log-empty { color: var(--gd-dim); font-size: 12px; padding: 8px 2px; }",
			".gdwz-msg { display: flex; gap: 8px; align-items: flex-start; }",
			".gdwz-msg-chip { flex: none; font-size: 10px; font-weight: 700; font-family: var(--gd-mono); letter-spacing: .1em; border-radius: 6px; padding: 2px 7px; margin-top: 1px; }",
			".gdwz-msg-chip.user { background: var(--gd-grad); color: #04202b; }",
			".gdwz-msg-chip.ai { color: var(--gd-a); border: 1px solid rgba(52,211,153,.55); background: rgba(52,211,153,.1); }",
			".gdwz-msg-chip.sys { color: var(--gd-sub); border: 1px dashed rgba(34,211,238,.35); }",
			".gdwz-msg-text { flex: 1; min-width: 0; font-size: 12.5px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: var(--gd-txt); }",
			".gdwz-msg.user .gdwz-msg-text { background: rgba(34,211,238,.06); border-radius: 0 10px 10px 0; padding: 3px 10px 3px 8px; border-left: 2px solid rgba(34,211,238,.65); }",
			".gdwz-msg.sys .gdwz-msg-text { color: var(--gd-sub); font-size: 12px; font-family: var(--gd-mono); }",
			".gdwz-msg.live .gdwz-msg-text::after { content: \"▍\"; color: var(--gd-a); text-shadow: 0 0 8px rgba(52,211,153,.8); animation: gdwz-caret 1s steps(1) infinite; }",
			"@keyframes gdwz-caret { 50% { opacity: 0; } }",
			".gdwz-console-input { display: flex; gap: 8px; padding: 6px 12px 10px; }",
			".gdwz-console-input input { flex: 1; min-width: 0; border: 1px solid var(--gd-line); border-radius: 10px; background: var(--gd-panel2); color: var(--gd-txt); padding: 8px 12px; font-size: 13px; transition: all .15s; }",
			".gdwz-console-input input::placeholder { color: var(--gd-dim); }",
			".gdwz-console-input input:focus { outline: none; border-color: var(--gd-b); box-shadow: 0 0 0 3px rgba(34,211,238,.18), 0 0 16px rgba(34,211,238,.3); }",
			".gdwz-console-input button { flex: none; border: none; background: var(--gd-grad); color: #04202b; border-radius: 10px; padding: 8px 18px; cursor: pointer; font-size: 13px; font-weight: 700; box-shadow: 0 0 14px rgba(52,211,153,.35); transition: all .15s; }",
			".gdwz-console-input button:hover:not(:disabled) { filter: brightness(1.12); transform: translateY(-1px); }",
			".gdwz-console-input button:disabled { opacity: .4; cursor: not-allowed; }",
			// ── 机器宠物（对话台状态化身） ──
			".gdwz-bot { position: relative; width: 30px; height: 34px; flex: none; }",
			".gdwz-bot-ant { position: absolute; top: 0; left: 50%; width: 2px; height: 7px; margin-left: -1px; background: rgba(34,211,238,.4); }",
			".gdwz-bot-ant::after { content: \"\"; position: absolute; top: -4px; left: 50%; width: 6px; height: 6px; margin-left: -3px; border-radius: 50%; background: var(--gd-sub); }",
			".gdwz-bot-head { position: absolute; top: 9px; bottom: 0; left: 2px; right: 2px; border-radius: 10px 10px 8px 8px; background: var(--gd-panel2); border: 1px solid var(--gd-line); display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: inset 0 0 10px rgba(34,211,238,.15); }",
			".gdwz-bot-eye { width: 5px; height: 5px; border-radius: 50%; background: var(--gd-b); box-shadow: 0 0 8px var(--gd-b); animation: gdwz-blink 4.5s infinite; }",
			".gdwz-bot-mouth { position: absolute; bottom: 6px; left: 50%; transform: translateX(-50%); width: 8px; height: 2px; border-radius: 1px; background: var(--gd-sub); }",
			"@keyframes gdwz-blink { 0%, 92%, 100% { transform: scaleY(1); } 95% { transform: scaleY(.1); } }",
			"@keyframes gdwz-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }",
			"@keyframes gdwz-talk { from { width: 4px; } to { width: 13px; } }",
			".gdwz-bot.idle { animation: gdwz-float 3.2s ease-in-out infinite; }",
			".gdwz-bot.think .gdwz-bot-eye { animation: gdwz-blink 1.4s infinite; }",
			".gdwz-bot.think .gdwz-bot-ant::after { background: var(--gd-warn); box-shadow: 0 0 8px rgba(251,191,36,.7); animation: gd-ring 1.2s ease-out infinite; }",
			".gdwz-bot.work .gdwz-bot-ant::after { background: var(--gd-b); box-shadow: 0 0 8px rgba(34,211,238,.8); animation: gd-ring .8s ease-out infinite; }",
			".gdwz-bot.work .gdwz-bot-head { border-color: var(--gd-line2); }",
			".gdwz-bot.speak .gdwz-bot-eye { background: var(--gd-a); box-shadow: 0 0 10px var(--gd-a); }",
			".gdwz-bot.speak .gdwz-bot-mouth { animation: gdwz-talk .5s ease-in-out infinite alternate; }",
			".gdwz-bot.ask .gdwz-bot-ant::after { background: var(--gd-warn); box-shadow: 0 0 8px rgba(251,191,36,.8); animation: gd-ring 1.6s ease-out infinite; }",
			".gdwz-bot.ask .gdwz-bot-head { border-color: rgba(251,191,36,.6); }",
			".gdwz-pet-tag { flex: none; font-size: 11px; font-weight: 700; padding: 2px 9px; border-radius: 999px; border: 1px solid var(--gd-line); color: var(--gd-sub); font-family: var(--gd-mono); letter-spacing: .06em; }",
			".gdwz-pet-tag.think { color: var(--gd-warn); border-color: rgba(251,191,36,.6); }",
			".gdwz-pet-tag.work { color: var(--gd-b); border-color: var(--gd-b); box-shadow: 0 0 12px rgba(34,211,238,.35); }",
			".gdwz-pet-tag.speak { color: var(--gd-a); border-color: rgba(52,211,153,.6); }",
			".gdwz-pet-tag.ask { color: var(--gd-warn); border-color: rgba(251,191,36,.7); animation: gdwz-caret 1.2s steps(1) infinite; }",
			// ── 挂起交互卡（提问 / 权限确认） ──
			".gdwz-qwrap { flex: none; display: flex; flex-direction: column; gap: 8px; }",
			".gdwz-q { border: 1px solid rgba(251,191,36,.5); background: linear-gradient(180deg, rgba(251,191,36,.09), transparent 40%), var(--gd-panel); border-radius: 13px; padding: 10px 14px; flex: none; box-shadow: 0 0 18px rgba(251,191,36,.16); position: relative; }",
			".gdwz-q::before { content: \"\"; position: absolute; left: 12px; right: 12px; top: 0; height: 1.5px; border-radius: 2px; background: linear-gradient(135deg, #fbbf24, #f59e0b); opacity: .8; pointer-events: none; }",
			".gdwz-q-strip { display: flex; align-items: center; gap: 8px; color: var(--gd-warn); font-size: 12.5px; font-weight: 700; margin-bottom: 4px; letter-spacing: .03em; }",
			".gdwz-q-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--gd-warn); box-shadow: 0 0 10px rgba(251,191,36,.9); animation: gdwz-caret 1.2s steps(1) infinite; flex: none; }",
			".gdwz-q-item { margin-bottom: 8px; }",
			".gdwz-q-eyebrow { color: var(--gd-dim); font-size: 11px; margin-top: 4px; font-family: var(--gd-mono); letter-spacing: .08em; }",
			".gdwz-q-question { font-size: 13.5px; font-weight: 700; margin: 2px 0 2px; color: #fff7e6; }",
			".gdwz-q-detail { font-size: 12px; color: var(--gd-sub); margin-bottom: 6px; white-space: pre-wrap; }",
			".gdwz-q-opts { display: flex; flex-direction: column; gap: 4px; }",
			".gdwz-q-opt { display: flex; align-items: flex-start; gap: 8px; text-align: left; border: 1px solid transparent; background: none; border-radius: 10px; padding: 7px 10px; cursor: pointer; color: var(--gd-txt); font-size: 13px; transition: all .15s; }",
			".gdwz-q-opt:hover:not(:disabled) { background: rgba(34,211,238,.08); border-color: var(--gd-line); }",
			".gdwz-q-opt.sel { border-color: var(--gd-b); background: rgba(34,211,238,.12); box-shadow: 0 0 14px rgba(34,211,238,.25); }",
			".gdwz-q-opt:disabled { opacity: .5; cursor: default; }",
			".gdwz-q-opt .box { flex: none; width: 16px; height: 16px; margin-top: 3px; border: 1px solid rgba(34,211,238,.4); border-radius: 50%; display: grid; place-items: center; font-size: 10px; color: var(--gd-b); }",
			".gdwz-q-opt.sel .box { border-color: var(--gd-b); box-shadow: 0 0 8px rgba(34,211,238,.6); }",
			".gdwz-q-label { font-weight: 600; }",
			".gdwz-q-desc { display: block; font-size: 12px; color: var(--gd-sub); font-weight: 400; margin-top: 1px; }",
			".gdwz-q-custom { margin-top: 6px; }",
			".gdwz-q-custom input { width: 100%; box-sizing: border-box; border: 1px solid var(--gd-line); border-radius: 9px; background: var(--gd-panel2); color: var(--gd-txt); padding: 6px 10px; font-size: 13px; transition: all .15s; }",
			".gdwz-q-custom input:focus { outline: none; border-color: var(--gd-b); box-shadow: 0 0 0 3px rgba(34,211,238,.18); }",
			".gdwz-q-skip { border: none; background: none; color: var(--gd-dim); font-size: 11.5px; cursor: pointer; padding: 2px 0; margin-top: 4px; text-decoration: underline dotted; }",
			".gdwz-q-skip:hover { color: var(--gd-sub); }",
			".gdwz-q-actions { display: flex; align-items: center; gap: 10px; margin-top: 8px; }",
			".gdwz-q-err { color: var(--gd-err); font-size: 12px; flex: 1; }",
			".gdwz-q-submit { border: none; background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #3a2a05; border-radius: 10px; padding: 7px 18px; font-size: 13px; font-weight: 700; cursor: pointer; box-shadow: 0 0 14px rgba(251,191,36,.35); }",
			".gdwz-q-submit:disabled { opacity: .4; cursor: not-allowed; }",
			".gdwz-q-hint { flex: 1; font-size: 11.5px; color: var(--gd-dim); }",
			// ── 重置流程控件（两步确认） ──
			".gdwz-reset { display: flex; align-items: center; flex: none; margin-right: 8px; }",
			".gdwz-resetwrap { display: flex; align-items: center; gap: 6px; }",
			".gdwz-resetbtn { border: 1px solid rgba(251,113,133,.45); background: rgba(251,113,133,.08); color: #fda4af; font-size: 11.5px; border-radius: 9px; padding: 3px 11px; cursor: pointer; transition: all .15s; font-family: var(--gd-mono); letter-spacing: .04em; }",
			".gdwz-resetbtn:hover { border-color: rgba(251,113,133,.75); box-shadow: 0 0 12px rgba(251,113,133,.3); }",
			".gdwz-resetq { font-size: 11.5px; color: var(--gd-err); font-weight: 700; letter-spacing: .03em; }",
			".gdwz-resetyes { border: none; background: linear-gradient(135deg, #fb7185, #f43f5e); color: #2a040c; font-size: 11.5px; font-weight: 700; border-radius: 9px; padding: 3px 11px; cursor: pointer; box-shadow: 0 0 12px rgba(251,113,133,.35); }",
			".gdwz-resetyes:disabled { opacity: .5; cursor: not-allowed; }",
			".gdwz-resetno { border: 1px solid var(--gd-line); background: none; color: var(--gd-sub); font-size: 11.5px; border-radius: 9px; padding: 3px 11px; cursor: pointer; }",
			".gdwz-resetno:hover { color: var(--gd-txt); border-color: var(--gd-line2); }",
		].join("\n");

		const STAGES = [
			{ n: 1, label: "项目解读" },
			{ n: 2, label: "数据体检" },
			{ n: 3, label: "参数确认" },
			{ n: 4, label: "求解" },
			{ n: 5, label: "校验与解读" },
		];

		/** 绿电会话一建立工作台即出现：宿主尚无向导记录（未调
		 * workbench_open）时使用这份默认态——阶段①等待项目开始。 */
		const DEFAULT_WIZARD = { open: true, stage: 1, project: "", note: "", stages: {}, updatedAt: 0 };

		const SERIES_META = [
			{ key: "load", label: "负荷", color: "#60a5fa" },
			{ key: "wind_generation", label: "风电", color: "#34d399" },
			{ key: "pv_generation", label: "光伏", color: "#fbbf24" },
			{ key: "biomass_generation", label: "生物质", color: "#a78bfa" },
			{ key: "diesel_to_load", label: "柴油", color: "#f87171" },
			{ key: "grid_to_load", label: "网购电", color: "#94a3b8" },
		];

		/** 字段显示名：键名与引擎参数库（gd template）严格对齐。 */
		const PROJECT_LABELS = {
			type: "项目类型（grid_connected 并网 / offgrid 离网）",
			loss_of_load_penalty_per_kwh: "失负荷惩罚（元/kWh）",
			max_loss_ratio_of_load: "最大失负荷率上限",
		};
		const COSTS_LABELS = {
			wind_capex_per_kw: "风电造价（元/kW）",
			pv_capex_per_kw: "光伏造价（元/kW）",
			ess_energy_capex_per_kwh: "储能能量造价（元/kWh）",
			ess_power_capex_per_kw: "储能功率造价（元/kW）",
			wind_om_per_kw_year: "风电运维（元/kW·年）",
			pv_om_per_kw_year: "光伏运维（元/kW·年）",
			ess_energy_om_per_kwh_year: "储能能量运维（元/kWh·年）",
			ess_power_om_per_kw_year: "储能功率运维（元/kW·年）",
		};
		const POLICY_LABELS = {
			min_self_use_ratio_of_load: "负荷绿电覆盖率要求",
			min_self_use_ratio_of_green: "绿电自用率要求",
			max_sell_ratio_of_green: "绿电上网比例上限",
		};
		const STORAGE_LABELS = {
			min_storage_hours: "储能时长下限（h）",
			max_storage_hours: "储能时长上限（h）",
		};

		const COMPONENT_LABELS = {
			enabled: "是否纳入",
			capex_per_kw: "单位投资（元/kW）",
			fixed_om_per_kw_year: "固定运维（元/kW·年）",
			fuel_cost_per_kwh: "燃料成本（元/kWh）",
			capacity_factor: "容量因子",
			min_output_ratio: "最小出力比例（占装机）",
			maintenance_days: "年检修天数（天）",
			max_annual_energy_kwh: "年燃料能量上限（kWh）",
			min_capacity_kw: "容量下限（kW）",
			max_capacity_kw: "容量上限（kW）",
		};

		const FINANCE_LABELS = {
			discount_rate: "折现率",
			lifecycle_years: "全寿命周期（年）",
			depreciation_years: "折旧年限（年）",
			income_tax_rate: "所得税率",
			salvage_rate: "残值率",
		};

		const BOUNDS_LABELS = {
			wind_capacity_kw_max: "风电装机上限（kW）",
			pv_capacity_kw_max: "光伏装机上限（kW）",
			ess_energy_kwh_max: "储能容量上限（kWh）",
			ess_power_kw_max: "储能功率上限（kW）",
			grid_export_kw_max: "上网功率上限（kW）",
			grid_import_kw_max: "购电功率上限（kW）",
		};

		const GROUP_TITLES = { project: "项目", solver: "求解引擎", policy: "政策要求", costs: "造价与运维", finance: "财务与税费", storage: "储能", diesel: "柴油发电机", biomass: "生物质发电", bounds: "装机边界" };

		/** 求解引擎模式：内部代号 → 对外呈现名（引擎隐藏铁律，绝不出现品牌）。 */
		const SOLVER_MODES = { default: "天枢", alternate: "天璇", dual: "双擎互证" };
		const SOLVER_MODE_DESC = {
			default: "天枢 · 主引擎：成熟稳定，速度与精度均衡（默认）",
			alternate: "天璇 · 备选引擎：独立方法实现，用于交叉复核",
			dual: "双擎互证 · 两引擎同时求解并核对目标值，最稳妥，耗时约2倍",
		};
		function solverModeDisplay(code) {
			return SOLVER_MODES[code] || String(code);
		}

		/** 宿主 RPC：connection.rpc 直连 /api 通道。 */
		function gdCall(method, args) {
			const connection = appCtx.connection;
			return connection.rpc.call("/api", "gdWorkbench/" + method, { args: args || {} }).then((result) => {
				if (!result || result.ok !== true) {
					const err = (result && result.error) || {};
					throw new Error(err.code ? err.code + ": " + err.message : "远程调用失败");
				}
				return result.value;
			});
		}

		/** 把一段文字作为用户消息提交进会话（与输入框同通道）。 */
		function sendToSession(sessionId, text) {
			try {
				const sessions = appCtx.sessions;
				const binding = sessions.binding(sessionId);
				if (binding === undefined || binding === null || !binding.session || typeof binding.session.prompt !== "function") {
					return Promise.resolve(false);
				}
				return binding.session.prompt([{ type: "text", text: text }], "queue").then((r) => !!(r && r.ok)).catch(() => false);
			} catch (e) { return Promise.resolve(false); }
		}

		function num(x) {
			const v = typeof x === "number" ? x : parseFloat(x);
			return isFinite(v) ? v : null;
		}

		function fmt(x, digits) {
			const v = num(x);
			if (v === null) return "—";
			return v.toLocaleString("zh-CN", { maximumFractionDigits: digits === undefined ? 1 : digits });
		}

		function fmtWan(x) {
			const v = num(x);
			if (v === null) return "—";
			const w = v / 10000;
			return w.toLocaleString("zh-CN", { maximumFractionDigits: 2 }) + " 万元";
		}

		function pct(x) {
			const v = num(x);
			if (v === null) return "—";
			return (v * 100).toFixed(1) + "%";
		}

		function typeText(t) {
			if (t === "offgrid") return "离网";
			if (t === "grid_connected") return "并网";
			return "";
		}

		function statusText(s) {
			if (s === "OPTIMAL") return "最优解";
			if (s === "INFEASIBLE") return "不可行（容量或燃料资源上限冲突）";
			if (s === "UNBOUNDED") return "无界";
			return s || "—";
		}

		function statusChipFor(p) {
			if (p.hasValidation && p.validationPassed) return { cls: "ok", text: "✓ 校验通过" };
			if (p.hasValidation && !p.validationPassed) return { cls: "bad", text: "校验未通过" };
			if (p.hasSolve) return { cls: "mid", text: "已求解 · 待校验" };
			if (p.hasConfig) return { cls: "mid", text: "参数已确认" };
			return { cls: "mid", text: "进行中" };
		}

		function stageReached(p) {
			if (!p) return 0;
			if (p.hasValidation) return 5;
			if (p.hasSolve) return 4;
			if (p.hasConfig) return 3;
			return 1;
		}

		function failureText(f) {
			if (!f) return "";
			if (typeof f === "string") return f;
			if (typeof f === "object") {
				let name = "";
				let msg = "";
				if (typeof f.check === "string") name = f.check;
				else if (typeof f.name === "string") name = f.name;
				if (typeof f.message === "string") msg = f.message;
				else if (typeof f.detail === "string") msg = f.detail;
				if (name || msg) return (name ? name + "：" : "") + msg;
				try { return JSON.stringify(f); } catch (e) { return String(f); }
			}
			return String(f);
		}

		//#region 通用展示组件（档案与向导共用）

		function LineChart(props) {
			const series = props.series;
			const W = 620, H = 200, L = 40, R = 12, T = 12, B = 24;
			let maxV = 0;
			for (let i = 0; i < series.length; i++) {
				for (let h = 0; h < series[i].values.length; h++) {
					if (series[i].values[h] > maxV) maxV = series[i].values[h];
				}
			}
			if (maxV <= 0) maxV = 1;
			const iw = W - L - R;
			const ih = H - T - B;
			const children = [];
			for (let g = 0; g <= 4; g++) {
				const gy = T + (ih * g) / 4;
				children.push(el("line", { key: "gl" + g, x1: L, y1: gy, x2: W - R, y2: gy, stroke: "var(--dsw-alias-border-l1)", strokeWidth: 1 }));
				children.push(el("text", { key: "gt" + g, x: L - 5, y: gy + 3, textAnchor: "end", fontSize: 9, fill: "var(--dsw-alias-label-secondary)" }, String(Math.round((maxV * (4 - g)) / 4))));
			}
			for (let h = 0; h <= 23; h += 4) {
				const x = L + (iw * h) / 23;
				children.push(el("text", { key: "hx" + h, x: x, y: H - 7, textAnchor: "middle", fontSize: 9, fill: "var(--dsw-alias-label-secondary)" }, h + "时"));
			}
			for (let i = 0; i < series.length; i++) {
				const s = series[i];
				let pts = "";
				for (let h = 0; h < s.values.length; h++) {
					const x = L + (iw * h) / 23;
					const y = T + ih - (ih * s.values[h]) / maxV;
					pts += (h > 0 ? " " : "") + x.toFixed(1) + "," + y.toFixed(1);
				}
				children.push(el("polyline", { key: "p" + s.key, points: pts, fill: "none", stroke: s.color, strokeWidth: 2, strokeLinejoin: "round", strokeLinecap: "round" }));
			}
			return el("svg", { viewBox: "0 0 " + W + " " + H, style: { width: "100%", height: "auto", display: "block" } }, children);
		}

		function Donut(props) {
			const v = Math.max(0, Math.min(1, props.value || 0));
			const r = 34;
			const c = 2 * Math.PI * r;
			return el("div", { className: "gdw-donut" },
				el("svg", { width: 80, height: 80, viewBox: "0 0 80 80" },
					el("circle", { cx: 40, cy: 40, r: r, fill: "none", stroke: "var(--dsw-alias-bg-layer-2)", strokeWidth: 9 }),
					el("circle", { cx: 40, cy: 40, r: r, fill: "none", stroke: props.color, strokeWidth: 9, strokeLinecap: "round", strokeDasharray: (c * v).toFixed(2) + " " + c.toFixed(2), transform: "rotate(-90 40 40)" }),
					el("text", { x: 40, y: 45, textAnchor: "middle", fontSize: 13, fontWeight: 700, fill: "var(--dsw-alias-label-primary)" }, pct(props.value))),
				el("div", { className: "gdw-donut-label" }, el("b", null, props.label), props.sub ? el("div", null, props.sub) : null));
		}

		function Kpi(props) {
			return el("div", { className: "gdw-kpi" },
				el("div", { className: "k" }, props.label),
				el("div", { className: "v" }, props.value),
				props.sub ? el("div", { className: "s" }, props.sub) : null);
		}

		function Cap(props) {
			const dim = !(props.value > 0);
			return el("div", { className: "gdw-cap" + (dim ? " dim" : ""), style: { borderLeftColor: props.color } },
				el("div", { className: "n" }, props.label),
				el("div", { className: "v" }, dim ? "不建设" : fmt(props.value, 1), dim ? null : el("span", { className: "u" }, " " + props.unit)),
				props.sub && !dim ? el("div", { className: "n" }, props.sub) : null);
		}

		function CostBars(props) {
			const items = props.items;
			let maxAbs = 0;
			for (let i = 0; i < items.length; i++) {
				const a = Math.abs(items[i].value || 0);
				if (a > maxAbs) maxAbs = a;
			}
			if (maxAbs <= 0) maxAbs = 1;
			const rows = [];
			for (let i = 0; i < items.length; i++) {
				const it = items[i];
				const a = Math.abs(it.value || 0);
				rows.push(el("div", { className: "gdw-bar-row", key: it.label },
					el("span", { className: "gdw-bar-label" }, it.label),
					el("div", { className: "gdw-bar-track" },
						el("div", { className: "gdw-bar-fill", style: { width: (a / maxAbs * 100).toFixed(1) + "%", background: it.color } })),
					el("span", { className: "gdw-bar-val" }, fmtWan(it.value))));
			}
			return el("div", null, rows);
		}

		function Guide(props) {
			return el("div", { className: "gdw-guide" },
				el("div", { style: { fontSize: 26 } }, props.emoji),
				el("b", null, props.title),
				el("div", { style: { marginTop: 6 } }, props.text));
		}

		function ProfileSection(props) {
			const d = props.detail;
			const p = d.project;
			const r = d.result;
			const s = d.summary || {};
			const config = d.config;
			const rows = [];
			rows.push(["项目类型", typeText(p.projectType) || "—"]);
			rows.push(["求解状态", r ? statusText(r.status) : "未求解"]);
			rows.push(["数据文件", s.input_file || "—"]);
			rows.push(["价格文件", s.price_file || "—"]);
			rows.push(["配置来源", p.configSource || "—"]);
			if (s.timestep_hours) rows.push(["时间步长", s.timestep_hours + " 小时"]);
			if (s.discount_rate !== undefined && s.discount_rate !== "") rows.push(["折现率", String(s.discount_rate)]);
			if (s.lifecycle_years) rows.push(["运营期", s.lifecycle_years + " 年"]);
			if (s.depreciation_years) rows.push(["折旧年限", s.depreciation_years + " 年"]);
			if (s.income_tax_rate !== undefined && s.income_tax_rate !== "") rows.push(["所得税率", String(s.income_tax_rate)]);
			if (s.salvage_rate !== undefined && s.salvage_rate !== "") rows.push(["残值率", String(s.salvage_rate)]);
			const kvEls = [];
			for (let i = 0; i < rows.length; i++) {
				kvEls.push(el("div", { className: "k", key: "k" + i }, rows[i][0]));
				kvEls.push(el("div", { className: "v", key: "v" + i }, rows[i][1]));
			}
			const blocks = [];
			if (config && typeof config === "object") {
				if (config.policy && typeof config.policy === "object") {
					const els = [];
					for (const k in config.policy) {
						const v = config.policy[k];
						if (v === null || typeof v === "object") continue;
						els.push(el("div", { className: "k", key: "pk" + k }, POLICY_LABELS[k] || k));
						els.push(el("div", { className: "v", key: "pv" + k }, typeof v === "boolean" ? (v ? "启用" : "停用") : String(v)));
					}
					if (els.length > 0) {
						blocks.push(el("div", { className: "gdw-panel", key: "policy" },
							el("div", { className: "gdw-panel-title" }, "政策要求"),
							el("div", { className: "gdw-kv" }, els)));
					}
				}
				const compNames = [["storage", "储能"], ["diesel", "柴油发电机"], ["biomass", "生物质发电"]];
				for (let i = 0; i < compNames.length; i++) {
					const cn = compNames[i];
					const block = config[cn[0]];
					if (!block || typeof block !== "object") continue;
					const enabled = block.enabled === true;
					const els = [el("div", { className: "k", key: "enk" }, "状态"), el("div", { className: "v", key: "env" }, enabled ? "启用" : "停用（默认）")];
					if (enabled) {
						for (const k in block) {
							if (k === "enabled") continue;
							const v = block[k];
							if (v === null || typeof v === "object") continue;
							els.push(el("div", { className: "k", key: "ck" + k }, COMPONENT_LABELS[k] || k));
							els.push(el("div", { className: "v", key: "cv" + k }, String(v)));
						}
					}
					blocks.push(el("div", { className: "gdw-panel", key: cn[0] },
						el("div", { className: "gdw-panel-title" }, cn[1]),
						el("div", { className: "gdw-kv" }, els)));
				}
			}
			return el("div", null,
				el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "项目画像"),
					el("div", { className: "gdw-kv" }, kvEls)),
				blocks);
		}

		function ResultSection(props) {
			const d = props.detail;
			const r = d.result;
			const s = d.summary || {};
			if (!r) return el(Guide, { emoji: "⏳", title: "尚未求解", text: "在聊天中完成参数确认并求解后，这里将展示装机容量、成本构成、典型日曲线与绿电指标。" });
			const caps = r.installed_capacities || {};
			const eco = r.economic_metrics || {};
			const rat = r.ratio_metrics || {};
			const tp = d.typicalDay;

			const kpis = el("div", { className: "gdw-kpis" },
				el(Kpi, { key: "npv", label: "全生命周期总成本", value: fmtWan(r.objective_value), sub: "NPV · " + (r.objective_meaning || "") }),
				el(Kpi, { key: "ld", label: "年用电总量", value: fmt(s.total_load_kwh, 0) + " kWh" }),
				el(Kpi, { key: "gr", label: "年绿电总量", value: fmt(s.total_green_generation_kwh, 0) + " kWh", sub: (num(s.total_biomass_generation_kwh) || 0) > 0 ? "含生物质 " + fmt(s.total_biomass_generation_kwh, 0) + " kWh" : null }),
				el(Kpi, { key: "cov", label: "绿电覆盖率（负荷口径）", value: pct(rat.self_use_ratio_of_load) }));

			const capList = [
				el(Cap, { key: "w", label: "风电", value: caps.wind_capacity_kw, unit: "kW", color: "#34d399" }),
				el(Cap, { key: "p", label: "光伏", value: caps.pv_capacity_kw, unit: "kW", color: "#fbbf24" }),
				el(Cap, { key: "e", label: "储能容量", value: caps.ess_energy_kwh, unit: "kWh", color: "#60a5fa", sub: caps.ess_power_kw > 0 ? "额定功率 " + fmt(caps.ess_power_kw, 1) + " kW" : null }),
				el(Cap, { key: "d", label: "柴油发电机", value: caps.diesel_capacity_kw, unit: "kW", color: "#f87171" }),
				el(Cap, { key: "b", label: "生物质", value: caps.biomass_capacity_kw, unit: "kW", color: "#a78bfa" }),
			];

			const costItems = [];
			if (eco.initial_investment_cost !== undefined) costItems.push({ label: "初始投资", value: eco.initial_investment_cost, color: "#60a5fa" });
			if (eco.om_cost_npv !== undefined) costItems.push({ label: "运维成本 NPV", value: eco.om_cost_npv, color: "#34d399" });
			if (eco.buy_cost_npv !== undefined) costItems.push({ label: "购电成本 NPV", value: eco.buy_cost_npv, color: "#94a3b8" });
			if ((eco.biomass_fuel_cost_npv || 0) > 0) costItems.push({ label: "生物质燃料 NPV", value: eco.biomass_fuel_cost_npv, color: "#a78bfa" });
			if ((eco.diesel_fuel_cost_npv || 0) > 0) costItems.push({ label: "柴油燃料 NPV", value: eco.diesel_fuel_cost_npv, color: "#f87171" });
			if ((eco.unmet_penalty_npv || 0) > 0) costItems.push({ label: "缺电惩罚 NPV", value: eco.unmet_penalty_npv, color: "#f87171" });
			if ((eco.sell_revenue_npv || 0) > 0) costItems.push({ label: "售电收益 NPV（抵减）", value: -eco.sell_revenue_npv, color: "#10b981" });

			const donuts = [];
			donuts.push(el(Donut, { key: "cov", value: rat.self_use_ratio_of_load, color: "var(--dsw-alias-brand-primary)", label: "绿电覆盖率", sub: "负荷口径" }));
			donuts.push(el(Donut, { key: "sug", value: rat.self_use_ratio_of_green, color: "#34d399", label: "绿电自用率", sub: "绿电口径" }));
			if ((rat.biomass_ratio_of_green || 0) > 0) donuts.push(el(Donut, { key: "bio", value: rat.biomass_ratio_of_green, color: "#a78bfa", label: "生物质占绿电", sub: "可调度绿电" }));
			if ((rat.diesel_ratio_of_load || 0) > 0) donuts.push(el(Donut, { key: "die", value: rat.diesel_ratio_of_load, color: "#f87171", label: "柴油兜底占比", sub: "负荷口径" }));
			if ((rat.curtail_ratio_of_green || 0) > 0) donuts.push(el(Donut, { key: "cur", value: rat.curtail_ratio_of_green, color: "#f59e0b", label: "弃电率", sub: "绿电口径" }));
			if ((rat.loss_ratio_of_load || 0) > 0) donuts.push(el(Donut, { key: "loss", value: rat.loss_ratio_of_load, color: "#ef4444", label: "失负荷率", sub: "负荷口径" }));

			let chartPanel = null;
			if (tp) {
				const shown = [];
				const legend = [];
				for (let i = 0; i < SERIES_META.length; i++) {
					const m = SERIES_META[i];
					const vals = tp[m.key];
					if (!vals) continue;
					let any = false;
					for (let h = 0; h < vals.length; h++) { if (vals[h] > 0.5) { any = true; break } }
					if (!any && m.key !== "load") continue;
					shown.push({ key: m.key, color: m.color, values: vals });
					legend.push(el("span", { className: "gdw-lg", key: m.key }, el("i", { style: { background: m.color } }), m.label));
				}
				chartPanel = el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "典型日曲线（全年 8760 小时按小时平均）"),
					el("div", { className: "gdw-legend" }, legend),
					el(LineChart, { series: shown }));
			}

			return el("div", null,
				kpis,
				el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "装机容量方案"),
					el("div", { className: "gdw-caps" }, capList)),
				el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "全生命周期成本构成（NPV）"),
					el(CostBars, { items: costItems }),
					el("div", { style: { marginTop: 8, fontSize: 12, color: "var(--gd-sub)" } }, "合计（净现值总成本）：" + fmtWan(r.objective_value))),
				donuts.length > 0 ? el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "绿电指标"),
					el("div", { className: "gdw-ratios" }, donuts)) : null,
				chartPanel);
		}

		function ValidationSection(props) {
			const d = props.detail;
			const v = d.validation;
			if (!v) return el(Guide, { emoji: "🔍", title: "尚未校验", text: "在聊天中让智能体执行后验校验后，这里将展示逐项校验结果。" });
			if (v.passed) {
				return el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-vok" }, "✓ 校验通过"),
					el("div", null, (v.passed_checks !== undefined ? v.passed_checks : "—") + " / " + (v.total_checks !== undefined ? v.total_checks : "—") + " 项通过"),
					el("div", { style: { marginTop: 8, color: "var(--gd-sub)", fontSize: 12 } }, "物理与经济一致性校验全部通过，结果可正式采信。"));
			}
			const failures = Array.isArray(v.failures) ? v.failures : [];
			const failEls = [];
			for (let i = 0; i < failures.length; i++) {
				failEls.push(el("div", { className: "gdw-fail", key: "f" + i }, failureText(failures[i])));
			}
			return el("div", { className: "gdw-panel" },
				el("div", { className: "gdw-vbad" }, "✗ 校验未通过"),
				el("div", null, "通过 " + (v.passed_checks || 0) + " / " + (v.total_checks || 0) + " 项"),
				el("div", { style: { marginTop: 10 } }, failEls));
		}

		//#endregion

		//#region 档案视图（原仪表盘，作为工作台的次级页签）

		function ArchiveView() {
			const projectsState = React.useState(null);
			const setProjects = projectsState[1];
			const projects = projectsState[0];
			const selectedState = React.useState(null);
			const selected = selectedState[0];
			const setSelected = selectedState[1];
			const detailState = React.useState(null);
			const detail = detailState[0];
			const setDetail = detailState[1];
			const loadingState = React.useState(true);
			const loading = loadingState[0];
			const setLoading = loadingState[1];
			const errorState = React.useState(null);
			const error = errorState[0];
			const setError = errorState[1];
			const sectionState = React.useState("result");
			const section = sectionState[0];
			const setSection = sectionState[1];

			function refresh() {
				gdCall("listProjects", {}).then((list) => {
					if (Array.isArray(list)) {
						setProjects(list);
						setError(null);
						setSelected((prev) => {
							if (prev !== null) {
								for (let i = 0; i < list.length; i++) { if (list[i].name === prev) return prev; }
							}
							return list.length > 0 ? list[0].name : null;
						});
					}
					setLoading(false);
				}).catch((e) => { setError(String(e && e.message ? e.message : e)); setLoading(false); });
			}

			function loadDetail(name, silent) {
				const token = ++latestDetailToken;
				if (!silent) setDetail(null);
				gdCall("getProject", { name: name }).then((res) => {
					if (token !== latestDetailToken) return;
					setDetail(res);
					if (!silent && (!res || res.error || !res.result)) setSection("profile");
				}).catch((e) => {
					if (token !== latestDetailToken) return;
					setDetail({ error: String(e && e.message ? e.message : e) });
				});
			}

			React.useEffect(() => { refresh(); }, []);

			React.useEffect(() => {
				if (selected === null) return undefined;
				loadDetail(selected, false);
				const stop = appCtx.interval(() => { refresh(); loadDetail(selected, true); }, 15000);
				return stop;
			}, [selected]);

			const list = projects || [];
			let selEntry = null;
			if (selected !== null) {
				for (let i = 0; i < list.length; i++) { if (list[i].name === selected) { selEntry = list[i]; break } }
			}

			const head = el("div", { className: "gdw-head" },
				el("div", null,
					el("div", { className: "gd-eyebrow" }, "GREEN-DIRECT · PROJECT ARCHIVE"),
					el("div", { className: "gdw-title" }, "📁 项目档案")),
				el("div", { className: "gdw-sub" }, list.length > 0 ? list.length + " 个项目 · 15 秒自动刷新" : ""),
				el("button", { className: "gdw-btn", onClick: refresh }, "⟳ 刷新"));

			if (loading) {
				return el("div", { className: "gdw-root" }, head, el("div", { className: "gdw-loading" }, "正在读取项目档案…"));
			}
			if (error !== null) {
				return el("div", { className: "gdw-root" }, head, el("div", { className: "gdw-loading" }, "读取失败：" + error));
			}
			if (list.length === 0) {
				return el("div", { className: "gdw-root" }, head,
					el(Guide, { emoji: "📁", title: "还没有项目档案", text: "完成一次求解后，产物目录会出现在这里。" }));
			}

			const cards = list.map((p) => {
				const chip = statusChipFor(p);
				return el("div", { className: "gdw-pcard" + (p.name === selected ? " sel" : ""), key: p.name, onClick: () => setSelected(p.name) },
					el("div", { className: "gdw-pcard-top" },
						el("span", { className: "gdw-pname" }, p.name),
						p.projectType ? el("span", { className: "gdw-badge " + (p.projectType === "offgrid" ? "off" : "grid") }, typeText(p.projectType)) : null),
					el("span", { className: "gdw-chip " + chip.cls }, chip.text),
					el("div", { className: "gdw-pcard-npv" }, p.objectiveValue !== null && p.objectiveValue !== undefined ? "NPV " + fmtWan(p.objectiveValue) : "—"));
			});

			let detailBody = null;
			if (detail === null) {
				detailBody = el("div", { className: "gdw-loading" }, "加载中…");
			} else if (detail.error) {
				detailBody = el("div", { className: "gdw-loading" }, String(detail.error));
			} else {
				const tabDefs = [["profile", "画像"], ["result", "结果"], ["validation", "校验"]];
				const tabs = tabDefs.map((t) => el("button", { className: "gdw-tab" + (section === t[0] ? " on" : ""), key: t[0], onClick: () => setSection(t[0]) }, t[1]));
				let content = null;
				if (section === "profile") content = el(ProfileSection, { detail: detail });
				else if (section === "validation") content = el(ValidationSection, { detail: detail });
				else content = el(ResultSection, { detail: detail });
				detailBody = el("div", { className: "gdw-detail" },
					el("div", { className: "gdw-tabs" }, tabs,
						el("span", { className: "gdw-tabs-fill" }),
						el("span", { className: "gdw-dpath" }, detail.project ? detail.project.dir : "")),
					content);
			}

			return el("div", { className: "gdw-root" }, head,
				el("div", { className: "gdw-body" },
					el("div", { className: "gdw-list" }, cards),
					detailBody));
		}

		//#endregion

		//#region 向导视图

		/** 参数字段显示名。 */
		function fieldLabel(group, key) {
			if (group === "project") return PROJECT_LABELS[key] || key;
			if (group === "solver") return key === "mode" ? "求解模式" : key;
			if (group === "costs") return COSTS_LABELS[key] || key;
			if (group === "finance") return FINANCE_LABELS[key] || key;
			if (group === "bounds") return BOUNDS_LABELS[key] || key;
			if (group === "policy") return POLICY_LABELS[key] || key;
			if (group === "storage") return STORAGE_LABELS[key] || key;
			return COMPONENT_LABELS[key] || key;
		}

		/** 参数值 → 短文本（消息里用）。 */
		function fmtValue(v) {
			if (typeof v === "boolean") return v ? "启用" : "停用";
			if (typeof v === "number") return String(v);
			return String(v);
		}

		/** 构造「参数已确认」回注消息：列出全部决策组的最终取值并标注修改项。 */
		function buildConfirmMessage(params, edits) {
			const lines = [];
			const groups = [["project", "项目"], ["solver", "求解引擎"], ["policy", "政策"], ["costs", "造价"], ["finance", "财务"], ["storage", "储能"], ["diesel", "柴油"], ["biomass", "生物质"], ["bounds", "装机边界"]];
			for (let i = 0; i < groups.length; i++) {
				const g = groups[i][0];
				const block = params[g];
				if (!block || typeof block !== "object") continue;
				const parts = [];
				for (const k in block) {
					const v = block[k];
					if (v === null || typeof v === "object") continue;
					const edited = edits[g + "." + k];
					const changed = edited !== undefined && edited !== v;
					const finalV = edited !== undefined ? edited : v;
					const valueText = g === "solver" && k === "mode" ? solverModeDisplay(finalV) : fmtValue(finalV);
					const oldText = g === "solver" && k === "mode" ? solverModeDisplay(v) : fmtValue(v);
					parts.push(fieldLabel(g, k) + "=" + valueText + (changed ? "（修改，草案 " + oldText + "）" : ""));
				}
				if (parts.length > 0) lines.push(groups[i][1] + "：" + parts.join("；"));
			}
			return "[工作台] 参数已在工作台确认。" + (lines.length > 0 ? "\n" + lines.join("\n") : "") + "\n请按以上最终取值写入 config 并开始求解。";
		}

		/** 细步进条：可点选查看已完成阶段，当前阶段呼吸动效。 */
		function Stepper(props) {
			const reached = props.current;
			const viewing = props.viewing;
			const items = [];
			for (let i = 0; i < STAGES.length; i++) {
				const st = STAGES[i];
				const state = st.n < reached ? "done" : (st.n === reached ? "active" : "");
				const viewed = st.n === viewing ? " viewed" : "";
				items.push(el("div", {
					className: "gdwz-step " + state + viewed,
					key: "s" + st.n,
					onClick: () => { if (st.n <= reached) props.onView(st.n); },
					title: st.n <= reached ? "查看该阶段" : "尚未开始",
				},
					el("span", { className: "gdwz-dot" }, st.n < reached ? "✓" : String(st.n)),
					el("span", { className: "gdwz-sl" }, st.label)));
				if (i < STAGES.length - 1) {
					items.push(el("div", { className: "gdwz-seg" + (st.n < reached ? " done" : ""), key: "l" + st.n }));
				}
			}
			return el("div", { className: "gdwz-stepper" }, items);
		}

		/** 阶段① 项目解读面板：项目画像（业务概况），数据文件属阶段②。 */
		function Stage1Panel(props) {
			const p = props.data || {};
			if (props.data === undefined || props.data === null) {
				return el("div", { className: "gdwz-empty" },
					el("span", { className: "big" }, "🌱"),
					el("b", null, "项目尚未开始 · 两种开始方式"),
					el("div", { style: { textAlign: "left", marginTop: 6 } },
						el("div", null, "① 已填好《收资清单（智能体版）》——推荐：把文件路径发给智能体，自动读取、校验并开始分析；填写值视为已确认，留空项由智能体给推荐值。"),
						el("div", { style: { marginTop: 4 } }, "② 没有清单——直接描述项目概况（并网/离网、电源组合、政策或供电要求），走问答流程。")),
					el("div", { style: { marginTop: 10, fontSize: 12, color: "var(--gd-dim)" } }, "清单模板可向智能体索取；也可以在下方对话台直接说话。"));
			}
			// 新契约：profile = [{label, value}] 业务画像清单。
			const profile = Array.isArray(p.profile) ? p.profile.filter(function (it) { return it && it.label; }) : [];
			// 旧档案兼容：老项目载荷是数据字段（dataFile/rows/loadPeak/…）。
			const legacy = !p.profile && (p.dataFile !== undefined || p.rows !== undefined);
			let body;
			if (profile.length > 0) {
				body = el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "项目画像"),
					el("div", { className: "gdw-kv" },
						profile.map(function (it, i) {
							return [
								el("span", { key: "l" + i, style: { color: "var(--gd-sub)" } }, String(it.label)),
								el("span", { key: "v" + i }, String(it.value === undefined || it.value === null ? "—" : it.value)),
							];
						}).flat()));
			} else if (legacy) {
				const priceFiles = Array.isArray(p.priceFiles) ? p.priceFiles : [];
				body = el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "数据画像 · " + (p.dataFile || "—")),
					el("div", { className: "gdw-kpis" },
						el(Kpi, { key: "rows", label: "时序行数", value: p.rows !== undefined ? fmt(p.rows, 0) : "—" }),
						el(Kpi, { key: "pk", label: "负荷峰值", value: p.loadPeak !== undefined ? fmt(p.loadPeak, 1) + " kW" : "—" }),
						el(Kpi, { key: "mn", label: "负荷均值", value: p.loadMean !== undefined ? fmt(p.loadMean, 1) + " kW" : "—" }),
						el(Kpi, { key: "pf", label: "电价文件", value: priceFiles.length > 0 ? priceFiles.join("、") : "（离网，无需）" })));
			} else {
				body = el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "项目画像"),
					el("div", { style: { color: "var(--gd-dim)", fontSize: 12 } }, "画像内容以对话为准。"));
			}
			return el("div", null,
				body,
				p.notes ? el("div", { className: "gdwz-hl" }, el("span", { className: "ic" }, "💡"), el("span", null, String(p.notes))) : null,
				props.ctas);
		}

		/** 阶段② 数据体检面板。逐项清单 + 汇总。 */
		function Stage2Panel(props) {
			const p = props.data || {};
			const checks = Array.isArray(p.checks) ? p.checks : [];
			let passCount = 0;
			const rows = checks.map((c, i) => {
				const passed = !!(c && c.passed);
				if (passed) passCount++;
				return el("div", { className: "gdwz-check " + (passed ? "ok" : "bad"), key: "c" + i },
					el("span", { className: "ic" }, passed ? "✓" : "✗"),
					el("span", { className: "nm" }, String((c && c.name) || "检查项")),
					el("span", { className: "dt" }, String((c && c.detail) || "")));
			});
			return el("div", null,
				el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "体检清单 · " + passCount + " / " + checks.length + " 项通过"),
					rows.length > 0 ? rows : el("div", { className: "gdw-loading" }, "等待智能体推送体检结果…")),
				p.notes ? el("div", { className: "gdwz-hl" }, el("span", { className: "ic" }, "💡"), el("span", null, String(p.notes))) : null,
				props.ctas);
		}

		/** 阶段③ 参数确认面板：就地可编辑。 */
		function Stage3Panel(props) {
			const p = props.data || {};
			const params = p.params && typeof p.params === "object" ? p.params : {};
			const edits = props.edits;
			const setEdits = props.setEdits;
			const groupKeys = ["project", "solver", "policy", "costs", "finance", "storage", "diesel", "biomass", "bounds"];
			const groups = [];
			for (let gi = 0; gi < groupKeys.length; gi++) {
				const g = groupKeys[gi];
				const block = params[g];
				if (!block || typeof block !== "object") continue;
				const fields = [];
				for (const k in block) {
					const v = block[k];
					if (v === null || typeof v === "object") continue;
					const fk = g + "." + k;
					const isBool = typeof v === "boolean";
					const isNum = typeof v === "number";
					const edited = edits[fk];
					const changed = edited !== undefined && edited !== v;
					const shown = edited !== undefined ? edited : v;
					let input;
					if (g === "solver" && k === "mode") {
						// 求解模式：三选一下拉（代号存值、呈现名显示），下方随选说明。
						const modeKeys = ["default", "alternate", "dual"];
						const current = modeKeys.indexOf(shown) >= 0 ? shown : "default";
						input = el("select", {
							value: current,
							onChange: (e) => setEdits(Object.assign({}, edits, { [fk]: e.target.value })),
						},
							modeKeys.map((m) => el("option", { key: m, value: m }, solverModeDisplay(m))));
						fields.push(el("div", { key: fk },
							el("div", { className: "gdwz-field" },
								el("span", { className: "gdwz-fl" }, fieldLabel(g, k)),
								el("div", { className: "gdwz-fv" }, input),
								changed ? el("span", { className: "gdwz-old" }, "草案 " + solverModeDisplay(v)) : null),
							el("div", { style: { fontSize: 11.5, color: "var(--dsw-alias-label-secondary)", padding: "0 4px 6px" } }, SOLVER_MODE_DESC[current] || "")));
						continue;
					}
					input = isBool
						? el("input", { type: "checkbox", checked: shown === true, onChange: (e) => setEdits(Object.assign({}, edits, { [fk]: e.target.checked })) })
						: el("input", {
							type: isNum ? "number" : "text",
							value: shown === undefined || shown === null ? "" : String(shown),
							step: "any",
							onChange: (e) => {
								const raw = e.target.value;
								let next = raw;
								if (isNum) {
									const parsed = parseFloat(raw);
									next = isFinite(parsed) ? parsed : raw;
								}
								setEdits(Object.assign({}, edits, { [fk]: next }));
							},
						});
					fields.push(el("div", { className: "gdwz-field" + (changed ? " chg" : ""), key: fk },
						el("span", { className: "gdwz-fl" }, fieldLabel(g, k)),
						el("div", { className: "gdwz-fv" }, input),
						changed ? el("span", { className: "gdwz-old" }, "草案 " + fmtValue(v)) : null));
				}
				if (fields.length > 0) {
					groups.push(el("div", { className: "gdwz-group", key: g },
						el("div", { className: "gdwz-group-title" }, "▸ " + (GROUP_TITLES[g] || g)),
						fields));
				}
			}
			if (groups.length === 0) {
				return el("div", { className: "gdwz-center" },
					el("div", { className: "gdwz-spin" }),
					el("b", null, "等待智能体推送参数草案…"),
					el("div", null, "草案就绪后会出现在这里，可直接编辑或交给聊天讨论。"));
			}
			const editCount = Object.keys(edits).length;
			return el("div", null,
				el("div", { style: { fontSize: 12, color: "var(--gd-sub)", margin: "2px 0 10px" } },
					"逐项核对并直接修改取值（修改处高亮）。确认后点击「确认参数并求解」，也可在下方对话台向智能体提问。"),
				groups,
				p.notes ? el("div", { className: "gdwz-hl" }, el("span", { className: "ic" }, "💡"), el("span", null, String(p.notes))) : null,
				props.ctas,
				editCount > 0 ? el("div", { style: { marginTop: 8, fontSize: 12, color: "var(--gd-b)" } }, "已修改 " + editCount + " 项，未修改项按草案取值。") : null);
		}

		/** 阶段④ 求解面板：running / failed / done（done 复用结果仪表盘）。 */
		function Stage4Panel(props) {
			const p = props.data || {};
			if (p.status === "running" || (!p.status && !props.detail)) {
				return el("div", { className: "gdwz-center" },
					el("div", { className: "gdwz-spin" }),
					el("b", null, "内置优化求解引擎计算中…"),
					el("div", null, "通常需要数十秒到几分钟，进度与结论由智能体在聊天中同步。"));
			}
			if (p.status === "failed") {
				return el("div", null,
					el("div", { className: "gdw-panel" },
						el("div", { className: "gdw-vbad" }, "✗ 求解失败"),
						el("div", null, String(p.error || "原因见聊天，智能体会给出修改建议。"))),
					props.ctas);
			}
			if (props.detail && !props.detail.error) {
				return el("div", null,
					el(ResultSection, { detail: props.detail }),
					props.ctas);
			}
			if (props.failed) {
				return el("div", null,
					el("div", { className: "gdwz-note" }, "求解已报告完成，但工作台按已知项目名未能读取到结果明细（档案目录与项目名对不上）。结论与数值请以智能体在聊天中的报告为准。"),
					props.ctas);
			}
			return el("div", { className: "gdwz-center" },
				el("div", { className: "gdwz-spin" }),
				el("b", null, "求解完成，正在读取结果…"));
		}

		/** 阶段⑤ 校验与解读面板：校验清单 + 解读要点 + 采纳/重算。 */
		function Stage5Panel(props) {
			const p = props.data || {};
			const highlights = Array.isArray(p.highlights) ? p.highlights : [];
			const hlEls = highlights.map((h, i) => el("div", { className: "gdwz-hl", key: "h" + i }, el("span", { className: "ic" }, "◆"), el("span", null, String(h))));
			let validation = null;
			if (props.detail && !props.detail.error) validation = el(ValidationSection, { detail: props.detail });
			else if (props.failed) validation = el("div", { className: "gdwz-note" }, "校验明细读取失败（项目名与档案目录未对上）。校验结论请以智能体在聊天中的报告为准。");
			return el("div", null,
				validation !== null ? validation : el("div", { className: "gdwz-center" }, el("div", { className: "gdwz-spin" }), el("b", null, "正在读取校验报告…")),
				highlights.length > 0 ? el("div", { className: "gdw-panel" },
					el("div", { className: "gdw-panel-title" }, "解读要点"),
					hlEls) : null,
				props.ctas);
		}

		/** 机器宠物：把与智能体的对话实时反馈进工作台。
		 * 数据来自会话快照钩子 useSession（conversation.view 框架注入）：
		 * 运行状态、流式输出、执行中的工具、最近一问一答。
		 * 注意块字段：助手侧（partial 与最终消息）是 UI 分类块 kind:"text"，
		 * 用户侧 content 是核心块 type:"text" —— 两者都认。 */
		function blocksTextOf(blocks) {
			if (!Array.isArray(blocks)) return "";
			let out = "";
			for (let i = 0; i < blocks.length; i++) {
				const b = blocks[i];
				if (b && typeof b.text === "string" && (b.kind === "text" || b.type === "text")) out += b.text;
			}
			return out.replace(/\s+/g, " ").trim();
		}

		function tailOf(text, n) {
			if (typeof text !== "string" || text.length <= n) return text || "";
			return "…" + text.slice(text.length - n);
		}

		/** 从快照节点里倒序找最近一条用户/助手文本。 */
		function latestNodeText(nodes, kinds, field) {
			if (!Array.isArray(nodes)) return "";
			for (let i = nodes.length - 1; i >= 0; i--) {
				const n = nodes[i];
				if (n && kinds.indexOf(n.kind) >= 0) {
					const t = blocksTextOf(n[field]);
					if (t !== "") return t;
				}
			}
			return "";
		}

		/** 内部会话快照订阅：直接绑定 Session（ObservableSnapshot：
		 * subscribe/getSnapshot），不依赖框架注入 props——发送消息用的就是
		 * 同一个 binding，数据路径确定。 */
		function useSessionSnapshot(sessionId) {
			const session = React.useMemo(() => {
				try {
					const binding = appCtx.sessions.binding(sessionId);
					return binding && binding.session ? binding.session : null;
				} catch (e) { return null; }
			}, [sessionId]);
			const subscribe = React.useMemo(() => session ? (fn) => session.subscribe(fn) : () => () => {}, [session]);
			const getSnapshot = React.useMemo(() => session ? () => session.getSnapshot() : () => null, [session]);
			return React.useSyncExternalStore(subscribe, getSnapshot);
		}

		/** 实时对话台：与智能体的对话完整呈现在工作台底部（无需点击
		 * 展开），流式输出实时滚动；机器宠物是它的状态化身；底部内嵌
		 * 指令输入行。数据来自 useSessionSnapshot（内部会话绑定）。 */
		function LiveConsole(props) {
			const sessionId = props.sessionId;
			const snap = useSessionSnapshot(sessionId);
			const running = !!(snap && snap.running);
			const legacy = snap && snap.chat ? snap.chat.legacy : null;
			const streaming = legacy && legacy.partial && Array.isArray(legacy.partial.blocks) ? blocksTextOf(legacy.partial.blocks) : "";
			const calls = legacy ? legacy.runningCalls : null;
			let toolName = "";
			if (Array.isArray(calls) && calls.length > 0) {
				const c = calls[calls.length - 1];
				if (c && typeof c.name === "string") toolName = c.name;
			}
			const pendingQuestion = !!(snap && Array.isArray(snap.pending) && snap.pending.some((w) => w && w.kind === "question"));

			// 转录行：最近 40 个节点里的用户/助手文本（全文，滚动查看）。
			const rows = [];
			const nodes = legacy ? legacy.nodes : null;
			if (Array.isArray(nodes)) {
				for (let i = Math.max(0, nodes.length - 40); i < nodes.length; i++) {
					const n = nodes[i];
					if (!n) continue;
					if (n.kind === "user" || n.kind === "steering") {
						const t = blocksTextOf(n.content);
						if (t !== "") rows.push({ role: "user", text: t });
					} else if (n.kind === "assistant") {
						const t = blocksTextOf(n.blocks);
						if (t !== "") rows.push({ role: "ai", text: t });
					}
				}
			}
			while (rows.length > 30) rows.shift();
			// 排队中的消息（智能体回合进行中发出的指令会先进入会话队列）。
			const queue = snap && Array.isArray(snap.queue) ? snap.queue : [];

			const mode = pendingQuestion ? "ask" : toolName !== "" ? "work" : (streaming !== "" ? "speak" : (running ? "think" : "idle"));
			const tagText = mode === "ask" ? "等回答" : mode === "work" ? "执行中" : mode === "speak" ? "回复中" : mode === "think" ? "思考中" : "待命";

			// 新内容（新行或流式增量）到达时自动滚到底部。
			const logRef = React.useRef(null);
			React.useEffect(() => {
				const node = logRef.current;
				if (node !== null) node.scrollTop = node.scrollHeight;
			}, [rows.length, streaming, queue.length]);

			// 指令输入行：与聊天输入同通道提交。
			const textState = React.useState("");
			const text = textState[0];
			const setText = textState[1];
			const busyState = React.useState(false);
			const busy = busyState[0];
			const setBusy = busyState[1];
			function submitText() {
				const t = text.trim();
				if (t === "" || busy) return;
				setText("");
				setBusy(true);
				sendToSession(sessionId, "[工作台] " + t).then(() => { setBusy(false); });
			}

			const rowEls = rows.map((r, i) => el("div", { className: "gdwz-msg " + r.role, key: "m" + i },
				el("span", { className: "gdwz-msg-chip " + r.role }, r.role === "user" ? "你" : "AI"),
				el("div", { className: "gdwz-msg-text" }, r.text)));
			if (mode === "work") rowEls.push(el("div", { className: "gdwz-msg sys", key: "sys-work" },
				el("span", { className: "gdwz-msg-chip sys" }, "⚙"),
				el("div", { className: "gdwz-msg-text" }, "正在执行 " + toolName + " …")));
			else if (mode === "think") rowEls.push(el("div", { className: "gdwz-msg sys", key: "sys-think" },
				el("span", { className: "gdwz-msg-chip sys" }, "…"),
				el("div", { className: "gdwz-msg-text" }, "正在思考…")));
			else if (mode === "ask") rowEls.push(el("div", { className: "gdwz-msg sys", key: "sys-ask" },
				el("span", { className: "gdwz-msg-chip sys" }, "?"),
				el("div", { className: "gdwz-msg-text" }, "智能体在等你的回答（见上方问题卡）…")));
			if (streaming !== "") rowEls.push(el("div", { className: "gdwz-msg ai live", key: "live" },
				el("span", { className: "gdwz-msg-chip ai" }, "AI"),
				el("div", { className: "gdwz-msg-text" }, streaming)));
			// 排队中的消息显式呈现，让用户知道消息已送达、将在当前回合结束后处理。
			for (let i = 0; i < queue.length; i++) {
				const q = queue[i];
				const t = q && typeof q.text === "string" && q.text !== "" ? q.text : (q && typeof q.preview === "string" ? q.preview : "");
				if (t === "") continue;
				rowEls.push(el("div", { className: "gdwz-msg sys", key: "qu" + i },
					el("span", { className: "gdwz-msg-chip sys" }, "⏳"),
					el("div", { className: "gdwz-msg-text" }, t + "（排队中，智能体当前回合结束后送达）")));
			}

			return el("div", { className: "gdwz-console gd-card" + (mode === "ask" ? " ask" : "") },
				el("div", { className: "gdwz-console-head" },
					el("div", { className: "gdwz-bot " + mode, "aria-hidden": true },
						el("div", { className: "gdwz-bot-ant" }),
						el("div", { className: "gdwz-bot-head" },
							el("span", { className: "gdwz-bot-eye" }),
							el("span", { className: "gdwz-bot-eye" }),
							el("span", { className: "gdwz-bot-mouth" }))),
					el("div", { className: "gdwz-console-tt" },
						el("div", { className: "gdwz-console-name" }, "实时对话"),
						el("div", { className: "gdwz-console-sub" }, "LIVE · 与智能体全程同步")),
					el("span", { className: "gdwz-pet-tag " + mode }, tagText)),
				el("div", { className: "gdwz-log", ref: logRef },
					rowEls.length === 0
						? el("div", { className: "gdwz-log-empty" }, "我在这里。把数据文件路径或项目需求发给我——也可以直接在下面输入。")
						: rowEls),
				el("div", { className: "gdwz-console-input" },
					el("input", {
						placeholder: "问点什么，或直接下指令（发给智能体）…",
						value: text,
						onChange: (e) => setText(e.target.value),
						onKeyDown: (e) => { if (e.key === "Enter") { e.preventDefault(); submitText(); } },
					}),
					el("button", { disabled: busy || text.trim() === "", onClick: submitText }, busy ? "发送中…" : "发送")));
		}

		/** 挂起交互卡：把智能体的提问（ask_user_question）与权限确认
		 * 镜像进工作台。聊天里的这两类卡片渲染在 composer 座位上，而
		 * 工作台激活期间该座位被隐藏——不镜像用户就没法作答。
		 * 载体来自会话快照 pending 列表（PendingWait），应答走官方
		 * wait.respond 协议（ok/壳 + sessionId + 领域载荷）。 */
		function PendingInteractions(props) {
			const snap = useSessionSnapshot(props.sessionId);
			const pending = snap && Array.isArray(snap.pending) ? snap.pending : [];
			const cards = [];
			for (let i = 0; i < pending.length; i++) {
				const w = pending[i];
				if (!w || typeof w.respond !== "function" || !w.payload) continue;
				if (w.kind === "approval") cards.push(el(ApprovalCard, { key: w.key, wait: w }));
				else if (w.kind === "question") cards.push(el(QuestionCard, { key: w.key, wait: w }));
			}
			if (cards.length === 0) return null;
			return el("div", { className: "gdwz-qwrap" }, cards);
		}

		/** 权限确认卡：允许一次 / 拒绝。 */
		function ApprovalCard(props) {
			const wait = props.wait;
			const payload = wait.payload || {};
			const answeredState = React.useState(false);
			const answered = answeredState[0];
			const setAnswered = answeredState[1];

			function decide(outcome) {
				setAnswered(true);
				wait.respond({
					ok: true,
					value: { sessionId: wait.sessionId, approvalId: payload.approvalId, outcome: outcome },
				}).then((receipt) => {
					if (!receipt || receipt.accepted !== true) setAnswered(false);
				}).catch(() => { setAnswered(false); });
			}

			return el("div", { className: "gdwz-q" },
				el("div", { className: "gdwz-q-strip" },
					el("span", { className: "gdwz-q-dot" }),
					"权限确认" + (payload.toolName ? " · " + payload.toolName : "")),
				el("div", { className: "gdwz-q-detail" }, String(payload.reason || "智能体请求执行一个需要确认的操作。")),
				el("div", { className: "gdwz-q-actions" },
					el("button", { className: "gdwz-cta2", disabled: answered, onClick: () => decide("rejected") }, "拒绝"),
					el("button", { className: "gdwz-cta", disabled: answered, onClick: () => decide("allowed-once") }, "允许一次")));
		}

		/** 提问卡：选项点选 / 多选 / 自定义文本 / 跳过，批量提交。
		 * 单问题单选批次点击选项立即提交（最常见的确认场景）。 */
		function QuestionCard(props) {
			const wait = props.wait;
			const questions = wait.payload && Array.isArray(wait.payload.questions) ? wait.payload.questions : [];
			const draftsState = React.useState(() => questions.map(() => ({ selected: [], custom: "", skipped: false })));
			const drafts = draftsState[0];
			const setDrafts = draftsState[1];
			const busyState = React.useState(false);
			const busy = busyState[0];
			const setBusy = busyState[1];
			const errState = React.useState(null);
			const err = errState[0];
			const setErr = errState[1];

			const singleQuick = questions.length === 1 && questions[0].multiSelect !== true && (Array.isArray(questions[0].options) && questions[0].options.length > 0);

			function submit(values) {
				const answers = questions.map((q, i) => {
					const v = values[i];
					if (v.skipped) return { id: q.id, selected: [] };
					const custom = (v.custom || "").trim();
					return {
						id: q.id,
						selected: custom === "" || q.multiSelect === true ? v.selected : [],
						...(custom === "" ? {} : { custom: custom }),
					};
				});
				setBusy(true);
				setErr(null);
				wait.respond({
					ok: true,
					value: { sessionId: wait.sessionId, answer: { answers: answers } },
				}).then((receipt) => {
					if (!receipt || receipt.accepted !== true) {
						setBusy(false);
						setErr(!receipt || !receipt.reason ? "回答未被接受" : String(receipt.reason));
					}
				}).catch((e) => {
					setBusy(false);
					setErr(e && e.message ? e.message : String(e));
				});
			}

			const parts = [];
			for (let qi = 0; qi < questions.length; qi++) {
				const q = questions[qi];
				const multi = q.multiSelect === true;
				const opts = Array.isArray(q.options) ? q.options : [];
				const draft = drafts[qi];
				const optEls = opts.map((o, oi) => {
					const label = typeof o === "string" ? o : String(o && o.label !== undefined ? o.label : oi);
					const desc = o && typeof o === "object" && typeof o.description === "string" ? o.description : "";
					const sel = draft.selected.indexOf(label) >= 0;
					return el("button", {
						className: "gdwz-q-opt" + (sel ? " sel" : ""),
						key: "o" + oi,
						disabled: busy || draft.skipped,
						onClick: () => {
							if (singleQuick) { submit([{ selected: [label], custom: "", skipped: false }]); return; }
							setDrafts(drafts.map((d, di) => di !== qi ? d : (multi
								? { ...d, selected: sel ? d.selected.filter((x) => x !== label) : [...d.selected, label], skipped: false }
								: { selected: [label], custom: "", skipped: false })));
							setErr(null);
						},
					},
						el("span", { className: "box" }, multi ? (sel ? "✓" : "") : (sel ? "●" : "")),
						el("span", { className: "gdwz-q-label" }, label, desc !== "" ? el("span", { className: "gdwz-q-desc" }, desc) : null));
				});
				parts.push(el("div", { className: "gdwz-q-item", key: "q" + qi },
					q.header ? el("div", { className: "gdwz-q-eyebrow" }, String(q.header)) : null,
					el("div", { className: "gdwz-q-question" }, String(q.question || "")),
					q.detail ? el("div", { className: "gdwz-q-detail" }, String(q.detail)) : null,
					optEls.length > 0 ? el("div", { className: "gdwz-q-opts" }, optEls) : null,
					el("div", { className: "gdwz-q-custom" },
						el("input", {
							placeholder: opts.length > 0 ? "或输入自定义回答（可选）…" : "输入你的回答…",
							value: draft.custom,
							disabled: busy || draft.skipped,
							onChange: (e) => setDrafts(drafts.map((d, di) => di !== qi ? d : { ...d, custom: e.target.value, skipped: false })),
							onKeyDown: (e) => {
								if (e.key === "Enter") {
									e.preventDefault();
									if ((draft.custom || "").trim() !== "") submit(drafts.map((d, di) => di !== qi ? d : { ...d, skipped: false }));
								}
							},
						})),
					el("button", {
						className: "gdwz-q-skip",
						disabled: busy,
						onClick: () => setDrafts(drafts.map((d, di) => di !== qi ? d : { ...d, skipped: !d.skipped })),
					}, draft.skipped ? "已跳过（点击恢复）" : "跳过此问")));
			}

			const completed = drafts.every((d) => d.selected.length > 0 || (d.custom || "").trim() !== "" || d.skipped);
			return el("div", { className: "gdwz-q" },
				el("div", { className: "gdwz-q-strip" },
					el("span", { className: "gdwz-q-dot" }),
					"智能体提问" + (questions.length > 1 ? " · " + questions.length + " 个问题" : "")),
				parts,
				!singleQuick ? el("div", { className: "gdwz-q-actions" },
					el("div", { className: "gdwz-q-err" }, err !== null ? err : (completed ? "" : "还有未回答的问题")),
					el("button", { className: "gdwz-q-submit", disabled: busy || !completed, onClick: () => submit(drafts) }, busy ? "提交中…" : "提交回答")) : null,
				singleQuick ? el("div", { className: "gdwz-q-actions" },
					el("div", { className: "gdwz-q-err" }, err !== null ? err : ""),
					el("span", { className: "gdwz-q-hint" }, "点击选项即回答；也可在输入框自定义后回车。")) : null);
		}

		/** 向导主体。 */
		function WizardView(props) {
			const sessionId = props.sessionId;
			const wizardState = React.useState(DEFAULT_WIZARD);
			const wizard = wizardState[0];
			const setWizard = wizardState[1];
			const viewStageState = React.useState(1);
			const viewStage = viewStageState[0];
			const setViewStage = viewStageState[1];
			const editsState = React.useState({});
			const edits = editsState[0];
			const setEdits = editsState[1];
			const modeState = React.useState("guide");
			const mode = modeState[0];
			const setMode = modeState[1];
			const detailState = React.useState(null);
			const detail = detailState[0];
			const setDetail = detailState[1];
			const detailFailedState = React.useState(false);
			const detailFailed = detailFailedState[0];
			const setDetailFailed = detailFailedState[1];
			const rootRef = React.useRef(null);
			const sendingState = React.useState(false);
			const sending = sendingState[0];
			const setSending = sendingState[1];
			// 重置流程：两步确认（先点亮再确认），确认后清空宿主侧向导
			// 状态并回到阶段①空态；磁盘产物与档案不受影响。
			const resetArmedState = React.useState(false);
			const resetArmed = resetArmedState[0];
			const setResetArmed = resetArmedState[1];
			const resettingState = React.useState(false);
			const resetting = resettingState[0];
			const setResetting = resettingState[1];

			function doReset() {
				setResetting(true);
				gdCall("resetWizard", { sessionId: sessionId }).then(() => {
					setWizard(DEFAULT_WIZARD);
					setEdits({});
					setViewStage(1);
					setDetail(null);
					setDetailFailed(false);
					setResetArmed(false);
					setResetting(false);
					sendToSession(sessionId, "[工作台] 流程已重置：当前项目的工作台状态已清空，回到阶段①待命。开始新项目请直接描述，继续旧项目请说明。");
				}).catch(() => { setResetting(false); setResetArmed(false); });
			}

			// 点亮确认态 6 秒无操作自动收回。
			React.useEffect(() => {
				if (!resetArmed) return undefined;
				const stop = appCtx.setTimeout(() => setResetArmed(false), 6000);
				return () => { if (typeof stop === "function") { try { stop(); } catch (e) { /* 忽略 */ } } };
			}, [resetArmed]);

			// 工作台页签激活期间隐藏基础输入框：从自身 DOM 向上找到
			// 会话滚动容器里的 composer 座位（稳定属性锚点），打标记 + CSS 隐藏。
			// 卸载（切回聊天页签 / 换会话）时移除标记即恢复；composer 本体保持
			// 挂载，草稿与输入状态不丢。
			React.useEffect(() => {
				const root = rootRef.current;
				if (root === null || typeof root.closest !== "function") return undefined;
				const scrollBody = root.closest("[data-conversation-scroll]");
				const seat = scrollBody !== null ? scrollBody.querySelector("[data-composer-seat]") : null;
				if (seat === null) return undefined;
				seat.setAttribute("data-gd-workbench", "");
				return () => { try { seat.removeAttribute("data-gd-workbench"); } catch (e) { /* 已卸载则忽略 */ } };
			}, []);

			// 向导状态轮询（2 秒）。
			React.useEffect(() => {
				let alive = true;
				function poll() {
					gdCall("wizardState", { sessionId: sessionId }).then((s) => {
						if (!alive) return;
						setWizard(s || DEFAULT_WIZARD);
					}).catch(() => { /* 轮询失败静默保留旧状态 */ });
				}
				poll();
				const stop = appCtx.interval(poll, 2000);
				return () => { alive = false; stop(); };
			}, [sessionId]);

			// 阶段 ≥4 时拉取结果详情。项目名候选链：当前向导记录的 project →
			// 阶段④载荷的 project → 阶段⑤载荷的 project（智能体可能在阶段⑤
			// 误报项目名，此时回退阶段④的输出目录名）；15 秒兜底刷新。
			const projectName = wizard && wizard.project ? wizard.project : "";
			const stageNum = wizard ? wizard.stage : 0;
			const stage4 = wizard && wizard.stages ? wizard.stages["4"] : null;
			const stage5 = wizard && wizard.stages ? wizard.stages["5"] : null;
			const candidatesKey = [projectName,
				stage4 && typeof stage4.project === "string" ? stage4.project : "",
				stage5 && typeof stage5.project === "string" ? stage5.project : "",
			].filter((x, i, a) => x !== "" && a.indexOf(x) === i).join("|");
			const needDetail = stageNum >= 4 && candidatesKey !== "";
			React.useEffect(() => {
				if (!needDetail) { setDetail(null); setDetailFailed(false); return undefined; }
				let token = 0;
				const names = candidatesKey.split("|");
				function fetchDetail() {
					const t = ++token;
					(async () => {
						for (let i = 0; i < names.length; i++) {
							try {
								const res = await gdCall("getProject", { name: names[i] });
								if (t !== token) return;
								if (res && !res.error) { setDetail(res); setDetailFailed(false); return; }
							} catch (e) { /* 尝试下一个候选名 */ }
						}
						if (t !== token) return;
						setDetailFailed(true);
					})();
				}
				fetchDetail();
				const stop = appCtx.interval(fetchDetail, 15000);
				return () => { token++; stop(); };
			}, [needDetail, candidatesKey]);

			// 阶段推进时自动跟随到最新阶段（用户没在回看旧阶段时）。
			React.useEffect(() => {
				if (wizard && wizard.stage) setViewStage(wizard.stage);
			}, [wizard && wizard.stage]);

			function send(text) {
				setSending(true);
				sendToSession(sessionId, text).then(() => { setSending(false); });
			}

			// 重置按钮常显（空白状态下重置是无害的空操作），
			// 保证入口始终可发现。
			const resetCtl = el("div", { className: "gdwz-reset" },
				resetArmed
					? el("span", { className: "gdwz-resetwrap" },
						el("span", { className: "gdwz-resetq" }, "清空当前流程？"),
						el("button", { className: "gdwz-resetyes", disabled: resetting, onClick: doReset }, resetting ? "重置中…" : "确认重置"),
						el("button", { className: "gdwz-resetno", onClick: () => setResetArmed(false) }, "取消"))
					: el("button", {
						className: "gdwz-resetbtn",
						title: "清空当前项目的工作台流程，回到阶段①（磁盘产物与档案库不受影响）",
						onClick: () => setResetArmed(true),
					}, "↺ 重置流程"));

			const head = el("div", { className: "gdwz-head" },
				el("div", { className: "gdwz-headL" },
					el("div", { className: "gd-eyebrow" }, "GREEN-DIRECT · OPTIMIZATION WORKBENCH"),
					el("div", { className: "gdwz-title" },
						el("span", { className: "leaf" }, "🌱"),
						"项目向导",
						projectName !== "" ? el("span", { className: "gdwz-proj", title: projectName }, projectName) : null),
					el("div", { className: "gdwz-sub" }, wizard && wizard.note ? wizard.note : "五阶段流程 · 由智能体驱动")),
				resetCtl,
				el("div", { className: "gdwz-modes" },
					el("button", { className: "gdwz-mode" + (mode === "guide" ? " on" : ""), onClick: () => setMode("guide") }, "向导"),
					el("button", { className: "gdwz-mode" + (mode === "archive" ? " on" : ""), onClick: () => setMode("archive") }, "档案")));

			// 底栏：挂起交互卡（提问/确认，聊天 composer 隐藏期间的应答入口）
			// + 实时对话台（完整对话展示 + 流式 + 指令输入），向导/档案两态共用。
			const interactions = el(PendingInteractions, { sessionId: sessionId });
			const consoleBar = el(LiveConsole, { sessionId: sessionId });

			if (mode === "archive") {
				return el("div", { className: "gdwz-root", ref: rootRef }, head,
					el("div", { className: "gdwz-body" }, el(ArchiveView, null)),
					interactions, consoleBar);
			}

			const reached = wizard.stage || 1;
			const stages = wizard.stages || {};

			// 智能体已推进到新阶段而用户在回看旧阶段：提示跳转。
			const jumpBar = viewStage < reached
				? el("div", { className: "gdwz-jump" },
					el("span", null, "智能体已推进到「" + (STAGES[reached - 1] ? STAGES[reached - 1].label : "") + "」"),
					el("button", { className: "gdwz-cta2", onClick: () => setViewStage(reached) }, "跳转跟随 →"))
				: null;

			// 各阶段 CTA（只跟随当前最新阶段；阶段①须画像已推送才出现；
			// 交流入口是底部对话台，不再放「在聊天中提问」辅助按钮）。
			let ctas = null;
			if (viewStage === reached) {
				if (reached === 1 && stages["1"]) {
					ctas = el("div", { className: "gdwz-cta-row" },
						el("button", { className: "gdwz-cta", disabled: sending, onClick: () => send("[工作台] 请开始数据体检。") }, "开始数据体检 →"));
				} else if (reached === 2) {
					ctas = el("div", { className: "gdwz-cta-row" },
						el("button", { className: "gdwz-cta", disabled: sending, onClick: () => send("[工作台] 数据体检已确认，请进入参数确认阶段并给出参数草案。") }, "体检确认，去定参数 →"));
				} else if (reached === 3) {
					ctas = el("div", { className: "gdwz-cta-row" },
						el("button", { className: "gdwz-cta", disabled: sending, onClick: () => send(buildConfirmMessage(stages["3"] && stages["3"].params ? stages["3"].params : {}, edits)) }, "确认参数并求解"));
				} else if (reached === 4) {
					const status = stages["4"] && stages["4"].status;
					if (status === "done") {
						ctas = el("div", { className: "gdwz-cta-row" },
							el("button", { className: "gdwz-cta", disabled: sending, onClick: () => send("[工作台] 请执行校验并给出解读报告。") }, "执行校验与解读 →"));
					}
				} else if (reached === 5) {
					ctas = el("div", { className: "gdwz-cta-row" },
						el("button", { className: "gdwz-cta", disabled: sending, onClick: () => send("[工作台] 采纳当前方案，请整理最终交付说明与结果文件引用。") }, "采纳方案"),
						el("button", { className: "gdwz-cta2", disabled: sending, onClick: () => { setViewStage(3); gdCall("restoreStage", { sessionId: sessionId, stage: 3 }).catch(() => {}); send("[工作台] 调整参数重算：请回到阶段③参数确认，基于上次确认取值重新给出参数草案，待我确认后再重新求解。"); } }, "调整参数重算"),
						el("button", { className: "gdwz-cta2", disabled: sending, onClick: () => send("[工作台] 请生成并交付最终方案报告。") }, "导出报告"));
				}
			}

			let panel = null;
			const stageData = stages[String(viewStage)];
			if (viewStage === 1) panel = el(Stage1Panel, { data: stageData, ctas: ctas });
			else if (viewStage === 2) panel = el(Stage2Panel, { data: stageData, ctas: ctas });
			else if (viewStage === 3) panel = el(Stage3Panel, { data: stageData, edits: edits, setEdits: setEdits, ctas: ctas });
			else if (viewStage === 4) panel = el(Stage4Panel, { data: stageData, detail: detail, failed: detailFailed, ctas: ctas });
			else panel = el(Stage5Panel, { data: stageData, detail: detail, failed: detailFailed, ctas: ctas });

			return el("div", { className: "gdwz-root", ref: rootRef }, head,
				el("div", { className: "gdwz-body" },
					el(Stepper, { current: reached, viewing: viewStage, onView: setViewStage }),
					el("div", { className: "gdwz-main" }, jumpBar,
						el("div", { className: "gdwz-stagecard gd-card" }, panel))),
				interactions,
				consoleBar);
		}

		//#endregion

		/**
		 * 视图门卫：注册本身已按「当前会话为 green-direct 预设」门控
		 * （见 apply 的 sync），这里再用渲染期 props 双保险。
		 */
		function ViewGate(props) {
			let preset = undefined;
			try {
				const sid = props && props.sessionId;
				const useSessions = props && props.useSessions;
				if (typeof useSessions === "function" && sid !== undefined) {
					preset = useSessions((state) => {
						const row = state && state.byId ? state.byId[sid] : undefined;
						return row ? row.agentPreset : undefined;
					});
				}
			} catch (e) { preset = undefined; }
			if (preset !== "green-direct") return null;
			return el(WizardView, { sessionId: props.sessionId });
		}

		const inject = ["slots", "timer", "sessions", "connection"];

		function apply(ctx) {
			appCtx = ctx;

			// 样式：一次性注入 <style data-plugin-css>，插件卸载时移除。
			let styleTag = null;
			if (typeof document !== "undefined" && document.head) {
				if (document.querySelector('style[data-plugin-css="green-direct-workbench-v7"]') === null) {
					styleTag = document.createElement("style");
					styleTag.setAttribute("data-plugin-css", "green-direct-workbench-v7");
					styleTag.textContent = CSS;
					document.head.appendChild(styleTag);
				}
			}

			// 双重门控的标签页管理：
			//   外层——当前会话必须是 green-direct 预设；
			//   内层——该会话的向导已开启（智能体调用 workbench_open 后）。
			// 智能体判定项目流程启动之前，界面与普通会话完全一致，零打扰。
			const slots = ctx.slots;
			const sessions = ctx.sessions;
			let stopView = null;

			function currentSessionId() {
				try {
					const state = sessions.list.getSnapshot();
					return state.current;
				} catch (e) { return undefined; }
			}

			function currentPreset() {
				try {
					const state = sessions.list.getSnapshot();
					const cur = state.current;
					const row = cur === undefined ? undefined : (state.byId ? state.byId[cur] : undefined);
					return row ? row.agentPreset : undefined;
				} catch (e) { return undefined; }
			}

			let lastCurrent = undefined;

			/** 新建绿电会话成为当前且仍为空白时，把工作台切为当前视图：
			 * 代点框架渲染的 tab 按钮（触发官方 setView，非状态注入）。
			 * 会话一旦有了第一条消息（blank=false）立即作废，切回老会话
			 * 不打扰；tab 渲染有时序，用短重试等待其出现。 */
			function autoSwitchIfBlank(sid) {
				function isBlank() {
					try {
						const binding = appCtx.sessions.binding(sid);
						const snap = binding && binding.session && typeof binding.session.getSnapshot === "function" ? binding.session.getSnapshot() : null;
						return !!(snap && snap.blank === true);
					} catch (e) { return false; }
				}
				if (!isBlank()) return;
				let tries = 0;
				const attempt = () => {
					if (tries++ > 25 || !isBlank()) return;
					let mine = null;
					try {
						const tabs = document.querySelectorAll('[role="tab"]');
						for (let i = 0; i < tabs.length; i++) {
							const b = tabs[i];
							const label = b.textContent || "";
							if (label.indexOf("工作台") < 0) continue;
							if (b.getAttribute("aria-selected") === "true") return; // 已是当前视图
							if (mine === null) mine = b;
						}
					} catch (e) { mine = null; }
					if (mine !== null) { try { mine.click(); } catch (e) { /* 忽略 */ } return; }
					appCtx.setTimeout(attempt, 120);
				};
				appCtx.setTimeout(attempt, 60);
			}

			// 标签页管理：当前会话是 green-direct 预设即注册——新建绿电会话
			// 工作台立刻出现（空白会话还会自动切换为当前视图），阶段①在
			// 智能体推送画像前显示「等待项目开始」空态；其他预设的会话
			// 不受任何影响。切换当前会话即时跟进。
			function syncTab() {
				const sid = currentSessionId();
				const want = sid !== undefined && currentPreset() === "green-direct";
				if (want && stopView === null) {
					try {
						stopView = slots.register(
							{ name: "conversation.view", id: "gd-workbench", label: "🌱 工作台", order: 60 },
							ViewGate,
						);
					} catch (e) {
						// 条目 id 已被占用（如页面里残留旧版工作台插件未随热更新卸载）：
						// 跳过本次注册，刷新页面后即恢复。
						stopView = null;
					}
				} else if (!want && stopView !== null) {
					const stop = stopView;
					stopView = null;
					try { stop(); } catch (e) { /* 已注销则忽略 */ }
				}
				if (want && sid !== lastCurrent) autoSwitchIfBlank(sid);
				lastCurrent = sid;
			}

			let stopSub = null;
			try {
				if (sessions.list && typeof sessions.list.subscribe === "function") {
					stopSub = sessions.list.subscribe(() => { syncTab(); });
				}
			} catch (e) { /* 订阅失败则退化为轮询 */ }
			syncTab();
			const stopPoll = appCtx.interval(syncTab, 3000);

			ctx.effect(() => () => {
				if (stopSub !== null) { try { stopSub(); } catch (e) { /* 忽略 */ } }
				stopPoll();
				if (stopView !== null) { const stop = stopView; stopView = null; try { stop(); } catch (e) { /* 忽略 */ } }
				if (styleTag !== null && styleTag.parentNode) { try { styleTag.parentNode.removeChild(styleTag); } catch (e) { /* 忽略 */ } }
			});
		}

		exports.inject = inject;
		exports.apply = apply;
		return module.exports;
	}
});
