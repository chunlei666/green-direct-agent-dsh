from __future__ import annotations

import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path

try:  # 主引擎求解器组件为可选依赖：缺失时备选引擎（天璇）仍可完整工作。
    from mindoptpy import MDO, Model, quicksum

    MINDOPT_AVAILABLE = True
except Exception:  # pragma: no cover - 依赖缺失场景
    MDO = None  # type: ignore[assignment]
    Model = None  # type: ignore[assignment]
    quicksum = None  # type: ignore[assignment]
    MINDOPT_AVAILABLE = False

from .config import OptimizationConfig
from .excel_report import build_component_bounds
from .io_utils import (
    export_results_to_csv,
    load_price_data,
    load_profile_data,
    read_hourly_biomass_series,
    select_maintenance_window,
)

GRID_CONNECTED = "grid_connected"
OFFGRID = "offgrid"
PROJECT_TYPES = {GRID_CONNECTED, OFFGRID}

# 求解状态的通用名称映射（对外不暴露求解器品牌，仅报告通用优化状态）。
# 状态码与主引擎求解器保持一致（OPTIMAL=1 体系）；组件缺失时用同一套
# 字面量，保证备选引擎与状态命名不依赖该组件。
_MDO_STATUS_CODES = (
    (1, "OPTIMAL"),
    (2, "INFEASIBLE"),
    (3, "UNBOUNDED"),
    (4, "INF_OR_UBD"),
    (0, "UNKNOWN"),
)
STATUS_OPTIMAL = MDO.OPTIMAL if MINDOPT_AVAILABLE else 1
STATUS_INFEASIBLE = MDO.INFEASIBLE if MINDOPT_AVAILABLE else 2
STATUS_UNBOUNDED = MDO.UNBOUNDED if MINDOPT_AVAILABLE else 3
STATUS_INF_OR_UBD = MDO.INF_OR_UBD if MINDOPT_AVAILABLE else 4
STATUS_UNKNOWN = MDO.UNKNOWN if MINDOPT_AVAILABLE else 0
SOLVER_STATUS_NAMES: dict[int, str] = dict(_MDO_STATUS_CODES)

# 主引擎组件缺失时的业务口径错误（不透传底层信息）。
PRIMARY_UNAVAILABLE_MESSAGE = (
    "天枢引擎环境未就绪：缺少求解器组件。请先完成求解器环境安装与许可配置"
    "（运行 ./agent_tools/gd doctor 自检），或在本次求解中改用天璇引擎"
    "（--solver alternate / 配置 solver.mode=alternate）。"
)


@dataclass(frozen=True)
class SolveResult:
    status: int
    objective_value: float
    hourly_csv_path: Path
    summary_csv_path: Path
    installed_capacities: dict[str, float]
    economic_metrics: dict[str, float]
    ratio_metrics: dict[str, float]
    config: dict
    project_type: str = GRID_CONNECTED
    # 双擎互证模式的交叉核对摘要（两引擎目标值与一致性）；单引擎模式为 None。
    cross_check: dict | None = None
    # 持续运行模式（v4.1）：两阶段定窗自动选择的生物质检修窗。
    # {"start_hour": 起始小时(0 起), "hours": 窗口小时数}；未启用检修时为 None。
    maintenance_window: dict | None = None
    # 边界触顶提示（v4.1）：决策量贴住配置边界时的建议性说明（不改变结果
    # 与校验结论），用于向用户明示"优化结果受边界限制"。
    boundary_notes: tuple[str, ...] = ()
    # 成果工作簿（v4.2）：面向用户的 Excel 交付物路径；写簿失败时为 None
    # （CSV 通道不受影响）。
    excel_path: Path | None = None
    # 两阶段定窗的预解（不检修）目标值（v4.3）：双擎互证在预解层做严格
    # 比对（该模型目标值唯一，是建模一致性的真正关卡）；单引擎模式为 None。
    stage_a_objective: float | None = None
    # 引擎降级附注（v4.4）：主引擎组件缺失导致自动改用备选引擎时，向用户
    # 明示实际使用的引擎；正常路径为 None。
    engine_fallback_note: str | None = None


def present_value_factor(years: int, discount_rate: float) -> float:
    if years <= 0:
        return 0.0
    if abs(discount_rate) <= 1.0e-12:
        return float(years)
    return (1.0 - (1.0 + discount_rate) ** (-years)) / discount_rate


def build_and_solve_model(
    data_path: str,
    price_path: str | None = None,
    output_dir: str | None = None,
    config: OptimizationConfig | None = None,
) -> SolveResult:
    """按配置的求解引擎模式调度：天枢（默认）/ 天璇（备选）/ 双擎互证。"""
    config = config or OptimizationConfig()
    mode = config.solver.mode
    if mode == "alternate":
        from .solver_highs import build_and_solve_model_alternate

        return build_and_solve_model_alternate(data_path, price_path, output_dir, config)
    if mode == "dual":
        from .solver_highs import build_and_solve_model_alternate

        return _solve_dual(data_path, price_path, output_dir, config, build_and_solve_model_alternate)
    if not MINDOPT_AVAILABLE:
        # 主引擎组件缺失（未安装或未配置许可）：自动降级为天璇引擎完成本次
        # 求解，并在载荷中明示，保证开箱可用；需要双擎互证时先补齐环境。
        from .solver_highs import build_and_solve_model_alternate

        result = build_and_solve_model_alternate(data_path, price_path, output_dir, config)
        return replace(
            result,
            engine_fallback_note=(
                "天枢引擎环境未就绪（缺少求解器组件或许可），本次已自动改用天璇引擎完成求解；"
                "结果经完整校验后同样可用。如需双擎互证，请先完成天枢环境安装与许可配置"
                "（运行 ./agent_tools/gd doctor 自检）。"
            ),
        )
    return _solve_primary(data_path, price_path, output_dir, config)


