# Quick Start Guide
## Xclipse 940 Extension Gap Analysis

**5-Minute Setup to Get Started**

---

## For First-Time Users

### 1. Read the Main Documentation
Start here to understand the GPU capabilities and gaps:
```bash
cat docs/xclipse940-extension-gap.md
# Or open in your favorite markdown viewer
```

**Key Sections:**
- Section 2: Vulkan extensions (what's missing, what's broken)
- Section 4: Emulator-specific issues (if you use Winlator, Dolphin, etc.)
- Section 8: Recommended configurations

### 2. Check Emulator Compatibility
**Quick Reference Table (from Section 4):**

| Emulator | Status | Key Issues | Fix |
|----------|--------|------------|-----|
| Winlator | ✅ 75% working | BC texture compression | Install ExynosTools 1.4.0 |
| Dolphin | ✅ 92% working | Depth fog bug | Use OpenGL backend for some games |
| PPSSPP | ✅ 100% working | None | Works great with wrapper |
| Yuzu/Skyline | ⚠️ 30% working | Sparse 3D textures | No fix (hardware limitation) |
| RetroArch | ✅ 88% working | VRS shader bugs | Use simple shaders |

### 3. Install GPU Wrapper (If Needed)
If you experience texture issues:

**Option A: ExynosTools v1.4.0** (recommended)
- Location: `extracted/exynostools/`
- See: `extracted/exynostools/usr/share/meta.json` for details

**Option B: Xclipse Tools v1.2.0**
- Location: `extracted/xclipse_tools/`
- See: `extracted/xclipse_tools/README.txt` for Winlator installation

---

## For Developers

### 1. Review Implementation Backlog
```bash
cat docs/IMPLEMENTATION_BACKLOG.md
```

**Priority Overview:**
- **P0 (Done):** BC1-BC7 texture decode ✅
- **P1 (Next):** BC6H HDR, VRS workaround, depth/stencil fix
- **P2:** Performance optimizations (cache, multi-threading)

### 2. Understand Architecture
```bash
cat docs/xclipse940-extension-gap.md
# Focus on:
# - Section 9: Technical deep dives (BCn formats, performance data)
# - Section 7: Known driver bugs
```

### 3. Start Implementation
Follow the 6-month sprint plan in `docs/IMPLEMENTATION_BACKLOG.md`:
- Sprint 1 (Weeks 1-2): BC6H completion
- Sprint 2 (Weeks 3-4): VRS bug workaround
- Sprint 3 (Weeks 5-6): Cache optimization

---

## For Testers / Device Owners

### 1. Install Prerequisites
```bash
# Ubuntu/Debian
sudo apt install android-tools-adb python3

# macOS
brew install android-platform-tools python3

# Windows
# Download ADB from: https://developer.android.com/tools/releases/platform-tools
# Download Python from: https://www.python.org/downloads/
```

### 2. Enable USB Debugging on Device
- Settings → About phone → Tap "Build number" 7 times
- Settings → Developer options → Enable "USB debugging"
- Connect USB cable and accept debugging prompt

### 3. Run Capability Scripts
```bash
cd scripts

# Check device connection
python3 enumerate_vulkan_capabilities.py --list-devices

# Run Vulkan enumeration
python3 enumerate_vulkan_capabilities.py --mode device --output ../research/my_vulkan_report.txt

# Run OpenGL ES enumeration
python3 enumerate_gles_capabilities.py --mode device --output ../research/my_gles_report.txt
```

### 4. Compare Results
```bash
# Compare your output to sample
diff research/my_vulkan_report.txt research/xclipse940_vulkan_sample_output.txt
```

---

## For Project Managers

### 1. Review Deliverables
```bash
cat DELIVERABLES_SUMMARY.md
```

**Key Metrics:**
- 115KB documentation across 10 files
- 254 GPU extensions documented (98 Vulkan + 156 OpenGL ES)
- 20+ game-specific issues mapped to root causes
- 5 emulators analyzed with compatibility data

### 2. Check Acceptance Criteria
```bash
cat docs/ACCEPTANCE_CRITERIA_CHECKLIST.md
```
All 4 acceptance criteria ✅ met and validated.

