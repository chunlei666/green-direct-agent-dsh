from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import OptimizationConfig
from .io_utils import load_price_data, load_profile_data, read_table
from .solver import present_value_factor


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    metric: float | None
    threshold: float | None
    details: str


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    files: dict[str, str]
    checks: list[ValidationCheck]


def _make_check(
    name: str,
    passed: bool,
    details: str,
    metric: float | None = None,
    threshold: float | None = None,
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=passed,
        metric=float(metric) if metric is not None else None,
        threshold=float(threshold) if threshold is not None else None,
        details=details,
    )


def _max_abs_difference(left_values: list[float], right_values: list[float]) -> float:
    if len(left_values) != len(right_values):
        raise ValueError("Cannot compare sequences with different lengths.")
    worst = 0.0
    for left, right in zip(left_values, right_values):
        difference = abs(left - right)
        # 非有限（NaN/±∞）的差值直接判为无穷违反：Python 的 max() 会跳过
        # NaN（NaN > x 恒 False），历史实现因此对含 NaN 的结果完全失明。
        if not math.isfinite(difference):
            return float("inf")
        if difference > worst:
            worst = difference
    return worst


def _max_violation(values: list[float]) -> float:
    worst = 0.0
    for value in values:
        if not math.isfinite(value):
            return float("inf")
        violation = max(value, 0.0)
        if violation > worst:
            worst = violation
    return worst


def _validate_config(config: OptimizationConfig) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []

    project_type_valid = config.project.type in {"grid_connected", "offgrid"}
    checks.append(
        _make_check(
            name="config_project_type_valid",
            passed=project_type_valid,
            details="项目类型必须是 grid_connected 或 offgrid。",
        )
    )
    checks.append(
        _make_check(
            name="config_loss_of_load_penalty_non_negative",
            passed=config.project.loss_of_load_penalty_per_kwh >= 0.0,
            metric=config.project.loss_of_load_penalty_per_kwh,
            threshold=0.0,
            details="失负荷惩罚单价必须非负。",
        )
    )
    lpue_cap = config.project.max_loss_ratio_of_load
    lpue_cap_valid = lpue_cap is None or 0.0 <= lpue_cap <= 1.0
    checks.append(
        _make_check(
            name="config_max_loss_ratio_range",
            passed=lpue_cap_valid,
            metric=lpue_cap,
            threshold=1.0,
            details="最大失负荷率上限需为空（不设上限）或位于 [0, 1]。",
        )
    )

    diesel = config.diesel
    diesel_issues = []
    if diesel.enabled:
        if diesel.capex_per_kw < 0.0:
            diesel_issues.append("capex_per_kw < 0")
        if diesel.fixed_om_per_kw_year < 0.0:
            diesel_issues.append("fixed_om_per_kw_year < 0")
        if diesel.fuel_cost_per_kwh < 0.0:
            diesel_issues.append("fuel_cost_per_kwh < 0")
        if diesel.min_capacity_kw < 0.0:
            diesel_issues.append("min_capacity_kw < 0")
        if diesel.min_capacity_kw > diesel.max_capacity_kw:
            diesel_issues.append("min_capacity_kw > max_capacity_kw")
    checks.append(
        _make_check(
            name="config_diesel_params_valid",
            passed=not diesel_issues,
            details=(
                "柴油参数在有效范围内。"
                if not diesel_issues
                else f"柴油参数异常: {', '.join(diesel_issues)}"
            ),
        )
    )

    biomass = config.biomass
    biomass_issues = []
    if biomass.enabled:
        if biomass.capex_per_kw < 0.0:
            biomass_issues.append("capex_per_kw < 0")
        if biomass.fixed_om_per_kw_year < 0.0:
            biomass_issues.append("fixed_om_per_kw_year < 0")
        if biomass.fuel_cost_per_kwh < 0.0:
            biomass_issues.append("fuel_cost_per_kwh < 0")
        if not 0.0 < biomass.capacity_factor <= 1.0:
            biomass_issues.append("capacity_factor 不在 (0, 1]")
        if biomass.min_capacity_kw < 0.0:
            biomass_issues.append("min_capacity_kw < 0")
        if biomass.min_capacity_kw > biomass.max_capacity_kw:
            biomass_issues.append("min_capacity_kw > max_capacity_kw")
        if biomass.max_annual_energy_kwh is not None and biomass.max_annual_energy_kwh < 0.0:
            biomass_issues.append("max_annual_energy_kwh < 0")
        if not 0.0 <= biomass.min_output_ratio < 1.0:
            biomass_issues.append("min_output_ratio 不在 [0, 1)")
        if not 0.0 <= biomass.maintenance_days <= 365.0:
            biomass_issues.append("maintenance_days 不在 [0, 365]")
    checks.append(
        _make_check(
            name="config_biomass_params_valid",
            passed=not biomass_issues,
            details=(
                "生物质参数在有效范围内。"
                if not biomass_issues
                else f"生物质参数异常: {', '.join(biomass_issues)}"
            ),
        )
    )

    checks.append(
        _make_check(
            name="config_timestep_positive",
            passed=config.timestep_hours > 0.0,
            metric=config.timestep_hours,
            threshold=0.0,
            details="timestep_hours 必须大于 0。",
        )
    )
    checks.append(
        _make_check(
            name="config_charge_efficiency_range",
            passed=0.0 < config.storage.charge_efficiency <= 1.0,
            metric=config.storage.charge_efficiency,
            threshold=1.0,
            details="charge_efficiency 必须在 (0, 1] 内。",
        )
    )
    checks.append(
        _make_check(
            name="config_discharge_efficiency_range",
            passed=0.0 < config.storage.discharge_efficiency <= 1.0,
            metric=config.storage.discharge_efficiency,
            threshold=1.0,
            details="discharge_efficiency 必须在 (0, 1] 内。",
        )
    )
    soc_bounds_valid = 0.0 <= config.storage.soc_min_ratio < config.storage.soc_max_ratio <= 1.0
    checks.append(
        _make_check(
            name="config_soc_bounds_valid",
            passed=soc_bounds_valid,
            metric=config.storage.soc_max_ratio - config.storage.soc_min_ratio,
            threshold=0.0,
            details="SOC 上下界需满足 0 <= soc_min < soc_max <= 1。",
        )
    )
    storage_hours_valid = config.storage.min_storage_hours <= config.storage.max_storage_hours
    checks.append(
        _make_check(
            name="config_storage_hours_valid",
            passed=storage_hours_valid,
            metric=config.storage.max_storage_hours - config.storage.min_storage_hours,
            threshold=0.0,
            details="储能时长上下界需满足 min_storage_hours <= max_storage_hours。",
        )
    )

    non_negative_values = {
        "wind_capex_per_kw": config.costs.wind_capex_per_kw,
        "pv_capex_per_kw": config.costs.pv_capex_per_kw,
        "ess_energy_capex_per_kwh": config.costs.ess_energy_capex_per_kwh,
        "ess_power_capex_per_kw": config.costs.ess_power_capex_per_kw,
        "wind_capacity_kw_max": config.bounds.wind_capacity_kw_max,
        "pv_capacity_kw_max": config.bounds.pv_capacity_kw_max,
        "ess_energy_kwh_max": config.bounds.ess_energy_kwh_max,
        "ess_power_kw_max": config.bounds.ess_power_kw_max,
    }
    min_value = min(non_negative_values.values())
    offending = [name for name, value in non_negative_values.items() if value < 0.0]
    checks.append(
        _make_check(
            name="config_non_negative_costs_and_bounds",
            passed=not offending,
            metric=min_value,
            threshold=0.0,
            details=(
                "关键成本与容量上界必须非负。"
                if not offending
                else f"以下字段为负值: {', '.join(offending)}"
            ),
        )
    )

    return checks


