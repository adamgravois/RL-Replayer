import sys
sys.path.append(r'T:\agTools\scripts')
import agFileTools
from pymel.core import *
import agMath
import math
import maya.api.OpenMaya as api

json_file = r"T:\RL-Replayer\scratch\replay_test_220926mini-trunc-update2.json"
maya_file = json_file.replace(".json", ".mb")
scale_factor = 0.001

maya_template = r"T:\RL-Replayer\scenes\pitch_simple\pitch-simple-01.mb"
ball_geo = 'ball_simple'
car_geo = 'octane_orange'
blue_geo = 'octane_blue'
orange_geo = 'octane_orange'
axis_geo = 'chonky_axis'

active_actors_list = []

def get_frames_json(input_json):
    full_dict = agFileTools.read_json(input_json)

    # new_dict = replay_dict_struct.copy()
    frames_list = full_dict["content"]["body"]["frames"]

    return frames_list

def get_actor_name(actor_id):
    return 'actor_%s_loc' % actor_id
def get_rotation_name(actor_id):
    return 'actor_%s_rot' % actor_id
def get_rotation_swivel_name(actor_id):
    return 'actor_%s_rot_swivel' % actor_id
def get_vectorviz_name(actor_id):
    return 'vector_%s_rot' % actor_id

class Car:
    def __init__(self, player_name="", team=-1):
        self.player_name = player_name
        self.team = team
        self.pri_id = -1
        self.car_id = -1
        self.geo_name = ""

    def display(self):
        print("Car: %s  Team: %d  PRI: %d  CarID: %d  Model: %s" % (
            self.player_name, self.team, self.pri_id,
            self.car_id, self.geo_name ))


def get_actor_locator(actor_id):
    actor_name = get_actor_name(actor_id)

    # make locator if it does not exist
    if not objExists(actor_name):
        print(" get_actor_loc making > ", actor_name,"for id >", actor_id)
        actor = spaceLocator(n = actor_name)
        # set hidden at frame 1
        setKeyframe(actor, v=0, at='visibility', t=1)
        # Add a rotate subactor
        rotator_name = get_rotation_name(actor_id)
        rotator = spaceLocator(n= rotator_name)
        print('   created actor > %s , rotator > %s' % (actor, rotator))
        parent(rotator, actor)
        # add a swivel subactor
        #swivel_name = get_rotation_swivel_name(actor_id)
        #swivel = spaceLocator(n = swivel_name)
        #parent(swivel, rotator)
        # clone chonky
        #axis = duplicate(axis_geo)
        #parent(axis, swivel)

        # add a quaternion vector visualizer (loc = rq-x,z,y)
        vectorviz_name = get_vectorviz_name(actor_id)
        vector_visualizer = polySphere(r=1, sx=8, sy=5, n= vectorviz_name)[0]
        print("vvv > ", vector_visualizer)
        parent(vector_visualizer, actor)

        # aim constrain the rotator
        # aimConstraint(vector_visualizer, rotator, wut="none")

        # add a camera to follow it around
        camera_name = "actor_%s_camera" % actor_id
        car_cam = camera(n=camera_name, focalLength=24 )[0]
        car_cam_shp = car_cam.getShape()
        setAttr("%s.locatorScale" % car_cam_shp, 10)
        setAttr("%s.translateZ" % car_cam, 50)
        setAttr("%s.translateY" % car_cam, 10)
        setAttr("%s.rotateX" % car_cam, -10)
        parent(car_cam, actor)

    return actor_name


def create_actor_model(actor_id, class_name, frame_time, car_list):
        # and a better placeholder
        parent_name = get_rotation_name(actor_id)
        geo_list = listRelatives(parent_name, type="transform")
        print("  geo list for > %s is >> %s" % (parent_name, geo_list) )
        if class_name == "TAGame.Car_TA":
            source_geo = car_geo
            geo_name = "actor_%s_car_geo" % actor_id
            #car = get_car_obj(car_list, actor_id=actor_id)
            #print("spawning car for player %s" % car.player_name)
        elif class_name == "TAGame.Ball_TA":
            source_geo = ball_geo
            geo_name = "actor_%s_ball_geo" % actor_id
        else:
            return None

            # does it already exist?
        if geo_name in geo_list:
        # key it to be visible, and done
            setKeyframe(geo_name, v=1, at='visibility', t=frame_time)
            return geo_name
        # if not visible, create new
        else:
            geo = duplicate(source_geo, n = geo_name)
            print("  creating car >", geo)
            parent(geo, parent_name)
            setKeyframe(geo_name, v=1, at='visibility', t=frame_time)
            setKeyframe(geo_name, v=0, at='visibility', t=1)
            return geo_name

#def event_pawn_pri(event):
    # is called from event


def key_location(actor_id, loc, frame_time):
    actor = PyNode(get_actor_name(actor_id) )

    #print('location of ',actor_name, 'is', loc)
    # note that we're flipping Y and Z -- source is z-up, maya is y-up
    setKeyframe(actor, v=(loc[0]*scale_factor), at='tx', t=frame_time)
    setKeyframe(actor, v=(loc[1]*scale_factor), at='tz', t=frame_time)
    setKeyframe(actor, v=(loc[2]*scale_factor), at='ty', t=frame_time)


