#!/usr/bin/env python3
#
import sys
import json
sys.path.append(r'T:\agTools\scripts')
import agFileTools


json_file = r"T:\RL-Replayer\scratch\replay_test_220926mini-trunc.json"
event_names_list = ["TAGame.RBActor_TA:ReplicatedRBState", "TAGame.CarComponent_TA:Vehicle"]

event_names_dict =  {"TAGame.RBActor_TA:ReplicatedRBState" : "RBState"
                     }

object_classes_list = ["TAGame.Ball_TA", "TAGame.Car_TA", "TAGame.CarComponent_Boost_TA"]


replay_dict_struct = { "content":
                           {"body":
                                {"frames": []}
                            }
                       }
actor_event_dict_struct = {"actor_id": {"value": 1},
                            "value": { "updated": [] }
                     }

event_dict_struct =  { "name": "TAGame.RBActor_TA:ReplicatedRBState",
                        "value": { "rigid_body_state": {}}
                     }


rbd_data_struct = {"location": {"x": 0, "y": 0, "z": 0},
                    "rotation": {
                      "quaternion": {"w": 0.0, "x": 0.0, "y": 0.0, "z": 0.0} }
                   }


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


def recursive_dict_compare(dict_a, dict_b):
    result_dict = {}
    for key, value in dict_a.items():

        if not key in dict_b: continue
        # print("     key>",key, "value>", dict_b[value])
        if type(value) == dict:
            # print('going deeper')
            new_value = recursive_dict_compare(dict_a[key], dict_b[key])
        else:
            new_value = dict_b[key]
        result_dict[key]= new_value
    return result_dict

def get_rigid_body_data(rigid_body_state_dict):

    rbd_dict = recursive_dict_compare(rbd_data_struct, rigid_body_state_dict)
    return rbd_dict

def get_RBState_dict(event):
    new_event_dict = {}  # event_dict_struct.copy()
    if "value" not in event:
        # print('   xxx no event value found, bailing')
        return None
    if "rigid_body_state" not in event["value"]:
        # print('   xxx no rbs found in event value, bailing')
        return None
    print('    found >', event["name"])
    # get rigid body transform data
    rbd_dict = get_rigid_body_data(event["value"]["rigid_body_state"])
    if not rbd_dict:
        print('    xxx did not return rbd_dict, skipping')
        return None
    # print('    returned rbd_dict>', rbd_dict)
    # assemble new dict entry
    new_event_dict["location"] = {key:rbd_dict["location"][key] for key in ["x", "y", "z"]}   #  ["value"]["rigid_body_state"] = rbd_dict.copy()
    new_event_dict["rotation"] = {key:rbd_dict["rotation"]["quaternion"][key] for key in ["w", "x", "y", "z"]}
    return rbd_dict
    #return new_event_dict

def log_replication_value_types(replications_list, event_type_dict):
    print(' logging replications with ', len(replications_list), 'actor items')
    for actor_index, actor_event_dict in enumerate(replications_list):
        print("  reading index", actor_index, "actor event dict>", actor_event_dict["actor_id"])
        # Does this match the wide pattern?
        if "value" not in actor_event_dict: continue
        if "updated" not in actor_event_dict["value"]: continue
        new_actor_event_dict = { "actor_id": {"value": 0}, "value": { "updated": []}}  # actor_event_dict_struct.copy()
        keep_actor = False
        # get actor ID
        actor_id = actor_event_dict["actor_id"]["value"]
        # OK, let's start processing events!
        # print("   there are ", len(actor_event_dict["value"]["updated"]), "update events in it")
        for event_index, event in enumerate(actor_event_dict["value"]["updated"]):

            # Is it the kind of event we want?
            if event["name"] not in event_type_dict: # == "TAGame.RBActor_TA:ReplicatedRBState":
                # go get em
                new_event_name = event["name"]
                print('  logging new event>', new_event_name)
                new_event_value = event["value"]
                event_type_dict[new_event_name] = {"value":new_event_value, "count":1}
            else:
                event_name = event["name"]
                count = event_type_dict[event_name]["count"]
                count += 1
                event_type_dict[event_name]["count"] = count

    return event_type_dict

