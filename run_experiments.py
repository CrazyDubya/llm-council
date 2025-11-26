import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict, Tuple, List

from backend.analytics import AnalyticsEngine
from backend.config import CHAIRMAN_MODEL, COUNCIL_MODELS
from backend.openrouter import reset_call_log, summarize_call_log
from backend.pricing import PricingManager
from backend.strategies import get_strategy

DEFAULT_QUESTION = (
    "How could a coastal city repurpose a retired offshore oil platform into "
    "a climate-resilient aquaculture and research hub while generating revenue "
    "within five years?"
)

AVAILABLE_COUNCILS = {
    'full': {
        'models': COUNCIL_MODELS,
        'chairman': CHAIRMAN_MODEL,
    },
    'low_cost': {
        'models': [
            'anthropic/claude-haiku-4.5',
            'google/gemini-2.5-flash-lite',
            'openai/gpt-5-mini',
            'openai/gpt-5-nano',
        ],
        'chairman': 'anthropic/claude-haiku-4.5',
    },
}

DEFAULT_STRATEGIES = ['simple', 'multi_round', 'weighted_voting']


def parse_council_definition(raw: str) -> Tuple[str, Dict[str, List[str]]]:
    """Parse CLI council definition in the form name=chairman:model1,model2"""
    if '=' not in raw or ':' not in raw:
        raise ValueError(
            "Custom council must be in the form name=chairman:model1,model2"
        )
    name, remainder = raw.split('=', 1)
    chairman, models_part = remainder.split(':', 1)
    models = [m.strip() for m in models_part.split(',') if m.strip()]
    if not models:
        raise ValueError('Custom council requires at least one model')
    return name.strip(), {'chairman': chairman.strip(), 'models': models}


def build_council_map(args) -> Dict[str, Dict[str, List[str]]]:
    councils = dict(AVAILABLE_COUNCILS)
    for raw in args.council_def or []:
        name, definition = parse_council_definition(raw)
        councils[name] = definition
    if args.council:
        missing = [name for name in args.council if name not in councils]
        if missing:
            raise ValueError(f"Unknown council(s): {', '.join(missing)}")
        councils = {name: councils[name] for name in args.council}
    return councils


def build_strategy_list(args, analytics: AnalyticsEngine):
    strategies = args.strategy or DEFAULT_STRATEGIES
    configs = []
    for name in strategies:
        config = {}
        if name == 'weighted_voting':
            config['analytics_engine'] = analytics
        configs.append((name, config))
    return configs


def load_question(args) -> str:
    if args.question_file:
        return Path(args.question_file).read_text().strip()
    if args.question:
        return args.question
    return DEFAULT_QUESTION


def format_plan(strategies, councils, question, output_dir):
    lines = ["Experiment plan:"]
    lines.append(f"Question: {question}")
    lines.append(f"Output dir: {output_dir}")
    for strategy, _ in strategies:
        for council_name in councils:
            lines.append(f" - {strategy} on council '{council_name}'")
    return '\n'.join(lines)


def create_parser():
    parser = argparse.ArgumentParser(description='Run LLM Council experiments.')
    parser.add_argument('--question', help='Override the default question text')
    parser.add_argument('--question-file', help='Read the question from a text file')
    parser.add_argument(
        '--strategy',
        action='append',
        help='Strategy name to run (can be specified multiple times)'
    )
    parser.add_argument(
        '--council',
        action='append',
        help='Council name to run (full, low_cost, or custom added via --council-def)'
    )
    parser.add_argument(
        '--council-def',
        action='append',
        help='Define a custom council: name=chairman:model1,model2'
    )
    parser.add_argument(
        '--output-dir',
        default='experiment_outputs',
        help='Directory to store experiment JSON files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the experiment plan without calling any models'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available strategies and councils and exit'
    )
    return parser


async def run_strategy(strategy_name, config, council_name, council, question, pricing, output_dir):
    strategy = get_strategy(strategy_name, config=dict(config))
    reset_call_log()
    result = await strategy.execute(
        query=question,
        models=council['models'],
        chairman=council['chairman']
    )
    usage_summary = summarize_call_log(pricing.estimate_cost)
    result.setdefault('metadata', {})['api_usage'] = usage_summary
    output = {
        'strategy': strategy_name,
        'council': council_name,
        'question': question,
        'models': council['models'],
        'chairman': council['chairman'],
        'result': result,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{strategy_name}_{council_name}.json"
    output_path.write_text(json.dumps(output, indent=2))
    return output_path


async def main_async(args):
    question = load_question(args)
    councils = build_council_map(args)
    analytics = AnalyticsEngine()
    pricing = PricingManager()
    strategies = build_strategy_list(args, analytics)
    output_dir = Path(args.output_dir)

    if args.list:
        print('Available strategies:', ', '.join(DEFAULT_STRATEGIES))
        print('Available councils:', ', '.join(sorted(councils.keys())))
        return

    plan = format_plan(strategies, councils, question, output_dir)
    if args.dry_run:
        print(plan)
        return

    print(plan)
    saved = []
    for strategy_name, config in strategies:
        for council_name, council in councils.items():
            path = await run_strategy(
                strategy_name,
                config,
                council_name,
                council,
                question,
                pricing,
                output_dir
            )
            saved.append(path)
            print(f"Saved {path}")


def main():
    parser = create_parser()
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
