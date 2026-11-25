# Barangay Sinagtala 3D — First-Person Raycasting Explorer

A first-person 3D engine built entirely with Python and Pygame using classical DDA (Digital Differential Analysis) raycasting/raytracing.

## How to Run

1. Make sure Python 3.10+ is installed.
2. In terminal, navigate to this folder:
   ```cmd
   cd Barangay_Sinagtala_3D
   python main.py
   ```
   Or double-click `run.bat` on Windows.

## Controls

- **W / A / S / D**: Move forward / backward, strafe left / right
- **Left / Right Arrows**: Turn camera
- **Shift** (hold): Sprint boost
- **Tab**: Toggle Mouse-Look mode (look around smoothly with your mouse)
- **M**: Toggle Minimap Radar overlay
- **Esc**: Quit

## Features

- **High-Performance 3D Raycasting**: Renders 640 ray columns with DDA traversal and fish-eye correction at 60 FPS.
- **Directional Shading & Depth Fog**: East/West and North/South wall faces have distinct lighting, and distant objects fade naturally into atmospheric haze.
- **Procedural Colonial Textures**: Spanish colonial stone masonry, terracotta bricks, timber, and antique plaster textures.
- **Collision Detection**: Real-time bounding collision with wall sliding.
- **2D Minimap Radar**: Overhead view displaying player position and field-of-view cone.
