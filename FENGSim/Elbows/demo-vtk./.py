#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import argparse
import math
import re
import vtk

renumbered_nodes = {}  # old_number : new_number


def clean_screen():
    """Clean screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def write_converted_file(file_name, ugrid):
    """Writes .vtk files in ASCII format compatible with VTK 2.0."""
    if file_name.endswith('.vtk'):
        with open(file_name, 'w') as file:
            # Write the VTK header for version 2.0
            file.write('# vtk DataFile Version 2.0\n')
            file.write('vtk output\n')
            file.write('ASCII\n')
            file.write('DATASET UNSTRUCTURED_GRID\n')

            # Write the points
            file.write(f'POINTS {ugrid.GetNumberOfPoints()} float\n')
            for i in range(ugrid.GetNumberOfPoints()):
                point = ugrid.GetPoint(i)
                file.write(f"{point[0]} {point[1]} {point[2]}\n")

            # Write cells (connectivity)
            file.write(f'CELLS {ugrid.GetNumberOfCells()} {ugrid.GetNumberOfCells() * 5}\n')
            for i in range(ugrid.GetNumberOfCells()):
                cell = ugrid.GetCell(i)
                cell_points = [cell.GetPoints().GetId(j) for j in range(cell.GetNumberOfPoints())]
                file.write(f"{len(cell_points)} {' '.join(map(str, cell_points))}\n")

            # Write cell types (for example, HEXAHEDRON = 12)
            file.write(f'CELL_TYPES {ugrid.GetNumberOfCells()}\n')
            for i in range(ugrid.GetNumberOfCells()):
                file.write("12\n")  # Example cell type (e.g., hexahedron)

            file.close()


class NodalPointCoordinateBlock:
    """Nodal Point Coordinate Block: cgx_2.20.pdf Manual, § 11.3."""

    def __init__(self, in_file):
        """Read nodal coordinates."""
        global renumbered_nodes
        renumbered_nodes.clear()
        self.points = vtk.vtkPoints()

        new_node_number = 0
        while True:
            line = in_file.readline().strip()

            # End of block
            if not line or line == '-3':
                break

            regex = '^-1(.{10})' + '(.{12})'*3
            match = match_line(regex, line)
            node_number = int(match.group(1))
            node_coords = [float(match.group(2)),
                           float(match.group(3)),
                           float(match.group(4)), ]

            renumbered_nodes[node_number] = new_node_number
            self.points.InsertPoint(new_node_number, node_coords)
            new_node_number += 1

        self.numnod = self.points.GetNumberOfPoints()  # number of nodes in this block
        logging.info('{} nodes'.format(self.numnod))  # total number of nodes

    def get_node_numbers(self):
        global renumbered_nodes
        return sorted(renumbered_nodes.keys())


def match_line(regex, line):
    """Search regex in line and report problems."""
    match = re.search(regex, line)
    if match:
        return match
    else:
        logging.error('Can\'t parse line:\n{}\nwith regex:\n{}'\
            .format(line, regex))
        raise Exception


class FRD:
    """Main class to read and parse FRD files."""

    def __init__(self, in_file):
        """Read contents of the .frd file."""
        self.in_file = in_file  # path to the .frd-file to be read
        self.node_block = None  # node block
        self.elem_block = None  # elements block
        self.steps_increments = []  # [(step, inc), ]
        self.ugrid = vtk.vtkUnstructuredGrid()  # create empty grid in VTK

    def parse_mesh(self):
        """Fill in self.ugrid."""
        while True:
            line = self.in_file.readline()
            if not line:
                break
            key = line[:5].strip()

            # Nodes
            if key == '2':
                self.node_block = NodalPointCoordinateBlock(self.in_file)

            # Elements
            elif key == '3':
                self.elem_block = ElementDefinitionBlock(self.in_file)

            # Results
            if key == '100':
                self.in_file.seek(self.in_file.tell() - len(line))  # go up one line
                break

            # End
            elif key == '9999':
                break

        if self.node_block.numnod:
            self.ugrid.SetPoints(self.node_block.points)  # insert all points to the grid
        if self.elem_block.numelem:
            self.ugrid.Allocate(self.elem_block.numelem)
            self.ugrid.SetCells(self.elem_block.types, self.elem_block.cells)

    def has_mesh(self):
        blocks = [self.node_block, self.elem_block]
        if all([b is not None for b in blocks]):
            return True
        logging.warning('File is empty!')
        return False


class Converter:
    """Converts CalculiX .frd file to .vtk (ASCII) format."""

    def __init__(self, frd_file_name):
        self.frd_file_name = frd_file_name

    def run(self):
        logging.info('Reading ' + os.path.basename(self.frd_file_name))
        in_file = open(self.frd_file_name, 'r')
        self.frd = FRD(in_file)

        # Check if file contains mesh data
        self.frd.parse_mesh()
        if not self.frd.has_mesh():
            return

        # Write the VTK file (in ASCII format, compatible with VTK 2.0)
        file_name = self.frd_file_name[:-4] + '.vtk'
        logging.info('Writing ' + os.path.basename(file_name))
        write_converted_file(file_name, self.frd.ugrid)

        in_file.close()


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('filename', type=str, help='FRD file name with extension')
    args = ap.parse_args()

    # Create converter and run it
    converter = Converter(args.filename)
    converter.run()


if __name__ == '__main__':
    clean_screen()
    main()
