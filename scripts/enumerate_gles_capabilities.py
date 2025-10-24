#!/usr/bin/env python3
"""
OpenGL ES Capability Enumeration Script for Xclipse 940 (Exynos 2400)

This script queries OpenGL ES extensions, version, and capabilities via adb-connected
Android device using various methods (dumpsys, native test app, or parsed logs).

Usage:
  # Query via adb device
  python3 enumerate_gles_capabilities.py --mode device

  # Parse from log file
  python3 enumerate_gles_capabilities.py --mode log --input gles_info.txt

  # List available devices
  python3 enumerate_gles_capabilities.py --list-devices
"""

import argparse
import json
import re
import subprocess
import sys
from typing import Dict, List, Optional, Set


class GLESCapabilityEnumerator:
    """Enumerates OpenGL ES capabilities from Android device or logs."""

    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.adb_cmd = ["adb"]
        if device_id:
            self.adb_cmd.extend(["-s", device_id])

    def check_adb_available(self) -> bool:
        """Check if adb is available and device is connected."""
        try:
            result = subprocess.run(
                self.adb_cmd + ["devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "device" in result.stdout
        except Exception as e:
            print(f"ADB check failed: {e}", file=sys.stderr)
            return False

    def list_devices(self) -> List[str]:
        """List connected Android devices."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split("\n")[1:]
            devices = []
            for line in lines:
                if "\tdevice" in line:
                    devices.append(line.split("\t")[0])
            return devices
        except Exception as e:
            print(f"Failed to list devices: {e}", file=sys.stderr)
            return []

    def query_via_dumpsys(self) -> Dict:
        """Query OpenGL ES info via dumpsys SurfaceFlinger."""
        print("Querying OpenGL ES info via dumpsys...", file=sys.stderr)
        
        data = {
            "device_info": {},
            "gl_version": None,
            "gl_vendor": None,
            "gl_renderer": None,
            "egl_version": None,
            "egl_extensions": [],
            "gl_extensions": []
        }

        # Get device info
        try:
            model = subprocess.run(
                self.adb_cmd + ["shell", "getprop ro.product.model"],
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()
            
            android_version = subprocess.run(
                self.adb_cmd + ["shell", "getprop ro.build.version.release"],
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()
            
            chipset = subprocess.run(
                self.adb_cmd + ["shell", "getprop ro.hardware.chipname"],
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()

            data["device_info"] = {
                "model": model,
                "android_version": android_version,
                "chipset": chipset or "unknown"
            }
        except Exception as e:
            print(f"Failed to get device properties: {e}", file=sys.stderr)

        # Get GPU info from SurfaceFlinger
        try:
            result = subprocess.run(
                self.adb_cmd + ["shell", "dumpsys SurfaceFlinger"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parse GL strings
                gl_version_match = re.search(r'GLES:\s*(.+)', output)
                if gl_version_match:
                    data["gl_version"] = gl_version_match.group(1).strip()
                
                gl_vendor_match = re.search(r'GL_VENDOR:\s*(.+)', output)
                if gl_vendor_match:
                    data["gl_vendor"] = gl_vendor_match.group(1).strip()
                
                gl_renderer_match = re.search(r'GL_RENDERER:\s*(.+)', output)
                if gl_renderer_match:
                    data["gl_renderer"] = gl_renderer_match.group(1).strip()
                
                # Parse GL extensions
                gl_exts_match = re.search(r'GL extensions:\s*(.+?)(?:\n\n|\Z)', output, re.DOTALL)
                if gl_exts_match:
                    ext_text = gl_exts_match.group(1)
                    extensions = [ext.strip() for ext in ext_text.split() if ext.strip()]
                    data["gl_extensions"] = extensions
                
                # Parse EGL version
                egl_version_match = re.search(r'EGL version:\s*(.+)', output)
                if egl_version_match:
                    data["egl_version"] = egl_version_match.group(1).strip()
                
                # Parse EGL extensions
                egl_exts_match = re.search(r'EGL extensions:\s*(.+?)(?:\n\n|\Z)', output, re.DOTALL)
                if egl_exts_match:
                    ext_text = egl_exts_match.group(1)
                    extensions = [ext.strip() for ext in ext_text.split() if ext.strip()]
                    data["egl_extensions"] = extensions
                    
        except Exception as e:
            print(f"dumpsys SurfaceFlinger failed: {e}", file=sys.stderr)

        return data

    def query_via_getprop(self) -> Dict:
        """Query OpenGL ES info via system properties."""
        print("Querying via getprop...", file=sys.stderr)
        
        data = {}
        
        try:
            # Get GLES version from property
            result = subprocess.run(
                self.adb_cmd + ["shell", "getprop ro.opengles.version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                version_code = int(result.stdout.strip())
                major = version_code >> 16
                minor = version_code & 0xFFFF
                data["gl_version_property"] = f"OpenGL ES {major}.{minor}"
                
        except Exception as e:
            print(f"getprop query failed: {e}", file=sys.stderr)

        return data

    def parse_log_file(self, filepath: str) -> Dict:
        """Parse OpenGL ES info from log file."""
        print(f"Parsing log file: {filepath}", file=sys.stderr)
        
        data = {
            "gl_version": None,
            "gl_vendor": None,
            "gl_renderer": None,
            "egl_version": None,
            "egl_extensions": [],
            "gl_extensions": []
        }
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Parse GL version
            gl_version_match = re.search(r'GL_VERSION:\s*(.+)', content)
            if gl_version_match:
                data["gl_version"] = gl_version_match.group(1).strip()
            
            # Parse GL vendor
            gl_vendor_match = re.search(r'GL_VENDOR:\s*(.+)', content)
            if gl_vendor_match:
                data["gl_vendor"] = gl_vendor_match.group(1).strip()
            
            # Parse GL renderer
            gl_renderer_match = re.search(r'GL_RENDERER:\s*(.+)', content)
            if gl_renderer_match:
                data["gl_renderer"] = gl_renderer_match.group(1).strip()
            
            # Parse GL extensions
            gl_exts_match = re.search(r'GL_EXTENSIONS:\s*(.+?)(?:\n\n|\Z)', content, re.DOTALL)
            if gl_exts_match:
                ext_text = gl_exts_match.group(1)
                extensions = [ext.strip() for ext in ext_text.split() if ext.strip()]
                data["gl_extensions"] = extensions
            
            # Parse EGL version
            egl_version_match = re.search(r'EGL_VERSION:\s*(.+)', content)
            if egl_version_match:
                data["egl_version"] = egl_version_match.group(1).strip()
            
            # Parse EGL extensions
            egl_exts_match = re.search(r'EGL_EXTENSIONS:\s*(.+?)(?:\n\n|\Z)', content, re.DOTALL)
            if egl_exts_match:
                ext_text = egl_exts_match.group(1)
                extensions = [ext.strip() for ext in ext_text.split() if ext.strip()]
                data["egl_extensions"] = extensions
                
        except Exception as e:
            print(f"Failed to parse log file: {e}", file=sys.stderr)
        
        return data

    def query_device_capabilities(self) -> Dict:
        """Query OpenGL ES capabilities from connected device."""
        if not self.check_adb_available():
            print("ERROR: adb not available or device not connected", file=sys.stderr)
            return {}

        # Combine results from multiple methods
        capabilities = {}
        
        # Try dumpsys first
        dumpsys_data = self.query_via_dumpsys()
        capabilities.update(dumpsys_data)
        
        # Add property data
        prop_data = self.query_via_getprop()
        capabilities.update(prop_data)

        return capabilities

    def generate_report(self, capabilities: Dict, output_file: Optional[str] = None):
        """Generate formatted report of OpenGL ES capabilities."""
        output = []
        
        output.append("=" * 80)
        output.append("OPENGL ES CAPABILITY REPORT - Exynos 2400 (Xclipse 940)")
        output.append("=" * 80)
        output.append("")

        # Device info
        if "device_info" in capabilities:
            output.append("## Device Information")
            for key, value in capabilities["device_info"].items():
                output.append(f"  {key}: {value}")
            output.append("")

        # OpenGL ES info
        output.append("## OpenGL ES Information")
        if capabilities.get("gl_version"):
            output.append(f"  Version: {capabilities['gl_version']}")
        if capabilities.get("gl_version_property"):
            output.append(f"  Version (property): {capabilities['gl_version_property']}")
        if capabilities.get("gl_vendor"):
            output.append(f"  Vendor: {capabilities['gl_vendor']}")
        if capabilities.get("gl_renderer"):
            output.append(f"  Renderer: {capabilities['gl_renderer']}")
        output.append("")

        # EGL info
        output.append("## EGL Information")
        if capabilities.get("egl_version"):
            output.append(f"  Version: {capabilities['egl_version']}")
        output.append("")

        # EGL extensions
        if capabilities.get("egl_extensions"):
            output.append(f"## EGL Extensions ({len(capabilities['egl_extensions'])})")
            for ext in sorted(capabilities["egl_extensions"]):
                output.append(f"  - {ext}")
            output.append("")

        # GL extensions
        if capabilities.get("gl_extensions"):
            output.append(f"## OpenGL ES Extensions ({len(capabilities['gl_extensions'])})")
            for ext in sorted(capabilities["gl_extensions"]):
                output.append(f"  - {ext}")
            output.append("")

        report_text = "\n".join(output)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}", file=sys.stderr)
        
        print(report_text)
        
        return report_text


def main():
    parser = argparse.ArgumentParser(
        description="Enumerate OpenGL ES capabilities for Xclipse 940 GPU"
    )
    parser.add_argument(
        "--mode",
        choices=["device", "log"],
        default="device",
        help="Query mode: device (via adb) or log (from file)"
    )
    parser.add_argument(
        "--input",
        help="Input log file (when mode=log)"
    )
    parser.add_argument(
        "--output",
        help="Output report file path"
    )
    parser.add_argument(
        "--device",
        help="Specific device serial number (for adb)"
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available adb devices"
    )
    parser.add_argument(
        "--json-output",
        help="Export raw capabilities as JSON"
    )

    args = parser.parse_args()

    enumerator = GLESCapabilityEnumerator(device_id=args.device)

    if args.list_devices:
        devices = enumerator.list_devices()
        if devices:
            print("Connected devices:")
            for device in devices:
                print(f"  - {device}")
        else:
            print("No devices found")
        return

    capabilities = {}
    
    if args.mode == "device":
        print("Querying OpenGL ES capabilities from device...", file=sys.stderr)
        capabilities = enumerator.query_device_capabilities()
    elif args.mode == "log":
        if not args.input:
            print("ERROR: --input required for log mode", file=sys.stderr)
            sys.exit(1)
        print(f"Loading capabilities from {args.input}...", file=sys.stderr)
        capabilities = enumerator.parse_log_file(args.input)

    if not capabilities:
        print("ERROR: No capabilities data retrieved", file=sys.stderr)
        sys.exit(1)

    # Generate report
    enumerator.generate_report(capabilities, output_file=args.output)

    # Export raw JSON if requested
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(capabilities, f, indent=2)
        print(f"Raw JSON saved to: {args.json_output}", file=sys.stderr)


if __name__ == "__main__":
    main()
