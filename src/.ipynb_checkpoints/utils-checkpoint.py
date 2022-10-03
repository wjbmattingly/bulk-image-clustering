import pandas as pd
import glob
from docarray import DocumentArray
from docarray import Document
import timm
from PIL import Image
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform
import umap
import numpy as np
import os
import hdbscan
import shutil


def preproc(d: Document):
    try:
        return (
            d.load_uri_to_image_tensor()  # load
            .set_image_tensor_shape(shape=(224, 224))
            .set_image_tensor_normalization()  # normalize color
            .set_image_tensor_channel_axis(-1, 0)
        )
    except:
        pass

def process_images(directory,
                   app_name,
                   new_directory,
                   model_name = 'mobilenetv3_large_100',
                   csv_filename="results.csv",
                   save_csv=False,
                   save_files=False,
                    save_docarray=False,
                    docarray_filename="docarray_sample"):
    print(f"Creating App Directory {app_name}")
    if os.path.exists(app_name):
        pass
    else:
        os.mkdir(app_name)
    shutil.copyfile("app_files/main.py", f"{app_name}/main.py")
    shutil.copyfile("app_files/utils.py", f"{app_name}/utils.py")
    print("Running Processing on Images")
    da = DocumentArray.from_files(directory)
    print(f"{len(da)} Images Gathered into DocumentArray.")
    model = timm.create_model(model_name, pretrained=True, num_classes=0)
    config = resolve_data_config({}, model=model)
    print("Model Created")
    da.apply(preproc)
    da.embed(model)
    print("Documents Embedded")
    print("Creating UMAP Projections...")
    umap_proj = umap.UMAP(n_neighbors=15,
                          min_dist=0.01,
                          metric='correlation').fit_transform(da.embeddings)
    print("Identifying Clusters with HDBScan")
    hdbscan_labels = hdbscan.HDBSCAN(min_samples=5, min_cluster_size=8).fit_predict(umap_proj)
    data = []
    if os.path.exists(new_directory):
        pass
    else:
        os.makedirs(new_directory)
    if save_files == True:
        print("Creating DataFrame and Saving Files")
    else:
        print("Creating DataFrame")
    for d, coord, label in zip(da, umap_proj, hdbscan_labels):
        
        filename = d.uri.replace("\\", "/").split("/")[-1]
        d.tags['umap_proj_x'] = coord[0]
        d.tags['umap_proj_y'] = coord[1]
        d.tags["name"] = filename
        static_save = f"{new_directory}/{filename}"
        d.tags["static_filename"] = static_save
        d.tags["label"] = label
        data.append({"text": d.tags["name"],
                     "x": d.tags['umap_proj_x'],
                     "y": d.tags['umap_proj_y'],
                     "filename": d.tags['static_filename'],
                    "color": label})
        if save_files == True:
            img = Image.open(d.uri)
            img.save(static_save)
    df = pd.DataFrame(data)
    if save_csv == True:
        df.to_csv(csv_filename, index=False)
    if save_docarray == True:
        da.save(docarray_filename, file_format="binary", encoding="utf-8")
    print("Finished")
    return da, df