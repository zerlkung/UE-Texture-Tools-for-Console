"""GUI wrapper for console_swizzler - handles output path auto-generation"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from console_swizzler import process_dds, process_folder

if len(sys.argv) < 4:
    print("Usage: swizzle_gui.py <mode> <input> <output_folder> [platform] [gobs]")
    sys.exit(1)

mode = sys.argv[1]      # swizzle or unswizzle
input_path = sys.argv[2]
output_dir = sys.argv[3]
platform = sys.argv[4] if len(sys.argv) > 4 else 'ps5'
gobs = int(sys.argv[5]) if len(sys.argv) > 5 else 8

is_swizzle = (mode == 'swizzle')

if not os.path.exists(input_path):
    print(f"Input not found: {input_path}")
    sys.exit(1)

os.makedirs(output_dir, exist_ok=True)

if os.path.isdir(input_path):
    # Batch mode - process all DDS files in the folder
    process_folder(input_path, output_dir, is_swizzle, platform, gobs)
else:
    # Single file mode
    base = os.path.splitext(os.path.basename(input_path))[0]
    suffix = f"_{platform}_{'swz' if is_swizzle else 'unswz'}.dds"
    output_path = os.path.join(output_dir, base + suffix)
    process_dds(input_path, output_path, is_swizzle, platform, gobs)
