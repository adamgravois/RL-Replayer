#!/usr/bin/env python3
#
import sys
import json
sys.path.append(r'T:\agTools\scripts')
import agFileTools


json_file = r"T:\RL-Replayer\scratch\replay_test_220926mini-trunc.json"



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



def main(json_file):
    print('lo word')
    # open json 'update' file

    # get the event list

    # new blank event list
    # new dict previous_state

    # for event in event list

    # if its an rbstate event:

        # get actor id and time
        # get current rotation wxyz

        # is actor id in previous_state?
        # and maybe check time diff

            # get previous state wxyz

            # flip_count = 0
            # for term in wxyz:
                # if sign(new term) != sign(old term):
                # or (abs(new term) < 0.1)
                    # flip_count += 1

            # if flip count = 4:
                # for term in wxyz:
                    # term = - term

        # either way, updated previous state dict with
        # current actor id, time , wxyz

    # add current event to the event list

    # save new json
