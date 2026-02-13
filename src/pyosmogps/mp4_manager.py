import datetime
import struct
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional, List, Tuple, Union



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

    def __init__(self, mp4_file, extract_metadata=True):
        self.mp4_file = mp4_file
        self._parse_video_file_info()
        self.video_frame_rate = self.video_sample_count / self.video_duration
        if extract_metadata:
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
        if self.metadata is not None:
            self.metadata += chunk_data
        else:
            self.metadata = chunk_data

        return True


    """
    Inject mdta keys into an MP4:
      moov/udta/meta (hdlr=mdta) + keys + ilst

    Supports:
      - com.apple.quicktime.location.ISO6709 (required)
      - com.apple.quicktime.location.accuracy.horizontal (optional)
      - com.apple.quicktime.make / model / software / creationdate (optional)

    Safety:
      - Only supports files where 'moov' is AFTER 'mdat' (non-faststart),
        because we change 'moov' size and would otherwise need to rewrite chunk offsets.
    """

    # ---------- Public API ----------

    def write_udta_mdta(
        self,
        output_path: Union[str, Path],
        lat: float,
        lon: float,
        alt_m: Optional[float] = None,
        accuracy_horizontal_m: Optional[float] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        software: Optional[str] = None,
        creationdate: Optional[str] = None,
    ) -> None:
        """
        Create output file with injected Apple mdta metadata under moov/udta.

        Args:
          input_path/output_path: file paths
          lat/lon/alt_m: GPS in decimal degrees and meters
          accuracy_horizontal_m: meters; written as 6-decimal string like iPhone
          make/model/software/creationdate: optional; if provided, written as mdta keys.
            creationdate accepts:
              - 2025-12-13T16:01:00+0100
              - 2025-12-13T16:01:00+01:00
              - 2025:12:13 16:01:00+01:00   (ExifTool-like)
        """
        input_path = Path(self.mp4_file)
        output_path = Path(output_path)

        data = input_path.read_bytes()

        moov = self._find_top(data, b"moov")
        mdat = self._find_top(data, b"mdat")
        if not moov or not mdat:
            raise RuntimeError("moov/mdat not found")

        moov_pos, moov_size, moov_head = moov
        mdat_pos, _, _ = mdat

        if moov_pos < mdat_pos:
            raise RuntimeError(
                "faststart detected (moov before mdat). Not supported by this writer; "
                "would require rewriting stco/co64 chunk offsets."
            )

        moov_start = moov_pos + moov_head
        moov_end = moov_pos + moov_size
        moov_children = list(self._iter_boxes(data, moov_start, moov_end))

        # Build ISO6709 string (Apple-like)
        iso = self._iso6709_string(lat, lon, alt_m)

        # Build ordered keys/values similar to iPhone output
        keys_and_values: List[Tuple[str, str]] = []
        if accuracy_horizontal_m is not None:
            keys_and_values.append(
                ("com.apple.quicktime.location.accuracy.horizontal", f"{accuracy_horizontal_m:.6f}")
            )
        keys_and_values.append(("com.apple.quicktime.location.ISO6709", iso))

        if make:
            keys_and_values.append(("com.apple.quicktime.make", make))
        if model:
            keys_and_values.append(("com.apple.quicktime.model", model))
        if software:
            keys_and_values.append(("com.apple.quicktime.software", software))
        if creationdate:
            keys_and_values.append(("com.apple.quicktime.creationdate", self._normalize_creationdate(creationdate)))

        mdta_meta = self._build_mdta_meta(keys_and_values)

        # Rebuild moov children:
        # - remove any moov/meta that is mdta
        # - extract udta (if present) to modify it
        rebuilt_children = bytearray()
        udta_blob = None

        for pos, size, typ, head in moov_children:
            blob = data[pos:pos + size]
            if typ == b"meta" and self._is_mdta_meta(data, pos, size, head):
                continue
            if typ == b"udta":
                udta_blob = blob
                continue
            rebuilt_children += blob

        new_udta = self._upsert_mdta_meta_under_udta(udta_blob, mdta_meta)
        rebuilt_children += new_udta

        # Rebuild moov box with updated size
        new_moov_content = bytes(rebuilt_children)
        new_size32 = 8 + len(new_moov_content)
        if moov_head == 8 and new_size32 < (1 << 32):
            new_moov = self._p32(new_size32) + b"moov" + new_moov_content
        else:
            new_size64 = 16 + len(new_moov_content)
            new_moov = self._p32(1) + b"moov" + self._p64(new_size64) + new_moov_content

        out = data[:moov_pos] + new_moov + data[moov_pos + moov_size:]
        output_path.write_bytes(out)

    # ---------- Internal: ISO-BMFF helpers ----------

    def _p32(self, x: int) -> bytes:
        return struct.pack(">I", x)

    def _p64(self, x: int) -> bytes:
        return struct.pack(">Q", x)

    def _u32(self, b: bytes, o: int = 0) -> int:
        return struct.unpack_from(">I", b, o)[0]

    def _u64(self, b: bytes, o: int = 0) -> int:
        return struct.unpack_from(">Q", b, o)[0]

    def _make_box(self, t: bytes, payload: bytes) -> bytes:
        size32 = 8 + len(payload)
        if size32 < (1 << 32):
            return self._p32(size32) + t + payload
        size64 = 16 + len(payload)
        return self._p32(1) + t + self._p64(size64) + payload

    def _iter_boxes(self, data: bytes, start: int, end: int):
        pos = start
        while pos + 8 <= end:
            size = self._u32(data, pos)
            typ = data[pos + 4:pos + 8]
            head = 8
            if size == 1:
                if pos + 16 > end:
                    return
                size = self._u64(data, pos + 8)
                head = 16
            elif size == 0:
                size = end - pos
            if size < head or pos + size > end:
                return
            yield pos, size, typ, head
            pos += size

    def _find_top(self, data: bytes, typ: bytes):
        for pos, size, t, head in self._iter_boxes(data, 0, len(data)):
            if t == typ:
                return pos, size, head
        return None

    # ---------- Internal: mdta meta building ----------

    def _build_mdta_meta(self, keys_and_values: List[Tuple[str, str]]) -> bytes:
        # meta is FullBox: version/flags first
        meta_full = b"\x00\x00\x00\x00"

        # hdlr fullbox: version/flags + predef + handler + reserved + name
        hdlr_payload = (
            b"\x00\x00\x00\x00" +
            b"\x00\x00\x00\x00" +
            b"mdta" +
            b"\x00" * 12 +
            b"\x00"
        )
        hdlr = self._make_box(b"hdlr", hdlr_payload)

        # keys box
        keys_payload = b"\x00\x00\x00\x00" + self._p32(len(keys_and_values))
        for k, _ in keys_and_values:
            kb = k.encode("utf-8")
            keys_payload += self._p32(8 + len(kb)) + b"mdta" + kb
        keys_box = self._make_box(b"keys", keys_payload)

        def data_utf8(s: str) -> bytes:
            # data payload: type_set(1 => UTF-8 string) + locale(0) + bytes
            return self._make_box(b"data", self._p32(1) + self._p32(0) + s.encode("utf-8"))

        # ilst: items are numbered 1..N as 4-byte big-endian "type"
        ilst_payload = b""
        for idx, (_, v) in enumerate(keys_and_values, start=1):
            ilst_payload += self._make_box(idx.to_bytes(4, "big", signed=False), data_utf8(v))
        ilst_box = self._make_box(b"ilst", ilst_payload)

        return self._make_box(b"meta", meta_full + hdlr + keys_box + ilst_box)

    def _is_mdta_meta(self, data: bytes, meta_pos: int, meta_size: int, meta_head: int) -> bool:
        start = meta_pos + meta_head
        end = meta_pos + meta_size
        for pos, size, typ, head in self._iter_boxes(data, start, end):
            if typ == b"hdlr":
                payload = data[pos + head:pos + size]
                # hdlr: version/flags(4) + predef(4) + handler(4)
                if len(payload) >= 12 and payload[8:12] == b"mdta":
                    return True
        return False

    def _upsert_mdta_meta_under_udta(self, udta_blob: Optional[bytes], mdta_meta: bytes) -> bytes:
        """
        Ensure udta contains exactly one mdta meta:
          - if udta missing: create it
          - if udta present: remove existing udta/meta that is mdta, then append ours
        """
        if udta_blob is None:
            return self._make_box(b"udta", mdta_meta)

        size = self._u32(udta_blob, 0)
        head = 8
        if size == 1:
            size = self._u64(udta_blob, 8)
            head = 16
        udta_payload = udta_blob[head:head + (size - head)]

        cleaned = bytearray()
        for cpos, csize, ctyp, chead in self._iter_boxes(udta_payload, 0, len(udta_payload)):
            cblob = udta_payload[cpos:cpos + csize]
            if ctyp == b"meta":
                if self._is_mdta_meta(udta_payload, cpos, csize, chead):
                    continue
            cleaned += cblob

        return self._make_box(b"udta", bytes(cleaned) + mdta_meta)

    # ---------- Internal: formatting helpers ----------

    def _iso6709_string(
        self,
        lat: float,
        lon: float,
        alt_m: Optional[float],
        lat_dec: int = 4,
        lon_dec: int = 4,
        alt_dec: int = 3,
    ) -> str:
        def fmt(v: float, w: int, dec: int) -> str:
            sign = "+" if v >= 0 else "-"
            av = Decimal(str(abs(v))).quantize(Decimal(10) ** (-dec), rounding=ROUND_HALF_UP)
            deg = int(av)
            frac = av - Decimal(deg)
            frac_i = int((frac * (10 ** dec)).to_integral_value(rounding=ROUND_HALF_UP))
            if frac_i == 10 ** dec:
                deg += 1
                frac_i = 0
            return f"{sign}{deg:0{w}d}.{frac_i:0{dec}d}"

        lat_s = fmt(lat, 2, lat_dec)
        lon_s = fmt(lon, 3, lon_dec)

        if alt_m is None:
            return f"{lat_s}{lon_s}/"

        alt = Decimal(str(alt_m)).quantize(Decimal(10) ** (-alt_dec), rounding=ROUND_HALF_UP)
        alt_s = f"{alt:+f}"
        if "." not in alt_s:
            alt_s += "." + "0" * alt_dec
        else:
            a, b = alt_s.split(".", 1)
            alt_s = a + "." + b.ljust(alt_dec, "0")[:alt_dec]

        return f"{lat_s}{lon_s}{alt_s}/"

    def _normalize_creationdate(self, date) -> str:
        """
        Normalize to: YYYY-MM-DDTHH:MM:SS+HHMM
        """
        if type(date) == datetime.datetime:
            return date.strftime("%Y-%m-%dT%H:%M:%S%z")

        s = date.strip()

        # ExifTool-like: YYYY:MM:DD HH:MM:SS±HH:MM
        m = re.match(r"^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2}):(\d{2})([+-]\d{2}):?(\d{2})$", s)
        if m:
            y, mo, d, hh, mm, ss, tzh, tzm = m.groups()
            return f"{y}-{mo}-{d}T{hh}:{mm}:{ss}{tzh}{tzm}"

        # ISO-like: YYYY-MM-DDTHH:MM:SS±HH:MM or ±HHMM
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{2}):?(\d{2})$", s)
        if m:
            y, mo, d, hh, mm, ss, tzh, tzm = m.groups()
            return f"{y}-{mo}-{d}T{hh}:{mm}:{ss}{tzh}{tzm}"

        raise ValueError("Unsupported creationdate format")
