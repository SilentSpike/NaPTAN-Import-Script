import csv
import xml.etree.ElementTree as ET

# Codes can be found at: https://wiki.openstreetmap.org/wiki/NaPTAN/Request_for_Import
area_code = "639"
stops_out = {}
alt_names = {}

def validBusStop(data):
    # "BCT" means bus/coach/trolley stop
    # "MKD" means there's a pole or shelter
    # "del" status should be stops that no longer exists
    return (data["ATCOCode"].startswith(area_code)
        and data["StopType"] == "BCT"
        and data["BusStopType"] == "MKD"
        and data["Status"] == "act")

def addToOutput(data):
    atco = data["ATCOCode"]
    local = data["LocalityName"]

    # Use "LocalityName" to split up import
    if local not in stops_out:
        stops_out[local] = []

    # Inject any alternate language names
    if atco in alt_names:
        for alt in alt_names[atco]:
            if alt[1] == "gd":
                data["GaelicName"] = alt[0]
            if alt[1] == "cy":
                data["WelshName"] = alt[0]

    stops_out[local].append(data)

def writeOutput(path, data):
    osm = ET.Element("osm", version="0.6",
        generator="NaPTAN Import Script")

    for i, stop in enumerate(data, 1):
        node = ET.SubElement(osm, "node", id=str(-i),
            lat=stop["Latitude"], lon=stop["Longitude"])
        # Tags required for bus stop
        ET.SubElement(node, "tag", k="highway", v="bus_stop")
        ET.SubElement(node, "tag", k="public_transport", v="platform")
        ET.SubElement(node, "tag", k="bus", v="yes")
        # Naptan tags
        ET.SubElement(node, "tag", k="source", v="naptan")
        ET.SubElement(node, "tag", k="naptan:verified", v="no")
        ET.SubElement(node, "tag", k="naptan:AtcoCode", v=stop["ATCOCode"])
        ET.SubElement(node, "tag", k="naptan:NaptanCode", v=stop["NaptanCode"])
        # Name tags
        ET.SubElement(node, "tag", k="name", v=stop["CommonName"])
        if "GaelicName" in stop:
            ET.SubElement(node, "tag", k="name:gd", v=stop["GaelicName"])
        if "WelshName" in stop:
            ET.SubElement(node, "tag", k="name:cy", v=stop["WelshName"])

    tree = ET.ElementTree(osm)
    tree.write(path, encoding='utf-8',
        xml_declaration=True, method='xml')

# Alternate names stored in another file
# gd - Scottish gaelic
# cy - Welsh
with open("NaPTANcsv/AlternativeDescriptors.csv") as csvfile:
    reader = csv.DictReader(csvfile)

    # Build dictionary
    for row in reader:
        atco = row["AtcoCode"]
        if atco not in alt_names:
            alt_names[atco] = []

        # Stops can have multiple alternate names
        alt_names[atco].append((row["CommonName"], row["CommonNameLang"]))

with open("NaPTANcsv/Stops.csv") as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        if validBusStop(row):
            addToOutput(row)

# Write OSM XML output
for local in stops_out:
    writeOutput(f"Output/{local}.osm", stops_out[local])
