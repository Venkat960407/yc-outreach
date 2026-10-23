"""Round-trip check: export the synthetic network as GeoJSON (placed at an arbitrary latitude),
load it back through the GeoJSON path, and confirm the plan comes out the same."""
import json, math
import numpy as np
import pad_planner as pp

lines, names, subs = pp.synthetic_network()
# centre the network on lat0 so the loader's projection (taken at the mean latitude) matches
cy = np.mean(np.vstack([np.vstack([pp.sample_line(l, 0.25) for l in lines])])[:, 1])
lines = [l - [0, cy] for l in lines]; subs = subs - [0, cy]
lat0, lon0 = 47.5, -121.5
to_ll = lambda xy: [[lon0 + x / (pp.MI_PER_DEG_LAT * math.cos(math.radians(lat0))), lat0 + y / pp.MI_PER_DEG_LAT]
                    for x, y in xy]
feats = [{"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": to_ll(l)}}
         for l in lines]
feats += [{"type": "Feature", "properties": {"substation": True, "name": n},
           "geometry": {"type": "Point", "coordinates": to_ll([p])[0]}} for n, p in zip(names, subs)]
json.dump({"type": "FeatureCollection", "features": feats}, open("synthetic_network.geojson", "w"))

a = pp.plan(lines, subs, 85, 0.2, 30)
l2, n2, s2 = pp.load_geojson("synthetic_network.geojson")
b = pp.plan(l2, s2, 85, 0.2, 30)
assert len(a["pads"]) == len(b["pads"]), (len(a["pads"]), len(b["pads"]))
assert abs(a["line_mi"] - b["line_mi"]) / a["line_mi"] < 0.02
print("GeoJSON round trip OK:", len(b["pads"]), "pads,", b["line_mi"], "line-mi")
