"""Agent-facing CLI for the green-direct muscle layer.

This module is the deterministic "muscle" half of the green-direct agent: the
LLM brain must never write solver code, only drive this CLI. Every subcommand
prints one JSON payload wrapped in ===GD_JSON=== markers so the model can
extract it regardless of log noise.

Engine-hiding: all engine output (solver banners, logs, tracebacks) is captured
and persisted only to a hidden ``.engine_debug.log`` next to the outputs; it is
never printed to stdout, so the conversation surface never reveals which
solver or internal methods power the optimization.

Subcommands
    template  Parameter confirmation sheet (defaults + categories + confirm rules)
    inspect   Data health check for profile/price files (units, gaps, expansion)
    solve     Run the capacity optimization (grid-connected or off-grid)
    validate  Post-hoc validation of solve outputs
"""

from __future__ import annotations

import argparse
import json
import os
import traceback
from dataclasses import replace
from pathlib import Path

JSON_BEGIN = "===GD_JSON_BEGIN==="
JSON_END = "===GD_JSON_END==="
ENGINE_LOG_NAME = ".engine_debug.log"

# --------------------------------------------------------------------------
# Parameter knowledge base: category drives how the brain must treat a field.
#   project  : project topology choice (grid/offgrid) -> confirmed in stage 1
#   business : commercial assumption -> MUST be confirmed by the user
#   policy   : project policy requirement -> MUST be confirmed by the user
#   technical: physical typical value -> usable, but tell the user the value
#   finance  : financial assumption -> confirm recommended, sane defaults exist
#   bounds   : search-space guardrail -> confirm on first use, then stable
# --------------------------------------------------------------------------

