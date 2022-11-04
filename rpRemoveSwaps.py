#!/usr/bin/env python3
#
import sys
import json
import numpy as np
sys.path.append(r'T:\agTools\scripts')
import agFileTools


json_file = r"T:\RL-Replayer\scratch\replay_test_220926mini-trunc-update2.json"



json_linebreaks_dict = ['{"player_name":', '"events":','{"time":', '"loc"']
def write_json(data, file_path):
    print('writing data to %s' % file_path)
    n = open(file_path, "w")
    json_string = json.dumps(data)
    # go thru string
    # when u find (substring) from list of substrings, add a newline in front of it
    for j in json_linebreaks_dict:
        j_newline = '\n'+j
        json_string = json_string.replace(j, j_newline)
    n.write(json_string)
    n.close()

def get_previous_state(previous_state_list, actor_id):
    for i, d in enumerate(previous_state_list):
        if d["actor_id"] == actor_id:
            print('    found actor in list')
            previous_state_list.pop(i)
            return d, previous_state_list
    return None, previous_state_list

def process_update_events(frames_list):
    # new blank event list
    # new dict previous_state
    new_frames_list = []

    # entries in psd: actor_id : { time: time, rot_q }
    previous_state_list = []
    previous_state_dict = {}

    print('Dictionary has>', len(frames_list), 'entries')
    for i, frame_dict in enumerate(frames_list):

        # for event in event list
        # if its an rbstate event:
        if frame_dict["event_type"]=="RBState":
            print('looking at',frame_dict)
            # get actor id and time
            actor_id = frame_dict["actor_id"]
            current_time = frame_dict["time"]
            # get current rotation wxyz
            rot_q = frame_dict["rot_q"]

            # is actor id in previous_state?
            (previous_state_dict, previous_state_list) = get_previous_state(previous_state_list, actor_id)
            if previous_state_dict:
            # and maybe check time diff
                # get previous state wxyz
                rot_q_old = previous_state_dict["rot_q"]
                print('  comparing new rot_q > ', rot_q, 'to previous rot_q >', rot_q_old)
                flip_count = 0

                for i in range(4):
                    new = rot_q[i]
                    old = rot_q_old[i]
                    #print('    comparing', new,'and',old)
                    # if sign(new term) != sign(old term):
                    if np.sign(new) != np.sign(old):
                        #print('sign flipped')
                        flip_count += 1
                    # or (abs(new term) < 0.1)
                    elif abs(new) < 0.1:
                        #print('value too small')
                        flip_count += 1
                    # flip_count += 1

                # if flip count = 4:
                if flip_count == 4:
                    print('thats four flips, lets invert')
                    # for term in wxyz:
                    for i in range(4):
                        rot_q[i] = -rot_q[i]
                    print(' new rot_q is',rot_q)
                else:
                    print('didnt flip')
            # either way, updated previous state dict with
            # current actor id, time , wxyz
            previous_state_list.append({"actor_id": actor_id,
                                        "time": current_time,
                                        "rot_q": rot_q})
            print('updated prev state list >',previous_state_list)
            # assemble new event
            frame_dict["rot_q"] = rot_q
            print(' changed frame dict is', frame_dict)
            print('')

        # add current event to the event list
        new_frames_list.append(frame_dict)
        #if i >= 300: break
    return new_frames_list


def main(input_json_file):
    print('starting main loop w file>', input_json_file)
    # load json file
    data = agFileTools.read_json(input_json_file)
    header_data = data["header"]

    # get the event list
    frames_list = data["events"]
    new_frames_list = process_update_events(frames_list) # get content / body / frames


    # save new json
    # write results
    output_json_file = input_json_file.replace('.json', '-unswapped.json')
    ######  MODIFY FOR body, header to save team lists
    json_data = {"header":header_data, "events": new_frames_list }
    write_json(json_data, output_json_file)   #was agFileTools.
    #write_frames_json(new_frames_list, output_json_file)
    print('finished looop')



main(json_file)
