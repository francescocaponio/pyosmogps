import os
import subprocess
from pathlib import Path


# Funzione per ottenere il numero totale di frame
def get_total_frame_count(video_path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate,duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"Error during the execution of ffprobe: {result.stderr.strip()}"
        )
    try:
        output = result.stdout.strip().split("\n")
        frame_rate = eval(output[0])
        duration = float(output[1])
        return frame_rate, duration
    except ValueError:
        raise ValueError(
            "Unable to obtain the frame number and rate. "
            f"Output ffprobe: '{result.stdout.strip()}'"
        )


def extract_dji_metadata_stream(video_path, output_path):

    if not video_path.lower().endswith(".mp4"):
        raise ValueError("the input file must be a mp4 file.")

    if Path(output_path).is_file():
        os.remove(output_path)

    command = [
        "ffmpeg",
        "-hwaccel",
        "cuda",  # Usa accelerazione hardware
        "-loglevel",
        "error",
        "-nostdin",
        "-flush_packets",
        "1",
        "-i",
        video_path,  # Input video
        "-map",
        "0:2",
        "-c",
        "copy",
        "-f",
        "data",
        output_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            "Error during the ffmpeg metadata stream "
            f"extraction: {result.stderr.strip()}"
        )
