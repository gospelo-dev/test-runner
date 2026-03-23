"""CLI entry point for gospelo-test-runner."""

from __future__ import annotations

import argparse
import sys

from .types import TestCase, TestSuiteConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gospelo-test-runner",
        description="gospelo test-runner: Generic test execution harness",
    )
    parser.add_argument(
        "--version", action="store_true",
        help="Show version and exit",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run ---
    run_parser = subparsers.add_parser(
        "run", help="Execute tests from a spec JSON or YAML",
    )
    run_parser.add_argument(
        "--config", "-c",
        help="Path to config file (yml or JSON)",
    )
    spec_group = run_parser.add_mutually_exclusive_group(required=True)
    spec_group.add_argument(
        "--spec-json",
        help="Path to test spec JSON (test_spec.json)",
    )
    spec_group.add_argument(
        "--spec-yml",
        help="Path to test spec YAML (api_test_data.yml)",
    )
    run_parser.add_argument(
        "--test-id",
        help="Run only the specified test case ID",
    )
    run_parser.add_argument(
        "--category",
        help="Run only test cases matching category prefix",
    )
    run_parser.add_argument(
        "--list", action="store_true",
        help="List test cases without executing",
    )
    run_parser.add_argument(
        "--dry-run", action="store_true",
        help="Show requests without executing",
    )
    run_parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay between test cases in seconds (default: 1.0)",
    )
    run_parser.add_argument(
        "--output-dir", default="logs",
        help="Directory for evidence output (default: logs)",
    )
    run_parser.add_argument(
        "--export-spec", action="store_true",
        help="Export test spec JSON and exit",
    )
    run_parser.add_argument(
        "--executor", default="http",
        help="Executor type (default: http). Use --list-executors to see available executors",
    )
    run_parser.add_argument(
        "--list-executors", action="store_true",
        help="List available executor plugins and exit",
    )

    # --- version ---
    subparsers.add_parser(
        "version", help="Show version and format information",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        _cmd_version()
        sys.exit(0)

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "version":
        _cmd_version()
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_run(args: argparse.Namespace) -> None:
    from .executor.registry import get_executor_class, list_executors
    from .loader.config_loader import DEFAULT_CONFIG_SCHEMA, load_config
    from .loader.spec_loader import load_spec_json, load_spec_yml
    from .reporter.spec_exporter import export_test_spec
    from .runner import list_cases, run_suite
    from .types import TestStatus

    # List executors mode
    if args.list_executors:
        names = list_executors()
        print("Available executors:")
        for name in names:
            print(f"  {name}")
        sys.exit(0)

    # Load config
    config: dict = {}
    if args.config:
        config = load_config(args.config, schema=DEFAULT_CONFIG_SCHEMA)

    # Load test cases from spec JSON or YAML
    if args.spec_yml:
        test_name, test_id_prefix, groups = load_spec_yml(args.spec_yml)
    else:
        test_name, test_id_prefix, groups = load_spec_json(args.spec_json)
    cases: list[TestCase] = []
    for group_cases in groups.values():
        cases.extend(group_cases)

    # List mode
    if args.list:
        list_cases(cases)
        sys.exit(0)

    # Export spec mode
    if args.export_spec:
        out_path = export_test_spec(
            cases, test_name, test_id_prefix,
            script_prefix=test_id_prefix,
            output_dir=args.output_dir,
        )
        print(f"Spec exported: {out_path}")
        sys.exit(0)

    # Build suite config
    suite_config = TestSuiteConfig(
        test_name=test_name,
        test_id_prefix=test_id_prefix,
        script_prefix=test_id_prefix,
        config=config,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        delay=args.delay,
        test_id_filter=args.test_id,
        category_filter=args.category,
    )

    # Select executor via plugin registry
    executor_cls = get_executor_class(args.executor)
    executor = executor_cls(suite_config)

    # Run
    results = run_suite(suite_config, cases, executor)

    # Exit code: non-zero if any NG or ERROR
    has_failures = any(r.status in (TestStatus.NG, TestStatus.ERROR) for r in results)
    sys.exit(1 if has_failures else 0)


def _cmd_version() -> None:
    from .version import FORMAT_VERSION, get_version_info

    info = get_version_info()
    print(f"gospelo-test-runner {info['package_version']}")
    print(f"Format version: {FORMAT_VERSION}")


if __name__ == "__main__":
    main()
