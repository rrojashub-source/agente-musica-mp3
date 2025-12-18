// Fragment Shader - Organic Music Visualizer
// Ported from NEXUS Avatar (nexusCore.ts)
// Adapted for audio-reactive visualization
//
// Part of Organic Visualizer (Phase 10)
// Created: December 17, 2025

#version 330 core

// Audio inputs (from FFT analysis)
uniform float u_bass;       // Low frequencies (20-250 Hz) -> nucleus pulse
uniform float u_mids;       // Mid frequencies (250-4000 Hz) -> extension movement
uniform float u_highs;      // High frequencies (4000-20000 Hz) -> particles/sparkles
uniform float u_amplitude;  // Overall volume -> general size
uniform float u_beat;       // Beat detection -> metamorphosis trigger (0=fluid, 1=crystal)

// Time and resolution
uniform float u_time;
uniform vec2 u_resolution;

// Style colors
uniform vec3 u_baseColor;   // Primary color (default: cyan)
uniform vec3 u_accentColor; // Secondary color (default: magenta)

in vec2 vUv;
out vec4 fragColor;

const float PI = 3.14159265359;
const int MAX_STEPS = 64;
const float MAX_DIST = 50.0;
const float SURF_DIST = 0.002;

// ==========================================
// Simplex Noise (for organic deformation)
// ==========================================

vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);

    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);

    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;

    i = mod289(i);
    vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
        + i.y + vec4(0.0, i1.y, i2.y, 1.0))
        + i.x + vec4(0.0, i1.x, i2.x, 1.0));

    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;

    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);

    vec4 x = x_ *ns.x + ns.yyyy;
    vec4 y = y_ *ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);

    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);

    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));

    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;

    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);

    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;

    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}

// ==========================================
// SDF Primitives
// ==========================================

float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdOctahedron(vec3 p, float s) {
    p = abs(p);
    return (p.x + p.y + p.z - s) * 0.57735027;
}

// Smooth-min: heart of metamorphosis (organic blending)
float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}

// ==========================================
// Core Shapes (Audio-Reactive)
// ==========================================

// Nucleus - pulses with BASS (AMPLIFIED for dancing effect!)
float sdNucleus(vec3 p, float time) {
    float nucleus = sdSphere(p, 0.25);
    // Bass-driven pulse - MUCH stronger response!
    float pulse = sin(time * 4.0 + u_bass * PI * 2.0) * 0.15 * u_bass;
    pulse += u_bass * 0.2;  // Direct bass expansion
    nucleus -= pulse;
    return nucleus;
}

// Fluid Extensions - move with MIDS (organic, flowing) - DANCE MODE!
float sdExtensionsFluid(vec3 p, float time) {
    float ext = MAX_DIST;

    for (int i = 0; i < 6; i++) {
        float angle = float(i) * PI * 2.0 / 6.0 + time * 0.5;
        vec3 dir = vec3(cos(angle), sin(angle) * 0.7, sin(angle));

        // Mids-driven wave - MUCH more movement!
        float wave = sin(time * 3.0 + float(i) * 1.5 + u_mids * PI * 2.0) * 0.25 * (0.3 + u_mids);
        wave += u_mids * 0.15;  // Direct mids expansion
        vec3 offset = dir * (0.45 + wave);

        float synapse = sdSphere(p - offset, 0.12 + wave * 0.08);
        ext = smin(ext, synapse, 0.35);
    }

    return ext;
}

// Crystal Extensions - angular, geometric (for beat detection)
float sdExtensionsCrystal(vec3 p, float time) {
    float ext = MAX_DIST;

    for (int i = 0; i < 6; i++) {
        float angle = float(i) * PI * 2.0 / 6.0;
        vec3 dir = vec3(cos(angle), 0.0, sin(angle));
        vec3 offset = dir * 0.6;

        float rot = time * 0.5 + float(i);
        mat3 rotation = mat3(
            cos(rot), 0, sin(rot),
            0, 1, 0,
            -sin(rot), 0, cos(rot)
        );

        vec3 localP = rotation * (p - offset);
        float crystal = sdOctahedron(localP, 0.15);
        ext = smin(ext, crystal, 0.05);
    }

    return ext;
}

// ==========================================
// NEW METAMORPHOSIS SHAPES
// ==========================================