PARAM_META: list[dict] = [
    {"path": "project.type", "label": "项目类型", "unit": "-", "category": "project",
     "need_confirm": True, "note": "grid_connected（并网）/ offgrid（离网），阶段1确认。"},
    {"path": "solver.mode", "label": "求解引擎模式", "unit": "-", "category": "project",
     "need_confirm": True,
     "note": "default=天枢（主引擎，成熟稳定）；alternate=天璇（备选引擎，独立方法实现）；"
             "dual=双擎互证（两引擎同时求解并交叉核对目标值，最稳妥，耗时约2倍）。由用户选择。"},
    {"path": "project.loss_of_load_penalty_per_kwh", "label": "失负荷惩罚单价", "unit": "元/kWh", "category": "business",
     "need_confirm": True, "note": "仅离网项目；默认 10 元/kWh 为参考值，须确认。"},
    {"path": "project.max_loss_ratio_of_load", "label": "最大失负荷率上限", "unit": "-", "category": "policy",
     "need_confirm": True, "note": "仅离网项目；null=不设硬上限仅靠惩罚；供电保证率99%对应0.01。"},
    {"path": "diesel.enabled", "label": "柴油发电机启用", "unit": "-", "category": "project",
     "need_confirm": True, "note": "离网项目兜底电源，阶段1确认是否纳入；并网项目一般不启用。"},
    {"path": "diesel.capex_per_kw", "label": "柴油机组单位造价", "unit": "元/kW", "category": "business",
     "need_confirm": True, "note": "商务参数；仅 diesel.enabled=true 时生效。"},
    {"path": "diesel.fixed_om_per_kw_year", "label": "柴油机组固定运维", "unit": "元/kW/年", "category": "business",
     "need_confirm": True, "note": "商务参数；仅 diesel.enabled=true 时生效。"},
    {"path": "diesel.fuel_cost_per_kwh", "label": "柴油综合燃料成本", "unit": "元/kWh", "category": "business",
     "need_confirm": True, "note": "按发电量计的边际成本（含油料与耗材），对柴油配置规模影响最大。"},
    {"path": "diesel.min_capacity_kw", "label": "柴油装机下限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏；仅 diesel.enabled=true 时生效。"},
    {"path": "diesel.max_capacity_kw", "label": "柴油装机上限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏；仅 diesel.enabled=true 时生效。"},
    {"path": "biomass.enabled", "label": "生物质发电启用", "unit": "-", "category": "project",
     "need_confirm": True, "note": "可调度绿电电源，并网/离网均可，阶段1确认是否纳入。"},
    {"path": "biomass.capex_per_kw", "label": "生物质单位造价", "unit": "元/kW", "category": "business",
     "need_confirm": True, "note": "商务参数；仅 biomass.enabled=true 时生效。"},
    {"path": "biomass.fixed_om_per_kw_year", "label": "生物质固定运维", "unit": "元/kW/年", "category": "business",
     "need_confirm": True, "note": "商务参数；仅 biomass.enabled=true 时生效。"},
    {"path": "biomass.fuel_cost_per_kwh", "label": "生物质燃料成本", "unit": "元/kWh", "category": "business",
     "need_confirm": True, "note": "按发电量计的燃料边际成本（含收集、运输、预处理）。"},
    {"path": "biomass.capacity_factor", "label": "生物质容量因子", "unit": "-", "category": "technical",
     "need_confirm": False, "note": "可调度出力上限 = 装机 × 容量因子；典型值 0.85。"},
    {"path": "biomass.min_output_ratio", "label": "生物质最小出力比例", "unit": "-", "category": "business",
     "need_confirm": True,
     "note": "持续运行模式：机组启停昂贵，须持续运行，运行时段出力下限 = 比例 × 装机；"
             "参考值 0.5（即装机的一半），参数草案直接取该推荐值，用户可修改或置 0；"
             "0 = 不设最小出力（自由调度）。仅 biomass.enabled=true 时生效。"},
    {"path": "biomass.maintenance_days", "label": "生物质年检修天数", "unit": "天/年", "category": "business",
     "need_confirm": True,
     "note": "每年安排一个连续检修窗（窗口内出力为 0），起止时段由优化在全年自动选择"
             "（落在其他电源出力充裕的时段）；参考值 5~10 天（参数草案建议取 7），用户可修改或置 0；"
             "0 = 不检修。仅 biomass.enabled=true 时生效。"},
    {"path": "biomass.max_annual_energy_kwh", "label": "生物质燃料年可用量上限", "unit": "kWh/年", "category": "business",
     "need_confirm": True, "note": "燃料供应合同量（电量口径）；null=不设上限。"},
    {"path": "biomass.min_capacity_kw", "label": "生物质装机下限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏；仅 biomass.enabled=true 时生效。"},
    {"path": "biomass.max_capacity_kw", "label": "生物质装机上限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏；仅 biomass.enabled=true 时生效。"},
    {"path": "timestep_hours", "label": "时间步长", "unit": "h", "category": "technical",
     "need_confirm": False, "note": "固定 1.0，全年 8760 点。"},
    {"path": "costs.wind_capex_per_kw", "label": "风电单位造价", "unit": "元/kW", "category": "business",
     "need_confirm": True, "note": "商务参数，必须由用户提供或确认来源。"},
    {"path": "costs.pv_capex_per_kw", "label": "光伏单位造价", "unit": "元/kW", "category": "business",
     "need_confirm": True, "note": "商务参数，必须由用户提供或确认来源。"},
    {"path": "costs.ess_energy_capex_per_kwh", "label": "储能单位能量造价", "unit": "元/kWh", "category": "business",
     "need_confirm": True, "note": "商务参数，必须由用户提供或确认来源。"},
    {"path": "costs.ess_power_capex_per_kw", "label": "储能单位功率造价", "unit": "元/kW", "category": "business",
     "need_confirm": True, "note": "商务参数，必须由用户提供或确认来源。"},
    {"path": "costs.wind_om_per_kw_year", "label": "风电年运维", "unit": "元/kW/年", "category": "business",
     "need_confirm": True, "note": "商务参数。"},
    {"path": "costs.pv_om_per_kw_year", "label": "光伏年运维", "unit": "元/kW/年", "category": "business",
     "need_confirm": True, "note": "商务参数。"},
    {"path": "costs.ess_energy_om_per_kwh_year", "label": "储能能量年运维", "unit": "元/kWh/年", "category": "business",
     "need_confirm": True, "note": "商务参数。"},
    {"path": "costs.ess_power_om_per_kw_year", "label": "储能功率年运维", "unit": "元/kW/年", "category": "business",
     "need_confirm": True, "note": "商务参数。"},
    {"path": "storage.charge_efficiency", "label": "充电效率", "unit": "-", "category": "technical",
     "need_confirm": False, "note": "典型值 0.90，可按项目技术条件调整。"},
    {"path": "storage.discharge_efficiency", "label": "放电效率", "unit": "-", "category": "technical",
     "need_confirm": False, "note": "典型值 0.90，可按项目技术条件调整。"},
    {"path": "storage.soc_min_ratio", "label": "SOC 下限", "unit": "-", "category": "technical",
     "need_confirm": False, "note": "典型值 0.10。"},
    {"path": "storage.soc_max_ratio", "label": "SOC 上限", "unit": "-", "category": "technical",
     "need_confirm": False, "note": "典型值 0.90。"},
    {"path": "storage.min_storage_hours", "label": "储能时长下限", "unit": "h", "category": "technical",
     "need_confirm": False, "note": "典型值 2.0。"},
    {"path": "storage.max_storage_hours", "label": "储能时长上限", "unit": "h", "category": "technical",
     "need_confirm": False, "note": "典型值 6.0。"},
    {"path": "policy.min_self_use_ratio_of_green", "label": "绿电自用率下限", "unit": "-", "category": "policy",
     "need_confirm": True, "note": "政策/合同要求，属于项目约束条件。"},
    {"path": "policy.min_self_use_ratio_of_load", "label": "负荷绿电覆盖率下限", "unit": "-", "category": "policy",
     "need_confirm": True, "note": "政策/合同要求，属于项目约束条件。"},
    {"path": "policy.max_sell_ratio_of_green", "label": "绿电外售比例上限", "unit": "-", "category": "policy",
     "need_confirm": True, "note": "政策/合同要求；并网项目适用。"},
    {"path": "finance.discount_rate", "label": "折现率", "unit": "-", "category": "finance",
     "need_confirm": True, "note": "建议确认，默认 0.08。"},
    {"path": "finance.lifecycle_years", "label": "全寿命周期", "unit": "年", "category": "finance",
     "need_confirm": True, "note": "建议确认，默认 20。"},
    {"path": "finance.depreciation_years", "label": "折旧年限", "unit": "年", "category": "finance",
     "need_confirm": True, "note": "建议确认，默认 15。"},
    {"path": "finance.income_tax_rate", "label": "所得税率", "unit": "-", "category": "finance",
     "need_confirm": True, "note": "建议确认，默认 0.25。"},
    {"path": "finance.salvage_rate", "label": "残值率", "unit": "-", "category": "finance",
     "need_confirm": True, "note": "建议确认，默认 0.05。"},
    {"path": "bounds.wind_capacity_kw_max", "label": "风电装机上限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏，按项目条件设定。"},
    {"path": "bounds.pv_capacity_kw_max", "label": "光伏装机上限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏，按项目条件设定。"},
    {"path": "bounds.ess_energy_kwh_max", "label": "储能能量上限", "unit": "kWh", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏，按项目条件设定。"},
    {"path": "bounds.ess_power_kw_max", "label": "储能功率上限", "unit": "kW", "category": "bounds",
     "need_confirm": True, "note": "搜索空间护栏，按项目条件设定。"},
    {"path": "bounds.grid_import_kw_max", "label": "购电功率上限", "unit": "kW", "category": "bounds",
     "need_confirm": False, "note": "默认 100000，一般不约束；并网项目适用。"},
    {"path": "bounds.grid_export_kw_max", "label": "上网功率上限", "unit": "kW", "category": "bounds",
     "need_confirm": False, "note": "默认 100000，一般不约束；并网项目适用。"},
]

EXPECTED_HOURS = 8760


def _emit(payload: dict, audit_path: Path | None = None) -> None:
    """Print the payload between markers and optionally persist it for audit."""
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if audit_path is not None:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(text + "\n", encoding="utf-8")
    print(JSON_BEGIN)
    print(text)
    print(JSON_END)


def _dig(config_dict: dict, path: str):
    node: object = config_dict
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def _write_engine_log(output_dir: Path | None, captured: str) -> None:
    """Persist engine output to a hidden internal log only; never print it."""
    if output_dir is None:
        return
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / ENGINE_LOG_NAME).write_text(captured or "(no engine output)", encoding="utf-8")
    except OSError:
        pass


