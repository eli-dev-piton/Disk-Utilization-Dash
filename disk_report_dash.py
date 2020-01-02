import base64
import os
from urllib.parse import quote as urlquote
from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import pandas as pd
import getpass

############################ Model #########################################
UPLOAD_DIRECTORY = "/Documents"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

name = "data-vinfolio.csv"
user = getpass.getuser()
path = str("C:\\Users\\"+user+"\\Documents\\Dev\\python\\disk_utilization_report\\data\\"+name)
df = pd.read_csv(path)
############################################################################

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server)


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)

################### VIEW #################################################
app.layout = html.Div([
        html.H1("Xtivia Report Dash", style={'textAlign': 'center', 'color':'white','background-color':'green'}),
        html.H2("Upload a CSV so that a chart can be made"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Drag and drop or click to select a file to upload."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
                "color":"green",
                "max-width": "500px",
            },
            multiple=True,
        ),
        html.H2("Data file list"),
        html.Ul(id="file-list"),
        html.Div([
        html.H1('Disk Utilization Report', style={'textAlign': 'center'}),
        html.Br(),
        html.H3(children='Select a Drive from the dropdown'),
        

    #dropdown component
    dcc.Dropdown(
        id='yaxis',
        options=[{'label': i, 'value': i} for i in df['FILESYSTEM'].unique()],
        style={'width': '25%', 'display': 'inline-block'}),
    html.H3(children='Instance: '+ df['MAIL_ID'].iloc[0], style={'color':'rgb(255,102,102)'}),
    html.H6(children='*** Dates are in yyyy-mm-dd format'),
    html.H3(children='From: '+df['TIMESTAMP'].min()),
    html.H3(children='To: '+df['TIMESTAMP'].max()),
    #graph component
    dcc.Graph(
        id='scatter',
        figure={'data': [go.Scatter()],
        'layout':go.Layout(
            title = 'Please Pick a Disk from the dropdown',
            xaxis = {'title':'TIMESTAMP'},
            yaxis = {'title': 'USED GB'} 
            ) 
        } 
        )


    ])
        ],
        )
########################## Controller ###########################################
def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)


@app.callback(
    Output("file-list", "children"),
    [Input("upload-data", "filename"), Input("upload-data", "contents")],
)
def update_output(uploaded_filenames, uploaded_file_contents):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        return [html.Li(file_download_link(filename)) for filename in files]



@app.callback(
    Output('scatter', 'figure'),
    [Input('yaxis', 'value')])
    # dash.dependencies.Output('scatter', 'figure'),
    # [dash.dependencies.Input('yaxis', 'value')])
def update_graphics(value):
    filtered_df = df[df['FILESYSTEM'] == value]
    report_title=str(value) + ' Disk utilization report'
    return{
    'data': [go.Scatter(
        x=filtered_df.TIMESTAMP,
        y=filtered_df.USED/1048576, #to convert into GB
        mode='markers',
        )],
            'layout': go.Layout(
                title=report_title,
                xaxis={'title':'TIMESTAMP'},
                yaxis={'title':'USED GB'},

                ),

    }



if __name__ == "__main__":
    app.run_server(debug=False, port=8888)
