// Vertex Shader - Simple passthrough for fullscreen quad
// Part of Organic Visualizer (Phase 10)

#version 330 core

in vec2 position;
in vec2 texCoord;

out vec2 vUv;

void main() {
    vUv = texCoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
