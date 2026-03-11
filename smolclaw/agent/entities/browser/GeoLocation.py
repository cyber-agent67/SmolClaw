"""GeoLocation entity - pure state container."""

from typing import Optional


class GeoLocation:
    def __init__(self):
        self.latitude: Optional[float] = None
        self.longitude: Optional[float] = None
        self.accuracy: Optional[float] = None
        self.altitude: Optional[float] = None
        self.altitude_accuracy: Optional[float] = None
        self.heading: Optional[float] = None
        self.speed: Optional[float] = None
        self.timestamp: Optional[int] = None
        self.success: bool = False
        self.error: Optional[str] = None
