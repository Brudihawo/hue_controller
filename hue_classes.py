#!/usr/bin/python
import sys, os
import requests
import json

from hue_util import map_linear, cutoff_val


class BaseMessageError(Exception):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class SignInError(BaseMessageError):
  pass


class SerializeError(BaseMessageError):
  pass

class LightParamError(BaseMessageError):
  pass

class NetworkObject:
  """
  A network object with http request functionality
  """
    
  def __init__(self, ip, name):
    """Initialization from ip and name
    
    Returns:
      None
    """
    self.ip = ip.strip("/") + "/"
    self.name = name

  def __repr__(self):
    """Representation of self
    
    Returns:
      Representation of self as string
    """
    return f"Object <NetworkObject>({self.name},{self.ip})"
    
  def __str__(self):    
    """Representation of self
    
    Returns:
      Representation of self as string
    """
    return f"Network Object {self.name} at {self.ip}"

  def post(self, subadress, data=None):
    """Execute a http POST request at self.ip/subadress with payload data
    
    Args:
      subadress (str): Subadress for request
      data (dict): JSON Data to send
    
    Returns:
      requests http response
    """
    response = requests.post(f"{self.ip}{subadress}", json=data)
    return response

  def get(self, subadress):
    """Execute a http GET request at self.ip/subadress with payload data
    
    Args:
      subadress (str): Subadress for request
    
    Returns:
      requests http response
    """
    response = requests.get(f"{self.ip}{subadress}")
    return response

  def put(self, subadress, data):
    """Execute a http PUT request at self.ip/subadress with payload data
    
    Args:
      subadress (str): Subadress for request
      data (dict): JSON Data to send
    
    Returns:
      requests http response
    """
    response = requests.put(f"{self.ip}{subadress}", json=data)
    return response