def key_rotation(actor_id, rot_q, frame_time):
    rotator = PyNode(get_rotation_name(actor_id))
    actor = PyNode(rotator)
    #print('  q_dict >', rot_q)

    ## option one
    q = api.MQuaternion(rot_q[0], rot_q[1], rot_q[2], rot_q[3] )
    e = q.asEulerRotation()
    r = list(map(math.degrees, e))
    r_x = r[0]
    r_y = r[1]
    r_z = r[2]

    ## option two
    #q_rot = agMath.Quaternion._make(rot_q)
    #print('qrot is>', q_rot)
    #rot_rad = agMath.quaternion_to_euler(q_rot)
    #r_x = agMath.convert_to_degrees(rot_rad.x)
    #r_y = agMath.convert_to_degrees(rot_rad.y)
    #r_z = agMath.convert_to_degrees(rot_rad.z)
    #print('rotation of', actor_name, 'is', r_x, r_y, r_z)
    #
    setKeyframe(actor, v=r_x, at='ry', t=frame_time)
    setKeyframe(actor, v=r_y, at='rx', t=frame_time)
    setKeyframe(actor, v=r_z, at='rz', t=frame_time)

    # also set the vector visualizart
    vector_visualizer = PyNode(get_vectorviz_name(actor_id))
    setKeyframe(vector_visualizer, v=(rot_q[1]*10), at='tx', t=frame_time)
    setKeyframe(vector_visualizer, v=(rot_q[2]*10), at='tz', t=frame_time)
    setKeyframe(vector_visualizer, v=(rot_q[3]*10), at='ty', t=frame_time)

    # transform the w value to swivel in degrees
    #swivel = get_rotation_swivel_name(actor_id)
    #swivel_value = math.degrees(math.acos(rot_q[0]) * 2)
    #setKeyframe(swivel, v=swivel_value, at = 'rx', t=frame_time)

def get_car_obj(car_list, actor_id=-1, pri_id=-1, name=""):
    if actor_id >= 0:
        for car in car_list:
            if car.car_id == actor_id: return car
    if pri_id >= 0:
        for car in car_list:
            if car.pri_id == pri_id: return car
    if name != "":
        for car in car_list:
            if car.player_name == name: return car
    return None

def do_actor_events(event_dict, frame_time, car_list):
    global active_actors_list
    actor_id = event_dict["actor_id"]

    print("  do event %s for actor id %s "\
          % (event_dict["event_type"], actor_id))
    if "spawned" in event_dict["event_type"]:
        print('spawning actor>', actor_id)
        actor_name = get_actor_locator(actor_id)
        active_actors_list.append(actor_id)
        print("updated active list>", active_actors_list)
        create_actor_model(actor_id, event_dict["class_name"], frame_time, car_list)
        setKeyframe(actor_name, v=1, at='visibility', t=frame_time)

    ##  This tells us what PRI the Car_TA_Actor has.
    ## (We can set Actor_id" on the car with this PRI
    if "Engine.Pawn:PlayerReplicationInfo" in event_dict["event_type"]:
        pri = event_dict["pri_id"]
        car = get_car_obj(car_list, pri_id=pri)
        if car:
            car.car_id = actor_id
            car.display()
        else: print("couldnt find a car with PRI %d" % pri)

    ## this tells us name of player for this PRI
    ## (we can set PRI of car)
    if "Engine.PlayerReplicationInfo:PlayerName" in event_dict["event_type"]:
        name = event_dict["player_name"]
        car = get_car_obj(car_list, name=name)
        if car:
            car.car_id = actor_id
            car.display()
        else: print("couldnt find a car with name %s" % name)

    if "destroyed" in event_dict["event_type"]:
        if actor_id not in active_actors_list: return None
        print('DESSSTTTTOORRRYYY')
        actor_name = get_actor_locator(actor_id)
        setKeyframe(actor_name, v=0, at='visibility', t=frame_time)
        # take it off the list
        active_actors_list.remove(actor_id)
        print("updated active list>", active_actors_list)
        # also hide the child mesh
        rotate_parent = get_rotation_name(actor_id)
        kids = listRelatives(rotate_parent)
        for k in kids:
            setKeyframe(k, v=0, at='visibility',t= frame_time)

    if "RBState" in event_dict["event_type"]:
        if actor_id not in active_actors_list: return None
        key_location(actor_id, event_dict["loc"], frame_time)
        key_rotation(actor_id, event_dict["rot_q"], frame_time)


def setup_scene(header):
    print("foo")
    #### CREATE SIX CAR MODELS

    ### get player list
    player_list = header["player_list"]
    print("player list>", player_list)
    car_list = []
    name_list = []
    team_id_list = []

    for p in player_list:
        name_list.append(p["player_name"])
        team_id_list.append(p["team"])

    l = len(player_list)
    print("lenghth", l)
    cars = [Car() for i in range(l)]
    for i,car in enumerate(cars):
        car.player_name = name_list[i]
        car.team = team_id_list[i]


    print("Car List complete > ", cars)
    return cars


def main(json_file):
    print('###### LETS GO #########')
    # new Maya file
    openFile(maya_template, f=True)
    saveAs(maya_file, f=True)
    #setup_scene()
    # get JSON

    data = agFileTools.read_json(json_file)
    update_list = data["events"]
    ######## Set up player cars based on team list
    car_list = setup_scene(data["header"])
    first = True
    for i, event_dict in enumerate(update_list):
        #if i > 200: break
        #if (i % 500)==0: saveFile()

        # get time, set currrent time
        frame_time = int (event_dict["time"] * 30)
        print('frame time is',frame_time, 'aka json time', event_dict["time"])
        if first:
            playbackOptions(minTime = frame_time)
            first = False
        playbackOptions(maxTime = frame_time)
        # currentTime(frame_time, update=True)
        do_actor_events(event_dict, frame_time, car_list)

    #### add Euler Cleanup to all rotations
    rotators = ls("actor_*_rot")

    rot_list = []
    for r in rotators:
        rot_list.append("%s.rotateX" % r)
        rot_list.append("%s.rotateY" % r)
        rot_list.append("%s.rotateZ" % r)

    #for r in rot_list:
    #    filterCurve(r)

    print("Done I guess")

main(json_file)