// Humanoid silhouette (torso + head + arms hint)
float sdHumanoid(vec3 p, float time) {
    // Torso (elongated sphere)
    vec3 torsoP = p;
    torsoP.y *= 0.6;  // Stretch vertically
    float torso = sdSphere(torsoP, 0.25);

    // Head
    vec3 headP = p - vec3(0.0, 0.4, 0.0);
    float head = sdSphere(headP, 0.15);

    // Arms (two spheres on sides, moving with mids)
    float armWave = sin(time * 3.0 + u_mids * PI) * 0.1;
    vec3 leftArmP = p - vec3(-0.35, 0.1 + armWave, 0.0);
    vec3 rightArmP = p - vec3(0.35, 0.1 - armWave, 0.0);
    float leftArm = sdSphere(leftArmP, 0.1);
    float rightArm = sdSphere(rightArmP, 0.1);

    // Combine with smooth blend
    float body = smin(torso, head, 0.15);
    body = smin(body, leftArm, 0.2);
    body = smin(body, rightArm, 0.2);

    return body;
}

// Star/Flower shape (expands on bass peaks)
float sdStar(vec3 p, float time) {
    float star = MAX_DIST;
    int numPoints = 5;

    // Central core
    float core = sdSphere(p, 0.15 + u_bass * 0.1);
    star = core;

    // Star points radiating outward
    for (int i = 0; i < 5; i++) {
        float angle = float(i) * PI * 2.0 / 5.0 + time * 0.2;
        float elevation = sin(time * 2.0 + float(i)) * 0.3;

        vec3 dir = vec3(cos(angle), elevation, sin(angle));
        float dist = 0.4 + u_bass * 0.3;  // Expands with bass
        vec3 pointPos = dir * dist;

        // Tapered point (smaller sphere at tip)
        float point = sdSphere(p - pointPos, 0.08);

        // Connector to core
        vec3 midPos = dir * dist * 0.5;
        float connector = sdSphere(p - midPos, 0.06);

        star = smin(star, point, 0.15);
        star = smin(star, connector, 0.2);
    }

    return star;
}

// Spiral/DNA helix shape
float sdSpiral(vec3 p, float time) {
    float spiral = MAX_DIST;

    // Two intertwined helices
    for (int i = 0; i < 12; i++) {
        float t = float(i) / 12.0;
        float angle = t * PI * 4.0 + time * 1.5;  // Two full rotations
        float y = (t - 0.5) * 1.2;  // Vertical spread

        // First helix
        vec3 pos1 = vec3(cos(angle) * 0.25, y, sin(angle) * 0.25);
        float sphere1 = sdSphere(p - pos1, 0.08 + u_mids * 0.03);

        // Second helix (offset by PI)
        vec3 pos2 = vec3(cos(angle + PI) * 0.25, y, sin(angle + PI) * 0.25);
        float sphere2 = sdSphere(p - pos2, 0.08 + u_mids * 0.03);

        spiral = smin(spiral, sphere1, 0.1);
        spiral = smin(spiral, sphere2, 0.1);
    }

    return spiral;
}

// ==========================================
// FLUBBER DANCING FIGURE - With METAMORPHOSIS!
// ==========================================

