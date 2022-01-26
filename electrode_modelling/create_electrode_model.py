import json
import bpy
import os
import math
from os.path import join
from pathlib import Path
import bmesh

json_filename = join(Path(__file__).parent.parent, 'elspec.json')
model_path = bpy.path.abspath("//")

with open(json_filename) as f:
	elspecs = json.load(f)

# options
electrodes = ['example_non_directional_electrode']
# electrodes = elspecs.keys() # all electrodes present in json sidecar
nr_vertices = 72  # base number for mesh quality (360 and size of segments should be even dividable for segmented electrodes!)


def create_tip(z, tip_length, isContact):
	# create sphere for tip
	bpy.ops.mesh.primitive_uv_sphere_add(segments=nr_vertices, radius=radius_lead, enter_editmode=False, align='WORLD',
	                                     location=(0, 0, z + radius_lead), scale=(1, 1, 1), ring_count=nr_vertices / 2)  # create sphere
	tip_sphere = bpy.context.object
	tip_sphere.name = 'tip_sphere'

	# add cylinder that cuts sphere into half-sphere
	cut_cyl_depth = radius_lead + 0.2 * radius_lead
	bpy.ops.mesh.primitive_cylinder_add(vertices=nr_vertices, radius=radius_lead,
	                                    depth=cut_cyl_depth, enter_editmode=False,
	                                    align='WORLD', location=(0, 0, z + (cut_cyl_depth / 2) + radius_lead), scale=(1, 1, 1))

	cut_cyl = bpy.context.object
	cut_cyl.name = 'cut_cylinder'
	cut_cyl.scale = (1.2, 1.2, 1)

	diff_bool = tip_sphere.modifiers.new('remove_half_sphere', 'BOOLEAN')
	# Set the mode of the modifier to DIFFERENCE.
	diff_bool.operation = 'DIFFERENCE'
	# Set the object to be used by the modifier.
	diff_bool.object = cut_cyl

	# apply the modifier
	bpy.context.view_layer.objects.active = bpy.data.objects['tip_sphere']  # make sphere tip active objects
	bpy.ops.object.modifier_apply(modifier="remove_half_sphere")  # cut

	# remove top face of sphere
	bpy.ops.object.select_all(action='DESELECT')
	tip_sphere.select_set(True)
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='DESELECT')
	bm = bmesh.from_edit_mesh(tip_sphere.data)
	bm.faces.ensure_lookup_table()
	#
	#    # iterate through all faces, delete the ones that are facing up- or downwards and have a minimum area (to not delete bottom of tip)
	for f in bm.faces:
		if (f.normal[2] <= -0.99 or f.normal[2] >= 0.99) and f.calc_area() > 0.1:
			f.select = True
			bpy.ops.mesh.delete(type='FACE')

	bpy.ops.object.editmode_toggle()

	bpy.ops.object.select_all(action='DESELECT')

	# remove cut cyl
	bpy.data.objects['cut_cylinder'].select_set(True)
	bpy.ops.object.delete()

	# add cylinder to finish tip
	tip_spacer_depth = tip_length - radius_lead
	bpy.ops.mesh.primitive_cylinder_add(vertices=nr_vertices, radius=radius_lead,
	                                    depth=tip_spacer_depth, enter_editmode=False,
	                                    align='WORLD', location=(0, 0, z + (tip_spacer_depth / 2) + radius_lead), scale=(1, 1, 1))

	# Get the cylinder object and rename it.
	tip_cyl = bpy.context.object
	tip_cyl.name = 'tip_cylinder'

	# remove bottom of cylinder
	bpy.ops.object.select_all(action='DESELECT')
	tip_cyl.select_set(True)
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='DESELECT')
	bm = bmesh.from_edit_mesh(tip_cyl.data)
	bm.faces.ensure_lookup_table()
	#
	#    # iterate through all faces, delete the ones that are facing up- or downwards and have a minimum area (to not delete bottom of tip)
	for f in bm.faces:
		if f.normal[2] <= -0.99 and f.calc_area() > 0.1:
			f.select = True
			bpy.ops.mesh.delete(type='FACE')

	bpy.ops.object.editmode_toggle()

	bpy.ops.object.select_all(action='DESELECT')

	mesh = [m for m in bpy.context.scene.objects if m.type == 'MESH']

	for obj in mesh:
		obj.select_set(state=True)
		bpy.context.view_layer.objects.active = obj

	bpy.ops.object.join()

	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.remove_doubles()
	bpy.ops.object.editmode_toggle()

	if isContact:
		contact_components.append(tip_cyl)
		tip_cyl.name = 'con0'
	else:
		insulation_components.append(tip_cyl)
		tip_cyl.name = 'ins0'

	bpy.data.collections['components'].objects.link(tip_cyl)  # link to components collection
	bpy.context.scene.collection.objects.unlink(tip_cyl)  # unlink from master collection


