#! /usr/bin/env python

# general imports
import argparse
import psutil
import math
import os
import time

# import ros libraries
from time import sleep

import rospy
from roslaunch import rlutil, parent
import roslaunch
from bot_controller import BotController
from constants import AdaptationLevel
from ready_db import ReadyDB
from launch_utils import *

commands = ["place_obstacle", "remove_obstacle", "set_charge", "execute_task", "go_directly", "execute_task_reactive",
            "execute_task_reactive_fancy"]

rosnode = "cp1_node"


def main():
    # bring up a ros node
    init(rosnode)
    bot = BotController()

    # track battery charge
    bot.gazebo.track_battery_charge()

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=commands, help='The command to issue to Gazebo')

    po_parser = argparse.ArgumentParser(prog=parser.prog + " place_obstacle")
    po_parser.add_argument('x', type=float, help='The x location relative to the map to place the obstacle')
    po_parser.add_argument('y', type=float, help='The y location relative to the map to place the obstacle')

    ro_parser = argparse.ArgumentParser(prog=parser.prog + " remove_obstacle")
    ro_parser.add_argument('obstacle_id', help='The id of the obstacle to remove')

    sc_parser = argparse.ArgumentParser(prog=parser.prog + " set_charge")
    sc_parser.add_argument('charge', type=float, help='Charge in mwh')

    et_parser = argparse.ArgumentParser(prog=parser.prog + " execute_task")
    et_parser.add_argument('start', type=str, help='The starting waypoint')
    et_parser.add_argument('target', nargs='+', type=str, help='The target waypoints')
    et_parser.add_argument('target', nargs='+', type=str, help='The target waypoint')

    er_parser = argparse.ArgumentParser(prog=parser.prog + " execute_task_reactive")
    er_parser.add_argument('start', type=str, help='The starting waypoint')
    er_parser.add_argument('target', nargs='+', type=str, help='The target waypoints')

    ef_parser = argparse.ArgumentParser(prog=parser.prog + " execute_task_reactive_fancy")
    ef_parser.add_argument('start', type=str, help='The starting waypoint')
    ef_parser.add_argument('target', nargs='+', type=str, help='The target waypoints')

    go_parser = argparse.ArgumentParser(prog=parser.prog + " go_directly")
    go_parser.add_argument('start', type=str, help='The starting waypoint')
    go_parser.add_argument('target', type=str, help='The target waypoint')

    args, extras = parser.parse_known_args()

    if args.command == "execute_task":
        pargs = et_parser.parse_args(extras)

        # put the robot at the start position
        start_coords = bot.map_server.waypoint_to_coords(pargs.start)
        bot.gazebo.set_bot_position(start_coords['x'], start_coords['y'], 0)
        rospy.sleep(10)
        task_finished, locs = bot.go_instructions_multiple_tasks_adaptive(pargs.start, pargs.target)
        print("{0}/{1} tasks are successfully done".format(task_finished, len(pargs.target)))

    if args.command == "execute_task_reactive":
        pargs = er_parser.parse_args(extras)

        # put the robot at the start position
        start_coords = bot.map_server.waypoint_to_coords(pargs.start)
        bot.gazebo.set_bot_position(start_coords['x'], start_coords['y'], 0)
        rospy.sleep(10)

        task_finished, locs = bot.go_instructions_multiple_tasks_reactive(pargs.start, pargs.target)
        print("{0}/{1} tasks are successfully done".format(task_finished, len(pargs.target)))

    if args.command == "execute_task_reactive_fancy":
        pargs = ef_parser.parse_args(extras)

        # put the robot at the start position
        start_coords = bot.map_server.waypoint_to_coords(pargs.start)
        bot.gazebo.set_bot_position(start_coords['x'], start_coords['y'], 0)
        rospy.sleep(10)

        task_finished, locs = bot.go_instructions_multiple_tasks_reactive_fancy(pargs.start, pargs.target)
        print("{0}/{1} tasks are successfully done".format(task_finished, len(pargs.target)))

    elif args.command == "go_directly":
        pargs = go_parser.parse_args(extras)

        # put the robot at the start position
        start_coords = bot.map_server.waypoint_to_coords(pargs.start)
        bot.gazebo.set_bot_position(start_coords['x'], start_coords['y'], 0)

        res = bot.go_without_instructions(pargs.target)
        if res:
            print("Reached the target")

    elif args.command == "set_charge":
        pargs = sc_parser.parse_args(extras)
        # converting mwh to Ah
        charge = pargs.charge / (1000 * bot.robot_battery.battery_voltage)
        res = bot.gazebo.set_charge(charge)
        if res:
            print('New charge has been set')
        else:
            print('Error happened setting the charge')

    elif args.command == "place_obstacle":
        pargs = po_parser.parse_args(extras)
        ob_id = bot.gazebo.place_obstacle(pargs.x, pargs.y)
        if ob_id is None:
            print('Could not place an obstacle')
        else:
            print('Obstacle {0} placed in the world.'.format(ob_id))

    elif args.command == "remove_obstacle":
        rargs = ro_parser.parse_args(extras)
        res = bot.gazebo.remove_obstacle(rargs.obstacle_id, check=False)
        if res:
            print('Obstacle was removed successfully')
        else:
            print('Obstacle was removed unsuccessfully')


if __name__ == '__main__':
    main()

