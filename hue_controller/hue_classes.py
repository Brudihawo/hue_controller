"""Module Containing Class Representations of Hue and Network Objects."""
import os
import json
import requests

from .hue_util import map_linear, cutoff_val


class BaseMessageError(Exception):
    """Base Error with Message."""

    def __init__(self, expression, message):
        """Initialize Base Message Error.

        Parameters
        ----------
            expression : str
                         Error Title
            message : str
                      Error Message
        """
        super().__init__()
        self.expression = expression
        self.message = message


class SignInError(BaseMessageError):
    """Error On Sign in."""


class SerializeError(BaseMessageError):
    """Error on serialisation."""


class LightParamError(BaseMessageError):
    """Error with light parameters."""


class NetworkObject:
    """Network object with http request functionality."""

    def __init__(self, ip, name):
        """Initialize from ip and name."""
        self.ip = ip.strip("/") + "/"
        self.name = name

    def __repr__(self):
        """Return string representation of self.

        Returns
        -------
            Str
                Representation of self.
        """
        return f"Object <NetworkObject>({self.name},{self.ip})"

    def __str__(self):
        """Return string of self.

        Returns
        -------
            str
                Representation of self as string.
        """
        return f"Network Object {self.name} at {self.ip}"

    def post(self, subadress, data=None):
        """Execute a http POST request at self.ip/subadress with payload data.

        Parameters
        ----------
            subadress : str
                        Subadress for request.
            data : dict
                   JSON Data to send.

        Returns
        -------
            Requests HTTP response
                Response to HTTP post request.
        """
        response = requests.post(f"{self.ip}{subadress}", json=data)
        return response

    def get(self, subadress):
        """Execute a http GET request at self.ip/subadress with payload data.

        Parameters
        ----------
            subadress : str
                        Subadress for request

        Returns
        -------
            Requests HTTP response
                Response to HTTP  get request.
        """
        response = requests.get(f"{self.ip}{subadress}")
        return response

    def put(self, subadress, data):
        """Execute a http PUT request at self.ip/subadress with payload data.

        Parameters
        ----------
            subadress : str
                        Subadress for request
            data : dict
                   JSON Data to send

        Returns
        -------
            Requests HTTP response
                Response to HTTP put request.
        """
        response = requests.put(f"{self.ip}{subadress}", json=data)
        return response


