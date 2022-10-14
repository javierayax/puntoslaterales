# Name:        Generate offset points
# Purpose:     Genera puntos a ambos costados de un segmento vial
#
# Author:      Javier 'Shielder' Escudero, Jhonatan 'Potan' Castillo, Jennyfer Sarmiento
# Modified by: Javier 'Shielder' Escudero
#
# Created:     2022
# Modified:    14/10/2022

# Copyright:   (c) Esri Co

# imports
import datetime
import arcpy
import os
import sys
from arcpy.management import AddField, CreateFeatureclass, GetCount, FeatureToPoint, SelectLayerByLocation, \
    SelectLayerByAttribute
from arcpy.analysis import Buffer
from arcpy.da import InsertCursor, SearchCursor
from arcpy import Project_management as Project

# environments
arcpy.env.overwriteOutput = 1
WKID = 103599
name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Parameters
input_line = arcpy.GetParameter(0)
area_of_interest = arcpy.GetParameter(1)
meters = arcpy.GetParameter(2)
ws = arcpy.env.scratchGDB

# Validations
count = int(GetCount(area_of_interest).getOutput(0))
if count != 1:
    arcpy.AddWarning(f"Debe seleccionar solo un poligono para ejecutar el analisis. Hay {count} seleccionados")
    sys.exit(1)


def calculate_points(_cutter, _value):
    if _value > _cutter.length:
        _value = _cutter.length*0.5  # La mitad de la longitud de la linea
    _buffer = arcpy.PointGeometry(_cutter.centroid).buffer(_value)
    _polys = _buffer.cut(_cutter)
    _points = []
    for _poly in _polys:
        _points.append(_poly.centroid)
    # arcpy.AddMessage(_points)
    return _points


def main(_input_line):
    try:
        try:
            SelectLayerByLocation(input_line, "INTERSECT", area_of_interest, None, "NEW_SELECTION", "NOT_INVERT")
            prj_line = Project(_input_line, os.path.join(ws, f"prj_input_{name}"), WKID)  # Mejor en metros
            SelectLayerByAttribute(input_line, "CLEAR_SELECTION", '', None)
            out_point = CreateFeatureclass(ws, f"output_point{name}", "POINT", None, "DISABLED", "DISABLED", WKID)
            AddField(out_point, "side", "TEXT", None,  field_length=10)
        except Exception as _error:
            arcpy.AddError(_error)
            arcpy.AddError("Hubo un error grave al preprocesar los datos")
            sys.exit(1)

        # Solo se ejecuta para el primer registro
        insertor = InsertCursor(out_point, ["shape@", "side"])
        with SearchCursor(prj_line, "shape@") as cursor:
            for row in cursor:
                try:
                    _ini_line = row[0]
                    _points = calculate_points(_ini_line, meters)
                    s = "Izquierda"
                    for _point in _points:
                        insertor.insertRow((_point, s,))
                        s = "Derecha"
                except Exception as _error:
                    arcpy.AddWarning(_error)

        del insertor
        # Result
        arcpy.SetParameter(3, out_point)

    except Exception as _error:
        arcpy.AddError(_error)


if __name__ == "__main__":
    main(input_line)

# End
