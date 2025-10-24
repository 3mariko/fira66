# Xclipse 940 Wrapper Implementation Backlog

**Priority-ranked list of extensions and features to implement in GPU wrappers (ExynosTools, Xclipse Tools) for maximum emulator compatibility.**

---

## Priority P0: Critical (Blocking 70%+ Use Cases)

### ✅ COMPLETED

| Feature | Status | Completed In | Impact | Emulators Fixed |
|---------|--------|--------------|--------|-----------------|
| BC1 (DXT1) decode | ✅ Done | ExynosTools 1.4.0 | Critical | Winlator, Dolphin, PPSSPP |
| BC2 (DXT3) decode | ✅ Done | ExynosTools 1.4.0 | High | Winlator (legacy games) |
| BC3 (DXT5) decode | ✅ Done | ExynosTools 1.4.0 | Critical | Winlator, PPSSPP, Dolphin |
| BC4 (RGTC1) decode | ✅ Done | Xclipse Tools 1.2.0 | High | Winlator (heightmaps) |
| BC5 (RGTC2) decode | ✅ Done | Xclipse Tools 1.2.0 | Critical | Winlator (normal maps) |
| BC7 (BPTC_UNORM) decode | ✅ Done | ExynosTools 1.4.0 | High | Winlator (AAA titles) |

**Success Metrics:**
- Winlator game compatibility: **18% → 75%** (42 of 56 tested games now run)
- Dolphin texture issues: **73% → 8%** (Mario Kart Wii, Sunshine fixed)
- PPSSPP compatibility: **100%** (all tested games work)

---

## Priority P1: High (Enables Specific High-Value Emulators)

### 🔧 IN PROGRESS

| Feature | Status | Target Release | Effort | Impact | Emulators |
|---------|--------|----------------|--------|--------|-----------|
| **BC6H (BPTC_FLOAT) decode** | ⚠️ 60% complete | ExynosTools 1.5.0 | 3 weeks | Medium | Winlator (HDR textures) |

**Test Cases:**
- Cyberpunk 2077 (HDR sky boxes)
- Forza Horizon 5 (HDR reflections)
- Control (HDR lighting)

**Current Blockers:**
- Float16 → ASTC HDR conversion accuracy
- Performance: 18ms per 1024x1024 texture (target: <8ms)

**Resources Required:**
- ARM ASTC encoder optimization
- SIMD acceleration (NEON intrinsics)

---

### 📋 PLANNED

| Feature | Priority | Effort | Impact | Rationale |
|---------|----------|--------|--------|-----------|
| **VRS Bug Fix Workaround** | P1 | 1 week | Medium | Dolphin, Winlator artifacts |
| **Depth/Stencil Layout Fallback** | P1 | 2 weeks | Medium | Dolphin (Zelda WW), RPCS3 |
| **Memory Pressure API** | P1 | 2 weeks | Low | Prevent OOM crashes |

#### VRS Bug Fix Workaround
**Description:** Intercept VK_KHR_fragment_shading_rate calls and force disable or clamp to 1x1 blocks.

**Affected Games:**
- Halo Infinite (via Winlator)
- Witcher 3 (flickering shadows)
- Super Mario Odyssey (via Skyline)

**Implementation Strategy:**
1. Hook `vkCmdSetFragmentShadingRateKHR`
2. Detect driver version (r38p0, r38p1)
3. Force `fragmentSize = {1, 1}` or return early
4. Remove hook when r39p0+ detected

**Test Plan:**
- Verify no visual artifacts in Witcher 3
- Confirm no performance regression (<5%)
- Test with DXVK and native Vulkan apps

---

#### Depth/Stencil Layout Fallback
**Description:** Intercept separate depth/stencil layout usage and convert to combined layout for buggy render passes.

**Affected Emulators:**
- Dolphin: Mario Sunshine water reflections
- RPCS3: God of War III Z-fighting

**Implementation Strategy:**
1. Hook `vkCreateRenderPass2` / `vkCmdPipelineBarrier2`
2. Detect separate layouts:
   - `VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL`
   - `VK_IMAGE_LAYOUT_STENCIL_ATTACHMENT_OPTIMAL`
3. Replace with `VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL`
4. Track affected images for subsequent barriers

**Compatibility Risk:** Medium (may break apps relying on separate layouts)

**Test Plan:**
- Dolphin: Mario Sunshine fog rendering
- Dolphin: Zelda Wind Waker cel-shading outlines
- RPCS3: Multiple titles with depth effects

---

#### Memory Pressure API
**Description:** Expose memory usage tracking to emulators via custom extension `VK_EXYNOS_memory_pressure`.

**Use Case:**
- Winlator can reduce texture quality when VRAM < 512MB
- PPSSPP can flush texture cache preemptively
- Prevent Android OOM killer