class HueBridge(NetworkObject):
    """Object representation of a hue bridge."""

    HUE_FILE_LOCATION = f"{os.path.expanduser('~')}/.hue_controller"

    def __init__(self, name, ip=None):
        """Initialize hue Bridge.

        Parameters
        ----------
            name : str
                   name of the Hue Bridge
            ip : str
                 network ip of Hue Bridge

        Raises
        ------
            SignInError
                If no ip is provided and no config file for hue bridge name exists.
        """
        self.lights = {}
        self.username = None
        self.groups = {}

        try:
            os.mkdir(HueBridge.HUE_FILE_LOCATION)
        except FileExistsError:
            pass

        # Try loading existing JSON configuration file first
        try:
            with open(f"{HueBridge.HUE_FILE_LOCATION}/{name}.json", "r") as json_file:
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

    def __repr__(self):
        """Return string representation of self.

        Returns
        -------
            str
                Representation of self as string in format Object <HueBridge>().
        """
        return f"Object <HueBridge> ({self.name}, {self.ip})"

    def get_auth(self):
        """Get authentification information from Hue Bridge via http request.

        Raises
        ------
            SignInError
                If the Hue Bridge did not return a success message.
        """
        lights_response = self.post("api", data={"devicetype": "hue_controller"})
        if "link button not pressed" in lights_response.text:
            raise SignInError("Sign In Failed", "Press sync button on Hue Bridge and try again!")

        if "success" in lights_response.text:
            response_data = lights_response.json()
            username = response_data[0]["success"]["username"]
            print(f"Success! Signed in with username {self.username}")
            return username

        raise SignInError("Sign In Failed", "An unknown error occurred!")

    def get_lights(self):
        """Get information on lights connected to hue bridge.

        Returns
        -------
            Dict
                Mapping of light names to light numbers of Hue Bridge.

        Raises
        ------
            SignInError
                If no username is set when trying to access lights.
        """
        if not self.username:
            raise SignInError("Order of Operations", "Anmeldung vor Lichtabfrage durchführen!")

        lights_data = self.get(f"api/{self.username}/lights").json()
        light_dict = {}
        for light in lights_data.keys():
            light_dict.update({lights_data[light]["name"]: light})

        return light_dict

    def serialize(self):
        """Save Information on Hue Bridge to bridges/bridge_name.json in JSON format.

        Raises
        ------
            SerializeError
                If Hue Bridge is not fully initialized at time of serialization.
        """
        if not self.ip or not self.username or not self.lights or not self.name:
            raise SerializeError("Missing Information",
                                 "Cannot serialize uninitialized hue bridge!")
        out = {"ip": self.ip, "username": self.username,
               "lights": self.lights, "groups": self.groups}

        with open(f"{HueBridge.HUE_FILE_LOCATION}/{self.name}.json", "w") as json_file:
            json.dump(out, json_file)

    def set_light_on(self, names):
        """Turn on light(s) by name.

        Parameters
        ----------
            names (str[]): List of light names
        """
        for light_name in self.lights:
            if light_name in names:
                self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state",
                         data={"on": True})

    def set_light_off(self, names):
        """Turn off light(s) by name.

        Parameters
        ----------
            names (str[]): List of light names.

        """
        for light_name in self.lights:
            if light_name in names:
                self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state",
                         data={"on": False})

    def get_light_names(self):
        """Get light names.

        Returns
        -------
            str[]
                Light names connected to hue bridge.
        """
        return self.get_lights().keys()

    def create_group(self, group_name, light_names):
        """Create a group of lights with given name.

        Parameters
        ----------
            group_name : str
                         Group name.
            light_names : str[]
                          Light name list.

        """
        group = []
        for light_name in light_names:
            if light_name in self.lights:
                group.append(light_name)
            else:
                print(f"Could not find light: {light_name}. "
                      f"Skipped when creating group {group_name}.")
        print(group)
        self.groups.update({group_name: group})
        self.serialize()

    def remove_group(self, group_name):
        """Remove group by name.

        Parameters
        ----------
            group_name : str
                         Name of group to remove.

        """
        try:
            removed = self.groups.pop(group_name)
        except KeyError:
            print(f"Cannot remove non-existant group {group_name}!")
        else:
            print(f"Removed group {group_name}({str(removed)})")

        self.serialize()

    def set_group_on(self, group_name):
        """Turn on all lights in a group.

        Parameters
        ----------
            group_name : str
                         Name of the group to turn on.


        Raises
        ------
            KeyError
                If group does not exist.
        """
        self.set_light_on(self.groups[group_name])

    def set_group_off(self, group_name):
        """Turn off all lights in a group.

        Parameters
        ----------
            group_name : str
                         Name of the group to turn off.


        Raises
        ------
            KeyError
                If group does not exist.
        """
        self.set_light_off(self.groups[group_name])

    # TODO: fix to use only one set of if-statements
    def set_bri_sat_hue(self, light_names, brightness=None, saturation=None, hue=None):
        """Set light state by name.

        Parameters
        ----------
            light_names : str[]
                          Names of lights to modify
            brightness : numeric
                         Optional, brightness of lights (in percent) between 0 and 100.
            saturation : numeric
                         Optional, saturation of lights (in percent) between 0 and 100.
            hue : numeric
                  Optional, hue of lights between 0 and 65535.
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
        if isinstance(brightness, int):
            params.update({"bri": brightness})
        if isinstance(saturation, int):
            params.update({"sat": saturation})
        if isinstance(hue, int):
            params.update({"hue": hue})
        for light_name in light_names:
            if params["bri"] <= 0:
                self.set_light_off(light_name)
            else:
                self.set_light_on(light_name)
            self.put(f"api/{self.username}/lights/{self.lights[light_name]}/state",
                     data=params)

    def group_set_bri_sat_hue(self, group_name, brightness=None, saturation=None, hue=None):
        """Set brightness, saturation and hue of lighting group.

        Parameters
        ----------
            group_name : str
                         Name of group to modify.
            brightness : numeric
                         Optional, brightness of lights (in percent) between 0 and 100.
            saturation : numeric
                         Optional, saturation of lights (in percent) between 0 and 100.
            hue : numeric
                  Optional, hue of lights between 0 and 65535.
        """
        self.set_bri_sat_hue(self.groups[group_name], brightness=brightness,
                             saturation=saturation, hue=hue)

    def get_light_states(self):
        """Get current state of all lights connected to hue bridge.

        Returns
        -------
            Dict
               Mapping of light states (brightness, saturation, hue) to lights.
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
            if "on" in light_state:
                tmp_dict.update({"on": light_state["on"]})
            light_states.update({light_name: tmp_dict})
        return light_states

    def increment_light(self, names, brightness_inc=None, saturation_inc=None, hue_inc=None):
        """Increment light status by name.

        Increments light paramters of a list of lights.
        Note that the same increments will be applied to all lights.
        Initially different light states of lights in a group will
        result in different states after increment.
        Brightness and Saturation are capped at 100, hue is capped at 65535

        Parameters
        ----------
            names : str[]
                    Names of lights to increment_light.
            brightness_inc : int
                             Percentage brightness increment.
            saturation_inc : int
                             Percentage saturation increment.
            hue_inc : int
                      Absolute hue increment between 0 and 65535.

        Raises
        ------
            LightParamError
                If the light does not support the parameter you want to set.
        """
        light_states = self.get_light_states()
        for name in names:
            if name in light_states:
                for param, inc in zip(["brightness", "saturation", "hue"],
                                      [brightness_inc, saturation_inc, hue_inc]):
                    if inc:
                        if param not in light_states[name]:
                            raise LightParamError("Nonsupported Parameter",
                                                  f"Cannot set parameter {param} for light {name}")
                        if param == "hue":
                            light_states[name][param] = light_states[name][param] + inc
                        else:
                            light_states[name][param] = map_linear(light_states[name][param],
                                                                   0, 255, 0, 100) + inc
                if light_states[name]["brightness"] <= 0:
                    self.set_light_off([name])
                else:
                    self.set_light_on([name])
                try:
                    light_states[name].pop("on")
                except KeyError:
                    pass
                self.set_bri_sat_hue([name], **light_states[name])

    def increment_group(self, group_name, brightness_inc=None, saturation_inc=None, hue_inc=None):
        """Increment all lights in group by same values.

        Increments light paramters of a group.
        Note that the same increments will be applied to all lights.
        Initially different light states of lights in a group will
        result in different states after increment.
        Brightness and Saturation are capped at 100, hue is capped at 65535

        Turns light off if brightness reaches 0 and turns light on otherwise

        Parameters
        ----------
            group_name : str
                         Names of lights to increment_light.
            brightness_inc : int
                             Percentage brightness increment.
            saturation_inc : int
                             Percentage saturation increment.
            hue_inc : int
                      Absolute hue increment between 0 and 65535.

        Raises
        ------
            KeyError
                If group does not exist.
        """
        self.increment_light(self.groups[group_name], brightness_inc=brightness_inc,
                             saturation_inc=saturation_inc, hue_inc=hue_inc)

    def toggle_lights(self, light_names):
        """Toggle state of lights in light_names by name.

        Parameters
        ----------
            light_names : str[]
                          list containing names of all lights to toggle.
        """
        light_states = self.get_light_states()
        for light_name in light_names:
            try:
                light_on = light_states[light_name]["on"]
            except KeyError:
                print(f"Light '{light_name}' not connected to hue bridge")
            else:
                if light_on:
                    self.set_light_off(light_name)
                else:
                    self.set_light_on(light_name)

    def toggle_group(self, group_name):
        """Separately toggle whether a light is on or off for each light in the group.

        Does not set the state of each lamp separately. Each light will be toggled individually.

        Parameters
        ----------
            group_name : str
                         Name of group to toggle.
        """
        self.toggle_lights(self.groups[group_name])
