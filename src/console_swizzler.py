"""
Console Texture Swizzler v0.5.0
Swizzle/unswizzle DDS textures for PS4, PS5, and Nintendo Switch.

Based on ReverseBox swizzling algorithms by Bartlomiej Duda (GPL-3.0)
https://github.com/bartlomiejduda/ReverseBox

Usage:
    python console_swizzler.py swizzle  input.dds output.dds [ps4|ps5|switch]
    python console_swizzler.py unswizzle input.dds output.dds [ps4|ps5|switch]
    python console_swizzler.py batch-s folder [ps4|ps5|switch]
    python console_swizzler.py batch-u folder [ps4|ps5|switch]
"""
import sys
import os
import struct
import glob

__version__ = "0.5.0"

# ========== Morton Index (from ReverseBox) ==========

def calculate_morton_index(t, input_width, input_height):
    num1 = num2 = 1
    num3 = num4 = 0
    img_width, img_height = input_width, input_height
    while img_width > 1 or img_height > 1:
        if img_width > 1:
            num3 += num2 * (t & 1)
            t >>= 1
            num2 *= 2
            img_width >>= 1
        if img_height > 1:
            num4 += num1 * (t & 1)
            t >>= 1
            num1 *= 2
            img_height >>= 1
    return num4 * input_width + num3


# ========== PS4 Swizzling ==========

