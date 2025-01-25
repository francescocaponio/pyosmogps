import logging
from datetime import timedelta

from dateutil import parser

from .dji_pb2 import GenericMessage

logger = logging.getLogger(__name__)  # pylint: disable=C0103

# TODO: add tests


def extract_gps_info(input_file, timezone_offset=0):

    with open(input_file, "rb") as f:
        data = f.read()

    message = GenericMessage()
    try:
        message.ParseFromString(data)
    except Exception as e:
        print(f"Error during the decode operation: {e}")
        exit(-1)

    # TODO: check the camera model

    # TODO: check that the message contains the GPS data

    gps_data = []

    for gps in message.gps_info:
        try:
            gpsdate = parser.parse(gps.remote_gps_info.coordinates.datetime.datetime)
            homedate = gpsdate - timedelta(hours=timezone_offset)

            gps_data.append(
                {
                    "timeinfo": homedate,
                    "altitude": gps.remote_gps_info.coordinates.gps_altitude_mm / 1000,
                    "longitude": gps.remote_gps_info.coordinates.info.longitude,
                    "latitude": gps.remote_gps_info.coordinates.info.latitude,
                    "camera_acc_x": gps.camera_info.accelerometer1.x,
                    "camera_acc_y": gps.camera_info.accelerometer1.y,
                    "camera_acc_z": gps.camera_info.accelerometer1.z,
                    "camera_acc2_x": gps.camera_info.accelerometer2.x,
                    "camera_acc2_y": gps.camera_info.accelerometer2.y,
                    "camera_acc2_z": gps.camera_info.accelerometer2.z,
                    "remote_der_x": gps.remote_gps_info.derivatives.x,
                    "remote_der_y": gps.remote_gps_info.derivatives.y,
                    "remote_der_z": gps.remote_gps_info.derivatives.z,
                }
            )
        except Exception as e:
            logger.warning(f"Error parsing GPS entry: {e}")
            continue

    return gps_data