### 3. Review Roadmap
```bash
cat docs/IMPLEMENTATION_BACKLOG.md
# See: Sprint Planning section (6-month timeline)
```

---

## Common Tasks

### Check What's Missing on Your Device
```bash
# Run Vulkan script
cd scripts
python3 enumerate_vulkan_capabilities.py --mode device --output vulkan_check.txt

# Search for BCn support
grep -i "bc[1-7]\|dxt\|bptc\|rgtc" vulkan_check.txt

# If no results = BCn not supported (install wrapper)
```

### Get Recommended Settings for Your Emulator
```bash
# Read Section 8 of main document
grep -A 20 "8.1 Winlator" docs/xclipse940-extension-gap.md
grep -A 20 "8.2 Dolphin" docs/xclipse940-extension-gap.md
grep -A 20 "8.3 PPSSPP" docs/xclipse940-extension-gap.md
```

### Report a Bug
1. Run capability scripts (capture your device info)
2. Note affected emulator + game + symptoms
3. Check if issue is documented:
   ```bash
   grep -i "your_game_name" docs/xclipse940-extension-gap.md
   ```
4. If new issue, add to `research/` directory with device info

---

## Troubleshooting

### "adb: device not found"
```bash
# Kill and restart adb server
adb kill-server
adb start-server
adb devices

# Check USB debugging is enabled on device
# Accept "Allow USB debugging" popup on device
```

### "Python script shows no extensions"
```bash
# Verify device connection
adb shell getprop ro.product.model

# Try alternative method (manual dumpsys)
adb shell dumpsys SurfaceFlinger > surfaceflinger.txt
grep -i "GL\|vulkan" surfaceflinger.txt
```

### "My texture issues aren't documented"
1. Check main doc Section 4 for your emulator
2. Check if wrapper is installed (ExynosTools/Xclipse Tools)
3. Verify wrapper is enabled in emulator settings
4. Check driver version: `adb shell dumpsys SurfaceFlinger | grep -i driver`

---

## Document Index

| Document | Purpose | Size |
|----------|---------|------|
| **docs/xclipse940-extension-gap.md** | Main gap analysis | 26KB, 607 lines |
| **docs/IMPLEMENTATION_BACKLOG.md** | Prioritized roadmap | 13KB, 377 lines |
| **docs/ACCEPTANCE_CRITERIA_CHECKLIST.md** | Validation checklist | 15KB, 421 lines |
| **scripts/README.md** | Script usage guide | 6KB |
| **research/README.md** | Research methodology | 10KB |
| **README.md** | Project overview | 15KB, 286 lines |
| **DELIVERABLES_SUMMARY.md** | Task completion report | 18KB, 544 lines |
| **QUICK_START.md** | This file | 5KB |

---

## One-Liner Cheat Sheet

```bash
# Check device
adb devices

# Run Vulkan check
python3 scripts/enumerate_vulkan_capabilities.py --mode device --output vulkan.txt

# Run OpenGL ES check
python3 scripts/enumerate_gles_capabilities.py --mode device --output gles.txt

# Read main analysis
cat docs/xclipse940-extension-gap.md | less

# Check specific emulator
grep -A 50 "Winlator" docs/xclipse940-extension-gap.md

# View implementation priorities
head -n 100 docs/IMPLEMENTATION_BACKLOG.md

# See all deliverables
ls -lh docs/ scripts/ research/
```

---

## Next Steps After Reading

1. **Users:** Install ExynosTools 1.4.0, configure your emulator (Section 8)
2. **Developers:** Review backlog, start Sprint 1 (BC6H completion)
3. **Testers:** Run scripts, compare to sample data, report discrepancies
4. **Managers:** Review roadmap, allocate resources, track metrics

---

**Need Help?**
- Detailed script help: `scripts/README.md`
- Troubleshooting: `scripts/README.md` → Troubleshooting section
- Technical details: `docs/xclipse940-extension-gap.md` → Section 9 (Appendix)
- Bug reporting: Add file to `research/` with device info and issue description

**Project Status:** ✅ Complete - All acceptance criteria met  
**Last Updated:** 2025-01-09
