# leaddbs-blender

This repository collects utility scripts to render DBS 3D scenes with Blender. In the first release (v0.2), a script is included to autmatically create a 3D model of a DBS electrode (non-directional or directional) based on specifications in a .json file.

## Requirements

- Tested on Blender 2.92 and 3.0
- The script relies on the following (built-in) Add-ons:
  - Add Curve: Curve Tools
  - Add Curve: Extra Objects

## Usage

Simply copy/paste the code into the scripting window of a Blender file. Copy/paste the example [.json file](/electrode_modelling/elspec.json) in the same folder as you Blender file and hit run. It will create a simple 4 contact electrode as an example.

### Explanation of the .json specification file

Most of the parameters should be self-explanatory. A couple of things to note:

- `contact_spacing": [0.5]` Contact spacings are usually uniform, but some electrode may very in spacings between levels. So the variable `contact_spacing` can be a list, in which each level can have a different spacing if needed.
- `num_level: 5` This parameter specifies the number of levels the contact should have. If the tip is not a contact, this is the amount of contact levels + 1, because in this case, we need to specifiy the size of the tip in `contact_specification`. If the tip is a contact, this number represents the number of contact levels.
- Size of segmented contacts is in degrees, all other units in mm.