_DUAL_OBJECTIVE_REL_TOLERANCE = 1.0e-6
_DUAL_CAPACITY_REL_TOLERANCE = 1.0e-3


def _solve_dual(
    data_path: str,
    price_path: str | None,
    output_dir: str | None,
    config: OptimizationConfig,
    alternate_builder,
) -> SolveResult:
    """双擎互证：天枢先求解（不可行/无解时与单引擎口径完全一致，用户直接
    获得业务归因）；天枢最优后天璇独立复核——天璇任何失败都转为互证不
    一致，两引擎目标值超出容差即判结果不可信（RuntimeError）。一致时采
    用天枢方案；装机组合差异（多重最优解）仅作说明性附注。持续运行模式
    下两引擎各自以本引擎完成完整两阶段（预解、定窗、重解的求解器一致），
    互证分层进行：预解（不检修）目标值唯一，严格比对——这是建模一致性
    的真正关卡；最终目标值在两引擎选窗相同时严格比对，选窗不同（多重最
    优使预解出力画像不同）时如实附注并以主引擎检修窗为准。"""
    primary = _solve_primary(data_path, price_path, output_dir, config)
    try:
        alternate = alternate_builder(
            data_path,
            price_path,
            None,
            config,
            write_outputs=False,
        )
    except Exception as exc:  # noqa: BLE001 - 统一转为互证口径，不透传底层报错
        raise RuntimeError(
            "双擎互证不一致：主引擎已求得最优解，而备选引擎未能求解，"
            "本次结果不可信；请改用单一引擎模式（天枢/天璇）重试。"
        ) from exc
    scale = max(abs(primary.objective_value), 1.0)
    relative_difference = abs(primary.objective_value - alternate.objective_value) / scale
    cross_check = {
        "engines": 2,
        "consistent": True,
        "objective_primary": primary.objective_value,
        "objective_alternate": alternate.objective_value,
        "relative_difference": relative_difference,
    }
    # 预解层严格互证（v4.3）：持续运行模式下两引擎各自两阶段定窗，预解
    # （不检修）模型的目标值唯一，其一致才是建模一致性的真正关卡；预解
    # 不一致直接判结果不可信。
    if primary.stage_a_objective is not None and alternate.stage_a_objective is not None:
        stage_a_scale = max(abs(primary.stage_a_objective), 1.0)
        stage_a_relative = (
            abs(primary.stage_a_objective - alternate.stage_a_objective) / stage_a_scale
        )
        cross_check["stage_a_relative_difference"] = stage_a_relative
        if stage_a_relative > _DUAL_OBJECTIVE_REL_TOLERANCE:
            raise RuntimeError(
                "双擎互证不一致：两个独立求解引擎的结果差异超出容差"
                f"（相对差异 {stage_a_relative:.3e}），本次结果不可信；"
                "请检查数据与配置后重试，或改用单一引擎模式（天枢/天璇）。"
            )
    # 最终层互证：选窗相同（或无检修决策）时目标值必须严格一致；两引擎
    # 各自预解的多重最优可能使选窗不同，此时目标值差异属启发式选窗方差
    # 而非建模分歧，如实附注并以主引擎检修窗为准。
    windows_differ = (
        primary.maintenance_window is not None
        and alternate.maintenance_window is not None
        and primary.maintenance_window != alternate.maintenance_window
    )
    if relative_difference > _DUAL_OBJECTIVE_REL_TOLERANCE and not windows_differ:
        raise RuntimeError(
            "双擎互证不一致：两个独立求解引擎的最优目标值差异超出容差"
            f"（相对差异 {relative_difference:.3e}），本次结果不可信；"
            "请检查数据与配置后重试，或改用单一引擎模式（天枢/天璇）。"
        )
    capacity_names = [
        "wind_capacity_kw",
        "pv_capacity_kw",
        "ess_energy_kwh",
        "ess_power_kw",
        "diesel_capacity_kw",
        "biomass_capacity_kw",
    ]
    diverged = []
    for name in capacity_names:
        primary_value = primary.installed_capacities.get(name, 0.0)
        alternate_value = alternate.installed_capacities.get(name, 0.0)
        capacity_scale = max(abs(primary_value), abs(alternate_value), 1.0)
        if abs(primary_value - alternate_value) / capacity_scale > _DUAL_CAPACITY_REL_TOLERANCE:
            diverged.append(name)
    # 持续运行模式（v4.3）：两引擎各自两阶段定窗，多重最优可能使选窗不同；
    # 目标值一致时仅为说明性差异，以主引擎检修窗为准并如实附注。
    notes: list[str] = []
    if (
        primary.maintenance_window is not None
        and alternate.maintenance_window is not None
        and primary.maintenance_window != alternate.maintenance_window
    ):
        cross_check["maintenance_window_alternate"] = alternate.maintenance_window
        notes.append("两引擎各自选定的检修窗不同（多重最优解），已采用主引擎的检修窗")
    if diverged:
        notes.append(
            "两引擎最优目标一致但装机组合存在差异（存在多重最优解），已采用主引擎方案；差异项："
            + ", ".join(diverged)
        )
    if notes:
        cross_check["capacity_note"] = "；".join(notes)
    return replace(primary, cross_check=cross_check)


