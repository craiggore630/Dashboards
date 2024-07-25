from dash import Dash, dcc, html, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
import country_converter as coco
import State_to_Abbrev as states
from datetime import timedelta

def load_data(view, selected_data, start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    data = pd.read_csv('rental_payment_data', index_col=0, parse_dates=['rental_date', 'payment_date'])
    data['rental_date'] = [date.date() for date in data['rental_date']]
    data['payment_date'] = [date.date() for date in data['payment_date']]
    data = data[(data['rental_date']>=start_date) & (data['rental_date']<=end_date)]
    if view == "World":
        data = data[data['country']!='Yugoslavia'].reset_index(drop=True)
        cc = coco.CountryConverter()
        new_country = cc.pandas_convert(data['country'], to='ISO3')
        data['country'] = new_country
        grouped_data = data.groupby('country')
        
    if view == "USA":
        data = data[data['country']=='United States']
        data = data.rename(columns={'district': 'state'})
        data = data.replace({'state': states.us_state_to_abbrev})
        grouped_data = data.groupby('state')

    data = pd.DataFrame({'customers': grouped_data['customer_id'].nunique(), 'payments': grouped_data['amount'].sum(),
                    'rentals': grouped_data['rental_id'].count()})
    data['rentals per customer'] = data['rentals'] / data['customers']
    data['payments per customer'] = data['payments'] / data['customers']
    data['payment per rental'] = data['payments'] / data['rentals']
    data = data.reset_index()
    return data


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.SPACELAB, dbc.icons.FONT_AWESOME],
)

"""
*************************************
     Make Tabs  
*************************************
"""

view_card = dbc.Card(
    [
        html.H4(
            "Select View:",
            className="card-title",
        ),
        dcc.Dropdown(
            id="select_view",
            options=['World', 'USA'],
            value='World',
        ),
    ],
    body=True,
    className="mt-4",
)

data_card = dbc.Card(
    [
        html.H4(
            "Select Data to View:",
            className="card-title",
        ),
        dcc.RadioItems(
            id="select_data",
            options=[
                {'label':'Number of customers', 'value':'customers'},
                {'label':'Number of rentals', 'value':'rentals'},
                {'label':'Total payments', 'value':'payments'},
                {'label':'Rentals per customer', 'value':'rentals per customer'},
                {'label':'Payments per customer', 'value':'payments per customer'},
                {'label':'Payment per rental', 'value':'payment per rental'},
            ],
            inputClassName="me-2",
            value='payments',
        ),
    ],
    body=True,
    className="mt-4",
)

time_frame_card = dbc.Card(
    [
        html.H4(
            "Select time frame:",
            className='card-title',
        ),
        dcc.DatePickerRange(
            id = "date_picker",
            min_date_allowed = '2005-05-24',
            max_date_allowed = '2006-02-14',
            start_date = '2005-05-24',
            end_date = '2006-02-14',
            className = "me-2",
        ),
        dbc.Button(
            "Submit",
            id = "date_submit",
            className = "me-2",
            n_clicks = 0,
        ),
    ],
    body=True,
    className="mt-4",
)

about_text = dcc.Markdown(
    """
    The Sakila database is a sample database that models a DVD rental store.

    This dashborad investigates the total numbers of rentals, payments and customers per country or US state.
    """
)

about_card = dbc.Card(
    [
        dbc.CardHeader("An Introduction"),
        dbc.CardBody(about_text),
    ],
    className="mt-4",
)

# Build tabs

tabs = dbc.Tabs(
    [
        dbc.Tab(about_card, tab_id="tab-1", label="About"),
        dbc.Tab(
            [view_card, data_card, time_frame_card],
            tab_id="tab-2",
            label="Data Selection",
            className="pb-4",
        ),
    ],
    id="tabs",
    active_tab="tab-2",
    className="mt-2",
)

"""
*************************************
     Make Figures
*************************************
"""

def make_map(view, selected_data, data, start_date):
    if selected_data == 'customers':
        label_txt = 'Customers'
    elif selected_data == 'rentals':
        label_txt = 'Total rentals'
    elif selected_data == 'payments':
        label_txt = 'Total payments'
    elif selected_data == 'rentals per customer':
        label_txt = 'Rentals per customer'
    elif selected_data == 'payments per customer':
        label_txt = 'Payments per customer'
    elif selected_data == 'payment per rental':
        label_txt = 'Payment per rental'
        
    if view == "World":
        fig = px.choropleth(
            data_frame = data,
            locations = "country",
            color = selected_data,
            scope = "world",
        )
        fig.update_layout(
            title_text = f"{label_txt} by country",
            geo={"projection": {"type": "natural earth"}},
            margin = dict(l=50, r=50, t=50, b=50),
        )
    else:
        fig = px.choropleth(
            data_frame = data,
            locations = "state",
            locationmode="USA-states",
            color = selected_data,
            scope = "usa",
        )
        fig.update_layout(
            title_text = f"{label_txt} by state",
        )
        
    fig.update_layout(
        title_x = 0.5,
        title_font_size = 20,
        title_font_weight = 'bold',
    )
    return fig

def make_bar(view, selected_data, data):
    data = data.sort_values(by=selected_data, ascending = False)[0:10]
    if view == "World":
        labels = 'country'
    else:
        labels = 'state'
    fig = px.bar(data, x = labels, y = selected_data)
    return fig

"""
*************************************
     Main Layout 
*************************************
"""

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H2(
                    "Sakila Payments and Rentals",
                    className="text-center bg-primary text-white p-2",
                ),
            )
        ),
        dbc.Row(
            [
                dbc.Col(tabs, width=12, lg=5, className="mt-4 border"),
                dbc.Col(
                    [
                        dcc.Graph(id="map"),
                        dcc.Graph(id="bar_chart"),
                    ],
                    width=12,
                    lg=7,
                    className="pt-4",
                ),
            ],
            className="ms-1",
        ),
    ],
    fluid=True,
)


"""
*************************************
     App Callbacks
*************************************
"""

@app.callback(
    Output("map", "figure"),
    Output("bar_chart", "figure"),
    Input("select_view", "value"),
    Input("select_data", "value"),
    Input("date_submit", "n_clicks"),
    State("date_picker", "start_date"),
    State("date_picker", "end_date"),
)
def update_figures(select_view, select_data, n_clicks, start_date, end_date):
    data = load_data(select_view, select_data, start_date, end_date)
    figure1 = make_map(select_view, select_data, data, start_date)
    figure2 = make_bar(select_view, select_data, data)
    return figure1, figure2
    

if __name__ == "__main__":
    app.run_server(debug=True)