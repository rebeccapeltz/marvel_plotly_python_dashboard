import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# --------------------
# Load and prepare data
# --------------------
df = pd.read_csv("marvel_clean.csv")

# Ensure numeric columns
num_cols = [
    "Budget",
    "OpeningWeekendNorthAmerica",
    "NorthAmerica",
    "OtherTerritories",
    "Worldwide",
]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Parse date and year
df["ReleaseDateUS"] = pd.to_datetime(df["ReleaseDateUS"], errors="coerce")
df["Year"] = df["ReleaseDateUS"].dt.year

# ROI
df["ROI"] = (df["Worldwide"] - df["Budget"]) / df["Budget"]

# --------------------
# Dash app
# --------------------
app = dash.Dash(__name__)

distributor_options = [{"label": d, "value": d} for d in sorted(df["Distributor"].unique())]

app.layout = html.Div(
    style={"fontFamily": "Arial", "margin": "20px"},
    children=[
        html.H1("Marvel Movies Performance Dashboard"),

        # Slicers
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    style={"minWidth": "250px"},
                    children=[
                        html.Label("Distributor"),
                        dcc.Dropdown(
                            id="distributor-filter",
                            options=distributor_options,
                            value=[],
                            multi=True,
                            placeholder="Select distributor(s)",
                        ),
                        html.Br(),
                        html.Label("Release Year"),
                        dcc.RangeSlider(
                            id="year-filter",
                            min=int(df["Year"].min()),
                            max=int(df["Year"].max()),
                            step=1,
                            value=[int(df["Year"].min()), int(df["Year"].max())],
                            marks={int(y): str(y) for y in sorted(df["Year"].unique())},
                            allowCross=False,
                        ),
                    ],
                ),
                # KPI cards
                html.Div(
                    style={"flex": 1, "display": "grid", "gridTemplateColumns": "repeat(5, 1fr)", "gap": "10px"},
                    children=[
                        html.Div(id="kpi-worldwide", className="kpi-card"),
                        html.Div(id="kpi-budget", className="kpi-card"),
                        html.Div(id="kpi-roi", className="kpi-card"),
                        html.Div(id="kpi-opening", className="kpi-card"),
                        html.Div(id="kpi-count", className="kpi-card"),
                    ],
                ),
            ],
        ),

        # Charts
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1.2fr 1fr", "gap": "20px"},
            children=[
                dcc.Graph(id="scatter-budget-opening"),
                dcc.Graph(id="bar-worldwide-distributor"),
            ],
        ),
        html.Br(),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                dcc.Graph(id="bar-roi-movie"),
                dcc.Graph(id="line-worldwide-year"),
            ],
        ),
        html.Br(),
        dcc.Graph(id="bar-top10-worldwide"),
    ],
)

# --------------------
# Callbacks
# --------------------
def filter_data(distributors, year_range):
    dff = df.copy()
    if distributors:
        dff = dff[dff["Distributor"].isin(distributors)]
    if year_range and len(year_range) == 2:
        dff = dff[(dff["Year"] >= year_range[0]) & (dff["Year"] <= year_range[1])]
    return dff


@app.callback(
    [
        Output("kpi-worldwide", "children"),
        Output("kpi-budget", "children"),
        Output("kpi-roi", "children"),
        Output("kpi-opening", "children"),
        Output("kpi-count", "children"),
        Output("scatter-budget-opening", "figure"),
        Output("bar-worldwide-distributor", "figure"),
        Output("bar-roi-movie", "figure"),
        Output("line-worldwide-year", "figure"),
        Output("bar-top10-worldwide", "figure"),
    ],
    [
        Input("distributor-filter", "value"),
        Input("year-filter", "value"),
    ],
)
def update_dashboard(distributors, year_range):
    dff = filter_data(distributors, year_range)

    # KPIs
    total_worldwide = dff["Worldwide"].sum()
    total_budget = dff["Budget"].sum()
    avg_roi = dff["ROI"].mean()
    max_opening = dff["OpeningWeekendNorthAmerica"].max()
    movie_count = dff["Title"].nunique()

    kpi_style = {
        "border": "1px solid #ddd",
        "borderRadius": "6px",
        "padding": "10px",
        "backgroundColor": "#f9f9f9",
    }

    kpi_worldwide = html.Div(
        style=kpi_style,
        children=[
            html.Div("Total Worldwide Gross", style={"fontSize": "12px", "color": "#555"}),
            html.Div(f"${total_worldwide:,.0f}", style={"fontSize": "18px", "fontWeight": "bold"}),
        ],
    )
    kpi_budget = html.Div(
        style=kpi_style,
        children=[
            html.Div("Total Budget", style={"fontSize": "12px", "color": "#555"}),
            html.Div(f"${total_budget:,.0f}", style={"fontSize": "18px", "fontWeight": "bold"}),
        ],
    )
    kpi_roi = html.Div(
        style=kpi_style,
        children=[
            html.Div("Average ROI", style={"fontSize": "12px", "color": "#555"}),
            html.Div(f"{avg_roi:,.2f}x", style={"fontSize": "18px", "fontWeight": "bold"}),
        ],
    )
    kpi_opening = html.Div(
        style=kpi_style,
        children=[
            html.Div("Highest Opening Weekend (NA)", style={"fontSize": "12px", "color": "#555"}),
            html.Div(f"${max_opening:,.0f}", style={"fontSize": "18px", "fontWeight": "bold"}),
        ],
    )
    kpi_count = html.Div(
        style=kpi_style,
        children=[
            html.Div("# of Movies", style={"fontSize": "12px", "color": "#555"}),
            html.Div(f"{movie_count}", style={"fontSize": "18px", "fontWeight": "bold"}),
        ],
    )

    # Scatter: Budget vs Opening Weekend
    fig_scatter = px.scatter(
        dff,
        x="Budget",
        y="OpeningWeekendNorthAmerica",
        color="Distributor",
        hover_data=["Title", "Worldwide"],
        title="Budget vs Opening Weekend (North America)",
    )

    # Bar: Worldwide by Distributor
    dff_dist = dff.groupby("Distributor", as_index=False)["Worldwide"].sum()
    fig_bar_dist = px.bar(
        dff_dist.sort_values("Worldwide", ascending=False),
        x="Distributor",
        y="Worldwide",
        title="Worldwide Gross by Distributor",
    )

    # Bar: ROI by Movie
    dff_roi = dff.sort_values("ROI", ascending=False)
    fig_bar_roi = px.bar(
        dff_roi,
        x="ROI",
        y="Title",
        orientation="h",
        title="ROI by Movie",
    )

    # Line: Worldwide by Year
    dff_year = dff.groupby("Year", as_index=False)["Worldwide"].sum()
    fig_line_year = px.line(
        dff_year,
        x="Year",
        y="Worldwide",
        markers=True,
        title="Worldwide Gross Over Time",
    )

    # Top 10 Movies by Worldwide
    dff_top10 = dff.sort_values("Worldwide", ascending=False).head(10)
    fig_top10 = px.bar(
        dff_top10,
        x="Worldwide",
        y="Title",
        orientation="h",
        title="Top 10 Movies by Worldwide Gross",
    )

    fig_top10.update_yaxes(autorange="reversed")

    return (
        kpi_worldwide,
        kpi_budget,
        kpi_roi,
        kpi_opening,
        kpi_count,
        fig_scatter,
        fig_bar_dist,
        fig_bar_roi,
        fig_line_year,
        fig_top10,
    )


if __name__ == "__main__":
    # app.run_server(debug=True)
    app.run(debug=True)