def _isolated(work):
    """Run work() with fd-level stdout/stderr capture so no engine detail leaks.

    The underlying engine writes logs at the OS file-descriptor level, so a
    plain Python ``redirect_stdout`` is not enough: both fd 1 and fd 2 are
    temporarily pointed at a temp file. Returns (value, captured, error_text).
    """
    import os
    import sys
    import tempfile

    captured_file = tempfile.TemporaryFile(mode="w+")
    saved_stdout = os.dup(1)
    saved_stderr = os.dup(2)
    try:
        os.dup2(captured_file.fileno(), 1)
        os.dup2(captured_file.fileno(), 2)
        try:
            value = work()
            error_text = None
        except Exception:
            value = None
            error_text = traceback.format_exc()
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
    finally:
        os.dup2(saved_stdout, 1)
        os.dup2(saved_stderr, 2)
        os.close(saved_stdout)
        os.close(saved_stderr)
    captured_file.seek(0)
    captured = captured_file.read()
    captured_file.close()
    return value, captured, error_text


def _load_config_quietly(config_arg: str | None):
    """Load config outside engine isolation; config errors are user-facing."""
    from .config import load_optimization_config

    try:
        return load_optimization_config(config_arg), None
    except Exception as exc:  # noqa: BLE001 - surfaced to the brain verbatim
        return None, f"{type(exc).__name__}: {exc}"


def _precheck_data_quietly(data_path: str | None, price_path: str | None):
    """Pre-load data outside engine isolation; data errors are user-facing.

    含缺失/非有限数值（NaN、±∞）的文件在求解层会静默击穿约束，必须
    在进入引擎隔离区之前以 USAGE_ERROR 拒绝，错误信息直达用户。
    """
    from .io_utils import load_price_data, load_profile_data

    try:
        profile = load_profile_data(data_path)
        if price_path is not None:
            load_price_data(price_path, len(profile))
        return None
    except Exception as exc:  # noqa: BLE001 - surfaced to the brain verbatim
        return f"{type(exc).__name__}: {exc}"


def cmd_template(_args: argparse.Namespace) -> None:
    from .config import OptimizationConfig, config_to_dict

    defaults = config_to_dict(OptimizationConfig())
    parameters = []
    for meta in PARAM_META:
        entry = dict(meta)
        entry["default"] = _dig(defaults, meta["path"])
        parameters.append(entry)
    _emit({
        "tool": "green_direct.template",
        "objective": "全生命周期投资成本（NPV）最小化",
        "horizon_hours": EXPECTED_HOURS,
        "parameters": parameters,
        "usage": (
            "起草项目 config.json 时：technical 类字段可用默认值；project/business/policy/finance/bounds "
            "中 need_confirm=true 的字段必须先向用户确认；未确认前不得求解。"
            "离网项目（project.type=offgrid）无购售电，需确认失负荷惩罚与最大失负荷率；"
            "并网项目（grid_connected）必须提供电价文件。"
            "可选组件：diesel.enabled=true 启用柴油兜底电源（多用于离网），"
            "biomass.enabled=true 启用生物质发电（并网/离网均可，计入绿电口径）。"
            "组件默认禁用：不写 diesel/biomass 节点即与纯风/光/储模型一致。"
        ),
    })


