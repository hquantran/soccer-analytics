"""MetricFlow CLI entry point with arguments loaded from a private request file."""
import json
from pathlib import Path
import sys


def main():
    from dbt_metricflow.cli.main import cli
    arguments = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    cli(args=arguments, prog_name='mf')


if __name__ == '__main__':
    main()
