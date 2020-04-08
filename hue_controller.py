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
        out = {"ip": self.ip, "username": self.username, "lights": self.lights}
        with open(f"bridges/{self.name}.json", "w") as json_file:
            json.dump(out, json_file)
    
    def set_light_on(self, name):
        """Turns light on by name
        Returns:
            None
        """
        for light_id, light_name in self.lights.items():
            if light_name == name:
                response = self.put(f"api/{self.username}/lights/{light_id}/state", data={"on":True})

    def set_light_off(self, name):
        """Turns light off by name
        Returns:
            None
        """
        for light_id, light_name in self.lights.items():
            if light_name == name:
                response = self.put(f"api/{self.username}/lights/{light_id}/state", data={"on":False})
    
    def get_light_names(self):
        """Gets light names
        Returns:
            List of lights (names) connected to hue bridge
        """
        return [self.get_lights()[key] for key in self.get_lights()]

def get_input_params():
    """Gets input parameters
    Return:
        Tuple containing information on input parameters
    """
    

    save = False
    ip = None
    name = None
    turn_on = None
    turn_off = None
    showlights = False

    for index, element in enumerate(sys.argv):
        if element.startswith("-"):
            if element == "--show-bridges":
                for bridge_file in os.scandir("bridges"):
                    print(bridge_file.name.strip(".json"))

            else:
                if element == "--show-lights":
                    showlights = True
                if element == "-s":
                    save = True
                if element == "-i":
                    ip = sys.argv[sys.argv.index(element) + 1]
                if element == "-n":
                    name = sys.argv[sys.argv.index(element) + 1]
                if element == "--on":
                    turn_on = sys.argv[sys.argv.index(element) + 1]
                if element == "--off":
                    turn_off = sys.argv[sys.argv.index(element) + 1]
    return save, ip, name, turn_on, turn_off, showlights

save, ip, name, turn_on, turn_off, showlights = get_input_params()

if name:
    if ip:
        bridge = HueBridge(name, ip)
    else:
        bridge = HueBridge(name)
    if save:
        bridge.serialize()

    if turn_on:
        bridge.set_light_on(turn_on)
    if turn_off:
        bridge.set_light_off(turn_off)
    if showlights:
        for light in bridge.get_light_names():
            print(light)