def _series_stats(frame, column: str) -> dict:
    series = frame[column]
    numeric = series.astype(float)
    nan_count = int(series.isna().sum())
    negative = int((numeric.dropna() < 0).sum())
    zero = int((numeric.dropna() == 0).sum())
    max_value = float(numeric.max()) if not numeric.dropna().empty else 0.0
    min_value = float(numeric.min()) if not numeric.dropna().empty else 0.0
    mean_value = float(numeric.mean()) if not numeric.dropna().empty else 0.0
    normalized = max_value <= 1.05
    if normalized:
        unit_guess = "归一化出力系数（出力 = 装机容量 × 该值），需确认单位为 kW 口径"
    else:
        unit_guess = "绝对功率（按 kW 理解），必须与用户确认单位"
    return {
        "min": min_value,
        "max": max_value,
        "mean": mean_value,
        "nan_count": nan_count,
        "negative_count": negative,
        "zero_count": zero,
        "normalized_guess": normalized,
        "unit_guess": unit_guess,
    }


def cmd_inspect(args: argparse.Namespace) -> None:
    from .io_utils import load_price_data, load_profile_data, read_table

    issues: list[str] = []
    data_path = Path(args.data)
    if not data_path.exists():
        _emit({"tool": "green_direct.inspect", "verdict": "FILE_NOT_FOUND", "error": str(data_path)})
        raise SystemExit(1)

    try:
        profile = load_profile_data(data_path)
    except Exception as exc:  # noqa: BLE001 - report any ingestion failure as data
        _emit({"tool": "green_direct.inspect", "verdict": "PROFILE_UNREADABLE", "error": f"{type(exc).__name__}: {exc}"})
        raise SystemExit(1) from exc

    raw = read_table(data_path)
    horizon = len(profile)
    if horizon != EXPECTED_HOURS:
        issues.append(f"时序长度 {horizon} 小时（预期 {EXPECTED_HOURS}），需与用户确认口径。")

    series_stats = {
        "load": _series_stats(profile, "Load"),
        "pv": _series_stats(profile, "PV"),
        "wind": _series_stats(profile, "Wind"),
    }
    for key in ("pv", "wind"):
        stats = series_stats[key]
        if stats["max"] == 0.0 and stats["zero_count"] == horizon:
            issues.append(f"{key.upper()} 列全为 0，请确认该电源是否参与本项目。")
    if series_stats["load"]["max"] == 0.0:
        issues.append("负荷列全为 0，无法求解。")
    for key, stats in series_stats.items():
        if stats["nan_count"]:
            issues.append(f"{key} 列存在 {stats['nan_count']} 个缺失值。")
        if stats["negative_count"]:
            issues.append(f"{key} 列存在 {stats['negative_count']} 个负值。")

    price_report: dict | None = None
    if args.price:
        price_path = Path(args.price)
        if not price_path.exists():
            issues.append(f"电价文件不存在：{price_path}")
        else:
            try:
                price_frame = read_table(price_path)
                buy, sell = load_price_data(price_path, horizon)
                price_report = {
                    "file": str(price_path),
                    "rows": int(len(price_frame)),
                    "expansion": {
                        "needed": len(price_frame) != horizon,
                        "mode": (
                            "truncated"
                            if len(price_frame) > horizon
                            else "cyclic"
                        ),
                        "target_rows": horizon,
                    },
                    "buy": {"min": min(buy), "max": max(buy)},
                    "sell": {"min": min(sell), "max": max(sell)},
                }
                if len(price_frame) < horizon:
                    issues.append(
                        f"电价文件 {len(price_frame)} 行，将循环扩展到 {horizon} 小时，请向用户说明该扩展方式。"
                    )
                elif len(price_frame) > horizon:
                    issues.append(
                        f"电价文件 {len(price_frame)} 行多于时序 {horizon} 行，将仅使用前 {horizon} 行，请与用户确认口径。"
                    )
                if min(sell) >= max(buy):
                    issues.append("售电价整体不低于购电价，套利方向异常，请与用户核对。")
            except Exception as exc:  # noqa: BLE001
                issues.append(f"电价文件解析失败：{type(exc).__name__}: {exc}")

    _emit({
        "tool": "green_direct.inspect",
        "data_file": str(data_path),
        "format": data_path.suffix.lower().lstrip("."),
        "rows": horizon,
        "expected_rows": EXPECTED_HOURS,
        "columns_raw": [str(col) for col in raw.columns],
        "matched_columns": {"load": "Load", "pv": "PV", "wind": "Wind"},
        "series": series_stats,
        "price": price_report,
        "issues": issues,
        "verdict": "DATA_OK" if not issues else "DATA_ISSUES",
    })


# 求解引擎模式的对外呈现名（引擎隐藏铁律：绝不出现品牌或实现细节）。
_SOLVER_MODE_DISPLAY = {"default": "天枢", "alternate": "天璇", "dual": "双擎互证"}


