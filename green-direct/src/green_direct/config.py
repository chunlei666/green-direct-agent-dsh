from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar, get_type_hints


@dataclass(frozen=True)
class ProjectParameters:
    # 项目类型：grid_connected（并网）| offgrid（离网）。
    # 离网模式：无购电/售电，引入失负荷变量；惩罚与 LPUE 上限仅在离网模式生效。
    type: str = "grid_connected"
    loss_of_load_penalty_per_kwh: float = 10.0
    max_loss_ratio_of_load: float | None = None


@dataclass(frozen=True)
class SolverParameters:
    # 求解引擎模式（内部代号，对外一律呈现引擎名称，绝不出现品牌名）：
    #   default   = 天枢（主引擎，成熟稳定）
    #   alternate = 天璇（备选引擎，独立方法实现）
    #   dual      = 双擎互证（两引擎同时求解并交叉核对目标值，最稳妥，耗时约2倍）
    mode: str = "default"


@dataclass(frozen=True)
class DieselParameters:
    # 柴油发电机：离网项目兜底电源（并网项目也可配置，但经济性通常不占优）。
    # enabled=false 时不创建任何变量与约束（与历史模型完全一致）。
    enabled: bool = False
    capex_per_kw: float = 1000.0
    fixed_om_per_kw_year: float = 50.0
    # 综合燃料边际成本（含油料与耗材），按发电量计。
    fuel_cost_per_kwh: float = 2.2
    min_capacity_kw: float = 0.0
    max_capacity_kw: float = 5000.0


@dataclass(frozen=True)
class BiomassParameters:
    # 生物质发电：可调度绿电电源，并网/离网均可参与；计入绿电口径。
    # enabled=false 时不创建任何变量与约束（与历史模型完全一致）。
    enabled: bool = False
    capex_per_kw: float = 9000.0
    fixed_om_per_kw_year: float = 250.0
    # 燃料边际成本（含收集、运输与预处理），按发电量计。
    fuel_cost_per_kwh: float = 0.65
    # 最大容量因子（可调度上限 = 装机 × capacity_factor）。
    capacity_factor: float = 0.85
    # 燃料年可用量上限（电量口径）；null = 不设上限。
    max_annual_energy_kwh: float | None = None
    # 持续运行模式（v4）：生物质机组启停昂贵，须持续运行。
    # min_output_ratio: 最小出力比例（占装机）；运行时段出力下限 = 比例 × 装机。
    #   0 = 不设最小出力（自由调度，历史行为）。参考值 0.5，由用户确认。
    # maintenance_days: 年检修天数。每年一个连续检修窗（按日 0 点起始、按日粒度、
    #   可跨年首尾衔接），窗口内出力为 0；窗口起止由优化在全年范围内自动选择。
    #   0 = 不检修。参考值 5~10 天，由用户确认。
    # 两者默认均为 0（历史行为），使旧项目档案重新求解/校验的结果不变。
    min_output_ratio: float = 0.0
    maintenance_days: float = 0.0
    min_capacity_kw: float = 0.0
    max_capacity_kw: float = 5000.0


@dataclass(frozen=True)
class CostParameters:
    wind_capex_per_kw: float = 7000.0
    pv_capex_per_kw: float = 5500.0
    ess_energy_capex_per_kwh: float = 1100.0
    ess_power_capex_per_kw: float = 500.0
    wind_om_per_kw_year: float = 120.0
    pv_om_per_kw_year: float = 45.0
    ess_energy_om_per_kwh_year: float = 20.0
    ess_power_om_per_kw_year: float = 10.0


@dataclass(frozen=True)
class StorageParameters:
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9
    soc_min_ratio: float = 0.1
    soc_max_ratio: float = 0.9
    min_storage_hours: float = 2.0
    max_storage_hours: float = 8.0


@dataclass(frozen=True)
class PolicyConstraints:
    min_self_use_ratio_of_green: float = 0.60
    min_self_use_ratio_of_load: float = 0.30
    max_sell_ratio_of_green: float = 0.20


@dataclass(frozen=True)
class FinancialParameters:
    discount_rate: float = 0.08
    lifecycle_years: int = 20
    depreciation_years: int = 15
    income_tax_rate: float = 0.25
    salvage_rate: float = 0.05


@dataclass(frozen=True)
class CapacityBounds:
    wind_capacity_kw_max: float = 5000.0
    pv_capacity_kw_max: float = 5000.0
    ess_energy_kwh_max: float = 10000.0
    ess_power_kw_max: float = 5000.0
    grid_import_kw_max: float = 100000.0
    grid_export_kw_max: float = 100000.0


