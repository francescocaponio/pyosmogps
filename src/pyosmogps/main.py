import argparse
import logging
import logging.config
import sys

from . import OsmoGps
from . import __version__ as pyosmogps_version

logger = logging.getLogger(__name__)  # pylint: disable=C0103


def _make_parser() -> argparse.ArgumentParser:
    # Separated so sphinx-argparse-cli can do its auto documentation magic.
    parser = argparse.ArgumentParser(
        description="Extract the GPS data from the Osmo Action video files",
        prog="pyosmogps",
    )
    parser.add_argument(
        "command",
        choices=["extract", "merge", "geotag"],
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
        choices=["discard", "linear", "lpf", "none"],
        default="linear",
        help="Set the method for resampling data: 'discard' to drop "
        "excess samples, 'linear' for linear interpolation, 'lpf' "
        "for low pass filtering, 'none' for no data reduction (default: linear).",
    )
    parser.add_argument(
        "--timezone-offset",
        "-t",
        type=int,
        default=0,
        help="Set the timezone offset in hours (default: 0).",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {pyosmogps_version}"
    )
    return parser


def extract(inputs, output=None, frequency=2.0, resampling_method="linear", timezone_offset=0) -> bool:
    try:
        gps = OsmoGps(inputs, timezone_offset)
        gps.resample(frequency, resampling_method)
        if output is not None:
            gps.save_gpx(output)

    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    return gps


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
        gps = extract(
            args.inputs,
            args.output,
            args.frequency,
            args.resampling_method,
            args.timezone_offset,
        )
        return 0 if gps is not None else 1

    elif args.command == "merge":
        print("Running merge command...")
        # TODO: Implement merge command

    elif args.command == "geotag":
        print("Running geotag command...")
        gps = OsmoGps(args.inputs, args.timezone_offset)
        for input_file in args.inputs:
            gps.geotag(input_file)

    else:
        parser.print_help()
        parser.exit()

    return 0


if __name__ == "__main__":
    exit(main())