def log_replication_types(replications_list, event_type_dict):
    print(' logging replications with ', len(replications_list), 'actor items')
    for actor_index, actor_event_dict in enumerate(replications_list):
        print("  reading index", actor_index, "actor event dict>", actor_event_dict["actor_id"])
        # Does this match the wide pattern?
        if "value" not in actor_event_dict: continue
        if "updated" not in actor_event_dict["value"]: continue
        new_actor_event_dict = { "actor_id": {"value": 0}, "value": { "updated": []}}  # actor_event_dict_struct.copy()
        keep_actor = False
        # get actor ID
        actor_id = actor_event_dict["actor_id"]["value"]
        # OK, let's start processing events!
        # print("   there are ", len(actor_event_dict["value"]["updated"]), "update events in it")
        for event_index, event in enumerate(actor_event_dict["value"]["updated"]):

            # Is it the kind of event we want?
            if event["name"] not in event_type_dict: # == "TAGame.RBActor_TA:ReplicatedRBState":
                # go get em
                new_event_name = event["name"]
                print('  logging new event>', new_event_name)
                new_event_value = event["value"]
                event_type_dict[new_event_name] = {"value":new_event_value, "count":1}
            else:
                event_name = event["name"]
                count = event_type_dict[event_name]["count"]
                count += 1
                event_type_dict[event_name]["count"] = count

    return event_type_dict

def log_spawn_events(replications_list, spawn_event_list, time):
    print(' logging spawns and destroys with ', len(replications_list), 'actor items')
    for actor_index, actor_event_dict in enumerate(replications_list):
        print("  reading index", actor_index, "actor event dict>", actor_event_dict["actor_id"])
        # Does this match the wide pattern?
        if "value" not in actor_event_dict: continue
        if "spawned" in actor_event_dict["value"]:
            new_actor_event_dict = { }
            keep_actor = False
            # get time
            new_actor_event_dict["time"] = time
            # get actor ID
            new_actor_event_dict["actor_id"] = actor_event_dict["actor_id"]["value"]
            new_actor_event_dict["event"] = "spawned"

            # get name
            new_actor_event_dict["name"] = actor_event_dict["value"]["spawned"]["name"]
            new_actor_event_dict["name_index"] = actor_event_dict["value"]["spawned"]["name_index"]

            # get class
            new_actor_event_dict["object_id"] = actor_event_dict["value"]["spawned"]["object_id"]
            # get object ID
            new_actor_event_dict["class"] = actor_event_dict["value"]["spawned"]["class_name"]
            # get object Name
            new_actor_event_dict["object_name"] = actor_event_dict["value"]["spawned"]["object_name"]
            spawn_event_list.append(new_actor_event_dict)
        elif "destroyed" in actor_event_dict["value"]:    # Is it the kind of event we want?
            new_actor_event_dict = { }
            keep_actor = False
            # get time
            new_actor_event_dict["time"] = time
            # get actor ID
            new_actor_event_dict["actor_id"] = actor_event_dict["actor_id"]["value"]
            new_actor_event_dict["event"] = "destroyed"
            spawn_event_list.append(new_actor_event_dict)
        else:
            continue
    return spawn_event_list

def get_pri_id(event):
    print('player replication info!')
    pri_id = event["value"]["flagged_int"]["int"]
    return pri_id