def _solve_primary(
    data_path: str,
    price_path: str | None = None,
    output_dir: str | None = None,
    config: OptimizationConfig | None = None,
    fixed_maintenance_start: int | None = None,
) -> SolveResult:
    config = config or OptimizationConfig()
    project_type = config.project.type
    if project_type not in PROJECT_TYPES:
        raise ValueError(
            f"未知项目类型: {project_type}。支持的类型: {', '.join(sorted(PROJECT_TYPES))}。"
        )

    input_path = Path(data_path)
    df = load_profile_data(input_path)
    load = df["Load"].astype(float).tolist()
    pv_profile = df["PV"].astype(float).tolist()
    wind_profile = df["Wind"].astype(float).tolist()

    time_steps = range(len(df))
    dt = config.timestep_hours

    if project_type == GRID_CONNECTED:
        if price_path is None:
            raise ValueError("并网项目必须提供电价文件（price_path）。")
        buy_price, sell_price = load_price_data(price_path, len(df))
    else:
        if price_path is None:
            buy_price = [0.0] * len(df)
            sell_price = [0.0] * len(df)
        else:
            # 离网项目电价文件仅作逐时结果记录参考，不参与经济计算。
            buy_price, sell_price = load_price_data(price_path, len(df))

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

    # 持续运行模式（v4.1 两阶段定窗）：生物质机组启停昂贵，启用后运行时段
    # 出力不得低于最小出力比例×装机；每年安排一个连续检修窗（窗口内出力为
    # 0），窗口位置由两阶段方法自动确定（见下方编排）。两者默认关闭（历史
    # 行为）。
    biomass_must_run = biomass_enabled and biomass.min_output_ratio > 0.0
    biomass_maint_hours = (
        int(round(biomass.maintenance_days * 24)) if biomass_enabled else 0
    )
    biomass_continuous = biomass_enabled and (biomass_must_run or biomass_maint_hours > 0)
    biomass_num_days = len(df) // 24
    if biomass_maint_hours > 0:
        if len(df) % 24 != 0 or biomass_num_days < 1:
            raise ValueError("时序长度须为整天数（8760h），才能按日粒度安排生物质检修窗。")
        if biomass_maint_hours >= len(df):
            raise ValueError("生物质检修时长不小于时序长度，无法求解。")

    # 检修窗两阶段定窗编排（v4.1，v4.3 明确两层求解器一致）：检修窗位置若
    # 与容量/调度联合优化（混合整数规划），线性松弛过弱导致求解困难且对求
    # 解器数值敏感。改为两阶段：①先按"不检修"预解 NPV 最优（纯线性，秒
    # 级）；②在预解方案上选"窗口内生物质出力之和最小"的连续时段为检修窗
    # （定窗规则两套引擎共用同一实现）；③以固定窗口重解 NPV 最优（纯线性，
    # 窗内出力直接置零，无任何整数变量）。预解与重解均由本引擎完成（两层
    # 求解器必须一致）。结果是近似最优（与联合优化精确解的差距经基准场景
    # 实测极小），换取求解速度与数值稳健。预解在临时目录落盘后即弃，不污
    # 染最终输出。
    if biomass_maint_hours > 0 and fixed_maintenance_start is None:
        stage_a_config = replace(
            config, biomass=replace(config.biomass, maintenance_days=0.0)
        )
        with tempfile.TemporaryDirectory() as stage_a_dir:
            stage_a = _solve_primary(data_path, price_path, stage_a_dir, stage_a_config)
            biomass_series = read_hourly_biomass_series(stage_a.hourly_csv_path)
            start_day = select_maintenance_window(
                biomass_series, len(biomass_series) // 24, biomass_maint_hours
            )
        result = _solve_primary(
            data_path,
            price_path,
            output_dir,
            config,
            fixed_maintenance_start=start_day * 24,
        )
        return replace(result, stage_a_objective=stage_a.objective_value)
    if biomass_maint_hours > 0:
        maintenance_hour_set = {
            (fixed_maintenance_start + k) % len(df) for k in range(biomass_maint_hours)
        }
    else:
        maintenance_hour_set = set()

    total_load = sum(load) * dt
    lifecycle_pvf = present_value_factor(finance.lifecycle_years, finance.discount_rate)
    depreciation_pvf = present_value_factor(finance.depreciation_years, finance.discount_rate)
    salvage_discount_factor = (1.0 + finance.discount_rate) ** finance.lifecycle_years

    if not MINDOPT_AVAILABLE:
        raise RuntimeError(PRIMARY_UNAVAILABLE_MESSAGE)
    model = Model("green_direct_supply_lp")
    model.ModelSense = MDO.MINIMIZE
    p_wind = model.addVar(0.0, bounds.wind_capacity_kw_max, 0.0, "C", "P_wind")
    p_pv = model.addVar(0.0, bounds.pv_capacity_kw_max, 0.0, "C", "P_pv")
    e_ess = model.addVar(0.0, bounds.ess_energy_kwh_max, 0.0, "C", "E_ess")
    p_ess = model.addVar(0.0, bounds.ess_power_kw_max, 0.0, "C", "P_ess")
    # 新组件（柴油/生物质）默认禁用：禁用时不创建任何变量，
    # 历史变量创建顺序保持不变（并网回归锚点依赖该顺序）。
    p_diesel = (
        model.addVar(diesel.min_capacity_kw, diesel.max_capacity_kw, 0.0, "C", "P_diesel")
        if diesel_enabled
        else None
    )
    p_biomass = (
        model.addVar(biomass.min_capacity_kw, biomass.max_capacity_kw, 0.0, "C", "P_biomass")
        if biomass_enabled
        else None
    )

    green_to_load = {}
    green_to_storage = {}
    green_to_sell = {}
    green_curtail = {}
    grid_to_load = {}
    unmet_load = {}
    storage_to_load = {}
    soc = {}
    diesel_to_load = {}
    biomass_output = {}
    biomass_to_load = {}
    biomass_to_sell = {}
    biomass_curtail = {}

    for t in time_steps:
        green_to_load[t] = model.addVar(0.0, float("inf"), 0.0, "C", f"green_to_load_{t}")
        green_to_storage[t] = model.addVar(
            0.0, float("inf"), 0.0, "C", f"green_to_storage_{t}"
        )
        if project_type == GRID_CONNECTED:
            # 与历史版本保持完全一致的变量创建顺序（并网回归锚点）。
            green_to_sell[t] = model.addVar(
                0.0, bounds.grid_export_kw_max, 0.0, "C", f"green_to_sell_{t}"
            )
        green_curtail[t] = model.addVar(0.0, float("inf"), 0.0, "C", f"green_curtail_{t}")
        if project_type == GRID_CONNECTED:
            grid_to_load[t] = model.addVar(
                0.0, bounds.grid_import_kw_max, 0.0, "C", f"grid_to_load_{t}"
            )
        storage_to_load[t] = model.addVar(
            0.0, float("inf"), 0.0, "C", f"storage_to_load_{t}"
        )
        soc[t] = model.addVar(0.0, float("inf"), 0.0, "C", f"soc_{t}")
        if project_type == OFFGRID:
            unmet_load[t] = model.addVar(0.0, float("inf"), 0.0, "C", f"unmet_load_{t}")
        # 新组件变量在既有变量之后追加（禁用时不创建，锚点不变）。
        if diesel_enabled:
            diesel_to_load[t] = model.addVar(
                0.0, float("inf"), 0.0, "C", f"diesel_to_load_{t}"
            )
        if biomass_enabled:
            biomass_output[t] = model.addVar(
                0.0, float("inf"), 0.0, "C", f"biomass_output_{t}"
            )
            biomass_to_load[t] = model.addVar(
                0.0, float("inf"), 0.0, "C", f"biomass_to_load_{t}"
            )
            if project_type == GRID_CONNECTED:
                biomass_to_sell[t] = model.addVar(
                    0.0, bounds.grid_export_kw_max, 0.0, "C", f"biomass_to_sell_{t}"
                )
            # 持续运行模式（v4）：必发富余的弃电通道（燃料照付，优化自然规避）。
            if biomass_continuous:
                biomass_curtail[t] = model.addVar(
                    0.0, float("inf"), 0.0, "C", f"biomass_curtail_{t}"
                )

    # 检修窗（v4.1）：不再创建任何变量——窗口位置由两阶段方法在模型之外
    # 确定（见上方编排），模型内仅以固定窗内出力上/下限直接表达。检修启用
    # 时模型仍不新增变量（历史变量布局与回归锚点完全不变）。

    initial_investment_expr = (
        costs.wind_capex_per_kw * p_wind
        + costs.pv_capex_per_kw * p_pv
        + costs.ess_energy_capex_per_kwh * e_ess
        + costs.ess_power_capex_per_kw * p_ess
    )
    annual_om_cost_expr = (
        costs.wind_om_per_kw_year * p_wind
        + costs.pv_om_per_kw_year * p_pv
        + costs.ess_energy_om_per_kwh_year * e_ess
        + costs.ess_power_om_per_kw_year * p_ess
    )
    # 新组件仅在启用时追加成本项（禁用时表达式与历史版本完全一致）。
    if diesel_enabled:
        initial_investment_expr = (
            initial_investment_expr + diesel.capex_per_kw * p_diesel
        )
        annual_om_cost_expr = (
            annual_om_cost_expr + diesel.fixed_om_per_kw_year * p_diesel
        )
    if biomass_enabled:
        initial_investment_expr = (
            initial_investment_expr + biomass.capex_per_kw * p_biomass
        )
        annual_om_cost_expr = (
            annual_om_cost_expr + biomass.fixed_om_per_kw_year * p_biomass
        )

    # 柴油/生物质燃料边际成本：按发电量计，计入年运营成本（NPV 口径进入目标）。
    annual_diesel_fuel_expr = (
        quicksum(diesel_to_load[t] * diesel.fuel_cost_per_kwh * dt for t in time_steps)
        if diesel_enabled
        else 0.0
    )
    annual_biomass_fuel_expr = (
        quicksum(biomass_output[t] * biomass.fuel_cost_per_kwh * dt for t in time_steps)
        if biomass_enabled
        else 0.0
    )

    if project_type == GRID_CONNECTED:
        annual_buy_cost_expr = quicksum(grid_to_load[t] * buy_price[t] * dt for t in time_steps)
        annual_sell_revenue_expr = quicksum(
            green_to_sell[t] * sell_price[t] * dt for t in time_steps
        )
        if biomass_enabled:
            # 并网模式下生物质富余电量可上网获得售电收益。
            annual_sell_revenue_expr = annual_sell_revenue_expr + quicksum(
                biomass_to_sell[t] * sell_price[t] * dt for t in time_steps
            )
        annual_unmet_penalty_expr = 0.0
    else:
        annual_buy_cost_expr = 0.0
        annual_sell_revenue_expr = 0.0
        annual_unmet_penalty_expr = quicksum(
            unmet_load[t] * project.loss_of_load_penalty_per_kwh * dt for t in time_steps
        )

    salvage_value_npv_expr = (
        finance.salvage_rate * initial_investment_expr / salvage_discount_factor
    )
    tax_shield_npv_expr = (
        finance.income_tax_rate
        * (1.0 - finance.salvage_rate)
        * initial_investment_expr
        / finance.depreciation_years
        * depreciation_pvf
    )

    # 统一目标：CAPEX + PVF×年运维 + PVF×年购电 - PVF×年售电 - 残值现值 - 折旧税盾现值；
    # 离网模式另加 PVF×年失负荷惩罚（购售电项为 0）。
    # 并网模式的表达式与历史版本完全一致（回归锚点）。
    objective_expr = (
        initial_investment_expr
        + lifecycle_pvf * annual_om_cost_expr
        + lifecycle_pvf * annual_buy_cost_expr
        - lifecycle_pvf * annual_sell_revenue_expr
        - salvage_value_npv_expr
        - tax_shield_npv_expr
    )
    if project_type == OFFGRID:
        objective_expr = objective_expr + lifecycle_pvf * annual_unmet_penalty_expr
    if diesel_enabled or biomass_enabled:
        objective_expr = objective_expr + lifecycle_pvf * (
            annual_diesel_fuel_expr + annual_biomass_fuel_expr
        )
    model.setObjective(objective_expr)

    for t in time_steps:
        green_generation = p_wind * wind_profile[t] + p_pv * pv_profile[t]

        if project_type == GRID_CONNECTED:
            model.addConstr(
                green_generation
                == green_to_load[t] + green_to_storage[t] + green_to_sell[t] + green_curtail[t],
                f"green_balance_{t}",
            )
            load_balance_expr = (
                green_to_load[t] + storage_to_load[t] + grid_to_load[t]
            )
        else:
            model.addConstr(
                green_generation
                == green_to_load[t] + green_to_storage[t] + green_curtail[t],
                f"green_balance_{t}",
            )
            load_balance_expr = (
                green_to_load[t] + storage_to_load[t] + unmet_load[t]
            )
        if diesel_enabled:
            load_balance_expr = load_balance_expr + diesel_to_load[t]
        if biomass_enabled:
            load_balance_expr = load_balance_expr + biomass_to_load[t]
        model.addConstr(load_balance_expr == load[t], f"load_balance_{t}")

        model.addConstr(green_to_load[t] <= load[t], f"green_to_load_limit_{t}")
        model.addConstr(storage_to_load[t] <= load[t], f"storage_to_load_limit_{t}")
        if project_type == GRID_CONNECTED:
            model.addConstr(grid_to_load[t] <= load[t], f"grid_to_load_limit_{t}")
        model.addConstr(green_to_storage[t] <= p_ess, f"charge_limit_{t}")
        model.addConstr(storage_to_load[t] <= p_ess, f"discharge_limit_{t}")
        # 柴油出力受装机上限约束（仅直供负荷）。
        if diesel_enabled:
            model.addConstr(diesel_to_load[t] <= p_diesel, f"diesel_capacity_limit_{t}")
        # 生物质出力受“装机×容量因子”上限约束，并按去向拆分（离网无上网）。
        if biomass_enabled:
            model.addConstr(
                biomass_output[t] <= p_biomass * biomass.capacity_factor,
                f"biomass_capacity_limit_{t}",
            )
            if biomass_maint_hours > 0:
                # 检修联动（v4.1 固定窗）：窗内出力强制为 0（等式，纯线性）；
                # 窗外按持续运行要求施加最小出力下限。
                if t in maintenance_hour_set:
                    model.addConstr(
                        biomass_output[t] == 0.0, f"biomass_maint_off_{t}"
                    )
                elif biomass_must_run:
                    model.addConstr(
                        biomass_output[t]
                        >= biomass.min_output_ratio * p_biomass,
                        f"biomass_min_output_{t}",
                    )
            elif biomass_must_run:
                # 持续运行下限（纯线性）：出力 ≥ 最小出力比例 × 装机。
                model.addConstr(
                    biomass_output[t] >= biomass.min_output_ratio * p_biomass,
                    f"biomass_min_output_{t}",
                )
            if project_type == GRID_CONNECTED:
                balance_expr = biomass_to_load[t] + biomass_to_sell[t]
                if biomass_continuous:
                    balance_expr = balance_expr + biomass_curtail[t]
                model.addConstr(
                    biomass_output[t] == balance_expr,
                    f"biomass_balance_{t}",
                )
                # 并网通道物理上限：绿电与生物质合计上网共用一条线路，
                # 逐时合计不得超过并网容量上限（两条售电通道不能各自打满）。
                model.addConstr(
                    green_to_sell[t] + biomass_to_sell[t] <= bounds.grid_export_kw_max,
                    f"combined_export_limit_{t}",
                )
            else:
                balance_expr = biomass_to_load[t]
                if biomass_continuous:
                    balance_expr = balance_expr + biomass_curtail[t]
                model.addConstr(
                    biomass_output[t] == balance_expr,
                    f"biomass_balance_{t}",
                )

    for t in time_steps:
        prev_t = time_steps[-1] if t == 0 else t - 1
        model.addConstr(
            soc[t]
            == soc[prev_t]
            + storage.charge_efficiency * green_to_storage[t] * dt
            - storage_to_load[t] * dt / storage.discharge_efficiency,
            f"soc_update_{t}",
        )

    for t in time_steps:
        model.addConstr(soc[t] >= storage.soc_min_ratio * e_ess, f"soc_min_{t}")
        model.addConstr(soc[t] <= storage.soc_max_ratio * e_ess, f"soc_max_{t}")

    model.addConstr(e_ess >= storage.min_storage_hours * p_ess, "storage_hour_min")
    model.addConstr(e_ess <= storage.max_storage_hours * p_ess, "storage_hour_max")

    # 生物质燃料年可用量上限（电量口径），仅在配置时生效。
    if biomass_enabled and biomass.max_annual_energy_kwh is not None:
        model.addConstr(
            quicksum(biomass_output[t] * dt for t in time_steps)
            <= biomass.max_annual_energy_kwh,
            "biomass_annual_energy_limit",
        )

    # 检修窗约束（v4.1）：已在逐时约束中以固定窗内出力为零表达，无需任何
    # 额外约束块（历史版本此处的起始日整数变量与可用容量联动已随两阶段
    # 定窗移除）。

    total_green_expr = quicksum(
        (p_wind * wind_profile[t] + p_pv * pv_profile[t]) * dt for t in time_steps
    )
    self_use_expr = quicksum((green_to_load[t] + storage_to_load[t]) * dt for t in time_steps)
    # 生物质计入绿电口径：发电量进绿电总量，直供电量进自用量；
    # 柴油为化石能源，不计入绿电口径。
    if biomass_enabled:
        total_green_expr = total_green_expr + quicksum(
            biomass_output[t] * dt for t in time_steps
        )
        self_use_expr = self_use_expr + quicksum(
            biomass_to_load[t] * dt for t in time_steps
        )

    model.addConstr(
        self_use_expr >= policy.min_self_use_ratio_of_green * total_green_expr,
        "min_self_use_ratio_of_green",
    )
    model.addConstr(
        self_use_expr >= policy.min_self_use_ratio_of_load * total_load,
        "min_self_use_ratio_of_load",
    )
    if project_type == GRID_CONNECTED:
        sell_expr = quicksum(green_to_sell[t] * dt for t in time_steps)
        if biomass_enabled:
            sell_expr = sell_expr + quicksum(biomass_to_sell[t] * dt for t in time_steps)
        model.addConstr(
            sell_expr <= policy.max_sell_ratio_of_green * total_green_expr,
            "max_sell_ratio_of_green",
        )
    elif project.max_loss_ratio_of_load is not None:
        unmet_expr = quicksum(unmet_load[t] * dt for t in time_steps)
        model.addConstr(
            unmet_expr <= project.max_loss_ratio_of_load * total_load,
            "max_loss_ratio_of_load",
        )

    model.optimize()

    try:
        objective_value = model.ObjVal
    except Exception as exc:
        status_name = SOLVER_STATUS_NAMES.get(model.Status, str(model.Status))
        raise RuntimeError(
            f"优化未得到可用解（状态：{status_name}）。"
        ) from exc

    initial_investment_cost = (
        costs.wind_capex_per_kw * p_wind.X
        + costs.pv_capex_per_kw * p_pv.X
        + costs.ess_energy_capex_per_kwh * e_ess.X
        + costs.ess_power_capex_per_kw * p_ess.X
    )
    annual_om_cost = (
        costs.wind_om_per_kw_year * p_wind.X
        + costs.pv_om_per_kw_year * p_pv.X
        + costs.ess_energy_om_per_kwh_year * e_ess.X
        + costs.ess_power_om_per_kw_year * p_ess.X
    )
    diesel_capacity = p_diesel.X if diesel_enabled else 0.0
    biomass_capacity = p_biomass.X if biomass_enabled else 0.0
    if diesel_enabled:
        initial_investment_cost += diesel.capex_per_kw * diesel_capacity
        annual_om_cost += diesel.fixed_om_per_kw_year * diesel_capacity
    if biomass_enabled:
        initial_investment_cost += biomass.capex_per_kw * biomass_capacity
        annual_om_cost += biomass.fixed_om_per_kw_year * biomass_capacity
    annual_diesel_fuel_cost = (
        sum(diesel_to_load[t].X * diesel.fuel_cost_per_kwh * dt for t in time_steps)
        if diesel_enabled
        else 0.0
    )
    annual_biomass_fuel_cost = (
        sum(biomass_output[t].X * biomass.fuel_cost_per_kwh * dt for t in time_steps)
        if biomass_enabled
        else 0.0
    )
    if project_type == GRID_CONNECTED:
        annual_buy_cost = sum(grid_to_load[t].X * buy_price[t] * dt for t in time_steps)
        annual_sell_revenue = sum(green_to_sell[t].X * sell_price[t] * dt for t in time_steps)
        if biomass_enabled:
            annual_sell_revenue += sum(
                biomass_to_sell[t].X * sell_price[t] * dt for t in time_steps
            )
        annual_unmet_penalty = 0.0
    else:
        annual_buy_cost = 0.0
        annual_sell_revenue = 0.0
        annual_unmet_penalty = sum(
            unmet_load[t].X * project.loss_of_load_penalty_per_kwh * dt for t in time_steps
        )
    om_cost_npv = annual_om_cost * lifecycle_pvf
    buy_cost_npv = annual_buy_cost * lifecycle_pvf
    sell_revenue_npv = annual_sell_revenue * lifecycle_pvf
    unmet_penalty_npv = annual_unmet_penalty * lifecycle_pvf
    diesel_fuel_cost_npv = annual_diesel_fuel_cost * lifecycle_pvf
    biomass_fuel_cost_npv = annual_biomass_fuel_cost * lifecycle_pvf
    salvage_value_npv = finance.salvage_rate * initial_investment_cost / salvage_discount_factor
    tax_shield_npv = (
        finance.income_tax_rate
        * (1.0 - finance.salvage_rate)
        * initial_investment_cost
        / finance.depreciation_years
        * depreciation_pvf
    )

    total_green = sum((p_wind.X * wind_profile[t] + p_pv.X * pv_profile[t]) * dt for t in time_steps)
    total_biomass = (
        sum(biomass_output[t].X * dt for t in time_steps) if biomass_enabled else 0.0
    )
    total_diesel = (
        sum(diesel_to_load[t].X * dt for t in time_steps) if diesel_enabled else 0.0
    )
    total_green += total_biomass
    total_self_use = sum((green_to_load[t].X + storage_to_load[t].X) * dt for t in time_steps)
    if biomass_enabled:
        total_self_use += sum(biomass_to_load[t].X * dt for t in time_steps)
    if project_type == GRID_CONNECTED:
        total_sell = sum(green_to_sell[t].X * dt for t in time_steps)
        if biomass_enabled:
            total_sell += sum(biomass_to_sell[t].X * dt for t in time_steps)
        total_unmet = 0.0
    else:
        total_sell = 0.0
        total_unmet = sum(unmet_load[t].X * dt for t in time_steps)

    # 边界触顶提示（v4.1）：优化结果贴住配置边界时向用户明示"结果受限"，
    # 避免把边界内的解误读为无约束最优。仅提示有限且为正的边界；建议性质，
    # 不改变结果与校验结论。两套引擎共用同一判定口径（相对容差 1e-6）。
    boundary_notes: list[str] = []

    def _at_bound(value: float, bound: float) -> bool:
        return abs(value - bound) <= 1.0e-6 * max(1.0, abs(bound))

    if bounds.wind_capacity_kw_max > 0.0 and _at_bound(p_wind.X, bounds.wind_capacity_kw_max):
        boundary_notes.append(
            f"风电装机 {p_wind.X:.1f} kW 达到配置上限 {bounds.wind_capacity_kw_max:g} kW，扩容空间受边界限制"
        )
    if bounds.pv_capacity_kw_max > 0.0 and _at_bound(p_pv.X, bounds.pv_capacity_kw_max):
        boundary_notes.append(
            f"光伏装机 {p_pv.X:.1f} kW 达到配置上限 {bounds.pv_capacity_kw_max:g} kW，扩容空间受边界限制"
        )
    if bounds.ess_energy_kwh_max > 0.0 and _at_bound(e_ess.X, bounds.ess_energy_kwh_max):
        boundary_notes.append(
            f"储能容量 {e_ess.X:.1f} kWh 达到配置上限 {bounds.ess_energy_kwh_max:g} kWh，扩容空间受边界限制"
        )
    if bounds.ess_power_kw_max > 0.0 and _at_bound(p_ess.X, bounds.ess_power_kw_max):
        boundary_notes.append(
            f"储能功率 {p_ess.X:.1f} kW 达到配置上限 {bounds.ess_power_kw_max:g} kW，扩容空间受边界限制"
        )
    if diesel_enabled:
        if diesel.max_capacity_kw > 0.0 and _at_bound(p_diesel.X, diesel.max_capacity_kw):
            boundary_notes.append(
                f"柴油装机 {p_diesel.X:.1f} kW 达到配置上限 {diesel.max_capacity_kw:g} kW，扩容空间受边界限制"
            )
        if diesel.min_capacity_kw > 0.0 and _at_bound(p_diesel.X, diesel.min_capacity_kw):
            boundary_notes.append(
                f"柴油装机被配置最小容量 {diesel.min_capacity_kw:g} kW 托底，结果含强制投资成分"
            )
    if biomass_enabled:
        if biomass.max_capacity_kw > 0.0 and _at_bound(p_biomass.X, biomass.max_capacity_kw):
            boundary_notes.append(
                f"生物质装机 {p_biomass.X:.1f} kW 达到配置上限 {biomass.max_capacity_kw:g} kW，扩容空间受边界限制"
            )
        if biomass.min_capacity_kw > 0.0 and _at_bound(p_biomass.X, biomass.min_capacity_kw):
            boundary_notes.append(
                f"生物质装机被配置最小容量 {biomass.min_capacity_kw:g} kW 托底，结果含强制投资成分"
            )
        if biomass.max_annual_energy_kwh is not None:
            energy_cap = float(biomass.max_annual_energy_kwh)
            energy_used = sum(biomass_output[t].X * dt for t in time_steps)
            if energy_used >= energy_cap - max(1.0, 1.0e-6 * energy_cap):
                boundary_notes.append(
                    f"生物质年发电量 {energy_used:.0f} kWh 达到燃料年可用量上限 {energy_cap:g} kWh，发电空间受燃料供应限制"
                )

    output_path = Path(output_dir) if output_dir is not None else Path("outputs")
    input_price_path = Path(price_path) if price_path is not None else None

    # 检修窗结果提取（v4.1）：起始小时即两阶段定窗选定的固定窗（不从变量
    # 读取——模型中已无检修变量），落盘检修标记供校验器复核。
    maintenance_window = None
    maintenance_flag = None
    if biomass_maint_hours > 0:
        horizon_len = len(df)
        start_hour = int(fixed_maintenance_start)
        maintenance_window = {
            "start_hour": start_hour,
            "hours": biomass_maint_hours,
        }
        maintenance_flag = [
            1.0 if ((t - start_hour) % horizon_len) < biomass_maint_hours else 0.0
            for t in time_steps
        ]

    hourly_csv_path, summary_csv_path, excel_path = export_results_to_csv(
        output_dir=output_path,
        input_path=input_path,
        price_path=input_price_path,
        df=df,
        buy_price=buy_price,
        sell_price=sell_price,
        dt=dt,
        p_wind=p_wind,
        p_pv=p_pv,
        e_ess=e_ess,
        p_ess=p_ess,
        green_to_load=green_to_load,
        green_to_storage=green_to_storage,
        green_to_sell=green_to_sell if project_type == GRID_CONNECTED else None,
        green_curtail=green_curtail,
        grid_to_load=grid_to_load if project_type == GRID_CONNECTED else None,
        unmet_load=unmet_load if project_type == OFFGRID else None,
        storage_to_load=storage_to_load,
        soc=soc,
        diesel_to_load=diesel_to_load if diesel_enabled else None,
        biomass_output=biomass_output if biomass_enabled else None,
        biomass_to_load=biomass_to_load if biomass_enabled else None,
        biomass_to_sell=biomass_to_sell if (biomass_enabled and project_type == GRID_CONNECTED) else None,
        biomass_curtail={t: biomass_curtail[t] for t in time_steps} if biomass_continuous else None,
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
        objective_value=objective_value,
        initial_investment_cost=initial_investment_cost,
        annual_om_cost=annual_om_cost,
        annual_buy_cost=annual_buy_cost,
        annual_sell_revenue=annual_sell_revenue,
        annual_unmet_penalty_cost=annual_unmet_penalty,
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
        status=model.Status,
        objective_value=objective_value,
        hourly_csv_path=hourly_csv_path,
        summary_csv_path=summary_csv_path,
        installed_capacities={
            "wind_capacity_kw": p_wind.X,
            "pv_capacity_kw": p_pv.X,
            "ess_energy_kwh": e_ess.X,
            "ess_power_kw": p_ess.X,
            "diesel_capacity_kw": diesel_capacity,
            "biomass_capacity_kw": biomass_capacity,
        },
        economic_metrics={
            "initial_investment_cost": initial_investment_cost,
            "annual_om_cost": annual_om_cost,
            "annual_buy_cost": annual_buy_cost,
            "annual_sell_revenue": annual_sell_revenue,
            "annual_unmet_penalty_cost": annual_unmet_penalty,
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
            "biomass_ratio_of_green": (
                total_biomass / total_green if total_green > 1.0e-9 else 0.0
            ),
            "diesel_ratio_of_load": (
                total_diesel / total_load if total_load > 1.0e-9 else 0.0
            ),
        },
        config=asdict(config),
        project_type=project_type,
        maintenance_window=maintenance_window,
        boundary_notes=tuple(boundary_notes),
        excel_path=excel_path,
    )
