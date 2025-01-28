import struct


class MP4Manager:
    mp4_file = None
    video_trak_index = 1
    metadata_track_index = 3

    metadata = None
    video_width = None
    video_height = None
    video_frame_rate = None
    video_duration = None

    video_sample_count = None
    video_sample_delta = None

    offsets = []
    sizes = []

    def __init__(self, mp4_file):
        self.mp4_file = mp4_file
        self._parse_video_file_info()
        self.video_frame_rate = self.video_sample_count / self.video_duration
        self._extract_chunks()

    def get_metadata(self):
        return self.metadata

    def save_metadata(self, output_file):
        with open(output_file, "wb") as f:
            f.write(self.metadata)
        return True

    def get_video_width(self):
        return self.video_width

    def get_video_height(self):
        return self.video_height

    def get_video_frame_rate(self):
        return self.video_frame_rate

    def get_video_duration(self):
        return self.video_duration

    def _read_box(self, fp):
        """
        Read a box header and return its details.

        :param fp: File pointer.
        :return: Tuple containing box size, box type, and start position.
        """
        start_of_box = fp.tell()
        header = fp.read(8)
        if len(header) < 8:
            return None, None, None

        box_size, box_type = struct.unpack(">I4s", header)
        box_type = box_type.decode("utf-8")

        if box_size == 1:  # Extended size case
            box_size = struct.unpack(">Q", fp.read(8))[0]

        return box_size, box_type, start_of_box

    def _parse_video_file_info(self):
        """
        Read the chunk offsets and sizes for a specific track from the
        'co64' and 'stsz' boxes.

        """

        with open(self.mp4_file, "rb") as f:
            while True:
                box_size, box_type, start_of_box = self._read_box(f)
                if not box_size:
                    break
                if box_type == "moov":
                    moov_data = f.read(box_size - (f.tell() - start_of_box))
                    self._parse_moov_for_co64_and_stsz(moov_data)
                    break
                f.seek(start_of_box + box_size)

        return True

    def _parse_moov_for_co64_and_stsz(self, moov_data):
        """
        Parse the 'moov' box to extract chunk offsets and sizes for
        the specified track.

        """
        track_counter = 0

        i = 0
        while i < len(moov_data):
            box_size, box_type = struct.unpack(">I4s", moov_data[i : i + 8])
            box_type = box_type.decode("utf-8")
            if box_size == 1:  # Extended size case
                box_size = struct.unpack(">Q", moov_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "trak":
                track_counter += 1
                if track_counter == self.video_trak_index:
                    trak_data = moov_data[i + header_size : i + box_size]
                    self._parse_trak_for_tkhd(trak_data)
                if track_counter == self.metadata_track_index:
                    trak_data = moov_data[i + header_size : i + box_size]
                    self._parse_trak_for_co64_and_stsz(trak_data)
            if box_type == "mvhd":
                mvhd_data = moov_data[i + header_size : i + box_size]
                self._parse_mvhd(mvhd_data)
            i += box_size
        return True

    def _parse_mvhd(self, data):
        """
        Parse the 'mvhd' box for video duration.
        """
        version = struct.unpack(">B", data[0:1])[0]
        if version == 1:
            duration = struct.unpack(">Q", data[20:28])[0]
        else:
            duration = struct.unpack(">I", data[16:20])[0]
        time_scale = struct.unpack(">I", data[12:16])[0]
        duration = duration / time_scale
        self.video_duration = duration
        return

    def _parse_trak_for_tkhd(self, trak_data):
        """
        Parse the 'tkhd' box to extract video resolution.
        """
        i = 0
        while i < len(trak_data):
            box_size, box_type = struct.unpack(">I4s", trak_data[i : i + 8])
            box_type = box_type.decode("utf-8")

            if box_size == 1:  # Extended size case
                box_size = struct.unpack(">Q", trak_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "tkhd":
                mdia_data = trak_data[i + header_size : i + box_size]
                self._parse_tkhd(mdia_data)
            if box_type == "mdia":
                mdia_data = trak_data[i + header_size : i + box_size]
                self._parse_mdia_for_stts(mdia_data)
            i += box_size
        return True

    def _parse_tkhd(self, data):
        width = struct.unpack(">I", data[76:80])[0] / 65536
        height = struct.unpack(">I", data[80:84])[0] / 65536
        self.video_width = width
        self.video_height = height
        return True

    def _parse_mdia_for_stts(self, mdia_data):
        """
        Parse the 'mdia' box to find the 'minf' box for video duration.
        """
        i = 0
        while i < len(mdia_data):
            box_size, box_type = struct.unpack(">I4s", mdia_data[i : i + 8])
            box_type = box_type.decode("utf-8")
            if box_size == 1:
                box_size = struct.unpack(">Q", mdia_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "minf":
                minf_data = mdia_data[i + header_size : i + box_size]
                self._parse_minf_for_stts(minf_data)
                break
            i += box_size
        return True

    def _parse_minf_for_stts(self, minf_data):
        """
        Parse the 'minf' box to find the 'stbl' box for video duration.
        """
        i = 0
        while i < len(minf_data):
            box_size, box_type = struct.unpack(">I4s", minf_data[i : i + 8])
            box_type = box_type.decode("utf-8")
            if box_size == 1:
                box_size = struct.unpack(">Q", minf_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "stbl":
                stbl_data = minf_data[i + header_size : i + box_size]
                self._parse_stbl_for_stts(stbl_data)
                break
            i += box_size
        return True

    def _parse_stbl_for_stts(self, stbl_data):
        """
        Parse the 'stbl' box to find the 'stts' box for video duration.
        """
        i = 0
        while i < len(stbl_data):
            box_size, box_type = struct.unpack(">I4s", stbl_data[i : i + 8])
            box_type = box_type.decode("utf-8")
            if box_size == 1:
                box_size = struct.unpack(">Q", stbl_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "stts":
                stts_data = stbl_data[i + header_size : i + box_size]
                self._parse_stts(stts_data)
                break
            i += box_size
        return True

    def _parse_stts(self, data):
        """
        Parse the 'stts' box for video duration.
        """
        sample_count = struct.unpack(">I", data[8:12])[0]
        sample_delta = struct.unpack(">I", data[12:16])[0]
        self.video_sample_count = sample_count
        self.video_sample_delta = sample_delta
        return True

    def _parse_trak_for_co64_and_stsz(self, trak_data):
        """
        Parse the 'trak' box to find the 'co64' and 'stsz' boxes
        for chunk offsets and sizes.

        :param trak_data: Binary data of the 'trak' box.
        """

        i = 0
        while i < len(trak_data):
            box_size, box_type = struct.unpack(">I4s", trak_data[i : i + 8])
            box_type = box_type.decode("utf-8")
            if box_size == 1:  # Extended size case
                box_size = struct.unpack(">Q", trak_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "mdia":
                mdia_data = trak_data[i + header_size : i + box_size]
                self._parse_mdia_for_co64_and_stsz(mdia_data)
                break
            i += box_size
        return True

    def _parse_mdia_for_co64_and_stsz(self, mdia_data):
        """
        Parse the 'mdia' box to find the 'co64' and 'stsz' boxes for
        chunk offsets and sizes.

        :param mdia_data: Binary data of the 'mdia' box.
        """
        i = 0
        while i < len(mdia_data):
            box_size, box_type = struct.unpack(">I4s", mdia_data[i : i + 8])
            box_type = box_type.decode("utf-8")
            if box_size == 1:  # Extended size case
                box_size = struct.unpack(">Q", mdia_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "minf":
                minf_data = mdia_data[i + header_size : i + box_size]
                self._parse_minf_for_co64_and_stsz(minf_data)
                break
            i += box_size
        return True

    def _parse_minf_for_co64_and_stsz(self, minf_data):
        """
        Parse the 'minf' box to find the 'co64' and 'stsz' boxes
        for chunk offsets and sizes.

        :param minf_data: Binary data of the 'minf' box.
        """
        i = 0
        while i < len(minf_data):
            box_size, box_type = struct.unpack(">I4s", minf_data[i : i + 8])
            box_type = box_type.decode("utf-8")

            if box_size == 1:  # Extended size case
                box_size = struct.unpack(">Q", minf_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "stbl":
                stbl_data = minf_data[i + header_size : i + box_size]
                self._parse_stbl_for_co64_and_stsz(stbl_data)
                break
            i += box_size
        return True

    def _parse_stbl_for_co64_and_stsz(self, stbl_data):
        """
        Parse the 'stbl' box to find the 'co64' and 'stsz' boxes
        for chunk offsets and sizes.

        :param stbl_data: Binary data of the 'stbl' box.
        """

        i = 0
        while i < len(stbl_data):
            box_size, box_type = struct.unpack(">I4s", stbl_data[i : i + 8])
            box_type = box_type.decode("utf-8")

            if box_size == 1:  # Extended size case
                box_size = struct.unpack(">Q", stbl_data[i + 8 : i + 16])[0]
                header_size = 16
            else:
                header_size = 8
            if box_type == "co64":
                co64_data = stbl_data[i + header_size : i + box_size]
                self._parse_co64(co64_data)
            if box_type == "stco":
                stco_data = stbl_data[i + header_size : i + box_size]
                self._parse_stco(stco_data)
            elif box_type == "stsz":
                stsz_data = stbl_data[i + header_size : i + box_size]
                self._parse_stsz(stsz_data)
            i += box_size

        return True

    def _parse_stco(self, data):
        """
        Parse the 'stco' box for chunk offsets.

        :param data: Binary data of the 'stco' box.
        :return: List of chunk offsets.
        """
        offsets = []

        # Ensure there are at least 12 bytes for the header
        if len(data) < 12:
            raise ValueError(
                f"Insufficient data for 'stco' header. Got {len(data)} "
                "bytes, expected at least 12."
            )

        # Extract flags/version (4 byte) e entry_count (4 byte)
        flags_version, entry_count = struct.unpack(">II", data[:8])

        # Calculate required length and validate
        required_length = 8 + entry_count * 4
        if len(data) < required_length:
            raise ValueError(
                f"Incomplete 'stco' data. Expected {required_length} "
                f"bytes, got {len(data)}."
            )

        # Extract chunk offsets (4 bytes each)
        for i in range(entry_count):
            start = 8 + i * 4
            end = start + 4
            offset = struct.unpack(">I", data[start:end])[0]
            offsets.append(offset)

        self.offsets = offsets
        return True

    def _parse_co64(self, data):
        """
        Parse the 'co64' box for chunk offsets.

        :param data: Binary data of the 'co64' box.
        :return: List of chunk offsets.
        """
        offsets = []

        # Ensure there are at least 12 bytes for the header
        if len(data) < 12:
            raise ValueError(
                f"Insufficient data for 'co64' header. Got {len(data)} "
                "bytes, expected at least 12."
            )

        # Extract flags/version (4 byte) e entry_count (4 byte)
        flags_version, entry_count = struct.unpack(">II", data[:8])

        # Calculate required length and validate
        required_length = 8 + entry_count * 8
        if len(data) < required_length:
            raise ValueError(
                f"Incomplete 'co64' data. Expected {required_length} "
                f"bytes, got {len(data)}."
            )

        # Extract chunk offsets (8 bytes each)
        for i in range(entry_count):
            start = 8 + i * 8
            end = start + 8
            offset = struct.unpack(">Q", data[start:end])[0]
            offsets.append(offset)

        self.offsets = offsets
        return True

    def _parse_stsz(self, data):
        """
        Parse the 'stsz' box for chunk offsets.

        :param data: Binary data of the 'stsz' box.
        :return: List of chunk sizes.
        """
        sizes = []

        # Ensure there are at least 12 bytes for the header
        if len(data) < 12:
            raise ValueError(
                f"Insufficient data for 'stsz' header. Got {len(data)} "
                "bytes, expected at least 12."
            )

        # Extract flags/version (4 byte) e entry_count (4 byte)

        flags, version, entry_count = struct.unpack(">III", data[:12])

        # Calculate required length and validate
        required_length = 4 + entry_count * 4
        if len(data) < required_length:
            raise ValueError(
                f"Incomplete 'stsz' data. Expected {required_length} "
                f"bytes, got {len(data)}."
            )

        # Extract chunk sizes (4 bytes each)
        for i in range(entry_count):
            start = 12 + i * 4
            end = start + 4
            size = struct.unpack(">I", data[start:end])[0]
            sizes.append(size)
        self.sizes = sizes
        return True

    def _extract_chunks(self):
        """
        Extract chunks from the 'mdat' box and join them into a single file.
        """
        with open(self.mp4_file, "rb") as f:
            for i, offset in enumerate(self.offsets):
                f.seek(offset)
                chunk_data = f.read(self.sizes[i])
                self._append_metadata(chunk_data)
        return True

    def _append_metadata(self, chunk_data):
        """
        Append metadata to the extracted chunk data.

        :param chunk_data: Binary data of the extracted chunk.
        """
        if self.metadata:
            chunk_data += self.metadata
        else:
            self.metadata = chunk_data

        return True