def cmd_solve(args: argparse.Namespace) -> None:
    config, config_error = _load_config_quietly(args.config)
    if config_error is not None:
        _emit({"tool": "green_direct.solve", "verdict": "USAGE_ERROR",
               "error": f"配置文件无法加载：{config_error}"})
        raise SystemExit(1)
    # --solver 覆盖配置里的引擎模式（CLI 便捷覆盖，config 为准绳）。
    if args.solver is not None and args.solver != config.solver.mode:
        config = replace(config, solver=replace(config.solver, mode=args.solver))
    if config.project.type == "grid_connected" and args.price is None:
        _emit({"tool": "green_direct.solve", "verdict": "USAGE_ERROR",
               "error": "并网项目必须提供 --price 电价文件；离网项目可省略。"})
        raise SystemExit(1)
    data_error = _precheck_data_quietly(args.data, args.price)
    if data_error is not None:
        _emit({"tool": "green_direct.solve", "verdict": "USAGE_ERROR",
               "error": f"数据文件无法加载：{data_error}"})
        raise SystemExit(1)

    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs")

    def work():
        from .solver import build_and_solve_model

        return build_and_solve_model(
            data_path=args.data,
            price_path=args.price,
            output_dir=str(output_dir),
            config=config,
        )

    result, captured, error = _isolated(work)
    if error is not None:
        _write_engine_log(output_dir, captured + "\n" + error)
        message = _summarize_engine_error(error)
        _emit({"tool": "green_direct.solve", "verdict": "SOLVE_ERROR", "error": message,
               "hint": "内部日志已写入输出目录的 .engine_debug.log，请勿向用户展示该文件内容。"})
        raise SystemExit(1)
    _write_engine_log(output_dir, captured)

    from .solver import SOLVER_STATUS_NAMES

    status_name = SOLVER_STATUS_NAMES.get(result.status, f"STATUS_{result.status}")
    payload = {
        "tool": "green_direct.solve",
        "project_type": result.project_type,
        "status": status_name,
        "solver_mode": _SOLVER_MODE_DISPLAY.get(config.solver.mode, config.solver.mode),
        "objective_value": result.objective_value,
        "objective_meaning": "全生命周期净现值总成本（元）",
        "installed_capacities": result.installed_capacities,
        "economic_metrics": result.economic_metrics,
        "ratio_metrics": result.ratio_metrics,
        "outputs": {
            "hourly_csv": str(result.hourly_csv_path),
            "summary_csv": str(result.summary_csv_path),
            **({"excel": str(result.excel_path)} if result.excel_path else {}),
        },
        "outputs_meaning": (
            "excel 为面向用户的成果工作簿（方案总览/经济性明细/装机与边界/逐时运行/校验结论"
            "等多 Sheet、全中文），应作为主要交付物向用户提供路径；两个 CSV 为机器通道文件，"
            "无需向用户强调。"
        ),
        "config_source": str(args.config) if args.config else "代码默认值",
        "next_step": "运行 validate 子命令做后验校验；校验通过前不得向用户呈现结论。",
    }
    if result.cross_check is not None:
        payload["cross_check"] = result.cross_check
        payload["cross_check_meaning"] = (
            "双擎互证：两个相互独立的求解引擎对同一模型各自求解并交叉核对最优目标值，"
            "一致方可采信；装机组合差异（多重最优解）时采用主引擎方案。"
        )
    if result.maintenance_window is not None:
        payload["biomass_maintenance_window"] = result.maintenance_window
        payload["biomass_maintenance_window_meaning"] = (
            "生物质检修窗由优化在全年自动选择：窗口内出力为 0；start_hour 为窗口起始小时"
            "（0 起，8760h 循环年），hours 为窗口小时数；应向用户转述窗口位置（换算为日期）。"
        )
    if result.boundary_notes:
        payload["boundary_hints"] = list(result.boundary_notes)
        payload["boundary_hints_meaning"] = (
            "边界触顶提示：以下决策量已贴住配置边界，优化结果受边界约束影响，"
            "并非无约束最优；应向用户逐条转述，并说明如需扩大寻优空间可回到"
            "阶段3放宽对应边界后重新求解。"
        )
    if getattr(result, "engine_fallback_note", None):
        payload["engine_fallback_note"] = result.engine_fallback_note
        payload["engine_fallback_note_meaning"] = (
            "引擎降级说明：默认天枢引擎环境未就绪，本次实际由天璇引擎完成求解；"
            "应向用户如实转述（结果仍经完整校验），并建议完成环境安装与许可配置"
            "后恢复双擎互证。"
        )
    if result.project_type == "offgrid" and args.price is not None:
        payload["price_note"] = "离网项目电价文件仅作逐时结果记录，不参与经济计算。"
    _emit(payload, audit_path=output_dir / "agent_result.json")


def _summarize_engine_error(error_text: str) -> str:
    """Translate engine failures into business-facing messages without leaking internals."""
    if "互证不一致" in error_text:
        return ("双擎互证未通过：两个独立求解引擎的结果不一致，本次结果不可信；"
                "请检查数据与配置后重试，或改用单一引擎模式（天枢/天璇）。")
    if "缺少求解器组件" in error_text:
        # 主引擎组件缺失：traceback 不入载荷，返回与 solver 模块一致的业务消息。
        from .solver import PRIMARY_UNAVAILABLE_MESSAGE

        return PRIMARY_UNAVAILABLE_MESSAGE
    if "license" in error_text.lower() or "许可" in error_text:
        return ("天枢引擎许可未就绪：请先完成求解器许可的安装与配置（获取后放置于"
                "~/mindopt/mindopt.lic，或用环境变量 MINDOPT_LICENSE_PATH 指定路径），"
                "或改用免许可的天璇引擎（--solver alternate）。可运行 "
                "./agent_tools/gd doctor 自检环境状态。")
    lowered = error_text.lower()
    if "inf_or_ubd" in lowered or "infeasible" in lowered or "不可行" in error_text or "无可行解" in error_text:
        return ("优化在当前约束下不可行：项目要求与资源条件相互冲突，"
                "请检查政策比例要求、失负荷率上限、容量与燃料资源上限、负荷/资源数据后调整配置；"
                "政策级放宽须经用户确认。")
    if "unbounded" in lowered or "无界" in error_text:
        return "优化目标无界，请检查经济参数（如负成本或异常价格）设置。"
    if "unknown" in lowered or "无可用解" in error_text:
        return "优化未得到可用解，请检查数据与参数后重试。"
    return "求解引擎执行失败，请检查数据文件与配置后重试。"


