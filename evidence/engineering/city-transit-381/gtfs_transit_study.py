"""Bounded GTFS archive integrity readback and data-derived SVG study.

The canonical MobilityData CLI is the GTFS specification validator. This
independent standard-library program checks specific identity/geometry joins
against its original report and draws only supplied geographic coordinates.
It does not certify service, accessibility, routing, distances or ridership.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import csv
import io
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


SOURCE = "https://www.manteca.gov/DocumentCenter/View/2279"
TERMS = "https://www.manteca.gov/384/GTFS-Data"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
FEED_SHA = "31bf6a9d37f9d8606c47d03be14022255b458308abd0f893c9a53ba2cc91e329"
JAR_SHA = "19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2"
REPORT_SHA = "83f0aa6c60edb3a90d927b609ed4d5edb870bec1b0154ecd435971be8d225a9b"
SYSTEM_SHA = "823b06dada6cf539dde01b9451b5d2b6817ee7930f1ebeba4dc79d7688e79287"
REQUIRED = {"agency.txt", "routes.txt", "trips.txt", "stops.txt", "stop_times.txt", "calendar.txt", "calendar_dates.txt", "shapes.txt", "feed_info.txt"}
MAX_ZIP = 10_000_000
MAX_UNPACKED = 30_000_000
MAX_REPORT = 2_000_000
MAX_SYSTEM = 100_000
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def bounded_bytes(path, ceiling):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= ceiling:
        raise ValueError("Not a bounded regular file")
    with path.open("rb") as stream:
        raw = stream.read(ceiling + 1)
    if not 0 < len(raw) <= ceiling:
        raise ValueError("File exceeds bounded size")
    return raw


def digest(path, ceiling=MAX_ZIP):
    return sha256(bounded_bytes(path, ceiling)).hexdigest()


def load_tables(path):
    if not 0 < path.stat().st_size <= MAX_ZIP:
        raise ValueError("Feed exceeds bounded size")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [e.filename for e in entries]
        if (len(names) > 50 or len(set(names)) != len(names)
                or not REQUIRED <= set(names)
                or any(not re.fullmatch(r"[a-z_]+\.txt", name) for name in names)
                or sum(e.file_size for e in entries) > MAX_UNPACKED):
            raise ValueError("Unexpected ZIP member names or size")
        tables = {}
        for name in names:
            with archive.open(name) as stream:
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
                fields = reader.fieldnames or []
                if not fields or len(fields) != len(set(fields)):
                    raise ValueError(f"Malformed CSV header: {name}")
                rows = list(reader)
            if len(rows) > 200_000 or any(None in row or None in row.values() for row in rows):
                raise ValueError(f"Unbounded or ragged CSV: {name}")
            tables[name] = rows
    return tables


def keyed(rows, key):
    result = {row[key]: row for row in rows}
    if "" in result or len(result) != len(rows):
        raise ValueError(f"Absent/duplicate ID: {key}")
    return result


def coordinate(row, lat, lon):
    y, x = float(row[lat]), float(row[lon])
    if not (math.isfinite(x) and math.isfinite(y) and -90 <= y <= 90 and -180 <= x <= 180):
        raise ValueError("Invalid geographic coordinate")
    return x, y


def sequence(value):
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError("Invalid nonnegative sequence")
    return int(value)


def analyze(tables):
    agency = keyed(tables["agency.txt"], "agency_id")
    routes = keyed(tables["routes.txt"], "route_id")
    trips = keyed(tables["trips.txt"], "trip_id")
    stops = keyed(tables["stops.txt"], "stop_id")
    services = set(keyed(tables["calendar.txt"], "service_id"))
    service_exceptions = set()
    for row in tables["calendar_dates.txt"]:
        datetime.strptime(row["date"], "%Y%m%d")
        key = row["service_id"], row["date"]
        if key in service_exceptions or not key[0] or row["exception_type"] not in {"1", "2"}:
            raise ValueError("Invalid calendar exception")
        service_exceptions.add(key)
        services.add(key[0])
    stop_coords = {key: coordinate(row, "stop_lat", "stop_lon") for key, row in stops.items()}
    shapes = defaultdict(dict)
    for row in tables["shapes.txt"]:
        key, seq = row["shape_id"], sequence(row["shape_pt_sequence"])
        if not key or seq in shapes[key]:
            raise ValueError("Missing/duplicate shape coordinate sequence")
        shapes[key][seq] = coordinate(row, "shape_pt_lat", "shape_pt_lon")
    if not shapes or any(len(points) < 2 for points in shapes.values()):
        raise ValueError("Route geometry requires at least two actual coordinates")
    route_shapes, route_trips = defaultdict(set), Counter()
    for route in routes.values():
        if route["agency_id"] not in agency:
            raise ValueError("Route agency reference missing")
    for trip in trips.values():
        route, shape = trip["route_id"], trip["shape_id"]
        if route not in routes or shape not in shapes or trip["service_id"] not in services:
            raise ValueError("Trip route/service/shape reference missing")
        route_shapes[route].add(shape)
        route_trips[route] += 1
    trip_seqs, trip_stops = set(), defaultdict(set)
    for row in tables["stop_times.txt"]:
        trip, stop = row["trip_id"], row["stop_id"]
        key = trip, sequence(row["stop_sequence"])
        if trip not in trips or stop not in stops or key in trip_seqs:
            raise ValueError("Invalid stop-time trip/stop/sequence reference")
        trip_seqs.add(key)
        trip_stops[trip].add(stop)
    if set(trip_stops) != set(trips):
        raise ValueError("Trip without stop times")
    shapes_ordered = {key: [coords[k] for k in sorted(coords)] for key, coords in shapes.items()}
    source_counts = {"Agencies": len(agency), "Routes": len(routes), "Trips": len(trips),
                     "Stops": len(stops), "Shapes": len(shapes)}
    route_summary = [{"route_id": key, "route_short_name": row["route_short_name"],
                      "route_long_name": row["route_long_name"], "trips": route_trips[key],
                      "shape_ids": sorted(route_shapes[key])} for key, row in sorted(routes.items())]
    return source_counts, route_summary, shapes_ordered, stop_coords


def render_svg(path, counts, routes, shapes, stops, feed_start, feed_end, errors):
    points = [p for coords in shapes.values() for p in coords] + list(stops.values())
    minx, maxx = min(p[0] for p in points), max(p[0] for p in points)
    miny, maxy = min(p[1] for p in points), max(p[1] for p in points)
    coslat = math.cos(math.radians((miny + maxy) / 2))
    scale = min(565 / ((maxx-minx)*coslat), 472 / (maxy-miny))
    def project(p):
        return (42+(p[0]-minx)*coslat*scale, 570-(p[1]-miny)*scale)
    def elem(parent, tag, attrs, content=None):
        node = ET.SubElement(parent, f"{{{SVG}}}{tag}", {k: str(v) for k,v in attrs.items()})
        if content is not None:
            node.text = content
        return node
    root = ET.Element(f"{{{SVG}}}svg", {"viewBox": "0 0 960 715", "width": "960", "height": "715",
                     "role": "img", "aria-labelledby": "title desc"})
    elem(root, "title", {"id":"title"}, "Manteca transit — original GTFS geometry study")
    elem(root, "desc", {"id":"desc"}, "Original illustration from City of Manteca public data; actual trip-linked shape points and stops, not current travel directions.")
    elem(root, "rect", {"width":960,"height":715,"fill":"#f7fafb"})
    elem(root, "text", {"x":42,"y":43,"font-family":"sans-serif","font-size":26,"font-weight":"700","fill":"#132f46"}, "MANTECA | Transit patterns")
    elem(root, "text", {"x":42,"y":70,"font-size":14,"font-family":"sans-serif","fill":"#40566a"}, f"Declared feed period {feed_start} — {feed_end} | {counts['Stops']} stops, {counts['Shapes']} supplied shapes")
    elem(root, "rect", {"x":24,"y":87,"width":610,"height":501,"rx":8,"fill":"#fff","stroke":"#d4dfe6"})
    palette = ["#b44d21", "#186d93", "#237d65", "#8757ad", "#bc9a1b", "#df5280", "#52657a"]
    for i, route in enumerate(routes):
        color = palette[i % len(palette)]
        for shape in route["shape_ids"]:
            xy = [project(p) for p in shapes[shape]]
            elem(root, "polyline", {"points":" ".join(f"{x:.2f},{y:.2f}" for x,y in xy),
                "fill":"none","stroke":color,"stroke-width":2.2,"stroke-opacity":0.82,
                "stroke-linecap":"round","stroke-linejoin":"round","data-route":route["route_id"],"data-shape":shape})
        y = 112 + 51*i
        elem(root, "line", {"x1":660,"x2":684,"y1":y,"y2":y,"stroke":color,"stroke-width":4})
        elem(root, "text", {"x":695,"y":y+4,"font-family":"sans-serif","font-weight":"600","font-size":14,"fill":"#132f46"}, f"ID {route['route_id']} | {route['route_short_name']}")
        elem(root, "text", {"x":695,"y":y+22,"font-family":"sans-serif","font-size":12,"fill":"#40566a"}, f"{route['route_long_name']} ({route['trips']} trips)")
    for key, p in sorted(stops.items()):
        x,y = project(p)
        elem(root, "circle", {"cx":f"{x:.2f}","cy":f"{y:.2f}","r":1.9,"fill":"#fff","stroke":"#244359","stroke-width":0.7,"data-stop":key})
    elem(root, "text", {"x":659,"y":494,"font-family":"sans-serif","font-size":14,"font-weight":"700","fill":"#962e28"}, f"{errors} upstream GTFS errors")
    elem(root, "text", {"x":659,"y":514,"font-family":"sans-serif","font-size":11,"fill":"#40566a"}, "Geometry depiction, not validity certification.")
    elem(root, "text", {"x":42,"y":618,"font-family":"sans-serif","font-size":13,"fill":"#132f46"}, "Data: City of Manteca (CC BY 4.0); original coordinate projection, recoloring and annotation by Plenum.")
    elem(root, "text", {"x":42,"y":641,"font-family":"sans-serif","font-size":12,"fill":"#40566a"}, "Original source: manteca.gov/384/GTFS-Data | creativecommons.org/licenses/by/4.0/")
    elem(root, "text", {"x":42,"y":663,"font-family":"sans-serif","font-size":12,"fill":"#40566a"}, "North up; approximate local equirectangular projection. Scheduled pattern only; no live movements or ridership.")
    elem(root, "text", {"x":42,"y":685,"font-family":"sans-serif","font-size":12,"fill":"#40566a"}, "No city endorsement implied. No external map tiles, imagery or icons used.")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", type=Path, required=True)
    parser.add_argument("--upstream-report", type=Path, required=True, help="Original pinned MobilityData report.json")
    parser.add_argument("--system-errors", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report_bytes = bounded_bytes(args.upstream_report, MAX_REPORT)
    system_bytes = bounded_bytes(args.system_errors, MAX_SYSTEM)
    if (digest(args.feed) != FEED_SHA or sha256(report_bytes).hexdigest() != REPORT_SHA
            or sha256(system_bytes).hexdigest() != SYSTEM_SHA):
        raise ValueError("This original study requires the exact immutable input and original upstream receipt")
    report = json.loads(report_bytes)
    system = json.loads(system_bytes)
    if report["summary"]["validatorVersion"] != "8.0.1" or system != {"notices": []}:
        raise ValueError("Upstream run did not finish cleanly at expected version")
    counts, routes, shapes, stops = analyze(load_tables(args.feed))
    if any(report["summary"]["counts"].get(key) != value for key,value in counts.items()):
        raise ValueError("Independent count differs from canonical validator")
    totals = Counter()
    for notice in report["notices"]:
        totals[notice["severity"]] += int(notice["totalNotices"])
    args.out.mkdir(parents=True, exist_ok=False)
    svg = args.out / "transit-patterns.svg"
    feed_info = report["summary"]["feedInfo"]
    render_svg(svg, counts, routes, shapes, stops, feed_info["feedStartDate"], feed_info["feedEndDate"], totals["ERROR"])
    root = ET.parse(svg).getroot()
    if (len(root.findall(f"{{{SVG}}}circle")) != counts["Stops"] or
            {(p.attrib["data-route"], p.attrib["data-shape"]) for p in root.findall(f"{{{SVG}}}polyline")} !=
            {(r["route_id"], s) for r in routes for s in r["shape_ids"]}):
        raise ValueError("SVG readback diverges from actual input geometry identities")
    out = {"source":SOURCE,"license":LICENSE,"terms":TERMS,"input_sha256":FEED_SHA,
           "input_bytes":args.feed.stat().st_size,"upstream_version":"8.0.1","upstream_jar_sha256":JAR_SHA,
           "upstream_report_sha256":REPORT_SHA,"upstream_system_errors_sha256":SYSTEM_SHA,
           "status":"DATA_QUALITY_ERRORS_FOUND" if totals["ERROR"] else "NO_UPSTREAM_ERRORS",
           "independent_reference_integrity":"PASS","counts":counts,"route_rows":routes,
           "actual_shape_points":sum(map(len,shapes.values())),"svg_sha256":digest(svg),
           "upstream_notice_counts":dict(sorted(totals.items())), "feed_info":feed_info,
           "scope":"Original immutable schedule archive; finite coordinate and join check, not full GTFS reimplementation, live routing or ridership."}
    (args.out/"independent-report.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))


if __name__ == "__main__":
    main()
