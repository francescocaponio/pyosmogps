import xml.etree.ElementTree as ET

import gpxpy.gpx

# TODO: add tests


def write_gpx_file(output_file, gps_data, write_extensions=False):

    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    latitude = [point["latitude"] for point in gps_data]
    longitude = [point["longitude"] for point in gps_data]
    altitude = [point["altitude"] for point in gps_data]
    timeinfo = [point["timeinfo"] for point in gps_data]
    camera_acc_x = [point["camera_acc_x"] for point in gps_data]
    camera_acc_y = [point["camera_acc_y"] for point in gps_data]
    camera_acc_z = [point["camera_acc_z"] for point in gps_data]
    remote_der_x = [point["remote_der_x"] for point in gps_data]
    remote_der_y = [point["remote_der_y"] for point in gps_data]
    remote_der_z = [point["remote_der_z"] for point in gps_data]

    for i in range(len(timeinfo)):
        point = gpxpy.gpx.GPXTrackPoint(
            latitude=latitude[i],
            longitude=longitude[i],
            elevation=altitude[i],
            time=timeinfo[i],
        )

        if write_extensions:
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