def cmd_validate(args: argparse.Namespace) -> None:
    config, config_error = _load_config_quietly(args.config)
    if config_error is not None:
        _emit({"tool": "green_direct.validate", "verdict": "USAGE_ERROR",
               "error": f"配置文件无法加载：{config_error}"})
        raise SystemExit(1)
    if config.project.type == "grid_connected" and args.price is None:
        _emit({"tool": "green_direct.validate", "verdict": "USAGE_ERROR",
               "error": "并网项目必须提供 --price 电价文件；离网项目可省略。"})
        raise SystemExit(1)
    data_error = _precheck_data_quietly(args.data, args.price)
    if data_error is not None:
        _emit({"tool": "green_direct.validate", "verdict": "USAGE_ERROR",
               "error": f"数据文件无法加载：{data_error}"})
        raise SystemExit(1)

    report_path = Path(args.report) if args.report else Path("outputs") / "validation_report.json"

    def work():
        from .validation import save_validation_report, validate_solution_outputs

        report = validate_solution_outputs(
            data_path=args.data,
            price_path=args.price,
            hourly_results_path=args.hourly_results,
            summary_results_path=args.summary_results,
            config=config,
            objective_tolerance=args.objective_tolerance,
        )
        saved = save_validation_report(report, str(report_path))
        # 校验结论自动并入成果工作簿（v4.2）：与汇总 CSV 同目录存在
        # green_direct_results.xlsx 时更新其"校验结论"页；不存在则跳过。
        excel_updated: str | None = None
        try:
            from pathlib import Path as _Path

            candidate = _Path(args.summary_results).parent / "green_direct_results.xlsx"
            if candidate.exists():
                from .excel_report import append_validation_sheet

                excel_updated = str(append_validation_sheet(candidate, report))
        except Exception:  # noqa: BLE001 - 工作簿是增值交付物，失败不影响校验结论
            excel_updated = None
        return saved, report, excel_updated

    value, captured, error = _isolated(work)
    if error is not None:
        target_dir = report_path.parent
        _write_engine_log(target_dir, captured + "\n" + error)
        _emit({"tool": "green_direct.validate", "verdict": "VALIDATE_ERROR",
               "error": "结果文件无法校验，请确认结果文件由最近一次求解生成。",
               "hint": "内部日志已写入 .engine_debug.log，请勿向用户展示该文件内容。"})
        raise SystemExit(1)
    _write_engine_log(report_path.parent, captured)
    report_path_out, report, excel_updated = value

    payload = {
        "tool": "green_direct.validate",
        "passed": report.passed,
        "total_checks": report.total_checks,
        "passed_checks": report.passed_checks,
        "failed_checks": report.failed_checks,
        "failures": [
            {"name": check.name, "metric": check.metric, "threshold": check.threshold, "details": check.details}
            for check in report.checks
            if not check.passed
        ],
        "report_path": str(report_path_out),
        "gate": "passed=false 时，结果不得呈现给用户，必须先诊断修复。",
    }
    if excel_updated:
        payload["excel_updated"] = excel_updated
        payload["excel_updated_meaning"] = "校验结论已写入成果工作簿的「校验结论」页。"
    _emit(payload, audit_path=Path(args.report) if args.report else None)


