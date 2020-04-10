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


class NetworkObject:
  """
  A network object
  """
    
  def __init__(self, ip, name):
    self.ip = ip.strip("/") + "/"
    self.name = name

  def __repr__(self):
    return f"Network Object {self.name} at {self.ip}"
    
  def __str__(self):
    return f"Network Object {self.name} at {self.ip}"

  def post(self, subadress, data=None):
    response = requests.post(f"{self.ip}{subadress}", json=data)
    return response

  def get(self, subadress):
    response = requests.get(f"{self.ip}{subadress}")
    return response

  def put(self, subadress, data):
    response = requests.put(f"{self.ip}{subadress}", json=data)
    return response


class HueBridge(NetworkObject):
  """
  Object representation of a hue bridge.
  """
    
  def __init__(self, name, ip=None):
    """Initializes hue Bridge
    Args:
      name: name of the Hue Bridge
      ip: network ip of Hue Bridge

    Returns:
      None

    Raises:
      SignInError if no ip is provided and no config file for hue bridge name exists

    """

    self.lights = {}
    self.username = None
    self.groups = {}

    try:
      os.mkdir("bridges")
    except FileExistsError:
      pass

    # Try loading existing JSON configuration file first
    try:
      with open(f"bridges/{name}.json", "r") as json_file:
        load = json.load(json_file)
        self.username = load["username"]
        self.ip = load["ip"]
        self.lights = self.get_lights()
        self.name = name
        try:
          self.groups = load["groups"]
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
      logging.info(f"Success! Signed in with username {self.username}")
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
    out = {"ip": self.ip, "username": self.username, "lights": self.lights, "groups": self.groups}
    with open(f"bridges/{self.name}.json", "w") as json_file:
      json.dump(out, json_file)
  
  def set_light_on(self, names):
    """Turns lights on by name
    Args:
      names: List of light names
    
    Returns:
      None
    """
    for light_name in self.lights:
      if light_name in names:
        response = self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state", data={"on":True})

  def set_light_off(self, names):
    """Turns lights off by name
    Args:
      names: List of light names
    
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
      group_name: Name of the group
      light_names: List containing light names

    Returns:
      None
    """
    group = []
    for light_name in light_names:
      if light_name in self.lights.values():
        group.append(light_name)
      else:
        print(f"Could not find light: {light_name}. Skipped when creating group {group_name}.")
    self.groups.update({group_name: group})
    self.serialize()

  def remove_group(self, group_name):
    """Removes group by name
    Args:
      group_name: Name of group to remove

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
      group_name: Name of the group to turn on

    Returns:
      None

    Raises:
      KeyError if group does not exist
    """
    self.set_light_on(self.groups[group_name])

  def set_group_off(self, group_name):
    """Turns off all lights in a group
    Args:
      group_name: Name of the group to turn off

    Returns:
      None

    Raises:
      KeyError if group does not exist
    """
    self.set_light_off(self.groups[group_name])

  def set_bri_sat_hue(self, light_names, brightness=None, saturation=None, hue=None):
    """Sets light settings by name
    Args:
      light_names: Names of lights to modify
      brightness: Optional, brightness of lights (in percent) between 0 and 100
      saturation: Optional, saturation of lights (in percent) between 0 and 100
      hue: Optional, hue of lights between 0 and 65535
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
      self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state", data=params)
      
  def group_set_bri_sat_hue(self, group_name, brightness=None, saturation=None, hue=None):
    """Sets brightness, saturation and hue of lighting group
    Args:
      group_name: Name of group to modify
      brightness: Optional, brightness of lights (in percent) between 0 and 100
      saturation: Optional, saturation of lights (in percent) between 0 and 100
      hue: Optional, hue of lights between 0 and 65535
    Returns:
      None
    """
    self.set_bri_sat_hue(self.groups[group_name], brightness=brightness, saturation=saturation, hue=hue)
