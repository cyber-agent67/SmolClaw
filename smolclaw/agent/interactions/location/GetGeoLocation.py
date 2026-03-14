"""Get geolocation interaction."""

import json
import time

from helium import get_driver

from smolclaw.agent.entities.browser.GeoLocation import GeoLocation


class GetGeoLocation:
    @staticmethod
    def execute() -> GeoLocation:
        """Gets physical location from browser geolocation service."""
        geo = GeoLocation()

        try:
            driver = get_driver()
            driver.execute_script(
                """
                var resultElement = document.createElement('div');
                resultElement.id = 'geolocation-result';
                resultElement.style.display = 'none';
                document.body.appendChild(resultElement);

                function handleLocation(position) {
                    var coords = position.coords;
                    var locationData = {
                        latitude: coords.latitude,
                        longitude: coords.longitude,
                        accuracy: coords.accuracy,
                        altitude: coords.altitude,
                        altitudeAccuracy: coords.altitudeAccuracy,
                        heading: coords.heading,
                        speed: coords.speed,
                        timestamp: position.timestamp,
                        success: true
                    };
                    resultElement.textContent = JSON.stringify(locationData);
                }

                function handleError(error) {
                    var errorData = {
                        error: error.message,
                        code: error.code,
                        success: false
                    };
                    resultElement.textContent = JSON.stringify(errorData);
                }

                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(handleLocation, handleError, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000
                    });
                } else {
                    resultElement.textContent = JSON.stringify({
                        error: 'Geolocation not supported',
                        success: false
                    });
                }

                setTimeout(function() {
                    if (resultElement.textContent === '') {
                        resultElement.textContent = JSON.stringify({
                            error: 'Timeout waiting for geolocation',
                            success: false
                        });
                    }
                }, 5000);
                """
            )

            time.sleep(6)
            location_result = driver.execute_script(
                """
                var element = document.getElementById('geolocation-result');
                if (element) {
                    var result = element.textContent;
                    element.remove();
                    return result;
                }
                return JSON.stringify({error: 'Result element not found', success: false});
                """
            )

            try:
                data = json.loads(location_result)
                geo.latitude = data.get("latitude")
                geo.longitude = data.get("longitude")
                geo.accuracy = data.get("accuracy")
                geo.altitude = data.get("altitude")
                geo.altitude_accuracy = data.get("altitudeAccuracy")
                geo.heading = data.get("heading")
                geo.speed = data.get("speed")
                geo.timestamp = data.get("timestamp")
                geo.success = data.get("success", False)
                geo.error = data.get("error")
            except Exception:
                geo.success = False
                geo.error = "Could not parse location data"
        except Exception as e:
            geo.success = False
            geo.error = str(e)

        return geo