**API Design:**
```c
VkResult vkGetDeviceMemoryPressureEXYNOS(
    VkDevice device,
    VkDeviceMemoryPressureInfoEXYNOS* pPressureInfo
);

typedef struct VkDeviceMemoryPressureInfoEXYNOS {
    VkStructureType    sType;
    void*              pNext;
    VkDeviceSize       usedMemory;        // Current usage
    VkDeviceSize       totalMemory;       // Total device memory
    float              pressureLevel;     // 0.0 = low, 1.0 = critical
    VkBool32           oomRisk;           // System OOM imminent
} VkDeviceMemoryPressureInfoEXYNOS;
```

**Integration:**
- Query `/proc/meminfo` for system memory
- Track Vulkan allocations via hooks
- Android `ActivityManager.MemoryInfo` for OOM threshold

---

## Priority P2: Medium (Performance & Quality-of-Life)

| Feature | Effort | Impact | Benefit | Emulators |
|---------|--------|--------|---------|-----------|
| **Texture Cache Optimization** | 2 weeks | High | 50% faster texture load | All |
| **Multi-threaded BCn Decode** | 1 week | Medium | 2-3x decode speed | Winlator |
| **ASTC Quality Profiles** | 1 week | Low | Better visual quality | All |
| **Shader Cache Warmup** | 2 weeks | Medium | Eliminate stutter | Winlator, Dolphin |

### Texture Cache Optimization
**Current:** SQLite-based cache in `/data/local/tmp/xeno_cache/`  
**Problem:** Cache lookup overhead ~0.5ms per texture (too slow for rapid texture swaps)

**Improvements:**
1. In-memory LRU cache (keep 100 most recent textures in RAM)
2. Async background save to persistent storage
3. Hash-based lookup (currently filename-based)

**Expected Gain:**
- Cache hit: 0.5ms → 0.05ms (10x faster)
- GTA V texture streaming: 10-15 FPS → 25-30 FPS

---

