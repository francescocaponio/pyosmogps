# PyOsmoGPS

PyOsmoGPS is a Python library designed to extract GPS data embedded in video files created by the DJI Osmo Action 4 or Osmo Action 5 cameras. It converts the GPS data into GPX files for further processing or analysis.

## Features

- Extracts GPS data from video files.
- Supports DJI Osmo Action 4 and 5 cameras.
- Converts GPS data to standard GPX format.
- Allows customization of output frequency and resampling methods.
- Implements filtering and interpolation algorithms for better accuracy.
- Provides a command-line interface for easy use.

## Disclaimer

This project is **not affiliated, sponsored, or approved by DJI**. DJI is a registered trademark of SZ DJI Technology Co., Ltd. The use of their product names is purely for descriptive purposes to indicate compatibility.

## How to Use

### Installation

#### Linux

You can install PyOsmoGPS using pip:

```bash
pip install pyosmogps
```

You will need to have ffmpeg installed on your system to extract the GPS data from the video files. You can install it using the following command:

```bash
sudo apt-get install ffmpeg
```

or using the package manager of your distribution.

#### Windows

You can install PyOsmoGPS using pip:

```bash
pip install pyosmogps
```

You will need to have ffmpeg installed on your system to extract the GPS data from the video files. You can download it from the [official website](https://ffmpeg.org/download.html) and add it to your system path.
Or you can use the [Chocolatey](https://chocolatey.org/) package manager to install it:

```bash
choco install ffmpeg
```

or winget:

```bash
winget install ffmpeg
```

Remember to restart your terminal after installing ffmpeg to make sure the changes take effect.

Moreover, on windows the shortcut `pyosmogps` is not created, so you can use the following command to run the tool:

```bash
python -m pyosmogps ...
```

### Usage

You can use PyOsmoGPS as a command-line tool or as a Docker container. The tool checks that the input video file is compatible with the DJI Osmo Action 4 or 5 cameras and that it contains GPS data, extracting it and converting it to a `.gpx` file. It can be used to create video overlays with GPS data or to analyze the GPS track.

The GPS data is stored when the camera is successfully connected to the remote controller and the GPS signal is acquired. The data is embedded in the video file and can be extracted using PyOsmoGPS.

![Osmo Remote Controller](assets/osmo-remote.png)
![Osmo Remote Controller](assets/osmo-action-4.png)

A compatible tool for the video overlay creation is [gopro-dashboard-overlay](https://github.com/time4tea/gopro-dashboard-overlay), which has a gpx input mode that can be used with the output of PyOsmoGPS.

#### Command-Line Tool

To extract GPS data from a video file and save it as a GPX file, you can use the following command:

```bash
pyosmogps extract input.mp4 output.gpx
```

This command will read the GPS data from the video file `input.mp4` and save it as a GPX file `output.gpx`.

If you want to extract GPS data from multiple video files, you can specify them as a list:

```bash
pyosmogps extract input1.mp4 input2.mp4 input3.mp4 output.gpx
```

In this case the GPS data from all the input files will be combined and saved in the output GPX file.

You can customize the output frequency and resampling method using the following options:

```bash
pyosmogps --frequency 5 --resampling-method lpf extract input.mp4 output.gpx
```

where frequency indicates the output frequency in Hz and method specifies the resampling method (`lpf` for low-pass filtering, `linear` for linear interpolation or `discard` for dropping samples). Please refer to the [Data filtering](#data-filtering) section for more information on the available filtering methods.

You may need to specify the time offset from the default timezone in qhich the data is stored in the video file. This can be done using the `--time-offset` option:

```bash
pyosmogps --timezone-offset 2 extract input.mp4 output.gpx
```

For more information on the available options, you can use the `--help` flag:

```bash
pyosmogps --help
```

#### Docker Container

Available soon!

### How it works

PyOsmoGPS reads the GPS data embedded in the video files created by the DJI Osmo Action 4 or 5 cameras. The GPS data is stored in the video file as metadata and can be extracted using PyOsmoGPS.
PyOsmoGPS reads the GPS data from the video using ffmpeg to extract the binary metadata, then it uses the protobuf library to parse the binary data and extract the GPS coordinates. The extracted GPS coordinates can be written in a GPX file, which is a standard format for GPS data that can be used with various tools and services.

#### Data filtering

It may be necessary to filter the GPS data to remove noise and improve accuracy. PyOsmoGPS provides several filtering options, including low-pass filtering and linear interpolation. The low-pass filtering method applies a low-pass filter to the GPS data to remove high-frequency noise, while the linear interpolation method fills in missing data points by interpolating between the existing points. The filtering options can be customized to achieve the desired level of accuracy.

##### I'm not a digital filter expert, let me understand what I should use:

When working with GPS data, it's important to filter the data to remove noise and improve accuracy. There are several filtering methods that can be used, depending on the type of noise in the data and the desired level of accuracy. Some common filtering methods include:

- **Low-pass filtering**: This method is useful when you have a lot of noise in your data, and you want to smooth it out. It removes high-frequency noise, but it can also introduce some lag in the data. If you have a lot of jitter in your GPS data, this method can help to reduce it.

- **Linear interpolation**: This method is useful when you have missing data points in your GPS track. It fills in the gaps by interpolating between the existing points. This can help to create a more continuous track and improve the accuracy of the data.

- **Discard**: This method is useful when you have a lot of noise in your data and you want to remove it. It simply discards the noisy data points, which can help to clean up the track. However, this method can also remove valid data points, so use it with caution.

Here is an example of the same GPS track with different filtering methods applied:

![Filter differences](assets/filter-differences.png)

This screenshot is made with the [GPX Studio](https://gpx.studio/) tool, where you can upload one or multiple GPX files and visualize and edit them on a map.

The `red` track is the original data stream without any filtering or resampling of the data (59.94 Hz data). This is used only as a comparison, but it is a heavy file and not recommended for most applications.

The other tracks are processed with pyosmogps using different filtering methods at a low rate (one every 10 seconds, or 0.1 Hz).

- The `orange` track is the **discard method**, where 1 sample every 10 is sent to the output file with the following command:

```bash
pyosmogps -t 6 -f 0.1 -r discard extract input.mp4 output.gpx
```

- The `blue` track is processed with the **linear interpolation**, and you can notice that doesn't share a point with the previous data stream, but it uses the 2 neighboring points to create a new one. It may help to reduce the noise when it is not strong. This is done with the following command:

```bash
pyosmogps -t 6 -f 0.1 -r linear extract input.mp4 output.gpx
```

- The `light blue` track is processed with the **low-pass filter**, it is a lot smoother because it uses more neighboring points to filter the data, lowering the output noise in the coordinates. As you can notice on the image, where the changes are fast, it may result less accurate than the other 2 methods. This is done with the following command:

```bash
pyosmogps -t 6 -f 0.1 -r lpf extract input.mp4 output.gpx
```

The filtering method you choose will depend on the characteristics of your data and the level of accuracy you need. You may need to experiment with different methods to find the one that works best for your application.

### Contributing

Contributions are welcome! This is a fairly new project, and there is still a lot of work to be done. If you have any ideas for new features, improvements, or bug fixes, please feel free to open an issue or submit a pull request.

Please check the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.
