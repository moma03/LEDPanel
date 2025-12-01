from typing import Any, Dict, Iterable
import xmltodict

# ----------------------
# Helpers for XML -> dict normalization
# ----------------------

LIST_FIELDS = {
    # Timetable
    ("timetable", "s"),                # list of TimetableStop
    ("timetable", "m"),                # list of Message
    # TimetableStop
    ("s", "conn"),                     # list of Connection
    ("s", "m"),                        # list of Message
    ("s", "hd"),                       # list of HistoricDelay
    ("s", "hpc"),                      # list of HistoricPlatformChange
    ("s", "rtr"),                      # list of ReferenceTripRelation
    # Message
    ("m", "dm"),                       # list of DistributorMessage
    ("m", "tl"),                       # list of TripLabel (for trip label references inside message)
    # TripReference
    ("ref", "rt"),                     # list of TripLabel (reference trips)
    # MultipleStationData
    ("stations", "station"),           # list of StationData – when top-level element is <stations>
    # Events
    ("ar", "m"),                       # list of Message
    ("dp", "m"),                       # list of Message
    # Pipe-separated fields
    ("ar", "ppth"),                    # list of planned path
    ("dp", "ppth"),                    # list of planned path
    ("ar", "cpth"),                    # list of current path
    ("dp", "cpth"),                    # list of current path
    ("ar", "wings"),                  # list of wing stations
    ("dp", "wings"),                  # list of wing stations
    ("station", "meta"),              # list of meta tags (in StationData)
    ("station", "p"),                 # list of platforms (in StationData)
}

PIPE_LIST_FIELDS = [
    "cpth",
    "ppth",
    "wings",
    "meta",
    "p"
]

def _strip_attr_prefix(obj: Any) -> Any:
    """Recursively remove xmltodict attribute prefix '@' and collapse '#text'."""
    if isinstance(obj, dict):
        new: Dict[str, Any] = {}
        for k, v in obj.items():
            if k == "#text":
                # prefer text as plain value when encountered
                return _strip_attr_prefix(v)
            key = k[1:] if k.startswith("@") else k
            new[key] = _strip_attr_prefix(v)
        return new
    elif isinstance(obj, list):
        return [_strip_attr_prefix(v) for v in obj]
    else:
        return obj


def _ensure_lists(node: Any, parent_key: str | None = None) -> Any:
    """Recursively enforce LIST_FIELDS: certain children must always be lists."""
    if isinstance(node, dict):
        normalized = {}
        for k, v in node.items():
            v_norm = _ensure_lists(v, parent_key=k)
            normalized[k] = v_norm

            # If (parent_key, this_key) is in LIST_FIELDS -> enforce list
            if (parent_key, k) in LIST_FIELDS:
                if v_norm is None:
                    normalized[k] = []
                elif not isinstance(v_norm, list):
                    normalized[k] = [v_norm]
        return normalized
    elif isinstance(node, list):
        return [_ensure_lists(x, parent_key=parent_key) for x in node]
    else:
        return node


def _split_pipe_fields(node: Any, fields: Iterable[str] = PIPE_LIST_FIELDS) -> Any:
    """Recursively split pipe-separated station path fields into lists."""
    if isinstance(node, dict):
        new_node = {}
        for k, v in node.items():
            v = _split_pipe_fields(v)  # recurse first
            if k in PIPE_LIST_FIELDS and isinstance(v, str):
                new_node[k] = [s.strip() for s in v.split("|") if s.strip()]
            else:
                new_node[k] = v
        return new_node
    elif isinstance(node, list):
        return [_split_pipe_fields(x) for x in node]
    else:
        return node


def normalize_xml_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = _strip_attr_prefix(d)
    d = _split_pipe_fields(d)
    d = _ensure_lists(d)

    # Handle empty timetable explicitly
    if "timetable" in d and (d["timetable"] is None or d["timetable"] == {}):
        d["timetable"] = {"s": []}

    d = _ensure_lists(d)

    return d


def parse(xml: str) -> Dict[str, Any]:
    parsed = xmltodict.parse(xml)
    return normalize_xml_dict(parsed)
