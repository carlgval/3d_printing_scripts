#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 09:53:05 2019

gcode-to-voxel

Tool to extract from g-code file a voxelized version of the piece. The voxels
store attributes such as direction, speed, temperature and material.

Examples:
    $ python stl_to_amf.py file1.stl file2.stl --output_path 'out.amf'

    $ python stl_to_amf.py -custom_config --config_path config.yaml
        file1.stl profile_1 file2.stl profile_2


@author: carlgval
"""

import tables
import numpy as np
import re

N_ATTRIBUTES = 5
RESOLUTION = 0.1




class Parser(object):
    '''Parser Object

    G-Code parser that generates the voxelized representation.

    '''
    def __init__(self, gcode_file, ouput_file):
        self.gcode_file = gcode_file
        self.voxels_repr = Voxels(ouput_file)
        self.width = 0.5

    def parse(self):

        state = {'material': 0.,
                 'direction_x': 0.,
                 'direction_y': 0.}

        with open(self.gcode_file) as f:
            x, y = 0, 0
            i = 0
            for line in f:
                if line.startswith('M109'):
                    state['temperature'] = float(re.findall('S([0-9]+)\s',
                                                            line)[0])
                elif line.startswith('T'):
                    state['material'] = float(line[1])

                elif line.startswith('G1 F'):
                    state['speed'] = float(re.findall('F([0-9]+)\s',
                                                            line)[0])
                elif line.startswith('G1 Z'):
                    z = float(re.findall('Z[ \t]*([0-9\.]+)\s', line)[0])
                    self.voxels_repr.new_layer(z)
                elif re.search('G1[ \t]*X([0-9\.]+)[ \t]*Y([0-9\.]+)[ \t]*E',
                               line):
                   x2, y2 = re.findall('X([0-9\.]+)[ \t]*Y([0-9\.]+)[ \t]*E',
                                       line)[0]

                   self.voxels_repr.layer.fill_traj((x, y),
                                                    (x2, y2),
                                                    state.values(),
                                                    self.width)
                   x, y = x2, y2

                elif re.search('G1[ \t]*X([0-9\.]+)[ \t]*Y([0-9\.]+)[ \t]*',
                               line):
                   x, y = re.findall('X([0-9\.]+)[ \t]*Y([0-9\.]+)[ \t]*',
                                       line)[0]

                i += 1

                print('%i lines processed' % i)

            self.voxels_repr.write_keys(str(state.keys()))


class Voxels(object):

    def __init__(self, path=None, size=[200, 200]):
        self.hdf5_file = tables.open_file(path, 'w')
        self.size = [int(s / RESOLUTION) for s in size]
        self.prev_z = 0
        self._init_array()

    def _init_array(self):
        atom = tables.FloatAtom(shape=N_ATTRIBUTES)
        filters = tables.Filters(complevel=1)
        self.table = self.hdf5_file.create_earray(self.hdf5_file.root,
                                                  atom=atom,
                                                  shape=self.size + [0],
                                                  name='voxel_data',
                                                  title='voxel_data',
                                                  filters=filters)

    def new_layer(self, z):
        if self.prev_z != 0:
            self._dump_layer()
        z = int(round(z / RESOLUTION, 0))
        self.layer_height = z - self.prev_z
        self.layer = Layer(self.size)
        self.prev_z = z

    def _dump_layer(self):
        for i in range(int(self.layer_height / RESOLUTION)):
            self.table.append(self.layer.layer.reshape(self.size +
                                                       [1, N_ATTRIBUTES]))

    def write_keys(self, keys):
        self.table.attrs['keys'] = keys

    def __del__(self):
        self.hdf5_file.close()
        del self.hdf5_file


class Layer(object):
    def __init__(self, size=[2000, 2000]):
        self.layer = np.zeros(size + [N_ATTRIBUTES])

    def create_mask(self, width):
        radius = int(round(width / RESOLUTION / 2, 0))
        y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
        mask = x**2 + y**2 <= (radius)**2

        return mask

    def fill_traj(self, pos_1, pos_2, data, width):
        x_1, y_1 = pos_1
        x_2, y_2 = pos_2
        steps = int(max(abs(x_1 - x_2), abs(y_1 - y_2)) / RESOLUTION)
        traj = zip(np.linspace(x_1, x_2, steps), np.linspace(y_1, y_2, steps))

        mask = self.create_mask(width)
        masked_data = np.tile(data, (np.sum(mask), 1))
        w = len(mask) // 2

        for x, y in traj:
            x = int(round(x, 0))
            y = int(round(y, 0))
            print(x, y, w)

            self.layer[(x - w):(x + w + 1), (y - w):(y + w + 1)][mask] = masked_data

i='/home/carlgval/Documents/Atico/devel/pipeline/tests/test/out.gcode'
o='/home/carlgval/Documents/Atico/devel/pipeline/tests/test/out.hdf5'
p=Parser(i, o)
p.parse()