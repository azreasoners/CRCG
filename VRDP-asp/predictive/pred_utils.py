import numpy as np
np.seterr(divide='ignore')

colors={'gray', 'red', 'blue', 'green', 'brown', 'cyan', 'purple', 'yellow'}
shapes={'cube', 'sphere', 'cylinder'}
materials={'metal', 'rubber'}

RAD_THRESHOLD = np.pi / 2.5

def prog_to_ids(prog,objs):
    col_idx=prog.index('filter_collision')
    split1=prog[:col_idx]
    split2=prog[col_idx+1:]

    choice_obj1=get_attrs(split1)
    choice_obj2=get_attrs(split2)
    obj1_id= partial_match(objs,choice_obj1)
    obj2_id=partial_match(objs,choice_obj2)

    return obj1_id, obj2_id


def get_attrs(split):
    split_attrs={}
    for ele in split:
        if ele in colors:
            split_attrs['color']=ele
        if ele in shapes:
            split_attrs['shape']=ele
        if ele in materials:
            split_attrs['material']=ele

    return split_attrs


def partial_match(objs,obj_attrs):
    for obj in objs:
        match = True
        for attr in obj_attrs:
            if obj_attrs[attr]==obj[attr]:
                continue
            else:
                match = False
                break
        if match:
            return obj['id']
    return 'error'
    
def AC(c_program,sim):
    c1, c2 = prog_to_ids(c_program, sim.objs)
    if c1 == 'error' or c2 == 'error':
        return 'error'
    # motion vector
    c1_slope = sim.obj_motion_dict[c1]['slope'][0][-1]
    c2_slope = sim.obj_motion_dict[c2]['slope'][0][-1]

    c1_x_sign = np.sign(sim.obj_motion_dict[c1]['slope'][1][-1])
    c2_x_sign = np.sign(sim.obj_motion_dict[c2]['slope'][1][-1])

    c1_rad_motion = np.arctan(c1_slope)
    c2_rad_motion = np.arctan(c2_slope)

    if c1_x_sign == -1:
        c1_rad_motion += np.pi
        if c1_rad_motion > 2 * np.pi:
            c1_rad_motion -= 2 * np.pi
    if c2_x_sign == -1:
        c2_rad_motion += np.pi
        if c2_rad_motion > 2 * np.pi:
            c2_rad_motion -= 2 * np.pi
    # position vector
    c1x, c1y = sim.obj_motion_dict[c1]['pos'][0][-1], sim.obj_motion_dict[c1]['pos'][1][-1]
    c2x, c2y = sim.obj_motion_dict[c2]['pos'][0][-1], sim.obj_motion_dict[c2]['pos'][1][-1]

    c1head = (c1y - c2y) / (c1x - c2x)
    c2head = (c2y - c1y) / (c2x - c1x)

    c1_rad_pos = np.arctan(c1head)
    c2_rad_pos = np.arctan(c2head)

    if np.sign(c1x - c2x) == -1:
        c1_rad_pos += np.pi
        if c1_rad_pos > 2 * np.pi:
            c1_rad_pos -= 2 * np.pi
    if np.sign(c2x - c1x) == -1:
        c2_rad_pos += np.pi
        if c2_rad_pos > 2 * np.pi:
            c2_rad_pos -= 2 * np.pi

    c1_rad_diff = abs(c2_rad_motion - c1_rad_pos)
    c2_rad_diff = abs(c1_rad_motion - c2_rad_pos)

    defer1 = False
    defer2 = False
    if c1_slope < 100:
        if c1_rad_diff < RAD_THRESHOLD:
            c1_towards = True
        else:
            c1_towards = False
    else:
        c1_towards = True
        defer1 = True
    if c2_slope < 100:
        if c2_rad_diff < RAD_THRESHOLD:
            c2_towards = True
        else:
            c2_towards = False
    else:
        c2_towards = True
        defer2 = True
    if (c1_towards and not defer1) or (c2_towards and not defer2):
        if not defer1 and not defer2:
            return 1  # they are moving towards each other
        else:
            return 0  # both objects are not moving
    else:
        return 0  # they are not moving towards each other
