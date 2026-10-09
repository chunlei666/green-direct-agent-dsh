"""备选求解引擎（天璇）：矩阵化 LP 的独立建模实现。

与 solver.py 的主引擎（天枢）构成相互独立的两套建模：本模块不共享主引擎
的任何建模代码，从同一份输入以标准稀疏矩阵形式独立重建线性规划并求解。
刻意保持双实现是「双擎互证」模式的基础——任何一处建模漂移都会表现为两
引擎目标值不一致而被交叉核对拦截。

对外呈现约束（引擎隐藏铁律）：本模块产生的一切用户可见文本（异常消息、
结果字段）只使用引擎代号与通用优化状态，不出现求解器品牌或内部方法名；
底层求解库的原始报错一律不得透传给上层。
"""

from __future__ import annotations

import tempfile
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from .config import OptimizationConfig
from .excel_report import build_component_bounds
from .io_utils import (
    export_results_to_csv,
    load_price_data,
    load_profile_data,
    read_hourly_biomass_series,
    select_maintenance_window,
)
from .solver import (
    GRID_CONNECTED,
    OFFGRID,
    SOLVER_STATUS_NAMES,
    STATUS_INFEASIBLE,
    STATUS_INF_OR_UBD,
    STATUS_OPTIMAL,
    STATUS_UNBOUNDED,
    STATUS_UNKNOWN,
    SolveResult,
    present_value_factor,
)

# 底层求解库状态码 → 两引擎共用的通用优化状态常量（不依赖主引擎组件）。
_LINPROG_STATUS_TO_CODE = {
    0: STATUS_OPTIMAL,
    2: STATUS_INFEASIBLE,
    3: STATUS_UNBOUNDED,
    4: STATUS_INF_OR_UBD,
}


class _SolutionValue:
    """export_results_to_csv 通过 .X 属性取值；本引擎以纯数值包装适配。"""

    __slots__ = ("X",)

    def __init__(self, value: float) -> None:
        self.X = float(value)


