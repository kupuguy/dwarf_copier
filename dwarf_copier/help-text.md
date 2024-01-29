Dwarf Copy
==========

Copies files from the Dwarf II telescope to a PC moving them into a structure that is compatible with Siril.

Steps:

1. Add a new Dwarf telescope definition.
2. Select images to copy
3. Watch as the app does its stuff

Connecting to the Dwarf II
--------------------------
You connect to your Dwarf II in any of several ways:

1. Put the micro SD card in a card reading slot on your PC. In this case you get a drive letter and create a definition to access that drive.

2. Connect via Bluetooth. This is similar to the way the app connects.

3. Connect via IP address. This option is handy if you commonly use STA mode. If you can, configure your router to reserve the telescope's IP address so it always connects using the same one.

You may create as many telescope definitions as you wish to connect in different ways.

Commands
--------

* D - Toggle dark mode
* Q - Quit
* S - Edit settings
* ? - Show this help text (press `Esc` to return to the main screen)

Configuration
-------------

### Templates

Directory and filenames in the configuration are given as templates, use "$name" or "${name}" to substitute `name` into the string, use "$$" to insert a single dollar sign.

The following names are available for use in templates.

* exp - Exposure (as a decimal rather than a fraction for exposures less than 1 second)
* gain - Gain
* Y - 4 digit year
* M - 2 digit month
* d - 2 digit day of the month
* H - 2 digit hour
* m - 2 digit minutes
* S - 2 digit seconds
* ms - 3 digit milliseconds
* target - the target that was being tracked (if any)
* name - original filename

### General

General configuration:

- theme - 'light' or 'dark'

### Sources

Locations to find Dwarf image files.

- name - Name displayed in the source selection box
- type - 'Drive', 'FTP', 'MTP.  FTP and MTP and not currently implemented.
- path - Path to the location containing the 'Astronomy' folder.
- darks - List of templated paths that may contain darks.
- link - Boolean. If true for both source and destination then symlinks may be used
    instead of copying the files. Defaults to false.

### Targets

Destination to receive image files (or to create symlinks).

- name: Name displayed in the target selection box
- description: Brief description about the destination
- path: Path to the destination (not a template!)
- format: How files are rearranged in the destination, must match a name in the
    formats section.
- link: Boolean. If true for both source and destination then symlinks may be used
    instead of copying the files. Defaults to true.

### Formats

Describes how files are rearranged when copied or linked. The default configurations:

- 'Backup' just copies the files as they are, and copies darks to a specified folder if they exist.
- 'Siril' creates a directory structure including 'lights', 'darks', 'biases' and
    'flats' folders. Fits files are copied into 'lights', the Dwarf's stacked images and the JSON file are copied to the top level but the images are renamed.