@dataclass(frozen=True)
class OptimizationConfig:
    timestep_hours: float = 1.0
    project: ProjectParameters = field(default_factory=ProjectParameters)
    solver: SolverParameters = field(default_factory=SolverParameters)
    costs: CostParameters = field(default_factory=CostParameters)
    storage: StorageParameters = field(default_factory=StorageParameters)
    diesel: DieselParameters = field(default_factory=DieselParameters)
    biomass: BiomassParameters = field(default_factory=BiomassParameters)
    policy: PolicyConstraints = field(default_factory=PolicyConstraints)
    finance: FinancialParameters = field(default_factory=FinancialParameters)
    bounds: CapacityBounds = field(default_factory=CapacityBounds)


ConfigType = TypeVar("ConfigType")


def config_to_dict(config: OptimizationConfig) -> dict[str, Any]:
    return asdict(config)


def _build_dataclass(dataclass_type: type[ConfigType], values: dict[str, Any] | None) -> ConfigType:
    if values is None:
        return dataclass_type()
    if not isinstance(values, dict):
        raise TypeError(f"Expected a mapping for {dataclass_type.__name__}, got {type(values).__name__}.")

    dataclass_fields = {item.name: item for item in fields(dataclass_type)}
    type_hints = get_type_hints(dataclass_type)
    unknown_keys = sorted(set(values) - set(dataclass_fields))
    if unknown_keys:
        unknown_text = ", ".join(unknown_keys)
        raise ValueError(f"Unknown fields for {dataclass_type.__name__}: {unknown_text}")

    kwargs: dict[str, Any] = {}
    for name, value in values.items():
        field_type = type_hints.get(name, dataclass_fields[name].type)
        if is_dataclass(field_type):
            kwargs[name] = _build_dataclass(field_type, value)
        else:
            kwargs[name] = value
    return dataclass_type(**kwargs)


VALID_SOLVER_MODES = ("default", "alternate", "dual")


def optimization_config_from_dict(values: dict[str, Any] | None) -> OptimizationConfig:
    config = _build_dataclass(OptimizationConfig, values)
    # 跨字段校验：启用组件的装机上下界必须有序。求解器对 lb>ub 的行为
    # 不可依赖（会静默取 lb），必须在配置加载处 fail-fast（USAGE_ERROR）。
    for component_name, component in (("diesel", config.diesel), ("biomass", config.biomass)):
        if component.enabled and component.min_capacity_kw > component.max_capacity_kw:
            raise ValueError(
                f"{component_name}.min_capacity_kw ({component.min_capacity_kw}) "
                f"大于 {component_name}.max_capacity_kw ({component.max_capacity_kw})，"
                "装机上下界无效。"
            )
    # 持续运行模式参数（v4）：必须在进入引擎前 fail-fast，避免静默取 0。
    biomass_cfg = config.biomass
    if biomass_cfg.enabled:
        if not 0.0 <= biomass_cfg.min_output_ratio < 1.0:
            raise ValueError(
                f"biomass.min_output_ratio 必须在 [0, 1) 内，收到 {biomass_cfg.min_output_ratio}。"
            )
        if not 0.0 <= biomass_cfg.maintenance_days <= 365.0:
            raise ValueError(
                f"biomass.maintenance_days 必须在 [0, 365] 内，收到 {biomass_cfg.maintenance_days}。"
            )
        if biomass_cfg.maintenance_days > 0.0 and round(biomass_cfg.maintenance_days * 24) >= 8760:
            raise ValueError(
                f"biomass.maintenance_days ({biomass_cfg.maintenance_days}) 的检修时长覆盖全年，"
                "机组将全年停运，请调小检修天数。"
            )
    if config.solver.mode not in VALID_SOLVER_MODES:
        allowed = "/".join(VALID_SOLVER_MODES)
        raise ValueError(f"solver.mode 必须是 {allowed} 之一，收到 {config.solver.mode!r}。")
    return config


def _load_yaml_config(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "YAML configuration requires PyYAML. Please install it with `python -m pip install pyyaml`."
        ) from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected a mapping in config file {path}, got {type(data).__name__}.")
    return data


def load_optimization_config(config_path: str | Path | None = None) -> OptimizationConfig:
    if config_path is None:
        return OptimizationConfig()

    path = Path(config_path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        data = _load_yaml_config(path)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}. Use .json, .yaml, or .yml.")

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected a mapping in config file {path}, got {type(data).__name__}.")
    return optimization_config_from_dict(data)


def save_optimization_config(config: OptimizationConfig, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = config_to_dict(config)
    suffix = path.suffix.lower()

    if suffix == ".json":
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise ImportError(
                "YAML configuration requires PyYAML. Please install it with `python -m pip install pyyaml`."
            ) from exc
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    raise ValueError(f"Unsupported config format: {path.suffix}. Use .json, .yaml, or .yml.")
