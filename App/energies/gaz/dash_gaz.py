import pandas as pd
from dash import Dash, dcc, html, Input, Output,dash_table
import plotly.express as px
from App.energies.gaz.ProcessSQLGaz import ProcessSQLGaz

# Define a list of French month names
months_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
# Define a list of French quarter names
quarters_fr = ["1er trimestre", "2ème trimestre", "3ème trimestre", "4ème trimestre"]

def g(i):
    if -1<i and i<10:
        return "0"+str(i)
    return str(i)

df=ProcessSQLGaz().get_sqlserver() #get SQL data from SQL Server

#DataViz
# Initialize the Dash app
app = Dash(__name__)
# Define the layout of the app
app.layout = html.Div([
    html.H1("Consommation de Gaz des ménages en France",style={"color":"#DC143C"}),
    html.Div(
        dash_table.DataTable(id="table",data=df.to_dict('records'),columns=[{"name": i, "id": i} for i in df.columns]),
        style={"display":"none"},
    ),
    dcc.Interval(
        id='interval-component',
        interval=60*1000, # in milliseconds
        n_intervals=0,
    ),
    html.Div(children=[
    html.P("Selectionnez l'horaire de consommation:"),
    dcc.Dropdown(
        id='hours-axis_line',
        options=["Toutes horaires"]+[g(i)+"h00" for i in range(24)],
        value="Toutes horaires",
        clearable=False,
        style={"width":"50%"},
    ),
    dcc.Graph(id="graph_line"),
    ],style={"display":"block"},
    ),
    html.Div(children=[
        dcc.Dropdown(
            id='hours-axis_chart',
            options=["Toutes horaires"]+[g(i)+"h00" for i in range(24)],
            value="Toutes horaires",
            clearable=False,
            style={"width":"50%"},
        ),
        dcc.Dropdown(
            id='period-axis_chart',
            options=["Année","Trimestre","Mois"],
            value="Mois",
            clearable=False,
            style={"width":"50%"},
        ),
        dcc.Graph(id="graph_chart"),
    ],style={"display":"block"}
    ),
    html.Div(children=[
        dcc.Dropdown(
            id='hours-axis_hist',
            options=["Toutes horaires"]+[g(i)+"h00" for i in range(24)],
            value="Toutes horaires",
            clearable=False,
            style={"width":"50%"},
        ),
        dcc.Graph(id="graph_hist"),
    ],style={"display":"block"},
    ),
],
)

@app.callback(
    Output("table","data"),
    Input("interval-component","n_intervals")
)
def update_table(n):
    return ProcessSQLGaz().get_sqlserver().to_dict(orient='records')#get SQL data from SQL Server
# Define the callback function for the area plot
@app.callback(
    Output("graph_line", "figure"),
    Input("hours-axis_line", "value"),
    Input("table","data"),
)
def display_graph_line(hour,df_json):
    df=pd.DataFrame.from_dict(df_json)
    # If the "Toutes horaires" option was selected, set the feature to "conso"
    if hour=="Toutes horaires":
        feature="conso"
    else:
        # Otherwise, set the feature to the selected hour
        feature=hour[:2]+"_00"
    # Aggregate the data by date and regions group
    df_agg = df.groupby(['date', 'region_groups'])[['conso']+[f"{g(i)}_00" for i in range(24)]].mean().reset_index()
    # Create the area plot
    fig = px.scatter(df_agg, x="date", y=feature, color="region_groups",\
        color_discrete_map={0:"#9400D3",1:"#1E90FF",2:"#FFFFF0",3:"#FF4500"},\
        labels={feature:"Consommation à "+hour,"region_groups":"Groupe de régions"})\
    .update_layout(
        title="Graphique représentant la consommation de Gaz (MWh) moyenne par groupe de régions et par date", \
        xaxis_title="Date",yaxis_title="Consommation de Gaz (MWh) moyenne")
    return fig

# Define the callback function for the bar chart
@app.callback(
    Output("graph_chart", "figure"),
    Input("hours-axis_chart", "value"),
    Input("period-axis_chart", "value"),
    Input("table","data"),
)
def display_graph_chart(hour,period,df_json):
    df=pd.DataFrame.from_dict(df_json)
    # Convert the period to the corresponding column and labels in French
    conv_fr={"Trimestre":(list(range(1,5)),quarters_fr),"Mois":(list(range(1,13)),months_fr)}
    period_conv={"Année":"year","Trimestre":"quarter","Mois":"month"}[period]
    conv_period_dict={value:key for key,value in {"Année":"year","Trimestre":"quarter","Mois":"month"}.items()}
    # If the "Toutes horaires" option was selected, set the feature to "conso"
    if hour=="Toutes horaires":
        feature="conso"
    else:
        # Otherwise, set the feature to the selected hour
        feature=hour[:2]+"_00"
    # Aggregate the data by the selected period and region group
    df_agg = df.groupby([period_conv, 'region_groups'])[['conso']+[f"{g(i)}_00" for i in range(24)]].mean().reset_index()
    # Create the bar chart
    fig = px.bar(df_agg, x=period_conv, y=feature, color="region_groups",barmode="group",
    labels={
        "region_groups":"Groupe de régions",
    })\
    .update_layout(
    title="Diagramme à barres de la consommation de Gaz (MWh) moyenne par groupe de régions/par horaire/par fréquence temporelle",\
        xaxis_title=conv_period_dict[period_conv],yaxis_title="Consommation de Gaz (MWh) moyenne")
    if period != "Année":
        fig.update_xaxes(tickvals=conv_fr[period][0], ticktext=conv_fr[period][1])

    return fig

# Define the callback function for the histogram
@app.callback(
    Output("graph_hist", "figure"),
    Input("hours-axis_hist", "value"),
    Input("table","data"),
)
def display_graph_hist(hour,df_json):
    df=pd.DataFrame.from_dict(df_json)
    # If the "Toutes horaires" option was selected, set the feature to "conso"
    if hour=="Toutes horaires":
        feature="conso"
    else:
        # Otherwise, set the feature to the selected hour
        feature=hour[:2]+"_00"

    # Create the histogram
    try:
        fig = px.histogram(df,x=feature).update_layout(
        title="Histogramme de la consommation de Gaz (MWh) par horaire", xaxis_title="Consommation de Gaz (en MWh)",yaxis_title="Effectifs")
    except ValueError:
        fig = px.histogram(df,x=feature).update_layout(
            title="Histogramme de la consommation de Gaz (MWh) par horaire", xaxis_title="Consommation de Gaz (en MWh)",yaxis_title="Effectifs")
    return fig

# Run the app
app.run_server(debug=True,port=8053)