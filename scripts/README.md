# Xclipse 940 GPU Capability Enumeration Scripts

This directory contains Python scripts for querying and analyzing Vulkan and OpenGL ES capabilities on Android devices with the Exynos 2400 (Xclipse 940) GPU.

## Prerequisites

### System Requirements
- Python 3.7 or later
- ADB (Android Debug Bridge) installed and in PATH
- Android device with USB debugging enabled
- (Optional) Android NDK for advanced analysis

### Android Device Setup

1. **Enable Developer Options:**
   - Go to Settings → About phone
   - Tap "Build number" 7 times
   - Developer options will appear in Settings

2. **Enable USB Debugging:**
   - Settings → Developer options → USB debugging (enable)

3. **Connect Device:**
   ```bash
   # Connect via USB cable
   adb devices
   # You should see your device listed
   ```

### Installing ADB

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install android-tools-adb android-tools-fastboot
```

**macOS (via Homebrew):**
```bash
brew install android-platform-tools
```

**Windows:**
- Download platform-tools from https://developer.android.com/tools/releases/platform-tools
- Extract and add to PATH

## Scripts

### 1. enumerate_vulkan_capabilities.py

Queries Vulkan instance/device extensions, features, and properties from an Android device.

**Usage:**

```bash
# Query from connected device
python3 enumerate_vulkan_capabilities.py --mode device --output ../research/vulkan_report.txt

# List available devices
python3 enumerate_vulkan_capabilities.py --list-devices

# Query specific device (if multiple connected)
python3 enumerate_vulkan_capabilities.py --mode device --device YOUR_DEVICE_ID --output report.txt

# Parse from JSON file (if you have vulkaninfo output)
python3 enumerate_vulkan_capabilities.py --mode json --input vulkaninfo.json --output report.txt

# Export raw JSON for further analysis
python3 enumerate_vulkan_capabilities.py --mode device --json-output raw_capabilities.json
```

**Output Format:**
- Human-readable text report with:
  - Device information (model, Android version, chipset)
  - Device properties (Vulkan version, driver version, vendor ID)
  - Instance extensions (with version numbers)
  - Device extensions (with version numbers)
  - Enabled/disabled features

### 2. enumerate_gles_capabilities.py

Queries OpenGL ES and EGL extensions, version info from an Android device.

**Usage:**

```bash
# Query from connected device
python3 enumerate_gles_capabilities.py --mode device --output ../research/gles_report.txt

# List available devices
python3 enumerate_gles_capabilities.py --list-devices

# Query specific device
python3 enumerate_gles_capabilities.py --mode device --device YOUR_DEVICE_ID --output report.txt

# Parse from log file
python3 enumerate_gles_capabilities.py --mode log --input gles_dump.txt --output report.txt

# Export raw JSON
python3 enumerate_gles_capabilities.py --mode device --json-output raw_gles.json
```

**Output Format:**
- Human-readable text report with:
  - Device information
  - OpenGL ES version, vendor, renderer
  - EGL version
  - EGL extensions list
  - OpenGL ES extensions list

## Advanced: Using Android NDK vulkaninfo

For more detailed Vulkan information, you can use the official `vulkaninfo` tool from the Android NDK.

### Installation

```bash
# Download Android NDK (example for Linux)
wget https://dl.google.com/android/repository/android-ndk-r26d-linux.zip
unzip android-ndk-r26d-linux.zip

# Push vulkaninfo to device
adb push android-ndk-r26d/toolchains/llvm/prebuilt/linux-x86_64/lib64/vulkaninfo /data/local/tmp/
adb shell chmod +x /data/local/tmp/vulkaninfo
```

### Usage

```bash
# Run vulkaninfo on device and save output
adb shell /data/local/tmp/vulkaninfo > ../research/vulkaninfo_full.txt

# Get JSON output (for parsing)
adb shell /data/local/tmp/vulkaninfo --json > ../research/vulkaninfo.json

# Parse with our script
python3 enumerate_vulkan_capabilities.py --mode json --input ../research/vulkaninfo.json --output ../research/vulkan_parsed.txt
```

## Collecting OpenGL ES Info Manually

If the automated script doesn't work, you can manually collect OpenGL ES info:

```bash
# Dump SurfaceFlinger info
adb shell dumpsys SurfaceFlinger > ../research/surfaceflinger_dump.txt

# Get OpenGL ES version from system properties
adb shell getprop ro.opengles.version

# Look for GPU info in SurfaceFlinger dump
grep -E "GLES|GL_VENDOR|GL_RENDERER|GL_VERSION|GL extensions|EGL" ../research/surfaceflinger_dump.txt
```

## Troubleshooting

### "adb: device not found"
- Check USB cable connection
- Verify USB debugging is enabled
- Try `adb kill-server` then `adb start-server`
- Check device authorization popup (tap "Allow")

### "vulkaninfo: command not found"
- The device may not have vulkaninfo installed
- Use our Python script fallback method (it uses `dumpsys`)
- Or push vulkaninfo binary from Android NDK (see above)

### "dumpsys: permission denied"
- Some devices restrict dumpsys access
- Try running with `adb root` (requires rooted device)
- Or use Android Studio Device File Explorer to pull GPU info

### Script shows no extensions
- The device may not be properly connected
- Try restarting adb: `adb kill-server && adb start-server`
- Check if device is in MTP/PTP mode (not charge-only)

## Sample Outputs

Pre-generated sample outputs for Xclipse 940 are available in the `research/` directory:
- `xclipse940_vulkan_sample_output.txt` - Typical Vulkan capabilities
- `xclipse940_gles_sample_output.txt` - Typical OpenGL ES capabilities

These can be used as reference when comparing your device's output.

## Contributing

If you encounter issues or have improvements:
1. Check existing GitHub issues
2. Collect diagnostic info:
   ```bash
   adb devices -l
   adb shell getprop | grep -i "model\|version\|chipset"
   ```
3. Run scripts with verbose output and capture errors

## Related Documentation

- Main gap analysis: `../docs/xclipse940-extension-gap.md`
- Research outputs: `../research/`
- Project root: `../`

## License

These scripts are part of the Xclipse 940 GPU analysis project. See project root for license information.
