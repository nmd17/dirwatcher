import argparse
import os
import signal
import logging
import time
import sys
from datetime import datetime as dt

exit_flag = False
watched_files = {}

logger = logging.getLogger('__name__')
logging.basicConfig(format = '%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s [%(threadName)-12s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
, level=logging.DEBUG)


def create_parser():
    """Create an argument parser object"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir',
                        help='destination directory to monitor (defaults to current directory)',
                        default= '.')
    parser.add_argument('-x', '--ext', help='file extension to filter based on (defaults to .txt)',
                        default='.txt')
    parser.add_argument('-i', '--interval', help='interval to poll given directory at (defaults to 1 second',
                        default=5)
    parser.add_argument('magic', help='magic string to search files for within given directory')

    return parser


def scan_file(file_name, start_line, text):
    '''function for scanning a file and returning the final line number read'''

    final_line = 0
    line_number = 0

    with open(file_name) as f:
        for line_number, line in enumerate(f):
            if line_number >= start_line:
                if text in line:
                    logger.info('I found some magic text on line ' + str(line_number + 1))

    final_line = line_number + 1

    return final_line
    

def read_dir(current_dir, text):
    '''function for reading supplied directory'''

    try:
        file_list = os.listdir(current_dir)

        for file in file_list:
            if file not in watched_files:
                logger.info('New file named {} has been added'.format(file))
                watched_files[file] = 1


            for file in watched_files:
                if file not in file_list:
                    logger.info('This file has been deleted')
                    del watched_files[file]

            for file in watched_files:
                full_path = os.path.join(current_dir, file)
                final_line_read = scan_file(full_path, watched_files[file], text)
                watched_files[file] = final_line_read

        return watched_files

    except Exception as e:
        logger.info(e)


def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped here as well (SIGHUP?)
    Basically it just sets a global flag, and main() will exit it's loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    global exit_flag

    # log the associated signal name (the python3 way)
    logger.warning('Received ' + signal.Signals(sig_num).name)
    

    exit_flag = True

def main():
    # Creates argument parser
    parser = create_parser()
    args = parser.parse_args()

    # Hook these two signals from the OS .. 
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Now my signal_handler will get called if OS sends either of these to my process.

    start_time = dt.now()

    logger.info('Watching directory named {} every {} seconds checking for the word {}'.format(args.dir, args.interval, args.magic))
    while not exit_flag:
        try:
            # call my directory watching function..
            read_dir(args.dir, args.magic)
        except Exception as e:
            # This is an UNHANDLED exception
            # Log an ERROR level message here
            logger.error(e)

        # put a sleep inside my while loop so I don't peg the cpu usage at 100%
        time.sleep(args.interval)


    uptime = (dt.now()) - (start_time)

    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '   Stopped {}\n'
        '   Uptime was {}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, str(uptime)))
    
    # final exit point happens here
    # Log a message that we are shutting down
    # Include the overall uptime since program start.


if __name__ == "__main__":
    main()