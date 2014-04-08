__module_name__ = "Hexchat Slap"
__module_version__ = "1.2"
__module_description__ = "A classic IRC '/slap' command."
__author__ = "sentriz"

full_name = "{} v{} by {}".format(__module_name__,__module_version__,__author__)
help = """
		\"/slap [nick]\" will slap a [nick].
		- Use \"/slap [nick] {nick2} {nick3} {ect.}\" to slap multiple nicks.
		- ^ There is no limit."""
str_prefix = "\00301[\002HexChat\002\00301 \00304\002Slap\002\00301] \002:\002 \017"

import hexchat

def slap_func(word, word_eol, userdata):
    if len(word) >= 2:
        for nick in word[1:]:
            hexchat.command("me slaps \002{}\002 around a bit with a large trout.".format(nick))
    else:
        hexchat.prnt(str_prefix + "Could not slap. " + help)
    return hexchat.EAT_ALL

hexchat.hook_command("slap",slap_func,help=help)
hexchat.prnt(str_prefix + full_name + " loaded.")