def create_contact(z=0, contact_length=1.5, contact_nr=0, ins_nr=0, segmented=0, num_segments=3, size_segments=90):
	if not segmented:
		# circular contacts
		bpy.ops.mesh.primitive_cylinder_add(vertices=nr_vertices, radius=radius_lead, depth=contact_length, enter_editmode=False,
		                                    align='WORLD', location=(0, 0, z + contact_length / 2), scale=(1, 1, 1))
		contact = bpy.context.object

		contact.name = 'con' + str(contact_nr)

		contact_components.append(contact)
		bpy.data.collections['components'].objects.link(contact)  # link to components collection
		bpy.context.scene.collection.objects.unlink(contact)  # unlink from master collection
	else:

		# for good mesh creation of segmented contacts and insulations, we always have to create them with 0 angle and then rotate
		rot_angle = 40
		size_insulations = (360 - num_segments * size_segments) / num_segments

		for nrSegm in range(num_segments):
			# add segmented contact
			bpy.ops.curve.simple(align='WORLD', location=(0, 0, z), rotation=(0, 0, 0), Simple_Type='Sector', Simple_radius=radius_lead, use_cyclic_u=False, edit_mode=False, Simple_startangle=0, Simple_endangle=size_segments, outputType='POLY',
			                     Simple_sides=round(nr_vertices * size_segments / 360) - 1)
			contact = bpy.context.object
			contact.name = 'con' + str(contact_nr)
			contact_components.append(contact)
			bpy.data.collections['components'].objects.link(contact)  # link to components collection
			bpy.context.scene.collection.objects.unlink(contact)
			contact_nr = contact_nr + 1

			# rotate
			contact.rotation_euler[2] = math.radians(rot_angle)
			rot_angle = rot_angle + size_segments

			# convert it to mesh
			# bpy.ops.object.editmode_toggle()
			bpy.ops.object.convert(target='MESH')

			# add edge between vertices to complete segment
			bpy.ops.object.editmode_toggle()
			bpy.ops.mesh.select_all(action='DESELECT')
			# iterate through all faces, delete the ones that are facing up- or downwards and have a minimum area (to not delete bottom of tip)
			bm = bmesh.from_edit_mesh(contact.data)
			bm.verts.ensure_lookup_table()
			bm.verts[0].select_set(True)
			bm.verts[len(bm.verts) - 1].select_set(True)
			bpy.ops.mesh.edge_face_add()
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.mesh.edge_face_add()

			# extrude it
			# bpy.ops.object.editmode_toggle()
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip": False, "use_dissolve_ortho_edges": True,
			                                                         "mirror": False}, TRANSFORM_OT_translate={"value": (0, 0, contact_length),
			                                                                                                   "orient_type": 'NORMAL', "orient_matrix": ((0.707107, 0.707107, -0), (-0.707107, 0.707107, 0), (0, 0, 1)),
			                                                                                                   "orient_matrix_type": 'NORMAL', "constraint_axis": (True, True, True), "mirror": False, "use_proportional_edit": False,
			                                                                                                   "proportional_edit_falloff": 'SMOOTH',
			                                                                                                   "proportional_size": 1, "use_proportional_connected": False,
			                                                                                                   "use_proportional_projected": False, "snap": False, "snap_target": 'CLOSEST',
			                                                                                                   "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0), "gpencil_strokes": False,
			                                                                                                   "cursor_transform": False, "texture_space": False, "remove_on_cancel": False, "release_confirm": False,
			                                                                                                   "use_accurate": False, "use_automerge_and_split": False})
			bpy.ops.object.editmode_toggle()

			# add segmented insulation
			bpy.ops.curve.simple(align='WORLD', location=(0, 0, z), rotation=(0, 0, 0), Simple_Type='Sector', Simple_radius=radius_lead, use_cyclic_u=True, edit_mode=False, Simple_startangle=0,
			                     Simple_endangle=size_insulations, outputType='POLY',
			                     Simple_sides=round(nr_vertices * size_insulations / 360) - 1)
			insulation = bpy.context.object
			insulation.name = 'ins' + str(ins_nr)
			insulation_components.append(insulation)
			bpy.data.collections['components'].objects.link(insulation)  # link to components collection

			insulation.rotation_euler[2] = math.radians(rot_angle)
			rot_angle = rot_angle + size_insulations

			bpy.context.scene.collection.objects.unlink(insulation)
			ins_nr = ins_nr + 1

			# convert it to mesh
			bpy.ops.object.convert(target='MESH')

			# add edge between vertices to complete segment
			bpy.ops.object.editmode_toggle()
			bpy.ops.mesh.select_all(action='DESELECT')
			# iterate through all faces, delete the ones that are facing up- or downwards and have a minimum area (to not delete bottom of tip)
			bm = bmesh.from_edit_mesh(insulation.data)
			bm.verts.ensure_lookup_table()
			bm.verts[0].select_set(True)
			bm.verts[len(bm.verts) - 1].select_set(True)
			bpy.ops.mesh.edge_face_add()
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.mesh.edge_face_add()

			# extrude it
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip": False, "use_dissolve_ortho_edges": False,
			                                                         "mirror": False}, TRANSFORM_OT_translate={"value": (0, 0, contact_length),
			                                                                                                   "orient_type": 'NORMAL', "orient_matrix": ((0.707107, 0.707107, -0), (-0.707107, 0.707107, 0), (0, 0, 1)),
			                                                                                                   "orient_matrix_type": 'NORMAL', "constraint_axis": (True, True, True), "mirror": False, "use_proportional_edit": False,
			                                                                                                   "proportional_edit_falloff": 'SMOOTH',
			                                                                                                   "proportional_size": 1, "use_proportional_connected": False,
			                                                                                                   "use_proportional_projected": False, "snap": False, "snap_target": 'CLOSEST',
			                                                                                                   "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0), "gpencil_strokes": False,
			                                                                                                   "cursor_transform": False, "texture_space": False, "remove_on_cancel": False, "release_confirm": False,
			                                                                                                   "use_accurate": False, "use_automerge_and_split": False})
			bpy.ops.object.editmode_toggle()


