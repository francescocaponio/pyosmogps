from datetime import timedelta

import numpy as np
from scipy.signal import butter, filtfilt


def discard_resample_gps_data(global_gps_info, input_frequency, output_frequency):
    """
    Resample the GPS data by discarding samples.

    :param global_gps_info: List of dicts containing GPS data.
    :param input_frequency: Original frequency of the GPS data (Hz).
    :param output_frequency: Desired frequency of the GPS data (Hz).
    :return: Resampled list of dicts.
    """
    if output_frequency > input_frequency:
        raise ValueError("Output frequency cannot be higher than input frequency.")

    # Calculate the sampling step
    step = int(input_frequency / output_frequency)
    if step < 1:
        raise ValueError("Invalid step size. Check input and output frequencies.")

    # Subsample the data
    resampled_data = global_gps_info[::step]
    return resampled_data


def lpf_resample_gps_data(global_gps_info, input_frame_rate, output_frequency):
    """
    Resample the GPS data using a low pass filter method.

    :param global_gps_info: List of dicts containing GPS data.
    :param input_frame_rate: Original frame rate of the GPS data (Hz).
    :param output_frequency: Desired frequency of the GPS data (Hz).
    :return: Resampled list of dicts.
    """

    # Calculate cutoff frequency
    cutoff_frequency = output_frequency / 4.0

    # Design the Butterworth low-pass filter
    nyquist = 0.5 * input_frame_rate
    normal_cutoff = cutoff_frequency / nyquist
    b, a = butter(4, normal_cutoff, btype="low", analog=False)

    # Apply the filter to each field
    resampled_data = []

    original_timestamps = [entry["timeinfo"] for entry in global_gps_info]
    total_duration = (original_timestamps[-1] - original_timestamps[0]).total_seconds()
    num_samples = int(total_duration * output_frequency)
    new_timestamps = [
        original_timestamps[0] + timedelta(seconds=i / output_frequency)
        for i in range(num_samples)
    ]

    original_timestamps_seconds = np.array(
        [(t - original_timestamps[0]).total_seconds() for t in original_timestamps]
    )

    for new_time in new_timestamps:
        new_entry = {"timeinfo": new_time}

        for key in global_gps_info[0].keys():
            if key == "timeinfo":
                continue

            # Extract values for the current key
            values = np.array([entry[key] for entry in global_gps_info])

            # Apply the low-pass filter
            filtered_values = filtfilt(b, a, values)

            # Interpolate the filtered data to match the new timestamps
            new_value = np.interp(
                (new_time - original_timestamps[0]).total_seconds(),
                original_timestamps_seconds,
                filtered_values,
            )

            new_entry[key] = new_value

        resampled_data.append(new_entry)

    return resampled_data


def linear_resample_gps_data(global_gps_info, input_frame_rate, output_frequency):
    """
    Resample the GPS data using a linear interpolation method.

    :param global_gps_info: List of dicts containing GPS data.
    :param input_frame_rate: Original frame rate of the GPS data (Hz).
    :param output_frequency: Desired frequency of the GPS data (Hz).
    :return: Resampled list of dicts.
    """

    # Calculate total duration and the new sample interval
    total_duration = (
        global_gps_info[-1]["timeinfo"] - global_gps_info[0]["timeinfo"]
    ).total_seconds()
    num_samples = int(total_duration * output_frequency)
    new_timestamps = [
        global_gps_info[0]["timeinfo"] + timedelta(seconds=i / output_frequency)
        for i in range(num_samples)
    ]

    resampled_data = []

    # Extract original timestamps and values
    original_timestamps = [entry["timeinfo"] for entry in global_gps_info]
    original_timestamps_seconds = np.array(
        [(t - original_timestamps[0]).total_seconds() for t in original_timestamps]
    )

    # Interpolate each field
    for new_time in new_timestamps:
        new_entry = {"timeinfo": new_time}

        for key in global_gps_info[0].keys():
            if key == "timeinfo":
                continue

            # Extract values for the current key
            values = np.array([entry[key] for entry in global_gps_info])

            # Interpolate linearly
            new_value = np.interp(
                (new_time - original_timestamps[0]).total_seconds(),
                original_timestamps_seconds,
                values,
            )

            new_entry[key] = new_value

        resampled_data.append(new_entry)

    return resampled_data


def resample_gps_data(
    global_gps_info, input_frame_rate, output_frequency, resampling_method
):

    if resampling_method == "linear":
        resampled_data = linear_resample_gps_data(
            global_gps_info, input_frame_rate, output_frequency
        )
    elif resampling_method == "lpf":
        resampled_data = lpf_resample_gps_data(
            global_gps_info, input_frame_rate, output_frequency
        )
    elif resampling_method == "discard":
        resampled_data = discard_resample_gps_data(
            global_gps_info, input_frame_rate, output_frequency
        )

    return resampled_data