def cmd_report(args: argparse.Namespace) -> None:
    config, config_error = _load_config_quietly(args.config)
    if config_error is not None:
        _emit({"tool": "green_direct.report", "verdict": "USAGE_ERROR",
               "error": f"配置文件无法加载：{config_error}"})
        raise SystemExit(1)

    # 校验门（铁律）：同目录存在校验报告且未通过时，拒绝生成报告。
    summary_path = Path(args.summary_results)
    validation_path = summary_path.parent / "validation_report.json"
    if validation_path.exists():
        try:
            with open(validation_path, encoding="utf-8") as handle:
                gate = json.load(handle)
            if gate.get("passed") is False:
                _emit({"tool": "green_direct.report", "verdict": "REPORT_BLOCKED",
                       "error": "校验未通过，结果不得交付：请先诊断修复并通过校验，再生成报告。"})
                raise SystemExit(1)
        except json.JSONDecodeError:
            pass

    def work():
        import csv

        from .docx_report import write_report_docx

        with open(summary_path, encoding="utf-8-sig") as handle:
            summary = next(iter(csv.DictReader(handle)))
        output_path = args.output or str(summary_path.parent / "green_direct_report.docx")
        if args.project_name:
            project_name = args.project_name
        elif summary_path.parent.name == "outputs":
            project_name = summary_path.parent.parent.name
        else:
            project_name = summary_path.parent.name
        return write_report_docx(output_path, summary=summary, config=config, project_name=project_name)

    value, captured, error = _isolated(work)
    if error is not None:
        target_dir = summary_path.parent
        _write_engine_log(target_dir, captured + "\n" + error)
        _emit({"tool": "green_direct.report", "verdict": "REPORT_ERROR",
               "error": "报告生成失败：请确认汇总结果文件由最近一次求解生成后重试。",
               "hint": "内部日志已写入 .engine_debug.log，请勿向用户展示该文件内容。"})
        raise SystemExit(1)
    report_path_out, points = value
    payload = {
        "tool": "green_direct.report",
        "report_path": str(report_path_out),
        "project_name": args.project_name or report_path_out.parent.name,
        "summary_points": points,
        "summary_points_meaning": (
            "报告结论摘要（与报告正文逐字一致）：应原样引用到聊天与工作台 highlights，"
            "不得改写数字与措辞。"
        ),
        "report_meaning": (
            "业主交付的 Word 报告（项目简介/结论摘要/推荐方案/经济性/运行特性/附录），"
            "由引擎从求解结果与配置确定性生成，组件按项目实际配置过滤。"
        ),
        "next_step": "向用户提供报告与成果工作簿（green_direct_results.xlsx）的路径；报告正文即最终交付物。",
    }
    _emit(payload, audit_path=summary_path.parent / "agent_report_result.json")


def cmd_doctor(_args: argparse.Namespace) -> None:
    def work():
        import platform

        from .solver import MINDOPT_AVAILABLE, STATUS_OPTIMAL

        checks: dict[str, bool] = {}
        versions: dict[str, str] = {}
        for name in ("pandas", "numpy", "scipy", "openpyxl", "docx"):
            try:
                module = __import__(name)
                checks[name] = True
                versions[name] = getattr(module, "__version__", "unknown")
            except Exception:
                checks[name] = False
                versions[name] = "缺失"

        primary_ready = False
        license_ok = False
        license_hint = ""
        if MINDOPT_AVAILABLE:
            checks["primary_solver_component"] = True
            try:
                from mindoptpy import Model

                probe = Model("doctor_probe")
                x = probe.addVar(0.0, 10.0, 1.0, "C", "x")
                probe.setObjective(x + 0.0)
                probe.optimize()
                license_ok = bool(probe.Status == STATUS_OPTIMAL)
                probe.dispose()
                primary_ready = license_ok
                if not license_ok:
                    license_hint = "求解器组件已安装，但许可校验未通过：请配置有效的许可文件。"
            except Exception as exc:  # noqa: BLE001 - 自检需区分许可与组件问题
                if "license" in str(exc).lower():
                    license_hint = "未检测到有效许可：请注册获取许可文件并放置到 ~/mindopt/mindopt.lic，或用 MINDOPT_LICENSE_PATH 指定路径。"
                else:
                    license_hint = "求解器组件存在但初始化失败：请重装组件或检查系统依赖。"
        else:
            checks["primary_solver_component"] = False
            license_hint = "未安装求解器组件：天枢与双擎互证不可用，天璇引擎可正常工作。"

        alternate_ready = checks.get("scipy", False) and checks.get("numpy", False)
        base_ready = checks.get("pandas", False) and checks.get("openpyxl", False) and checks.get("docx", False)
        return {
            "python": platform.python_version(),
            "checks": checks,
            "versions": versions,
            "base_ready": base_ready,
            "primary_ready": primary_ready,
            "alternate_ready": alternate_ready,
            "license_ok": license_ok,
            "license_hint": license_hint,
        }

    value, captured, error = _isolated(work)
    if error is not None:
        target_dir = Path.cwd()
        _write_engine_log(target_dir, captured + "\n" + error)
        _emit({"tool": "green_direct.doctor", "verdict": "DOCTOR_ERROR",
               "error": "环境自检失败：基础依赖可能缺失，请按 README 安装章节补齐依赖后重试。"})
        raise SystemExit(1)
    payload = {
        "tool": "green_direct.doctor",
        **value,
        "meaning": (
            "环境自检：base_ready=基础依赖齐全（结果导出与报告生成可用）；"
            "primary_ready=天枢引擎可用（组件安装且许可有效）；"
            "alternate_ready=天璇引擎可用（免许可，始终可用的保底引擎）；"
            "license_hint=给出未就绪项的处置建议。"
        ),
        "next_step": "按 license_hint 与缺失项提示处置后重跑自检；至少 alternate_ready=true 即可开始使用。",
    }
    _emit(payload)


