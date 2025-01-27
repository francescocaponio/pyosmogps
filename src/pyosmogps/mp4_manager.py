import struct


class MP4Manager:
    mp4_file = None
    metadata_track_index = 3

    metadata = None

    offsets = []
    sizes = []

    def __init__(self, mp4_file):
        self.mp4_file = mp4_file
        self._read_chunk_offsets_and_sizes()
        self._extract_chunks()

    def get_metadata(self):
        return self.metadata

    def save_metadata(self, output_file):
        with open(output_file, "wb") as f:
            f.write(self.metadata)
        return True

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

    def _read_chunk_offsets_and_sizes(self):
        """
        Read the chunk offsets and sizes for a specific track from the
        'co64' and 'stsz' boxes.

        """

        with open(self.mp4_file, "rb") as f:
            while True:
                box_size, box_type, start_of_box = self._read_box(f)
                if not box_size:
                    break

                print(f"Found box: {box_type}, size: {box_size}, start: {start_of_box}")

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

            print(f"Parsing moov child box: {box_type}, size: {box_size}")

            if box_type == "trak":
                track_counter += 1
                if track_counter == self.metadata_track_index:
                    trak_data = moov_data[i + header_size : i + box_size]
                    self._parse_trak_for_co64_and_stsz(trak_data)
                    break

            i += box_size

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

            print(f"Parsing trak child box: {box_type}, size: {box_size}")

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

            print(f"Parsing mdia child box: {box_type}, size: {box_size}")

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

            print(f"Parsing minf child box: {box_type}, size: {box_size}")

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

            print(f"Parsing stbl child box: {box_type}, size: {box_size}")

            if box_type == "co64":
                co64_data = stbl_data[i + header_size : i + box_size]
                self._parse_co64(co64_data)
            elif box_type == "stsz":
                stsz_data = stbl_data[i + header_size : i + box_size]
                self._parse_stsz(stsz_data)

            i += box_size

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
        print(f"Found co64 box with flags={flags_version}, and {entry_count} entries.")

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
        print(
            f"Found stsz box with flags={flags}, version={version}, "
            f"and {entry_count} entries."
        )

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
