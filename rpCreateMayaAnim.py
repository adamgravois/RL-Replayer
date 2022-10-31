import sys
sys.path.append(r'T:\agTools\scripts')
import agFileTools
from pymel.core import *
from importlib import reload
import agMath
import math
import numpy as np
import maya.api.OpenMaya as api
reload(agMath)

object_classes_list = ["TAGame.Ball_TA", "TAGame.Car_TA", "TAGame.CarComponent_Boost_TA"]

json_file = r"T:\RL-Replayer\scratch\replay_test_220926mini-trunc-update2.json"
maya_file = json_file.replace(".json", ".mb")
scale_factor = 0.001

maya_template = r"T:\RL-Replayer\scenes\pitch_simple\pitch-simple-02.mb"
ball_geo = 'ball_voxel'
car_geo = 'FordMustang_Yellow'
blue_geo = 'car_blue'
orange_geo = 'car_orange'
axis_geo = 'chonky_axis'
boost_geo = 'boost_locator'

# was 1 0 0 0  0 0 -1 0  0 1 0 0  0 0 0 1
# but that doesnt match the other .. dropping last 1
# flipping second -1 to 1
#try identity matrix
RHZ_2_LHY_MATRIX = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
])

active_actors_list = []
unclaimed_pawn_list = []
spawned_boost_list = []

def get_frames_json(input_json):
    full_dict = agFileTools.read_json(input_json)

    # new_dict = replay_dict_struct.copy()
    frames_list = full_dict["content"]["body"]["frames"]

    return frames_list

def get_actor_name(actor_id):
    return 'actor_%s_loc' % actor_id
def get_rotation_name(actor_id):
    return 'actor_%s_rot' % actor_id
def get_rotation_vector_name(actor_id):
    return 'actor_%s_rot_vector' % actor_id
def get_rotation_swivel_name(actor_id):
    return 'actor_%s_rot_swivel' % actor_id
def get_vectorviz_name(actor_id):
    return 'vector_%s_node' % actor_id

# if Pawn_PRI happens before PRI_name
class Unclaimed_Pawn:
    def __init__(self, pri_id, car_id):
        self.pri_id = pri_id
        self.car_id = car_id

    def display(self):
        print("Unclaimed Pawn: Actor ID: %d  PRI: %d" % (self.car_id, self.pri_id ))

class Boost:
    def __init__(self):
        self.boost_geo = ""
        self.actor_id = -1

class Car:
    IS_CAR = True
    def __init__(self, player_name="", team=-1):
        self.player_name = player_name
        self.team = team
        self.pri_id = -1
        self.actor_id = -1
        self.geo_name = ""
        self.boost = Boost()

    def display(self):
        print("Car: %s  Team: %d  PRI: %d  CarID: %d  Model: %s" % (
            self.player_name, self.team, self.pri_id,
            self.actor_id, self.geo_name ))

class Ball:
    IS_CAR = False
    def __init__(self):
        self.player_name = "game ball"
        self.pri_id = 0
        self.actor_id = -1
        self.geo_name = ball_geo

    def display(self):
        print("Ball: Actor ID: %d  Model: %s" % (self.actor_id, self.geo_name ))


def get_actor_locator(actor_id, object_class):
    actor_name = get_actor_name(actor_id)

    # make locator if it does not exist
    if not objExists(actor_name):
        print(" get_actor_loc making > ", actor_name,"for id >", actor_id)
        actor = spaceLocator(n = actor_name)

        if object_class == "TAGame.Car_TA" or object_class == "TAGame.Ball_TA":
            # Add a rotate subactor
            rotator_name = get_rotation_name(actor_id)
            rotator = spaceLocator(n= rotator_name)
            # set yxz rotatoin order, best so far ... nope, switching to yzx...
            setAttr("%s.rotateOrder" % rotator, 0)
            print('   created actor > %s , rotator > %s' % (actor, rotator))
            parent(rotator, actor)


            # add a swivel subactor
            rot_vector_name = get_rotation_vector_name(actor_id)
            rot_vector = spaceLocator(n = rot_vector_name)
            parent(rot_vector, actor)
            swivel_name = get_rotation_swivel_name(actor_id)
            swivel = spaceLocator(n = swivel_name)
            parent(swivel, rot_vector)
            # clone chonky
            axis = duplicate(axis_geo)
            parent(axis, swivel)

            # add a quaternion vector visualizer (loc = rq-x,z,y)
            vectorviz_name = get_vectorviz_name(actor_id)
            vector_visualizer = polySphere(r=0.5, sx=8, sy=5, n= vectorviz_name)[0]
            print("vvv > ", vector_visualizer)
            parent(vector_visualizer, actor)

            # aim constrain the rotation vector
            aimConstraint(vector_visualizer, rot_vector, wut="none")

    return actor_name