def cmd_intake(args: argparse.Namespace) -> None:
    def work():
        from .intake import parse_intake_checklist

        return parse_intake_checklist(args.checklist)

    value, captured, error = _isolated(work)
    if error is not None:
        _write_engine_log(Path.cwd(), captured + "\n" + error)
        _emit({"tool": "green_direct.intake", "verdict": "INTAKE_ERROR",
               "error": "收资清单读取失败：请确认文件为《绿电直连项目收资清单_智能体版》模板填写后重试。"})
        raise SystemExit(1)
    result = value
    payload = {
        "tool": "green_direct.intake",
        "verdict": "OK" if result.ok else "NEEDS_CLARIFICATION",
        "project_name": result.project_name,
        "project_type": "并网型" if result.project_type == "grid_connected" else "离网型",
        "components": {"diesel": result.diesel_enabled, "biomass": result.biomass_enabled},
        "filled_params": [{"path": path, "value": value} for path, value in result.filled_params],
        "blank_params": list(result.blank_params),
        "ignored_params": list(result.ignored_params),
        "warnings": list(result.warnings),
    }
    if result.notes:
        payload["notes"] = result.notes
    if not result.ok:
        payload["issues"] = list(result.issues)
        payload["issues_meaning"] = (
            "收资清单存在必须澄清的问题：逐条原样转述给业主，请其修正清单后重新提供；"
            "不得猜测或代填，不得带问题推进。"
        )
        _emit(payload)
        return

    # 落盘项目配置并用真实配置加载器校验（类型/未知字段/取值范围）。
    projects_root = Path(os.environ.get("GD_HOME") or Path(__file__).resolve().parents[2]) / "projects"
    target_dir = projects_root / result.project_name
    target_dir.mkdir(parents=True, exist_ok=True)
    config_path = target_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(result.config_overrides, handle, ensure_ascii=False, indent=2)
    _, config_error = _load_config_quietly(str(config_path))
    if config_error is not None:
        config_path.unlink(missing_ok=True)
        _emit({"tool": "green_direct.intake", "verdict": "INTAKE_ERROR",
               "error": f"清单参数无法构成有效配置：{config_error}",
               "hint": "请核对清单中的数值与取值范围后重试。"})
        raise SystemExit(1)

    payload.update({
        "config_path": str(config_path),
        "data_files": {
            "load": str(result.load_path),
            **({"price": str(result.price_path)} if result.price_path else {}),
        },
        "filled_count": len(result.filled_params),
        "blank_params_meaning": (
            "业主留空的参数：阶段3 仅对这些项给出推荐值草案并经业主确认；"
            "filled_params 中的参数业主已拍板，不得再出草案或改写。"
        ),
        "warnings_meaning": "非阻断性提示：向业主逐条转述。",
        "next_step": (
            "清单已转成项目配置。进入阶段2 数据体检（负荷文件路径与电价文件路径见 data_files）；"
            f"体检通过后进入阶段3：{'存在留空参数，仅对留空项出推荐值草案' if result.blank_params else '无留空参数，陈述式小结后直接求解'}。"
        ),
    })
    _emit(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="green-direct-agent",
        description="绿电直连智能体肌肉层 CLI（LLM 大脑的唯一求解入口）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("template", help="输出参数确认表（默认值+分类+确认规则）")

    p_inspect = sub.add_parser("inspect", help="数据体检")
    p_inspect.add_argument("--data", required=True, help="负荷/出力时序文件")
    p_inspect.add_argument("--price", default=None, help="电价文件（可选；离网项目不需要）")
    p_inspect.set_defaults(func=cmd_inspect)

    p_solve = sub.add_parser("solve", help="容量优化求解（并网/离网）")
    p_solve.add_argument("--data", required=True)
    p_solve.add_argument("--price", default=None, help="电价文件；并网必填，离网可省略")
    p_solve.add_argument("--config", default=None, help="项目配置 JSON（部分覆盖默认值）")
    p_solve.add_argument("--solver", default=None, choices=["default", "alternate", "dual"],
                         help="求解引擎模式覆盖：default=天枢，alternate=天璇，dual=双擎互证")
    p_solve.add_argument("--output-dir", required=True, help="输出目录（须在会话工作区内）")
    p_solve.set_defaults(func=cmd_solve)

    p_intake = sub.add_parser("intake", help="读取智能体版收资清单 → 生成项目配置")
    p_intake.add_argument("--checklist", required=True, help="收资清单（智能体版）xlsx 路径")
    p_intake.set_defaults(func=cmd_intake)

    p_report = sub.add_parser("report", help="生成业主交付 Word 报告（须先求解，建议先校验）")
    p_report.add_argument("--summary-results", required=True, help="求解输出的汇总 CSV 路径")
    p_report.add_argument("--config", required=True, help="项目配置 JSON")
    p_report.add_argument("--project-name", default=None, help="项目名（默认取输出目录名）")
    p_report.add_argument("--output", default=None, help="报告输出路径（默认汇总 CSV 同目录 green_direct_report.docx）")
    p_report.set_defaults(func=cmd_report)

    sub.add_parser("doctor", help="环境自检：依赖、求解器组件与许可状态").set_defaults(func=cmd_doctor)

    p_validate = sub.add_parser("validate", help="结果后验校验")
    p_validate.add_argument("--data", required=True)
    p_validate.add_argument("--price", default=None, help="电价文件；并网必填，离网可省略")
    p_validate.add_argument("--config", default=None)
    p_validate.add_argument("--hourly-results", required=True)
    p_validate.add_argument("--summary-results", required=True)
    p_validate.add_argument("--report", required=True, help="校验报告 JSON 输出路径")
    p_validate.add_argument(
        "--objective-tolerance",
        type=float,
        default=1.0e-4,
        help="经济性重构容差（元）。默认 1e-4；数十亿元量级项目可放宽至 1.0 以容纳双精度累加尾差。",
    )
    p_validate.set_defaults(func=cmd_validate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "template":
        cmd_template(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
