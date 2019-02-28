#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 17:34:52 2019

stl-to-amf

Tool to convert, merge and modify stl files through command line. This tool
takes one ore more stls as input, and merge them in one amf. If you add a
configuration file, you can apply a Slicing configuration to the stls. If
specified in the arguments, different configurations can be applied to
different files.

Examples:
    $ python stl_to_amf.py file1.stl file2.stl --output_path 'out.amf'

    $ python stl_to_amf.py -custom_config --config_path config.yaml
        file1.stl profile_1 file2.stl profile_2

@author: carlgval
"""

import argparse
import os
import yaml
import re


class Triangle(object):
    '''Triangle class

    Class to represent the triangles of an amf file. Each triangle is
    represented as three vertices. In the class, only the indexes of the
    vertices are stored, referencing to the vertices list in the parent class.

    Attributes:
        v1 (int): Index of the first vertice of the triangle.
        v2 (int): Index of the second vertice of the triangle.
        v3 (int): Index of the third vertice of the triangle.
    '''

    def __init__(self, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def __repr__(self, spacing=0):
        '''Representation method

        This method represents the object as an xml in a amf format.

        Args:
            spacing (int): spacing level. Used in representations of the
                parent xml.

        Returns:
            (str): String containing the representation in xml.
        '''
        out = ' ' * spacing + '<triangle>\n'

        out += ' ' * (spacing + 2) + '<v1>%i</v1>\n' % self.v1
        out += ' ' * (spacing + 2) + '<v2>%i</v2>\n' % self.v2
        out += ' ' * (spacing + 2) + '<v3>%i</v3>\n' % self.v3

        out += ' ' * spacing + '</triangle>\n'
        return out


class Vertex(object):
    '''Vertex class

    Class to represent the vertices of an amf file. Each vertex is
    represented as three floats x,y,z.

    Attributes:
        coordinates (:obj:`list` of float): List with the x, y, z coordinates.

    Args:
        x (float): X coordinate.
        y (float): Y coordinate.
        z (float): Z coordinate.

    '''
    def __eq__(self, coordinates):
        '''Comparison method used for search'''
        return self.coordinates == coordinates

    def __init__(self, x, y, z):
        self.coordinates = [x, y, z]

    def __repr__(self, spacing=0):
        '''Representation method

        This method represents the object as an xml in a amf format.

        Args:
            spacing (int): spacing level. Used in representations of the
                parent xml.

        Returns:
            (str): String containing the representation in xml.
        '''
        out = ' ' * spacing + '<vertex>\n'
        out += ' ' * (spacing + 2) + '<coordinates>\n'

        x, y, z = self.coordinates
        out += ' ' * (spacing + 4) + '<x>{:.4f}</x>\n'.format(x)
        out += ' ' * (spacing + 4) + '<y>{:.4f}</y>\n'.format(y)
        out += ' ' * (spacing + 4) + '<z>{:.4f}</z>\n'.format(z)

        out += ' ' * (spacing + 2) + '</coordinates>\n'
        out += ' ' * spacing + '</vertex>\n'
        return out


class Volume(object):
    '''Volume class

    Class to represent the volume of an amf file. Each volume is
    represented as a list of triangles. Also, it supports the use of metadata
    specific for each volume.

    Attributes:
        triangles (:obj:`list` of :obj:`Triangle`): List of the triangles that
            compose the volume.
        metadata (:obj:`dict`): Dictionary of metadata, being k the tag and
            v the value.

    Args:
        triangles (:obj:`list` of :obj:`Triangle`): List of the triangles that
            compose the volume.
        metadata (:obj:`dict`): Dictionary of metadata, being k the tag and
            v the value.
    '''
    def __init__(self, triangles, metadata=None):
        self.triangles = triangles
        self.metadata = metadata

    def __repr__(self, spacing=0):
        '''Representation method

        This method represents the object as an xml in a amf format.

        Args:
            spacing (int): spacing level. Used in representations of the
                parent xml.

        Returns:
            (str): String containing the representation in xml.
        '''
        out = ' ' * spacing + '<volume>\n'
        # If there is metadata iter over the fields
        if self.metadata is not None:
            for k, v in self.metadata.items():
                out += ' ' * (spacing + 2) + \
                    '<metadata type="%s">%s</metadata>\n' % (k, v)
        # And then iter over the triangles
        for t in self.triangles:
            out += t.__repr__(spacing + 2)
        out += ' ' * spacing + '</volume>\n'
        return out


class Amf(object):
    '''Amf class

    Class to represent the contents of an amf file. Each amf is
    represented as a list of vertices and a list of volumes. Also, it
    supports the use of metadata specific for each volume.

    Attributes:
        volumes (:obj:`list` of :obj:`Volume`): List of the volumes that
            compose the file.
        vertices (:obj:`list` of :obj:`Vertex`): List of vertices of the
            triangles defined in the volumes.

    Attributes:
        volumes (:obj:`list` of :obj:`Volume`): List of the volumes that
            compose the file.
        vertices (:obj:`list` of :obj:`Vertex`): List of vertices of the
            triangles defined in the volumes.
    '''
    def __init__(self, volumes=[], vertices=[]):
        self.volumes = volumes
        self.vertices = vertices

    def append_stl(self, file_path, metadata=None):
        '''Append stl method

        Given an stl file, this method parses and adds its contents to the
        amf, creating a new volume. If metadata is used as argument, it is
        added to the volume.

        Attributes:
            file_path (:obj:`str`): Path to the stl path.
            metadata (:obj:`dict`): Dictionary of metadata, being k the tag
                and v the value.
        '''
        # Read the stl
        with open(file_path) as f:
            text = f.read()

        # Parse the facets
        facets = re.findall('facet ((?s).+?) endfacet', text)
        triangles = []
        # For each facet
        for facet in facets:
            # Find the vertices
            vertexs = re.findall('vertex[ \t]*(.+)', facet)
            temp_v = []
            # For each verex
            for vertex in vertexs:
                # Get the coordinates
                x, y, z = [float(i) for i in vertex.split()]
                try:
                    # If the point is defined, get the index.
                    idx = self.vertices.index([x, y, z])
                except ValueError:
                    # If it is not defined, create a new one.
                    self.vertices.append(Vertex(x, y, z))
                    idx = len(self.vertices) - 1
                # Store the index of the point
                temp_v.append(idx)
            # Create a new triangle with the indexes and add it to the list
            triangles.append(Triangle(*temp_v))
        # Create a new volume with the triangles and add it to the list
        self.volumes.append(Volume(triangles, metadata=metadata))

    def __repr__(self, spacing=0):
        '''Representation method

        This method represents the object as an xml in a amf format.

        Args:
            spacing (int): spacing level. Used in representations of the
                parent xml.

        Returns:
            (str): String containing the representation in xml.
        '''
        out = '<?xml version="1.0" encoding="UTF-8"?>\n'
        out += '<amf unit="millimeter">\n'
        out += ' ' * (spacing + 2) + ('<metadata type="cad">' +
                                      'carlgval-dev</metadata>\n')
        out += ' ' * (spacing + 2) + '<object id="0">\n'
        out += ' ' * (spacing + 4) + '<mesh>\n'
        out += ' ' * (spacing + 6) + '<vertices>\n'

        # Iter over the vertices
        for v in self.vertices:
            out += v.__repr__(spacing + 8)

        out += ' ' * (spacing + 6) + '</vertices>\n'

        # Iter over the volumes
        for v in self.volumes:
            out += v.__repr__(spacing + 6)

        out += ' ' * (spacing + 4) + '</mesh>\n'
        out += ' ' * (spacing + 2) + '</object>\n'

        out += ' ' * (spacing + 2) + '<constellation id="1">\n'
        out += ' ' * (spacing + 4) + '<instance objectid="0">\n'
        out += ' ' * (spacing + 6) + '<deltax>100</deltax>\n'
        out += ' ' * (spacing + 6) + '<deltay>100</deltay>\n'
        out += ' ' * (spacing + 6) + '<rz>0</rz>\n'
        out += ' ' * (spacing + 6) + '<scale>1</scale>\n'
        out += ' ' * (spacing + 4) + '</instance>\n'
        out += ' ' * (spacing + 2) + '</constellation>\n'
        out += ' ' * (spacing + 0) + '</amf>\n'

        return out


if __name__ == '__main__':
    # Get the path
    curr_path = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(description=__doc__)

    # Define the program arguments
    parser.add_argument('files',
                        metavar='FILE | FILE PROFILE',
                        type=str, nargs='+',
                        help='Path to stl files. If custom config is used, '
                        'a PROFILE must be added for each FILE')

    parser.add_argument('--output_path',
                        type=str, default=None,
                        help='Path to save the ouput')

    parser.add_argument('-custom_config', action='store_true',
                        help=('flag that indicates if a custom config file '
                              'will be used. If so, for each file, a PROFILE '
                              'must be added for each FILE'))

    parser.add_argument('--config_path',
                        type=str,
                        default=os.path.join(curr_path, 'amf_config.yaml'),
                        help='Path to the configurations')

    # Parse the arguments
    args = parser.parse_args()
    print(args.files)

    # Try to parse the config file
    try:
        config = yaml.load(open(args.config_path))
    except IOError:
        print('WARNING: config file could not be opened. It wont be used')
        config = {'Default': None}

    # Determine how many stls are in the arguments by checking the flags
    stls = []
    if args.custom_config:
        idxs = list(range(0, len(args.files), 2))
    else:
        idxs = list(range(len(args.files)))

    # For each file
    for i in idxs:
        # Try to read it
        if not os.path.isfile(args.files[i]):
            raise Exception('Not valid file: %s' % args.files[i])
        else:
            # Get the profile and read it from the configuration
            profile = None
            if args.custom_config:
                profile = args.files[i + 1]
            if profile not in config.keys():
                print('WARNING: Profile %s not found. Using Default'
                      % profile)
                metadata = config.keys()[0]
            else:
                metadata = config[profile]
            # Add the stl and the configuration to the list
            stls.append((args.files[i], metadata))

    # Create an empty amf
    amf = Amf()

    # Add all files
    for stl, metadata in stls:
        amf.append_stl(stl, metadata=metadata)

    # Export the output or print it on the console
    if args.output_path is None:
        print(amf)
    else:
        with open(args.output_path, "w") as text_file:
            text_file.write(amf.__repr__())
