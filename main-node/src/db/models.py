"""Relational schema for scalable timetable and change tracking."""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index, JSON, func
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True)
    eva = Column(Integer, unique=True, index=True, nullable=False)
    ds100 = Column(String(10), index=True)
    name = Column(String(100), nullable=False)
    meta = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    stops = relationship("TimetableStop", back_populates="station")


class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True)
    trip_id = Column(String, unique=True, index=True, nullable=False)
    category = Column(String(10))
    number = Column(String(20))
    operator = Column(String(20))
    type = Column(String(5))

    stops = relationship("TimetableStop", back_populates="trip")


class TimetableStop(Base):
    __tablename__ = "timetable_stops"
    id = Column(Integer, primary_key=True)
    stop_id = Column(String, unique=True, index=True, nullable=False)
    eva = Column(Integer, index=True, nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    station_id = Column(Integer, ForeignKey("stations.id"))

    trip = relationship("Trip", back_populates="stops")
    station = relationship("Station", back_populates="stops")
    planned_event = relationship("PlannedEvent", uselist=False, back_populates="stop")
    changed_events = relationship("ChangedEvent", back_populates="stop")

    __table_args__ = (Index("ix_stop_trip_eva", "trip_id", "eva"),)


class PlannedEvent(Base):
    __tablename__ = "planned_events"
    id = Column(Integer, primary_key=True)
    stop_id = Column(Integer, ForeignKey("timetable_stops.id"))
    event_type = Column(String(10))  # arrival / departure
    planned_time = Column(String)
    planned_platform = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    stop = relationship("TimetableStop", back_populates="planned_event")
    __table_args__ = (UniqueConstraint("stop_id", "event_type"),)


class ChangedEvent(Base):
    __tablename__ = "changed_events"
    id = Column(Integer, primary_key=True)
    stop_id = Column(Integer, ForeignKey("timetable_stops.id"))
    event_type = Column(String(10))  # arrival / departure
    changed_time = Column(String)
    changed_platform = Column(String)
    changed_status = Column(String)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    stop = relationship("TimetableStop", back_populates="changed_events")

    __table_args__ = (
        UniqueConstraint(
            "stop_id", "event_type", "changed_time", "changed_platform", "changed_status",
            name="uq_changed_event_dedup"
        ),
    )