def create_insulation(z, insulation_nr, depth):
	bpy.ops.mesh.primitive_cylinder_add(vertices=nr_vertices, radius=radius_lead, depth=depth, enter_editmode=False, align='WORLD', location=(0, 0, z + depth / 2), scale=(1, 1, 1))
	insulation = bpy.context.object

	insulation.name = 'ins' + str(insulation_nr)

	insulation_components.append(insulation)
	bpy.data.collections['components'].objects.link(insulation)  # link to components collection
	bpy.context.scene.collection.objects.unlink(insulation)


def create_marker(z=0, contact_length=0, contact_nr=0, insulation_nr=0, insulation_size=0, insulation_startangle=0):
	offset = 0.2
	# first create contact
	bpy.ops.mesh.primitive_cylinder_add(vertices=nr_vertices, radius=radius_lead, depth=contact_length, enter_editmode=False,
	                                    align='WORLD', location=(0, 0, z + contact_length / 2), scale=(1, 1, 1))
	contact = bpy.context.object

	contact.name = 'con' + str(contact_nr)

	contact_components.append(contact)
	bpy.data.collections['components'].objects.link(contact)  # link to components collection
	bpy.context.scene.collection.objects.unlink(contact)  # unlink from master collection

	# now create segmented insulation

	bpy.ops.curve.simple(align='WORLD', location=(0, 0, z + offset), rotation=(0, 0, 0), Simple_Type='Sector', Simple_radius=radius_lead, use_cyclic_u=True, edit_mode=False, Simple_startangle=0,
	                     Simple_endangle=insulation_size + 1e-5, outputType='POLY',
	                     Simple_sides=round(nr_vertices * insulation_size / 360) - 1)
	insulation = bpy.context.object

	insulation.name = 'ins' + str(insulation_nr)
	insulation_components.append(insulation)
	bpy.data.collections['components'].objects.link(insulation)  # link to components collection
	bpy.context.scene.collection.objects.unlink(insulation)

	insulation.rotation_euler[2] = math.radians(insulation_startangle)

	# convert it to mesh
	bpy.ops.object.convert(target='MESH')

	# add edge between vertices to complete segment
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='DESELECT')
	bm = bmesh.from_edit_mesh(insulation.data)
	bm.verts.ensure_lookup_table()
	bm.verts[0].select_set(True)
	bm.verts[len(bm.verts) - 1].select_set(True)
	bpy.ops.mesh.edge_face_add()
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.edge_face_add()

	# extrude it
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip": False, "use_dissolve_ortho_edges": False,
	                                                         "mirror": False}, TRANSFORM_OT_translate={"value": (0, 0, contact_length - 2 * offset),
	                                                                                                   "orient_type": 'NORMAL', "orient_matrix": ((0.707107, 0.707107, -0), (-0.707107, 0.707107, 0), (0, 0, 1)),
	                                                                                                   "orient_matrix_type": 'NORMAL', "constraint_axis": (True, True, True), "mirror": False, "use_proportional_edit": False,
	                                                                                                   "proportional_edit_falloff": 'SMOOTH',
	                                                                                                   "proportional_size": 1, "use_proportional_connected": False,
	                                                                                                   "use_proportional_projected": False, "snap": False, "snap_target": 'CLOSEST',
	                                                                                                   "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0), "gpencil_strokes": False,
	                                                                                                   "cursor_transform": False, "texture_space": False, "remove_on_cancel": False, "release_confirm": False,
	                                                                                                   "use_accurate": False, "use_automerge_and_split": False})
	bpy.ops.object.editmode_toggle()

	# now cut insulation from marker
	insulation.scale = (1.05, 1.05, 1.0)

	diff_bool = contact.modifiers.new('remove_insulation_marker', 'BOOLEAN')
	# Set the mode of the modifier to DIFFERENCE.
	diff_bool.operation = 'DIFFERENCE'
	diff_bool.solver = 'EXACT'
	# Set the object to be used by the modifier.
	diff_bool.object = insulation

	# apply the modifier
	bpy.context.view_layer.objects.active = bpy.data.objects['con' + str(contact_nr)]  # make sphere tip active objects
	bpy.ops.object.modifier_apply(modifier="remove_insulation_marker")  # cut

	bpy.ops.object.select_all(action='DESELECT')

	# reset scale on the marker insulation
	insulation.scale = (1., 1., 1.)


