"""
hcaway - a HexChat plugin that suffixes your nick and marks you away
 - intelligently.
Copyright (C) 2014 Senan Kelly (sentriz)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the  Free Software  Foundation,  either version 3 of the License, or
(at your option) any later version.

This  program  is  distributed in the hope  that it  will be useful,
but  WITHOUT  ANY  WARRANTY;  without  even the  implied warranty of
MERCHANTABILITY  or  FITNESS  FOR  A  PARTICULAR  PURPOSE.   See the
GNU General Public License for more details.

You should have received  a  copy of the GNU General  Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
Also add information on how to contact you  by  electronic and paper
mail.
"""

__module_name__ = "HexChat Away"
__module_description__ = "Suffixes your nick and marks you away."
__module_version__ = "6.0"
__module_author__ = "sentriz"

__module_fullname__ = "{} v{} by {}" \
    .format(__module_name__, __module_version__, __module_author__)

str_prefix = \
    "\00301[\002{0}\002\00301 \00304\002{1}\002\00301] \017".format(
        *__module_name__.split())

help_AWAYCMD = \
    """\n"/hcaway {reason}" will suffix your nick and mark you away.
- {reason} (optional) is the reason for being away.\n"""

help_BACKCMD = \
    """\n"/hcback" will remove your nick's away suffix and mark you back.\n"""

help_MANCMD = \
    """\n"/hcam networks add"      add the current network to the list of accepted severs.
"/hcam networks remove {server name}"   remove current network from the list.
"/hcam networks addall {server name}"   add all networks to the list.
"/hcam networks clear"    clear the list of networks all accepted severs.
"/hcam networks list"     view the list of accepted networks.
"/hcam autoback set"      set the talk threshold of autoback.
"/hcam autoback disable"  disable the autoback feature.\n"""

import hexchat
import time

def error(msg = "wrong usage. help:" + help_MANCMD):
    hexchat.prnt(str_prefix + "error: " + msg)

#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#

class AutobackConfig:

    def __init__(self, talk_increment = 0):
        self.threshold = 0
        self.talk_count = talk_increment
        self.enabled = None

    def __enter__(self):
        self.threshold = int(   
            hexchat.get_pluginpref("hcaway_autoback__threshold"))
        self.enabled = bool(
            hexchat.get_pluginpref("hcaway_autoback__enabled"))
        self.talk_count += int(
            hexchat.get_pluginpref("hcaway_autoback__talk_count"))
        return self

    def __exit__(self, type, value, traceback):
        hexchat.set_pluginpref(
            "hcaway_autoback__threshold", str(self.threshold))
        hexchat.set_pluginpref(
            "hcaway_autoback__enabled", str(int(self.enabled)))
        hexchat.set_pluginpref(
            "hcaway_autoback__talk_count", str(self.talk_count))

    def set(self, value):
        try:
            self.threshold = int(value)
        except ValueError:
            error("please enter an integer.")
            return
        self.enabled = True
        hexchat.prnt(str_prefix + \
            "autoback talkthreshold set to \002{}\002.".format(value))
    def disable(self):
        self.enabled = False
        hexchat.prnt(str_prefix + "autoback disabled.")

class NetworkList:

    def __init__(self):
        self.networks = []

    def __enter__(self):
        self.networks = \
            hexchat.get_pluginpref("hcaway_networks").split(";")
        if "" in self.networks:
            self.networks.remove("")
        return self

    def __exit__(self, type, value, traceback):
        hexchat.set_pluginpref(
            "hcaway_networks", ";".join(self.networks))

    def _get_connected(self):
        return set(
            channel.network for channel in hexchat.get_list("channels"))

    def _get_away(self):
        for network in self.networks:
            if hexchat.find_context(server=network).get_info("away"):
                yield network

    def _get_back(self):
        for network in self.networks:
            if not hexchat.find_context(server=network).get_info("away"):
                yield network

    def list(self):
        all_networks = self._get_connected() | set(self.networks)
        
        hexchat.prnt(str_prefix + "network list:")
        for network in all_networks:
            try:
                context = hexchat.find_context(server=network)
                if context.get_info("away"):
                    colour = "\00304" # away
                elif not context.get_info("server"):
                    colour = "\00314" # loaded, not connected
                else:
                    colour = "\00303" # online
            except AttributeError:
                colour = "\00314"     # not loaded

            hexchat.prnt(
                "{indent}[{status}] {colour}\002{network:<10}\002\017".format(
                indent = " " * (len(hexchat.strip(str_prefix))),
                network = network,
                colour = colour,
                status = "√" if network in self.networks else "-"
                )
            )

    def add(self, network_name = None):
        network_name = network_name or hexchat.get_info("network")

        if network_name not in self.networks:
            self.networks += [network_name]
            hexchat.prnt(str_prefix + "added \002{}\002.".format(network_name))
        else:
            error("\002{}\002 already in network list.".format(network_name))

    def remove(self, network_name = None):
        network_name = network_name or hexchat.get_info("network")

        if network_name in self.networks:
            self.networks.remove(network_name)
            hexchat.prnt(
                str_prefix + "removed \002{}\002.".format(network_name))
        else:
            error("\002{}\002 not in network list.".format(network_name))

    def addall(self):
        self.networks = self._get_connected()
        hexchat.prnt(
            str_prefix + "all currently loaded added to network list.")

    def clear(self):
        self.networks = []
        hexchat.prnt(str_prefix + "cleared network list.")

