"""Generate a credential-free Power BI semantic model from the shared rates."""
from pathlib import Path

from config.metrics import CANONICAL_METRICS
from dashboard.metrics_config import ADDITIVE_COLS

ROOT = Path(__file__).resolve().parents[1]


def dax_rate(contract, table='fct_player_seasons'):
    inputs = contract['numerator']
    inputs = [inputs] if isinstance(inputs, str) else inputs
    numerator = ' + '.join(f'SUM({table}[{column}])' for column in inputs)
    if len(inputs) > 1:
        numerator = '(' + numerator + ')'
    return f"DIVIDE({contract['scale']} * {numerator}, SUM({table}[{contract['denominator']}]))"


def generate():
    fact = {'player_season_id': 'string', 'player_id': 'int64', 'team_id': 'int64',
            'league_id': 'int64', 'season': 'int64', 'position': 'string',
            'injured': 'boolean', 'rating': 'double',
            **{column: 'int64' for column in ADDITIVE_COLS}}
    fact['passes_completed'] = 'double'
    tables = {'fct_player_seasons': fact,
              'dim_players': {'player_id': 'int64', 'name': 'string', 'nationality': 'string', 'age': 'int64'},
              'dim_teams': {'team_id': 'int64', 'team_name': 'string'},
              'dim_leagues': {'league_id': 'int64', 'league_name': 'string'},
              'dim_seasons': {'season': 'int64', 'season_label': 'string'}}
    script = ['createOrReplace', '\tmodel Model', '\t\tculture: en-US',
              '\t\tdefaultPowerBIDataSourceVersion: powerBI_V3', '\t\tsourceQueryCulture: en-US']
    for table, columns in tables.items():
        script += ['', f'\t\ttable {table}']
        for column, datatype in columns.items():
            script += ['', f'\t\t\tcolumn {column}', f'\t\t\t\tdataType: {datatype}',
                       '\t\t\t\tsummarizeBy: none', f'\t\t\t\tsourceColumn: {column}']
            if table == 'fct_player_seasons' and column not in ('position', 'injured'):
                script.append('\t\t\t\tisHidden')
            elif column.endswith('_id'):
                script.append('\t\t\t\tisHidden')
        if table == 'fct_player_seasons':
            measures = {key: dax_rate(contract) for key, contract in CANONICAL_METRICS.items()}
            measures.update({'minutes_total': 'SUM(fct_player_seasons[minutes])',
                             'goals_total': 'SUM(fct_player_seasons[goals])',
                             'assists_total': 'SUM(fct_player_seasons[assists])',
                             'players_count': 'DISTINCTCOUNT(fct_player_seasons[player_id])',
                             'rating_weighted': 'DIVIDE(SUMX(fct_player_seasons, COALESCE(fct_player_seasons[rating], 0) * fct_player_seasons[minutes]), SUM(fct_player_seasons[minutes]))'})
            for name, expression in measures.items():
                format_string = '0.0"%"' if name.endswith('_pct') else '0.00'
                script += ['', f'\t\t\tmeasure {name} = {expression}',
                           f'\t\t\t\tformatString: {format_string}', '\t\t\t\tdisplayFolder: Performance']
        source_table = 'fct_player_seasons' if table == 'dim_seasons' else table
        script += ['', f'\t\t\tpartition {table} = m', '\t\t\t\tmode: import', '\t\t\t\tsource =']
        m = ['let',
             '    Source = Databricks.Catalogs("<DATABRICKS_HOST>", "<DATABRICKS_HTTP_PATH>", [Catalog=null, Database=null]),',
             '    Catalog = Source{[Name="<DATABRICKS_CATALOG>",Kind="Database"]}[Data],',
             '    Schema = Catalog{[Name="<DATABRICKS_SCHEMA>",Kind="Schema"]}[Data],',
             f'    Data = Schema{{[Name="{source_table}",Kind="Table"]}}[Data],']
        if table == 'dim_seasons':
            m += ['    Seasons = Table.Distinct(Table.SelectColumns(Data, {"season"})),',
                  '    Selected = Table.AddColumn(Seasons, "season_label", each Text.From([season]) & "/" & Text.From([season]+1), type text)']
        else:
            names = ', '.join('"' + name + '"' for name in columns)
            m += [f'    Selected = Table.SelectColumns(Data, {{{names}}})']
        m += ['in', '    Selected']
        script += ['\t\t\t\t\t' + line for line in m]
    for dimension, key in [('dim_players', 'player_id'), ('dim_teams', 'team_id'),
                           ('dim_leagues', 'league_id'), ('dim_seasons', 'season')]:
        script += ['', f'\t\trelationship fact_{dimension}',
                   f'\t\t\tfromColumn: fct_player_seasons.{key}',
                   f'\t\t\ttoColumn: {dimension}.{key}',
                   '\t\t\tfromCardinality: many', '\t\t\ttoCardinality: one',
                   '\t\t\tcrossFilteringBehavior: oneDirection']
    return '\n'.join(script) + '\n'


if __name__ == '__main__':
    folder = ROOT / 'powerbi'
    folder.mkdir(exist_ok=True)
    (folder / 'semantic-model.tmdl').write_text(generate(), encoding='utf-8')
    (folder / 'measures.dax').write_text('\n'.join(
        f'{name} = {dax_rate(contract)}' for name, contract in CANONICAL_METRICS.items()) + '\n', encoding='utf-8')
    print('Generated Power BI semantic model and 16 measures; no credentials or data embedded.')
