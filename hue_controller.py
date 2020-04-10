#!/usr/bin/python
import sys, os
import requests
import json
import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt="%(asctime)s: %(levelname)8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

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
                self.lights = load["lights"]
                try:
                    self.groups = load["groups"]
                except KeyError:
                    pass
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
                light_dict.update({light: lights_data[light]["name"]})
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
        for light_id, light_name in self.lights.items():
            if light_name in names:
                response = self.put(f"api/{self.username}/lights/{light_id}/state", data={"on":True})

    def set_light_off(self, names):
        """Turns lights off by name
        Args:
            names: List of light names
        
        Returns:
            None
        """
        for light_id, light_name in self.lights.items():
            if light_name in names:
                response = self.put(f"api/{self.username}/lights/{light_id}/state", data={"on":False})
    
    def get_light_names(self):
        """Gets light names
        Returns:
            List of lights (names) connected to hue bridge
        """
        return [self.get_lights()[key] for key in self.get_lights()]
    
    def set_light_brightness(self, name):
        """Sets light brightness by name
        Returns:
            None
        """
        pass

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
        try:
            removed = self.groups.pop(group_name)
        except KeyError:
            print(f"Cannot remove non-existant group {group_name}!")
        else:
            print(f"Removed group {group_name}({str(removed)})")

        self.serialize()
    
    def get_groups(self):
        return self.groups
    
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
    
   

def get_next(arr, elem):
    try:
        return arr[arr.index(elem) + 1]
    except IndexError:
        return None


def get_input_params():
    """Gets input parameters
    Return:
        Tuple containing information on input parameters
    """
    
    bridge_name = None
    action = None
    params = None


    for index, element in enumerate(sys.argv):
        if element == "--help" or element == "-h":
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
"""
            print(help_str)
            return None, None, None
        elif element == "--show-bridges":
            for bridge_file in os.scandir("bridges"):
                print(bridge_file.name.strip(".json"))
                return None, None, None
        elif element == "--init-bridge":
            bridge_name = get_next(sys.argv, element)
            ip = get_next(sys.argv, bridge)
            bridge = HueBridge(name, ip)
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
    
    return bridge_name, action, params

def main():
    bridge_name, action, params = get_input_params()   
    if bridge_name:
        bridge = HueBridge(bridge_name)
    
        if action == "TURNON":
            bridge.set_light_on(params)
        if action == "TURNOFF":
            bridge.set_light_off(params)
        if action == "GROUPON":
            bridge.set_group_on(params)
        if action == "GROUPOFF":
            bridge.set_group_off(params)

        if action == "CREATEGROUP":
            try:
                bridge.create_group(params[0], params[1])
            except KeyError:
                print("Correct Usage: -b hue_bridge --create-group 'group_name|light_1;light_2;...")
        if action == "REMOVEGROUP":
            bridge.remove_group(params)
        
        if action == "SHOWLIGHTS":
            for light in bridge.get_lights():
                print(light)
        if action == "SHOWGROUPS":
            for group in bridge.groups:
                print(f"{group:>10}:{bridge.groups[group]}")

if __name__ == "__main__":
    main()