def remove_inner_apply_materials(insulation_nr, tip_is_contact):
	# before removing the inner part, copy and past all of the components once for final electrode (except inner)

	# make new collection for final
	collection_final = bpy.data.collections.new("final")
	bpy.context.scene.collection.children.link(collection_final)

	# get materials
	contact_material = bpy.data.materials.get("contact")
	insulation_material = bpy.data.materials.get("insulation")

	# assign materials
	for obj in contact_components:
		bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
		bpy.context.active_object.data.materials.append(contact_material)

	for obj in insulation_components:
		bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
		bpy.context.active_object.data.materials.append(insulation_material)

	#    # copy/paste them
	for obj in bpy.data.collections['components'].all_objects:

		if obj.name != "ins_inner":
			new_obj = obj.copy()
			new_obj.data = obj.data.copy()
			bpy.data.collections['final'].objects.link(new_obj)

			# exclude last insulation from face cleaning
			bpy.ops.object.select_all(action='DESELECT')
			new_obj.select_set(True)
			bpy.ops.object.editmode_toggle()
			bpy.ops.mesh.select_all(action='DESELECT')
			bm = bmesh.from_edit_mesh(new_obj.data)
			bm.faces.ensure_lookup_table()

			# iterate through all faces, delete the ones that are facing up- or downwards and have a minimum area (to not delete bottom of tip)
			for f in bm.faces:
				if obj.name == 'ins' + str(insulation_nr):  # for last insulation, only remove bottom one
					if f.normal[2] <= -0.99 and f.calc_area() > 0.01:
						f.select = True
						bpy.ops.mesh.delete(type='FACE')
				else:
					if (f.normal[2] <= -0.99 or f.normal[2] >= 0.99) and f.calc_area() > 0.01:  # throw out bottom and top
						f.select = True
						bpy.ops.mesh.delete(type='FACE')
					elif f.calc_area() > 0.5:
						f.select = True
						bpy.ops.mesh.delete(type='FACE')  # throw out the one in the middle of the markers

			bpy.ops.object.editmode_toggle()
			new_obj.select_set(False)

	# cut out inner
	bpy.ops.mesh.primitive_cylinder_add(vertices=nr_vertices, radius=radius_inner, depth=total_length - radius_lead / 3,
	                                    enter_editmode=False, align='WORLD', location=(0, 0,
	                                                                                   total_length / 2 + radius_lead / 6), scale=(1, 1, 1))

	# Get the cylinder object and rename it.
	cyl_inner = bpy.context.object
	cyl_inner.name = 'ins_inner'
	cyl_inner.scale = (1., 1., 1.001)  # increase scale by just a little bit to make sure inner part is cut out properly

	#    # add to all objects the difference modifier
	for obj in contact_components:
		obj.select_set(True)
		diff_bool = obj.modifiers.new('remove_inner_part', 'BOOLEAN')
		# Set the mode of the modifier to DIFFERENCE.
		diff_bool.operation = 'DIFFERENCE'
		diff_bool.solver = 'EXACT'
		diff_bool.use_self = True
		# Set the object to be used by the modifier.
		diff_bool.object = cyl_inner
		bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
		bpy.ops.object.modifier_apply(modifier="remove_inner_part")

	for obj in insulation_components:
		diff_bool = obj.modifiers.new('remove_inner_part', 'BOOLEAN')
		# Set the mode of the modifier to DIFFERENCE.
		diff_bool.operation = 'DIFFERENCE'
		diff_bool.solver = 'EXACT'
		# Set the object to be used by the modifier.
		diff_bool.object = cyl_inner
		bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
		bpy.ops.object.modifier_apply(modifier="remove_inner_part")

	# apply insulation material also to inner part
	bpy.context.view_layer.objects.active = bpy.data.objects['ins_inner']
	bpy.context.active_object.data.materials.append(insulation_material)

	insulation_components.append(cyl_inner)
	bpy.data.collections['components'].objects.link(cyl_inner)  # link to components collection
	bpy.context.scene.collection.objects.unlink(cyl_inner)

	cyl_inner.scale = (1., 1., 1.)


