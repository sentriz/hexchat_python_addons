__module_name__ = "HexChat Away"
__module_version__ = "5.2"
__module_description__ = "Suffixes your nick and marks you away."
__author__ = "sentriz"

full_name = "{} v{} by {}".format(__module_name__,__module_version__,__author__)
help_AWAYCMD = """
              \"/hcaway {-s} {reason}\" will suffix your nick and mark you away.
              - {-s} (optional) is flag to be marked away on the current server only.
              - {reason} (optional) is the reason for being away. (can be used with -s)"""
help_BACKCMD = """
              \"/hcback {-s}\" will remove your nick\'s away suffix and mark you back.
              - {-s} (optional) is flag to be marked back on the current server only."""
str_prefix = "\00301[\002HexChat\002\00301 \00304\002Away\002\00301] \002:\002 \017"
away = False

import hexchat
import time

nick = ["sentriz", "[A]"] # default nick, and away suffix to be added to it
time_zone = "UTC0" # your home time-zone for away time
talk_threshold = 4 # number of times you can talk before you're set back

def away_cb(word, word_eol, userdata):
    global away, talk_count
    away_time = time.strftime("%b %d %Y %H:%M:%S") + " " + time_zone
    away_string = "\'{}\' at {}".format(full_name,away_time)
    reason_append, talk_count = "", 0
    
    if "-s" in word:
        if len(word) >= 3:
            away_string = "\'{}\' at {}".format(word_eol[2],away_time)
            reason_append = " Reason: \"{}\"".format(word_eol[2])
        hexchat.command("nick " + nick[0] + nick[1])
        hexchat.command("away " + away_string)
        away = True
        hexchat.prnt(str_prefix + "You're now away on the \002current\002 server." + reason_append)
        return hexchat.EAT_ALL
    else:
        if len(word) >= 2:
            away_string = "\'{}\' at {}".format(word_eol[1],away_time)
            reason_append = " Reason: \"{}\"".format(word_eol[1])
        hexchat.command("allserv nick " + nick[0] + nick[1])
        hexchat.command("allserv away " + away_string)
        away = True
        hexchat.prnt(str_prefix + "You're now away on \002all\002 servers." + reason_append)
        return hexchat.EAT_ALL

def back_cb(word, word_eol, userdata):
    global away
    if "-s" in word:
        hexchat.command("nick " + nick[0])
        hexchat.command("back")
        away = False
        hexchat.prnt(str_prefix + "You're now back on the \002current\002 server.")
        return hexchat.EAT_ALL
    else:
        hexchat.command("allserv nick " + nick[0])
        hexchat.command("allserv back")
        away = False
        hexchat.prnt(str_prefix + "You're now back on \002all\002 servers.")
        return hexchat.EAT_ALL

def autoback_cb(word, word_eol, userdata):
    global talk_count
    if away == True:
        talk_count += 1
        warning = "talked {}/{} times while away".format(talk_count,talk_threshold)
        print("* [" + warning + "]")
        if talk_count == talk_threshold: 
            hexchat.prnt(str_prefix + "You will be set back.. ({})".format(warning))
            hexchat.command(BACKCMD)

AWAYCMD, BACKCMD = "hcaway", "hcback" #because of autoback_cb
hexchat.hook_command(AWAYCMD,away_cb,help=help_AWAYCMD)
hexchat.hook_command(BACKCMD,back_cb,help=help_BACKCMD)
hexchat.hook_print("Your Message", autoback_cb)

hexchat.prnt(str_prefix + full_name + " loaded.")