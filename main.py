from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ip_summary.config import Settings, load_settings
from ip_summary.pipeline import (
    aggregate_to_outputs,
    load_headers,
    process_contracts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM-based IP contract summarizer")
    parser.add_argument(
        "--config",
        default="config/deepseek_config.yaml",
        help="Path to YAML config. Default: config/deepseek_config.yaml",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Classify and extract contracts")
    run_parser.add_argument("--my-party", required=True, help="我方主体，例如：深圳腾讯")
    run_parser.add_argument(
        "--input-dir", default=None, help="Override input folder containing contracts"
    )
    run_parser.add_argument(
        "--intermediate-dir", default=None, help="Override intermediate output folder"
    )
    run_parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Max concurrent LLM calls (default from config)",
    )
    run_parser.add_argument(
        "--upstream-headers",
        default="表头字段/版权授权链-上游类-表头信息.xlsx",
        help="Path to upstream header Excel",
    )
    run_parser.add_argument(
        "--downstream-headers",
        default="表头字段/版权授权链-下游类-表头信息.xlsx",
        help="Path to downstream header Excel",
    )
    run_parser.add_argument(
        "--force-direction",
        choices=["upstream", "downstream"],
        default=None,
        help="Force direction for all contracts (skip auto classification)",
    )

    agg_parser = subparsers.add_parser("aggregate", help="Aggregate user-reviewed JSON to CSV/Excel")
    agg_parser.add_argument(
        "--direction",
        choices=["upstream", "downstream"],
        required=True,
        help="Choose which contract direction to aggregate",
    )
    agg_parser.add_argument(
        "--basename",
        default=None,
        help="Output file basename (default: direction_YYYYMMDD_HHMMSS)",
    )
    agg_parser.add_argument(
        "--intermediate-dir", default=None, help="Override intermediate folder"
    )
    agg_parser.add_argument("--final-dir", default=None, help="Override final folder")
    agg_parser.add_argument("--history-dir", default=None, help="Override history folder")
    agg_parser.add_argument(
        "--upstream-headers",
        default="表头字段/版权授权链-上游类-表头信息.xlsx",
        help="Path to upstream header Excel",
    )
    agg_parser.add_argument(
        "--downstream-headers",
        default="表头字段/版权授权链-下游类-表头信息.xlsx",
        help="Path to downstream header Excel",
    )

    return parser.parse_args()


def apply_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    pipeline = settings.pipeline
    if getattr(args, "input_dir", None):
        pipeline = pipeline.model_copy(update={"input_dir": Path(args.input_dir).resolve()})
    if getattr(args, "intermediate_dir", None):
        pipeline = pipeline.model_copy(
            update={"intermediate_dir": Path(args.intermediate_dir).resolve()}
        )
    if getattr(args, "final_dir", None):
        pipeline = pipeline.model_copy(update={"final_dir": Path(args.final_dir).resolve()})
    if getattr(args, "history_dir", None):
        pipeline = pipeline.model_copy(update={"history_dir": Path(args.history_dir).resolve()})
    if getattr(args, "concurrency", None):
        pipeline = pipeline.model_copy(update={"concurrent_requests": args.concurrency})
    return Settings(llm=settings.llm, pipeline=pipeline)


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    settings = load_settings(config_path)
    settings = apply_overrides(settings, args)

    if args.command == "run":
        upstream_headers = Path(args.upstream_headers)
        downstream_headers = Path(args.downstream_headers)
        asyncio.run(
            process_contracts(
                settings,
                args.my_party,
                upstream_headers,
                downstream_headers,
                force_direction=args.force_direction,
            )
        )
    elif args.command == "aggregate":
        headers = load_headers(Path(args.upstream_headers), Path(args.downstream_headers))
        basename = args.basename or f"{args.direction}_{datetime.now():%Y%m%d_%H%M%S}"
        outputs = aggregate_to_outputs(settings, headers, args.direction, basename)
        print(f"Wrote outputs: {outputs}")


if __name__ == "__main__":
    main()
