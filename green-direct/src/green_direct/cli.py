from __future__ import annotations

import argparse
from pathlib import Path

from .config import OptimizationConfig, load_optimization_config, save_optimization_config
from .solver import build_and_solve_model


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    repo_root = _default_repo_root()
    default_profile = repo_root / "data" / "examples" / "microgrid_test_data.csv"
    default_price = repo_root / "data" / "examples" / "price_24h.csv"
    default_output = repo_root / "outputs"
    default_config = repo_root / "config" / "defaults.json"

    parser = argparse.ArgumentParser(
        description="绿色直供优化项目命令行入口",
    )
    parser.add_argument(
        "--data",
        default=str(default_profile),
        help="负荷/光伏/风电时序数据文件，支持 CSV/XLSX/XLS。",
    )
    parser.add_argument(
        "--price",
        default=str(default_price),
        help="购电价/售电价文件，支持 CSV/XLSX/XLS。",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_output),
        help="结果输出目录。",
    )
    parser.add_argument(
        "--config",
        default=str(default_config),
        help="优化参数配置文件，支持 YAML/JSON。",
    )
    parser.add_argument(
        "--write-default-config",
        default=None,
        help="将默认配置模板写出到指定路径后退出，支持 YAML/JSON。",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.write_default_config:
        output_path = save_optimization_config(OptimizationConfig(), args.write_default_config)
        print(f"default_config: {output_path}")
        return

    config = load_optimization_config(args.config)

    result = build_and_solve_model(
        data_path=args.data,
        price_path=args.price,
        output_dir=args.output_dir,
        config=config,
    )

    print(f"Status: {result.status}")
    print(f"Objective: {result.objective_value:.6f}")
    print(f"config: {args.config}")
    for name, value in result.installed_capacities.items():
        print(f"{name}: {value:.6f}")
    print(f"hourly_csv: {result.hourly_csv_path}")
    print(f"summary_csv: {result.summary_csv_path}")


if __name__ == "__main__":
    main()