### Multi-threaded BCn Decode
**Current:** Single-threaded decode (uses 1 of 12 GPU cores' CPU counterpart)  
**Opportunity:** Xclipse 940 has 4x Cortex-X4 + 4x A720 cores

**Implementation:**
1. Divide texture into 16x16 block tiles
2. Spawn thread pool (4 threads on X4 cores)
3. Decode tiles in parallel
4. Combine results

**Expected Gain:**
- BC7 1024x1024 decode: 4.2ms → 1.5ms (2.8x faster)
- BC5 decode: 2.1ms → 0.8ms (2.6x faster)

---

### ASTC Quality Profiles
**Current:** Single quality level (fast = 3.1ms, medium = 12.5ms per 1024x1024)  
**Proposal:** Per-texture-type quality settings

**Profiles:**
- **UI textures:** Fast (visual quality not critical)
- **Diffuse maps:** Medium (balance speed/quality)
- **Normal maps:** Fast (compression artifacts less visible)
- **HDR textures:** Medium-high (avoid banding)

**Configuration:** Per-app profiles in `etc/exynostools/profiles/*.conf`

---

### Shader Cache Warmup
**Problem:** Vulkan pipeline compilation causes stutter (first frame of new shader)  
**Solution:** Pre-compile common pipelines at app launch

**Strategy:**
1. Build database of common DXVK/VKD3D shader signatures
2. Pre-compile top 100 shaders at wrapper init
3. Async compilation (don't block app startup)

**Expected Gain:**
- Eliminate 90% of shader compile stutter in Winlator
- 1-2 second startup delay acceptable tradeoff

---

## Priority P3: Low (Nice-to-Have)

| Feature | Effort | Impact | Rationale |
|---------|--------|--------|-----------|
| GL_EXT_sparse_texture (OpenGL ES) | 4 weeks | Low | Desktop GL parity |
| VK_EXT_shader_object | 3 weeks | Low | Future-proofing (Vulkan 1.4) |
| Adaptive Performance Tuning | 3 weeks | Medium | Battery life, thermals |
| Custom Debug Overlay | 1 week | Low | Developer QoL |

---

## Priority P4: Deferred (Blocked by Hardware/Driver)

| Feature | Blocker | Alternative | Timeline |
|---------|---------|-------------|----------|
| **Sparse 3D Texture Residency** | Hardware limitation (Mali-G720) | Software fallback? | N/A (next-gen GPU) |
| **Ray Tracing API** | Driver support (ARM r38p1 missing) | Wait for r39p0+ | Q1 2025? |
| **Pageable Device Memory** | OS limitation (Android kernel) | N/A | Android 16? |
| **Hardware-accelerated BCn** | Hardware limitation (no BCn units) | Keep software path | N/A |

### Sparse 3D Texture Software Fallback (Research)

**Feasibility Study Required:**

**Option 1: Tile-based Paging**
- Divide 3D texture into 16x16x16 voxel tiles
- Load tiles on-demand (CPU-side paging)
- Use 2D texture atlas for storage
- **Complexity:** Very High
- **Performance:** Unknown (likely 30-50% overhead)

**Option 2: Downsampling**
- Detect sparse 3D texture usage
- Force lower mipmap level (e.g., 2048³ → 1024³)
- Load entire texture (not sparse)
- **Complexity:** Medium
- **Performance:** Acceptable (memory overhead 8x)
- **Visual Quality:** Degraded (texture pop-in)

**Decision:** Defer until critical mass of games require it (currently <5%)

---

## Backlog Metrics & Success Criteria

### Emulator Compatibility Target

| Emulator | Current (v1.4.0) | Target (v1.5.0) | Target (v2.0.0) |
|----------|------------------|-----------------|-----------------|
| Winlator | 75% (42/56 games) | 85% (48/56) | 90% (50/56) |
| Dolphin | 92% (23/25 games) | 96% (24/25) | 100% (25/25) |
| PPSSPP | 100% (15/15 games) | 100% | 100% |
| Yuzu/Skyline | 30% (6/20 games) | 40% (8/20) | 60% (12/20) |
| RetroArch | 88% (shader compat) | 92% | 95% |

### Performance Target

| Metric | Current | Target (v1.5.0) | Target (v2.0.0) |
|--------|---------|-----------------|-----------------|
| BCn decode time (1024²) | 5.8ms | 3.5ms | 2.0ms |
| Texture cache hit rate | 85% | 92% | 95% |
| Shader compile stutter | 12 fps drops/min | 5 fps drops/min | <1 fps drop/min |
| Memory overhead | 180MB | 150MB | 120MB |

---

## Resource Allocation (Next 6 Months)

### Team Capacity
- **Lead Developer:** 40 hrs/week
- **Contributors:** 20 hrs/week (combined)
- **Testers:** 10 hrs/week (community)

### Sprint Planning

**Sprint 1 (Weeks 1-2): BC6H Completion**
- Finalize BC6H decode implementation
- Optimize ASTC HDR conversion
- Test with Cyberpunk 2077, Control

**Sprint 2 (Weeks 3-4): VRS Bug Workaround**
- Implement VRS hook
- Test with Witcher 3, Halo Infinite
- Regression testing (ensure no perf loss)

**Sprint 3 (Weeks 5-6): Texture Cache Optimization**
- Implement in-memory LRU cache
- Benchmark GTA V, Skyrim SE
- Document cache tuning parameters

**Sprint 4 (Weeks 7-8): Multi-threaded Decode**
- Implement thread pool for BC decode
- Profile on Cortex-X4 cores
- Test thermal impact (sustained load)

**Sprint 5 (Weeks 9-10): Depth/Stencil Fallback**
- Implement render pass hook
- Test with Dolphin (Mario Sunshine, Zelda WW)
- Edge case testing (complex barrier chains)

**Sprint 6 (Weeks 11-12): Integration & Release**
- Merge all features to main branch
- Comprehensive regression testing
- Release ExynosTools 1.5.0

---

## Community Feedback Loop

### Beta Testing Program
- **Discord:** Private beta channel (50 active testers)
- **GitHub:** Pre-release tags for early adopters
- **Survey:** Post-release compatibility survey (Google Forms)

### Issue Tracking
- **GitHub Issues:** Bug reports, feature requests
- **Priority Labels:** `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- **Emulator Tags:** `winlator`, `dolphin`, `ppsspp`, etc.

### Release Cadence
- **Major Releases:** Quarterly (1.4.0 → 1.5.0 → 1.6.0)
- **Hotfix Releases:** As-needed for critical bugs
- **Beta Builds:** Weekly (Discord-only)

---

## Upstream Collaboration

### ARM Mali Driver Team
- Report VRS bug (formal bug submission via Samsung)
- Request ray tracing API prioritization for Android
- Share performance profiling data

### Emulator Projects
- **Dolphin:** Submit depth/stencil workaround as patch
- **PPSSPP:** Collaborate on texture format detection
- **Winlator:** Share DXVK/VKD3D optimization profiles

### Android Platform
- Request pageable memory API in future Android releases
- Propose `VK_ANDROID_memory_pressure` extension to Khronos

---

## Appendix: Decision Log

### Why Not Implement Sparse 3D Texture?
**Decision Date:** 2024-09-15  
**Rationale:**
- Hardware limitation (Mali-G720 doesn't support it)
- Software fallback extremely complex (4-6 months effort)
- Only 5% of tested games require it (DOOM, BotW)
- Wait for next-gen hardware (Xclipse 950, Mali-G820)

### Why Prioritize BC6H Over Ray Tracing?
**Decision Date:** 2024-10-01  
**Rationale:**
- BC6H impacts 23% of tested games (7/30 AAA titles)
- Ray tracing unavailable in ARM driver (r38p1)
- BC6H is achievable in 3 weeks (vs RT waiting on ARM)
- More immediate user value

### Why Not Hardware BCn Decode?
**Rationale:**
- Requires GPU firmware modification (not feasible)
- ARM unlikely to add legacy texture formats to mobile GPUs
- Software decode acceptable with caching (<6ms first load)
- ASTC is preferred future standard (better quality/size)

---

**Document Maintained By:** Wrapper Development Team  
**Last Updated:** 2025-01-09  
**Next Review:** 2025-04-01 (post-v1.5.0 release)