#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#

def hcback_cb(word, word_eol, userdata):
    suffix = hexchat.get_pluginpref("hcaway_suffix")

    with NetworkList() as networks:
        # networks that the user is not away on
        whitelist = [network for network in networks.networks \
            if hexchat.find_context(server=network).get_info("away")]
        for network in whitelist:
            context = hexchat.find_context(server=network)
            context.command("nick {}".format(
                context.get_info("nick").replace(suffix, "")))
            context.command("back")

    if len(whitelist) >= 1:
        hexchat.prnt(str_prefix + "you're now back on \002{}\002.".format(
            ("\002, \002".join(whitelist[0:-1]) + \
                "\002 and \002" + whitelist[-1]) if len(whitelist) > 1 else \
                    (whitelist[0])))
    else:
        error("either you've no networks added to your whitelist, "
            "or you're already back on one or more of them.")

    return hexchat.EAT_ALL

def hcaway_cb(word, word_eol, userdata):
    away_time, reason = time.strftime("%H:%M (%b %d %Y) %z"), ""
    suffix = hexchat.get_pluginpref("hcaway_suffix")

    away_string = "'{}' at {}".format(__module_fullname__, away_time)
    if len(word) > 1:
        away_string = "'{}' at {}".format(word_eol[1], away_time)
        reason = " reason: \"{}\"".format(word_eol[1])

    with NetworkList() as networks:
        # networks that the user is not away on
        whitelist = list(networks._get_back())
        for network in whitelist:
            context = hexchat.find_context(server=network)
            context.command("nick {}{}".format(
                context.get_info("nick"), suffix))
            context.command("away " + away_string)

    if len(whitelist) >= 1:
        hexchat.prnt(str_prefix + "you're now away on \002{}\002.{}".format(
            ("\002, \002".join(whitelist[0:-1]) + "\002 and \002" + \
                whitelist[-1]) if len(whitelist) > 1 else (whitelist[0]), 
                    reason))
    else:
        error("either you've no networks added to your whitelist, "
            "or you're already away on one or more of them.")

    return hexchat.EAT_ALL

def autoback_cb(word, word_eol, userdata):

    with AutobackConfig() as autoback:
        enabled = autoback.enabled

    if enabled:
        current_network = hexchat.get_info("network")
        with NetworkList() as networks:
            away_networks = list(networks._get_away())

        if current_network in away_networks:
            # "AutobackConfig(1)", 1 to increment .talk_count
            with AutobackConfig(1) as autoback:
                hexchat.prnt(str_prefix + \
                    "\002warning:\002 you've talked " + \
                        "\002{}\002/\002{}\002 times while away.".format(
                            autoback.talk_count, autoback.threshold))
                if autoback.talk_count >= autoback.threshold:
                    hexchat.prnt(str_prefix + \
                        "You will be set back on network \002{}\002".format(
                            current_network))
                    autoback.talk_count = 0
                    suffix = hexchat.get_pluginpref("hcaway_suffix")
                    context = hexchat.find_context(server=current_network)
                    context.command("nick {}".format(
                        context.get_info("nick").replace(suffix, "")))
                    context.command("back")

    return hexchat.EAT_NONE

def hcam_cb(word, word_eol, userdata):

    # (eg.) "word" = ["hcam", "n", "list"]          (/hcam n list)
    # (eg.) "word" = ["hcam", "networks", "list"]   (/hcam networks list)
    # (eg.) "word" = ["hcam", "a", "set", "5"]      (/hcam a set 5)

    brains = None

    try:
        option, method = word[1:3]
    except IndexError:
        pass
    else:
        if option in ["networks", "n"]:
            brains = NetworkList()
        elif option in ["autoback", "a"]:
            brains = AutobackConfig()

    if brains:
        with brains:
            try:
                attr = getattr(brains, method)
                arguments = word[3:]
                attr(*arguments)
            # AttributeError for getattr(brains, <not existing in brain class>)
            # TypeError for attr(*<too many arguments being passed to method>)
            except (AttributeError, TypeError):
                error()
    else:
        error()

    return hexchat.EAT_ALL

#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#

def first_start_default_config():
    """
    > load default entries in addon_python.conf on first install
    * do not change anything in the dictionary, change addon_python.conf
        after running once.

    """
    config = {
        "autoback__threshold": "5",
        "autoback__enabled": "1",
        "autoback__talk_count": "0",
        "suffix": "[A]",
        "networks": ""
    }

    for key, value in config.items():
        full_key = "hcaway_" + key
        if not hexchat.get_pluginpref(full_key):
            hexchat.set_pluginpref(full_key, value)

hexchat.hook_command("hcaway", hcaway_cb, help=help_AWAYCMD)
hexchat.hook_command("hcback", hcback_cb, help=help_BACKCMD)
hexchat.hook_command("hcam", hcam_cb, help=help_MANCMD)
hexchat.hook_print("Your Message", autoback_cb)

first_start_default_config()

hexchat.prnt(str_prefix + __module_fullname__ + " loaded.")
