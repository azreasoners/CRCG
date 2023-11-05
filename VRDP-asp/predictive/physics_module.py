from collections import OrderedDict
import json
import numpy as np

class Physics():
    def __init__(self,frame_params):
        
        self.frame_params=frame_params
        
        self.TIME_DIFF=frame_params['TIME_DIFF']
        self.VIDEO_END=frame_params['VIDEO_END']
        self.HIT_THRESHOLD=frame_params['HIT_THRESHOLD']
        self.PREDICT_END=frame_params['PREDICT_END']
        
        
    def get_subdict(self, obj):
        
        subdict=OrderedDict()
        subdict['color']=obj['color']
        subdict['material']=obj['material']
        subdict['shape']=obj['shape']
        subdict_key=json.dumps(subdict)
        return subdict_key

    def get_attr_to_idx(self, pred_objs,frames,attr_to_idx=dict()):
    
        for obj in pred_objs:
            subdict_key=self.get_subdict(obj)
            obj_id=obj['id']
            if subdict_key not in attr_to_idx:
                attr_to_idx[subdict_key]=obj_id
                    
        return attr_to_idx
    
    def convert_attr_to_idx(self, frames,attr_to_idx):
    
        subdicts=dict()
        obj_num=0
        
        for f in frames:
            for obj in f['objects']:
                subdict_key=self.get_subdict(obj)
                if subdict_key not in subdicts:
                    subdicts[subdict_key]=attr_to_idx[subdict_key]
                    obj_num+=1
        return subdicts

    def convert_frame(self, frame,attr_to_idx):
        frame_dict=dict()
        for obj in frame['objects']:
            key_str=self.get_subdict(obj)
            obj_num=attr_to_idx[key_str]
            frame_dict[obj_num]=obj
        
        return frame_dict

    def replace_zeros(self, arr):
        
        arr_binary=(arr==0)*1
        
        start_idx=-1
        end_idx=-1
        if arr_binary[0]==1:
            for i in range(len(arr_binary)-1):
                if arr_binary[i]==1:
                    start_idx=i
                else:
                    break
        if arr_binary[-1]==1:
            for i in reversed(range(len(arr_binary))):
                if arr_binary[i]==1:
                    end_idx=i
                else:
                    break
        
        if start_idx!=-1:
            beginning_value=arr[start_idx+1]
            arr[np.arange(start_idx+1)]=beginning_value
        
        if end_idx!=-1:
            end_value=arr[end_idx-1]
            arr[np.arange(end_idx,len(arr))]=end_value
        return arr

    def get_velocities(self, arr):
    
        vel_list=[]
        for i in range(len(arr)-1):
            vel_list.append((arr[i+1]-arr[i])/self.TIME_DIFF)
        vel_np=np.array(vel_list)
        return vel_np
    
    def get_friction(self, arr):
    
        friction_window=round(8/self.TIME_DIFF)
        friction_term=-(arr[self.VIDEO_END]-arr[self.VIDEO_END-friction_window-1])/friction_window*self.TIME_DIFF
        
        return friction_term
    
    def get_slopes(self, X,Y):
    
        top=[]
        bottom=[]
        slope_window=int(5/self.TIME_DIFF)
    
        for i in range(slope_window,len(X)):
            top.append((Y[i]-Y[i-slope_window]))
            bottom.append((X[i]-X[i-slope_window]))
        
        for i in range(slope_window):
            top.insert(0,top[0])
            bottom.insert(0,bottom[0])
        
        top=np.array(top)
        bottom=np.array(bottom)
    
        no_movement_mask=np.ones(len(top))-(abs(top)<.05)*1
        no_movement_mask=no_movement_mask+np.ones(len(bottom))-(abs(bottom)<.05)*1
        no_movement_mask=np.ones(len(top))-(no_movement_mask==0)*1
        top=top*no_movement_mask
        
        top[np.where(no_movement_mask==0)]=np.nan
        
        bottom[np.where(bottom==0)]=.1
    
        return np.concatenate((np.array([0]),top/bottom)),np.concatenate((np.array([0]),bottom))

    def get_2d_velocity(self, arr1,arr2):
        twod_velocity = np.sqrt(np.power(arr1,2)+np.power(arr2,2))
        return twod_velocity

    def get_post_video_positions(self, vel, pos, slopes, friction, video_end, additional_frames=0,same=False):
    
        vel=np.copy(vel)
        vel[np.flatnonzero(vel<.005)]=0
        
        init_vel=vel[video_end-int(9/self.TIME_DIFF)]
        
        if init_vel==0:
            friction=0
        
        pre_arr=vel[:video_end]
        post_arr=vel[video_end:]
        
        post_len=self.frame_params['PREDICT_END']-len(pre_arr)
        
        post_vel=[init_vel-friction*i for i in range(post_len)]
        post_vel=[p for p in post_vel if p >0]+[0 for p in post_vel if p<=0]
        post_vel_np=np.array(post_vel)
        
        if np.isnan(slopes[0][video_end-1]):
            thetas=None
            theta=None
        else:
            thetas=np.arctan(slopes[0])
            theta=thetas[video_end-1] 
    
        y_sign=np.sign(pos[1][video_end-1]-pos[1][video_end-2]) 
        x_sign=np.sign(slopes[1][video_end-1])
    
        if not np.isnan(slopes[0][video_end-1]):    
            if x_sign==-1:
                theta+=np.pi
    
        post_distance=list()
        
        for v in post_vel:
            post_distance.append(v*self.TIME_DIFF)
        
        post_distance=np.cumsum(np.array(post_distance))
        
        if np.isnan(slopes[0][video_end-1]):
            x_pos=np.array([pos[0][video_end-1] for i in range(len(post_vel))])
            y_pos=np.array([pos[1][video_end-1] for i in range(len(post_vel))])
    
        else:
            x_pos=np.cos(theta)*post_distance+pos[0][video_end]
            y_pos=np.sin(theta)*post_distance+pos[1][video_end]
        
        predicted_full=np.concatenate((pre_arr, post_vel_np))
        
        x_pos=np.concatenate([pos[0][:self.frame_params['PREDICT_END']-len(x_pos)],x_pos])
        y_pos=np.concatenate([pos[1][:self.frame_params['PREDICT_END']-len(y_pos)],y_pos])
    
        if same:
            x_pos=np.ones(x_pos.shape)*999
            y_pos=np.ones(y_pos.shape)*999
    
        return x_pos,y_pos

    def get_predicted_trajectory(self, vel, pos, slopes, obj_num, removed, friction, video_end, additional_frames=0):
    
        if obj_num == removed:
            same=True
        else:
            same=False
    
        a,b=self.get_post_video_positions(vel, pos, slopes, friction, video_end=video_end, additional_frames=additional_frames,same=same)
        
        padding=self.frame_params['PREDICT_END']-len(a)
        x=np.pad(a,(padding,0),mode='edge')
        
        padding=self.frame_params['PREDICT_END']-len(b)
        y=np.pad(b,(padding,0),mode='edge')
        
        return [x,y]

    def simulate(self, pred_objs,u_vid,collisions, frame_params, sims=[], obj_to_be_removed=None, post_vid_only=False):
    
        frame1=u_vid[-2]
        frame2=u_vid[-1]
    
        velocity=list()
    
        for idx,obj1 in enumerate(frame1['objects']):
    
            for obj2 in frame2['objects']:
                if obj1==obj2:
                    continue
                if obj1['color']==obj2['color'] and obj1['material'] == obj2['material'] and obj1['shape']==obj2['shape']:
                    vx=(obj2['x']-obj1['x'])/self.TIME_DIFF
                    vy=(obj2['y']-obj1['y'])/self.TIME_DIFF
    
                    velocity.append({'vx':vx,'vy':vy, 'color': obj1['color'], 'material':obj1['material'],'shape':obj1['shape']})
    
        attr_to_idx=self.get_attr_to_idx(pred_objs,u_vid,dict())
        idx_to_attr = {v: eval(k) for k, v in attr_to_idx.items()}
        obj_motion_dict=dict()
    
        for key in attr_to_idx:
            obj_motion_dict[attr_to_idx[key]]={'pos':[[],[]], 'vel':[[],[],[]],'slope':[[],[]],'friction':[]}
    
        obj_motion_dict_rotated=dict()
    
        for key in attr_to_idx:
            obj_motion_dict_rotated[attr_to_idx[key]]={'pos':[[],[]], 'vel':[[],[],[]],'slope':[[],[]],'friction':[]}
    
        for frame_num in range(len(u_vid)):
    
            frame=u_vid[frame_num]
            sub_frame=self.convert_attr_to_idx([frame],attr_to_idx)
            frame_dict=self.convert_frame(frame,attr_to_idx)
            for obj_num in attr_to_idx.values():
    
                if obj_num in sub_frame.values():
    
                    x=frame_dict[obj_num]['x']
                    y=frame_dict[obj_num]['y']
                    color=frame_dict[obj_num]['color']
    
                    obj_motion_dict[obj_num]['pos'][0].append(x)
                    obj_motion_dict[obj_num]['pos'][1].append(y)
                    obj_motion_dict[obj_num]['color']=color
    
                    obj_motion_dict_rotated[obj_num]['pos'][0].append(x)
                    obj_motion_dict_rotated[obj_num]['pos'][1].append(y)
                    obj_motion_dict_rotated[obj_num]['color']=color
                else:
    
                    obj_motion_dict[obj_num]['pos'][0].append(0)
                    obj_motion_dict[obj_num]['pos'][1].append(0)
    
                    obj_motion_dict_rotated[obj_num]['pos'][0].append(0)
                    obj_motion_dict_rotated[obj_num]['pos'][1].append(0)
    
        for obj in obj_motion_dict:
            obj_motion_dict_rotated[obj]['pos']=[obj_motion_dict_rotated[obj]['pos'][1], [-jj for jj in obj_motion_dict_rotated[obj]['pos'][0]]]
    
        for obj in obj_motion_dict:
            
            obj_motion_dict_rotated[obj]['pos'][0]=self.replace_zeros(np.array(obj_motion_dict_rotated[obj]['pos'][0]))
            obj_motion_dict_rotated[obj]['pos'][1]=self.replace_zeros(np.array(obj_motion_dict_rotated[obj]['pos'][1]))
            obj_motion_dict_rotated[obj]['vel'][0]=self.get_velocities(obj_motion_dict_rotated[obj]['pos'][0]) #vel_x
            obj_motion_dict_rotated[obj]['vel'][1] = self.get_velocities(obj_motion_dict_rotated[obj]['pos'][1]) #vel_y
            obj_motion_dict_rotated[obj]['vel'][2]=self.get_2d_velocity(obj_motion_dict_rotated[obj]['vel'][0],obj_motion_dict_rotated[obj]['vel'][1])
            obj_motion_dict_rotated[obj]['slope'][:]=self.get_slopes(obj_motion_dict_rotated[obj]['pos'][0],obj_motion_dict_rotated[obj]['pos'][1])
            obj_motion_dict_rotated[obj]['friction']=self.get_friction(obj_motion_dict_rotated[obj]['vel'][2])
    
        earliest_collisions=list()
    
        for i in range(len(obj_motion_dict)):
            if i in sims:
                earliest_collisions.append(sims[i])
            else:
                earliest_collisions.append(None)
    
        predicted={attr_to_idx[obj]:[] for obj in attr_to_idx}
    
        for obj,earliest in zip(obj_motion_dict,earliest_collisions):
            if earliest!=None:
                if earliest/self.TIME_DIFF <=self.VIDEO_END+ 1:
    
                    end_frame=int(earliest/self.TIME_DIFF)
                else:
                    end_frame=self.VIDEO_END
            else:
                end_frame= self.VIDEO_END
    
            predicted[obj]=self.get_predicted_trajectory(obj_motion_dict_rotated[obj]['vel'][2],
                                                    obj_motion_dict_rotated[obj]['pos'],
                                                    obj_motion_dict_rotated[obj]['slope'], obj, obj_to_be_removed, obj_motion_dict_rotated[obj]['friction'],
                                                    video_end=end_frame,
                                                    additional_frames=4)
    
        predicted_x=np.stack([predicted[obj][0][:] for obj in predicted])
        predicted_y=np.stack([predicted[obj][1][:] for obj in predicted])
    
        keys=list(predicted.keys())
    
        x_diff=[]
        y_diff=[]
        dist=[]
    
        hits=[]
        collision_string=''
        collision_list=list()
        for p1 in keys:
    
            x_diff.append([])
            y_diff.append([])
            dist.append([])
            hits.append([])
            for p2 in keys[p1:]:
                
                x_difference=predicted_x[p1]-predicted_x[p2]
                y_difference=predicted_y[p1]-predicted_y[p2]
                x_diff[p1].append(x_difference)
                y_diff[p1].append(y_difference)
    
                distances=np.sqrt(np.power(x_difference,2) + np.power(y_difference,2))
                distances[np.where(distances==0)]=999 
    
                if post_vid_only:
                    hit_indices=np.where(distances[(self.VIDEO_END+ 1):]<self.frame_params['HIT_THRESHOLD'])[0]+(self.VIDEO_END+ 1)
                else:
                    hit_indices=np.where(distances<self.frame_params['HIT_THRESHOLD'])[0]
    
                for hit in hit_indices[:1]:
                    frame=(0+hit)*self.TIME_DIFF
                    collision_string+='collision({0},{1},{2}).'.format(p1,p2,frame)
                    collision_string+='\n'
                    collision_list.append({'type':'collision','object':[p1,p2],'frame':frame})
                dist[p1].append(distances)
    
            x_diff[p1]=np.array(x_diff[p1])
            y_diff[p1]=np.array(y_diff[p1])
            dist[p1]=np.array(dist[p1])
    
        collision_list=[col for col in collision_list]
        collision_candidates=[[] for i in range(len(keys))]
    
        for idx,cand_list in enumerate(collision_candidates):
            for col in collision_list:
                if col['object'][0]==idx:
                    cand_list.append(col)
    
        collision_filtered_list=[[] for i in range(len(keys))]
    
        for idx,filtered_list in enumerate(collision_filtered_list):
            candidate=None
            for cand in collision_candidates[idx]:
                if candidate==None:
                    candidate=cand
                else:
                    if cand['frame']<candidate['frame']:
                        candidate=cand
    
            collision_filtered_list[idx]=candidate
    
        collision_filtered_list=[i for i in collision_filtered_list if i!=None]
    
        return collision_list, attr_to_idx, obj_motion_dict_rotated, predicted