def get_replications(replications_list, time_stamp):
    print(' getting replications with ', len(replications_list), 'actor items')
    new_replication_list = []
    # one replication list per frame
    # multiple possible actor event dicts per replication list
    # one actor per actor event dict
    # multiple possible events per actor event dict ( value - updated )
    # rebuild to simplify:
    # return a list of update_events that look like:
    # ( time : 0.0, actor_id: 1, event_type: location: (0,0,0), rotation: (0,0,0,0) }

    for actor_index, actor_event_dict in enumerate(replications_list):
        print("  reading index", actor_index, "actor event dict>", actor_event_dict["actor_id"])
        # Does this match the wide pattern?
        # get actor ID
        actor_id = actor_event_dict["actor_id"]["value"]
        # just in case
        if "value" not in actor_event_dict: continue
        if "spawned" in actor_event_dict["value"]:
            # double check no bad data
            if "class_name" not in actor_event_dict["value"]["spawned"]: continue
            class_name = actor_event_dict["value"]["spawned"]["class_name"]
            # get spawn type
            # if it's the type we're looking for, make an entry
            if class_name in object_classes_list: # == "TAGame.Ball_TA" or class_name == "TAGame.Car_TA":
                new_replication_list.append({"time": time_stamp,
                                             "actor_id": actor_id,
                                             "event_type": "spawned",
                                             "class_name": class_name})
            continue
        elif "destroyed" in actor_event_dict["value"]:
            # get
            new_replication_list.append({"time": time_stamp,
                                         "actor_id": actor_id,
                                         "event_type": "destroyed"})
            continue

        if "updated" not in actor_event_dict["value"]: continue
        keep_actor = False
        # OK, let's start processing events!
        # print("   there are ", len(actor_event_dict["value"]["updated"]), "update events in it")
        for event_index, event in enumerate(actor_event_dict["value"]["updated"]):
            print('---------- event name', event["name"])

            # Is it the kind of event we want?
            if event["name"] == "TAGame.RBActor_TA:ReplicatedRBState":
                # go get
                new_event_dict = get_RBState_dict(event)
                if new_event_dict:
                    print('    adding event', event_index, ' to update list')
                    loc = (new_event_dict["location"]["x"],
                           new_event_dict["location"]["y"],
                           new_event_dict["location"]["z"])
                    rotq = (new_event_dict["rotation"]["quaternion"]["w"],
                            new_event_dict["rotation"]["quaternion"]["x"],
                            new_event_dict["rotation"]["quaternion"]["y"],
                            new_event_dict["rotation"]["quaternion"]["z"])
                    new_replication_list.append({"time": time_stamp,
                                                 "actor_id": actor_id,
                                                 "event_type": "RBState",
                                                 "loc": loc,
                                                 "rot_q": rotq
                                                 })
                else:
                    continue
            elif event["name"] == "Engine.Pawn:PlayerReplicationInfo":
                pri_id = get_pri_id(event)
                new_replication_list.append({"time": time_stamp,
                                             "actor_id": actor_id,
                                             "event_type": "Pawn_PRI",
                                             "pri_id": pri_id
                                             })
            elif event["name"] == "Engine.PlayerReplicationInfo:PlayerName":
                player_name = event["value"]["string"]
                new_replication_list.append({"time": time_stamp,
                                             "actor_id": actor_id,
                                             "event_type": "PRI_name",
                                             "player_name": player_name
                                             })
            elif event["name"] == "TAGame.GameEvent_TA:ReplicatedRoundCountDownNumber":
                countdown_num =  event["value"]["int"]
                new_replication_list.append({"time": time_stamp,
                                             "actor_id": actor_id,
                                             "event_type": "Countdown",
                                             "countdown_number": countdown_num
                                             })
            elif event["name"] == "TAGame.CarComponent_TA:ReplicatedActive":
                active_value =  event["value"]["byte"]
                new_replication_list.append({"time": time_stamp,
                                             "actor_id": actor_id,
                                             "event_type": "Active",
                                             "active_value": active_value
                                             })
            elif event["name"] == "TAGame.CarComponent_TA:Vehicle":
                vehicle_id =  event["value"]["flagged_int"]["int"]
                new_replication_list.append({"time": time_stamp,
                                             "actor_id": actor_id,
                                             "event_type": "Vehicle",
                                             "car_id": vehicle_id
                                             })
            else:
                print('  xxx event name was >', event["name"], '... skipping')

    # print('  Returning New Repl List >', new_replication_list)
    print('########### leaving GET_REPLICATIONS ##########')
    return new_replication_list


def get_frames_json(input_json):
    full_dict = agFileTools.read_json(input_json)

    # new_dict = replay_dict_struct.copy()
    frames_list = full_dict["content"]["body"]["frames"]

    return frames_list


def write_frames_json(frames_list, output_json_file):
    print('>>Writing Frames List to json')
    # wrap it in
    out_data = { "content": { "body" : { "frames": frames_list}}}

    agFileTools.write_json(out_data, output_json_file)


def class_mappings(input_json_file):
    data = agFileTools.read_json(input_json_file)
    class_maps_list = data["content"]["body"]["class_mappings"]
    output_json_file = input_json_file.replace('.json', '-class_mappings.json')
    agFileTools.write_json(class_maps_list, output_json_file)


def caches(input_json_file):
    data = agFileTools.read_json(input_json_file)
    caches_list = data["content"]["body"]["caches"]

    new_cache_list = []
    for cache in caches_list:
        cache_id = cache["cache_id"]
        class_id = cache["class_id"]
        parent_cache_id = cache["parent_cache_id"]
        map_list = cache["attribute_mappings"]
        if map_list:   # are there any mappings to report?
            for item in map_list:
                new_entry = { "cache_id" : cache["cache_id"],
                              "class_id" : cache["class_id"],
                              "parent_cache_id" : cache["parent_cache_id"],
                              "object_id" : item["object_id"],
                              "stream_id" : item["stream_id"]
                              }
                new_cache_list.append(new_entry)
        else:
            new_entry = {"cache_id": cache["cache_id"],
                         "class_id": cache["class_id"],
                         "parent_cache_id": cache["parent_cache_id"],
                         "object_id": "",
                         "stream_id": ""
                         }
            new_cache_list.append(new_entry)

    output_json_file = input_json_file.replace('.json', '-caches.json')
    agFileTools.write_json(new_cache_list, output_json_file )


def spawn_events(input_json_file):
    print('starting main loop w file>', input_json_file)
    # load json file
    frames_list = get_frames_json(input_json_file)  # get content / body / frames
    new_frames_list = []
    event_type_dict = {}
    spawn_event_list = []
    print('Dictionary has>', len(frames_list), 'entries')
    for i, frame_dict in enumerate(frames_list):
        # if i > 20: break
        # print('frame dict>', frame_dict)
        if "replications" in frame_dict:
            frame_time = frame_dict["time"]
            print('found replication at time> ', frame_time)
            spawn_event_list = log_spawn_events(frame_dict["replications"], spawn_event_list, frame_time)
        else:
            continue

    # write results
    output_json_file = input_json_file.replace('.json', '-spawns.json')
    agFileTools.write_json(spawn_event_list, output_json_file)
    print('finished loop')