def key_location(actor_id, loc, frame_time):
    actor = PyNode(get_actor_name(actor_id) )

    pm = matrixUtil(t=loc)
    print('pm t>', pm)
    npm = np.array(pm)
    npm = npm.reshape([4,4])
    print('npm t>', npm)

    new_matrix = np.matmul(npm, RHZ_2_LHY_MATRIX)
    nt = matrixUtil(np.ravel(new_matrix).tolist(), q=True, t=True)
    print('new t>', nt)

    #print('location of ',actor_name, 'is', loc)
    # NO LONGER: note that we're flipping Y and Z -- source is z-up, maya is y-up
    #setKeyframe(actor, v=(loc[0]*scale_factor), at='tx', t=frame_time)
    setKeyframe(actor, v=(nt[0] * scale_factor), at='tx', t=frame_time)
    setKeyframe(actor, v=(nt[1] * scale_factor), at='ty', t=frame_time)
    setKeyframe(actor, v=(nt[2] * scale_factor), at='tz', t=frame_time)


def key_rotation(actor_id, rot_q, frame_time):
    rotator = PyNode(get_rotation_name(actor_id))
    actor = PyNode(rotator)
    #print('  q_dict >', rot_q)

    ## DOES IT MATTER IF WE UNITIZE THE VECTOR?
    vector = np.array([rot_q[1], rot_q[2], rot_q[3]])
    unit_vector = vector / np.linalg.norm(vector)
    ## option one
    q = api.MQuaternion(rot_q[0], rot_q[1], rot_q[2], rot_q[3] )
    # why doesnt this unit vector seem to be correct?
    #q = api.MQuaternion(rot_q[0], unit_vector[0], unit_vector[1], unit_vector[2])
    e = q.asEulerRotation()
    r = list(map(math.degrees, e))
    r_x = r[0]
    r_y = r[1]
    r_z = r[2]

    # option 4 matrix attempt

    # option 5 matrix python
    pm = matrixUtil(qt=[rot_q[0], rot_q[1], rot_q[2], rot_q[3] ])
    #print('pm>',pm)
    rt = matrixUtil(pm, q=True, r=True)
    #print('rt>',rt)
    rtd = np.degrees(rt)
    #print('rtd>', rtd)
    print('RTD > x %.2f y %.2f z %.2f' % (rtd[0], rtd[1], rtd[2]))
    # convert pm to a numpy array
    npm = np.array(pm)
    npm = npm.reshape([4,4])
    print('npm t>', npm)
    # apply the Max-2-Maya Matrix transform!
    new_matrix = np.matmul(npm, RHZ_2_LHY_MATRIX)
    nr = matrixUtil(np.ravel(new_matrix).tolist(), q=True, r=True)
    print('new r>', nr)

    nrtd = np.degrees(nr)
    print('RTD > x %.2f y %.2f z %.2f' % (nrtd[0], nrtd[1], nrtd[2]))

    # TRY swapping X and Y... that's closer... but Y seems inverted...
    # TRY inverting Y ... closer
    # TRY swapping x and Z
    # TRY inverting X and Z .... hmm, better but X is often wrong?
    # TRY dont invert X .. best so far, still some swaps
    r_x = nrtd[2]
    r_y = -nrtd[0]
    r_z = -nrtd[1]

    ## option two
    #q_rot = agMath.Quaternion._make(rot_q)
    #print('qrot is>', q_rot)
    #rot_rad = agMath.quaternion_to_euler(q_rot)
    #r_x = agMath.convert_to_degrees(rot_rad.x)
    #r_y = agMath.convert_to_degrees(rot_rad.y)
    #r_z = agMath.convert_to_degrees(rot_rad.z)
    #print('rotation of', actor_name, 'is', r_x, r_y, r_z)
    # try swapping rx & rz, as an experiment -- ok, that did create a better result, but not perfect
    # OK: ttrying no-conversion XYZ ... interesting but not quite there...
    setKeyframe(actor, v=r_x, at='rx', t=frame_time)
    setKeyframe(actor, v=r_y, at='ry', t=frame_time)
    setKeyframe(actor, v=r_z, at='rz', t=frame_time)

    # get updated quaternion
    new_q = matrixUtil(np.ravel(new_matrix).tolist(), q=True, qt=True)
    # also set the vector visualizer
    vector_visualizer = PyNode(get_vectorviz_name(actor_id))
    setKeyframe(vector_visualizer, v=(new_q[1]*10), at='tx', t=frame_time)
    setKeyframe(vector_visualizer, v=(new_q[2]*10), at='ty', t=frame_time)
    setKeyframe(vector_visualizer, v=(new_q[3]*10), at='tz', t=frame_time)

    # OLD STYLE: transform the w value to swivel in degrees
    swivel = get_rotation_swivel_name(actor_id)
    swivel_value = math.degrees(math.acos(new_q[0]) * 2)
    setKeyframe(swivel, v=swivel_value, at = 'rx', t=frame_time)