def create_final(diameter=1):
	# deselect all
	bpy.ops.object.select_all(action='DESELECT')

	for obj in bpy.data.collections['final'].all_objects:
		obj.select_set(True)
		bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]

	bpy.ops.object.join()
	obj.name = 'final'

	# do some additional clean-up afer joining
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.remove_doubles(threshold=diameter / 100)
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.mesh.select_interior_faces()
	bpy.ops.mesh.delete(type='FACE')
	bpy.ops.object.editmode_toggle()

## construct electrode
for e, electrode in enumerate(electrodes):

	# remove all older objects from components
	collection = bpy.data.collections.get('components')

	if collection:
		for obj in collection.objects:
			bpy.data.objects.remove(obj, do_unlink=True)
		bpy.data.collections.remove(collection)

	# remove all older objects from final
	collection = bpy.data.collections.get('final')

	if collection:
		for obj in collection.objects:
			bpy.data.objects.remove(obj, do_unlink=True)
		bpy.data.collections.remove(collection)

	# spec of current electrode
	elspec_electrode = elspecs[electrode]

	# get relevant info
	radius_lead = elspec_electrode['lead_diameter'] / 2  # radius of the lead
	radius_inner = radius_lead / 2  # inner radius
	nr_elements = elspec_electrode['numel']  # how many elements (one element is either a contact or a group of segmented contacts, the tip is always an element)
	contact_spacing = elspec_electrode['contact_spacing']  # spacing between contacts (assumed to be not contact specific for now)
	total_length = elspec_electrode['lead_length']

	# create lists for components and collection
	insulation_components = []
	contact_components = []
	collection_components = bpy.data.collections.new("components")
	bpy.context.scene.collection.children.link(collection_components)

	z_height = 0  # this value will be increased with each element
	contact_nr = 0
	insulation_nr = 0

	for el_nr in range(0, nr_elements):

		if el_nr == 0:
			# tip
			create_tip(z_height, elspec_electrode["contact_specification"][str(el_nr)]["length"], elspec_electrode["tipiscontact"])

			if elspec_electrode["tipiscontact"]:
				z_height = z_height + elspec_electrode["contact_specification"][str(el_nr)]["length"]

				if nr_elements == 1:
					final_insulation_depth = total_length - z_height
					create_insulation(z_height, insulation_nr, final_insulation_depth)
				else:
					create_insulation(z_height, 0, contact_spacing[0])
					z_height = z_height + contact_spacing[0]
					contact_nr = contact_nr + 1
			else:
				z_height = z_height + elspec_electrode["contact_specification"][str(el_nr)]["length"]

			# if there is more than 1 elements, advance
			if nr_elements > 1:
				insulation_nr = insulation_nr + 1

		else:
			# following contacts
			if not elspec_electrode["contact_specification"][str(el_nr)]["segmented"]:
				create_contact(z=z_height, contact_length=elspec_electrode["contact_specification"][str(el_nr)]["length"], contact_nr=contact_nr)
				contact_nr = contact_nr + 1
			else:
				create_contact(z=z_height, contact_length=elspec_electrode["contact_specification"][str(el_nr)]["length"], contact_nr=contact_nr,
				               segmented=1, ins_nr=insulation_nr,
				               num_segments=elspec_electrode["contact_specification"][str(el_nr)]["num_segments"],
				               size_segments=elspec_electrode["contact_specification"][str(el_nr)]["size_segments"])

				contact_nr = contact_nr + 3
				insulation_nr = insulation_nr + 3

			z_height = z_height + elspec_electrode["contact_specification"][str(el_nr)]["length"]

			if el_nr != len(range(0, nr_elements)) - 1:
				# if not the last insulation element

				if len(contact_spacing) == 1:
					create_insulation(z_height, insulation_nr, contact_spacing[0])
					z_height = z_height + contact_spacing[0]
				elif len(contact_spacing) == 2 and el_nr == 1:
					create_insulation(z_height, insulation_nr, contact_spacing[0])
					z_height = z_height + contact_spacing[0]
				else:
					create_insulation(z_height, insulation_nr, contact_spacing[1])
					z_height = z_height + contact_spacing[1]
				insulation_nr = insulation_nr + 1
			else:
				# if it is the last insulation element and no marker is present, create a longer one to finish electrode
				if "marker_pos" not in elspec_electrode:
					final_insulation_depth = total_length - z_height
					create_insulation(z_height, insulation_nr, final_insulation_depth)
				else:
					# create insulation between last contact and marker
					print(insulation_nr)
					create_insulation(z_height, insulation_nr, elspec_electrode["marker_pos"] - z_height)
					z_height = z_height + elspec_electrode["marker_pos"] - z_height
					# now create final insulation until the end of the electrode
					final_insulation_depth = total_length - (z_height + elspec_electrode["marker_length"])
					create_insulation(z_height + elspec_electrode["marker_length"], insulation_nr + 2, final_insulation_depth)

	if "marker_pos" in elspec_electrode:
		# create marker if electrode has marker
		if "B33" in electrode:  # this is for sensight
			print('Sensight electrodes not implemented yet')
		else:  # conventional markers can be created on the fly
			create_marker(z=elspec_electrode["marker_pos"], contact_length=elspec_electrode["marker_length"], contact_nr=contact_nr, insulation_nr=insulation_nr + 1, insulation_size=elspec_electrode["marker_size"],
			              insulation_startangle=elspec_electrode["marker_startangle"])

		insulation_nr = insulation_nr + 2

	remove_inner_apply_materials(insulation_nr, elspec_electrode["tipiscontact"])

	create_final(diameter=elspec_electrode['lead_diameter'])