// Dancing humanoid with PRONOUNCED limbs
float sdDancingFigure(vec3 p, float time) {
    // === DRAMATIC MOVEMENT MULTIPLIER (based on audio energy) ===
    float energy = u_amplitude * 2.0 + u_bass * 1.5 + u_mids;
    float danceIntensity = 0.3 + energy * 0.7;  // Min 0.3, max 1.0+

    // === GLOBAL SQUASH & STRETCH ===
    float squash = 1.0 - u_beat * 0.35;       // MORE squash on beat
    float stretch = 1.0 + u_beat * 0.25;      // MORE stretch

    vec3 sp = p;
    sp.y /= squash;
    sp.x *= stretch;
    sp.z *= stretch;

    // === BODY BOUNCE (dramatic!) ===
    float bounce = u_beat * 0.25 + sin(time * 8.0) * 0.05 * u_amplitude;
    bounce += u_bass * 0.15;  // Extra bounce on bass
    sp.y += bounce;

    // === BODY SWAY (dramatic!) ===
    float sway = sin(time * 3.0) * 0.15 * danceIntensity;
    sway += sin(time * 5.0) * 0.05 * u_mids;
    sp.x += sway;

    // === HEAD (bouncy) ===
    vec3 headPos = vec3(0.0, 0.38, 0.0);
    headPos.y += sin(time * 6.0) * 0.05 * danceIntensity;
    headPos.x += sin(time * 4.0) * 0.03 * u_mids;
    float head = sdSphere(sp - headPos, 0.11 + u_bass * 0.03);

    // === TORSO ===
    vec3 torsoP = sp - vec3(0.0, 0.12, 0.0);
    torsoP.y *= 0.65;
    float torso = sdSphere(torsoP, 0.14 + u_bass * 0.04);

    // === HIPS (counter-sway) ===
    vec3 hipPos = vec3(-sway * 0.3, -0.1, 0.0);
    float hips = sdSphere(sp - hipPos, 0.12);

    // === ARMS - MUCH MORE PRONOUNCED! ===
    // Left arm - upper arm
    float leftArmAngle = sin(time * 5.0) * 0.8 * danceIntensity + u_mids * PI * 0.5;
    vec3 leftShoulderPos = vec3(-0.18, 0.18, 0.0);
    vec3 leftElbowOffset = vec3(
        -0.18 - cos(leftArmAngle) * 0.08,
        sin(leftArmAngle) * 0.12,
        sin(time * 3.0) * 0.05
    );
    vec3 leftElbowPos = leftShoulderPos + leftElbowOffset;
    float leftUpperArm = sdSphere(sp - leftElbowPos, 0.055);

    // Left forearm + hand
    vec3 leftHandOffset = vec3(
        -0.15 - cos(leftArmAngle) * 0.1,
        sin(leftArmAngle) * 0.18,
        sin(time * 4.0) * 0.08
    );
    vec3 leftHandPos = leftElbowPos + leftHandOffset;
    float leftHand = sdSphere(sp - leftHandPos, 0.045);

    // Right arm - upper arm (opposite phase)
    float rightArmAngle = sin(time * 5.0 + PI) * 0.8 * danceIntensity + u_mids * PI * 0.5;
    vec3 rightShoulderPos = vec3(0.18, 0.18, 0.0);
    vec3 rightElbowOffset = vec3(
        0.18 + cos(rightArmAngle) * 0.08,
        sin(rightArmAngle) * 0.12,
        sin(time * 3.0 + PI) * 0.05
    );
    vec3 rightElbowPos = rightShoulderPos + rightElbowOffset;
    float rightUpperArm = sdSphere(sp - rightElbowPos, 0.055);

    // Right forearm + hand
    vec3 rightHandOffset = vec3(
        0.15 + cos(rightArmAngle) * 0.1,
        sin(rightArmAngle) * 0.18,
        sin(time * 4.0 + PI) * 0.08
    );
    vec3 rightHandPos = rightElbowPos + rightHandOffset;
    float rightHand = sdSphere(sp - rightHandPos, 0.045);

    // === LEGS - MUCH MORE PRONOUNCED! ===
    // Left leg - thigh
    float leftLegPhase = sin(time * 4.0) * 0.2 * danceIntensity;
    vec3 leftThighPos = vec3(-0.08, -0.25, leftLegPhase * 0.8);
    leftThighPos.y += abs(leftLegPhase) * 0.4;  // Lift when kicking
    float leftThigh = sdSphere(sp - leftThighPos, 0.065);

    // Left shin + foot
    vec3 leftFootPos = leftThighPos + vec3(0.0, -0.18, leftLegPhase * 0.5);
    leftFootPos.y -= abs(sin(time * 4.0 + 0.5)) * 0.08 * danceIntensity;
    float leftFoot = sdSphere(sp - leftFootPos, 0.05);

    // Right leg - thigh (opposite phase)
    float rightLegPhase = sin(time * 4.0 + PI) * 0.2 * danceIntensity;
    vec3 rightThighPos = vec3(0.08, -0.25, rightLegPhase * 0.8);
    rightThighPos.y += abs(rightLegPhase) * 0.4;
    float rightThigh = sdSphere(sp - rightThighPos, 0.065);

    // Right shin + foot
    vec3 rightFootPos = rightThighPos + vec3(0.0, -0.18, rightLegPhase * 0.5);
    rightFootPos.y -= abs(sin(time * 4.0 + PI + 0.5)) * 0.08 * danceIntensity;
    float rightFoot = sdSphere(sp - rightFootPos, 0.05);

    // === COMBINE (gooey Flubber blend) ===
    float body = smin(head, torso, 0.1);
    body = smin(body, hips, 0.08);

    // Arms with shoulder connections
    float leftArm = smin(leftUpperArm, leftHand, 0.06);
    float rightArm = smin(rightUpperArm, rightHand, 0.06);
    body = smin(body, leftArm, 0.08);
    body = smin(body, rightArm, 0.08);

    // Legs with hip connections
    float leftLeg = smin(leftThigh, leftFoot, 0.05);
    float rightLeg = smin(rightThigh, rightFoot, 0.05);
    body = smin(body, leftLeg, 0.07);
    body = smin(body, rightLeg, 0.07);

    return body;
}

