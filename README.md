# UE Texture Tools for Console

GUI tool pack for **Unreal Engine texture modding** + **console texture swizzling** (PS4/PS5/Switch).

![Tabs](https://img.shields.io/badge/tabs-5-blue) ![Python](https://img.shields.io/badge/python-3.x-yellow) ![License](https://img.shields.io/badge/license-MIT%2FGPL--3.0-green)

## Screenshots

```
┌─ UE Texture Tools ───────────────────────────────────────────┐
│ [ Export ][ Inject ][ Swizzler ][ Check ][ Convert ]        │
│                                                              │
│  ⬆ Export Texture                                            │
│  ─────────────────────────────────────────────────────       │
│  ┌─ Input & Output ───────────────────────────────────┐     │
│  │  Uasset file or folder                             │     │
│  │  📁  Drop .uasset file or folder here    [Browse]  │     │
│  │  Output folder                                     │     │
│  │  exported                                [Browse]  │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌─ Options ──────────────────────────────────────────┐     │
│  │  UE Version  [4.26 ▼]   Export as  [dds ▼]        │     │
│  │  ☑ No mipmaps   ☑ Skip non-texture                │     │
│  └────────────────────────────────────────────────────┘     │
│  [          EXPORT          ]                                │
│                                                              │
│  ─ Output Log ───────────────────────────────────── ready ─  │
│  UE Texture Tools — PS4/PS5/Switch + UE Asset Tools         │
│    Drag & drop files or use Browse buttons                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Features

| Tab | Function |
|-----|----------|
| **Export** | Extract texture from `.uasset` → `.dds` / `.png` / `.tga` |
| **Inject** | Replace texture in `.uasset` with `.dds` / `.png` |
| **Swizzler** | Swizzle/Unswizzle DDS for **PS4 · PS5 · Nintendo Switch** |
| **Check** | Auto-detect UE version of `.uasset` |
| **Convert** | Convert texture format (DDS ↔ TGA/PNG/BMP/JPG) |

## Quick Start

### Requirements
- **Python 3.x** with tkinter (built into standard Python)
  - If missing: `pip install tkinterdnd2` (auto-installed by launcher)
- Windows 10+

### Download & Run
1. Clone or download this repo
2. Double-click **`UE Texture Tools.bat`**
3. Drag `.uasset` or `.dds` files into any drop zone (`📁`)
4. Pick your options and press the button

### Drag & Drop
Every input field supports drag-and-drop:
- Drop a **file** (`.uasset`, `.dds`, `.png`) → processes single file
- Drop a **folder** → batch processes all matching files inside

## Supported UE Versions

4.0 ~ 5.4, FF7R, Borderlands 3 (including PS5-format assets)

## Swizzler Platforms

| Platform | Algorithm | UE GOBs |
|----------|-----------|---------|
| **PS4** | Morton 8×8 micro-tiles | — |
| **PS5** | Morton 64×64 macro-tiles | — |
| **Switch** | GOBs tiling | 8 (UE games) |

## Supported Texture Formats

**Export/Inject**: DDS, TGA, HDR, BMP, JPG, PNG  
**Swizzle**: DDS only (BC1-7, uncompressed RGBA8/R8/RG8, all mipmaps)  
**Convert**: All above (BMP/JPG/PNG Windows only via texconv)

## CLI Usage (without GUI)

```batch
:: Export texture
python src/main.py path/to/file.uasset --mode=export --save_folder=out --version=4.26 --export_as=dds

:: Inject texture
python src/main.py path/to/file.uasset texture.dds --save_folder=out --version=4.26

:: Check UE version
python src/main.py path/to/file.uasset --mode=check

:: Swizzle single file
python src/console_swizzler.py unswizzle input.dds output.dds ps5

:: Swizzle batch folder
python src/console_swizzler.py batch-u folder ps5
```

## Credits

| Component | Author | License |
|-----------|--------|---------|
| **UE4-DDS-Tools** | [matyalatte](https://github.com/matyalatte/UE4-DDS-Tools) | MIT |
| **PS4/PS5/Switch Swizzle** | [Bartlomiej Duda](https://github.com/bartlomiejduda/ReverseBox) | GPL-3.0 |
| **Tuw GUI Framework** | [matyalatte](https://github.com/matyalatte/tuw) | MIT |
| **PS5 Integration + GUI** | [zerlkung](https://github.com/zerlkung) | MIT |

## License

This project combines MIT-licensed code (UE4-DDS-Tools, tkinter GUI) with GPL-3.0 licensed code (swizzling algorithms from ReverseBox).  
The combined work is distributed under **GPL-3.0**. See individual source files for details.
