# Barangay Sinagtala — World Map Explorer

This is the separated, ready-to-open project reconstructed from the supplied pasted code. The pasted text contained 11 Python modules joined into one document; they are now separate files.

## Open in PyCharm
1. Extract this ZIP to a normal folder, for example `Desktop\Barangay_Sinagtala_World_Explorer`.
2. In PyCharm choose **File → Open** and select the extracted `Barangay_Sinagtala_World_Explorer` folder (not an individual file).
3. Open the PyCharm Terminal. Make sure the terminal path ends in `Barangay_Sinagtala_World_Explorer`.
4. Install the dependency: `python -m pip install -r requirements.txt`
5. Right-click `main.py` in the Project panel and choose **Run 'main'**.

You can also double-click `run_map.bat` on Windows.

## Controls
- WASD / Arrow keys: pan around the map
- Shift: faster pan
- 1–8: center the camera on a district
- L: toggle cinematic lighting
- F12: export map overview and district renders
- Esc: quit

## Export map images
From the project terminal, run `python export_renders.py`. Images are saved in the `renders` folder.

## Project files
- `asset_loader.py`: loads and builds reusable assets from the supplied packs
- `terrain.py`, `autotile.py`, `tilemap.py`: terrain and tilemap systems
- `environment.py`: environmental props and layer rendering
- `animation.py`: animated environment and ambient effects
- `lighting.py`: district lighting
- `camera.py`: map camera
- `map.py`: Barangay Sinagtala map layout
- `main.py`: interactive map explorer entry point
- `export_renders.py`: image export tool

## Included assets
Selected PNG tilesets and sprite sheets are included under `assets/`. Original pack license/readme files are included where provided in the source archives. Keep those notices with the project and follow each pack's license terms.

## Troubleshooting
If PyCharm says it cannot find `main.py`, use **File → Open** and open this extracted project folder. In **Run → Edit Configurations**, set the script to this folder's `main.py` and the working directory to this folder.
