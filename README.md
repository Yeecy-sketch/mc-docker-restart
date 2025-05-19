# README
An automatic restart script for itzg/minecraft-server docker container.
The script can wait until all players log off until it restarts the server.
Relies on container's restart policy to start back up.
Add something to trigger it daily, like crontab.

# Options

**Required**:

`--server-name` or `-sn`, the container_name in your compose.yml

**Optional**:

`--wait` or `-w`, wait until all players log off, defaults to false.

`--announce-waiting` or `-aw`, announce that the server is waiting for players to log off, defaults to false.

`--max-wait` or `-mw`, maximum amount of time to wait in minutes for players to log off, defaults to -1 (infinite)

# Customizing
In the python script under `# MESSAGES #` there are all the messages sent if `-aw` is set.

Used commands are under the messages if you need to use custom ones like `execute as server run say {}`.

# Logs
The default logging path is the working directory, named `restarts.log`.
change `logpath` variable for a custom log path.
