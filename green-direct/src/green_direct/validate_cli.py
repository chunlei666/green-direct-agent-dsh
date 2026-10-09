from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_optimization_config
from .validation import save_validation_report, validate_solution_outputs


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    repo_root = _default_repo_root()
    parser = argparse.ArgumentParser(description="绿色直供结果独立验证命令")
    parser.add_argument(
        "--data",
        default=str(repo_root / "data" / "examples" / "microgrid_test_data.csv"),
        help="负荷/光伏/风电时序数据文件。",
    )
    parser.add_argument(
        "--price",
        default=str(repo_root / "data" / "examples" / "price_24h.csv"),
        help="购电价/售电价文件。",
    )
    parser.add_argument(
        "--config",
        default=str(repo_root / "config" / "defaults.json"),
        help="优化参数配置文件。",
    )
    parser.add_argument(
        "--hourly-results",
        default=str(repo_root / "outputs" / "green_direct_hourly_results.csv"),
        help="逐时结果文件。",
    )
    parser.add_argument(
        "--summary-results",
        default=str(repo_root / "outputs" / "green_direct_summary_results.csv"),
        help="汇总结果文件。",
    )
    parser.add_argument(
        "--report",
        default=str(repo_root / "outputs" / "validation_report.json"),
        help="验证报告输出路径。",
    )
    parser.add_argument(
        "--balance-tolerance",
        type=float,
        default=1.0e-4,
        help="平衡类约束容差。",
    )
    parser.add_argument(
        "--ratio-tolerance",
        type=float,
        default=1.0e-6,
        help="比例类约束容差。",
    )
    parser.add_argument(
        "--objective-tolerance",
        type=float,
        default=1.0e-4,
        help="经济性重构容差。",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_optimization_config(args.config)
    report = validate_solution_outputs(
        data_path=args.data,
        price_path=args.price,
        hourly_results_path=args.hourly_results,
        summary_results_path=args.summary_results,
        config=config,
        balance_tolerance=args.balance_tolerance,
        ratio_tolerance=args.ratio_tolerance,
        objective_tolerance=args.objective_tolerance,
    )
    report_path = save_validation_report(report, args.report)

    print(f"validation_passed: {report.passed}")
    print(f"total_checks: {report.total_checks}")
    print(f"passed_checks: {report.passed_checks}")
    print(f"failed_checks: {report.failed_checks}")
    print(f"report: {report_path}")

    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        metric_text = "" if check.metric is None else f", metric={check.metric:.6g}"
        threshold_text = "" if check.threshold is None else f", threshold={check.threshold:.6g}"
        print(f"[{status}] {check.name}{metric_text}{threshold_text} - {check.details}")

    if not report.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
