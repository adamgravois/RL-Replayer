import sys
sys.path.append(r'T:\agTools\scripts')
import agFileTools
from pymel.core import *
import agMath

json_file = r"T:\RL-Replayer\scratch\replay_test_220926-scraped.json"
maya_file = json_file.replace(".json", ".mb")
scale_factor = 0.001

def get_frames_json(input_json):
    full_dict = agFileTools.read_json(input_json)

    # new_dict = replay_dict_struct.copy()
    frames_list = full_dict["content"]["body"]["frames"]

    return frames_list

def get_actor_locator(actor_id):
    actor_name = 'actor_%s_loc' % actor_id
    # make locator if it does not exist
    if not objExists(actor_name):
        actor = spaceLocator(n = actor_name)
        cube = polyCube(w=8, h=4, d=16, n='actor_%s_cube' % actor_id)[0]
        cube.translateY = 1
        parent(cube, actor)

    return actor_name

def key_location(actor_name, event, time_stamp):
    if "value" not in event:
        # print('   xxx no event value found, bailing')
        return None
    if "rigid_body_state" not in event["value"]:
        # print('   xxx no rbs found in event value, bailing')
        return None
    actor = PyNode(actor_name)
    loc = event["value"]["rigid_body_state"]["location"]
    #print('location of ',actor_name, 'is', loc)
    # note that we're flipping Y and Z -- source is z-up, maya is y-up
    setKeyframe(actor, v=(loc["x"]*scale_factor), at='tx', t=time_stamp)
    setKeyframe(actor, v=(loc["y"]*scale_factor), at='tz', t=time_stamp)
    setKeyframe(actor, v=(loc["z"]*scale_factor), at='ty', t=time_stamp)


def key_rotation(actor_name, event, time_stamp):
    if "value" not in event:
        # print('   xxx no event value found, bailing')
        return None
    if "rigid_body_state" not in event["value"]:
        # print('   xxx no rbs found in event value, bailing')
        return None
    actor = PyNode(actor_name)
    q_dict = event["value"]["rigid_body_state"]["rotation"]["quaternion"]
    #print('  q_dict >', q_dict)
    q_rot = agMath.Quaternion(q_dict["w"], q_dict["x"],q_dict["y"],q_dict["z"] )

    rot_rad = agMath.quaternion_to_euler(q_rot)
    rot_x = agMath.convert_to_degrees(rot_rad.x)
    rot_y = agMath.convert_to_degrees(rot_rad.y)
    rot_z = agMath.convert_to_degrees(rot_rad.z)
    print('rotation of', actor_name, 'is', rot_x, rot_y, rot_z)
    # test swap Y & Z ...
    setKeyframe(actor, v=rot_x, at='rx', t=time_stamp)
    setKeyframe(actor, v=rot_y, at='rz', t=time_stamp)
    setKeyframe(actor, v=rot_z, at='ry', t=time_stamp)

def get_actor_events(replications_list, frame_time):
    print('aaaaaa actor events at time', frame_time)
    for actor_event_dict in replications_list:
        # make sure it's legit
        if "value" not in actor_event_dict: continue
        if "updated" not in actor_event_dict["value"]: continue
        #print('actor event dict>', actor_event_dict)
        # get actor ID
        actor_id = actor_event_dict["actor_id"]["value"]
        actor_name = get_actor_locator(actor_id)

        for event in actor_event_dict["value"]["updated"]:
            #print('event>', event)
            if "name" not in event: continue
            if event["name"] == "TAGame.RBActor_TA:ReplicatedRBState":
                key_location(actor_name, event, frame_time)
                key_rotation(actor_name, event, frame_time)


# quats to euler
# set rotation kfs

def setup_scene():
    p_cam = ls('persp')[0]
    p_shp = p_cam.getShape()
    setattr(p_shp, "nearClipPlane", 10)
    setattr(p_shp, "farClipPlane", 1000000)
    ground_plane = polyPlane(w=700, h=1000, sw= 7, sh= 10)
    shader = shadingNode('lambert', asShader=1)
    sg = sets(name='%s_SG' % shader, empty=True, renderable=True, noSurfaceShader=True)
    connectAttr('%s.outColor' % shader, '%s.surfaceShader' % sg)
    sets(sg, forceElement=ground_plane)
    setAttr('%s.color' % shader, 0.075, 0.18, 0.075, type='double3')


def main(json_file):
    print('###### LETS GO #########')
    # new Maya file
    newFile(f=True)
    saveAs(maya_file, f=True)
    setup_scene()
    # get JSON frames_list
    frames_list = get_frames_json(json_file)
    first = True
    for i, frame_dict in enumerate(frames_list):
        #if i > 300: break
        if (i % 500)==0: saveFile()

        if "replications" in frame_dict:
            # get time, set currrent time
            frame_time = int (frame_dict["time"] * 30)
            print('frame time is',frame_time)
            if first:
                playbackOptions(minTime = frame_time)
                first = False
            playbackOptions(maxTime = frame_time)
            # currentTime(frame_time, update=True)
            get_actor_events(frame_dict["replications"], frame_time)


main(json_file)