def get_rigid_body_obj(rb_list, actor_id=-1, pri_id=-1, name="", boost_id=-1, cars_only=False):
    print('     get rigid body obj from actor', actor_id, '  pri', pri_id, '  name', name, '  boost', boost_id)
    if actor_id >= 0:
        print('checking by actorid')
        for car in rb_list:
            if cars_only and car.IS_CAR == False: continue
            #car.display()
            if car.actor_id == actor_id:
                print('  found by actor')
                car.display()
                return car
    elif pri_id >= 0:
        print('checking by PRI')
        for car in rb_list:
            if car.IS_CAR == False: continue
            #car.display()
            if car.pri_id == pri_id:
                print('  found by PRI')
                car.display()
                return car
    elif name != "":
        print('checking by name')
        for car in rb_list:
            if cars_only and car.IS_CAR == False: continue
            #car.display()
            if car.player_name == name:
                print('  found by name')
                car.display()
                return car
    elif boost_id != "":
        for car in rb_list:
            if car.IS_CAR == False: continue
            if car.boost.actor_id == boost_id: return car
    print('  did NOT find rigid body')
    return None

def attach_rigid_body(rb_object, frame_time):
    print('lets try to attach car', rb_object.player_name)
    # first, check if car has everything it needs
    # is PRI ID -1? return none
    if rb_object.pri_id < 0:
        print('no valid PRI ID')
        return None
    # is car id -1? return none
    if rb_object.actor_id < 0:
        print('no valid Actor ID')
        return None

    actor_id = rb_object.actor_id
    # get player's car geo
    geo = rb_object.geo_name

    # get actor rotate node (from actor_id)
    rot_parent = get_rotation_name(actor_id)

    # does car geo already have a constraint(s) on it?
    cons = listConnections(geo, type='parentConstraint')
    # remove duplicates
    cons_short = [*set(cons)]
    print('   constraints on actor %d are %s' % (actor_id, cons_short))
    constraint_node = None
    for c in cons_short:
        target_list = parentConstraint(c, targetList = True, query =True)
        weight_list = parentConstraint(c, weightAliasList=True, query=True)
        print('     target list > ', target_list)
        for i, target in enumerate(target_list):
            attr_name = weight_list[i].split('.')[1].split("'")[0]
            # if the constraint points somewhere else, turn it off
            if target != rot_parent:
                print('        target %s is not RotPar %s' % (target,rot_parent))
                print('        Zero KF for Constraint >', c, attr_name)
                setKeyframe(c, at=attr_name, v=0, t=frame_time, ott='step')
            else:
                print('         found target %s matches RotPar %s' % (target,rot_parent))
                print('        1 KF for Constraint >', c, attr_name)
                constraint_node = c
                setKeyframe(c, at=attr_name, v=1, t=frame_time, ott='step')
                print('        and frame 1 Zero KF for constraint >', c, attr_name)
                setKeyframe(c, at=attr_name, v=0, t=1, ott='step')

    # did we find no existing constraint pointing at rot_parent?
    print('constrain node found? >', constraint_node)
    if not constraint_node:
        # create new constraint
        constraint_node = parentConstraint(rot_parent, geo, mo = False)
        print('        new constraint node name is > ', constraint_node)
        # get first target attribute
        w = parentConstraint(constraint_node, weightAliasList = True, query= True)[0]
        w_att = w.split('.')[1].split("'")[0]
        print('        makein new Constraint >',constraint_node, 'attr', w_att)
        # kf 0 at 1
        setKeyframe(constraint_node, at=w_att, v=0, t=1, ott='step')
        # kf 1 at current time
        setKeyframe(constraint_node, at=w_att, v=1, t=frame_time, ott='step')

    # return the node name as proof of work
    print('')
    return constraint_node

