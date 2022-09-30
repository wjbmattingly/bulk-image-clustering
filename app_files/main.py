import numpy as np
import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, TextInput, DataTable, TableColumn, ColorBar, HTMLTemplateFormatter, Spinner, RangeSlider, CustomJS, HoverTool, Div, Title, MultiChoice, CheckboxGroup
from bokeh.plotting import figure
from bokeh.palettes import Spectral6
from bokeh.io import curdoc
import os

from bokeh.palettes import Category10, Cividis256, Turbo256
from bokeh.transform import linear_cmap
from typing import Tuple, Optional

import bokeh.transform
import utils

from zipfile import ZipFile
from os.path import basename

import sys
print(sys.argv)
csv_filename = sys.argv[1]

def joint_update(attr, old, new):
    global highlighted_idx
    #Check to see if the change is coming from the scatter plot
    if attr == "indices":
        highlighted_idx = new
        #Set the Initial Subset basaed on selected index
        subset = df.iloc[highlighted_idx]

        #Grab the Labels in the Subset
        vals = list(set(subset.color.tolist()))
        vals.sort()
        vals_strs = [str(val) for val in vals]

        #Set the MultiChoice to the labels only found in subset
        multi_choice.value=vals_strs

        #Limit the Subset DataFrame to the rows that have labels in ValueList
        subset = subset.loc[subset.color.isin(vals)]
        highlighted_idx = subset.index.tolist()

        #Set the Scatter Plot
        scatter.data_source.selected.indices = highlighted_idx

        #Set the table
        source.data = subset

        print("Found Index Change")

    elif attr == "value":
        vals = [int(n) for n in new]

        if only_selected.active:
            subset = df.iloc[highlighted_idx]
        else:
            subset = [i for i in df.index.tolist() if df.iloc[i].color in vals]
            subset = df.iloc[subset]
        subset = subset.loc[subset.color.isin(vals)]
        highlighted_idx = subset.index.tolist()

        source.data = subset
        scatter.data_source.selected.indices = highlighted_idx

def save():
    """Callback used to save highlighted data points"""
    global highlighted_idx
    res = df.iloc[highlighted_idx]
    res[['text', 'filename', "color"]].to_csv(text_filename.value, index=False)
    print(save_images.active)
    if save_images.active:
        files = res.filename.tolist()
        with ZipFile(text_filename.value.replace(".csv", ".zip"), "w") as zipObj:
            for filename in files:
                zipObj.write(filename, basename(filename))

def clear_vals():
    """Clears the Values of the MultiSelect so that a user can select individual labels"""
    global highlighted_idx
    multi_choice.value = []
    highlighted_idx = df.index.tolist()

def reset_index():
    """Resets the Scatter Plot, DataTable, and Params"""
    global highlighted_idx
    highlighted_idx = [i for i in df.index]
    scatter.data_source.selected.indices = highlighted_idx

df = pd.read_csv(csv_filename)
highlighted_idx = df.index.tolist()
df['alpha'] = 0.5
columns = [
    TableColumn(field="text", title="filename"),
    TableColumn(field="color", title="label"),
    TableColumn(field="filename", title="image",
                formatter=HTMLTemplateFormatter(template='<img src="<%= filename %>" width=60>')),
    TableColumn(field="filename", title="download",
                formatter=HTMLTemplateFormatter(template=r'<a href="<%= filename %>", target="_blank">download</a>')),
        ]



# Establish Colors for Labels
mapper, df = utils.get_color_mapping(df)

#Create Data
source = ColumnDataSource(data=dict())
source_orig = ColumnDataSource(data=df)
source.data = df

#Link DataTable to Source Data
data_table = DataTable(source=source, columns=columns, row_height=100, height=500, width=500)

#Setup Params for Hover Image Display
image_urls = df.filename.tolist()
image_height = 250
image_tooltip = f'''
<div>
  <div>
    <img
      src="@filename" height="{str(image_height)}"
      style="float: left; margin: 0px 15px 15px 0px; image-rendering: pixelated;"
      border="2"
      ></img>
  </div>
  <div>
    <span style="font-size: 17px;">Label: @color</span>
    <span style="font-size: 17px;">@text</span>
  </div>
</div>
'''


#Create Figure
p = figure(sizing_mode="scale_both",
                tools=["lasso_select", "box_select", "pan", "box_zoom", "wheel_zoom", "save", "hover", "reset"],
                tooltips=image_tooltip)
p.toolbar.active_drag = None
p.toolbar.active_inspect = None
p.title.text = "Image Visualization"
p.title.align = "center"
p.title.text_font_size = "25px"
p.plot_width = 500
p.plot_height = 500


circle_kwargs = {"x": "x", "y": "y",
                    "size": 3,
                    "source": source_orig,
                    "alpha": "alpha"
                    }

#Updates the Colors with the Color Mapper
if "color" in df.columns:
    circle_kwargs.update({"color": mapper})
    color_bar = ColorBar(color_mapper=mapper['transform'], width=8)
    p.add_layout(color_bar, 'right')

#Create Scatter Plot
scatter = p.circle(**circle_kwargs)

#Layout and Title
t = Title()
t.text="Image Clustering Server"

## Spinner for Node Size
spinner = Spinner(title="Circle Size", low = 1, high=60, step=1, value=scatter.glyph.size, width=200)
spinner.js_link("value", scatter.glyph, "size")

## Adjust Row Height
row_spinner = Spinner(title="Row Height", low = 100, high=1000, step=10, value=data_table.row_height, width=200)
row_spinner.js_link("value", data_table, "row_height")






#Select Labels
labels = list(set(df.color.tolist()))
labels = [str(label) for label in labels]
labels.sort()

#Create MultiSelect
multi_choice = MultiChoice(value=labels, options=labels)
multi_choice.on_change("value", joint_update)


reset_button = Button(label="Reset Data")
reset_button.on_click(reset_index)

only_selected = CheckboxGroup(labels=["Only Change Selected"], active=[])
clear_vals_button = Button(label="Clear Label MultiSelect")
clear_vals_button.on_click(clear_vals)

scatter.data_source.selected.on_change('indices', joint_update)


text_filename = TextInput(value="out.csv", title="Filename:")
save_btn = Button(label="SAVE")
save_btn.on_click(save)
save_images = CheckboxGroup(labels=["Save Images"], active=[])

select_row = row(spinner, text_filename)
controls_main = column(p, select_row, save_images, save_btn)

controls = column(data_table,
                    reset_button,
                    only_selected,
                    clear_vals_button,
                    multi_choice)
curdoc().title = "USHMM Image Clustering Server"
curdoc().add_root(row(controls_main, controls))
