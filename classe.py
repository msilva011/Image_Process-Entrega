import io
import os
from turtle import color
import PySimpleGUI as sg
from PIL import Image
import requests
from PIL import ImageFilter
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path
import webbrowser
from PIL import ImageEnhance
import shutil
import tempfile

def open_image(temp_file,event,window):
    if event == "Importar imagem":
        filename = sg.popup_get_file('Importar IMG')
        image = Image.open(filename)
    else:
        url = sg.popup_get_text("Importar Web")
        image = requests.get(url)
        image = Image.open(io.BytesIO(image.content))

    image_copy = image.copy()
    image.save(temp_file)
    
    mostrar_imagem(image_copy, window)
    window.Element("Sobre a imagem").Update(disabled=False)
    window.Element("Mostrar Localização").Update(disabled=False)
    

    return filename

def mostrar_imagem(imagem, window):
    bio = io.BytesIO()
    imagem.save(bio, "PNG")
    window["-IMAGE-"].erase()
    window["-IMAGE-"].draw_image(data=bio.getvalue(), location=(0,400))
    
flips = {
'FLIP_TOP_BOTTOM': Image.FLIP_TOP_BOTTOM,
'FLIP_LEFT_RIGHT': Image.FLIP_LEFT_RIGHT,
'TRANSPOSE': Image.TRANSPOSE
}

filtros = {
    'SBlur': ImageFilter.BLUR,
    'BoxBlur': ImageFilter.BoxBlur(radius=9),
    'GaussianBlur': ImageFilter.GaussianBlur,
    'Contour': ImageFilter.CONTOUR,
    'Edge Enhance': ImageFilter.EDGE_ENHANCE,
    'Emboss': ImageFilter.EMBOSS,
    'Find Edges': ImageFilter.FIND_EDGES,
}

fields = {
"File name" : "File name",
"File size" : "File size",
"Model" : "Camera Model",
"ExifImageWidth" : "Width",
"ExifImageHeight" : "Height",
"DateTime" : "Creating Date",
"static_line" : "*",
"MaxApertureValue" : "Aperture",
"ExposureTime" : "Exposure",
"FNumber" : "F-Stop",
"Flash" : "Flash",
"FocalLength" : "Focal Length",
"ISOSpeedRatings" : "ISO",
"ShutterSpeedValue" : "Shutter Speed",
}

def GPSLocation(filename):
    image_path = Path(filename)
    exif_data = get_exif_data(image_path.absolute())
    north = exif_data["GPSInfo"]["GPSLatitude"]
    east = exif_data["GPSInfo"]["GPSLongitude"]
    latitude = round(float(((north[0] * 60 + north[1]) * 60 + north[2]) / 3600),7)
    longitude = round(float(((east[0] * 60 + east[1]) * 60 + east[2]) / 3600),7)
    layout = []
    layout.append([sg.Text(latitude, size=(10,1)), 
      sg.Text(longitude, size=(10,1)),])
    window = sg.Window("GPS", layout, modal=True)
    while True:
        event,values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
    window.close()

def openInfoWindow(filename, window):
    layout = []
    image_path = Path(filename)
    exif_data = get_exif_data(image_path.absolute())
    for field in fields:
        if field == "File name":
            layout.append([sg.Text(fields[field], size=(10,1)),sg.Text(image_path.name,size = (25,1))]) 
        elif field == "File size":
            layout.append([sg.Text(fields[field], size=(10,1)),sg.Text(image_path.stat().st_size,size = (25,1))]) 
        else:
            layout.append([sg.Text(fields[field], size=(10,1)),sg.Text(exif_data.get(field, "No data"),size = (25,1))]) 

    window = sg.Window("Informações Foto", layout, modal=True)
    while True:
        event,values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
    window.close()


def get_exif_data(path):
    exif_data = {}
    try:
        image = Image.open(path)
        info = image._getexif()
    except OSError:
        info = {}

    if info is None:
        info = {}
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for gps_tag in value:
                sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                gps_data[sub_decoded] = value[gps_tag]
            exif_data[decoded] = gps_data
        else:
            exif_data[decoded] = value

    return exif_data



def save_thumbnail(input_file,output_file,format,qualit,width, height):
    imagem = Image.open(input_file)
    imagem.save(output_file, format=format, optmize = True, quality = qualit)
    imagem.thumbnail((width,height))
    imagem.save(output_file)

def save_redux(input_file,output_file):
    imagem = Image.open(input_file)
    imagem.save(output_file,format = "PNG",optmize = True,quality=15)


def image_converter(input_file,output_file,format):
    out = output_file +'.'+ format
    imagem = Image.open(input_file)
    if format == 'JPEG':
        imagem = imagem.convert('RGB')
    imagem.save(out, format = format,optmize =True)

def resize(input_image_path, output_image_path, size):
    image = Image.open(input_image_path)
    resized_image = image.resize(size)
    resized_image.save(output_image_path)


def applyEffect(originalfile,tmp_file,event,values,window):
    slider = values["-SLIDER-"]
    if event in ["P/B","QTD Cor","Sepia"]:
        Effects[event](tmp_file)
    elif event == "Normal":
        Effects[event](originalfile, tmp_file)
    else:
        Effects[event](originalfile, slider, tmp_file)
    imagem = Image.open(tmp_file)
    imagem.thumbnail((500,500))
    bio = io.BytesIO()
    imagem.save(bio, "png")
    window["-IMAGE-"].erase()
    window["-IMAGE-"].draw_image(data=bio.getvalue(), location=(0,400))



def filter(tmp_file,filter,window):
    image = Image.open(tmp_file)
    if filter in ["TRANSPOSE","FLIP_TOP_BOTTOM","FLIP_LEFT_RIGHT"]:
        image = image.transpose(flips[filter])
    else:
        image = image.filter(filtros[filter])
        
    image.save(tmp_file)
    image.thumbnail((500,500))
    bio = io.BytesIO()
    image.save(bio, "png")
    window["-IMAGE-"].erase()
    window["-IMAGE-"].draw_image(data=bio.getvalue(), location=(0,400))

def convertToPb(filename):
    image = Image.open(filename)
    image = image.convert("L")
    image.save(filename)

def convertToQtdColor(filename):
    if os.path.exists(filename):
        qtdCores = sg.popup_get_text("Digite a quantidade de cores")
        image = Image.open(filename)
        image = image.convert("P", palette=Image.Palette.ADAPTIVE,colors = int(qtdCores))
        image.save(filename)

def calcula_paleta(cor):
    paleta = []
    r,g,b = cor
    for i in range(255):
        new_red = r * i // 255
        new_green = g * i // 255
        new_blue = b * i // 255
        paleta.extend((new_red,new_green,new_blue))
    return paleta

def convertTosepia(filename):
    if os.path.exists(filename):
        branco = (255,240,192)
        paleta = calcula_paleta(branco)
        image = Image.open(filename)
        image = image.convert("L")
        image.putpalette(paleta)
        sepia = image.convert("RGB")
        image.save(filename)

def brightness(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Brightness(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def contrast(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Contrast(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def opacity(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Color(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def sharpness(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Sharpness(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)


Effects = {
"P/B" : convertToPb,
"QTD Cor" : convertToQtdColor,
"Sepia": convertTosepia,
"Normal": shutil.copy,
"Brilho": brightness,
"Cores": opacity,
"Contraste": contrast,
"Nitidez": sharpness
}