def detach_rigid_body(rb_object, frame_time):
    print('      deactivate constraints')
    geo = rb_object.geo_name

    # find constraint(s) on it
    cons = listConnections(geo, type='parentConstraint')
    # remove duplicates
    cons_short = [*set(cons)]
    for c in cons_short:
        target_list = parentConstraint(c, targetList = True, query =True)
        weight_list = parentConstraint(c, weightAliasList=True, query=True)
        print('     deactivating target list > ', target_list)
        for i, target in enumerate(target_list):
            attr_name = weight_list[i].split('.')[1].split("'")[0]
            # if the constraint points somewhere else, turn it off
            setKeyframe(c, at=attr_name, v=0, t=frame_time, ott='step')

def spawn_actors(event_dict, frame_time, rb_list):
    global active_actors_list
    actor_id = event_dict["actor_id"]
    print('spawning actor>', actor_id)

    # WHAT KINDS OF ACTOR IS IT? CAR, BALL? PRI? ACCESSORY?
    object_class = event_dict["class_name"]
    if object_class not in object_classes_list: return None

    # get matching actor locator (create if necessary)
    actor_name = get_actor_locator(actor_id, object_class)
    active_actors_list.append(actor_id)
    print("updated active list>", active_actors_list)

    if object_class == "TAGame.Car_TA":
        rb = get_rigid_body_obj(rb_list, actor_id=actor_id)
        # if the actor association is already set
        if rb:
            # go ahead and try to attach it
            print('  spawn found valid rb with actor id', actor_id)
            rb.display()
            attach_rigid_body(rb, frame_time)
        else:
            print("  spawn couldnt find a car with actor id %d", actor_id)

    if object_class == "TAGame.Ball_TA":
        # ball is always the first item in the rb list
        print("    spawning ball to actor id>", actor_id)
        rb = rb_list[0]
        rb.actor_id = actor_id
        attach_rigid_body(rb, frame_time)


    if object_class == "TAGame.CarComponent_Boost_TA":
        print(' spawn a boost of actor Id >', actor_id)
        # OK- -- Car objects already have a Boost object with undefined actor_id
        # and this spawn creates a "Boost" with only its own actor_id,
        # not the car. So we need  to hold on to this list of Boost actors
        # until a known boost_ta actor passes update / "TAGame.CarComponent_TA:Vehicle"
        spawned_boost_list.append(actor_id)

def set_car_actor_id(event_dict, frame_time, rb_list):
    global unclaimed_pawn_list
    print('    set car actor ID ')
    actor_id = event_dict["actor_id"]
    pri = event_dict["pri_id"]
    car = get_rigid_body_obj(rb_list, pri_id=pri)
    if car:
        print('  found car with PRI id', pri)
        car.display()
        car.actor_id = actor_id
        car.display()
        # try to attach car to actor
        attach_rigid_body(car, frame_time)
        return car
    else:
        print("  couldnt find a car with PRI %d" % pri)
        add_pawn = True
        for p in unclaimed_pawn_list:
            if p.pri_id == pri: add_pawn = False

        if add_pawn:
            p = Unclaimed_Pawn(pri, actor_id)
            unclaimed_pawn_list.append(p)
            print("    adding car %d : pri %d to unclaimed pawn list " % (actor_id, pri))
            print("   UCP >", unclaimed_pawn_list)
            #for u in unclaimed_pawn_list:
            #    u.display()
        return None

def set_car_PRI_id(event_dict, frame_time, rb_list):
    ## this tells us name of player for this PR so we can set PRI of car)
    actor_id = event_dict["actor_id"]
    name = event_dict["player_name"]
    car = get_rigid_body_obj(rb_list, name=name)
    if car:
        print('   found car with name ', name)
        car.display()
        car.pri_id = actor_id
        car.display()
        # try to attach car to actor
        attach_rigid_body(car, frame_time)
    else: print("couldnt find a car with name %s" % name)