class HueBridge(NetworkObject):
  """
  Object representation of a hue bridge.
  """
    
  def __init__(self, name, ip=None):
    """Initializes hue Bridge
    
    Args:
      name (str): name of the Hue Bridge
      ip (str): network ip of Hue Bridge

    Returns:
      None

    Raises:
      SignInError if no ip is provided and no config file for hue bridge name exists

    """

    self.lights = {}
    self.username = None
    self.groups = {}
    self.scenes = {}
    
    project_loc = os.path.dirname(__file__)
    try:
      os.mkdir(f"{project_loc}/bridges")
    except FileExistsError:
      pass

    # Try loading existing JSON configuration file first
    try:
      with open(f"{project_loc}/bridges/{name}.json", "r") as json_file:
        load = json.load(json_file)
        self.username = load["username"]
        self.ip = load["ip"]
        self.lights = self.get_lights()
        self.name = name
        try:
          self.groups = load["groups"]
        except KeyError:
          pass
        try:
          self.scenes = load["scenes"]
        except KeyError:
          pass
        
        self.serialize()
        ip = load["ip"]
          
    # If it does not exist, get information from Hue Bridge
    # Note that the Sync-Button needs to have been pressed for this to work
    except FileNotFoundError:
      if not ip:
        raise SignInError("Sign in Failed", "Cannot sign in without ip!")
      if not ip.startswith("http://"):
        ip = f"http://{ip}"
      ip = f"{ip.strip('/')}/"
      self.ip = ip
      self.username = self.get_auth()
      self.lights = self.get_lights()
    super().__init__(ip, name)
  
  def __repr__(self):
    """Representation of self
    
    Returns:
      Representation of self as string in format Object <HueBridge>()
    """
    return f"Object <HueBridge> ({self.name}, {self.ip})"
  
  def __repr__(self):
    """String representation of self
    
    Returns:
      Representation of self as string in format <HueBridge> (ip|name)
    """
    return f"Hue Bridge {self.name} at {self.ip}"
  
  def get_auth(self):
    """Gets Authentification information from Hue Bridge via http request.
    
    Returns:
      None

    Raises:
      SignInError if the Hue Bridge did not return a success message
    """
    lights_response = self.post("api", data={"devicetype": "hue_controller"})
    if "link button not pressed" in lights_response.text:
      raise SignInError("Sign In Failed", "Press sync button on Hue Bridge and try again!")  
    elif "success" in lights_response.text:
      response_data = lights_response.json()
      username = response_data[0]["success"]["username"]
      print(f"Success! Signed in with username {self.username}")
      return username
    else:
      raise SignInError("Sign In Failed", "An unknown error occurred!")
  
  def get_lights(self):
    """Gets information on lights connected to hue bridge
    
    Returns:
      Dict mapping light names to light numbers of Hue Bridge

    Raises:
      SignInError if no username is set when trying to access lights
    """
    if not self.username:
      raise SignInError("Order of Operations", "Anmeldung vor Lichtabfrage durchführen!")
    else:
      lights_data = self.get(f"api/{self.username}/lights").json()
      light_dict = {}
      for light in lights_data.keys():
        light_dict.update({lights_data[light]["name"]: light})
    return light_dict

  def serialize(self):
    """Saves Information on Hue Bridge to bridges/bridge_name.json in JSON format.
    
    Returns:
      None

    Raises:
      SerializeError if Hue Bridge is not fully initialized at time of serialization.
    """
    if not self.ip or not self.username or not self.lights or not self.name:
      raise SerializeError("Missing Information", "Cannot serialize uninitialized hue bridge!")
    out = {"ip": self.ip, "username": self.username, "lights": self.lights, "groups": self.groups, "scenes": self.scenes}
    project_loc = __file__.strip("hue_classes.py")
    with open(f"{project_loc}/bridges/{self.name}.json", "w") as json_file:
      json.dump(out, json_file)
  
  def set_light_on(self, names):
    """Turns lights on by name
    
    Args:
      names (list): List of light names
    
    Returns:
      None
    """
    for light_name in self.lights:
      if light_name in names:
        response = self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state", data={"on":True})

  def set_light_off(self, names):
    """Turns lights off by name
    
    Args:
      names (list): List of light names
    
    Returns:
      None
    """
    for light_name in self.lights:
      if light_name in names:
        response = self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state", data={"on":False})

  def get_light_names(self):
    """Gets light names
    
    Returns:
      List of lights (names) connected to hue bridge
    """
    return self.get_lights().keys()
  
  def create_group(self, group_name, light_names):
    """Creates a group of lights with given name
    
    Args:
      group_name (str): Name of the group
      light_names (list): List containing light names

    Returns:
      None
    """
    group = []
    for light_name in light_names:
      if light_name in self.lights:
        group.append(light_name)
      else:
        print(f"Could not find light: {light_name}. Skipped when creating group {group_name}.")
    print(group)
    self.groups.update({group_name: group})
    self.serialize()

  def remove_group(self, group_name):
    """Removes group by name
    
    Args:
      group_name (str): Name of group to remove

    Returns:
      None
    """
    try:
      removed = self.groups.pop(group_name)
    except KeyError:
      print(f"Cannot remove non-existant group {group_name}!")
    else:
      print(f"Removed group {group_name}({str(removed)})")

    self.serialize()
  
  def set_group_on(self, group_name):
    """Turns on all lights in a group
    
    Args:
      group_name (str): Name of the group to turn on

    Returns:
      None

    Raises:
      KeyError if group does not exist
    """
    self.set_light_on(self.groups[group_name])

  def set_group_off(self, group_name):
    """Turns off all lights in a group
    
    Args:
      group_name (str): Name of the group to turn off

    Returns:
      None

    Raises:
      KeyError if group does not exist
    """
    self.set_light_off(self.groups[group_name])

  def set_bri_sat_hue(self, light_names, brightness=None, saturation=None, hue=None):
    """Sets light settings by name
    
    Args:
      light_names (list): Names of lights to modify
      brightness (int or float): Optional, brightness of lights (in percent) between 0 and 100
      saturation (int or float): Optional, saturation of lights (in percent) between 0 and 100
      hue (int or float): Optional, hue of lights between 0 and 65535
      
    Returns:
      None
    """
    # value cleanup
    if brightness:
      brightness = int(map_linear(cutoff_val(brightness, 0, 100), 0, 100, 0, 254))
    if saturation:
      saturation = int(map_linear(cutoff_val(saturation, 0, 100), 0, 100, 0, 254))
    if hue:
      hue = cutoff_val(hue, 0, 65535)
    
    # parsing to parameter dict
    params = {}
    if type(brightness) == int:
      params.update({"bri": brightness})
    if type(saturation) == int:
      params.update({"sat": saturation})
    if type(hue) == int:
      params.update({"hue": hue})
    for light_name in light_names:
      if params["bri"] <= 0:
        self.set_light_off(light_name)
      else:
        self.set_light_on(light_name)
      self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state", data=params)
      
  def group_set_bri_sat_hue(self, group_name, brightness=None, saturation=None, hue=None):
    """Sets brightness, saturation and hue of lighting group
    
    Args:
      group_name (str): Name of group to modify
      brightness (int or float): Optional, brightness of lights (in percent) between 0 and 100
      saturation (int or float): Optional, saturation of lights (in percent) between 0 and 100
      hue (int or float): Optional, hue of lights between 0 and 65535
      
    Returns:
      None
    """
    self.set_bri_sat_hue(self.groups[group_name], brightness=brightness, saturation=saturation, hue=hue)

  def get_light_states(self):
    """Gets current state of all lights connected to hue bridge
    
    Returns:
      light_states: Dict mapping light state (brightness, saturation, hue) to light
    """
    raw_json_light_data = self.get(f"api/{self.username}/lights").json()
    light_states = {}
    for light_name, light_id in self.lights.items():
      light_state = raw_json_light_data[light_id]["state"]
      tmp_dict = {}
      if "bri" in light_state:
        tmp_dict.update({"brightness": int(light_state["bri"])})
      if "sat" in light_state:
        tmp_dict.update({"saturation": int(light_state["sat"])})
      if "hue" in light_state:
        tmp_dict.update({"hue": int(light_state["hue"])})
      light_states.update({light_name: tmp_dict})
    return light_states
  
  def increment_light(self, names, brightness_inc=None, saturation_inc=None, hue_inc=None):
    """Increments light parameters of lights by name
    
    Increments light paramters of a list of lights. Note that the same increments will be applied to all lights.
    Initially different light states of lights in a group will result in different states after increment.
    Brightness and Saturation are capped at 100, hue is capped at 65535
    
    Args:
      names (list): Names of lights to increment_light
      brightness_inc (int): Percentage brightness increment
      saturation_inc (int): Percentage saturation increment
      hue_inc (int): Absolute hue increment between 0 and 65535
    
    Returns:
      None
      
    Raises:
      LightParamError if the light does not support the parameter you want to set
    """
    light_states = self.get_light_states()
    for name in names:
      if name in light_states:
        for param, inc in zip(["brightness", "saturation", "hue"], [brightness_inc, saturation_inc, hue_inc]):
          if inc:
            if param not in light_states[name]:
              raise LightParamError("Nonsupported Parameter", f"Cannot set parameter {param} for light {name}")
            if param == "hue":
              light_states[name][param] = light_states[name][param] + inc
            else:
              light_states[name][param] = map_linear(light_states[name][param], 0, 255, 0, 100) + inc
        if light_states[name]["brightness"] <= 0:
          self.set_light_off([name])
        else:
          self.set_light_on([name])
        self.set_bri_sat_hue([name], **light_states[name])
        
  def increment_group(self, group_name, brightness_inc=None, saturation_inc=None, hue_inc=None):
    """Increments all lights in group by same values
    
    Increments light paramters of a group. Note that the same increments will be applied to all lights.
    Initially different light states of lights in a group will result in different states after increment.
    Brightness and Saturation are capped at 100, hue is capped at 65535
    
    Turns light off if brightness reaches 0 and turns light on otherwise
    
    Args:
      group_name (str): Names of lights to increment_light
      brightness_inc (int): Percentage brightness increment
      saturation_inc (int): Percentage saturation increment
      hue_inc (int): Absolute hue increment between 0 and 65535
    
    Returns:
      None
      
    Raises:
      KeyError if group does not exist
    """
    self.increment_light(self.groups[group_name], brightness_inc=brightness_inc, saturation_inc=saturation_inc, hue_inc=hue_inc)
    
  def load_scene_file(name, file_path):
    """Loads JSON scene file for easier scene persistence
    
    Scene file needs to be in format:
    {"scene_name1": 
      {"light1": {"bri": brightness1, "sat": saturation1, "hue": hue1},
       "light2": {"bri": brightness2, "sat": saturation2, "hue": hue2}
       ...
      },
    {"scene_name2": ...}
    }
    
    Args:
      file_path (str): Path to scene file
      
    Returns:
      None
    """
    with open(file_path, "w") as scene_file:
      scenes = json.load(scene_file)
      for scene in scenes:
        self.scenes.append({scene: scenes[scene]})
      self.serialize()

  def activate_scene(self, scene_name):
    """Sets light states according to scene
    
    Prints an error message if that scene does not exist
    
    Args:
      scene_name (str): Name of Scene to activate
      
    Returns:
      None
    """
    if scene_name in self.scenes:
      for light in self.scenes[scene_name]:
        lightinfo = self.scenes[scene_name][light]
        self.set_bri_sat_hue(light, lightinfo["bri"], lightinfo["sat"], lightinfo["hue"])
    self.serialize()

  def remove_scene(self, scene_name):
    """Removes scene from saved scenes
    
    Args:
      scene_name (str): Name of scene to remove
    
    Returns:
      None
    """
        try:
      removed = self.groups.pop(scene_name)
    except KeyError:
      print(f"Cannot remove non-existant scene {scene_name}!")
    else:
      print(f"Removed scene {scene_name}({str(removed)})")
    self.serialize()