float map(vec3 p) {
    float time = u_time;

    // === AUDIO ENERGY for metamorphosis triggers ===
    float totalEnergy = u_bass + u_mids + u_highs + u_amplitude;
    float bassEnergy = u_bass;
    float midsEnergy = u_mids;
    float highsEnergy = u_highs;

    // === BASE FORM: Dancing figure ===
    float figure = sdDancingFigure(p, time);

    // === METAMORPHOSIS BLEND FACTORS (audio-reactive!) ===
    // Star: appears on strong BASS hits
    float starBlend = smoothstep(0.4, 0.8, bassEnergy) * u_beat;

    // Spiral: appears on sustained MIDS (melodic parts)
    float spiralBlend = smoothstep(0.3, 0.7, midsEnergy) * (1.0 - u_beat * 0.5);

    // Crystal: appears on HIGHS (sharp, crisp moments)
    float crystalBlend = smoothstep(0.5, 0.9, highsEnergy) * u_beat;

    // Humanoid base: always present but varies with amplitude
    float humanoidBlend = 1.0 - (starBlend + spiralBlend + crystalBlend) * 0.3;
    humanoidBlend = max(0.3, humanoidBlend);

    // === GET METAMORPHOSIS SHAPES ===
    float star = sdStar(p, time);
    float spiral = sdSpiral(p, time);
    float crystal = sdExtensionsCrystal(p, time);

    // === BLEND ALL SHAPES TOGETHER ===
    // Start with dancing figure
    float result = figure;

    // Blend in star on bass peaks (explosive!)
    if (starBlend > 0.01) {
        result = smin(result, star, 0.3 - starBlend * 0.15);
    }

    // Blend in spiral on mids (flowing)
    if (spiralBlend > 0.01) {
        result = smin(result, spiral, 0.25);
    }

    // Blend in crystals on highs (sharp accents)
    if (crystalBlend > 0.01) {
        result = smin(result, crystal, 0.15);
    }

    // === JIGGLY WOBBLE (scales with energy!) ===
    float wobbleStrength = 0.01 + totalEnergy * 0.025;
    float wobble = 0.0;
    wobble += sin(p.x * 12.0 + time * 7.0 + u_bass * 6.0) * wobbleStrength;
    wobble += sin(p.y * 10.0 + time * 8.0 + u_mids * 5.0) * wobbleStrength;
    wobble += sin(p.z * 11.0 + time * 6.0 + u_amplitude * 6.0) * wobbleStrength;

    result += wobble;

    // === BEAT PULSE (expand on every beat!) ===
    float beatPulse = u_beat * 0.08;
    result -= beatPulse;  // Negative = expand outward

    // === SURFACE NOISE ===
    float noise = snoise(p * 6.0 + time * 0.5) * 0.012;
    result += noise * (1.0 - u_beat * 0.7);

    return result;
}

// ==========================================
// Ray Marching
// ==========================================

float rayMarch(vec3 ro, vec3 rd) {
    float d0 = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * d0;
        float dS = map(p);
        d0 += dS;
        if (d0 > MAX_DIST || dS < SURF_DIST) break;
    }
    return d0;
}

vec3 getNormal(vec3 p) {
    float d = map(p);
    vec2 e = vec2(0.001, 0.0);
    vec3 n = d - vec3(
        map(p - e.xyy),
        map(p - e.yxy),
        map(p - e.yyx)
    );
    return normalize(n);
}

// ==========================================
// Brain AI Color Palette (6 colors)
// ==========================================

vec3 getBrainColor(float t) {
    // Brain AI palette: cyan -> blue -> purple -> magenta -> pink -> cyan-green
    vec3 colors[6];
    colors[0] = vec3(0.0, 0.78, 1.0);   // Cyan
    colors[1] = vec3(0.0, 0.39, 1.0);   // Blue
    colors[2] = vec3(0.39, 0.0, 1.0);   // Purple
    colors[3] = vec3(0.78, 0.0, 1.0);   // Magenta
    colors[4] = vec3(1.0, 0.0, 0.59);   // Pink
    colors[5] = vec3(0.0, 1.0, 0.78);   // Cyan-green

    t = clamp(t, 0.0, 1.0) * 5.0;  // Scale to 0-5
    int idx = int(floor(t));
    float blend = fract(t);

    idx = min(idx, 4);
    return mix(colors[idx], colors[idx + 1], blend);
}

// ==========================================
// Lighting - FLUBBER STYLE (gelatinous/translucent)
// ==========================================

