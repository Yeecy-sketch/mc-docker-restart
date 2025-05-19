"""
Script to restart itzg/minecraft-server docker container at schedule while 
still waiting for players to log off.

Required Arguments:
 --server-name container_name

By default it waits for players to log off forever until it can restart
"""

import subprocess
import logging
import time
import pathlib
import sys
import argparse

# parse args #
parser = argparse.ArgumentParser(
        description="restarts the minecraft server at schedule if no players are online.",
    )

parser.add_argument(
        '-sn', '--server-name',
        help="container_name in the docker compose",
        dest="server_name",
        type=str,
        required=True
    )

parser.add_argument(
        '-w', '--wait',
        help="Keep waiting until players log off to restart the server",
        dest="wait",
        type=bool,
        action=argparse.BooleanOptionalAction,
        required=False
    )

parser.add_argument(
        '-aw', '--announce-waiting',
        help="if we're waiting on player to log off for restart, announce every hour",
        dest="announce",
        type=bool,
        action=argparse.BooleanOptionalAction,
        required=False
    )

parser.add_argument(
        '-mw', '--max-wait',
        help="The maximum amount of time to wait in minutes for players to log off, -1 to wait forever",
        dest="max_wait",
        type=int,
        default=-1,
        required=False
    )

args = parser.parse_args()
# parse args #


# constants
SERVER_NAME = args.server_name
WAIT = args.wait
ANNOUNCE = args.announce
MAX_WAIT = args.max_wait
# constants


# MESSAGES #
MESSAGE_WAITING_ON_RESTART = "Server will restart when all players log off."

MESSAGE_RESTARTING_IN_5_MINS = "Server will restart in 5 mins!"
MESSAGE_RESTARTING_IN_1_MIN = "Server will restart in 1 min!"
MESSAGE_RESTARTING_IN_30_SEC = "Server will restart in 30 seconds!"
MESSAGE_RESTARTING_NOW = "Server is restarting NOW!"
# MESSAGES #

COMMAND_STOP = "stop"
SAY_COMMAND = "say {}"

# logging #
logger = logging.getLogger(__name__)

logpath = pathlib.Path('.')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    # log to file and stdout at the same time
    handlers=[
        logging.FileHandler(logpath.joinpath('restarts.log'), mode='a', encoding=None, delay=False),
        logging.StreamHandler(sys.stdout)
    ]
)
# logging #

def is_server_up() -> bool:
    """
    returns true if server is up, false otherwise
    """
    res, code = run_server_cmd('whitelist')

    if code != 0:
        return False

    return True

def run_server_cmd(command: str) -> tuple[str, int]:
    """
    runs a command on the server, 
    returns the result and exit code
    """
    shell_cmd = ['docker', 'exec', SERVER_NAME, 'rcon-cli']

    if ' ' in command:
        for i in command.split(' '):
            shell_cmd.append(i)
    else:
        shell_cmd.append(command)

    out = subprocess.run(shell_cmd, stdout=subprocess.PIPE)
    result_str = out.stdout.decode('utf-8')

    return result_str, out.returncode


def player_count() -> int:
    """
    returns the amount of players online
    """

    result, _ = run_server_cmd('list')

    # result is something like
    # 'There are 0 of a max of 20 players online: \n'

    return int(str(result)[10:].split(' ', maxsplit=1)[0])

def shutdown_with_notice(took_to_long: bool = False) -> None:
    """
    restart server but give players 5 mins with notices to leave.
    """
    if took_to_long:
        logger.info(f"The server '{SERVER_NAME}' reached the maximum amount of time to wait for players to log off ({MAX_WAIT} mins), {player_count()} players online. Commencing Restart Sequence.")
    else:
        logger.info(f"Restarting server '{SERVER_NAME}' with {player_count()} players online.")

    run_server_cmd(SAY_COMMAND.format(MESSAGE_RESTARTING_IN_5_MINS))
    time.sleep(60*4)
    run_server_cmd(SAY_COMMAND.format(MESSAGE_RESTARTING_IN_1_MIN))
    time.sleep(30)
    run_server_cmd(SAY_COMMAND.format(MESSAGE_RESTARTING_IN_30_SEC))
    time.sleep(30)
    run_server_cmd(SAY_COMMAND.format(MESSAGE_RESTARTING_NOW))
    time.sleep(2)
    run_server_cmd(COMMAND_STOP)


if not is_server_up():
    logger.info(f"Server '{SERVER_NAME}' wasn't up in the first place, exiting!")
    sys.exit(1)

if player_count() == 0:
    # we run stop and rely on containers restart policy
    run_server_cmd(COMMAND_STOP)
    logger.info(f"Successfully restarted server '{SERVER_NAME}' with 0 players online, had to wait 0 mins!")
    sys.exit(0)


counter_mins = 1

while WAIT:
    time.sleep(60)

    #  check uptime
    if not is_server_up():
        logger.info(f"Server '{SERVER_NAME}' went offline while waiting for players to log off, had waited for {counter_mins} mins!")
        sys.exit(1)

    # no players?
    if player_count() == 0:
        # we run stop and rely on containers restart policy
        run_server_cmd(COMMAND_STOP)
        logger.info(f"Successfully restarted server '{SERVER_NAME}' with 0 players online, have waited for {counter_mins} mins!")
        sys.exit(0)

    # if we have waited too long
    if MAX_WAIT != -1 and counter_mins >= MAX_WAIT:
        shutdown_with_notice(True)
        sys.exit(0)

    # message every hour
    if counter_mins % 60 == 0 or counter_mins == 1:
        logger.info(f"Still waiting to restart server '{SERVER_NAME}', {player_count()} players online, have waited for {counter_mins} mins!")
        run_server_cmd(SAY_COMMAND.format(MESSAGE_WAITING_ON_RESTART))

    counter_mins += 1