def _convert_morton_ps4(image_data, img_width, img_height, block_width,
                        block_height, block_data_size, swizzle_flag):
    converted_data = bytearray(len(image_data))
    source_index = 0
    img_height //= block_height
    img_width //= block_width

    for y in range((img_height + 7) // 8):
        for x in range((img_width + 7) // 8):
            for t in range(64):
                morton_index = calculate_morton_index(t, 8, 8)
                data_y = morton_index // 8
                data_x = morton_index % 8
                if x * 8 + data_x < img_width and y * 8 + data_y < img_height:
                    destination_index = block_data_size * ((y * 8 + data_y) * img_width + x * 8 + data_x)
                    if not swizzle_flag:
                        converted_data[destination_index: destination_index + block_data_size] = image_data[source_index: source_index + block_data_size]
                    else:
                        converted_data[source_index: source_index + block_data_size] = image_data[destination_index: destination_index + block_data_size]
                    source_index += block_data_size
    return bytes(converted_data)


def unswizzle_ps4(image_data, img_width, img_height, block_width=4, block_height=4, block_data_size=16):
    return _convert_morton_ps4(image_data, img_width, img_height, block_width, block_height, block_data_size, False)


def swizzle_ps4(image_data, img_width, img_height, block_width=4, block_height=4, block_data_size=16):
    return _convert_morton_ps4(image_data, img_width, img_height, block_width, block_height, block_data_size, True)


# ========== PS5 Swizzling ==========

def _get_block_value(block_data_size):
    if block_data_size == 4: return 4
    elif block_data_size == 8: return 2
    else: return 1


def _convert_morton_ps5(image_data, img_width, img_height, block_width,
                        block_height, block_data_size, swizzle_flag):
    converted_data = bytearray(len(image_data))
    source_index = 0
    img_height //= block_height
    img_width //= block_width

    if block_width == 1 and block_height == 1:
        for y in range((img_height + 127) // 128):
            for x in range((img_width + 127) // 128):
                for t in range(512):
                    morton_index = calculate_morton_index(t, 32, 16)
                    data_x = morton_index % 32
                    data_y = morton_index // 32
                    for i in range(32):
                        local_x = x * 128 + data_x * 4 + i % 4
                        local_y = y * 128 + (data_y * 8 + i // 4)
                        if local_x < img_width and local_y < img_height:
                            destination_index = block_data_size * (local_y * img_width + local_x)
                            if not swizzle_flag:
                                converted_data[destination_index: destination_index + block_data_size] = image_data[source_index: source_index + block_data_size]
                            else:
                                converted_data[source_index: source_index + block_data_size] = image_data[destination_index: destination_index + block_data_size]
                            source_index += block_data_size
    else:
        block_value = _get_block_value(block_data_size)
        for y in range((img_height + 63) // 64):
            for x in range((img_width + 63) // 64):
                for t in range(256 // block_value):
                    morton_index = calculate_morton_index(t, 16, 16 // block_value)
                    data_x = morton_index // 16
                    data_y = morton_index % 16
                    for i in range(16):
                        for j in range(block_value):
                            local_x = x * 64 + (data_x * 4 + i // 4) * block_value + j
                            local_y = y * 64 + data_y * 4 + i % 4
                            if local_x < img_width and local_y < img_height:
                                destination_index = block_data_size * (local_y * img_width + local_x)
                                if not swizzle_flag:
                                    converted_data[destination_index: destination_index + block_data_size] = image_data[source_index: source_index + block_data_size]
                                else:
                                    converted_data[source_index: source_index + block_data_size] = image_data[destination_index: destination_index + block_data_size]
                                source_index += block_data_size
    return bytes(converted_data)


def unswizzle_ps5(image_data, img_width, img_height, block_width=4, block_height=4, block_data_size=16):
    return _convert_morton_ps5(image_data, img_width, img_height, block_width, block_height, block_data_size, False)


def swizzle_ps5(image_data, img_width, img_height, block_width=4, block_height=4, block_data_size=16):
    return _convert_morton_ps5(image_data, img_width, img_height, block_width, block_height, block_data_size, True)


# ========== Nintendo Switch Swizzling ==========

def _convert_switch(image_data, img_width, img_height, bytes_per_block,
                    gobs_height, width_pad, height_pad, swizzle_flag):
    converted_data = bytearray(len(image_data))
    # Pad dimensions to alignment
    if img_width % width_pad or img_height % height_pad:
        width_show, height_show = img_width, img_height
        img_width = width_real = ((img_width + width_pad - 1) // width_pad) * width_pad
        img_height = height_real = ((img_height + height_pad - 1) // height_pad) * height_pad
    else:
        width_show = width_real = img_width
        height_show = height_real = img_height
    image_width_in_gobs = img_width * bytes_per_block // 64

    for Y in range(img_height):
        for X in range(img_width):
            Z = Y * img_width + X
            gob_address = (0 + (Y // (8 * gobs_height)) * 512 * gobs_height * image_width_in_gobs +
                           (X * bytes_per_block // 64) * 512 * gobs_height +
                           (Y % (8 * gobs_height) // 8) * 512)
            Xb = X * bytes_per_block
            address = (gob_address + ((Xb % 64) // 32) * 256 + ((Y % 8) // 2) * 64 +
                       ((Xb % 32) // 16) * 32 + (Y % 2) * 16 + (Xb % 16))
            if not swizzle_flag:
                converted_data[Z * bytes_per_block:(Z + 1) * bytes_per_block] = image_data[address:address + bytes_per_block]
            else:
                converted_data[address:address + bytes_per_block] = image_data[Z * bytes_per_block:(Z + 1) * bytes_per_block]

    # Crop back if padded
    if width_show != width_real or height_show != height_real:
        crop = bytearray(width_show * height_show * bytes_per_block)
        for Y in range(height_show):
            offset_in = Y * width_real * bytes_per_block
            offset_out = Y * width_show * bytes_per_block
            if not swizzle_flag:
                crop[offset_out:offset_out + width_show * bytes_per_block] = converted_data[offset_in:offset_in + width_show * bytes_per_block]
            else:
                crop[offset_in:offset_in + width_show * bytes_per_block] = converted_data[offset_out:offset_out + width_show * bytes_per_block]
        converted_data = crop
    return bytes(converted_data)


def unswizzle_switch(image_data, img_width, img_height,
                     bytes_per_block=4, gobs_height=8, width_pad=8, height_pad=8):
    return _convert_switch(image_data, img_width, img_height, bytes_per_block, gobs_height, width_pad, height_pad, False)


def swizzle_switch(image_data, img_width, img_height,
                   bytes_per_block=4, gobs_height=8, width_pad=8, height_pad=8):
    return _convert_switch(image_data, img_width, img_height, bytes_per_block, gobs_height, width_pad, height_pad, True)


# ========== DDS Format Info ==========

DXGI_FORMAT = {
    71:  ("BC1_UNORM",          4, 4, 8),
    72:  ("BC1_UNORM_SRGB",     4, 4, 8),
    74:  ("BC2_UNORM",          4, 4, 16),
    75:  ("BC2_UNORM_SRGB",     4, 4, 16),
    77:  ("BC3_UNORM",          4, 4, 16),
    78:  ("BC3_UNORM_SRGB",     4, 4, 16),
    80:  ("BC4_UNORM",          4, 4, 8),
    81:  ("BC4_SNORM",          4, 4, 8),
    83:  ("BC5_UNORM",          4, 4, 16),
    84:  ("BC5_SNORM",          4, 4, 16),
    95:  ("BC6H_UF16",          4, 4, 16),
    96:  ("BC6H_SF16",          4, 4, 16),
    98:  ("BC7_UNORM",          4, 4, 16),
    99:  ("BC7_UNORM_SRGB",     4, 4, 16),
    61:  ("R8_UNORM",           1, 1, 1),
    49:  ("R16_UNORM",          1, 1, 2),
    28:  ("R8G8_UNORM",         1, 1, 2),
    87:  ("B8G8R8A8_UNORM",     1, 1, 4),
    10:  ("R16G16B16A16_UNORM", 1, 1, 8),
    2:   ("R32G32B32A32_FLOAT", 1, 1, 16),
}

FOURCC_FORMATS = {
    b'DXT1': (71, 4, 4, 8),
    b'DXT2': (74, 4, 4, 16),
    b'DXT3': (74, 4, 4, 16),
    b'DXT4': (77, 4, 4, 16),
    b'DXT5': (77, 4, 4, 16),
    b'ATI1': (80, 4, 4, 8),
    b'BC4U': (80, 4, 4, 8),
    b'BC4S': (81, 4, 4, 8),
    b'ATI2': (83, 4, 4, 16),
    b'BC5U': (83, 4, 4, 16),
    b'BC5S': (84, 4, 4, 16),
    b'DX10': None,
}

DDPF_FOURCC      = 0x4
DDSD_MIPMAPCOUNT = 0x20000


def parse_dds_header(data):
    if data[:4] != b'DDS ':
        raise ValueError("Not a valid DDS file")

    h = {}
    h['height'] = struct.unpack_from('<I', data, 12)[0]
    h['width'] = struct.unpack_from('<I', data, 16)[0]
    h['depth'] = struct.unpack_from('<I', data, 24)[0]
    h['mipmap_count'] = struct.unpack_from('<I', data, 28)[0] or 1
    flags = struct.unpack_from('<I', data, 8)[0]
    h['has_mipmaps'] = bool(flags & DDSD_MIPMAPCOUNT)

    pf_flags = struct.unpack_from('<I', data, 80)[0]
    fourcc = data[84:88]

    h['block_w'] = 1
    h['block_h'] = 1
    h['block_size'] = 1

    if pf_flags & DDPF_FOURCC:
        if fourcc in FOURCC_FORMATS:
            fmt_info = FOURCC_FORMATS[fourcc]
            if fmt_info is None:
                fmt_info = _parse_dx10_header(data)
            if fmt_info:
                dxgi_fmt = fmt_info[0]
                format_entry = DXGI_FORMAT.get(dxgi_fmt)
                if format_entry:
                    h['format_name'] = format_entry[0]
                    h['block_w'] = format_entry[1]
                    h['block_h'] = format_entry[2]
                    h['block_size'] = format_entry[3]
                else:
                    h['format_name'] = f"DXGI:{dxgi_fmt}"
            else:
                h['format_name'] = "DX10_UNKNOWN"
        else:
            h['format_name'] = f"FOURCC:{fourcc.decode('ascii', errors='replace')}"
    else:
        bpp = struct.unpack_from('<I', data, 88)[0] // 8
        h['format_name'] = f"{bpp*8}bit"
        h['block_size'] = bpp

    return h


def _parse_dx10_header(data):
    if len(data) < 148:
        return None
    dxgi_format = struct.unpack_from('<I', data, 128)[0]
    if dxgi_format in DXGI_FORMAT:
        return (dxgi_format,) + DXGI_FORMAT[dxgi_format][1:]
    return None


def get_mip_dims(width, height, mipmap_count, block_w, block_h):
    mip_dims = []
    w, h = width, height
    for _ in range(mipmap_count):
        bw = max(1, (w + block_w - 1) // block_w)
        bh = max(1, (h + block_h - 1) // block_h)
        mip_dims.append((w, h, bw, bh))
        w = max(1, w // 2)
        h = max(1, h // 2)
    return mip_dims


def process_dds(input_path, output_path, is_swizzle, platform, switch_gobs=8):
    print(f"  Processing: {os.path.basename(input_path)}")

    with open(input_path, 'rb') as f:
        data = f.read()

    header = parse_dds_header(data)

    # Calculate actual header size (128 for standard, 148 with DX10 extension)
    pf_flags = struct.unpack_from('<I', data, 80)[0]
    has_dx10 = (pf_flags & DDPF_FOURCC) and data[84:88] == b'DX10'
    header_size = 148 if has_dx10 else 128
    pixel_data = data[header_size:]

    block_w, block_h = header['block_w'], header['block_h']
    block_size = header['block_size']
    width, height = header['width'], header['height']
    mip_count = header['mipmap_count']

    print(f"    Format: {header['format_name']}, {width}x{height}, {mip_count} mip(s), "
          f"block={block_w}x{block_h}, {block_size}B, platform={platform}")

    mip_dims = get_mip_dims(width, height, mip_count, block_w, block_h)

    # Select swizzle function
    if platform == 'ps4':
        fn = swizzle_ps4 if is_swizzle else unswizzle_ps4
    elif platform == 'ps5':
        fn = swizzle_ps5 if is_swizzle else unswizzle_ps5
    else:  # switch
        if is_swizzle:
            def fn(d, w, h, bw, bh, bs):
                return swizzle_switch(d, w, h, bytes_per_block=bs, gobs_height=switch_gobs)
        else:
            def fn(d, w, h, bw, bh, bs):
                return unswizzle_switch(d, w, h, bytes_per_block=bs, gobs_height=switch_gobs)

    # Process each mip
    processed_data = bytearray()
    offset = 0
    for idx, (w, h, bw, bh) in enumerate(mip_dims):
        mip_bytes = bw * bh * block_size
        if offset + mip_bytes > len(pixel_data):
            break
        mip_raw = pixel_data[offset:offset + mip_bytes]
        offset += mip_bytes

        try:
            mip_processed = fn(mip_raw, w, h, block_w, block_h, block_size)
        except Exception as e:
            print(f"    WARNING: Mip {idx} failed ({e}), copying raw")
            mip_processed = mip_raw

        processed_data.extend(mip_processed)

    output = data[:header_size] + bytes(processed_data)
    with open(output_path, 'wb') as f:
        f.write(output)

    return True


def process_folder(folder, output_folder, is_swizzle, platform, switch_gobs=8):
    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    dds_files = glob.glob(os.path.join(folder, '*.dds'))
    dds_files += glob.glob(os.path.join(folder, '*.DDS'))
    dds_files = sorted(dds_files)

    if not dds_files:
        print(f"No DDS files found in: {folder}")
        return

    action = "Swizzle" if is_swizzle else "Unswizzle"
    print(f"{action} {len(dds_files)} file(s) [{platform.upper()}]\n")

    success = 0
    for f in dds_files:
        base = os.path.splitext(os.path.basename(f))[0]
        suffix = f".{platform}_{'swz' if is_swizzle else 'unswz'}.dds"
        out_name = base + suffix
        out_path = os.path.join(output_folder or folder, out_name)

        try:
            process_dds(f, out_path, is_swizzle, platform, switch_gobs)
            success += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nDone: {success}/{len(dds_files)} succeeded")


# ========== CLI ==========

HELP = f"""
Console Texture Swizzler v{__version__}
PS4 / PS5 / Nintendo Switch DDS texture swizzler

Usage:
    python console_swizzler.py swizzle  input.dds output.dds [ps4|ps5|switch] [gobs]
    python console_swizzler.py unswizzle input.dds output.dds [ps4|ps5|switch] [gobs]
    python console_swizzler.py batch-s folder [ps4|ps5|switch] [gobs]
    python console_swizzler.py batch-u folder [ps4|ps5|switch] [gobs]

Platforms:
    ps4     - PlayStation 4 (Morton tiling, 8x8 micro-tiles)
    ps5     - PlayStation 5 (Morton tiling, 64x64 macro-tiles) [default]
    switch  - Nintendo Switch (GOBs tiling, UE games use gobs=8)

Examples:
    python console_swizzler.py unswizzle tiled.dds linear.dds ps5
    python console_swizzler.py batch-u folder ps4
    python console_swizzler.py unswizzle tiled.dds linear.dds switch 8

Credits:
    PS4/PS5/Switch algorithms: Bartlomiej Duda (ReverseBox, GPL-3.0)
    https://github.com/bartlomiejduda/ReverseBox
"""


def main():
    if len(sys.argv) < 2:
        print(HELP)
        return

    cmd = sys.argv[1].lower()

    if cmd in ('swizzle', 'unswizzle'):
        if len(sys.argv) < 4:
            print("Usage: console_swizzler.py swizzle|unswizzle <input.dds> <output.dds> [ps4|ps5|switch] [gobs]")
            return
        platform = sys.argv[4].lower() if len(sys.argv) > 4 else 'ps5'
        gobs = int(sys.argv[5]) if len(sys.argv) > 5 else 8
        if platform not in ('ps4', 'ps5', 'switch'):
            print(f"Unknown platform: {platform}. Use ps4, ps5, or switch.")
            return
        is_swizzle = (cmd == 'swizzle')
        process_dds(sys.argv[2], sys.argv[3], is_swizzle, platform, gobs)
        action = "swizzled" if is_swizzle else "unswizzled"
        print(f"  {action} [{platform.upper()}]: {sys.argv[3]}")

    elif cmd in ('batch-s', 'batch-u'):
        if len(sys.argv) < 3:
            print("Usage: console_swizzler.py batch-s|batch-u <folder> [ps4|ps5|switch] [gobs]")
            return
        platform = sys.argv[3].lower() if len(sys.argv) > 3 else 'ps5'
        gobs = int(sys.argv[4]) if len(sys.argv) > 4 else 8
        if platform not in ('ps4', 'ps5', 'switch'):
            print(f"Unknown platform: {platform}. Use ps4, ps5, or switch.")
            return
        is_swizzle = (cmd == 'batch-s')
        output_folder = f"{sys.argv[2]}_{platform}_{'swizzled' if is_swizzle else 'unswizzled'}"
        process_folder(sys.argv[2], output_folder, is_swizzle, platform, gobs)

    else:
        print(f"Unknown command: {cmd}")
        print(HELP)


if __name__ == '__main__':
    main()
