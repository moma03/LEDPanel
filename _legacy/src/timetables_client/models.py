from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# ----------------------
# Enums (as Literals)
# ----------------------
ConnectionStatus = Literal["w", "n", "a"]
"""
w - WAITING This (regular) connection is waiting.
n - TRANSITION This (regular) connection CANNOT wait.
a - ALTERNATIVE This is an alternative (unplanned) connection that has been introduced as a replacement for one regular connection that cannot wait. The connections "tl" (triplabel) attribute might in this case refer to the replaced connection (or more specifi-cally the trip from that connection). Alternative connections are always waiting (they are re-moved otherwise).
"""

DelaySource = Literal["L", "NA", "NM", "V", "IA", "IM", "A"]
"""
L - LEIBIT LeiBit/LeiDis.
NA - RISNE AUT IRIS-NE (automatisch).
NM - RISNE MAN IRIS-NE (manuell).
V - VDV Prognosen durch dritte EVU über VDVin.
IA - ISTP AUT ISTP automatisch.
IM - ISTP MAN ISTP manuell.
A - AUTOMATIC PROGNOSIS Automatische Prognose durch Prognoseautomat.
"""

DistributorType = Literal["s", "r", "f", "x"]
"""
s - CITY
r - REGION
f - LONG DISTANCE
x - OTHER
"""

MessageType = Literal["h", "q", "f", "d", "i", "u", "r", "c"]
"""
h - HIM A HIM message (generated through the Hafas Information Manager).
q - QUALITY CHANGE A message about a quality change.
f - FREE A free text message.
d - CAUSE OF DELAY A message about the cause of a delay.
i - IBIS An IBIS message (generated from IRIS-AP).
u - UNASSIGNED IBIS MESSAGE An IBIS message (generated from IRIS-AP) not yet assigned to a train.
r - DISRUPTION A major disruption.
c - CONNECTION A connection.
"""

Priority = Literal["1", "2", "3", "4"]
"""
1 - HIGH
2 - MEDIUM
3 - LOW
4 - DONE
"""

"""
b - BEFORE The reference trip ends before that stop.
e - END The reference trips ends at that stop.
c - BETWEEN The stop is between reference trips start and end, in other words, the stop is contained within its travel path.
s - START The reference trip starts at that stop.
a - AFTER The reference trip starts after that stop.
"""
ReferenceTripRelationToStop = Literal["b", "e", "c", "s", "a"]

"""
p - PLANNED The event was planned. This status is also used when the cancellation of an event has been revoked.
a - ADDED The event was added to the planned data (new stop).
c - CANCELLED The event was canceled (as changedstatus, can apply to planned and added stops).
"""
EventStatus = Literal["p", "a", "c"]

"""
Unknown codes
"""
TripType = Literal["p", "e", "z", "s", "h", "n"]


# ----------------------
# Models (Pydantic v2)
# ----------------------

