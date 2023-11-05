import json
import numpy as np


class Simulation():
    def __init__(
            self, ann_path, n_vis_frames=128,
            frame_diff=5, moving_v_th=0.29
    ):
        self.ann_path = ann_path  # for debugging
        self.n_vis_frames = n_vis_frames

        self.frame_diff = frame_diff
        self.moving_v_th = moving_v_th

        with open(ann_path) as f:
            ann = json.load(f)
            self.objs = ann['objects']
            self.preds = ann['predictions']

        self.num_objs = len(self.objs)

        self._init_sim()


    def get_visible_objs(self):
        return [o['id'] for o in self.objs]

    def get_static_attrs(self, obj_idx):
        for o in self.objs:
            if o['id'] == obj_idx:
                attrs = {
                    'color': o['color'],
                    'material': o['material'],
                    'shape': o['shape'],
                }
                return attrs
        raise ValueError('Invalid object index')


    def is_visible(self, obj_idx, frame_idx=None, ann_idx=None, what_if=-1):
        if frame_idx is not None or ann_idx is not None:
            frame_ann = self._get_frame_ann(frame_idx, ann_idx, what_if)
            for o in frame_ann['objects']:
                oid = self._get_obj_idx(o)
                if oid == obj_idx:
                    return True
            return False
        else:
            for i, t in enumerate(self.preds[0]['trajectory']):
                if t['frame_index'] < self.n_vis_frames and \
                   self.is_visible(obj_idx, ann_idx=i, what_if=what_if):
                    return True
            return False


    def is_moving(self, obj_idx, frame_idx=None, ann_idx=None):
        if frame_idx is not None or ann_idx is not None:
            frame_ann = self._get_frame_ann(frame_idx, ann_idx)
            for o in frame_ann['objects']:
                oid = self._get_obj_idx(o)
                if oid == obj_idx:
                    speed = np.linalg.norm([o['vx'], o['vy']])
                    return speed > self.moving_v_th
            print(frame_idx, ann_idx)
            raise ValueError('Invalid object index')
        else:
            for i, t in enumerate(self.preds[0]['trajectory']):
                if self.is_visible(obj_idx, ann_idx=i) and \
                   self.is_moving(obj_idx, ann_idx=i):
                    return True
            return False


    def _init_sim(self):
        self.in_out = []
        self.collisions = []

        p = self.preds[0]

        for i, t in enumerate(p['trajectory']):
            for o in t['objects']:
                o['id'] = self._get_obj_idx(o)

                if i != 0 and not self.is_visible(o['id'], ann_idx=i-1):
                    self.in_out.append({
                        'frame': t['frame_index'],
                        'type': 'in',
                        'object': [o['id']]
                    })

                if i != len(p['trajectory']) - 1 and not self.is_visible(o['id'], ann_idx=i+1):
                    self.in_out.append({
                        'frame': p['trajectory'][i + 1]['frame_index'],
                        'type': 'out',
                        'object': [o['id']]
                    })

                frame_curr = t['frame_index']

                frame_prev = frame_curr - self.frame_diff
                frame_next = frame_curr + self.frame_diff

                while True:  # it must stop at frame_prev == frame_curr
                    try:
                        x_prev, y_prev = self._get_obj_location(o['id'], frame_idx=frame_prev)

                    except Exception:
                        frame_prev += 1

                    else:
                        break

                while True:
                    try:
                        x_next, y_next = self._get_obj_location(o['id'], frame_idx=frame_next)

                    except Exception:
                        frame_next -= 1

                    else:
                        break

                if frame_prev == frame_next:
                    o['vx'], o['vy'] = 0, 0

                else:
                    o['vx'] = (x_next - x_prev) / (frame_next - frame_prev)
                    o['vy'] = (y_next - y_prev) / (frame_next - frame_prev)

        for c in p['collisions']:
            obj1_idx = self._get_obj_idx(c['objects'][0])
            obj2_idx = self._get_obj_idx(c['objects'][1])

            self.collisions.append({
                'type': 'collision',
                'object': [obj1_idx, obj2_idx],
                'frame': c['frame'],
            })

        self.cf_events = {}

        for j in range(1, len(self.preds)):
            assert self.preds[j]['what_if'] != -1

            self.cf_events[self.preds[j]['what_if']] = []

            for c in self.preds[j]['collisions']:
                obj1_idx = self._get_obj_idx(c['objects'][0])
                obj2_idx = self._get_obj_idx(c['objects'][1])

                self.cf_events[self.preds[j]['what_if']].append({
                    'type': 'collision',
                    'object': [obj1_idx, obj2_idx],
                    'frame': c['frame'],
                })


    def _get_obj_idx(self, obj):
        for o in self.objs:
            if o['color'] == obj['color'] and \
               o['material'] == obj['material'] and \
               o['shape'] == obj['shape']:
                return o['id']
        return -1


    def _get_frame_ann(self, frame_idx=None, ann_idx=None, what_if=-1):
        assert ann_idx is not None or frame_idx is not None
        target = None
        if frame_idx is not None:
            for t in self.preds[what_if+1]['trajectory']:
                if t['frame_index'] == frame_idx:
                    target = t
                    break
        else:
            target = self.preds[what_if+1]['trajectory'][ann_idx]
        if target is None:
            raise ValueError('Invalid input frame')
        return target


    def _get_obj_location(self, obj_idx, frame_idx=None, ann_idx=None, what_if=-1):
        assert self.is_visible(obj_idx, frame_idx, ann_idx, what_if=what_if)
        frame_ann = self._get_frame_ann(frame_idx, ann_idx, what_if)
        for o in frame_ann['objects']:
            if self._get_obj_idx(o) == obj_idx:
                return o['x'], o['y']