def unclaimed_pawn_cleanup(frame_time, rb_list):
    if unclaimed_pawn_list:
        print('unclaimed pawn cleanup has %d items' % len(unclaimed_pawn_list))
        for u in unclaimed_pawn_list:
            car_id = u.car_id
            pri = u.pri_id
            print('looking for %d and pri %d' % (car_id, pri))
            dummy_dict = {"time": 0,
                        "actor_id": car_id,
                        "event_type": "Pawn_PRI",
                        "pri_id": pri}
            test = set_car_actor_id(dummy_dict, frame_time, rb_list)
            if test:
                print('    United actor %d and PRI %d !!!' % (car_id, pri))
                unclaimed_pawn_list.remove(u)

def ignite_boost(car, frame_time):
    print('boost!')
    boost_geo = car.boost.boost_geo
    setKeyframe(boost_geo, at='scale', v=1, t=frame_time, ott='step')
    # set it to turn off in one second?
    setKeyframe(boost_geo, at='scale', v=0, t=frame_time+18, ott='step')
    # and check if there is a keyframe between now and then?

def destroy_actors(event_dict, frame_time, rb_list):
    actor_id = event_dict["actor_id"]

    # If we don't recognize this actor, ignore it
    if actor_id not in active_actors_list: return None
    print('DESSSTTTTOORRRYYY')

    # take this actor off the list
    active_actors_list.remove(actor_id)
    print("updated active list>", active_actors_list)
    # try to see if it's a car object
    rigid_body = get_rigid_body_obj(rb_list, actor_id)
    if rigid_body:
        print('despawn car/ball')
        # Deactivate the current constraints
        detach_rigid_body(rigid_body, frame_time)
        # set PRI_ID and CAR_ID to -1
        rigid_body.actor_id = -1
        rigid_body.pri_id = -1
        # also hide the child mesh? or just move it away? scale to zero?

    else:
        print('despawn something else')
        # This is for accessories
        # ask cars list if they know this actor

        # in which case set that car.boost.actor_id to -1

def show_countdown(event_dict, frame_time):
    count = event_dict["countdown_number"]
    print("COUNTDOWN!", count)
    # Show Big Number based on count
    # Big Number fade size

def do_actor_events(event_dict, frame_time, rb_list):
    global active_actors_list
    actor_id = event_dict["actor_id"]

    #print("  do %s for actor_id %s "\
    #      % (event_dict["event_type"], actor_id))

    if "spawned" in event_dict["event_type"]:
        spawn_actors(event_dict, frame_time, rb_list)

    ## (We can set Actor_id" on the car with this PRI)
    if "Pawn_PRI" in event_dict["event_type"]:
        print(' event Pawn_PRI sets Actor ID >', event_dict)
        set_car_actor_id(event_dict, frame_time, rb_list)

    ## this tells us name of player for this PR so we can set PRI of car)
    if "PRI_name" in event_dict["event_type"]:
        print(' event PRI_name sets PRI_id ', event_dict)
        set_car_PRI_id(event_dict, frame_time, rb_list)

    if "destroyed" in event_dict["event_type"]:
        destroy_actors(event_dict, frame_time, rb_list)

    if "RBState" in event_dict["event_type"]:
        if actor_id not in active_actors_list: return None
        # maybe write this
        #key_transforms(actor_id, event_dict["loc"], frame_time)
        key_location(actor_id, event_dict["loc"], frame_time)
        key_rotation(actor_id, event_dict["rot_q"], frame_time)

    if "Active" in event_dict["event_type"]:
        # deploy the booost
        car = get_rigid_body_obj(rb_list, boost_id=actor_id)
        boost_value = event_dict["active_value"]
        if car:
            print("     ZOOM activated actor >", car.actor_id, "value of >",boost_value)
            ignite_boost(car, frame_time)
        else:
            print("      ZOOM activated, cant find car. boost value >", boost_value)
        #
    if "Vehicle" in event_dict["event_type"]:
        # actor_id is a car component,  # car_id = actor_id
        if actor_id in spawned_boost_list:
            car_id = event_dict["car_id"]
            car = get_rigid_body_obj(rb_list, actor_id=car_id )
            if car:
                print('     attaching BOOOST actor %d to car actor %d' % (actor_id, car_id))
                car.boost.actor_id = actor_id
                spawned_boost_list.remove(actor_id)
            else:
                print('   wwwaaaaaaaa cant find car %d for this BOOST %d' % (car_id, actor_id))

    if "Countdown" in event_dict["event_type"]:
        show_countdown(event_dict, frame_time)

    if event_dict["event_type"] == "STOP":
        print("XXXXXXXXXXX Halting execution for STOP event")
        # sys.exit("Found STOP message")
        return "STOP"

