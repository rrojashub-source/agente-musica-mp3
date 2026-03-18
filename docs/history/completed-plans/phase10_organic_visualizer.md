# Phase 10: Organic/Fluid Visualizer

**Status:** PLANNED (Not started)
**Priority:** Enhancement (post-commercial release)
**Created:** December 17, 2025
**Origin:** Idea from NEXUS Avatar project (nexus-avatar)

---

## Concept

Add a new visualizer mode inspired by the NEXUS Avatar's fluid organic movement. Instead of traditional bars/circles, this visualizer uses:

- **SDF (Signed Distance Functions)** - Mathematical smooth shapes
- **Ray Marching** - 3D rendering without polygons
- **Smooth-min blending** - Organic transitions between forms
- **Simplex noise** - Natural deformation

The result is a living, breathing form that "dances" with the music.

---

## Technical Approach

### Shader Uniforms (Audio-driven)

```glsl
// Audio inputs (from FFT analysis)
uniform float u_bass;       // Low frequencies (20-250 Hz) → nucleus pulse
uniform float u_mids;       // Mid frequencies (250-4000 Hz) → extension movement
uniform float u_highs;      // High frequencies (4000-20000 Hz) → particles/sparkles
uniform float u_amplitude;  // Overall volume → general size
uniform float u_beat;       // Beat detection → metamorphosis trigger

// Time
uniform float u_time;
uniform vec2 u_resolution;

// Style
uniform vec3 u_baseColor;   // Theme color from app
uniform vec3 u_accentColor; // Secondary color
```

### PyQt6 Implementation

```python
# Use QOpenGLWidget for native GLSL support
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram

class OrganicVisualizerWidget(QOpenGLWidget):
    """
    SDF Ray Marching visualizer driven by audio FFT data.
    Ported from NEXUS Avatar shader (nexusCore.ts → GLSL).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shader_program = None
        # Audio uniforms
        self.bass = 0.0
        self.mids = 0.0
        self.highs = 0.0
        self.amplitude = 0.0
        self.beat = 0.0

    def update_audio(self, fft_data):
        """Called from audio analyzer with FFT bins."""
        # Map FFT bins to frequency ranges
        self.bass = self._average_bins(fft_data, 0, 10)      # ~20-250 Hz
        self.mids = self._average_bins(fft_data, 10, 100)    # ~250-4000 Hz
        self.highs = self._average_bins(fft_data, 100, 512)  # ~4000+ Hz
        self.amplitude = sum(fft_data) / len(fft_data)
        self.update()  # Trigger repaint
```

### Reference Shader

The base shader is in:
```
/mnt/d/01_PROYECTOS_ACTIVOS/NEXUS_CUERPO_DIGITAL/nexus-avatar/src/shaders/nexusCore.ts
```

Key functions to port:
- `snoise()` - Simplex noise
- `sdSphere()` - SDF sphere
- `smin()` - Smooth minimum (organic blend)
- `sdNucleoNexus()` - Core nucleus
- `sdExtensionesNexus()` - Extensions
- `rayMarch()` - Ray marching loop
- `getLight()` - Lighting calculation

---

## Visual Modes

Could support multiple organic styles:

1. **NEXUS Mode** - Blue, dual fluid↔crystal, technical
2. **ARIA Mode** - Pink/warm, always soft, heartbeat pulse
3. **ECHO Mode** - Silver/ethereal, memory ripples

Or a **Music Mode** that adapts colors from album art.

---

## Integration Points

1. **VisualizerTab** - Add as 4th visualizer option (Brain AI, Bars, Circles, **Organic**)
2. **AudioAnalyzer** - Already provides FFT data, just need to route to new widget
3. **Settings** - Add organic visualizer preferences (color scheme, sensitivity)

---

## Files to Create

```
src/gui/visualizers/
├── organic_visualizer.py      # QOpenGLWidget implementation
├── organic_shaders/
│   ├── vertex.glsl            # Simple passthrough vertex shader
│   ├── fragment_nexus.glsl    # NEXUS style (from avatar)
│   ├── fragment_aria.glsl     # ARIA style (optional)
│   └── fragment_echo.glsl     # ECHO style (optional)
└── __init__.py
```

---

## Estimated Effort

- **Shader port:** 2-3 hours (GLSL is nearly identical to Three.js)
- **QOpenGLWidget setup:** 2-3 hours
- **Audio integration:** 1-2 hours
- **UI integration:** 1-2 hours
- **Testing/polish:** 2-3 hours

**Total:** ~10-15 hours (1-2 sessions)

---

## Dependencies

- PyOpenGL (already in requirements.txt for Brain AI visualizer)
- numpy (already installed)

No new dependencies needed.

---

## Notes

- This came from the NEXUS Avatar desktop pet project
- The avatar uses Three.js/React, but the shader logic is pure GLSL
- PyQt6's QOpenGLWidget can run the same GLSL code
- Beat detection could trigger "metamorphosis" transitions (fluid ↔ crystal)

---

## Success Criteria

- [ ] Organic visualizer renders at 60fps
- [ ] Bass frequencies pulse the nucleus
- [ ] Mids move the extensions
- [ ] Highs create particle sparkles
- [ ] Beat detection triggers smooth transitions
- [ ] Multiple style presets available
- [ ] Integrates with existing visualizer tab

---

**Ricardo's Note:** "la forma en que esto se mueve es mucho mas fluido, y natural"

That's the goal - bring that organic, living movement to the music player.
