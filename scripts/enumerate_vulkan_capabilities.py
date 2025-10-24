#!/usr/bin/env python3
"""
Vulkan Capability Enumeration Script for Xclipse 940 (Exynos 2400)

This script queries Vulkan instance and device extensions, features, and properties
via adb-connected Android device. It can also parse JSON manifests exported from
vulkaninfo or similar tools.

Usage:
  # Direct device query (requires adb)
  python3 enumerate_vulkan_capabilities.py --mode device

  # Parse from JSON file
  python3 enumerate_vulkan_capabilities.py --mode json --input vulkaninfo.json

  # List available devices
  python3 enumerate_vulkan_capabilities.py --list-devices
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional, Set


class VulkanCapabilityEnumerator:
    """Enumerates Vulkan capabilities from Android device or JSON manifest."""

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
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            devices = []
            for line in lines:
                if "\tdevice" in line:
                    devices.append(line.split("\t")[0])
            return devices
        except Exception as e:
            print(f"Failed to list devices: {e}", file=sys.stderr)
            return []

    def run_vulkaninfo(self) -> Optional[str]:
        """Execute vulkaninfo on the device and return JSON output."""
        print("Checking if vulkaninfo is available on device...", file=sys.stderr)
        
        # Try to find vulkaninfo binary
        result = subprocess.run(
            self.adb_cmd + ["shell", "which vulkaninfo"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("vulkaninfo not found on device. Trying alternative method...", file=sys.stderr)
            return None

        print("Running vulkaninfo --json...", file=sys.stderr)
        result = subprocess.run(
            self.adb_cmd + ["shell", "vulkaninfo --json"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return result.stdout
        else:
            print(f"vulkaninfo execution failed: {result.stderr}", file=sys.stderr)
            return None

    def get_device_properties_via_dumpsys(self) -> Dict:
        """Get GPU and Vulkan information via dumpsys (fallback method)."""
        print("Attempting to gather Vulkan info via dumpsys...", file=sys.stderr)
        
        data = {
            "device_info": {},
            "vulkan_version": None,
            "extensions": [],
            "features": {}
        }

        # Get device model and Android version
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

        # Try dumpsys SurfaceFlinger for GPU info
        try:
            result = subprocess.run(
                self.adb_cmd + ["shell", "dumpsys SurfaceFlinger | grep -i 'GL\\|vulkan\\|gpu'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout:
                data["surfaceflinger_gpu_info"] = result.stdout.strip()
        except Exception as e:
            print(f"dumpsys SurfaceFlinger failed: {e}", file=sys.stderr)

        return data

    def parse_vulkaninfo_json(self, json_data: str) -> Dict:
        """Parse vulkaninfo JSON output."""
        try:
            data = json.loads(json_data)
            return self.normalize_vulkaninfo_data(data)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}", file=sys.stderr)
            return {}

    def normalize_vulkaninfo_data(self, raw_data: Dict) -> Dict:
        """Normalize vulkaninfo data to consistent format."""
        normalized = {
            "instance_extensions": [],
            "device_extensions": [],
            "features": {},
            "properties": {},
            "formats": [],
            "queue_families": []
        }

        # Extract instance extensions
        if "VkInstance" in raw_data:
            inst_exts = raw_data["VkInstance"].get("extensions", [])
            normalized["instance_extensions"] = [
                {"name": ext.get("extensionName", ""), "version": ext.get("specVersion", 0)}
                for ext in inst_exts
            ]

        # Extract device-specific data (first physical device)
        devices = raw_data.get("physicalDevices", [])
        if devices:
            device = devices[0]
            
            # Device extensions
            dev_exts = device.get("extensions", [])
            normalized["device_extensions"] = [
                {"name": ext.get("extensionName", ""), "version": ext.get("specVersion", 0)}
                for ext in dev_exts
            ]
            
            # Properties
            props = device.get("properties", {})
            normalized["properties"] = {
                "deviceName": props.get("deviceName", ""),
                "deviceType": props.get("deviceType", ""),
                "driverVersion": props.get("driverVersion", 0),
                "apiVersion": props.get("apiVersion", 0),
                "vendorID": props.get("vendorID", 0),
                "deviceID": props.get("deviceID", 0)
            }
            
            # Features
            normalized["features"] = device.get("features", {})
            
            # Formats
            normalized["formats"] = device.get("formats", [])
            
            # Queue families
            normalized["queue_families"] = device.get("queueFamilies", [])

        return normalized

    def query_device_capabilities(self) -> Dict:
        """Query Vulkan capabilities from connected device."""
        if not self.check_adb_available():
            print("ERROR: adb not available or device not connected", file=sys.stderr)
            return {}

        # Try vulkaninfo first
        vulkaninfo_output = self.run_vulkaninfo()
        if vulkaninfo_output:
            return self.parse_vulkaninfo_json(vulkaninfo_output)
        
        # Fallback to dumpsys
        print("Using fallback method (dumpsys)...", file=sys.stderr)
        return self.get_device_properties_via_dumpsys()

    def query_from_json_file(self, filepath: str) -> Dict:
        """Load and parse Vulkan capabilities from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return self.normalize_vulkaninfo_data(data)
        except Exception as e:
            print(f"Failed to load JSON file: {e}", file=sys.stderr)
            return {}

    def generate_report(self, capabilities: Dict, output_file: Optional[str] = None):
        """Generate formatted report of Vulkan capabilities."""
        output = []
        
        output.append("=" * 80)
        output.append("VULKAN CAPABILITY REPORT - Exynos 2400 (Xclipse 940)")
        output.append("=" * 80)
        output.append("")

        # Device info
        if "device_info" in capabilities:
            output.append("## Device Information")
            for key, value in capabilities["device_info"].items():
                output.append(f"  {key}: {value}")
            output.append("")

        # Properties
        if "properties" in capabilities and capabilities["properties"]:
            output.append("## Device Properties")
            props = capabilities["properties"]
            for key, value in props.items():
                if key == "apiVersion":
                    major = (value >> 22) & 0x7F
                    minor = (value >> 12) & 0x3FF
                    patch = value & 0xFFF
                    output.append(f"  {key}: {major}.{minor}.{patch} (0x{value:08x})")
                elif key == "driverVersion":
                    output.append(f"  {key}: 0x{value:08x}")
                else:
                    output.append(f"  {key}: {value}")
            output.append("")

        # Instance extensions
        if "instance_extensions" in capabilities:
            output.append(f"## Instance Extensions ({len(capabilities['instance_extensions'])})")
            for ext in sorted(capabilities["instance_extensions"], key=lambda x: x["name"]):
                output.append(f"  - {ext['name']} (v{ext['version']})")
            output.append("")

        # Device extensions
        if "device_extensions" in capabilities:
            output.append(f"## Device Extensions ({len(capabilities['device_extensions'])})")
            for ext in sorted(capabilities["device_extensions"], key=lambda x: x["name"]):
                output.append(f"  - {ext['name']} (v{ext['version']})")
            output.append("")

        # Features
        if "features" in capabilities and capabilities["features"]:
            output.append("## Device Features")
            features = capabilities["features"]
            if isinstance(features, dict):
                enabled_features = [k for k, v in features.items() if v]
                disabled_features = [k for k, v in features.items() if not v]
                
                output.append(f"### Enabled Features ({len(enabled_features)})")
                for feat in sorted(enabled_features):
                    output.append(f"  + {feat}")
                output.append("")
                
                output.append(f"### Disabled Features ({len(disabled_features)})")
                for feat in sorted(disabled_features):
                    output.append(f"  - {feat}")
                output.append("")

        # Surface flinger info (fallback)
        if "surfaceflinger_gpu_info" in capabilities:
            output.append("## GPU Info (from dumpsys SurfaceFlinger)")
            output.append(capabilities["surfaceflinger_gpu_info"])
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
        description="Enumerate Vulkan capabilities for Xclipse 940 GPU"
    )
    parser.add_argument(
        "--mode",
        choices=["device", "json"],
        default="device",
        help="Query mode: device (via adb) or json (from file)"
    )
    parser.add_argument(
        "--input",
        help="Input JSON file (when mode=json)"
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

    enumerator = VulkanCapabilityEnumerator(device_id=args.device)

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
        print("Querying Vulkan capabilities from device...", file=sys.stderr)
        capabilities = enumerator.query_device_capabilities()
    elif args.mode == "json":
        if not args.input:
            print("ERROR: --input required for json mode", file=sys.stderr)
            sys.exit(1)
        print(f"Loading capabilities from {args.input}...", file=sys.stderr)
        capabilities = enumerator.query_from_json_file(args.input)

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