vec3 getLight(vec3 p, vec3 rd) {
    vec3 lightPos = vec3(2.0, 3.0, 4.0);
    vec3 lightPos2 = vec3(-2.0, 1.0, -3.0);  // Secondary light for depth
    vec3 L = normalize(lightPos - p);
    vec3 L2 = normalize(lightPos2 - p);
    vec3 N = getNormal(p);
    vec3 V = -rd;
    vec3 R = reflect(-L, N);

    // Soft diffuse (gel-like)
    float diff = max(dot(N, L), 0.0);
    float diff2 = max(dot(N, L2), 0.0) * 0.3;  // Fill light

    // Subsurface scattering fake (light passes through gel)
    float subsurface = pow(max(0.0, dot(-L, V)), 2.0) * 0.4;
    subsurface += pow(max(0.0, dot(-L2, V)), 2.0) * 0.2;

    // Specular: shiny gel surface
    float specPower = 32.0 + u_beat * 32.0;  // Sharper on beat
    float spec = pow(max(dot(R, V), 0.0), specPower);
    spec *= 0.6 + u_beat * 0.3;

    // Strong fresnel (gel has strong edge glow)
    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 2.5);
    fresnel *= 0.7 + u_amplitude * 0.3;

    // Dynamic color cycling through Brain AI palette
    float colorT = u_mids * 0.4 + u_bass * 0.3 + u_time * 0.15;
    vec3 gelColor = getBrainColor(mod(colorT, 1.0));

    // Core color (slightly different for depth)
    vec3 coreColor = getBrainColor(mod(colorT + 0.2, 1.0));

    // Combine: ambient + diffuse + subsurface + specular + fresnel
    vec3 col = gelColor * 0.15;  // Ambient (gel glows slightly)
    col += gelColor * (diff * 0.5 + diff2);  // Main diffuse
    col += coreColor * subsurface;  // Light through gel
    col += vec3(1.0) * spec * 0.7;  // Bright specular highlight
    col += gelColor * fresnel * 0.5;  // Edge glow

    // Boost saturation on beats (more vibrant)
    float satBoost = 1.0 + u_beat * 0.3;
    vec3 gray = vec3(dot(col, vec3(0.299, 0.587, 0.114)));
    col = mix(gray, col, satBoost);

    return col;
}

// ==========================================
// Sparkle Particles (HIGHS reactive) - SUBTLE version
// ==========================================

vec3 sparkleParticles(vec2 uv, float time) {
    if (u_highs < 0.4) return vec3(0.0);  // Higher threshold

    vec3 particles = vec3(0.0);
    int numParticles = int(mix(2.0, 6.0, u_highs));  // Fewer particles

    for (int i = 0; i < 6; i++) {
        if (i >= numParticles) break;

        float angle = float(i) * PI * 2.0 / float(numParticles) + time * (0.3 + u_highs * 0.5);
        float radius = 0.5 + sin(time * 1.5 + float(i) * 0.9) * 0.15;

        vec2 particlePos = vec2(cos(angle) * radius * 1.2, sin(angle) * radius);

        float dist = length(uv - particlePos);
        float glow = 0.004 / (dist + 0.008);  // Much smaller glow
        glow *= u_highs * 0.6;  // Reduced intensity

        // Color: cyan/white sparkles (matches theme, not golden)
        vec3 particleColor = mix(u_baseColor, vec3(1.0), 0.5);
        particles += particleColor * glow;
    }
    return particles;
}

// ==========================================
// Main
// ==========================================

void main() {
    vec2 uv = vUv * 2.0 - 1.0;
    uv.x *= u_resolution.x / u_resolution.y;

    // Camera setup
    vec3 ro = vec3(0.0, 0.0, 2.5);
    vec3 rd = normalize(vec3(uv, -1.0));

    // Ray march
    float d = rayMarch(ro, rd);

    vec3 col = vec3(0.0);

    if (d < MAX_DIST) {
        vec3 p = ro + rd * d;
        col = getLight(p, rd);

        // Core glow (amplitude-reactive)
        float nucleusDist = length(p);
        float nucleusGlow = 0.1 / (nucleusDist + 0.1);
        col += u_baseColor * nucleusGlow * u_amplitude * 0.5;
    }

    // Add sparkle particles (highs-reactive)
    col += sparkleParticles(uv, u_time);

    // Gamma correction
    col = pow(col, vec3(0.4545));

    // Background fade (slight color based on amplitude)
    vec3 bgColor = u_baseColor * 0.05 * u_amplitude;
    col = max(col, bgColor);

    fragColor = vec4(col, 1.0);
}
