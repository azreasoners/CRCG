import argparse
import os
from tqdm import tqdm
import json
import numpy as np
import copy
H = 320
W = 480


def to_mask(enc):
    x = 0
    k = 0

    cnt = []

    for c in enc:
        z = ord(c) - 48

        x |= (z & 31) << k
        k += 5

        if z >= 32:
            continue

        if z >= 16:
            x -= 1 << k

        cnt.append(x)

        x = 0
        k = 0

    for i in range(3, len(cnt)):
        cnt[i] += cnt[i - 2]

    for i in range(1, len(cnt)):
        cnt[i] += cnt[i - 1]

    mask = np.zeros(H * W, dtype=np.bool_)

    for s, e in zip(cnt[::2], cnt[1::2]):
        mask[s:e] = True

    return mask.reshape(W, H).transpose()


def get_cube_coor(mask):  # Topmost pixel on mid column
    row = mask.any(axis=0)
    cy = int(np.argwhere(row).flatten().mean())

    col = mask[:, cy]
    cx = np.argwhere(col).flatten().min()

    return cx, cy


def get_sphere_coor(mask):  # Topmost pixel
    col = mask.any(axis=1)
    cx = np.argwhere(col).flatten().min()

    row = mask[cx, :]
    cy = int(np.argwhere(row).flatten().mean())

    return cx, cy


def make_object(tri, mask):
    #breakpoint()
    color, material, shape = tri

    if shape == 'cube':
        try:
            cx, cy = get_cube_coor(mask)

        except Exception:  # It sometimes fails with separated masks
            cx, cy = get_sphere_coor(mask)

    else:
        cx, cy = get_sphere_coor(mask)

    return {
        'color': color,
        'material': material,
        'shape': shape,
        'x': float(cx),
        'y': float(cy)
    }


def convert_objects(objects, objects_set):
    mask_map = {}
    for o in objects:
        tri = (o['color'], o['material'], o['shape'])

        if tri not in objects_set:
            continue
        mask = to_mask(o['mask']['counts'])

        if tri in mask_map:
            mask_map[tri] |= mask

        else:
            mask_map[tri] = mask

    return [make_object(tri, mask) for tri, mask in mask_map.items()]


def convert(sim_file, result_file):
    with open(sim_file) as f:
        data = json.load(f)

    objects = data['ground_truth']['objects']
    objects_set = {(o['color'], o['material'], o['shape']) for o in objects}

    collisions = [
        {
            'frame': o['frame'],
            'objects': [
                {
                    'color': objects[i]['color'],
                    'material': objects[i]['material'],
                    'shape': objects[i]['shape']
                } for i in o['object']
            ]
        } for o in data['ground_truth']['collisions']
    ]

    trajectory = [
        {
            'frame_index': o['frame_index'],
            'objects': convert_objects(o['objects'], objects_set)
        } for o in data['frames']
    ]

    for tri in objects_set:
        color, material, shape = tri
        li, lx, ly = None, 0, 0

        for i, t in enumerate(trajectory):
            found = False

            for o in t['objects']:
                if (o['color'], o['material'], o['shape']) == tri:
                    found, x, y = True, o['x'], o['y']

            if not found:
                continue

            if li is not None and i != li + 1:
                dx = (x - lx) / (i - li)
                dy = (y - ly) / (i - li)

                for j in range(li + 1, i):
                    trajectory[j]['objects'].append({
                        'color': color,
                        'material': material,
                        'shape': shape,
                        'x': lx + dx * (j - li),
                        'y': ly + dy * (j - li)
                    })

            li, lx, ly = i, x, y

    result = {
        'objects': objects,
        'predictions': [
            {
                'what_if': -1,
                'trajectory': trajectory,
                'collisions': collisions
            }
        ]
    }

    traj=result['predictions'][0]['trajectory']
    if len(traj) < 128:
        last_frame=traj[-1]
    for i in range(len(traj),128,1):
        new_frame=copy.copy(last_frame)
        new_frame['frame_index']=i
        result['predictions'][0]['trajectory'].append(new_frame)
        
    with open(result_file, 'w') as f:
        json.dump(result, f)


def main(args):
    os.makedirs(args.result_dir, exist_ok=True)
    for idx in tqdm(range(args.start, args.end)):
        sim_file = os.path.join(args.sim_dir, f'sim_{idx:05}.json')
        result_file = os.path.join(args.result_dir, f'sim_{idx:05}.json')
        convert(sim_file, result_file)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--sim-dir', default='processed_proposals/')
    parser.add_argument('--result-dir', default='converted/')

    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=20000)

    args = parser.parse_args()

    main(args)
