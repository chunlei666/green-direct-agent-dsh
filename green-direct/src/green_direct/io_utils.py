from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def read_table(data_path: str | Path) -> pd.DataFrame:
    path = Path(data_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        try:
            return pd.read_excel(path)
        except ImportError as exc:
            raise ImportError(
                "Excel support is unavailable in the current environment. "
                "Please install openpyxl or convert the input file to CSV."
            ) from exc

    raise ValueError(f"Unsupported input format: {path.suffix}")


def find_column(frame: pd.DataFrame, candidates: list[str], label: str) -> str:
    for name in candidates:
        if name in frame.columns:
            return name

    normalized = {str(col).strip().lower(): col for col in frame.columns}
    for name in candidates:
        key = name.strip().lower()
        if key in normalized:
            return normalized[key]

    candidate_text = ", ".join(candidates)
    raise ValueError(f"Missing required column for {label}. Accepted names: {candidate_text}")


def _require_finite(values: list[float], label: str) -> None:
    """拒绝缺失/非有限数值（NaN、±∞）。

    数据里一个 NaN 会在求解层静默击穿含该系数的全部约束（求解器丢弃
    约束、政策比例凭空消失），并在校验层被 max() 跳过而完全失明——
    因此必须在摄取入口直接拒绝，两条路径（solve/validate）共用本检查。
    """
    for index, value in enumerate(values):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(
                f"{label}第 {index} 行存在缺失或非有限数值（NaN/±∞），"
                "请修正数据文件后重试。"
            )


def load_profile_data(data_path: str | Path) -> pd.DataFrame:
    frame = read_table(data_path)

    load_col = find_column(frame, ["Load", "load", "demand", "load_kw", "负荷"], "load")
    pv_col = find_column(frame, ["PV", "pv", "pv_profile", "光伏"], "pv")
    wind_col = find_column(frame, ["Wind", "wind", "wind_profile", "风电"], "wind")

    result = frame.loc[:, [load_col, pv_col, wind_col]].rename(
        columns={load_col: "Load", pv_col: "PV", wind_col: "Wind"}
    )
    for col in ("Load", "PV", "Wind"):
        _require_finite(result[col].astype(float).tolist(), f"时序列 {col} ")
    return result


def expand_price_series(price_values: list[float], horizon: int) -> list[float]:
    if not price_values:
        raise ValueError("Price data must contain at least one row.")

    repeat_count = (horizon + len(price_values) - 1) // len(price_values)
    expanded = price_values * repeat_count
    return expanded[:horizon]


def load_price_data(price_path: str | Path, horizon: int) -> tuple[list[float], list[float]]:
    frame = read_table(price_path)

    buy_col = find_column(
        frame,
        ["buy_price", "purchase_price", "grid_buy_price", "买电价", "购电价"],
        "buy price",
    )
    sell_col = find_column(
        frame,
        ["sell_price", "feed_in_price", "grid_sell_price", "售电价", "上网电价"],
        "sell price",
    )

    buy_values = frame[buy_col].astype(float).tolist()
    sell_values = frame[sell_col].astype(float).tolist()
    _require_finite(buy_values, "电价列 buy_price ")
    _require_finite(sell_values, "电价列 sell_price ")
    return expand_price_series(buy_values, horizon), expand_price_series(sell_values, horizon)


def read_hourly_biomass_series(hourly_csv_path: str | Path) -> list[float]:
    """从逐时结果 CSV 读取生物质出力序列（两阶段检修窗定窗的预解依据）。"""
    import csv

    with open(hourly_csv_path, encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return [float(row["biomass_generation"]) for row in rows]


def select_maintenance_window(
    biomass_series: list[float], num_days: int, maint_hours: int
) -> int:
    """两阶段检修窗定窗规则（两套引擎共用，保证行为一致）。

    在预解（不检修）方案上，选"窗口内生物质出力之和最小"的连续检修窗
    （按日起始、可跨年首尾衔接）；并列时取最早起始日（确定性，避免多重
    最优导致两套引擎选窗漂移）。返回起始日（0 起，起始小时 = 起始日×24）。
    """
    horizon = len(biomass_series)
    best_day = 0
    best_sum = None
    for day in range(num_days):
        total = sum(
            biomass_series[(day * 24 + k) % horizon] for k in range(maint_hours)
        )
        if best_sum is None or total < best_sum - 1.0e-9:
            best_day, best_sum = day, total
    return best_day


def export_results_to_csv(
    output_dir: str | Path,
    input_path: str | Path,
    price_path: str | Path | None,
    df: pd.DataFrame,
    buy_price: list[float],
    sell_price: list[float],
    dt: float,
    p_wind: Any,
    p_pv: Any,
    e_ess: Any,
    p_ess: Any,
    green_to_load: dict[int, Any],
    green_to_storage: dict[int, Any],
    green_to_sell: dict[int, Any] | None,
    green_curtail: dict[int, Any],
    grid_to_load: dict[int, Any] | None,
    unmet_load: dict[int, Any] | None,
    storage_to_load: dict[int, Any],
    soc: dict[int, Any],
    objective_value: float,
    initial_investment_cost: float,
    annual_om_cost: float,
    annual_buy_cost: float,
    annual_sell_revenue: float,
    annual_unmet_penalty_cost: float,
    om_cost_npv: float,
    buy_cost_npv: float,
    sell_revenue_npv: float,
    salvage_value_npv: float,
    tax_shield_npv: float,
    discount_rate: float,
    lifecycle_years: int,
    depreciation_years: int,
    income_tax_rate: float,
    salvage_rate: float,
    project_type: str = "grid_connected",
    diesel_to_load: dict[int, Any] | None = None,
    biomass_output: dict[int, Any] | None = None,
    biomass_to_load: dict[int, Any] | None = None,
    biomass_to_sell: dict[int, Any] | None = None,
    # 持续运行模式（v4）：生物质必发富余的弃电通道与检修窗标记。
    biomass_curtail: dict[int, Any] | None = None,
    maintenance_flag: list[float] | None = None,
    maintenance_hours: int = 0,
    # 检修窗起始小时由求解器直接给出（窗口可跨年首尾衔接，不能从标记列
    # 取第一个 1 推断——回卷会把起始误报为 0）。
    maintenance_start_hour: int = -1,
    diesel_capacity: float = 0.0,
    biomass_capacity: float = 0.0,
    annual_diesel_fuel_cost: float = 0.0,
    annual_biomass_fuel_cost: float = 0.0,
    diesel_fuel_cost_npv: float = 0.0,
    biomass_fuel_cost_npv: float = 0.0,
    # 成果工作簿（v4.2）：组件边界与提示用于"装机与边界"页，solver_mode
    # 用于"方案总览"页；工作簿写失败时静默降级为仅 CSV。
    boundary_notes: list[str] | tuple[str, ...] = (),
    solver_mode: str | None = None,
    component_bounds: dict[str, tuple[float, float]] | None = None,
) -> tuple[Path, Path, Path | None]:
    output_dir = Path(output_dir)
    input_path = Path(input_path)
    price_path = Path(price_path) if price_path is not None else None
    output_dir.mkdir(parents=True, exist_ok=True)

    wind_capacity = p_wind.X
    pv_capacity = p_pv.X
    ess_energy = e_ess.X
    ess_power = p_ess.X

    hourly_rows: list[dict[str, float | int]] = []
    for t in range(len(df)):
        wind_generation = wind_capacity * float(df.loc[t, "Wind"])
        pv_generation = pv_capacity * float(df.loc[t, "PV"])
        green_generation = wind_generation + pv_generation
        load_power = float(df.loc[t, "Load"])
        green_to_sell_value = green_to_sell[t].X if green_to_sell is not None else 0.0
        grid_to_load_value = grid_to_load[t].X if grid_to_load is not None else 0.0
        unmet_load_value = unmet_load[t].X if unmet_load is not None else 0.0
        diesel_to_load_value = diesel_to_load[t].X if diesel_to_load is not None else 0.0
        biomass_output_value = biomass_output[t].X if biomass_output is not None else 0.0
        biomass_to_load_value = biomass_to_load[t].X if biomass_to_load is not None else 0.0
        biomass_to_sell_value = biomass_to_sell[t].X if biomass_to_sell is not None else 0.0
        biomass_curtail_value = biomass_curtail[t].X if biomass_curtail is not None else 0.0
        maintenance_value = float(maintenance_flag[t]) if maintenance_flag is not None else 0.0

        hourly_rows.append(
            {
                "hour_index": t,
                "load": load_power,
                "buy_price": float(buy_price[t]),
                "sell_price": float(sell_price[t]),
                "wind_profile": float(df.loc[t, "Wind"]),
                "pv_profile": float(df.loc[t, "PV"]),
                "wind_generation": wind_generation,
                "pv_generation": pv_generation,
                "green_generation": green_generation,
                "green_to_load": green_to_load[t].X,
                "green_to_storage": green_to_storage[t].X,
                "green_to_sell": green_to_sell_value,
                "green_curtail": green_curtail[t].X,
                "grid_to_load": grid_to_load_value,
                "unmet_load": unmet_load_value,
                "storage_to_load": storage_to_load[t].X,
                "soc_energy": soc[t].X,
                "soc_ratio": (soc[t].X / ess_energy) if ess_energy > 1.0e-9 else 0.0,
                "diesel_to_load": diesel_to_load_value,
                "biomass_generation": biomass_output_value,
                "biomass_to_load": biomass_to_load_value,
                "biomass_to_sell": biomass_to_sell_value,
                "biomass_curtail": biomass_curtail_value,
                "biomass_maintenance": maintenance_value,
                "biomass_balance_check": (
                    biomass_output_value
                    - biomass_to_load_value
                    - biomass_to_sell_value
                    - biomass_curtail_value
                ),
                "green_balance_check": (
                    green_generation
                    - green_to_load[t].X
                    - green_to_storage[t].X
                    - green_to_sell_value
                    - green_curtail[t].X
                ),
                "load_balance_check": (
                    green_to_load[t].X
                    + storage_to_load[t].X
                    + grid_to_load_value
                    + unmet_load_value
                    + diesel_to_load_value
                    + biomass_to_load_value
                    - load_power
                ),
            }
        )

    hourly_df = pd.DataFrame(hourly_rows)

    total_load = float((hourly_df["load"] * dt).sum())
    total_green_wind_pv = float((hourly_df["green_generation"] * dt).sum())
    total_biomass = float((hourly_df["biomass_generation"] * dt).sum())
    total_green = total_green_wind_pv + total_biomass
    total_green_to_load = float((hourly_df["green_to_load"] * dt).sum())
    total_green_to_storage = float((hourly_df["green_to_storage"] * dt).sum())
    total_green_to_sell = float((hourly_df["green_to_sell"] * dt).sum())
    total_biomass_to_load = float((hourly_df["biomass_to_load"] * dt).sum())
    total_biomass_to_sell = float((hourly_df["biomass_to_sell"] * dt).sum())
    total_sell = total_green_to_sell + total_biomass_to_sell
    total_green_curtail = float((hourly_df["green_curtail"] * dt).sum())
    total_grid_to_load = float((hourly_df["grid_to_load"] * dt).sum())
    total_storage_to_load = float((hourly_df["storage_to_load"] * dt).sum())
    total_diesel = float((hourly_df["diesel_to_load"] * dt).sum())
    total_unmet = float((hourly_df["unmet_load"] * dt).sum())
    total_self_use = total_green_to_load + total_storage_to_load + total_biomass_to_load
    total_buy_cost = float((hourly_df["grid_to_load"] * hourly_df["buy_price"] * dt).sum())
    total_sell_revenue = float(
        (
            (hourly_df["green_to_sell"] + hourly_df["biomass_to_sell"])
            * hourly_df["sell_price"]
            * dt
        ).sum()
    )

    summary_df = pd.DataFrame(
        [
            {
                "input_file": str(input_path),
                "price_file": str(price_path) if price_path is not None else "",
                "project_type": project_type,
                "timestep_hours": dt,
                "objective_value": objective_value,
                "lifecycle_discounted_total_cost": objective_value,
                "wind_capacity_kw": wind_capacity,
                "pv_capacity_kw": pv_capacity,
                "ess_energy_kwh": ess_energy,
                "ess_power_kw": ess_power,
                "diesel_capacity_kw": diesel_capacity,
                "biomass_capacity_kw": biomass_capacity,
                "storage_hours": (ess_energy / ess_power) if ess_power > 1.0e-9 else 0.0,
                "biomass_capacity_factor_utilized": (
                    total_biomass / (biomass_capacity * len(df) * dt)
                    if biomass_capacity > 1.0e-9
                    else 0.0
                ),
                "discount_rate": discount_rate,
                "lifecycle_years": lifecycle_years,
                "depreciation_years": depreciation_years,
                "income_tax_rate": income_tax_rate,
                "salvage_rate": salvage_rate,
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
                "diesel_fuel_cost_npv": diesel_fuel_cost_npv,
                "biomass_fuel_cost_npv": biomass_fuel_cost_npv,
                "salvage_value_npv": salvage_value_npv,
                "tax_shield_npv": tax_shield_npv,
                "total_load_kwh": total_load,
                "total_green_generation_kwh": total_green,
                "total_biomass_curtail_kwh": float((hourly_df["biomass_curtail"] * dt).sum()),
                "biomass_maintenance_start_hour": (
                    maintenance_start_hour if maintenance_hours > 0 else -1
                ),
                "biomass_maintenance_hours": maintenance_hours,
                "total_green_to_load_kwh": total_green_to_load,
                "total_green_to_storage_kwh": total_green_to_storage,
                "total_storage_to_load_kwh": total_storage_to_load,
                "total_self_use_kwh": total_self_use,
                "total_grid_purchase_kwh": total_grid_to_load,
                "total_green_sell_kwh": total_sell,
                "total_green_curtail_kwh": total_green_curtail,
                "total_unmet_kwh": total_unmet,
                "total_diesel_generation_kwh": total_diesel,
                "total_biomass_generation_kwh": total_biomass,
                "total_biomass_to_load_kwh": total_biomass_to_load,
                "total_biomass_to_sell_kwh": total_biomass_to_sell,
                "total_buy_cost": total_buy_cost,
                "total_sell_revenue": total_sell_revenue,
                "net_system_cost": total_buy_cost - total_sell_revenue,
                "self_use_ratio_of_green": (
                    total_self_use / total_green if total_green > 1.0e-9 else 0.0
                ),
                "self_use_ratio_of_load": (
                    total_self_use / total_load if total_load > 1.0e-9 else 0.0
                ),
                "sell_ratio_of_green": (
                    total_sell / total_green if total_green > 1.0e-9 else 0.0
                ),
                "curtail_ratio_of_green": (
                    total_green_curtail / total_green if total_green > 1.0e-9 else 0.0
                ),
                "loss_ratio_of_load": (
                    total_unmet / total_load if total_load > 1.0e-9 else 0.0
                ),
            }
        ]
    )

    hourly_csv_path = output_dir / "green_direct_hourly_results.csv"
    summary_csv_path = output_dir / "green_direct_summary_results.csv"
    hourly_df.to_csv(hourly_csv_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_csv_path, index=False, encoding="utf-8-sig")

    # 成果工作簿（v4.2）：面向用户的单一 Excel 交付物；失败静默降级为仅 CSV。
    excel_path: Path | None = None
    try:
        from .excel_report import write_results_workbook

        excel_path = write_results_workbook(
            output_dir / "green_direct_results.xlsx",
            summary=summary_df.iloc[0].to_dict(),
            hourly_rows=hourly_rows,
            project_type=project_type,
            diesel_enabled=diesel_to_load is not None,
            biomass_enabled=biomass_output is not None,
            biomass_continuous=biomass_curtail is not None,
            maintenance_hours=maintenance_hours,
            maintenance_start_hour=maintenance_start_hour,
            component_bounds=component_bounds,
            boundary_notes=boundary_notes,
            solver_mode=solver_mode,
        )
    except Exception:  # noqa: BLE001 - 工作簿是增值交付物，失败不阻断结果
        excel_path = None

    return hourly_csv_path, summary_csv_path, excel_path
