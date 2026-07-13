from __future__ import annotations

import argparse
import csv
import json
import struct
import sys
from pathlib import Path

from .passwords import DEFAULT_PASSWORD, EncryptionPolicy
from .bmp_codec import write_rgb565_bmp
from .wzl_container import read_wzl, set_placement, write_wzl
from .wzl_pixels import decode_frame_pixels
from .wzx_index import sync_wzx
from .wzl_builder import build_wzl, write_wzx_for_offsets


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="WzlCli")
    parser.add_argument("--password", help="资源密码；未提供时默认尝试 V8M2")
    parser.add_argument("--decrypt-input", dest="decrypt_input", action="store_true", default=True)
    parser.add_argument("--no-decrypt-input", dest="decrypt_input", action="store_false")
    parser.add_argument("--encrypt-output", dest="encrypt_output", action="store_true", default=True)
    parser.add_argument("--no-encrypt-output", dest="encrypt_output", action="store_false")
    sub = parser.add_subparsers(dest="command", required=True)
    info = sub.add_parser("info")
    info.add_argument("file", type=Path)
    placements = sub.add_parser("placements")
    placements.add_argument("file", type=Path)
    placements.add_argument("output", type=Path)
    action_map = sub.add_parser("action-map")
    action_map.add_argument("file", type=Path)
    action_map.add_argument("output", type=Path)
    raw = sub.add_parser("extract-raw")
    raw.add_argument("file", type=Path)
    raw.add_argument("output", type=Path)
    raw.add_argument("--index", type=int)
    export = sub.add_parser("export")
    export.add_argument("file", type=Path)
    export.add_argument("output", type=Path)
    export.add_argument("--all", action="store_true")
    export.add_argument("--index", type=int)
    export.add_argument("--one-based", action="store_true")
    sync_index = sub.add_parser("sync-wzx")
    sync_index.add_argument("wzx", type=Path)
    sync_index.add_argument("wzl", type=Path)
    sync_index.add_argument("output", type=Path)
    import_images = sub.add_parser("import-images")
    import_images.add_argument("directory", type=Path)
    import_images.add_argument("output_wzl", type=Path)
    import_images.add_argument("--output-wzx", type=Path)
    import_images.add_argument("--template-wzl", type=Path)
    import_images.add_argument("--empty-prefix", type=int, default=0)
    set_pos = sub.add_parser("set-placement")
    set_pos.add_argument("file", type=Path)
    set_pos.add_argument("output", type=Path)
    set_pos.add_argument("--index", type=int, required=True)
    set_pos.add_argument("--x", type=int, required=True)
    set_pos.add_argument("--y", type=int, required=True)
    set_many = sub.add_parser("set-placements")
    set_many.add_argument("file", type=Path)
    set_many.add_argument("output", type=Path)
    set_many.add_argument("placements", type=Path)
    bmp_index = sub.add_parser("index-bmp-dir")
    bmp_index.add_argument("directory", type=Path)
    bmp_index.add_argument("output", type=Path)
    correlate = sub.add_parser("correlate")
    correlate.add_argument("wzl", type=Path)
    correlate.add_argument("bmp_directory", type=Path)
    correlate.add_argument("output", type=Path)
    correlate.add_argument("--limit", type=int)
    correlate.add_argument("--record-offset", type=int, default=0, help="WZL记录号 = 导出编号 + offset，默认 0")
    correlate.add_argument("--skip-blank-bmp", action="store_true", help="跳过宽高为 1×1 的占位 BMP，并按实际图片顺序对应 WZL")
    correlate.add_argument("--wzl-start-index", type=int, default=0, help="实际图片序列对应的起始 WZL 记录号")
    args = parser.parse_args(argv)
    policy = EncryptionPolicy(
        decrypt_input=args.decrypt_input,
        encrypt_output=args.encrypt_output,
        input_password=args.password or DEFAULT_PASSWORD,
        output_password=args.password or DEFAULT_PASSWORD,
    )

    if args.command == "sync-wzx":
        sync_wzx(args.wzx, args.wzl, args.output)
        print(f"written: {args.output}")
        return 0

    if args.command == "import-images":
        images = sorted([p for p in args.directory.iterdir() if p.is_file() and p.suffix.lower() in {".bmp", ".png"}], key=lambda p: (int(p.stem) if p.stem.isdigit() else 10**18, p.name.lower()))
        offsets = build_wzl(images, args.output_wzl, template=args.template_wzl)
        if args.output_wzx:
            write_wzx_for_offsets(offsets, args.output_wzx, empty_prefix=args.empty_prefix)
        print(f"written {len(images)} image(s): {args.output_wzl}")
        return 0
    if args.command == "set-placement":
        resource = read_wzl(args.file)
        set_placement(resource, args.index, args.x, args.y)
        write_wzl(resource, args.output)
        print(f"written: {args.output}")
        return 0

    if args.command == "export":
        resource = read_wzl(args.file)
        if args.index is not None:
            selected = [frame for frame in resource.frames if frame.index == args.index]
        elif args.all:
            selected = resource.frames
        else:
            raise ValueError("export 需要 --all 或 --index")
        if args.index is not None and not selected:
            print(f"record not found: {args.index}")
            return 2
        args.output.mkdir(parents=True, exist_ok=True)
        for frame in selected:
            image = decode_frame_pixels(frame)
            number = frame.index + 1 if args.one_based else frame.index
            write_rgb565_bmp(args.output / f"{number:05d}.BMP", image)
        print(f"written {len(selected)} BMP frame(s): {args.output}")
        return 0

    if args.command == "set-placements":
        resource = read_wzl(args.file)
        payload = json.loads(args.placements.read_text(encoding="utf-8"))
        entries = payload.get("placements", payload) if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            raise ValueError("placements JSON 必须是数组，或包含 placements 数组")
        for entry in entries:
            if not isinstance(entry, dict) or not all(key in entry for key in ("index", "x", "y")):
                raise ValueError("每个坐标项必须包含 index、x、y")
            set_placement(resource, int(entry["index"]), int(entry["x"]), int(entry["y"]))
        write_wzl(resource, args.output)
        print(f"written {len(entries)} placement(s): {args.output}")
        return 0

    if args.command == "index-bmp-dir":
        files = sorted(args.directory.glob("*.bmp"), key=lambda p: p.name.lower())
        files += sorted(args.directory.glob("*.BMP"), key=lambda p: p.name.lower())
        seen: set[Path] = set()
        rows = []
        for path in files:
            if path in seen:
                continue
            seen.add(path)
            name = path.stem
            try:
                number = int(name)
            except ValueError:
                number = None
            raw = path.read_bytes()
            width = height = bpp = compression = None
            if raw[:2] == b"BM" and len(raw) >= 34:
                width, height = struct.unpack_from("<ii", raw, 18)
                bpp = struct.unpack_from("<H", raw, 28)[0]
                compression = struct.unpack_from("<I", raw, 30)[0]
            rows.append((number, path.name, width, height, bpp, compression, path.stat().st_size))
        rows.sort(key=lambda row: (row[0] is None, row[0] if row[0] is not None else row[1]))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["export_number_1_based", "filename", "width", "height", "bits_per_pixel", "compression", "file_size"])
            writer.writerows(rows)
        print(f"written {len(rows)} BMP entries: {args.output}")
        return 0

    if args.command == "correlate":
        resource = read_wzl(args.wzl)
        bmp_files = {int(path.stem): path for path in args.bmp_directory.iterdir() if path.is_file() and path.suffix.lower() == ".bmp" and path.stem.isdigit()}
        ordered_numbers = sorted(bmp_files)
        if args.skip_blank_bmp:
            filtered = []
            for number in ordered_numbers:
                raw = bmp_files[number].read_bytes()
                if len(raw) >= 26 and raw[:2] == b"BM" and struct.unpack_from("<ii", raw, 18) == (1, 1):
                    continue
                filtered.append(number)
            ordered_numbers = filtered
        limit = args.limit if args.limit is not None else len(ordered_numbers)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for sequence_index, export_number in enumerate(ordered_numbers[:limit]):
            record_index = (args.wzl_start_index + sequence_index) if args.skip_blank_bmp else (export_number + args.record_offset)
            if record_index >= len(resource.frames):
                rows.append([export_number, record_index, bmp_files[export_number].name, "missing_wzl_record"])
                continue
            frame = resource.frames[record_index]
            raw = bmp_files[export_number].read_bytes()
            width = height = bpp = compression = None
            if raw[:2] == b"BM" and len(raw) >= 34:
                width, height = struct.unpack_from("<ii", raw, 18)
                bpp = struct.unpack_from("<H", raw, 28)[0]
                compression = struct.unpack_from("<I", raw, 30)[0]
            rows.append([export_number, record_index, bmp_files[export_number].name, width, height, bpp, compression, frame.record_offset, frame.payload_offset, frame.payload_length, frame.decoded_length, frame.placement.x, frame.placement.y])
        with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["export_number_1_based", "wzl_record_index", "bmp_filename", "bmp_width", "bmp_height", "bmp_bpp", "bmp_compression", "wzl_record_offset", "wzl_payload_offset", "wzl_payload_length", "wzl_decoded_length", "placement_x_candidate", "placement_y_candidate"])
            writer.writerows(rows)
        print(f"written {len(rows)} correlations: {args.output}")
        return 0

    if args.command in {"info", "placements", "action-map", "extract-raw"}:
        resource = read_wzl(args.file)
        if args.command == "extract-raw":
            selected = resource.frames if args.index is None else [f for f in resource.frames if f.index == args.index]
            if args.index is not None and not selected:
                print(f"record not found: {args.index}")
                return 2
            args.output.mkdir(parents=True, exist_ok=True)
            for frame in selected:
                (args.output / f"{frame.index:05d}.decoded.bin").write_bytes(frame.decoded)
            print(f"written {len(selected)} decoded record(s) to: {args.output}")
            return 0
        result = {
            "file": str(resource.path),
            "format": resource.format,
            "metadata": resource.metadata,
            "default_password": DEFAULT_PASSWORD,
            "password_policy": {
                "decrypt_input": policy.decrypt_input,
                "encrypt_output": policy.encrypt_output,
                "default_password": DEFAULT_PASSWORD,
                "verification": "try default, then prompt on verification failure",
            },
            "frames": [
                {
                    "index": f.index,
                    "action_slot_candidate": f.action_slot,
                    "direction_slot_candidate": f.direction_slot,
                    "placement": {"x": f.placement.x, "y": f.placement.y} if f.placement else None,
                    "record_offset": f.record_offset,
                    "payload_offset": f.payload_offset,
                    "payload_length": f.payload_length,
                    "decoded_length": f.decoded_length,
                }
                for f in resource.frames
            ],
        }
        if args.command == "action-map":
            with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["action_slot_candidate", "direction_slot_candidate", "record_index", "placement_x", "placement_y", "payload_offset", "payload_length", "decoded_length"])
                for frame in resource.frames:
                    writer.writerow([frame.action_slot, frame.direction_slot, frame.index, frame.placement.x, frame.placement.y, frame.payload_offset, frame.payload_length, frame.decoded_length])
            print(f"written: {args.output}")
            return 0
        if args.command == "info":
            print(json.dumps({k: result[k] for k in ("file", "format", "metadata", "password_policy")}, ensure_ascii=False, indent=2))
        else:
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"written: {args.output}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