def get_replication_value_types(input_json_file):
    print('starting main loop w file>', input_json_file)
    # load json file
    frames_list = get_frames_json(input_json_file) # get content / body / frames
    rep_value_types = []
    print('Dictionary has>', len(frames_list), 'entries')
    for i, frame_dict in enumerate(frames_list):
        # if i > 20: break
        # print('frame dict>', frame_dict)
        if "replications" in frame_dict:
            new_frame_dict = {}
            frame_time = frame_dict["time"]
            print('found replication at time> ', frame_time)
            for rep_item in frame_dict["replications"]:
                if "value" not in rep_item: continue
                rep_value_keys = rep_item["value"].keys()
                if rep_value_keys:
                    for v in rep_value_keys:
                        if v not in rep_value_types:
                            rep_value_types.append(v)


    # write results
    output_json_file = input_json_file.replace('.json', '-replicationValueTypes.json')
    agFileTools.write_json(rep_value_types, output_json_file)
    #write_frames_json(new_frames_list, output_json_file)
    print('finished looop')


def get_event_types(input_json_file):
    print('starting main loop w file>', input_json_file)
    # load json file
    frames_list = get_frames_json(input_json_file) # get content / body / frames
    event_type_dict = {}
    print('Dictionary has>', len(frames_list), 'entries')
    for i, frame_dict in enumerate(frames_list):
        # if i > 20: break
        # print('frame dict>', frame_dict)
        if "replications" in frame_dict:
            new_frame_dict = {}
            frame_time = frame_dict["time"]
            print('found replication at time> ', frame_time)
            event_type_dict = log_replication_types(frame_dict["replications"], event_type_dict)
        else:
            continue

    # write results
    output_json_file = input_json_file.replace('.json', '-eventTypes.json')
    agFileTools.write_json(event_type_dict, output_json_file)
    #write_frames_json(new_frames_list, output_json_file)
    print('finished looop')


def get_team_lists(data):
    # populate two lists with the player names on each team
    team_lists = [[],[]]
    player_list = []
    player_stats = data["header"]["body"]["properties"]["value"]["PlayerStats"]
    for stat_dict in player_stats["value"]["array"]:
        name = stat_dict["value"]["Name"]["value"]["str"]
        team_int = stat_dict["value"]["Team"]["value"]["int"]
        team_lists[team_int].append(name)
        player_list.append({"player_name": name, "team": team_int})
    print("Team 0 >", team_lists[0])
    print("Team 1 >", team_lists[1])
    return (team_lists[0],team_lists[1], player_list)

def get_header_data(json_data):
    header_data = {}
    # for now, header is just team lists
    (team_0, team_1, player_list) = get_team_lists(json_data)
    header_data["player_list"] = player_list
    header_data["team_0"] = team_0
    header_data["team_1"] = team_1
## instead lets make a player list
    return header_data

def get_update_events(frames_list):
    new_frames_list = []
    event_type_dict = {}
    spawn_event_list = []
    print('Dictionary has>', len(frames_list), 'entries')
    for i, frame_dict in enumerate(frames_list):
        # if i > 20: break
        # print('frame dict>', frame_dict)
        if "replications" in frame_dict:
            new_frame_dict = {}
            frame_time = frame_dict["time"]
            print('found replication at time> ', frame_time)
            new_replications_list = get_replications(frame_dict["replications"], frame_time)
            # did we get a result? if so, assemble new entry
            if new_replications_list:
                print('=====================================================================')
                print('TTTT logging event at time>', frame_time)
                # print('new replications list>', new_replications_list)
                new_frames_list.extend(new_replications_list.copy())

            else:
                continue
        else:
            continue
    return new_frames_list


def main(input_json_file):
    print('starting main loop w file>', input_json_file)
    # load json file
    data = agFileTools.read_json(input_json_file)

    header_data = get_header_data(data)
    # for now, header is just player list, team lists

    frames_list = data["content"]["body"]["frames"]
    new_frames_list = get_update_events(frames_list) # get content / body / frames

    # write results
    output_json_file = input_json_file.replace('.json', '-update2.json')
    ######  MODIFY FOR body, header to save team lists
    json_data = {"header":header_data, "events": new_frames_list }
    write_json(json_data, output_json_file)   #was agFileTools.
    #write_frames_json(new_frames_list, output_json_file)
    print('finished looop')


#class_mappings(json_file)
#caches(json_file)
#get_update_events(json_file)
#get_event_types(json_file)
#get_replication_value_types(json_file)
main(json_file)
