import logging
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import gpxpy.gpx

from .data_filters import (
    discard_resample_gps_data,
    linear_resample_gps_data,
    lpf_resample_gps_data,
)
from .ffmpeg_manager import extract_dji_metadata_stream, get_total_frame_count
from .metadata_manager import extract_gps_info

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class OsmoGps:
    gps_data = None
    inputs = None
    input_frame_rate = None
    input_duration = 0
    output_frequency = None
    resampling_method = None
    extract_extensions = False

    def __init__(self, inputs, timezone_offset=0, extract_extensions=False):
        if inputs is None:
            raise ValueError("inputs cannot be None")
        self.inputs = inputs
        self.timezone_offset = timezone_offset
        self.extract_extensions = extract_extensions

        self.extract()

    def extract(self):

        logger.info(f"Running extract command with inputs: {self.inputs}")

        self.gps_data = []
        for i, input_file in enumerate(self.inputs, start=1):
            logger.info(f"Processing file {i}/{len(self.inputs)}: {input_file}")

            input_frame_rate, video_duration = get_total_frame_count(input_file)
            logger.info(f"Frame rate: {input_frame_rate}, duration: {video_duration}")
            self.input_frame_rate = input_frame_rate
            self.input_duration += video_duration

            temp_file = os.path.join(
                tempfile.gettempdir(), Path(input_file).stem + ".tmp"
            )
            extract_dji_metadata_stream(input_file, temp_file)

            gps_info = extract_gps_info(
                temp_file, self.timezone_offset, self.extract_extensions
            )
            logger.info(f"Extracted {len(gps_info)} GPS data points.")

            try:
                os.remove(temp_file)
            except FileNotFoundError:
                pass

            self.gps_data.extend(gps_info)

    def resample(
        self,
        output_frequency=None,
        resampling_method=None,
    ):
        self.resampling_method = resampling_method
        if self.resampling_method is not None:
            if self.resampling_method not in ["discard", "linear", "lpf", "none"]:
                raise ValueError(
                    "resampling_method must be one of "
                    "'discard', 'linear', 'lpf', 'none'"
                )
            self.output_frequency = output_frequency
            if self.resampling_method in ["discard", "linear", "lpf"]:
                if self.output_frequency is None:
                    raise ValueError(
                        "output_frequency cannot be None when "
                        "resampling_method is not 'none'"
                    )
        logger.info(
            f"Resampling GPS data with method: {self.resampling_method}, "
            f"output frequency: {self.output_frequency}"
        )
        if self.resampling_method is not None:
            if self.resampling_method == "linear":
                resampled_data = linear_resample_gps_data(
                    self.gps_data, self.input_frame_rate, self.output_frequency
                )
            elif self.resampling_method == "lpf":
                resampled_data = lpf_resample_gps_data(
                    self.gps_data, self.input_frame_rate, self.output_frequency
                )
            elif self.resampling_method == "discard":
                resampled_data = discard_resample_gps_data(
                    self.gps_data, self.input_frame_rate, self.output_frequency
                )
            self.gps_data = resampled_data

    def save_gpx(self, output_file):
        if self.gps_data != []:
            gpx = gpxpy.gpx.GPX()
            gpx.creator = "pyosmogps -- https://github.com/francescocaponio/pyosmogps"
            track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(track)
            segment = gpxpy.gpx.GPXTrackSegment()
            track.segments.append(segment)

            latitude = [point["latitude"] for point in self.gps_data]
            longitude = [point["longitude"] for point in self.gps_data]
            altitude = [point["altitude"] for point in self.gps_data]
            timeinfo = [point["timeinfo"] for point in self.gps_data]
            if self.extract_extensions:
                camera_acc_x = [point["camera_acc_x"] for point in self.gps_data]
                camera_acc_y = [point["camera_acc_y"] for point in self.gps_data]
                camera_acc_z = [point["camera_acc_z"] for point in self.gps_data]
                remote_der_x = [point["remote_der_x"] for point in self.gps_data]
                remote_der_y = [point["remote_der_y"] for point in self.gps_data]
                remote_der_z = [point["remote_der_z"] for point in self.gps_data]

            for i in range(len(timeinfo)):
                point = gpxpy.gpx.GPXTrackPoint(
                    latitude=latitude[i],
                    longitude=longitude[i],
                    elevation=altitude[i],
                    time=timeinfo[i],
                )

                if self.extract_extensions:
                    extensions = ET.Element("extensions")

                    acc_x_ext = ET.SubElement(extensions, "acc_x")
                    acc_x_ext.text = f"{camera_acc_x[i]:.3f}"

                    acc_y_ext = ET.SubElement(extensions, "acc_y")
                    acc_y_ext.text = f"{camera_acc_y[i]:.3f}"

                    acc_z_ext = ET.SubElement(extensions, "acc_z")
                    acc_z_ext.text = f"{camera_acc_z[i]:.3f}"

                    der_x_ext = ET.SubElement(extensions, "der_x")
                    der_x_ext.text = f"{remote_der_x[i]:.3f}"

                    der_y_ext = ET.SubElement(extensions, "der_y")
                    der_y_ext.text = f"{remote_der_y[i]:.3f}"

                    der_z_ext = ET.SubElement(extensions, "der_z")
                    der_z_ext.text = f"{remote_der_z[i]:.3f}"

                    point.extensions.append(extensions)
                segment.points.append(point)

            with open(output_file, "w") as gpx_file:
                gpx_file.write(gpx.to_xml())

            logger.info(f"GPS data written to {output_file}")
            return True
        else:
            logger.info("No GPS data extracted.")
            return False

    def get_altitude(self):
        return [point["altitude"] for point in self.gps_data]

    def get_latitude(self):
        return [point["latitude"] for point in self.gps_data]

    def get_longitude(self):
        return [point["longitude"] for point in self.gps_data]