def create_rb_cam(rb):
    # add a camera to follow it around
    print('making a camera for', rb.player_name)

    # Create Camera and Cam_Par
    camera_name = "camera_%s" % rb.player_name
    car_cam = camera(n=camera_name, focalLength=24)[0]
    car_cam_shp = car_cam.getShape()
    setAttr("%s.locatorScale" % car_cam_shp, 10)
    setAttr("%s.translateX" % car_cam, 60)
    setAttr("%s.translateY" % car_cam, 15)
    setAttr("%s.rotateX" % car_cam, -10)
    setAttr("%s.rotateY" % car_cam, 90)

    # create a locator to constrain to the car
    loc_name = "cam_loc_%s" % rb.player_name
    cam_loc = spaceLocator(n=loc_name)
    parent(car_cam, cam_loc)
    #parent(cam_loc, rb.geo_name)
    # DO POINT CONSTRAINT ON CAM PARENT
    pointConstraint(rb.geo_name, cam_loc, mo = False)


def setup_scene(header):
    print("foo")
    # create the ball and the list of rigid bodies
    ball = Ball()
    create_rb_cam(ball)
    rb_list = [ball]

    ### get player list
    player_list = header["player_list"]
    print("player list>", player_list)
    name_list = []
    team_id_list = []
    for p in player_list:
        name_list.append(p["player_name"])
        team_id_list.append(p["team"])

    #### CREATE CAR MODELS
    l = len(player_list)
    print("length", l)
    cars = [Car() for i in range(l)]
    for i,car in enumerate(cars):
        car.player_name = name_list[i]
        car.team = team_id_list[i]
        # duplicate orange or blue car

        if car.team == 1:
            car_name = 'car_%s_%s' % ('orange', car.player_name)
            new_car = duplicate(orange_geo, n = car_name)
        else:
            car_name = 'car_%s_%s' % ('blue', car.player_name)
            new_car = duplicate(blue_geo, n = car_name)
        # congrats on your New Car!
        car.geo_name = new_car
        # add a boost to this car
        boost = duplicate(boost_geo)
        parent(boost, new_car)
        car.boost.boost_geo = boost
        # make it invisible
        setKeyframe(boost, v=0, at='scale', t=1, ott='stepnext')
        # add a camera
        create_rb_cam(car)

    # add the cars to the list
    rb_list.extend(cars)

    print("Car List complete > ")
    for rb in rb_list:
        rb.display()
    return rb_list


def do_rotation_cleanup():
    #### add Euler Cleanup to all rotations
    rotators = ls("actor_*_rot")

    rot_list = []
    for r in rotators:
        r_curves = []
        r_curves.append("%s.rotateX" % r)
        r_curves.append("%s.rotateY" % r)
        r_curves.append("%s.rotateZ" % r)
        rot_list.append(r_curves)

    for r in rot_list:
        filterCurve(r)
    ### Someday Solve This Rotation Stutff


def main(json_file):
    print('###### LETS GO #########')
    openFile(maya_template, f=True)
    saveAs(maya_file, f=True)

    # get JSON
    data = agFileTools.read_json(json_file)
    update_list = data["events"]
    # Set up player cars based on team list
    rb_list = setup_scene(data["header"])

    # start processing events
    first = True
    result = None
    for i, event_dict in enumerate(update_list):
        #if i > 200: break

        # get time in frame numbers
        frame_time = int (event_dict["time"] * 30)
        print('f=',frame_time, ' time=', event_dict["time"])
        # set playback start / end
        if event_dict["event_type"] == "Countdown":
            if first:
                playbackOptions(minTime = (frame_time-15))
                first = False
        playbackOptions(maxTime = frame_time)
        # Go Do This Event 
        result = do_actor_events(event_dict, frame_time, rb_list)

        unclaimed_pawn_cleanup(frame_time, rb_list)
        if result == "STOP": break

    do_rotation_cleanup()

    print("Done I guess")

main(json_file)
