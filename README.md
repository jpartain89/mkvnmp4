# mkvnmp4

Script to remove duplicated .mkv files from a media server.

## How to install

1. Create a configuration file containing the directories you want the program to search. The program looks for the config in the following locations (in order):
   1. `/etc/mkvnmp4.conf`
   2. `~/.mkvnmp4.conf`
   3. `~/.config/mkvnmp4.conf`

2. Place the directories (one per line) in the config file. For example:

   /media/movies
   /media/tv

3. From the project directory, run the script. It will attempt to install/auto-link itself to `/usr/local/bin` if appropriate.

## Usage

1. Run the `mkvnmp4` command from the shell.
2. The script will search the configured directories and handle duplicated `.mkv` files according to the program's logic.

## Notes

- Make sure the config file is readable by the user running the script.
- Back up important files before running the script on production data.
