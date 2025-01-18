import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import Input, Output, State
import plotly.express as px
import pandas as pd

# Crear la app Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Cargar datos y filtrar columnas necesarias
df = pd.read_csv('ce2019_mich.csv', index_col=False)
df2 = df[['MUNICIPIO', 'CODIGO', 'A111A', 'ID_ESTRATO']]  # Seleccionar columnas relevantes

print("Asi empieza")
print(df2)

# Combinar df2 con la categorización
categorization_df = pd.read_csv('tc_codigo_actividad.csv', index_col=False)  # Cargar archivo de categorización
categorization_df = categorization_df[['CODIGO', 'DESC_CODIGO']]  # Seleccionar columnas relevantes

print("categorias")
print(categorization_df)

df2 = pd.merge(df2, categorization_df, on='CODIGO', how='left')  # Agregar la descripción
df2 = df2.rename(columns={'A111A': 'PIB', 'CODIGO': 'Numero del Sector', 'DESC_CODIGO': 'Sector'})


print("merge")
print(df2)

# Función para filtrar datos
def get_filtered_df(level, parent_code=""):

    if level == 2:  # Nivel inicial (sectores, 2 dígitos)
        filtered_df = df2[
            (df2.ID_ESTRATO.isnull()) &
            (df2['MUNICIPIO'] == 53) &
            (
                (df2['Numero del Sector'].str.len() == 2) |
                (df2['Numero del Sector'].isin(['31-33', '48-49']))  # Excepciones para sectores con 5 dígitos
            )
        ]
    else:  # Niveles subsecuentes
        if parent_code == '31-33':
            filtered_df = df2[
                (df2.ID_ESTRATO.isnull()) &
                (df2['MUNICIPIO'] == 53) &
                (df2['Numero del Sector'].str.len() == 3) &  # Filtrar para códigos de 3 dígitos
                (
                    df2['Numero del Sector'].str.startswith('31') |
                    df2['Numero del Sector'].str.startswith('32') |
                    df2['Numero del Sector'].str.startswith('33')
                )
            ]
        elif parent_code == '48-49':
            filtered_df = df2[
                (df2.ID_ESTRATO.isnull()) &
                (df2['MUNICIPIO'] == 53) &
                (df2['Numero del Sector'].str.len() == 3) &  # Filtrar para códigos de 3 dígitos
                (
                    df2['Numero del Sector'].str.startswith('48') |
                    df2['Numero del Sector'].str.startswith('49')
                )
            ]
        else:
            filtered_df = df2[
                (df2.ID_ESTRATO.isnull()) &
                (df2['MUNICIPIO'] == 53) &
                (df2['Numero del Sector'].str.startswith(parent_code)) &
                (df2['Numero del Sector'].str.len() == level)
            ]

    print("Filtrado final:")
    print(filtered_df)  # Verificar si hay datos después del filtro
    return filtered_df

# Crear la gráfica inicial
def create_figure(dataframe, title):
    """Crear gráfica de barras con título."""
    return px.bar(
        dataframe,
        x='PIB',
        y='Numero del Sector',
        hover_data={'Numero del Sector': False, 'Sector': True},  # Mostrar descripción al pasar el puntero
        height=800,
        title=title
    )

# Layout de la aplicación
app.layout = dbc.Container([
    dbc.Card([
        dbc.Button(
            '🡠 Regresar',
            id='back-button',
            outline=True,
            size="sm",
            className='mt-2 ml-2',
            style={'display': 'none'}  # Oculto inicialmente
        ),
        dcc.Store(id='current-level', data=2),  # Nivel actual (2 dígitos al inicio)
        dcc.Store(id='parent-code', data=""),  # Código padre actual
        dbc.Row(
            dcc.Graph(id='graph', figure=create_figure(get_filtered_df(2), "Sectores en Morelia")),
            justify='center'
        )
    ], className='mt-3')
])

# Callback para manejar interacciones en la gráfica y el botón
@app.callback(
    [Output('graph', 'figure'),
     Output('back-button', 'style'),
     Output('current-level', 'data'),
     Output('parent-code', 'data')],
    [Input('graph', 'clickData'),
     Input('back-button', 'n_clicks')],
    [State('current-level', 'data'),
     State('parent-code', 'data')]
)
def drilldown(clickData, n_clicks, current_level, parent_code):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Si el usuario hace clic en una barra
    if trigger_id == 'graph' and clickData:
        selected_code = clickData['points'][0]['y']
        next_level = len(selected_code) + 1  # El próximo nivel se basa en la longitud del código seleccionado

        # Construir el próximo código padre correctamente
        next_parent_code = selected_code
        next_df = get_filtered_df(next_level, next_parent_code)  # Filtrar datos

        # Si hay datos en el siguiente nivel
        if not next_df.empty:
            fig = create_figure(next_df, f"Detalle del código {next_parent_code}")
            return fig, {'display': 'block'}, next_level, next_parent_code

    # Si el usuario hace clic en "Regresar"
    elif trigger_id == 'back-button' and n_clicks:
        previous_level = current_level - 1  # Disminuir nivel
        if previous_level < 2:  # Regresar al nivel inicial
            previous_level = 2
            previous_parent_code = ""
        else:
            previous_parent_code = parent_code[:-1]  # Eliminar el último dígito del código padre

        prev_df = get_filtered_df(previous_level, previous_parent_code)
        title = f"Detalle del código {previous_parent_code}" if previous_parent_code else "Sectores en Morelia"
        return create_figure(prev_df, title), {'display': 'block' if previous_level > 2 else 'none'}, previous_level, previous_parent_code

    # Estado inicial
    return create_figure(get_filtered_df(2), "Sectores en Morelia"), {'display': 'none'}, 2, ""

# Ejecutar la app
if __name__ == '__main__':
    app.run_server(debug=True)
