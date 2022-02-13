# A simple CLI for controlling Hue lamps
Use -h or --help detailed instructions on command line usage.

## Setup for command line use
  1. Press Sync Button on Hue Bridge
  2. Connect to Hue Bridge with --init-bridge 'name' 'ip'
  3. View lights with --show-lights and define groups with --create-group

---

## TODO
- Make main method more sleek

## In-File TODOs

- [ ] `./hue_controller/control.py:95:` TODO: Make this more Elegant. Use Dict for actions
- [ ] `./hue_controller/hue_classes.py:354:` TODO: fix to use only one set of if-statements
- [ ] `./hue_controller/hue_util.py:4:` TODO: Fix this so it uses the index instead of the element.
- [ ] `./hue_controller/hue_util.py:5:` TODO: Also fix where `get_next`is used.
- [ ] `./build/scripts-3.10/control.py:95:` TODO: Make this more Elegant. Use Dict for actions
- [ ] `./build/scripts-3.9/control.py:98:` TODO: Make this more Elegant. Use Dict for actions
- [ ] `./build/lib/hue_controller/control.py:95:` TODO: Make this more Elegant. Use Dict for actions
- [ ] `./build/lib/hue_controller/hue_classes.py:354:` TODO: fix to use only one set of if-statements
- [ ] `./build/lib/hue_controller/hue_util.py:4:` TODO: Fix this so it uses the index instead of the element.
- [ ] `./build/lib/hue_controller/hue_util.py:5:` TODO: Also fix where `get_next` is used.

