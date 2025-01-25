import argparse
import logging
import logging.config
import os
import sys
import tempfile
from pathlib import Path

import pyosmogps

from .data_filters import resample_gps_data
from .ffmpeg_manager import extract_dji_metadata_stream, get_total_frame_count
from .gpx_manager import write_gpx_file
from .metadata_manager import extract_gps_info

logger = logging.getLogger(__name__)  # pylint: disable=C0103


def _make_parser() -> argparse.ArgumentParser:
    # Separated so sphinx-argparse-cli can do its auto documentation magic.
    parser = argparse.ArgumentParser(
        description="Extract the GPS data from the Osmo Action video files",
        prog="pyosmogps",
    )
    parser.add_argument(
        "command",
        choices=["extract", "merge"],
        help="Specify the command to run: 'extract' to extract "
        "GPS data or 'merge' to merge GPX files.",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input file(s). Accepts a single file or multiple files.",
    )
    parser.add_argument(
        "output",
        help="Output file. Accepts a single file or multiple files.",
    )
    parser.add_argument(
        "--frequency",
        "-f",
        type=float,
        default=2.0,
        help="Set the output data frequency in Hz (default: 2 Hz).",
    )
    parser.add_argument(
        "--resampling-method",
        "-r",
        choices=["discard", "interpolate", "lpf"],
        default="interpolate",
        help="Set the method for resampling data: 'discard' to drop "
        "excess samples, 'interpolate' for linear interpolation, 'lpf' "
        "for low pass filtering (default: interpolate).",
    )
    parser.add_argument(
        "--timezone-offset",
        "-t",
        type=int,
        default=0,
        help="Set the timezone offset in hours (default: 0).",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {pyosmogps.__version__}"
    )
    return parser


def extract(
    inputs, output_file, output_frequency, resampling_method, timezone_offset=0
):
    print(f"Running extract command with inputs: {inputs} and output: {output_file}")

    global_gps_info = []
    for i, input_file in enumerate(inputs, start=1):
        print(f"Processing file {i}/{len(inputs)}: {input_file} -> {output_file}")

        input_frame_rate, video_duration = get_total_frame_count(input_file)
        print(f"Frame rate: {input_frame_rate}, duration: {video_duration}")

        temp_file = os.path.join(tempfile.gettempdir(), Path(input_file).stem + ".tmp")
        extract_dji_metadata_stream(input_file, temp_file)

        gps_info = extract_gps_info(temp_file, timezone_offset)
        print(f"Extracted {len(gps_info)} GPS data points.")

        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass

        global_gps_info.extend(gps_info)

    global_gps_info = resample_gps_data(
        global_gps_info, input_frame_rate, output_frequency, resampling_method
    )

    if global_gps_info != []:
        write_gpx_file(output_file, global_gps_info)


def main() -> int:
    parser = _make_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    if args.command == "extract":
        if not args.inputs or not args.output:
            parser.error(
                "'extract' command requires at least one input file and one "
                "output file."
            )
        extract(args.inputs, args.output, args.frequency, args.resampling_method)

    elif args.command == "merge":
        print("Running merge command...")
        # TODO: Implement merge command
    else:
        parser.print_help()
        parser.exit()

    return 0


if __name__ == "__main__":
    exit(main())
