import sys
import json
import numpy as np
import torch


import os
import subprocess

def get_2d_coor(x3d, y3d, z3d=0.2):
    cam_mat = np.array(((-207.8461456298828, 525.0000610351562, -120.00001525878906, 1200.0003662109375),
                        (123.93595886230469, 1.832598354667425e-05, -534.663330078125, 799.9999389648438),
                        (-0.866025447845459, -3.650024282819686e-08, -0.4999999701976776, 5.000000476837158),
                        (0, 0, 0, 1)))
    pos_3d = np.array([[x3d], [y3d], [z3d], [1.0]], dtype=np.float32)
    uv = cam_mat[:3].dot(pos_3d)
    pos_2d = uv[:-1] / uv[-1]
    return pos_2d

INFERENCE_TIME=1860 
EXTRA_BACKTRACK = 2 # extra frames 
BACKTRACK = 1 # how many frames to backtrack after simulated object affects unsimulated object 
all_sims_dict = json.load(open('counterfactual/all_sims_dict.json'))
visualize = False
if visualize: #pip install taichi for visualization
    import taichi as ti
query_num = int(sys.argv[2] )


for process_index in range(int(sys.argv[1]), int(sys.argv[1])+1):
    
    sims_dict_vid_name = 'sim_%05d.json' % process_index
    questions_info = all_sims_dict[sims_dict_vid_name]
    questions_info = [questions_info[query_num]]
    ASP_sim_output=list()
    #breakpoint()
    for query in questions_info:
        print(query)
        vid_result_dir = 'results_video/{0}_{1}'.format(process_index,query_num)
        if visualize:
            if not os.path.exists(vid_result_dir):
                os.mkdir(vid_result_dir)
        object_dict_name =           f'data/object_dicts_with_physics/objects_{process_index:05d}.json'
        object_dict = json.load(open(object_dict_name))
        output_dict = json.load(open(f'data/object_simulated/sim_{process_index:05d}.json'))
        frame_info_dict = json.load(open(f'data/frame_info/frameInfo_{process_index:05d}.json'))
        
        frame_info_dict['orig_traj']['x']=torch.tensor(frame_info_dict['orig_traj']['x'])
        frame_info_dict['orig_traj']['v']=torch.tensor(frame_info_dict['orig_traj']['v'])
        frame_info_dict['orig_traj']['angle']=torch.tensor(frame_info_dict['orig_traj']['angle'])

        obj2idx= {k:idx  for idx,k in enumerate(object_dict.keys())}
        
        #obj to be removed
        obj_removed = query['obj_removed'][0]
        
        #read in sim facts
        max_sim = 127
        
        sims_dict={idx_num:(None if str(idx_num) not in query['sim'] else query['sim'][str(idx_num)])  for idx_num in range(len(object_dict.keys())) }
    
        sims_dict={key:value if value is not None else max_sim for key,value in sims_dict.items()}
        sims_dict = {key:value-1 if value >= 5 else value for key,value in sims_dict.items()}
        earliest_frame = min(sims_dict.values())
        earliest_obj_orig = min(zip(sims_dict.values(), sims_dict.keys()))[1]
        
        earliest_frame = earliest_frame if earliest_frame<=127 else 127
        start_sim_frame = earliest_frame-EXTRA_BACKTRACK
        
        too_early= earliest_frame<5
        if too_early:
            break

    
        device = 'cpu'
    
        n_balls = len(object_dict)
        target_x = torch.zeros((128, n_balls, 2), dtype=torch.float32).to(device) + 1000
    
        shapes = []
        shape_dict = {
            'sphere': 0,
            'cube': 1,
            'cylinder': 2
        }
        color_dict = {
            'gray': 0x708090,
            'red': 0xDC143C,
            'blue': 0x0000FF,
            'green': 0x228B22,
            'brown': 0x8b4513,
            'yellow': 0xFFFF00,
            'cyan': 0x00FFFF,
            'purple': 0x800080
        }
        for object_index, identity in enumerate(object_dict.keys()):
            locations = torch.tensor(object_dict[identity]['trajectory']).to(device)
            target_x[:locations.shape[0], object_index, :] = locations
            shapes.append(shape_dict[object_dict[identity]['shape']])
    
        for object_index, identity in enumerate(object_dict.keys()):
            for step_idx in range(target_x.shape[0]):
                if target_x[step_idx][object_index][0] > 500:
                    target_x[step_idx][object_index] = frame_info_dict['orig_traj']['x'][step_idx*10][object_index]
        
        shape = torch.tensor(shapes, dtype=torch.int8).to(device)
        angle0 = frame_info_dict['orig_traj']['angle'][0].clone() 
        angle0.requires_grad = True
    
        interval = 10
        dt = 1/350
        gravity = 9.806
        radius = 0.2
        inertia = 0.4 * 0.4 / 6
        
    ################## Taichi ###################
        
        if visualize:
            vis_resolution = 1024
            gui = ti.GUI("Dynamics", (vis_resolution, vis_resolution), background_color=0xDCDCDC)
            scale = 1/6
            pixel_radius = int(radius * scale * 1024) + 1
    #############################################

        frictional = torch.tensor(0.03).to(device)
        frictional.requires_grad = True
        linear_damping = torch.tensor(0.06).to(device)
        linear_damping.requires_grad = True
        v0 = frame_info_dict['orig_traj']['v'][0].clone() 
        v0.requires_grad = True
    
        restitution = torch.tensor(frame_info_dict['orig_traj']['restitution'], dtype=torch.float32).to(device) 
        restitution.requires_grad = True
        mass = torch.tensor(frame_info_dict['orig_traj']['mass'], dtype=torch.float32).to(device) 
        mass.requires_grad = True
    
        def norm(vector, degree=2, dim=0):
            return torch.norm(vector, degree, dim=dim)
    
    
        def normalized(vector):
            return vector / norm(vector)
    
    
        def collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions):
            imp = torch.tensor([0.0, 0.0]).to(device)
            x_inc_contrib = torch.tensor([0.0, 0.0]).to(device)
            if i != j:
                dist = (x[t, i] + dt * v[t, i]) - (x[t, j] + dt * v[t, j])
                dist_norm = norm(dist)
                rela_v = v[t, i] - v[t, j]
                if dist_norm < 2 * radius:
                    dir = normalized(dist)
                    projected_v = dir.dot(rela_v)
    
                    if projected_v < 0:
                        if i < j:
                            repeat = False
                            for item in collisions:
                                if json.dumps(item).startswith(json.dumps([i, j])[:-1]):
                                    repeat = True
                            if not repeat:
                                collisions.append([i, j, round(t / 10.0)])
                        imp = -(1 + restitution[i] * restitution[j]) * (mass[j] / (mass[i] + mass[j])) * projected_v * dir
                        toi = (dist_norm - 2 * radius) / min(
                            -1e-3, projected_v)
                        x_inc_contrib = min(toi - dt, 0) * imp
            x_inc[t + 1, i] += x_inc_contrib
            impulse[t + 1, i] += imp
    
    
        def sphere_collide_cube(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions):
            imp = torch.tensor([0.0, 0.0]).to(device)
            x_inc_contrib = torch.tensor([0.0, 0.0]).to(device)
            if i != j:
                rela_v = v[t, i] - v[t, j]
                pos_xy = x[t, i] - x[t, j]
                rotate_x = pos_xy.dot(torch.tensor([torch.cos(-angle[t, j]), -torch.sin(-angle[t, j])]))
                rotate_y = pos_xy.dot(torch.tensor([torch.sin(-angle[t, j]), torch.cos(-angle[t, j])]))
                moving_direction = torch.tensor([0.0, 0.0])
                dist_norm = 0.0
                collision = True
    
                if torch.abs(rotate_x) > 2 * radius:
                    collision = False
                elif torch.abs(rotate_y) > 2 * radius:
                    collision = False
                elif torch.abs(rotate_x) <= radius:
                    if rotate_y > 0:
                        moving_direction = torch.tensor([0.0, 1.0])
                        dist_norm = rotate_y
                    elif rotate_y < 0:
                        moving_direction = torch.tensor([0.0, -1.0])
                        dist_norm = - rotate_y
                elif torch.abs(rotate_y) <= radius:
                    if rotate_x > 0:
                        moving_direction = torch.tensor([1.0, 0.0])
                        dist_norm = rotate_x
                    elif rotate_x < 0:
                        moving_direction = torch.tensor([-1.0, 0.0])
                        dist_norm = - rotate_x
                elif (torch.abs(rotate_x) - radius) ** 2 + (torch.abs(rotate_y) - radius) ** 2 <= radius ** 2:
                    if rotate_x > radius and rotate_y > radius:
                        moving_direction = normalized(torch.tensor([rotate_x - radius, rotate_y - radius]))
                        dist_norm = norm(torch.tensor([rotate_x - radius, rotate_y - radius])) + radius
                    elif rotate_x < -radius and rotate_y > radius:
                        moving_direction = normalized(torch.tensor([rotate_x + radius, rotate_y - radius]))
                        dist_norm = norm(torch.tensor([rotate_x + radius, rotate_y - radius])) + radius
                    elif rotate_x > radius and rotate_y < -radius:
                        moving_direction = normalized(torch.tensor([rotate_x - radius, rotate_y + radius]))
                        dist_norm = norm(torch.tensor([rotate_x - radius, rotate_y + radius])) + radius
                    elif rotate_x < -radius and rotate_y < -radius:
                        moving_direction = normalized(torch.tensor([rotate_x + radius, rotate_y + radius]))
                        dist_norm = norm(torch.tensor([rotate_x + radius, rotate_y + radius])) + radius
    
                if collision:
                    origin_dir = torch.tensor(
                        [moving_direction.dot(torch.tensor([torch.cos(angle[t, j]), -torch.sin(angle[t, j])])),
                         moving_direction.dot(torch.tensor([torch.sin(angle[t, j]), torch.cos(angle[t, j])]))]
                    )
                    projected_v = origin_dir.dot(rela_v)
    
                    if projected_v < 0:
                        if i < j:
                            repeat = False
                            for item in collisions:
                                if json.dumps(item).startswith(json.dumps([i, j])[:-1]):
                                    repeat = True
                            if not repeat:
                                collisions.append([i, j, round(t / 10.0)])
                        imp = -(1 + restitution[i] * restitution[j]) * (mass[j] / (mass[i] + mass[j])) * projected_v * origin_dir  # 冲量，速度变化量
                        toi = (dist_norm - 2 * radius) / min(
                            -1e-3, projected_v)
                        x_inc_contrib = min(toi - dt, 0) * imp
    
            x_inc[t + 1, i] += x_inc_contrib
            impulse[t + 1, i] += imp
    
    
        def cube_collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions):
            imp = torch.tensor([0.0, 0.0])
            x_inc_contrib = torch.tensor([0.0, 0.0])
            a_rotate = 0.0
            if i != j:
                rela_v = v[t, i] - v[t, j]
                pos_xy = x[t, j] - x[t, i]
                rotate_x = pos_xy.dot(torch.tensor([torch.cos(-angle[t, i]), -torch.sin(-angle[t, i])]))
                rotate_y = pos_xy.dot(torch.tensor([torch.sin(-angle[t, i]), torch.cos(-angle[t, i])]))
    
                moving_direction = torch.tensor([0.0, 0.0])
                collision_direction = torch.tensor([0.0, 0.0])
                dist_norm = 0.0
                r_rotate = 0.0
                rotate_dir = False
                collision = True
    
                if torch.abs(rotate_x) > 2 * radius:
                    collision = False
                elif torch.abs(rotate_y) > 2 * radius:
                    collision = False
                elif torch.abs(rotate_x) <= radius:
                    if rotate_y > 0:
                        moving_direction = torch.tensor([0.0, -1.0])
                        collision_direction = normalized(torch.tensor([-rotate_x, -radius]))
                        dist_norm = rotate_y
                        if rotate_x > 0:
                            rotate_dir = 1
                    elif rotate_y < 0:
                        moving_direction = torch.tensor([0.0, 1.0])
                        collision_direction = normalized(torch.tensor([-rotate_x, radius]))
                        dist_norm = - rotate_y
                        if rotate_x < 0:
                            rotate_dir = 1
                    r_rotate = norm(torch.tensor([radius, rotate_x]))
                elif torch.abs(rotate_y) <= radius:
                    if rotate_x > 0:
                        moving_direction = torch.tensor([-1.0, 0.0])
                        collision_direction = normalized(torch.tensor([-radius, -rotate_y]))
                        dist_norm = rotate_x
                        if rotate_y < 0:
                            rotate_dir = 1
                    elif rotate_x < 0:
                        moving_direction = torch.tensor([1.0, 0.0])
                        collision_direction = normalized(torch.tensor([radius, -rotate_y]))
                        dist_norm = - rotate_x
                        if rotate_y > 0:
                            rotate_dir = 1
                    r_rotate = norm(torch.tensor([radius, rotate_y]))
                elif (torch.abs(rotate_x) - radius) ** 2 + (torch.abs(rotate_y) - radius) ** 2 <= radius ** 2:
                    if rotate_x > radius and rotate_y > radius:
                        moving_direction = - normalized(torch.tensor([rotate_x - radius, rotate_y - radius]))
                        collision_direction = normalized(torch.tensor([-1.0, -1.0]))
                        dist_norm = norm(torch.tensor([rotate_x - radius, rotate_y - radius])) + radius
                        if rotate_y > rotate_x:
                            rotate_dir = 1
                    elif rotate_x < -radius and rotate_y > radius:
                        moving_direction = - normalized(torch.tensor([rotate_x + radius, rotate_y - radius]))
                        collision_direction = normalized(torch.tensor([1.0, -1.0]))
                        dist_norm = norm(torch.tensor([rotate_x + radius, rotate_y - radius])) + radius
                        if -rotate_x > rotate_y:
                            rotate_dir = 1
                    elif rotate_x > radius and rotate_y < -radius:
                        moving_direction = - normalized(torch.tensor([rotate_x - radius, rotate_y + radius]))
                        collision_direction = normalized(torch.tensor([-1.0, 1.0]))
                        dist_norm = norm(torch.tensor([rotate_x - radius, rotate_y + radius])) + radius
                        if rotate_x > -rotate_y:
                            rotate_dir = 1
                    elif rotate_x < -radius and rotate_y < -radius:
                        moving_direction = - normalized(torch.tensor([rotate_x + radius, rotate_y + radius]))
                        collision_direction = normalized(torch.tensor([1.0, 1.0]))
                        dist_norm = norm(torch.tensor([rotate_x + radius, rotate_y + radius])) + radius
                        if -rotate_y > -rotate_x:
                            rotate_dir = 1
                    r_rotate = norm(torch.tensor([radius, radius]))
    
                if collision:
                    origin_moving_dir = torch.tensor(
                        [moving_direction.dot(torch.tensor([torch.cos(angle[t, i]), -torch.sin(angle[t, i])])),
                         moving_direction.dot(torch.tensor([torch.sin(angle[t, i]), torch.cos(angle[t, i])]))]
                    )
                    origin_collision_dir = torch.tensor(
                        [collision_direction.dot(torch.tensor([torch.cos(angle[t, i]), -torch.sin(angle[t, i])])),
                         collision_direction.dot(torch.tensor([torch.sin(angle[t, i]), torch.cos(angle[t, i])]))]
                    )
                    projected_v = origin_moving_dir.dot(rela_v)
    
                    if projected_v < 0:
                        if i < j:
                            repeat = False
                            for item in collisions:
                                if json.dumps(item).startswith(json.dumps([i, j])[:-1]):
                                    repeat = True
                            if not repeat:
                                collisions.append([i, j, round(t / 10.0)])
                        imp = -(1 + restitution[i] * restitution[j]) * (mass[j] / (mass[i] + mass[j])) * projected_v * origin_moving_dir
                        toi = (dist_norm - 2 * radius) / min(
                            -1e-3, projected_v)
                        x_inc_contrib = min(toi - dt, 0) * imp
    
                        f_rotate = (origin_moving_dir - origin_collision_dir.dot(origin_moving_dir) * origin_collision_dir).dot(-projected_v * origin_moving_dir)
                        a_rotate = f_rotate * r_rotate / inertia
                        if rotate_dir:
                            a_rotate = -a_rotate
    
            x_inc[t + 1, i] += x_inc_contrib
            impulse[t + 1, i] += imp
            angle_impulse[t + 1, i] += a_rotate
    
    
        def collide(shape, x, v, x_inc, impulse, t, angle, angle_impulse, collisions):
            for i in range(n_balls):
                for j in range(i):
                    if shape[i] != 1 and shape[j] != 1:
                        collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
                    elif shape[i] != 1 and shape[j] == 1:
                        sphere_collide_cube(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
                    elif shape[i] == 1 and shape[j] != 1:
                        cube_collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
                    elif shape[i] == 1 and shape[j] == 1:
                        collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
    
            for i in range(n_balls):
                for j in range(i + 1, n_balls):
                    if shape[i] != 1 and shape[j] != 1:
                        collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
                    elif shape[i] != 1 and shape[j] == 1:
                        sphere_collide_cube(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
                    elif shape[i] == 1 and shape[j] != 1:
                        cube_collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
                    elif shape[i] == 1 and shape[j] == 1:
                        collide_sphere(x, v, x_inc, impulse, t, i, j, angle, angle_impulse, collisions)
    
    
        def friction(shape, x, v, x_inc, impulse, v_old, t, i):
            if shape[i] == 0:
                if v_old[0] > 0.0:
                    v[t, i][0] = max(0, v_old[0] - linear_damping * dt * v_old[0] * norm(v_old))
                elif v_old[0] < 0.0:
                    v[t, i][0] = min(0, v_old[0] - linear_damping * dt * v_old[0] * norm(v_old))
                if v_old[1] > 0.0:
                    v[t, i][1] = max(0, v_old[1] - linear_damping * dt * v_old[1] * norm(v_old))
                elif v_old[1] < 0.0:
                    v[t, i][1] = min(0, v_old[1] - linear_damping * dt * v_old[1] * norm(v_old))
            else:
                if v_old[0] > 0.0:
                    v[t, i][0] = max(0, v_old[0] - gravity * frictional * dt * normalized(v_old)[0] - linear_damping * dt * v_old[0] * norm(v_old))
                elif v_old[0] < 0.0:
                    v[t, i][0] = min(0, v_old[0] - gravity * frictional * dt * normalized(v_old)[0] - linear_damping * dt * v_old[0] * norm(v_old))
                if v_old[1] > 0.0:
                    v[t, i][1] = max(0, v_old[1] - gravity * frictional * dt * normalized(v_old)[1] - linear_damping * dt * v_old[1] * norm(v_old))
                elif v_old[1] < 0.0:
                    v[t, i][1] = min(0, v_old[1] - gravity * frictional * dt * normalized(v_old)[1] - linear_damping * dt * v_old[1] * norm(v_old))
    
        def obj_in_collisions(new_idx):
            obj_desc = list(object_dict.keys())[new_idx]
            
            collision_preds = frame_info_dict['predictions'][0]['collisions']
            
            for pred in collision_preds:
                frame=pred['frame']
                if abs(t-frame*10)<11:
                    for col_obj in pred['objects']:
                        if col_obj['color']+col_obj['material']+col_obj['shape'] == obj_desc:
                            return True
                else:
                    pass
            return False
    
        def advance(shape, x, v, x_inc, impulse, t, angle, delta_angle, angle_impulse):
            for i in range(n_balls):
                v_old = v[t - 1, i] + impulse[t, i]
                friction(shape, x, v, x_inc, impulse, v_old, t, i)
                x[t, i] = x[t - 1, i] + dt * (v[t, i] + v_old)/2 + x_inc[t, i]
                delta_angle[t, i] = delta_angle[t - 1, i] + angle_impulse[t, i]
                if delta_angle[t, i] > 0.0:
                    delta_angle[t, i] = max(0, delta_angle[t, i] - dt * gravity / 2)
                elif delta_angle[t, i] < 0.0:
                    delta_angle[t, i] = min(0, delta_angle[t, i] + dt * gravity / 2)
                angle[t, i] = angle[t - 1, i] + dt * delta_angle[t, i]
        
                    
        
        def init_inference(inference_steps):
            x = torch.zeros((inference_steps, n_balls, 2), dtype=torch.float32).to(device)
            v = torch.zeros((inference_steps, n_balls, 2), dtype=torch.float32).to(device)
            x_inc = torch.zeros((inference_steps, n_balls, 2), dtype=torch.float32).to(device)
            impulse = torch.zeros((inference_steps, n_balls, 2), dtype=torch.float32).to(device)
            angle = torch.zeros((inference_steps, n_balls), dtype=torch.float32).to(device)
            delta_angle = torch.zeros((inference_steps, n_balls), dtype=torch.float32).to(device)
            angle_impulse = torch.zeros((inference_steps, n_balls), dtype=torch.float32).to(device)
    
            x[0, :] = x0
            v[0, :] = v0
            angle[0, :] = angle0
            return x, v, x_inc, impulse, angle, delta_angle, angle_impulse
        
        
        def gui_plot():
            gui.clear()
            for ball in range(n_balls):
                if shape[ball] in [0, 2]:
                    color = color_dict[colors[ball]]
                    gui.circle((x[t, ball][1] * scale + 0.5, 0.5 - x[t, ball][0] * scale), color, pixel_radius)
                elif shape[ball] == 1:
                    color = color_dict[colors[ball]]
                    rotate_x = torch.tensor([radius * scale, radius * scale]).dot(torch.tensor([ti.cos(angle[t, ball]), -torch.sin(angle[t, ball])]))
                    rotate_y = torch.tensor([radius * scale, radius * scale]).dot(torch.tensor([ti.sin(angle[t, ball]), torch.cos(angle[t, ball])]))
                    gui.triangle((x[t, ball][1] * scale + 0.5 - rotate_y, 0.5 - x[t, ball][0] * scale + rotate_x),
                                 (x[t, ball][1] * scale + 0.5 + rotate_x, 0.5 - x[t, ball][0] * scale + rotate_y),
                                 (x[t, ball][1] * scale + 0.5 + rotate_y, 0.5 - x[t, ball][0] * scale - rotate_x),
                                 color)
                    gui.triangle((x[t, ball][1] * scale + 0.5 - rotate_y, 0.5 - x[t, ball][0] * scale + rotate_x),
                                 (x[t, ball][1] * scale + 0.5 - rotate_x, 0.5 - x[t, ball][0] * scale - rotate_y),
                                 (x[t, ball][1] * scale + 0.5 + rotate_y, 0.5 - x[t, ball][0] * scale - rotate_x),
                                 color)
            frame_file_name = vid_result_dir+f'/frame_{frame_count:05d}.png'
            gui.show(frame_file_name)
        

        def propagate_affected():
            if len(collisions)>0:
                affected = [idx for idx,val in enumerate(use_perception) if val==0]
                current_frame = t//10
                for col in collisions:
                    o0=col[0]
                    o1=col[1]
                    frame=col[2]
                    if frame< current_frame:
                        continue
                    if o0 in affected or o1 in affected and not (o0 in affected and o1 in affected):
                        if new_collision:
                            opt_indices = [idx for idx,u in enumerate(use_perception) if u==1]
                            for o in [o0,o1]:
                                if use_perception[o]==1:
                                    desc = list(object_dict.keys())[o]
                                    print(desc + ' was affected by a simulation...starting simulation')
                                    use_perception_frame[o]=t//10
                            use_perception[o0]=0
                            use_perception[o1]=0
                            return opt_indices, BACKTRACK
                        else:
                            return [], 0
                    else:
                        return [], 0
                return [],0
            else:
                return [], 0
        
        def add_affected():
            current_frame = t//10
            popped_inds = [poppedidx2idx[idx] for idx,ele in enumerate(use_perception)]
            
            opt_indices=list()
            for idx,popped_ind in enumerate(popped_inds):
                if sims_dict[popped_ind] <= current_frame:
                    if use_perception[idx] ==1:
                        if 0 not in use_perception:
                            first = True
                        if len(opt_indices)==0:
                            opt_indices = [idx for idx,u in enumerate(use_perception) if u==1]
                        else:
                            pass
                        use_perception[idx]=0
                        use_perception_frame[idx] = t//10
                        
                        desc = list(object_dict.keys())[idx]
                        orig_idx = poppedidx2idx[idx]
                        print(desc + f' was affected in original video...starting simulation at time {t}')
            return opt_indices 

    
        
        def update_position(x_current, opt_indices,backtrack=0):
            t_start = (t-backtrack)//10-EXTRA_BACKTRACK
            t_start_10 = t_start*10
            n_balls=len(object_dict)

            x0 = torch.zeros((n_balls, 2), dtype=torch.float32).to(device)
            
            non_opt_indices = [i for i in range(len(object_dict)) if i not in opt_indices]
            non_opt_indices_orig = [i for i in range(len(object_dict)) if i not in opt_indices_orig]

            x0.data[opt_indices] = target_x[t_start][opt_indices_orig]
            x0.data[non_opt_indices] = x_current[t_start_10][non_opt_indices]
            
            return  x0[opt_indices], t_start_10,opt_indices

        
        object_dict = json.load(open(object_dict_name))
        
        obj_removed_desc = ''.join([v for k,v in output_dict['objects'][obj_removed].items() if k!='id'])
        assert obj_removed_desc == query['obj_removed'][1]
        object_dict.pop(obj_removed_desc)
        
        
        poppedidx2idx = {obj_idx:obj2idx[obj] for obj_idx,obj in enumerate(list(object_dict.keys()))} #orig idx 2 when popped 
        idx2poppedidx = dict((v, k) for k, v in poppedidx2idx.items())
        use_perception = [1 for _ in object_dict]
        use_perception_frame = [None for _ in object_dict]
        
        n_balls = len(object_dict)
        
        v0 = torch.zeros((n_balls, 2), dtype=torch.float32).to(device)
        v0.requires_grad = True
        x0 = torch.zeros((n_balls, 2), dtype=torch.float32).to(device)
        x0.requires_grad = True
        restitution = torch.zeros((n_balls), dtype=torch.float32).to(device) + 0.8
        restitution.requires_grad = True
        mass = torch.zeros((n_balls), dtype=torch.float32).to(device) + 1
        mass.requires_grad = True
        
        shapes = []
        colors = []
        materials = []
        angles = []
        for object_index, identity in enumerate(object_dict.keys()):
            orig_idx=poppedidx2idx[object_index]
            shapes.append(shape_dict[object_dict[identity]['shape']])
            colors.append(object_dict[identity]['color'])
            materials.append(object_dict[identity]['material'])
            x0.data[object_index] = torch.tensor(target_x[0][orig_idx].clone().detach()).to(device)
            v0.data[object_index] = torch.tensor(frame_info_dict['orig_traj']['v'][0][orig_idx]).to(device)
            mass.data[object_index] = object_dict[identity]['mass']
            restitution.data[object_index] = object_dict[identity]['restitution']
            angles.append(frame_info_dict['orig_traj']['angle'][0][orig_idx])
            
        shape = torch.tensor(shapes, dtype=torch.int8).to(device)
        angle0 = torch.tensor(angles, dtype=torch.float32).to(device)
    
        
        steps = 1860 
        
        x, v, x_inc, impulse, angle, delta_angle, angle_impulse = init_inference(steps)
        
        collisions = []
        collision_count = 0
        new_collision = False
        frame_count=0
        
        earliest_frame_simulation=False
        
        t=1
        post_vid=False
        while t <1860:
            
            new_collision=False
            
            if t==earliest_frame*10 and not earliest_frame_simulation:
                opt_indices_earliest_frame = [idx_i for idx_i,i in enumerate(use_perception) if i==1] 
                earliest_frame_simulation=True
            else:
                opt_indices_earliest_frame=[]
            

            
            if len(collisions)>collision_count:
                new_collision=True
                collision_count+=1
            
            opt_indices1 = add_affected()
            opt_indices2, backtrack = propagate_affected()
            
            opt_indices = list(set().union(sorted(opt_indices1),sorted(opt_indices2),sorted(opt_indices_earliest_frame)))
            
            opt_indices_orig = [poppedidx2idx[idx] for idx in opt_indices]

            if opt_indices and t <1280:

                x0_target, t_start_10, opt_indices  = update_position(x, opt_indices=opt_indices, backtrack=backtrack)
                t=t_start_10 +1  
                x[t_start_10][opt_indices]=x0_target
                x_inc[t_start_10:]=0
                impulse[t_start_10+1:]=0
                delta_angle[t_start_10+1:]=0
                angle_impulse[t_start_10+1:]=0

            collision_count=len(collisions)
            collide(shape, x, v, x_inc, impulse, t - 1, angle, angle_impulse, collisions)  
            advance(shape, x, v, x_inc, impulse, t, angle, delta_angle, angle_impulse)
            
            if visualize and t % interval == 0:
                gui_plot()

                frame_count+=1
            t+=1
        
        if visualize:
            video_filename = f'{process_index}_{query["q_idx"]}_{query_num}.mp4'
            p = subprocess.Popen(['ti', 'video', '-o', video_filename], cwd=os.path.join(os.getcwd(),vid_result_dir.replace('/','\\')))
            p.wait()
    
        shapes = []
        shape_dict = {
            'sphere': 0,
            'cube': 1,
            'cylinder': 2
        }
        reverse_shape_dict = {
            0: 'sphere',
            1: 'cube',
            2: 'cylinder'
        }
        colors = []
        materials = []
        for object_index, identity in enumerate(object_dict.keys()):
            shapes.append(shape_dict[object_dict[identity]['shape']])
            colors.append(object_dict[identity]['color'])
            materials.append(object_dict[identity]['material'])
    
        
        def obj2string_orig_idx(obj):
            string = obj['color']+obj['material']+obj['shape']
            
            popped_idx = [idx for idx,i in enumerate(list(object_dict.keys())) if i == string ][0]
            orig_idx = poppedidx2idx[popped_idx]
            return string, popped_idx, orig_idx
        CF_collisions=list()
        
        gt_objects = list(object_dict.keys())
        orig_collisions = output_dict['predictions'][0]['collisions'].copy()
        old_collisions = output_dict['predictions'][0]['collisions'].copy()
        
        uniq_collisions = []
        for item in old_collisions:
            
            for item_obj in item['objects']:
                if item_obj['color']+item_obj['material']+item_obj['shape']==obj_removed_desc:
                    orig_collisions.remove(item)
                    break
                
        old_collisions = orig_collisions.copy() 
        
        for item in old_collisions:
            #if item['frame'] > earliest_frame: # remove > earliest_frame collisions from old collisions
            o0_string,o0_popped, o0_orig = obj2string_orig_idx(item['objects'][0])
            o1_string, o1_popped, o1_orig = obj2string_orig_idx(item['objects'][1])
            
            if item['frame'] < use_perception_frame[o0_popped] and item['frame'] < use_perception_frame[o1_popped]:
                pass
            else:
                orig_collisions.remove(item)
                print('removed collision', item['frame'])
                
    
        collisions=[collision for collision in collisions if collision[2] >= start_sim_frame ]
    
        collisions_copy = collisions.copy()
        for item in range(len(collisions) - 1, -1, -1):
            i, j, frame = collisions_copy[item]
            if collisions.count(collisions_copy[item]) > 1: #remove duplicates 
                collisions.remove(collisions_copy[item])
        collisions_copy = collisions.copy()
        for item in range(len(collisions) - 1, -1, -1):
            i, j, frame = collisions_copy[item]
            if [i, j, frame - 2] in collisions or [i, j, frame - 1] in collisions: #remove duplicate collisions off by 1 or 2 frames (remove later ones)
                collisions.remove(collisions_copy[item])
        for collision_index, item in enumerate(collisions): #append collisions from 
            i, j, frame = item
            CF_collisions.append({
                'frame': frame,#+start_sim_frame,
                'objects': [{
                    'color': colors[i],
                    'material': materials[i],
                    'shape': reverse_shape_dict[shapes[i]],
                }, {
                    'color': colors[j],
                    'material': materials[j],
                    'shape': reverse_shape_dict[shapes[j]],
                }]
            })
    
        CF_collisions = orig_collisions+CF_collisions #add perceived (non-simulated, before start_sim_frame) collisions with simulated collisions (simulated, after start_sim_frame)
        ASP_sim_output.append({**query,**{'sim_ASP_col':CF_collisions},**{'too_early':too_early}})
    

    
    json.dump(ASP_sim_output, open(f'data/ASP_SIM_results/simulatedASP_{process_index:05d}_{query_num}.json', 'w'))
    