class BaseModelWithConfig(BaseModel):
    def __str__(self):
        # just print attributes that are not None
        attrs = []
        for field, value in self.__dict__.items():
            if value is not None:
                attrs.append(f"{field}={value}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"

    __repr__ = __str__


class DistributorMessage(BaseModelWithConfig):
    model_config = ConfigDict(extra="ignore")

    int: Optional[str] = None
    """ internal text """
    n: Optional[str] = None
    """ distributor name """
    t: Optional[DistributorType] = None
    """ distributor type """
    ts: Optional[str] = None
    """ Timestamp. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """


class Message(BaseModelWithConfig):
    """
    A message that is associated with an event, a stop or a trip.
    """
    model_config = ConfigDict(extra="ignore")

    c: Optional[str] = None
    """ message code"""
    cat: Optional[str] = None
    """ message category """
    del_: Optional[int] = Field(default=None, alias="del")
    """ deletion flag """
    dm: Optional[List[DistributorMessage]] = None
    """ distributor messages """
    ec: Optional[str] = None
    """ external category """
    elnk: Optional[str] = None
    """ External link associated with the message """
    ext: Optional[str] = None
    """ external text """
    from_: Optional[str] = Field(default=None, alias="from")
    """ Valid from. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    id: Optional[str] = None
    """ message id """
    int: Optional[str] = None
    """ internal text """
    o: Optional[str] = None
    """ owner """
    pr: Optional[Priority] = None
    """ priority """
    t: MessageType
    """ message type """
    tl: Optional[List["TripLabel"]] = None
    """ trip labels """
    to: Optional[str] = None
    """" Valid to. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    ts: str
    """ Timestamp. The time, in ten digit 'YYMMddHHmm' format, e.g. "1404011437" for 14:37 on April the 1st of 2014. """


class Event(BaseModelWithConfig):
    """
    An event (arrival or departure) that is part of a stop.
    """
    model_config = ConfigDict(extra="ignore")

    cde: Optional[str] = None
    """ Changed distant endpoint. """
    clt: Optional[str] = None
    """ Cancellation time. Time when the cancellation of this stop was created. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    cp: Optional[str] = None
    """ Changed platform. """
    cpth: Optional[List[str]] = None
    """ Changed path. """
    cs: Optional[EventStatus] = None
    """ Event status. """
    ct: Optional[str] = None
    """ Changed time. New estimated or actual departure or arrival time. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    dc: Optional[int] = None
    """ Distant change. """
    hi: Optional[int] = None
    """ Hidden. 1 if the event should not be shown on WBT because travellers are not supposed to enter or exit the train at this stop. """
    l: Optional[str] = None
    """ Line. The line indicator (e.g. "3" for an S-Bahn or "45S" for a bus). """
    m: Optional[List[Message]] = None
    """ List of messages. """
    pde: Optional[str] = None
    """ Planned distant endpoint. """
    pp: Optional[str] = None
    """ Planned platform. """
    ppth: Optional[List[str]] = None
    """ 
    Planned Path. A sequence of station names. E.g.: 'Mainz Hbf', 'Rüsselsheim', 'Frankfrt(M) Flughafen'. 
    For arrival, the path indicates the stations that come before the current station. The first element then is the trip's start station.
    For departure, the path indicates the stations that come after the current station. The last element in the path then is the trip's destination station.
    Note that the current station is never included in the path (neither for arrival nor for departure). 
    """
    ps: Optional[EventStatus] = None
    """ Planned event status. The previous value of the 'cs' attribute. """
    pt: Optional[str] = None
    """ Planned time. Planned departure or arrival time. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    tra: Optional[str] = None
    """ Transition. Trip id of the next or previous train of a shared train. At the start stop this references the previous trip, at the last stop it references the next trip. E.g. '2016448009055686515-1403311438-1 """
    wings: Optional[List[str]] = None
    """ Wing. A sequence of trip id. E.g. '-906407760000782942-1403311431'. """


class HistoricDelay(BaseModelWithConfig):
    """
    It's the history of all delay-messages for a stop. This element extends HistoricChange.
    """
    model_config = ConfigDict(extra="ignore")

    ar: Optional[str] = None
    """ The arrival event. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    cod: Optional[str] = None
    """ Detailed description of delay cause. """
    dp: Optional[str] = None
    """ The departure event. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """
    src: Optional[DelaySource] = None
    """ Delay source. """
    ts: Optional[str] = None
    """ Timestamp. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """


class HistoricPlatformChange(BaseModelWithConfig):
    """
    It's the history of all platform-changes for a stop. This element extends HistoricChange.
    """
    model_config = ConfigDict(extra="ignore")

    ar: Optional[str] = None
    """ Arrival platform. """
    cot: Optional[str] = None
    """ Detailed cause of track change. """
    dp: Optional[str] = None
    """ Departure platform. """
    ts: Optional[str] = None
    """ Timestamp. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """


class TripLabel(BaseModelWithConfig):
    """
    It's a compound data type that contains common data items that characterize a Trip.
    The contents is represented as a compact 6-tuple in XML.
    """
    model_config = ConfigDict(extra="ignore")

    c: str
    """ Category. Trip category, e.g. "ICE" or "RE """
    n: str
    """ Trip/train number, e.g. "4523". """
    o: str
    """ Owner. A unique short-form and only intended to map a trip to specific evu. """
    f: Optional[str] = None
    """ Filter flags. """
    t: Optional[TripType] = None
    """ Trip type. """


class ReferenceTripLabel(BaseModelWithConfig):
    """
    It's a compound data type that contains common data items that characterize a reference trip. The con-tents is represented as a compact 3-tuple in XML.
    """

    model_config = ConfigDict(extra="ignore")

    c: str
    """ Category. Trip category, e.g. "ICE" or "RE". """
    n: str
    """ Trip/train number, e.g. "4523". """


class ReferenceTripStopLabel(BaseModelWithConfig):
    """
    It's a compound data type that contains common data items that characterize a reference trip stop. The contents is represented as a compact 4-tuple in XML.
    """
    model_config = ConfigDict(extra="ignore")

    eva: int
    """ The eva number of the correspondent stop of the regular trip. """
    i: int
    """ The index of the correspondent stop of the regu-lar trip. """
    n: str
    """ The (long) name of the correspondent stop of the regular trip. """
    pt: str
    """ The planned time of the correspondent stop of the regular trip. """


class ReferenceTrip(BaseModelWithConfig):
    """
    A reference trip is another real trip, but it doesn't have its own stops and events. It refers only to its ref-erenced regular trip. The reference trip collects mainly all different attributes of the referenced regular trip.
    """
    model_config = ConfigDict(extra="ignore")

    c: bool
    """ The cancellation flag. True means, the reference trip is cancelled. """
    ea: ReferenceTripStopLabel
    """ The first stop of the reference trip. ???"""
    id: str
    """
    An id that uniquely identifies the reference trip. It consists of the following two elements separated by dashes:

    A 'daily trip id' that uniquely identifies a reference trip within one day. This id is typically reused on subsequent days. This could be negative.
    A 10-digit date specifier (YYMMddHHmm) that indicates the planned departure date of the referenced regular trip from its start station.
    Example:
    '-7874571842864554321-1403311221' would be used for a trip with daily trip id '-7874571842864554321' that starts on march the 31th 2014.
    """
    rtl: ReferenceTripLabel
    """ The trip label of the reference trip. ???"""
    sd: ReferenceTripStopLabel
    """ The last stop of the reference trip. ???"""


class ReferenceTripRelation(BaseModelWithConfig):
    """
    A reference trip relation holds how a reference trip is related to a stop, for instance the reference trip starts after the stop. Stop contains a collection of that type, only if reference trips are available.
    """
    model_config = ConfigDict(extra="ignore")

    rt: ReferenceTrip
    """ The reference trip. """
    rts: ReferenceTripRelationToStop
    """ The relation of the reference trip to the stop. """


class TripReference(BaseModelWithConfig):
    """
    It's a reference to another trip, which holds its label and reference trips, if available.
    """
    model_config = ConfigDict(extra="ignore")

    rt: Optional[List[TripLabel]] = None
    """ The referred trips reference trip elements. """
    tl: TripLabel
    """ The referred trips trip label. """


class Connection(BaseModelWithConfig):
    """ It's information about a connected train at a particular stop. """
    model_config = ConfigDict(extra="ignore")

    cs: ConnectionStatus
    """ Connection status. """
    eva: Optional[int] = None
    """ EVA station number. """
    id: str
    """ the trip id of the connected train. """
    ref: Optional["TimetableStop"] = None
    """ Reference to the connected train's stop at this station. Only available if the connected train is part of the same timetable response. """
    s: "TimetableStop"
    """ The stop of the connected train at this station. """
    ts: str
    """ Timestamp. The time, in ten digit 'YYMMddHHmm' format, e.g. '1404011437' for 14:37 on April the 1st of 2014. """


class TimetableStop(BaseModelWithConfig):
    """
    A stop is a part of a Timetable.
    """
    model_config = ConfigDict(extra="ignore")

    ar: Optional[Event] = None
    """ Arrival event. """
    conn: Optional[List[Connection]] = None
    """ Connection element. """
    dp: Optional[Event] = None
    """ Departure event. """
    eva: Optional[int] = None
    """ The eva code of the station of this stop. Example '8000105' for Frankfurt(Main)Hbf. """
    hd: Optional[List[HistoricDelay]] = None
    """ historic delays. """
    hpc: Optional[List[HistoricPlatformChange]] = None
    """ Historic platform change element. """
    id: str
    """
    An id that uniquely identifies the stop. It consists of the following three elements separated by dashes
    - a 'daily trip id' that uniquely identifies a trip within one day. This id is typically reused on subsequent days. This could be negative.
    - a 6-digit date specifier (YYMMdd) that indicates the planned departure date of the trip from its start station.
    - an index that indicates the position of the stop within the trip (in rare cases, one trip may arrive multiple times at one station). Added trips get indices above 100. Example '-7874571842864554321-1403311221-11' would be used for a trip with daily trip id '-7874571842864554321' that starts on march the 31th 2014 and where the current station is the 11th stop.
    """
    m: Optional[List[Message]] = None
    """ Message elements """
    ref: Optional[TripReference] = None
    """ Reference to another trip. Mostly used for the trip the train continues as. More details in the 'rtr' field """
    rtr: Optional[List[ReferenceTripRelation]] = None
    """ Reference trip relation element. Defines the relation of reference trips to this stop. """
    tl: Optional[TripLabel] = None
    """ The trip label of the trip that serves this stop. """


class StationData(BaseModelWithConfig):
    """
    A transport object which keep data for a station.
    """
    model_config = ConfigDict(extra="ignore")

    ds100: str
    """ DS100 station code. """
    eva: int
    """ EVA station number. """
    meta: Optional[List[str]] = None
    """ List of meta stations. """
    name: str
    """ Station name. """
    p: Optional[List[str]] = None
    """ List of platforms. """


class MultipleStationData(BaseModelWithConfig):
    """
    A wrapper that represents multiple StationData objects.
    """
    model_config = ConfigDict(extra="ignore")

    station: List[StationData]
    """ List of stations. """


class Timetable(BaseModelWithConfig):
    """
    A timetable is made of a set of TimetableStops and a potential Disruption.
    """
    model_config = ConfigDict(extra="ignore")

    eva: Optional[int] = None
    """ The eva code of the station for which this timetable is valid. Example '8000105' for Frankfurt(Main)Hbf. """
    m: Optional[List[Message]] = None
    """ Messages that are associated with the whole timetable. """
    s: Optional[List[TimetableStop]] = None
    """ The stops that are part of this timetable. """
    station: Optional[str] = None
    """ The name of the station for which this timetable is valid. Example 'Frankfurt(Main)Hbf' for Frankfurt(Main)Hbf. """

    def __add__(self, other):
        if self.eva is None and self == Timetable():
            return other
        if other.eva is None and other == Timetable():
            return self

        if isinstance(other, Timetable):
            if self.eva != other.eva:
                raise ValueError("Cannot combine Timetables for different stations")
            # concatenate messages and stops, avoiding duplicates by id
            if self.m is None:
                self.m = []
            if self.s is None:
                self.s = []
            if other.m:
                existing_message_ids = {msg.id for msg in self.m if msg.id is not None}
                for msg in other.m:
                    if msg.id not in existing_message_ids:
                        self.m.append(msg)
            if other.s:
                existing_stop_ids = {stop.id for stop in self.s}
                for stop in other.s:
                    if stop.id not in existing_stop_ids:
                        self.s.append(stop)
            return self
        return NotImplemented

    def __eq__(self, other):
        if not isinstance(other, Timetable):
            return NotImplemented
        return self.eva == other.eva and self.m == other.m and self.s == other.s and self.station == other.station


# Resolve forward refs
Message.model_rebuild()
Event.model_rebuild()
Connection.model_rebuild()
TimetableStop.model_rebuild()
TripReference.model_rebuild()
