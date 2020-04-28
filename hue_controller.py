#!/usr/bin/python
import sys, os
import requests
import json
import logging

from hue_classes import HueBridge
from hue_util import get_next


def print_help():
  """Prints Help Information
  
  Returns:
    None
  """
  help_str = \
"""Usage: hue_controller.py <command> [params]
Special Commands:
    --init-bridge  'bridge name' 'ip'
            Initializes new Hue Bridge at given ip. 
            Press hue sync button before executing.

    --show-bridges
            Shows all avaliable initialized bridges.

================================================================================
Bridge-Specific Commands (Specify bridge with -b 'bridge_name'):
    --show-lights
            Lists lights connected to a bridge.

    --show-groups
            Lists groups defined for a bridge.

-------------------------------------------------------------------------------
Grouping:
    --create-group 'group_name|light1;light2;light3...'
            Creates group of lights by light name. 

    --remove-group 'group_name'
            Removes group by name.

-------------------------------------------------------------------------------
Light Control:
    --on 'light_name'
            Turns on light by name.

    --off 'light_name'
            Turns off light by name.

    --group-on 'group_name'
            Turns on all lights in group by name

    --group-off 'group_name'
            Turns off all lights in group by name
    
    --set-bsh 'light_name|brightness;saturation;hue'
            Sets brightness, saturation and hue for light by name.
            Brightness and saturation values are percentages.
            Hue value is between 0 and 65535.
    
    --set-bsh-group 'group_name|brightness;saturation;hue'
            Similar to --set-bsh.
            Sets brightness, saturation and hue for a group.
    
    --inc-bsh 'light_name|brightness;saturation;hue'
            Increments brightness, saturation and hue of a light by name.
            Brightness and Saturation increments in are percentages.
            Hue increment is between 0 and 65535
            
    --inc-bsh-group 'group_name|brightness;saturation;hue'
            Similar to --inc-bsh.
            Increments brightness, saturation and hue for a group.
            
"""
  print(help_str)

def get_input_params():
  """Gets input parameters and manages special commands
  
  Returns:
    Tuple containing information on input parameters
  """
  
  bridge_name = None
  action = None
  params = None

  for index, element in enumerate(sys.argv):
    if element == "--help" or element == "-h":
      print_help()
      return None, None, None
    elif element == "--show-bridges":
      for bridge_file in os.scandir("bridges"):
        print(bridge_file.name.strip(".json"))
        return None, None, None
    elif element == "--init-bridge":
      bridge_name = get_next(sys.argv, element)
      ip = get_next(sys.argv, bridge_name)
      bridge = HueBridge(bridge_name, ip)
      bridge.serialize()
      print(f"Created Hue Bridge {bridge_name} at IP {ip}")
      return None, None, None
    else:
      if element == "-b":
        bridge_name = get_next(sys.argv, element)
          
      if element == "--show-lights":
        action = "SHOWLIGHTS"
        params = None
        break
          
      if element == "--show-groups":
        action = "SHOWGROUPS"
        params = None
        break
        
      if element == "--on":
        action = "TURNON"
        params = get_next(sys.argv, element).split(";")
        break

      if element == "--off":
        action = "TURNOFF"
        params = get_next(sys.argv, element).split(";")
        break
    
      if element == "--create-group":
        action = "CREATEGROUP"
        group_name, lights = get_next(sys.argv, element).split("|")
        params = [group_name, lights.split(";")]
        break
      
      if element == "--remove-group":
        action = "REMOVEGROUP"
        params = get_next(sys.argv, element)
        break
    
      if element == "--group-on":
        action = "GROUPON"
        params = get_next(sys.argv, element)
        break
    
      if element == "--group-off":
        action = "GROUPOFF"
        params = get_next(sys.argv, element)
        break
      
      if element == "--set-bsh":
        action = "SETBSH"
        light_name, l_params = get_next(sys.argv, element).split("|")
        params = [light_name, l_params.split(";")]
        break
      
      if element == "--set-bsh-group":
        action = "SETBSHGROUP"
        group_name, l_params = get_next(sys.argv, element).split("|")
        params = [group_name, l_params.split(";")]
        break
      
      if element == "--inc-bsh":
        action = "INCBSH"
        light_name, inc_params = get_next(sys.argv, element).split("|")
        params = [light_name, inc_params.split(";")]
        break
      
      if element == "--inc-bsh-group":
        action = "INCBSHGROUP"
        group_name, inc_params = get_next(sys.argv, element).split("|")
        params = [group_name, inc_params.split(";")]
        break
      
  return bridge_name, action, params

def main():
  """Manages command line input obtained through get_input_params
  
  Sanitizes values input values and calls hue bridge functions
  to control lights and output information on hue bridge
  
  Returns:
    None
  """
  bridge_name, action, params = get_input_params()
  if bridge_name:
      bridge = HueBridge(bridge_name)
      # Creating lockfile to prevent simultateous access to hue bridge
      project_dir = os.path.abspath(os.path.dirname(__file__))
      lockfile_path = f"{project_dir}/bridges/{bridge_name}.lck"
      print(lockfile_path)
      if not os.path.isfile(lockfile_path):
        with open(lockfile_path, "w+") as lck_file:
          lck_file.write(f"{bridge_name} is locked!")
        if action == "TURNON":
            bridge.set_light_on(params)
        if action == "TURNOFF":
            bridge.set_light_off(params)
        if action == "GROUPON":
            bridge.set_group_on(params)
        if action == "GROUPOFF":
            bridge.set_group_off(params)
        
        # removes "" values and replaces them with none, so nothing is changed
        if "BSH" in action:
          light_vals = params[1]
          for index, val in enumerate(light_vals):
            try:
              light_vals[index] = int(val)
            except ValueError:
              light_vals[index] = None
          # setting actions
          if action == "SETBSH":
            bridge.set_bri_sat_hue([params[0]], brightness=light_vals[0], saturation=light_vals[1], hue=light_vals[2])
          elif action == "SETBSHGROUP":
            bridge.group_set_bri_sat_hue(params[0], brightness=light_vals[0], saturation=light_vals[1], hue=light_vals[2])
          # incrementing actions
          elif action == "INCBSH":
            bridge.increment_light([params[0]], brightness_inc=light_vals[0], saturation_inc=light_vals[1], hue_inc=light_vals[2])
          elif action == "INCBSHGROUP":
            bridge.increment_group(params[0], brightness_inc=light_vals[0], saturation_inc=light_vals[1], hue_inc=light_vals[2])
        
          
        if action == "CREATEGROUP":
            try:
                print(params)
                bridge.create_group(*params)
            except KeyError:
                print("Correct Usage: -b hue_bridge --create-group 'group_name|light_1;light_2;...")
        if action == "REMOVEGROUP":
            bridge.remove_group(params)
        
        if action == "SHOWLIGHTS":
            for light in bridge.lights:
                print(bridge.lights[light])
        if action == "SHOWGROUPS":
            for group in bridge.groups:
                print(f"{group:>15}: {bridge.groups[group]}")
        os.remove(lockfile_path)
        
if __name__ == "__main__":
    main()
