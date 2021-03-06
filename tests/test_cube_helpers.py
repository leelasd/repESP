import my_unittest
from repESP import cube_helpers
from repESP.cube_helpers import angstrom_per_bohr
from repESP.rep_esp import calc_grid_field

import os

# I'm not sure whether this should be here but it seems fine, it's only
# evaluated once and will be available to all the TestCases in this module
inp_cube_path = "tests/test_mol_den.cub"
cube = cube_helpers.Cube(inp_cube_path)
atom = cube.molecule[0]
grid = cube.field.grid

# Write the field as a new cube
out_cube_path = "tests/temp_test.cub"
while True:
    try:
        cube.field.write_cube(out_cube_path, cube.molecule, 'cube')
        break
    except FileExistsError:
        os.remove(out_cube_path)

# This is getting complicated so these initialization lines should be a
# separate test. That likely requires a custom test suite so that they're only
# executed once and before the others.
dist_field = calc_grid_field(cube.molecule, grid, 'dist')
repESP_field = calc_grid_field(cube.molecule, grid, 'rep_esp', ['cube'])[0]
# Values calculated with an independent ad-hoc script
dist_result = [0.1, 0.3, 0.7, 0.316227766, 0.424264068, 0.761577310,
               0.608276253, 0.670820393, 0.921954445, 0.223606797, 0.360555127,
               0.728010988, 0.374165738, 0.469041575, 0.787400787, 0.640312423,
               0.7, 0.943398113, 0.412310562, 0.5, 0.806225774, 0.509901951,
               0.583095189, 0.860232526, 0.728010988, 0.781024967, 1.004987562]
# Values above in Bohr, convert to Angstrom
dist_result = [angstrom_per_bohr*elem for elem in dist_result]

# Isovalue selected so that only two points fall above it
ed_isoval = 7.01e-07
edt_field = cube.field.distance_transform(ed_isoval)
# This was calculated with the aforementioned script as the smaller elements of
# the distance matrices from those two points.
edt_result = [0.63245553, 0.63245553, 0.74833147, 0.36055512, 0.36055512,
              0.53851648, 0.2, 0.2, 0.44721359, 0.6, 0.6, 0.72111025, 0.3, 0.3,
              0.5, 0.0, 0.0, 0.4, 0.63245553, 0.63245553, 0.74833147,
              0.36055512, 0.36055512, 0.53851648, 0.2, 0.2, 0.44721359]
# Convert to Angstrom
edt_result = [angstrom_per_bohr*elem for elem in edt_result]


class TestCube(my_unittest.TestCase):

    def test_title(self):
        self.assertEqual(cube.title,
                         " Electron density from Total MP2 Density")

    def test_atom_count(self):
        self.assertEqual(cube.atom_count, 1)

    def test_type(self):
        self.assertEqual(cube.cube_type, 'ed')

    def test_writing_cube(self):
        with open(out_cube_path, 'r') as out_cube:
            msg = ' line of cube file different than expected.'
            self.assertEqual(out_cube.readline(),
                             " Cube file generated by repESP.\n",
                             msg='First' + msg)
            self.assertEqual(out_cube.readline(),
                             " Cube file for field of type ed.\n",
                             msg='Second' + msg)
            with open(inp_cube_path, 'r') as inp_cube:
                # Skip the first two lines
                for i in range(2):
                    inp_cube.readline()
                for inp_line, out_line in zip(inp_cube, out_cube):
                    self.assertEqual(inp_line, out_line)
                inp_line = inp_cube.readline()
                out_line = out_cube.readline()
                if inp_line or out_line:
                    raise AssertionError('The written and correct cube files '
                                         'have different lengths. Compare '
                                         'manually')
                # To allow comparison, intentionally no clean-up removal on
                # test failure
                os.remove(out_cube_path)


class TestGrid(my_unittest.TestCase):

    def test_origin_coords(self):
        origin_coords = [0.1, 0.2, 0.3]
        origin_coords = [angstrom_per_bohr*elem for elem in origin_coords]
        self.assertListAlmostEqual(grid.origin_coords, origin_coords)

    def test_dir_intervals(self):
        dir_intervals = [0.2, 0.3, 0.4]
        dir_intervals = [angstrom_per_bohr*elem for elem in dir_intervals]
        self.assertListAlmostEqual(grid.dir_intervals, dir_intervals)

    def test_aligned(self):
        self.assertTrue(grid.aligned_to_coord)

    def test_points_on_axes(self):
        self.assertListAlmostEqual(grid.points_on_axes, [3, 3, 3])


class TestMolecule(my_unittest.TestCase):

    def test_label(self):
        self.assertEqual(atom.label, 1)

    def test_atomic_no(self):
        self.assertEqual(atom.atomic_no, 1)

    def test_coords(self):
        coords = [0.1, 0.2, 0.4]
        coords = [angstrom_per_bohr*elem for elem in coords]
        self.assertListAlmostEqual(atom.coords, coords)

    def test_cube_charges(self):
        self.assertAlmostEqual(atom.charges['cube'], 0.9)

    def test_atom_count(self):
        self.assertEqual(len(cube.molecule), 1)


class TestDistField(my_unittest.TestCase):

    def test_min_atom(self):
        self.assertListEqual(list(dist_field[0].values.flatten()), [1]*27)

    def test_min_dist(self):
        self.assertListAlmostEqual(list(dist_field[1].values.flatten()),
                                   dist_result)

    def test_field_type(self):
        self.assertEqual(dist_field[0].field_type, 'parent_atom')
        self.assertEqual(dist_field[1].field_type, 'dist')

    def test_atom_field_info(self):
        self.assertListEqual(dist_field[0].field_info, ['Voronoi'])


class TestRepESPField(my_unittest.TestCase):

    def test_values(self):
        self.assertListAlmostEqual(list(repESP_field.values.flatten()),
                                   [0.9/(dist/angstrom_per_bohr) for dist in
                                   dist_result])

    def test_field_type(self):
        self.assertEqual(repESP_field.field_type, 'rep_esp')

    def test_atom_field_info(self):
        self.assertEqual(repESP_field.field_info, ['cube'])


class TestField(my_unittest.TestCase):

    def test_edt_type(self):
        self.assertEqual(edt_field.field_type, 'dist')

    def test_edt_info(self):
        self.assertEqual(edt_field.field_info[0], 'ed')
        self.assertAlmostEqual(edt_field.field_info[1], ed_isoval)

    def test_edt_values(self):
        self.assertListAlmostEqual(list(edt_field.values.flatten()),
                                   edt_result)