def validate_solution_outputs(
    data_path: str | Path,
    price_path: str | Path | None = None,
    hourly_results_path: str | Path = "",
    summary_results_path: str | Path = "",
    config: OptimizationConfig | None = None,
    balance_tolerance: float = 1.0e-4,
    ratio_tolerance: float = 1.0e-6,
    objective_tolerance: float = 1.0e-4,
) -> ValidationReport:
    config = config or OptimizationConfig()
    checks = _validate_config(config)

    profile_df = load_profile_data(data_path)
    if price_path is None:
        buy_price = [0.0] * len(profile_df)
        sell_price = [0.0] * len(profile_df)
    else:
        buy_price, sell_price = load_price_data(price_path, len(profile_df))
    hourly_df = read_table(hourly_results_path)
    summary_df = read_table(summary_results_path)

    if summary_df.empty:
        raise ValueError("Summary results file is empty.")

    summary = summary_df.iloc[0]
    dt = float(summary.get("timestep_hours", config.timestep_hours))

    price_required_missing = config.project.type == "grid_connected" and price_path is None
    checks.append(
        _make_check(
            name="price_file_present_for_grid_connected",
            passed=not price_required_missing,
            details="并网项目必须提供电价文件用于校验；离网项目可省略。",
        )
    )
    if price_required_missing:
        return _finalize_report(
            checks,
            data_path=data_path,
            price_path=price_path,
            hourly_results_path=hourly_results_path,
            summary_results_path=summary_results_path,
        )

    required_summary_columns = [
        "project_type",
        "annual_unmet_penalty_cost",
        "total_unmet_kwh",
        "loss_ratio_of_load",
        "diesel_capacity_kw",
        "biomass_capacity_kw",
        "annual_diesel_fuel_cost",
        "annual_biomass_fuel_cost",
        "total_diesel_generation_kwh",
        "total_biomass_generation_kwh",
    ]
    missing_summary_columns = [name for name in required_summary_columns if name not in summary_df.columns]
    checks.append(
        _make_check(
            name="summary_required_columns_present",
            passed=not missing_summary_columns,
            details=(
                "汇总结果文件包含所有必需列。"
                if not missing_summary_columns
                else f"汇总结果缺少列: {', '.join(missing_summary_columns)}"
            ),
        )
    )
    if missing_summary_columns:
        return _finalize_report(
            checks,
            data_path=data_path,
            price_path=price_path,
            hourly_results_path=hourly_results_path,
            summary_results_path=summary_results_path,
        )

    required_hourly_columns = [
        "hour_index",
        "load",
        "buy_price",
        "sell_price",
        "wind_profile",
        "pv_profile",
        "wind_generation",
        "pv_generation",
        "green_generation",
        "green_to_load",
        "green_to_storage",
        "green_to_sell",
        "green_curtail",
        "grid_to_load",
        "unmet_load",
        "storage_to_load",
        "soc_energy",
        "diesel_to_load",
        "biomass_generation",
        "biomass_to_load",
        "biomass_to_sell",
    ]
    missing_hourly_columns = [name for name in required_hourly_columns if name not in hourly_df.columns]
    checks.append(
        _make_check(
            name="hourly_required_columns_present",
            passed=not missing_hourly_columns,
            details=(
                "逐时结果文件包含所有必需列。"
                if not missing_hourly_columns
                else f"缺少列: {', '.join(missing_hourly_columns)}"
            ),
        )
    )
    if missing_hourly_columns:
        return _finalize_report(
            checks,
            data_path=data_path,
            price_path=price_path,
            hourly_results_path=hourly_results_path,
            summary_results_path=summary_results_path,
        )

    checks.append(
        _make_check(
            name="time_horizon_matches_input",
            passed=len(hourly_df) == len(profile_df),
            metric=float(abs(len(hourly_df) - len(profile_df))),
            threshold=0.0,
            details="逐时结果长度应与输入时序长度一致。",
        )
    )
    expected_hour_index = list(range(len(hourly_df)))
    actual_hour_index = hourly_df["hour_index"].astype(int).tolist()
    index_metric = _max_abs_difference(actual_hour_index, expected_hour_index) if actual_hour_index else 0.0
    checks.append(
        _make_check(
            name="hour_index_sequence_valid",
            passed=index_metric == 0.0,
            metric=index_metric,
            threshold=0.0,
            details="hour_index 应按 0..T-1 连续编号。",
        )
    )

    load_metric = _max_abs_difference(
        hourly_df["load"].astype(float).tolist(),
        profile_df["Load"].astype(float).tolist(),
    )
    checks.append(
        _make_check(
            name="hourly_load_matches_input",
            passed=load_metric <= balance_tolerance,
            metric=load_metric,
            threshold=balance_tolerance,
            details="逐时 load 应与输入负荷一致。",
        )
    )
    wind_profile_metric = _max_abs_difference(
        hourly_df["wind_profile"].astype(float).tolist(),
        profile_df["Wind"].astype(float).tolist(),
    )
    checks.append(
        _make_check(
            name="hourly_wind_profile_matches_input",
            passed=wind_profile_metric <= balance_tolerance,
            metric=wind_profile_metric,
            threshold=balance_tolerance,
            details="逐时 wind_profile 应与输入风电曲线一致。",
        )
    )
    pv_profile_metric = _max_abs_difference(
        hourly_df["pv_profile"].astype(float).tolist(),
        profile_df["PV"].astype(float).tolist(),
    )
    checks.append(
        _make_check(
            name="hourly_pv_profile_matches_input",
            passed=pv_profile_metric <= balance_tolerance,
            metric=pv_profile_metric,
            threshold=balance_tolerance,
            details="逐时 pv_profile 应与输入光伏曲线一致。",
        )
    )
    if price_path is not None:
        buy_price_metric = _max_abs_difference(
            hourly_df["buy_price"].astype(float).tolist(),
            buy_price,
        )
        checks.append(
            _make_check(
                name="hourly_buy_price_matches_input",
                passed=buy_price_metric <= balance_tolerance,
                metric=buy_price_metric,
                threshold=balance_tolerance,
                details="逐时 buy_price 应与扩展后的电价序列一致。",
            )
        )
        sell_price_metric = _max_abs_difference(
            hourly_df["sell_price"].astype(float).tolist(),
            sell_price,
        )
        checks.append(
            _make_check(
                name="hourly_sell_price_matches_input",
                passed=sell_price_metric <= balance_tolerance,
                metric=sell_price_metric,
                threshold=balance_tolerance,
                details="逐时 sell_price 应与扩展后的电价序列一致。",
            )
        )

    wind_capacity = float(summary["wind_capacity_kw"])
    pv_capacity = float(summary["pv_capacity_kw"])
    ess_energy = float(summary["ess_energy_kwh"])
    ess_power = float(summary["ess_power_kw"])

    recomputed_wind_generation = [
        wind_capacity * value for value in hourly_df["wind_profile"].astype(float).tolist()
    ]
    wind_generation_metric = _max_abs_difference(
        hourly_df["wind_generation"].astype(float).tolist(),
        recomputed_wind_generation,
    )
    checks.append(
        _make_check(
            name="wind_generation_consistent_with_capacity",
            passed=wind_generation_metric <= balance_tolerance,
            metric=wind_generation_metric,
            threshold=balance_tolerance,
            details="wind_generation 应等于风电装机乘以风电出力曲线。",
        )
    )

    recomputed_pv_generation = [
        pv_capacity * value for value in hourly_df["pv_profile"].astype(float).tolist()
    ]
    pv_generation_metric = _max_abs_difference(
        hourly_df["pv_generation"].astype(float).tolist(),
        recomputed_pv_generation,
    )
    checks.append(
        _make_check(
            name="pv_generation_consistent_with_capacity",
            passed=pv_generation_metric <= balance_tolerance,
            metric=pv_generation_metric,
            threshold=balance_tolerance,
            details="pv_generation 应等于光伏装机乘以光伏出力曲线。",
        )
    )

    recomputed_green_generation = [
        wind + pv for wind, pv in zip(recomputed_wind_generation, recomputed_pv_generation)
    ]
    green_generation_metric = _max_abs_difference(
        hourly_df["green_generation"].astype(float).tolist(),
        recomputed_green_generation,
    )
    checks.append(
        _make_check(
            name="green_generation_consistent_with_components",
            passed=green_generation_metric <= balance_tolerance,
            metric=green_generation_metric,
            threshold=balance_tolerance,
            details="green_generation 应等于 wind_generation + pv_generation。",
        )
    )

    green_balance_residuals = [
        green
        - to_load
        - to_storage
        - to_sell
        - curtail
        for green, to_load, to_storage, to_sell, curtail in zip(
            hourly_df["green_generation"].astype(float).tolist(),
            hourly_df["green_to_load"].astype(float).tolist(),
            hourly_df["green_to_storage"].astype(float).tolist(),
            hourly_df["green_to_sell"].astype(float).tolist(),
            hourly_df["green_curtail"].astype(float).tolist(),
        )
    ]
    green_balance_metric = max((abs(value) for value in green_balance_residuals), default=0.0)
    checks.append(
        _make_check(
            name="green_balance_feasible",
            passed=green_balance_metric <= balance_tolerance,
            metric=green_balance_metric,
            threshold=balance_tolerance,
            details="每个时段的绿电平衡残差应足够小。",
        )
    )

    load_balance_residuals = [
        to_load + storage_to_load + grid_to_load + unmet + diesel + biomass_to_load - load
        for to_load, storage_to_load, grid_to_load, unmet, diesel, biomass_to_load, load in zip(
            hourly_df["green_to_load"].astype(float).tolist(),
            hourly_df["storage_to_load"].astype(float).tolist(),
            hourly_df["grid_to_load"].astype(float).tolist(),
            hourly_df["unmet_load"].astype(float).tolist(),
            hourly_df["diesel_to_load"].astype(float).tolist(),
            hourly_df["biomass_to_load"].astype(float).tolist(),
            hourly_df["load"].astype(float).tolist(),
        )
    ]
    load_balance_metric = max((abs(value) for value in load_balance_residuals), default=0.0)
    checks.append(
        _make_check(
            name="load_balance_feasible",
            passed=load_balance_metric <= balance_tolerance,
            metric=load_balance_metric,
            threshold=balance_tolerance,
            details="每个时段的负荷平衡残差应足够小。",
        )
    )

    unmet_values = hourly_df["unmet_load"].astype(float).tolist()
    unmet_non_negative_metric = _max_violation([-value for value in unmet_values])
    checks.append(
        _make_check(
            name="unmet_load_non_negative",
            passed=unmet_non_negative_metric <= balance_tolerance,
            metric=unmet_non_negative_metric,
            threshold=balance_tolerance,
            details="失负荷功率应非负。",
        )
    )

    if config.project.type == "offgrid":
        grid_exchange_metric = max(
            _max_violation(hourly_df["grid_to_load"].astype(float).tolist()),
            _max_violation(hourly_df["green_to_sell"].astype(float).tolist()),
            _max_violation(hourly_df["biomass_to_sell"].astype(float).tolist()),
        )
        checks.append(
            _make_check(
                name="offgrid_no_grid_exchange_feasible",
                passed=grid_exchange_metric <= balance_tolerance,
                metric=grid_exchange_metric,
                threshold=balance_tolerance,
                details="离网项目不应出现购电或上网功率。",
            )
        )
    else:
        grid_unmet_metric = _max_violation(unmet_values)
        checks.append(
            _make_check(
                name="grid_connected_no_loss_of_load_feasible",
                passed=grid_unmet_metric <= balance_tolerance,
                metric=grid_unmet_metric,
                threshold=balance_tolerance,
                details="并网项目不应出现失负荷。",
            )
        )

    # ---- 柴油/生物质组件校验（未启用时各项恒为 0，自动通过） ----
    diesel_capacity = float(summary["diesel_capacity_kw"])
    biomass_capacity = float(summary["biomass_capacity_kw"])
    diesel_values = hourly_df["diesel_to_load"].astype(float).tolist()
    biomass_output_values = hourly_df["biomass_generation"].astype(float).tolist()
    biomass_to_load_values = hourly_df["biomass_to_load"].astype(float).tolist()
    biomass_to_sell_values = hourly_df["biomass_to_sell"].astype(float).tolist()

    diesel_capacity_bounds_violation = max(
        config.diesel.min_capacity_kw - diesel_capacity,
        diesel_capacity - config.diesel.max_capacity_kw,
        0.0,
    )
    checks.append(
        _make_check(
            name="diesel_capacity_within_bounds",
            passed=diesel_capacity_bounds_violation <= balance_tolerance,
            metric=diesel_capacity,
            threshold=config.diesel.max_capacity_kw,
            details="柴油装机应位于配置的容量上下界之间。",
        )
    )
    biomass_capacity_bounds_violation = max(
        config.biomass.min_capacity_kw - biomass_capacity,
        biomass_capacity - config.biomass.max_capacity_kw,
        0.0,
    )
    checks.append(
        _make_check(
            name="biomass_capacity_within_bounds",
            passed=biomass_capacity_bounds_violation <= balance_tolerance,
            metric=biomass_capacity,
            threshold=config.biomass.max_capacity_kw,
            details="生物质装机应位于配置的容量上下界之间。",
        )
    )

    # ---- 风/光/储装机界内校验（与柴/生同口径，防止越界装机混入结果） ----
    for check_name, capacity_value, bound_value, label in (
        ("wind_capacity_within_bounds", wind_capacity, config.bounds.wind_capacity_kw_max, "风电"),
        ("pv_capacity_within_bounds", pv_capacity, config.bounds.pv_capacity_kw_max, "光伏"),
        ("ess_energy_within_bounds", ess_energy, config.bounds.ess_energy_kwh_max, "储能容量"),
        ("ess_power_within_bounds", ess_power, config.bounds.ess_power_kw_max, "储能功率"),
    ):
        violation = max(capacity_value - bound_value, 0.0)
        checks.append(
            _make_check(
                name=check_name,
                passed=violation <= balance_tolerance,
                metric=capacity_value,
                threshold=bound_value,
                details=f"{label}应不超过配置上界。",
            )
        )

    diesel_output_metric = _max_violation(
        [value - diesel_capacity for value in diesel_values]
    )
    checks.append(
        _make_check(
            name="diesel_output_within_capacity",
            passed=diesel_output_metric <= balance_tolerance,
            metric=diesel_output_metric,
            threshold=balance_tolerance,
            details="柴油逐时出力不应超过柴油装机。",
        )
    )

    biomass_output_limit = biomass_capacity * config.biomass.capacity_factor
    biomass_output_metric = _max_violation(
        [value - biomass_output_limit for value in biomass_output_values]
    )
    checks.append(
        _make_check(
            name="biomass_output_within_capacity_factor",
            passed=biomass_output_metric <= balance_tolerance,
            metric=biomass_output_metric,
            threshold=balance_tolerance,
            details="生物质逐时出力不应超过装机乘以容量因子。",
        )
    )

    biomass_balance_residuals = [
        output - to_load - to_sell - curtail
        for output, to_load, to_sell, curtail in zip(
            biomass_output_values,
            biomass_to_load_values,
            biomass_to_sell_values,
            (
                hourly_df["biomass_curtail"].astype(float).tolist()
                if "biomass_curtail" in hourly_df.columns
                else [0.0] * len(hourly_df)
            ),
        )
    ]
    biomass_balance_metric = max((abs(value) for value in biomass_balance_residuals), default=0.0)
    checks.append(
        _make_check(
            name="biomass_balance_feasible",
            passed=biomass_balance_metric <= balance_tolerance,
            metric=biomass_balance_metric,
            threshold=balance_tolerance,
            details="生物质出力应等于直供、上网与弃电之和（离网项目上网为 0）。",
        )
    )

    # ---- 持续运行模式校验（v4）：检修窗与最小出力 ----
    # 检修窗启用时，逐时结果必须携带检修标记列（由求解器落盘），校验器据
    # 此独立复核：窗口时长恰为配置天数×24、全年恰一个连续（可跨年）窗口、
    # 窗内出力为 0、窗外出力不低于最小出力比例×装机。
    has_maintenance_flag = "biomass_maintenance" in hourly_df.columns
    maintenance_required = (
        config.biomass.enabled and config.biomass.maintenance_days > 0.0
    )
    if maintenance_required and not has_maintenance_flag:
        checks.append(
            _make_check(
                name="biomass_maintenance_flag_present",
                passed=False,
                metric=0.0,
                threshold=1.0,
                details="配置启用检修窗但结果缺少检修标记列（结果可能由不支持检修的旧引擎生成），请重新求解。",
            )
        )
    if maintenance_required and has_maintenance_flag:
        flag_values = hourly_df["biomass_maintenance"].astype(float).tolist()
        expected_hours = int(round(config.biomass.maintenance_days * 24))
        flagged_hours = sum(1 for value in flag_values if value > 0.5)
        flag_count_metric = abs(flagged_hours - expected_hours)
        checks.append(
            _make_check(
                name="biomass_maintenance_duration_matches_config",
                passed=flag_count_metric <= 0.5,
                metric=float(flagged_hours),
                threshold=float(expected_hours),
                details="检修标记的小时数应等于配置的年检修天数×24。",
            )
        )
        # 连续性（循环序列）：全年恰一个 0→1 跳变（即恰一个连续窗口）。
        transitions = sum(
            1
            for i in range(len(flag_values))
            if flag_values[i] > 0.5 and flag_values[i - 1] <= 0.5
        )
        checks.append(
            _make_check(
                name="biomass_maintenance_single_contiguous_window",
                passed=transitions == 1,
                metric=float(transitions),
                threshold=1.0,
                details="全年应恰有一个连续检修窗（可跨年首尾衔接）。",
            )
        )
        maint_output_metric = max(
            (abs(value) for value, flag in zip(biomass_output_values, flag_values) if flag > 0.5),
            default=0.0,
        )
        checks.append(
            _make_check(
                name="biomass_output_zero_during_maintenance",
                passed=maint_output_metric <= balance_tolerance,
                metric=maint_output_metric,
                threshold=balance_tolerance,
                details="检修窗内生物质出力应为 0。",
            )
        )
        if config.biomass.min_output_ratio > 0.0:
            floor = biomass_capacity * config.biomass.min_output_ratio
            outside_floor_metric = max(
                (
                    floor - value
                    for value, flag in zip(biomass_output_values, flag_values)
                    if flag <= 0.5
                ),
                default=0.0,
            )
            checks.append(
                _make_check(
                    name="biomass_min_output_outside_maintenance",
                    passed=outside_floor_metric <= balance_tolerance,
                    metric=outside_floor_metric,
                    threshold=balance_tolerance,
                    details="检修窗外生物质出力应不低于最小出力比例×装机。",
                )
            )
    elif (
        config.biomass.enabled
        and config.biomass.maintenance_days <= 0.0
        and config.biomass.min_output_ratio > 0.0
    ):
        floor = biomass_capacity * config.biomass.min_output_ratio
        floor_metric = max((floor - value for value in biomass_output_values), default=0.0)
        checks.append(
            _make_check(
                name="biomass_min_output_floor",
                passed=floor_metric <= balance_tolerance,
                metric=floor_metric,
                threshold=balance_tolerance,
                details="持续运行模式下生物质逐时出力应不低于最小出力比例×装机。",
            )
        )

    if config.biomass.enabled and config.biomass.max_annual_energy_kwh is not None:
        total_biomass_energy = float((hourly_df["biomass_generation"] * dt).sum())
        biomass_energy_violation = max(
            total_biomass_energy - config.biomass.max_annual_energy_kwh,
            0.0,
        )
        checks.append(
            _make_check(
                name="biomass_annual_energy_within_limit",
                passed=biomass_energy_violation <= balance_tolerance,
                metric=total_biomass_energy,
                threshold=config.biomass.max_annual_energy_kwh,
                details="生物质年发电量应不超过燃料年可用量上限。",
            )
        )

    # 并网通道物理上限：绿电与生物质合计上网共用一条线路（并网模式）。
    if config.project.type == "grid_connected":
        combined_export_values = [
            green_sell + biomass_sell
            for green_sell, biomass_sell in zip(
                hourly_df["green_to_sell"].astype(float).tolist(),
                hourly_df["biomass_to_sell"].astype(float).tolist(),
            )
        ]
        combined_export_metric = _max_violation(
            [
                value - config.bounds.grid_export_kw_max
                for value in combined_export_values
            ]
        )
        checks.append(
            _make_check(
                name="combined_export_within_grid_limit",
                passed=combined_export_metric <= balance_tolerance,
                metric=combined_export_metric,
                threshold=balance_tolerance,
                details="绿电与生物质合计上网功率不应超过并网容量上限（共用并网通道）。",
            )
        )

        # 并网通道同一小时只能单向流动：购电与上网并存意味着电价倒挂下的
        # 套利（LP 无 0/1 变量无法自禁），在此检出并阻断结果呈现。
        simultaneous_metric = max(
            (
                min(import_value, export_value)
                for import_value, export_value in zip(
                    hourly_df["grid_to_load"].astype(float).tolist(),
                    combined_export_values,
                )
            ),
            default=0.0,
        )
        checks.append(
            _make_check(
                name="grid_flow_single_direction",
                passed=simultaneous_metric <= balance_tolerance,
                metric=simultaneous_metric,
                threshold=balance_tolerance,
                details="并网通道同一小时不应同时购电与上网；若出现请检查电价文件是否售电价高于购电价。",
            )
        )

    if not config.diesel.enabled:
        diesel_nonzero_metric = max(
            _max_violation(diesel_values),
            abs(diesel_capacity),
            0.0,
        )
        checks.append(
            _make_check(
                name="diesel_disabled_consistent",
                passed=diesel_nonzero_metric <= balance_tolerance,
                metric=diesel_nonzero_metric,
                threshold=balance_tolerance,
                details="未启用柴油组件时不应出现柴油出力或装机。",
            )
        )
    if not config.biomass.enabled:
        biomass_nonzero_metric = max(
            _max_violation(biomass_output_values),
            _max_violation(biomass_to_load_values),
            _max_violation(biomass_to_sell_values),
            abs(biomass_capacity),
            0.0,
        )
        checks.append(
            _make_check(
                name="biomass_disabled_consistent",
                passed=biomass_nonzero_metric <= balance_tolerance,
                metric=biomass_nonzero_metric,
                threshold=balance_tolerance,
                details="未启用生物质组件时不应出现生物质出力或装机。",
            )
        )

    charge_values = hourly_df["green_to_storage"].astype(float).tolist()
    discharge_values = hourly_df["storage_to_load"].astype(float).tolist()
    soc_values = hourly_df["soc_energy"].astype(float).tolist()
    soc_update_residuals = []
    for index, soc_value in enumerate(soc_values):
        prev_index = len(soc_values) - 1 if index == 0 else index - 1
        expected_soc = (
            soc_values[prev_index]
            + config.storage.charge_efficiency * charge_values[index] * dt
            - discharge_values[index] * dt / config.storage.discharge_efficiency
        )
        soc_update_residuals.append(soc_value - expected_soc)
    soc_update_metric = max((abs(value) for value in soc_update_residuals), default=0.0)
    checks.append(
        _make_check(
            name="soc_update_feasible",
            passed=soc_update_metric <= balance_tolerance,
            metric=soc_update_metric,
            threshold=balance_tolerance,
            details="SOC 递推方程残差应足够小。",
        )
    )

    soc_lower_violations = [config.storage.soc_min_ratio * ess_energy - value for value in soc_values]
    soc_upper_violations = [value - config.storage.soc_max_ratio * ess_energy for value in soc_values]
    soc_violation_metric = max(
        _max_violation(soc_lower_violations),
        _max_violation(soc_upper_violations),
    )
    checks.append(
        _make_check(
            name="soc_bounds_feasible",
            passed=soc_violation_metric <= balance_tolerance,
            metric=soc_violation_metric,
            threshold=balance_tolerance,
            details="SOC 应位于配置的上下界之间。",
        )
    )

    charge_limit_metric = _max_violation([value - ess_power for value in charge_values])
    checks.append(
        _make_check(
            name="charge_power_limit_feasible",
            passed=charge_limit_metric <= balance_tolerance,
            metric=charge_limit_metric,
            threshold=balance_tolerance,
            details="充电功率不应超过储能功率装机。",
        )
    )
    discharge_limit_metric = _max_violation([value - ess_power for value in discharge_values])
    checks.append(
        _make_check(
            name="discharge_power_limit_feasible",
            passed=discharge_limit_metric <= balance_tolerance,
            metric=discharge_limit_metric,
            threshold=balance_tolerance,
            details="放电功率不应超过储能功率装机。",
        )
    )

    storage_hour_min_metric = max(config.storage.min_storage_hours * ess_power - ess_energy, 0.0)
    storage_hour_max_metric = max(ess_energy - config.storage.max_storage_hours * ess_power, 0.0)
    storage_hour_violation = max(storage_hour_min_metric, storage_hour_max_metric)
    checks.append(
        _make_check(
            name="storage_hour_bounds_feasible",
            passed=storage_hour_violation <= balance_tolerance,
            metric=storage_hour_violation,
            threshold=balance_tolerance,
            details="储能能量与功率应满足时长上下界约束。",
        )
    )

    total_green = float(
        ((hourly_df["green_generation"] + hourly_df["biomass_generation"]) * dt).sum()
    )
    total_load = float((hourly_df["load"] * dt).sum())
    total_self_use = float(
        (
            (
                hourly_df["green_to_load"]
                + hourly_df["storage_to_load"]
                + hourly_df["biomass_to_load"]
            )
            * dt
        ).sum()
    )
    total_sell = float((hourly_df["green_to_sell"] * dt).sum()) + float(
        (hourly_df["biomass_to_sell"] * dt).sum()
    )
    total_unmet = float((hourly_df["unmet_load"] * dt).sum())
    total_diesel = float((hourly_df["diesel_to_load"] * dt).sum())
    total_biomass = float((hourly_df["biomass_generation"] * dt).sum())
    total_buy_cost = float((hourly_df["grid_to_load"] * hourly_df["buy_price"] * dt).sum())
    total_sell_revenue = float(
        (
            (hourly_df["green_to_sell"] + hourly_df["biomass_to_sell"])
            * hourly_df["sell_price"]
            * dt
        ).sum()
    )

    project_type_metric = 0.0 if str(summary["project_type"]) == config.project.type else 1.0
    checks.append(
        _make_check(
            name="summary_project_type_matches_config",
            passed=project_type_metric == 0.0,
            metric=project_type_metric,
            threshold=0.0,
            details="汇总结果中的项目类型应与配置一致。",
        )
    )

    if config.project.type == "offgrid" and config.project.max_loss_ratio_of_load is not None:
        loss_ratio = total_unmet / total_load if total_load > 1.0e-9 else 0.0
        loss_ratio_violation = max(
            loss_ratio - config.project.max_loss_ratio_of_load,
            0.0,
        )
        checks.append(
            _make_check(
                name="offgrid_loss_ratio_within_cap",
                passed=loss_ratio_violation <= ratio_tolerance,
                metric=loss_ratio,
                threshold=config.project.max_loss_ratio_of_load,
                details="离网项目失负荷率应不超过配置的最大失负荷率上限。",
            )
        )

    summary_total_checks = [
        ("summary_total_load_consistent", float(summary["total_load_kwh"]), total_load, "summary 中 total_load_kwh 应与逐时积分一致。"),
        ("summary_total_green_consistent", float(summary["total_green_generation_kwh"]), total_green, "summary 中 total_green_generation_kwh 应与逐时积分一致。"),
        ("summary_total_self_use_consistent", float(summary["total_self_use_kwh"]), total_self_use, "summary 中 total_self_use_kwh 应与逐时积分一致。"),
        ("summary_total_sell_consistent", float(summary["total_green_sell_kwh"]), total_sell, "summary 中 total_green_sell_kwh 应与逐时积分一致。"),
        ("summary_total_unmet_consistent", float(summary["total_unmet_kwh"]), total_unmet, "summary 中 total_unmet_kwh 应与逐时积分一致。"),
        ("summary_total_diesel_consistent", float(summary["total_diesel_generation_kwh"]), total_diesel, "summary 中 total_diesel_generation_kwh 应与逐时积分一致。"),
        ("summary_total_biomass_consistent", float(summary["total_biomass_generation_kwh"]), total_biomass, "summary 中 total_biomass_generation_kwh 应与逐时积分一致。"),
        ("summary_buy_cost_consistent", float(summary["total_buy_cost"]), total_buy_cost, "summary 中 total_buy_cost 应与逐时成本一致。"),
        ("summary_sell_revenue_consistent", float(summary["total_sell_revenue"]), total_sell_revenue, "summary 中 total_sell_revenue 应与逐时收益一致。"),
    ]
    for name, expected_value, actual_value, details in summary_total_checks:
        metric = abs(expected_value - actual_value)
        checks.append(
            _make_check(
                name=name,
                passed=metric <= balance_tolerance,
                metric=metric,
                threshold=balance_tolerance,
                details=details,
            )
        )

    min_self_use_green_violation = max(
        config.policy.min_self_use_ratio_of_green - float(summary["self_use_ratio_of_green"]),
        0.0,
    )
    checks.append(
        _make_check(
            name="policy_min_self_use_ratio_of_green_feasible",
            passed=min_self_use_green_violation <= ratio_tolerance,
            metric=min_self_use_green_violation,
            threshold=ratio_tolerance,
            details="绿电自用率应满足策略下限。",
        )
    )
    min_self_use_load_violation = max(
        config.policy.min_self_use_ratio_of_load - float(summary["self_use_ratio_of_load"]),
        0.0,
    )
    checks.append(
        _make_check(
            name="policy_min_self_use_ratio_of_load_feasible",
            passed=min_self_use_load_violation <= ratio_tolerance,
            metric=min_self_use_load_violation,
            threshold=ratio_tolerance,
            details="负荷绿电覆盖率应满足策略下限。",
        )
    )
    max_sell_ratio_violation = max(
        float(summary["sell_ratio_of_green"]) - config.policy.max_sell_ratio_of_green,
        0.0,
    )
    checks.append(
        _make_check(
            name="policy_max_sell_ratio_of_green_feasible",
            passed=max_sell_ratio_violation <= ratio_tolerance,
            metric=max_sell_ratio_violation,
            threshold=ratio_tolerance,
            details="绿电外售比例应不高于策略上限。",
        )
    )

    initial_investment_expected = (
        config.costs.wind_capex_per_kw * wind_capacity
        + config.costs.pv_capex_per_kw * pv_capacity
        + config.costs.ess_energy_capex_per_kwh * ess_energy
        + config.costs.ess_power_capex_per_kw * ess_power
    )
    if config.diesel.enabled:
        initial_investment_expected += config.diesel.capex_per_kw * diesel_capacity
    if config.biomass.enabled:
        initial_investment_expected += config.biomass.capex_per_kw * biomass_capacity
    initial_investment_metric = abs(initial_investment_expected - float(summary["initial_investment_cost"]))
    checks.append(
        _make_check(
            name="initial_investment_consistent_with_config",
            passed=initial_investment_metric <= objective_tolerance,
            metric=initial_investment_metric,
            threshold=objective_tolerance,
            details="初始投资应与装机容量和成本参数一致。",
        )
    )

    annual_om_expected = (
        config.costs.wind_om_per_kw_year * wind_capacity
        + config.costs.pv_om_per_kw_year * pv_capacity
        + config.costs.ess_energy_om_per_kwh_year * ess_energy
        + config.costs.ess_power_om_per_kw_year * ess_power
    )
    if config.diesel.enabled:
        annual_om_expected += config.diesel.fixed_om_per_kw_year * diesel_capacity
    if config.biomass.enabled:
        annual_om_expected += config.biomass.fixed_om_per_kw_year * biomass_capacity
    annual_om_metric = abs(annual_om_expected - float(summary["annual_om_cost"]))
    checks.append(
        _make_check(
            name="annual_om_consistent_with_config",
            passed=annual_om_metric <= objective_tolerance,
            metric=annual_om_metric,
            threshold=objective_tolerance,
            details="年运维成本应与装机容量和运维参数一致。",
        )
    )

    lifecycle_pvf = present_value_factor(config.finance.lifecycle_years, config.finance.discount_rate)
    depreciation_pvf = present_value_factor(
        config.finance.depreciation_years,
        config.finance.discount_rate,
    )
    salvage_discount_factor = (1.0 + config.finance.discount_rate) ** config.finance.lifecycle_years
    objective_reconstructed = (
        float(summary["initial_investment_cost"])
        + lifecycle_pvf * float(summary["annual_om_cost"])
        + lifecycle_pvf * float(summary["annual_buy_cost"])
        - lifecycle_pvf * float(summary["annual_sell_revenue"])
        + lifecycle_pvf * float(summary["annual_unmet_penalty_cost"])
        + lifecycle_pvf * float(summary["annual_diesel_fuel_cost"])
        + lifecycle_pvf * float(summary["annual_biomass_fuel_cost"])
        - float(summary["salvage_value_npv"])
        - float(summary["tax_shield_npv"])
    )
    objective_metric = abs(objective_reconstructed - float(summary["objective_value"]))
    checks.append(
        _make_check(
            name="objective_value_consistent_with_summary_terms",
            passed=objective_metric <= objective_tolerance,
            metric=objective_metric,
            threshold=objective_tolerance,
            details="目标函数值应与导出的经济项重构结果一致。",
        )
    )

    unmet_penalty_expected = config.project.loss_of_load_penalty_per_kwh * total_unmet
    unmet_penalty_metric = abs(unmet_penalty_expected - float(summary["annual_unmet_penalty_cost"]))
    checks.append(
        _make_check(
            name="unmet_penalty_consistent_with_config",
            passed=unmet_penalty_metric <= objective_tolerance,
            metric=unmet_penalty_metric,
            threshold=objective_tolerance,
            details="年失负荷惩罚成本应等于惩罚单价乘以全年失负荷电量。",
        )
    )

    diesel_fuel_expected = config.diesel.fuel_cost_per_kwh * total_diesel
    diesel_fuel_metric = abs(diesel_fuel_expected - float(summary["annual_diesel_fuel_cost"]))
    checks.append(
        _make_check(
            name="diesel_fuel_cost_consistent_with_config",
            passed=diesel_fuel_metric <= objective_tolerance,
            metric=diesel_fuel_metric,
            threshold=objective_tolerance,
            details="年柴油燃料成本应等于燃料单价乘以全年柴油发电量。",
        )
    )

    biomass_fuel_expected = config.biomass.fuel_cost_per_kwh * total_biomass
    biomass_fuel_metric = abs(biomass_fuel_expected - float(summary["annual_biomass_fuel_cost"]))
    checks.append(
        _make_check(
            name="biomass_fuel_cost_consistent_with_config",
            passed=biomass_fuel_metric <= objective_tolerance,
            metric=biomass_fuel_metric,
            threshold=objective_tolerance,
            details="年生物质燃料成本应等于燃料单价乘以全年生物质发电量。",
        )
    )

    salvage_expected = config.finance.salvage_rate * float(summary["initial_investment_cost"]) / salvage_discount_factor
    salvage_metric = abs(salvage_expected - float(summary["salvage_value_npv"]))
    checks.append(
        _make_check(
            name="salvage_value_consistent_with_config",
            passed=salvage_metric <= objective_tolerance,
            metric=salvage_metric,
            threshold=objective_tolerance,
            details="残值现值应与财务参数一致。",
        )
    )

    tax_shield_expected = (
        config.finance.income_tax_rate
        * (1.0 - config.finance.salvage_rate)
        * float(summary["initial_investment_cost"])
        / config.finance.depreciation_years
        * depreciation_pvf
    )
    tax_shield_metric = abs(tax_shield_expected - float(summary["tax_shield_npv"]))
    checks.append(
        _make_check(
            name="tax_shield_consistent_with_config",
            passed=tax_shield_metric <= objective_tolerance,
            metric=tax_shield_metric,
            threshold=objective_tolerance,
            details="折旧税盾现值应与财务参数一致。",
        )
    )

    return _finalize_report(
        checks,
        data_path=data_path,
        price_path=price_path,
        hourly_results_path=hourly_results_path,
        summary_results_path=summary_results_path,
    )


def _finalize_report(
    checks: list[ValidationCheck],
    data_path: str | Path,
    price_path: str | Path,
    hourly_results_path: str | Path,
    summary_results_path: str | Path,
) -> ValidationReport:
    passed_checks = sum(1 for item in checks if item.passed)
    failed_checks = len(checks) - passed_checks
    return ValidationReport(
        passed=failed_checks == 0,
        total_checks=len(checks),
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        files={
            "data_path": str(Path(data_path)),
            "price_path": str(Path(price_path)) if price_path is not None else "",
            "hourly_results_path": str(Path(hourly_results_path)),
            "summary_results_path": str(Path(summary_results_path)),
        },
        checks=checks,
    )


def save_validation_report(report: ValidationReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = asdict(report)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
