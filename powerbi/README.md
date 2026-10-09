# Power BI connection layer

The Power BI path imports `fct_player_seasons`, `dim_players`, `dim_teams`,
and `dim_leagues` directly from Databricks. A season dimension is derived at
import. Streamlit separately reads `bi_player_seasons`, the scouting mart.
MetricFlow is optional for experiments and is not required by either dashboard.

`semantic-model.tmdl` defines the import partitions, four one-to-many,
single-direction relationships, 16 weighted rate measures, totals and weighted
rating. Rate formulas are generated from `dbt_project.yml`; regenerate with:

```powershell
.\.venv-analytics\Scripts\python.exe -m scripts.generate_power_bi_model
```

To connect, create a **blank** Power BI Desktop report, open Model > TMDL view,
paste `semantic-model.tmdl`, replace the four connection placeholders using your
workspace host, warehouse HTTP path, catalog and curated schema, then Apply and
refresh. Authenticate through Power BI's connector prompt; do not paste tokens
into this script. This script replaces the model, so use a blank report.

Alternatively, use Get Data > Azure Databricks to import the four tables, create
the dimension-to-fact relationships on their IDs, and add the measures from
`measures.dax`. Add a season slicer using the fact's season column in this route.

Use dimension names for slicers and explicit measures for chart values. Percentage
measures already multiply by 100; the TMDL format uses a literal percent symbol.
Never average stored per-90 values. Missing completed passes produce blank
accuracy when no completion estimate exists; zero denominators return blank.
Player age reflects the latest player attribute, not historical age by season.
Facts retain the existing 300-minute stint threshold, including goalkeepers;
apply position filters for outfield comparisons. Season is a season-start year,
not a match date. Streamlit's scouting mart excludes goalkeepers.

This is a source-controlled semantic-model starter, not a report or a hosted
endpoint. TMDL/M/DAX application and refresh still require validation in Desktop.
Save populated reports privately; `.pbix` files contain imported data.

References: [TMDL import workflow](https://learn.microsoft.com/en-us/power-bi/create-reports/tutorial-end-to-end-power-bi),
[Databricks connector](https://learn.microsoft.com/en-us/power-query/connectors/databricks-azure),
[star schema modeling](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).
