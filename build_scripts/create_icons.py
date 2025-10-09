#!/usr/bin/env python3
"""
Create app icons from logo PNG for Mac (.icns) and Windows (.ico)
"""

import sys
from pathlib import Path
from PIL import Image

project_root = Path(__file__).parent.parent
logo_path = project_root / "assets" / "buena-logo.png"
output_dir = project_root / "assets"

# Icon sizes needed
ICON_SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]

def create_ico(logo_path, output_path):
    """Create Windows .ico file"""
    print(f"Creating Windows icon: {output_path}")

    img = Image.open(logo_path)

    # Create square canvas
    size = max(img.size)
    square = Image.new('RGBA', (size, size), (255, 255, 255, 0))

    # Paste image centered
    offset = ((size - img.size[0]) // 2, (size - img.size[1]) // 2)
    square.paste(img, offset)

    # Create multiple sizes for .ico
    icon_sizes = [(s, s) for s in [16, 32, 48, 64, 128, 256]]

    # Save as .ico with multiple sizes
    square.save(output_path, format='ICO', sizes=icon_sizes)
    print(f"✓ Created: {output_path}")

def create_iconset_for_mac(logo_path, output_dir):
    """Create Mac .icns file using iconutil"""
    print(f"Creating macOS icon")

    img = Image.open(logo_path)

    # Create square canvas
    size = max(img.size)
    square = Image.new('RGBA', (size, size), (255, 255, 255, 0))

    # Paste image centered
    offset = ((size - img.size[0]) // 2, (size - img.size[1]) // 2)
    square.paste(img, offset)

    # Create iconset directory
    iconset_dir = output_dir / "buena-logo.iconset"
    iconset_dir.mkdir(exist_ok=True)

    # Generate all required sizes
    sizes = [16, 32, 128, 256, 512]
    for size in sizes:
        # Normal resolution
        resized = square.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / f"icon_{size}x{size}.png")

        # Retina resolution (@2x)
        if size <= 512:
            retina_size = size * 2
            resized_retina = square.resize((retina_size, retina_size), Image.Resampling.LANCZOS)
            resized_retina.save(iconset_dir / f"icon_{size}x{size}@2x.png")

    print(f"✓ Created iconset: {iconset_dir}")

    # Convert to .icns using iconutil (Mac only)
    import subprocess
    icns_path = output_dir / "buena-logo.icns"

    try:
        result = subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Created: {icns_path}")
        return icns_path
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating .icns: {e}")
        print(f"  You may need to run this on macOS")
        return None
    except FileNotFoundError:
        print(f"✗ iconutil not found (only available on macOS)")
        return None

def main():
    print("=" * 60)
    print("BuenaLive Icon Creator")
    print("=" * 60)

    if not logo_path.exists():
        print(f"✗ Logo not found: {logo_path}")
        return 1

    print(f"\nSource: {logo_path}")
    print(f"Output: {output_dir}")

    # Create Windows icon
    ico_path = output_dir / "buena-logo.ico"
    create_ico(logo_path, ico_path)

    # Create Mac icon
    if sys.platform == "darwin":
        icns_path = create_iconset_for_mac(logo_path, output_dir)
    else:
        print("\n⚠ Skipping .icns creation (requires macOS)")

    print("\n" + "=" * 60)
    print("Icon creation complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print(f"  - {output_dir / 'buena-logo.ico'} (Windows)")
    if sys.platform == "darwin":
        print(f"  - {output_dir / 'buena-logo.icns'} (macOS)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
