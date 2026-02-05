import logging
from datetime import timedelta

from dateutil import parser

from .dji_pb2 import GenericMessage

logger = logging.getLogger(__name__)  # pylint: disable=C0103

# TODO: add tests

# Supported models:
# dvtm_ac203.proto is the Osmo Action 4 camera model
# dvtm_ac204.proto is the Osmo Action 5 camera model
# dvtm_ac206.proto is the Osmo Action 6 camera model
supported_models = ["dvtm_ac203.proto", "dvtm_ac204.proto", "dvtm_ac206.proto"]


def check_camera_model(message):
    """Check the camera model from the message."""
    # camera name is a string that contains the camera model
    # we do the compatibility check on the proto_name,
    # like is done in the exiftool repository:
    # https://exiftool.org/TagNames/DJI.html#Protobuf

    try:
        camera_model = message.video_global_info.module_info[0].camera_name
    except Exception as e:
        logger.error(f"Error during the camera model extraction: {e}")
        camera_model = "Unknown"
    else:
        try:
            sn = message.video_global_info.module_info[0].serial_number
            sn_string = f" (SN: {sn})"
        except Exception:
            sn_string = ""
        print(f"Detected Camera model: {camera_model}{sn_string}")
    try:
        proto_name = message.video_global_info.module_info[0].proto_name
    except Exception as e:
        logger.error(f"Error during the camera proto_name: {e}")
        proto_name = ""
    if proto_name not in supported_models:
        raise ValueError(
            "The camera model is not a supported Osmo Action camera (yet?)."
        )
    return True


def extract_gps_info(metadata, timezone_offset=0, extract_extensions=False):

    message = GenericMessage()
    try:
        message.ParseFromString(metadata)
    except Exception as e:
        print(f"Error during the decode operation: {e}")
        exit(-1)

    check_camera_model(message)

    frame_rate = None
    try:
        frame_rate = message.video_stream_info.details.frame_rate
    except Exception as e:
        logger.error(f"Error during the frame rate extraction: {e}")

    # TODO: check that the message contains the GPS data

    gps_data = []

    for gps in message.gps_info:
        try:
            gpsdate = parser.parse(gps.remote_gps_info.coordinates.datetime.datetime)
            homedate = gpsdate - timedelta(hours=timezone_offset)

            gps_point = {
                "timeinfo": homedate,
                "altitude": gps.remote_gps_info.coordinates.gps_altitude_mm / 1000,
                "longitude": gps.remote_gps_info.coordinates.info.longitude,
                "latitude": gps.remote_gps_info.coordinates.info.latitude,
            }

            if extract_extensions:
                gps_point.update(
                    {
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

            gps_data.append(gps_point)
        except Exception as e:
            logger.warning(f"Error parsing GPS entry: {e}")
            continue

    return gps_data, frame_rate
