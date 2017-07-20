#version 150
 
// Input from vertex shader
in vec3 position;

// inputs from panda3d
uniform vec3 wspos_camera;

out vec4 out_Color;
 
void main() {
  // distance from object to camera
  float dist = distance(position, wspos_camera);
  float fact = smoothstep(0, 1, dist / 2000);

  // some constants
  vec3 diffuse = vec3(0, 0, 0);
  vec3 normal = vec3(1.0, 1.0, 1.0);
  vec3 fake_sun = normalize(vec3(0.7, 0.2, 0.6));
  vec3 shading = max(0.0, dot(normal, fake_sun)) * diffuse;
  shading += vec3(0.5, 0.2, 0.2);

  // mix the constants with the distance factor
  shading = mix(shading, vec3(0.7, 0.7, 0.8), fact);

  out_Color = vec4(shading, 1.0);
}
