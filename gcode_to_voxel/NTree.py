#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 15:55:26 2019

N-Tree representation for spatial data.

This class contains an implementation of BSP (Binary Space Partitioning) trees
for an arbitrary number of dimensions. It is very useful for images or 3d
data storage and processing. When used with 2d data it will create quadtrees,
and with 3d data, it will create octrees.

The storage is intializated to a single node, and when a set operations is
used it is recursevily subdivided till the set range or the max depth
(whatever is larger).

__________________                   ___________________
|                |                   |    |   |        |
|                |                   |____|___|        |
|     x          |                   |    |x|_|        |
|                |        ->         |____|_|_|________|
|                |                   |        |        |
|                |                   |        |        |
|                |                   |        |        |
|________________|                   |________|________|

Get calls will provide a full map of the tree (including repetitions) unless
the step argument is used.

All deletions of the object should use the del argument, instead of set to 0.
This will merge the adjacent leafs if the information is the same.

It also provides methods of storage in hdf5 (TODO) and parsing to discrete
representations of the data contained.

NOTE: This implementation is intended for 2d and 3d data, Consider it
experimental when working with more than 3d.

@author: carlgval
"""

import numpy as np


class Ntree(object):
    ''' Ntree object

    Binary trees representation for data with N dimensions.

    This class stores the main node of the tree, and provides methods to
    access the data. It also performs the mapping with the operations of get
    and set, from a pre-defined input space to a discrete space with spacial
    resolution equal to range / 2^max_depth.

    Attributes:
        dims (int): Number of dimensions of the BSP.
        ranges (:obj:`np.array` of float): min and max for each dimension.
        n_attrs (int): Number of attributes per leaf (channels in images).
        dflt_attrs (:obj:`list`): Default values of the attributes.
        resolution (:obj:`np.array` of float): minimum element size for each
            dimension.
        max_depth (int): Max recursive depth in nodes.
        root (:obj:`Node`): The root node in the tree.

    '''
    def __init__(self,
                 ranges=None,
                 resolution=None,
                 attrs=0,
                 n_dimensions=None,
                 max_depth=8):
        ''' Tree constructor method

        This method inits the tree and the base node for an arbitrary number
        of dimensions.

        Args:
            ranges ()
        '''
        self.dims = len(ranges) if n_dimensions is not None else n_dimensions

        # Parse data to create the first node and the mapping space
        if ranges is not None:
            ranges = np.array(ranges, dtype=float)
            # If there are ranges and resolution, calculate the max depth
            if resolution is not None:
                resolution = resolution if hasattr(resolution, '__len__') \
                    else [resolution] * len(ranges)
                steps = np.diff(ranges, axis=-1).flatten() / resolution
                max_depth = int(np.ceil(np.max(np.log2(steps))))
            else:
                # If there are ranges and no resolution, calculate it
                resolution = np.diff(ranges, axis=-1).flatten() /\
                    2. ** max_depth
        else:
            # If there arent ranges nor resolution, the resolution is 1
            if resolution is None:
                resolution = 1
            # And the ranges are calculated using the default max depth
            resolution = resolution if hasattr(resolution, '__len__') \
                else [resolution] * self.dims
            ranges = [[0, resolution[i] * 2.**max_depth]
                      for i in range(self.dims)]

        # Store the results
        self.ranges = np.array(ranges, dtype=float)
        self.resolution = np.array(resolution, dtype=float)
        self.max_depth = max_depth
        self.dflt_attrs = attrs if hasattr(attrs, '__len__') else [attrs]
        self.n_attrs = len(attrs)

        # Test the attributes
        self._assert_construction()
        # Create the root node
        self.root = Node(self.ranges, attrs, max_level=max_depth)

    def _assert_construction(self):
        ''' Method to check if the input parameters can create a feasible tree

        Raises:

        '''
        # TODO
        pass

    def __getitem__(self, coords):
        ''' Get Item wrapper
        '''
        coords = self._parse_coords(coords)
        return self.root.__getitem__(coords)

    def __setitem__(self, coords):
        ''' Set Item wrapper
        '''
        coords = self._parse_coords(coords)
        return self.root.__getitem__(coords)

    def __delitem__(self, coords):
        ''' Del Item wrapper
        '''
        coords = self._parse_coords(coords)
        return self.root.__getitem__(coords)

    def _parse_coords(self, coords):
        ''' Convert a set of coords to a set of slices

        This method takes as input a set of float / slices of floats that
        point to a region in the represented space, and convert them to a set
        of dicrete slices indexable in the binary space.

        Args:
            coords(:obj:`list` of float or float or :obj:`np.array` of float):
                The coordinates to convert in the represented space.
        Returns:
            (:obj:`list` of :obj:`slice`): Discretized slices.
        '''
        # TODO : REARRANGE
        if not hasattr(coords, '__len__'):
            coords = [coords]
        assert len(coords) <= self.dims
        ranges = self.ranges.copy()
        for i, el in enumerate(coords):
            if type(el) is slice:
                start = el.start if el.start is not None \
                    else float(self.ranges[i][0])
                end = el.stop if el.stop is not None \
                    else float(self.ranges[i][1])
            else:
                start = float(el)
                end = start + float(np.diff(self.ranges[i])) /\
                    (2 ** (self.max_level - self.level))
            ranges[i] = [start, end]
        ranges = np.array(ranges)
        print(ranges)
        return ranges
        pass


class Node(object):
    ''' Node object

    BSP Node object


    '''
    def __init__(self, ranges, attrs=None, level=0, max_level=None):
        ''' Init method

        Constructor of Nodes
        '''
        self.dims = len(ranges.shape)
        self.centers = ranges.mean(-1)
        self.ranges = ranges
        self.attrs = attrs
        self.level = level
        self.max_level = max_level
        self.nodes = None

    def __getitem__(self, coords):
        ''' Get item operation in BSP structure.

        Args:
            coords(:obj:`list` of :obj:`slice`): Indexes to perform the get
                operation.
        Returns:
            (:obj:`np.array`): Array of size [[(s.stop - s.start) / s.step]
                for s in coords.
        '''
        if self.nodes is not None:
            return self._read_nodes(coords)
        else:
            out_shape = [[(s.stop - s.start) / s.step] for s in coords]
            return np.tile(self.attrs, out_shape)

    def __setitem__(self, coords, value):
        ''' Set item operation in BSP structure.

        Args:
            coords(:obj:`list` of :obj:`slice`): Indexes to perform the get
                operation.
            value (:obj:): Object of size n_attrs that will be assigned to the
                correspondant children.
        Returns:
            (bool): True if the operation is a success.
        '''
        if self.level <= self.max_level and not self._contained_by(coords):
            if self.nodes is None:
                self._split()
            self._set_nodes(coords, value)
            self._merge()
        else:
            self.attrs = value
        return True

    def _merge(self):
        ''' Perform a recursive merge operation

        Try to perform a merge operation recursively. For each node, perform
        the merge if possible, and then compare all nodes attributes and merge
        them if they are equal.

        Returns:
            (bool): True if the merge is succesfull, False otherwise.
        '''
        # No children: already merged
        if self.nodes is None:
            return True
        # Try to merge grandchildren
        if not all(n._merge() for n in self.nodes.flatten()):
            return False
        # Compare all nodes to the first one
        cmp_val = self.nodes.flatten()[0].attrs
        if all(cmp_val == n.attrs for n in self.nodes.flatten()):
            # If all are equal, delete them
            self.attrs = cmp_val
            self.nodes = None
            return True
        return False


    def _split(self):
        ''' Split node in sub-nodes

        This method create 2 ^ N subnodes for the current node and stores
        them as objects.

        '''
        nodes_ranges = self._divide_ranges(self.ranges)
        self.nodes = np.empty([2] * self.dims, dtype=object)
        for idx, n in np.ndenumerate(self.nodes):
            range_idx = np.array(idx).reshape(-1, 1)
            self.nodes[idx] = Node(attrs=self.attrs,
                                   level=self.level + 1,
                                   max_level=self.max_level)

    def _divide_ranges(self, ranges):
        ''' Divide ranges method

        This methods splits the slices objects using the central hyperplanes,
        to pass the splitted slices to the node's children.

        Args:
            coords(:obj:`list` of :obj:`slice`): Indexes to perform the get
                operation.

        Returns:
            (:obj:`np.array`): Numpy array with the slices correspondant to
                each dimension of the children nodes.
        '''
        # TODO : Refactor

        return divided_ranges

    def _get_nodes(self, coords):
        ''' Parse coords method

        Args:
            list / np.array / int / slice

        Returns:
            (:obj:`np.array`): Numpy array of shape [2 x n_dimensions x 2].
                Each dimension has two ranges, one for each subdivision.
                Eachrange is indicated as [start, end].
                For example [[[start_x_1, end_x_1], [start_x_2, end_x_2]],
                [[start_y_1, end_y_1], [start_y_2, end_y_2]]]
        '''

        coords = self.divided_ranges(coords)
        nodes_items = np.empty(coords.shape, dtype=object)

        for idx, s in np.ndenumerate(coords):
            nodes_items[idx] = self.nodes[idx].__getitem__(s)

        return np.block(nodes_items)

    def _set_nodes(self, coords, value):
        ''' Method to read the sub-nodes in a getitem operation

        This method calculates the

        Args:
            coords (:obj:`np.array`): Numpy array of shape [n_dimensions x 2].
                For each dimension, the range is indicated as [start, end].
                For example [[start_x, end_x], [start_y, end_y]]
        Returns:
            (:obj:`np.array`): Numpy array of shape
                [range_x, range_y, ..., n_attrs]. The representation of the
                object mapped in these coordinates of the trees.
        '''
        status = True
        coords = self.divided_ranges(coords)

        for idx, s in np.ndenumerate(coords):
            status &= self.nodes[idx].__setitem__(s, value)
        return status


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    t = Ntree([[0, 100], [0, 100]], 0)
    plt.imshow(t[:])
    self = t