def build_and_solve_model_alternate(
    data_path: str,
    price_path: str | None = None,
    output_dir: str | None = None,
    config: OptimizationConfig | None = None,
    write_outputs: bool = True,
    fixed_maintenance_start: int | None = None,
) -> SolveResult:
    """天璇引擎：矩阵化 LP 独立求解（结果结构与主引擎完全一致）。

    write_outputs=False 供双擎互证模式使用：只求解不落盘（落盘由主引擎
    方案负责），CSV 路径字段返回占位路径。检修窗两阶段定窗与主引擎完全
    同构，且预解同样由本引擎完成（两阶段求解器一致）：本引擎预解（不检
    修）→ 共用规则选窗 → 本引擎固定窗重解；各引擎独立完成自己的两阶段，
    双擎互证在最终结果层面交叉核对。
    """
    config = config or OptimizationConfig()
    project_type = config.project.type
    if project_type not in {GRID_CONNECTED, OFFGRID}:
        raise ValueError(f"未知项目类型: {project_type}。支持的类型: grid_connected, offgrid。")

    df = load_profile_data(Path(data_path))
    load = df["Load"].astype(float).tolist()
    pv_profile = df["PV"].astype(float).tolist()
    wind_profile = df["Wind"].astype(float).tolist()
    horizon = len(df)
    dt = config.timestep_hours
    grid = project_type == GRID_CONNECTED

    if grid:
        if price_path is None:
            raise ValueError("并网项目必须提供电价文件（price_path）。")
        buy_price, sell_price = load_price_data(price_path, horizon)
    else:
        if price_path is None:
            buy_price = [0.0] * horizon
            sell_price = [0.0] * horizon
        else:
            buy_price, sell_price = load_price_data(price_path, horizon)

    costs = config.costs
    storage = config.storage
    policy = config.policy
    finance = config.finance
    bounds = config.bounds
    project = config.project
    diesel = config.diesel
    biomass = config.biomass
    diesel_enabled = diesel.enabled
    biomass_enabled = biomass.enabled

    # 持续运行模式（v4.1 两阶段定窗）：与主引擎完全一致的语义——运行时段
    # 出力 ≥ 最小出力比例 × 装机；每年一个连续检修窗（按日起始、可跨年首
    # 尾），窗内出力为 0，窗口位置由两阶段方法确定（预解选窗后固定，模型
    # 保持纯线性，本引擎不升格为混合整数规划）。
    biomass_must_run = biomass_enabled and biomass.min_output_ratio > 0.0
    biomass_maint_hours = (
        int(round(biomass.maintenance_days * 24)) if biomass_enabled else 0
    )
    biomass_continuous = biomass_enabled and (biomass_must_run or biomass_maint_hours > 0)
    biomass_num_days = horizon // 24
    if biomass_maint_hours > 0:
        if horizon % 24 != 0 or biomass_num_days < 1:
            raise ValueError("时序长度须为整天数（8760h），才能按日粒度安排生物质检修窗。")
        if biomass_maint_hours >= horizon:
            raise ValueError("生物质检修时长不小于时序长度，无法求解。")

    # 检修窗两阶段定窗编排（v4.3，与主引擎同构）：预解与重解均由本引擎
    # 完成（两阶段求解器必须一致），仅定窗"规则"（选窗函数）与主引擎共用
    # 同一实现以保证规则一致。预解在临时目录落盘后即弃，不污染最终输出。
    if biomass_maint_hours > 0 and fixed_maintenance_start is None:
        stage_a_config = replace(
            config, biomass=replace(config.biomass, maintenance_days=0.0)
        )
        with tempfile.TemporaryDirectory() as stage_a_dir:
            stage_a = build_and_solve_model_alternate(
                data_path,
                price_path,
                stage_a_dir,
                stage_a_config,
                write_outputs=True,
            )
            biomass_series = read_hourly_biomass_series(stage_a.hourly_csv_path)
            start_day = select_maintenance_window(
                biomass_series, len(biomass_series) // 24, biomass_maint_hours
            )
        result = build_and_solve_model_alternate(
            data_path,
            price_path,
            output_dir,
            config,
            write_outputs=write_outputs,
            fixed_maintenance_start=start_day * 24,
        )
        return replace(result, stage_a_objective=stage_a.objective_value)
    if biomass_maint_hours > 0:
        maintenance_hour_set = {
            (fixed_maintenance_start + k) % horizon for k in range(biomass_maint_hours)
        }

    total_load = sum(load) * dt
    lifecycle_pvf = present_value_factor(finance.lifecycle_years, finance.discount_rate)
    depreciation_pvf = present_value_factor(finance.depreciation_years, finance.discount_rate)
    salvage_discount_factor = (1.0 + finance.discount_rate) ** finance.lifecycle_years

    # ── 变量布局：0..5 为六个容量，随后每时段一个 stride 长度的块 ──
    stride_items = (
        ["gl", "gs"]
        + (["gse"] if grid else [])
        + ["gc", "st", "soc"]
        + (["un"] if not grid else [])
        + (["dl"] if diesel_enabled else [])
        + (["bo", "bl"] if biomass_enabled else [])
        + (["bse"] if (biomass_enabled and grid) else [])
        + (["gimp"] if grid else [])
    )
    stride = len(stride_items)
    offset_of = {name: index for index, name in enumerate(stride_items)}
    base = 6
    num_vars = base + horizon * stride

    # 持续运行模式（v4.1）追加变量：布局上排在既有变量之后（旧布局与历史
    # 版本逐位一致）。仅逐时弃电 bc_t（必发富余通道）；检修窗不引入变量
    # （固定窗以约束表达）。
    extra_curtail_base = num_vars
    total_vars = extra_curtail_base + (horizon if biomass_continuous else 0)

    def curt(t: int) -> int:
        return extra_curtail_base + t

    def vi(item: str, t: int) -> int:
        return base + t * stride + offset_of[item]

    lower = np.zeros(total_vars)
    upper = np.full(total_vars, np.inf)
    lower[0], upper[0] = 0.0, bounds.wind_capacity_kw_max
    lower[1], upper[1] = 0.0, bounds.pv_capacity_kw_max
    lower[2], upper[2] = 0.0, bounds.ess_energy_kwh_max
    lower[3], upper[3] = 0.0, bounds.ess_power_kw_max
    lower[4], upper[4] = (diesel.min_capacity_kw, diesel.max_capacity_kw) if diesel_enabled else (0.0, 0.0)
    lower[5], upper[5] = (biomass.min_capacity_kw, biomass.max_capacity_kw) if biomass_enabled else (0.0, 0.0)
    if grid:
        for t in range(horizon):
            upper[vi("gse", t)] = bounds.grid_export_kw_max
            upper[vi("gimp", t)] = bounds.grid_import_kw_max
        if biomass_enabled:
            for t in range(horizon):
                upper[vi("bse", t)] = bounds.grid_export_kw_max
    # 全部变量连续（v4.1：检修窗固定后模型为纯线性，无整数变量）。

    # ── 目标：全生命周期 NPV（投资+运维+燃料+购电-售电-残值-税盾） ──
    salvage_ratio = finance.salvage_rate / salvage_discount_factor
    tax_shield_ratio = (
        finance.income_tax_rate * (1.0 - finance.salvage_rate) / finance.depreciation_years * depreciation_pvf
    )
    investment_factor = 1.0 - salvage_ratio - tax_shield_ratio
    objective = np.zeros(total_vars)
    objective[0] = costs.wind_capex_per_kw * investment_factor + lifecycle_pvf * costs.wind_om_per_kw_year
    objective[1] = costs.pv_capex_per_kw * investment_factor + lifecycle_pvf * costs.pv_om_per_kw_year
    objective[2] = costs.ess_energy_capex_per_kwh * investment_factor + lifecycle_pvf * costs.ess_energy_om_per_kwh_year
    objective[3] = costs.ess_power_capex_per_kw * investment_factor + lifecycle_pvf * costs.ess_power_om_per_kw_year
    if diesel_enabled:
        objective[4] = diesel.capex_per_kw * investment_factor + lifecycle_pvf * diesel.fixed_om_per_kw_year
    if biomass_enabled:
        objective[5] = biomass.capex_per_kw * investment_factor + lifecycle_pvf * biomass.fixed_om_per_kw_year
    for t in range(horizon):
        if grid:
            objective[vi("gimp", t)] = lifecycle_pvf * buy_price[t] * dt
            objective[vi("gse", t)] = -lifecycle_pvf * sell_price[t] * dt
            if biomass_enabled:
                objective[vi("bse", t)] = -lifecycle_pvf * sell_price[t] * dt
        else:
            objective[vi("un", t)] = lifecycle_pvf * project.loss_of_load_penalty_per_kwh * dt
        if diesel_enabled:
            objective[vi("dl", t)] = lifecycle_pvf * diesel.fuel_cost_per_kwh * dt
        if biomass_enabled:
            objective[vi("bo", t)] = lifecycle_pvf * biomass.fuel_cost_per_kwh * dt

    # ── 约束（稀疏 COO 累积） ──
    eq_rows: list[int] = []
    eq_cols: list[int] = []
    eq_vals: list[float] = []
    eq_rhs: list[float] = []
    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_vals: list[float] = []
    ub_rhs: list[float] = []
    eq_count = [0]
    ub_count = [0]

    def add_eq(entries, rhs: float) -> None:
        for col, value in entries:
            eq_rows.append(eq_count[0])
            eq_cols.append(col)
            eq_vals.append(value)
        eq_rhs.append(rhs)
        eq_count[0] += 1

    def add_le(entries, rhs: float) -> None:
        for col, value in entries:
            ub_rows.append(ub_count[0])
            ub_cols.append(col)
            ub_vals.append(value)
        ub_rhs.append(rhs)
        ub_count[0] += 1

    for t in range(horizon):
        # 绿电平衡：风+光出力 = 直供 + 充储 + 弃电 + 上网（并网含上网）。
        entries = [
            (0, wind_profile[t]),
            (1, pv_profile[t]),
            (vi("gl", t), -1.0),
            (vi("gs", t), -1.0),
            (vi("gc", t), -1.0),
        ]
        if grid:
            entries.append((vi("gse", t), -1.0))
        add_eq(entries, 0.0)
        # 负荷平衡：绿电直供 + 储能放电 + 购电/失负荷 + 柴油 + 生物质直供 = 负荷。
        entries = [(vi("gl", t), 1.0), (vi("st", t), 1.0)]
        if grid:
            entries.append((vi("gimp", t), 1.0))
        else:
            entries.append((vi("un", t), 1.0))
        if diesel_enabled:
            entries.append((vi("dl", t), 1.0))
        if biomass_enabled:
            entries.append((vi("bl", t), 1.0))
        add_eq(entries, load[t])
        # 生物质平衡：出力 = 直供 + 上网（并网）+ 弃电（持续运行模式）。
        if biomass_enabled:
            entries = [(vi("bo", t), 1.0), (vi("bl", t), -1.0)]
            if grid:
                entries.append((vi("bse", t), -1.0))
            if biomass_continuous:
                entries.append((curt(t), -1.0))
            add_eq(entries, 0.0)
        # 功率界。
        add_le([(vi("gs", t), 1.0), (3, -1.0)], 0.0)
        add_le([(vi("st", t), 1.0), (3, -1.0)], 0.0)
        if diesel_enabled:
            add_le([(vi("dl", t), 1.0), (4, -1.0)], 0.0)
        if biomass_enabled:
            add_le([(vi("bo", t), 1.0), (5, -biomass.capacity_factor)], 0.0)
            if biomass_maint_hours > 0 and t in maintenance_hour_set:
                # 检修联动（v4.1 固定窗）：窗内出力强制为 0（等式，纯线性）。
                add_eq([(vi("bo", t), 1.0)], 0.0)
            elif biomass_must_run:
                # 持续运行下限（纯线性）：出力 ≥ 最小出力比例 × 装机。
                add_le([(5, biomass.min_output_ratio), (vi("bo", t), -1.0)], 0.0)
        # SOC 循环递推。
        previous = horizon - 1 if t == 0 else t - 1
        add_eq(
            [
                (vi("soc", t), 1.0),
                (vi("soc", previous), -1.0),
                (vi("gs", t), -storage.charge_efficiency * dt),
                (vi("st", t), dt / storage.discharge_efficiency),
            ],
            0.0,
        )
        add_le([(2, storage.soc_min_ratio), (vi("soc", t), -1.0)], 0.0)
        add_le([(vi("soc", t), 1.0), (2, -storage.soc_max_ratio)], 0.0)
        # 各去向不超过负荷。
        add_le([(vi("gl", t), 1.0)], load[t])
        add_le([(vi("st", t), 1.0)], load[t])
        if grid:
            add_le([(vi("gimp", t), 1.0)], load[t])
            if biomass_enabled:
                # 并网通道合计上限：绿电与生物质上网共用一条线路。
                add_le([(vi("gse", t), 1.0), (vi("bse", t), 1.0)], bounds.grid_export_kw_max)
    # 储能时长界。
    add_le([(3, storage.min_storage_hours), (2, -1.0)], 0.0)
    add_le([(2, 1.0), (3, -storage.max_storage_hours)], 0.0)
    # 生物质年能量上限。
    if biomass_enabled and biomass.max_annual_energy_kwh is not None:
        add_le([(vi("bo", t), dt) for t in range(horizon)], biomass.max_annual_energy_kwh)
    # 检修窗约束（v4.1）：已在逐时约束中以固定窗内出力为零表达，无需额外
    # 约束块（历史版本此处的起始日整数约束与可用容量联动已随两阶段定窗
    # 移除）。
    # 政策：绿电自用率下限。
    entries = []
    for t in range(horizon):
        entries.append((0, policy.min_self_use_ratio_of_green * dt * wind_profile[t]))
        entries.append((1, policy.min_self_use_ratio_of_green * dt * pv_profile[t]))
        if biomass_enabled:
            entries.append((vi("bo", t), policy.min_self_use_ratio_of_green * dt))
        entries.append((vi("gl", t), -dt))
        entries.append((vi("st", t), -dt))
        if biomass_enabled:
            entries.append((vi("bl", t), -dt))
    add_le(entries, 0.0)
    # 政策：负荷绿电覆盖率下限。
    entries = []
    for t in range(horizon):
        entries.append((vi("gl", t), -dt))
        entries.append((vi("st", t), -dt))
        if biomass_enabled:
            entries.append((vi("bl", t), -dt))
    add_le(entries, -policy.min_self_use_ratio_of_load * total_load)
    # 政策：外售比例上限（并网）。
    if grid:
        entries = []
        for t in range(horizon):
            entries.append((vi("gse", t), dt))
            if biomass_enabled:
                entries.append((vi("bse", t), dt))
            entries.append((0, -policy.max_sell_ratio_of_green * dt * wind_profile[t]))
            entries.append((1, -policy.max_sell_ratio_of_green * dt * pv_profile[t]))
            if biomass_enabled:
                entries.append((vi("bo", t), -policy.max_sell_ratio_of_green * dt))
        add_le(entries, 0.0)
    # 离网失负荷率上限。
    if not grid and project.max_loss_ratio_of_load is not None:
        add_le([(vi("un", t), dt) for t in range(horizon)], project.max_loss_ratio_of_load * total_load)

    matrix_eq = coo_matrix((eq_vals, (eq_rows, eq_cols)), shape=(eq_count[0], total_vars)).tocsr()
    matrix_ub = coo_matrix((ub_vals, (ub_rows, ub_cols)), shape=(ub_count[0], total_vars)).tocsr()

    try:
        result = linprog(
            objective,
            A_ub=matrix_ub,
            b_ub=np.array(ub_rhs),
            A_eq=matrix_eq,
            b_eq=np.array(eq_rhs),
            bounds=list(zip(lower, upper)),
            method="highs",
        )
    except Exception as exc:  # noqa: BLE001 - 不透传底层报错文本
        raise RuntimeError("备选求解引擎执行失败，请检查数据与配置后重试。") from exc

    status = (
        STATUS_OPTIMAL
        if result.status == 0 and result.success
        else _LINPROG_STATUS_TO_CODE.get(result.status, STATUS_UNKNOWN)
    )
    if status != STATUS_OPTIMAL:
        status_name = SOLVER_STATUS_NAMES.get(status, "UNKNOWN")
        raise RuntimeError(f"优化未得到可用解（备选引擎状态：{status_name}）。")

    x = result.x
    wind_capacity = float(x[0])
    pv_capacity = float(x[1])
    ess_energy = float(x[2])
    ess_power = float(x[3])
    diesel_capacity = float(x[4]) if diesel_enabled else 0.0
    biomass_capacity = float(x[5]) if biomass_enabled else 0.0

    def series(item: str) -> list[float]:
        return [float(x[vi(item, t)]) for t in range(horizon)]

    green_to_load = series("gl")
    green_to_storage = series("gs")
    green_curtail = series("gc")
    storage_to_load = series("st")
    soc = series("soc")
    green_to_sell = series("gse") if grid else [0.0] * horizon
    grid_to_load = series("gimp") if grid else [0.0] * horizon
    unmet_load = series("un") if not grid else [0.0] * horizon
    diesel_to_load = series("dl") if diesel_enabled else [0.0] * horizon
    biomass_output = series("bo") if biomass_enabled else [0.0] * horizon
    biomass_to_load = series("bl") if biomass_enabled else [0.0] * horizon
    biomass_to_sell = series("bse") if (biomass_enabled and grid) else [0.0] * horizon
    biomass_curtail_series = (
        [float(x[curt(t)]) for t in range(horizon)] if biomass_continuous else [0.0] * horizon
    )

    # 检修窗结果提取（v4.1）：起始小时即两阶段定窗选定的固定窗（不从变量
    # 读取——模型中已无检修变量），落盘检修标记供校验器复核。
    maintenance_flag = None
    maintenance_window = None
    if biomass_maint_hours > 0:
        start_hour = int(fixed_maintenance_start)
        maintenance_flag = [
            1.0 if ((t - start_hour) % horizon) < biomass_maint_hours else 0.0
            for t in range(horizon)
        ]
        maintenance_window = {"start_hour": start_hour, "hours": biomass_maint_hours}

    # ── 指标口径与主引擎逐项一致（校验器会从 CSV 独立复算把关） ──
    initial_investment_cost = (
        costs.wind_capex_per_kw * wind_capacity
        + costs.pv_capex_per_kw * pv_capacity
        + costs.ess_energy_capex_per_kwh * ess_energy
        + costs.ess_power_capex_per_kw * ess_power
    )
    annual_om_cost = (
        costs.wind_om_per_kw_year * wind_capacity
        + costs.pv_om_per_kw_year * pv_capacity
        + costs.ess_energy_om_per_kwh_year * ess_energy
        + costs.ess_power_om_per_kw_year * ess_power
    )
    if diesel_enabled:
        initial_investment_cost += diesel.capex_per_kw * diesel_capacity
        annual_om_cost += diesel.fixed_om_per_kw_year * diesel_capacity
    if biomass_enabled:
        initial_investment_cost += biomass.capex_per_kw * biomass_capacity
        annual_om_cost += biomass.fixed_om_per_kw_year * biomass_capacity

    annual_buy_cost = sum(grid_to_load[t] * buy_price[t] * dt for t in range(horizon))
    annual_sell_revenue = sum(
        (green_to_sell[t] + biomass_to_sell[t]) * sell_price[t] * dt for t in range(horizon)
    )
    annual_unmet_penalty_cost = sum(
        unmet_load[t] * project.loss_of_load_penalty_per_kwh * dt for t in range(horizon)
    )
    annual_diesel_fuel_cost = (
        sum(diesel_to_load[t] * diesel.fuel_cost_per_kwh * dt for t in range(horizon))
        if diesel_enabled
        else 0.0
    )
    annual_biomass_fuel_cost = (
        sum(biomass_output[t] * biomass.fuel_cost_per_kwh * dt for t in range(horizon))
        if biomass_enabled
        else 0.0
    )

    om_cost_npv = annual_om_cost * lifecycle_pvf
    buy_cost_npv = annual_buy_cost * lifecycle_pvf
    sell_revenue_npv = annual_sell_revenue * lifecycle_pvf
    unmet_penalty_npv = annual_unmet_penalty_cost * lifecycle_pvf
    diesel_fuel_cost_npv = annual_diesel_fuel_cost * lifecycle_pvf
    biomass_fuel_cost_npv = annual_biomass_fuel_cost * lifecycle_pvf
    salvage_value_npv = (
        initial_investment_cost * finance.salvage_rate / salvage_discount_factor
    )
    tax_shield_npv = (
        initial_investment_cost
        * finance.income_tax_rate
        * (1.0 - finance.salvage_rate)
        / finance.depreciation_years
        * depreciation_pvf
    )

    total_green = (
        sum(wind_profile[t] * wind_capacity + pv_profile[t] * pv_capacity for t in range(horizon))
        + sum(biomass_output[t] for t in range(horizon))
    ) * dt
    total_self_use = (
        sum(green_to_load[t] + storage_to_load[t] + biomass_to_load[t] for t in range(horizon)) * dt
    )
    total_sell = sum(green_to_sell[t] + biomass_to_sell[t] for t in range(horizon)) * dt
    total_unmet = sum(unmet_load[t] for t in range(horizon)) * dt
    total_diesel = sum(diesel_to_load[t] for t in range(horizon)) * dt
    total_biomass = sum(biomass_output[t] for t in range(horizon)) * dt

    # 边界触顶提示（v4.1）：与主引擎同一判定口径（相对容差 1e-6），建议性
    # 质，不改变结果与校验结论。
    boundary_notes: list[str] = []

    def _at_bound(value: float, bound: float) -> bool:
        return abs(value - bound) <= 1.0e-6 * max(1.0, abs(bound))

    if bounds.wind_capacity_kw_max > 0.0 and _at_bound(wind_capacity, bounds.wind_capacity_kw_max):
        boundary_notes.append(
            f"风电装机 {wind_capacity:.1f} kW 达到配置上限 {bounds.wind_capacity_kw_max:g} kW，扩容空间受边界限制"
        )
    if bounds.pv_capacity_kw_max > 0.0 and _at_bound(pv_capacity, bounds.pv_capacity_kw_max):
        boundary_notes.append(
            f"光伏装机 {pv_capacity:.1f} kW 达到配置上限 {bounds.pv_capacity_kw_max:g} kW，扩容空间受边界限制"
        )
    if bounds.ess_energy_kwh_max > 0.0 and _at_bound(ess_energy, bounds.ess_energy_kwh_max):
        boundary_notes.append(
            f"储能容量 {ess_energy:.1f} kWh 达到配置上限 {bounds.ess_energy_kwh_max:g} kWh，扩容空间受边界限制"
        )
    if bounds.ess_power_kw_max > 0.0 and _at_bound(ess_power, bounds.ess_power_kw_max):
        boundary_notes.append(
            f"储能功率 {ess_power:.1f} kW 达到配置上限 {bounds.ess_power_kw_max:g} kW，扩容空间受边界限制"
        )
    if diesel_enabled:
        if diesel.max_capacity_kw > 0.0 and _at_bound(diesel_capacity, diesel.max_capacity_kw):
            boundary_notes.append(
                f"柴油装机 {diesel_capacity:.1f} kW 达到配置上限 {diesel.max_capacity_kw:g} kW，扩容空间受边界限制"
            )
        if diesel.min_capacity_kw > 0.0 and _at_bound(diesel_capacity, diesel.min_capacity_kw):
            boundary_notes.append(
                f"柴油装机被配置最小容量 {diesel.min_capacity_kw:g} kW 托底，结果含强制投资成分"
            )
    if biomass_enabled:
        if biomass.max_capacity_kw > 0.0 and _at_bound(biomass_capacity, biomass.max_capacity_kw):
            boundary_notes.append(
                f"生物质装机 {biomass_capacity:.1f} kW 达到配置上限 {biomass.max_capacity_kw:g} kW，扩容空间受边界限制"
            )
        if biomass.min_capacity_kw > 0.0 and _at_bound(biomass_capacity, biomass.min_capacity_kw):
            boundary_notes.append(
                f"生物质装机被配置最小容量 {biomass.min_capacity_kw:g} kW 托底，结果含强制投资成分"
            )
        if biomass.max_annual_energy_kwh is not None:
            energy_cap = float(biomass.max_annual_energy_kwh)
            energy_used = sum(biomass_output[t] * dt for t in range(horizon))
            if energy_used >= energy_cap - max(1.0, 1.0e-6 * energy_cap):
                boundary_notes.append(
                    f"生物质年发电量 {energy_used:.0f} kWh 达到燃料年可用量上限 {energy_cap:g} kWh，发电空间受燃料供应限制"
                )

    output_path = Path(output_dir) if output_dir is not None else Path("outputs")
    hourly_csv_path = output_path / "green_direct_hourly_results.csv"
    summary_csv_path = output_path / "green_direct_summary_results.csv"
    excel_path: Path | None = None

    if write_outputs:
        output_path.mkdir(parents=True, exist_ok=True)
        hourly_csv_path, summary_csv_path, excel_path = export_results_to_csv(
            output_dir=output_path,
            input_path=Path(data_path),
            price_path=Path(price_path) if price_path is not None else None,
            df=df,
            buy_price=buy_price,
            sell_price=sell_price,
            dt=dt,
            p_wind=_SolutionValue(wind_capacity),
            p_pv=_SolutionValue(pv_capacity),
            e_ess=_SolutionValue(ess_energy),
            p_ess=_SolutionValue(ess_power),
            green_to_load={t: _SolutionValue(green_to_load[t]) for t in range(horizon)},
            green_to_storage={t: _SolutionValue(green_to_storage[t]) for t in range(horizon)},
            green_to_sell={t: _SolutionValue(green_to_sell[t]) for t in range(horizon)} if grid else None,
            green_curtail={t: _SolutionValue(green_curtail[t]) for t in range(horizon)},
            grid_to_load={t: _SolutionValue(grid_to_load[t]) for t in range(horizon)} if grid else None,
            unmet_load={t: _SolutionValue(unmet_load[t]) for t in range(horizon)} if not grid else None,
            storage_to_load={t: _SolutionValue(storage_to_load[t]) for t in range(horizon)},
            soc={t: _SolutionValue(soc[t]) for t in range(horizon)},
            diesel_to_load={t: _SolutionValue(diesel_to_load[t]) for t in range(horizon)} if diesel_enabled else None,
            biomass_output={t: _SolutionValue(biomass_output[t]) for t in range(horizon)} if biomass_enabled else None,
            biomass_to_load={t: _SolutionValue(biomass_to_load[t]) for t in range(horizon)} if biomass_enabled else None,
            biomass_to_sell={t: _SolutionValue(biomass_to_sell[t]) for t in range(horizon)} if (biomass_enabled and grid) else None,
            biomass_curtail={t: _SolutionValue(biomass_curtail_series[t]) for t in range(horizon)} if biomass_continuous else None,
            maintenance_flag=maintenance_flag,
            maintenance_hours=biomass_maint_hours if biomass_maint_hours > 0 else 0,
            maintenance_start_hour=(
                maintenance_window["start_hour"] if maintenance_window is not None else -1
            ),
            diesel_capacity=diesel_capacity,
            biomass_capacity=biomass_capacity,
            annual_diesel_fuel_cost=annual_diesel_fuel_cost,
            annual_biomass_fuel_cost=annual_biomass_fuel_cost,
            diesel_fuel_cost_npv=diesel_fuel_cost_npv,
            biomass_fuel_cost_npv=biomass_fuel_cost_npv,
            boundary_notes=boundary_notes,
            solver_mode=config.solver.mode,
            component_bounds=build_component_bounds(
                bounds, diesel, biomass, diesel_enabled, biomass_enabled
            ),
            objective_value=float(result.fun),
            initial_investment_cost=initial_investment_cost,
            annual_om_cost=annual_om_cost,
            annual_buy_cost=annual_buy_cost,
            annual_sell_revenue=annual_sell_revenue,
            annual_unmet_penalty_cost=annual_unmet_penalty_cost,
            om_cost_npv=om_cost_npv,
            buy_cost_npv=buy_cost_npv,
            sell_revenue_npv=sell_revenue_npv,
            salvage_value_npv=salvage_value_npv,
            tax_shield_npv=tax_shield_npv,
            discount_rate=finance.discount_rate,
            lifecycle_years=finance.lifecycle_years,
            depreciation_years=finance.depreciation_years,
            income_tax_rate=finance.income_tax_rate,
            salvage_rate=finance.salvage_rate,
            project_type=project_type,
        )

    return SolveResult(
        status=status,
        objective_value=float(result.fun),
        hourly_csv_path=hourly_csv_path,
        summary_csv_path=summary_csv_path,
        installed_capacities={
            "wind_capacity_kw": wind_capacity,
            "pv_capacity_kw": pv_capacity,
            "ess_energy_kwh": ess_energy,
            "ess_power_kw": ess_power,
            "diesel_capacity_kw": diesel_capacity,
            "biomass_capacity_kw": biomass_capacity,
        },
        economic_metrics={
            "initial_investment_cost": initial_investment_cost,
            "annual_om_cost": annual_om_cost,
            "annual_buy_cost": annual_buy_cost,
            "annual_sell_revenue": annual_sell_revenue,
            "annual_unmet_penalty_cost": annual_unmet_penalty_cost,
            "annual_diesel_fuel_cost": annual_diesel_fuel_cost,
            "annual_biomass_fuel_cost": annual_biomass_fuel_cost,
            "om_cost_npv": om_cost_npv,
            "buy_cost_npv": buy_cost_npv,
            "sell_revenue_npv": sell_revenue_npv,
            "unmet_penalty_npv": unmet_penalty_npv,
            "diesel_fuel_cost_npv": diesel_fuel_cost_npv,
            "biomass_fuel_cost_npv": biomass_fuel_cost_npv,
            "salvage_value_npv": salvage_value_npv,
            "tax_shield_npv": tax_shield_npv,
        },
        ratio_metrics={
            "self_use_ratio_of_green": total_self_use / total_green if total_green > 1.0e-9 else 0.0,
            "self_use_ratio_of_load": total_self_use / total_load if total_load > 1.0e-9 else 0.0,
            "sell_ratio_of_green": total_sell / total_green if total_green > 1.0e-9 else 0.0,
            "loss_ratio_of_load": total_unmet / total_load if total_load > 1.0e-9 else 0.0,
            "biomass_ratio_of_green": total_biomass / total_green if total_green > 1.0e-9 else 0.0,
            "diesel_ratio_of_load": total_diesel / total_load if total_load > 1.0e-9 else 0.0,
        },
        config=asdict(config),
        project_type=project_type,
        maintenance_window=maintenance_window,
        boundary_notes=tuple(boundary_notes),
        excel_path=excel_path,
    )
