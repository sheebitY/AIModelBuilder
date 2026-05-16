"""建模操作模块 - 执行各种Fusion 360建模操作"""

import adsk.core
import adsk.fusion

from modules.state_manager import state


def mm_to_cm(mm):
    """mm转cm（Fusion内部单位）"""
    return mm / 10.0


def execute_operations(operations, ui):
    """执行一个或多个操作"""
    design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    rootComp = design.rootComponent

    results = []

    # 确保操作是列表
    if isinstance(operations, dict):
        operations = [operations]

    for op in operations:
        try:
            action = op.get("action")

            if action == "create_component":
                result = op_create_component(design, op)
            elif action == "switch_component":
                result = op_switch_component(op)
            elif action == "create":
                result = op_create_entity(rootComp, op)
            elif action == "feature":
                result = op_apply_feature(rootComp, op)
            elif action == "pattern":
                result = op_apply_pattern(rootComp, op)
            elif action == "mirror":
                result = op_apply_mirror(rootComp, op)
            elif action == "transform":
                result = op_apply_transform(rootComp, op)
            elif action == "boolean":
                result = op_apply_boolean(rootComp, op)
            else:
                result = f"未知操作: {action}"

            results.append(result)

        except Exception as e:
            error_msg = f"操作失败 [{op.get('action', '?')}]: {str(e)}"
            results.append(error_msg)
            if ui:
                ui.messageBox(error_msg)

    return results


# ==================== 组件操作 ====================


def op_create_component(design, op):
    """创建新组件"""
    name = op.get("name", "未命名组件")
    comp_id = op.get("component_id") or state.generate_component_id()

    rootComp = design.rootComponent
    occurrences = rootComp.occurrences
    occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())

    component = occurrence.component
    component.name = name

    state.register_component(component, name)
    state.current_component = state.components[comp_id]

    return f"创建组件: {comp_id} ({name})"


def op_switch_component(op):
    """切换当前组件"""
    comp_id = op.get("component_id")

    if comp_id in state.components:
        state.current_component = state.components[comp_id]
        return f"切换到组件: {comp_id}"
    else:
        raise Exception(f"组件不存在: {comp_id}")


# ==================== 实体创建 ====================


def op_create_entity(rootComp, op):
    """创建基础实体"""
    shape = op.get("shape")
    params = op.get("params", {})
    position = op.get("position", {"x": 0, "y": 0, "z": 0})
    entity_id = op.get("entity_id") or state.generate_entity_id(shape)

    # 确定在哪个组件中创建
    if state.current_component:
        target_comp = state.current_component["component"]
    else:
        target_comp = rootComp

    x = mm_to_cm(position.get("x", 0))
    y = mm_to_cm(position.get("y", 0))
    z = mm_to_cm(position.get("z", 0))

    body = None

    if shape == "box":
        body = _create_box(
            target_comp,
            mm_to_cm(params["length"]),
            mm_to_cm(params["width"]),
            mm_to_cm(params["height"]),
            x, y, z,
        )
    elif shape == "cylinder":
        body = _create_cylinder(
            target_comp,
            mm_to_cm(params["diameter"]),
            mm_to_cm(params["height"]),
            x, y, z,
        )
    elif shape == "sphere":
        body = _create_sphere(target_comp, mm_to_cm(params["diameter"]), x, y, z)
    elif shape == "cone":
        body = _create_cone(
            target_comp,
            mm_to_cm(params["bottom_diameter"]),
            mm_to_cm(params.get("top_diameter", 0)),
            mm_to_cm(params["height"]),
            x, y, z,
        )
    elif shape == "torus":
        body = _create_torus(
            target_comp,
            mm_to_cm(params["major_diameter"]),
            mm_to_cm(params["minor_diameter"]),
            x, y, z,
        )
    else:
        raise Exception(f"不支持的形状: {shape}")

    if body:
        state.register_entity(body, entity_id)
        state.add_to_history(f"创建{shape} [{entity_id}]", "成功")
        return f"创建实体: {entity_id}"

    raise Exception("创建实体失败")


def _create_box(comp, length, width, height, x, y, z):
    """创建长方体"""
    sketches = comp.sketches
    xyPlane = comp.xYConstructionPlane
    sketch = sketches.add(xyPlane)

    lines = sketch.sketchCurves.sketchLines
    startPt = adsk.core.Point3D.create(x, y, 0)
    endPt = adsk.core.Point3D.create(x + length, y + width, 0)
    lines.addTwoPointRectangle(startPt, endPt)

    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    distance = adsk.core.ValueInput.createByReal(height)
    extInput.setDistanceExtent(False, distance)
    result = extrudes.add(extInput)

    body = result.bodies.item(0)
    if z != 0:
        _move_body(body, 0, 0, z)

    return body


def _create_cylinder(comp, diameter, height, x, y, z):
    """创建圆柱体"""
    sketches = comp.sketches
    xyPlane = comp.xYConstructionPlane
    sketch = sketches.add(xyPlane)

    center = adsk.core.Point3D.create(x, y, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter / 2.0)

    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    distance = adsk.core.ValueInput.createByReal(height)
    extInput.setDistanceExtent(False, distance)
    result = extrudes.add(extInput)

    body = result.bodies.item(0)
    if z != 0:
        _move_body(body, 0, 0, z)

    return body


def _create_sphere(comp, diameter, x, y, z):
    """创建球体"""
    sketches = comp.sketches
    xzPlane = comp.xZConstructionPlane
    sketch = sketches.add(xzPlane)

    radius = diameter / 2.0
    center = adsk.core.Point3D.create(x, 0, z)

    sketch.sketchCurves.sketchArcs.addByCenterStartEnd(
        center,
        adsk.core.Point3D.create(x - radius, 0, z),
        adsk.core.Point3D.create(x + radius, 0, z),
    )
    sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(x - radius, 0, z),
        adsk.core.Point3D.create(x + radius, 0, z),
    )

    prof = sketch.profiles.item(0)
    revolves = comp.features.revolveFeatures
    revInput = revolves.createInput(
        prof,
        comp.yConstructionAxis,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    revInput.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    result = revolves.add(revInput)

    body = result.bodies.item(0)
    if y != 0:
        _move_body(body, 0, y, 0)

    return body


def _create_cone(comp, bottom_d, top_d, height, x, y, z):
    """创建圆锥/圆台"""
    sketches = comp.sketches
    xzPlane = comp.xZConstructionPlane
    sketch = sketches.add(xzPlane)

    bottom_r = bottom_d / 2.0
    top_r = top_d / 2.0

    lines = sketch.sketchCurves.sketchLines
    points = [
        adsk.core.Point3D.create(x - bottom_r, 0, z),
        adsk.core.Point3D.create(x + bottom_r, 0, z),
        adsk.core.Point3D.create(x + top_r, 0, z + height),
        adsk.core.Point3D.create(x - top_r, 0, z + height),
    ]

    for i in range(4):
        lines.addByTwoPoints(points[i], points[(i + 1) % 4])

    prof = sketch.profiles.item(0)
    revolves = comp.features.revolveFeatures
    revInput = revolves.createInput(
        prof,
        comp.yConstructionAxis,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    revInput.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    result = revolves.add(revInput)

    return result.bodies.item(0)


def _create_torus(comp, major_d, minor_d, x, y, z):
    """创建圆环体"""
    major_r = major_d / 2.0
    minor_r = minor_d / 2.0
    center_dist = major_r - minor_r

    sketches = comp.sketches
    xzPlane = comp.xZConstructionPlane
    sketch = sketches.add(xzPlane)

    center = adsk.core.Point3D.create(x + center_dist, 0, z)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, minor_r)

    sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(x + center_dist, 0, z - minor_r),
        adsk.core.Point3D.create(x + center_dist, 0, z + minor_r),
    )

    prof = sketch.profiles.item(0)
    revolves = comp.features.revolveFeatures
    revInput = revolves.createInput(
        prof,
        comp.yConstructionAxis,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    revInput.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    result = revolves.add(revInput)

    body = result.bodies.item(0)
    if y != 0:
        _move_body(body, 0, y, 0)

    return body


def _move_body(body, x, y, z):
    """移动实体"""
    if x == 0 and y == 0 and z == 0:
        return

    parent_comp = body.parentComponent
    moves = parent_comp.features.moveFeatures

    input_bodies = adsk.core.ObjectCollection.create()
    input_bodies.add(body)

    vector = adsk.core.Vector3D.create(x, y, z)
    moveInput = moves.createInput(input_bodies, vector)
    moves.add(moveInput)


# ==================== 特征操作 ====================


def op_apply_feature(rootComp, op):
    """应用特征操作"""
    feature_type = op.get("type")
    target_id = op.get("target_entity")
    params = op.get("params", {})

    body = state.get_entity(target_id)
    if not body:
        raise Exception(f"实体不存在: {target_id}")

    if not body.isValid:
        raise Exception(f"实体无效: {target_id}")

    feature_funcs = {
        "hole": _feature_hole,
        "hole_through": _feature_hole_through,
        "fillet": _feature_fillet,
        "chamfer": _feature_chamfer,
        "shell": _feature_shell,
        "draft": _feature_draft,
        "pocket": _feature_pocket,
        "slot": _feature_slot,
    }

    func = feature_funcs.get(feature_type)
    if func:
        func(body, params)
    else:
        raise Exception(f"不支持的特征类型: {feature_type}")

    state.add_to_history(f"特征{feature_type} [{target_id}]", "成功")
    return f"应用特征: {feature_type} -> {target_id}"


def _find_top_face(body):
    """找到实体的上表面"""
    top_face = None
    max_z = -99999

    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            bbox = face.boundingBox
            if bbox.maxPoint.z > max_z:
                max_z = bbox.maxPoint.z
                top_face = face

    return top_face


def _feature_hole(body, params):
    """打孔"""
    diameter = mm_to_cm(params["diameter"])
    depth = mm_to_cm(params["depth"])
    x_offset = mm_to_cm(params.get("x_offset", 0))
    y_offset = mm_to_cm(params.get("y_offset", 0))

    top_face = _find_top_face(body)
    if not top_face:
        raise Exception("找不到上表面")

    comp = body.parentComponent
    sketches = comp.sketches
    sketch = sketches.add(top_face)

    bbox = body.boundingBox
    cx = (bbox.minPoint.x + bbox.maxPoint.x) / 2 + x_offset
    cy = (bbox.minPoint.y + bbox.maxPoint.y) / 2 + y_offset
    center = adsk.core.Point3D.create(cx, cy, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter / 2.0)

    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    distance = adsk.core.ValueInput.createByReal(depth)
    extInput.setDistanceExtent(False, distance)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    extInput.participantBodies = bodies

    extrudes.add(extInput)


def _feature_hole_through(body, params):
    """通孔"""
    diameter = mm_to_cm(params["diameter"])

    top_face = _find_top_face(body)
    if not top_face:
        raise Exception("找不到上表面")

    comp = body.parentComponent
    sketches = comp.sketches
    sketch = sketches.add(top_face)

    bbox = body.boundingBox
    center = adsk.core.Point3D.create(
        (bbox.minPoint.x + bbox.maxPoint.x) / 2,
        (bbox.minPoint.y + bbox.maxPoint.y) / 2,
        0,
    )
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter / 2.0)

    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    extInput.setAllExtent(prof)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    extInput.participantBodies = bodies

    extrudes.add(extInput)


def _feature_fillet(body, params):
    """圆角"""
    radius = mm_to_cm(params["radius"])
    edges_type = params.get("edges", "all")

    comp = body.parentComponent
    edges = adsk.core.ObjectCollection.create()

    if edges_type == "all":
        for edge in body.edges:
            edges.add(edge)
    elif edges_type == "top":
        max_z = body.boundingBox.maxPoint.z
        for edge in body.edges:
            if (
                abs(edge.startVertex.geometry.z - max_z) < 0.001
                and abs(edge.endVertex.geometry.z - max_z) < 0.001
            ):
                edges.add(edge)
    elif edges_type == "bottom":
        min_z = body.boundingBox.minPoint.z
        for edge in body.edges:
            if (
                abs(edge.startVertex.geometry.z - min_z) < 0.001
                and abs(edge.endVertex.geometry.z - min_z) < 0.001
            ):
                edges.add(edge)
    elif edges_type == "vertical":
        for edge in body.edges:
            sp = edge.startVertex.geometry
            ep = edge.endVertex.geometry
            if abs(sp.x - ep.x) < 0.001 and abs(sp.y - ep.y) < 0.001:
                edges.add(edge)

    if edges.count == 0:
        return

    fillets = comp.features.filletFeatures
    filletInput = fillets.createInput()
    filletInput.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByReal(radius), True
    )
    fillets.add(filletInput)


def _feature_chamfer(body, params):
    """倒角"""
    distance = mm_to_cm(params["distance"])
    edges_type = params.get("edges", "all")

    comp = body.parentComponent
    edges = adsk.core.ObjectCollection.create()

    if edges_type == "all":
        for edge in body.edges:
            edges.add(edge)
    elif edges_type == "top":
        max_z = body.boundingBox.maxPoint.z
        for edge in body.edges:
            if (
                abs(edge.startVertex.geometry.z - max_z) < 0.001
                and abs(edge.endVertex.geometry.z - max_z) < 0.001
            ):
                edges.add(edge)

    if edges.count == 0:
        return

    chamfers = comp.features.chamferFeatures
    chamferInput = chamfers.createInput(edges, True)
    chamferInput.setToEqualDistance(adsk.core.ValueInput.createByReal(distance))
    chamfers.add(chamferInput)


def _feature_shell(body, params):
    """抽壳"""
    thickness = mm_to_cm(params["thickness"])
    face_type = params.get("face", "top")

    comp = body.parentComponent

    target_face = None
    if face_type == "top":
        max_z = -99999
        for face in body.faces:
            if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
                bbox = face.boundingBox
                if bbox.maxPoint.z > max_z:
                    max_z = bbox.maxPoint.z
                    target_face = face
    elif face_type == "bottom":
        min_z = 99999
        for face in body.faces:
            if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
                bbox = face.boundingBox
                if bbox.minPoint.z < min_z:
                    min_z = bbox.minPoint.z
                    target_face = face

    if not target_face:
        raise Exception("找不到目标面")

    shells = comp.features.shellFeatures
    shellInput = shells.createInput()
    removeFaces = adsk.core.ObjectCollection.create()
    removeFaces.add(target_face)
    shellInput.removeFaces = removeFaces
    shellInput.insideThickness = adsk.core.ValueInput.createByReal(thickness)
    shells.add(shellInput)


def _feature_draft(body, params):
    """拔模"""
    angle = params.get("angle", 5)

    comp = body.parentComponent
    drafts = comp.features.draftFeatures

    min_z = 99999
    fixed_face = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            bbox = face.boundingBox
            if bbox.minPoint.z < min_z:
                min_z = bbox.minPoint.z
                fixed_face = face

    if not fixed_face:
        raise Exception("找不到固定面")

    pull_direction = comp.zConstructionAxis
    draftInput = drafts.createInput(angle, pull_direction, fixed_face)
    draftInput.participantFaces = None
    drafts.add(draftInput)


def _feature_pocket(body, params):
    """口袋槽"""
    shape = params.get("shape", "circle")
    depth = mm_to_cm(params["depth"])

    top_face = _find_top_face(body)
    if not top_face:
        raise Exception("找不到上表面")

    comp = body.parentComponent
    sketches = comp.sketches
    sketch = sketches.add(top_face)

    bbox = body.boundingBox
    cx = (bbox.minPoint.x + bbox.maxPoint.x) / 2
    cy = (bbox.minPoint.y + bbox.maxPoint.y) / 2

    if shape == "circle":
        diameter = mm_to_cm(params["diameter"])
        center = adsk.core.Point3D.create(cx, cy, 0)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter / 2.0)
    else:
        width = mm_to_cm(params["width"])
        length = mm_to_cm(params["length"])
        lines = sketch.sketchCurves.sketchLines
        startPt = adsk.core.Point3D.create(cx - length / 2, cy - width / 2, 0)
        endPt = adsk.core.Point3D.create(cx + length / 2, cy + width / 2, 0)
        lines.addTwoPointRectangle(startPt, endPt)

    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    distance = adsk.core.ValueInput.createByReal(depth)
    extInput.setDistanceExtent(False, distance)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    extInput.participantBodies = bodies

    extrudes.add(extInput)


def _feature_slot(body, params):
    """槽"""
    length = mm_to_cm(params["length"])
    width = mm_to_cm(params["width"])
    depth = mm_to_cm(params["depth"])

    top_face = _find_top_face(body)
    if not top_face:
        raise Exception("找不到上表面")

    comp = body.parentComponent
    sketches = comp.sketches
    sketch = sketches.add(top_face)

    bbox = body.boundingBox
    cx = (bbox.minPoint.x + bbox.maxPoint.x) / 2
    cy = (bbox.minPoint.y + bbox.maxPoint.y) / 2

    radius = width / 2.0
    straight = length - width

    arc1_c = adsk.core.Point3D.create(cx - straight / 2, cy, 0)
    sketch.sketchCurves.sketchArcs.addByCenterStartEnd(
        arc1_c,
        adsk.core.Point3D.create(cx - straight / 2, cy - radius, 0),
        adsk.core.Point3D.create(cx - straight / 2, cy + radius, 0),
    )

    arc2_c = adsk.core.Point3D.create(cx + straight / 2, cy, 0)
    sketch.sketchCurves.sketchArcs.addByCenterStartEnd(
        arc2_c,
        adsk.core.Point3D.create(cx + straight / 2, cy + radius, 0),
        adsk.core.Point3D.create(cx + straight / 2, cy - radius, 0),
    )

    sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(cx - straight / 2, cy + radius, 0),
        adsk.core.Point3D.create(cx + straight / 2, cy + radius, 0),
    )
    sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(cx + straight / 2, cy - radius, 0),
        adsk.core.Point3D.create(cx - straight / 2, cy - radius, 0),
    )

    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    distance = adsk.core.ValueInput.createByReal(depth)
    extInput.setDistanceExtent(False, distance)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    extInput.participantBodies = bodies

    extrudes.add(extInput)


# ==================== 阵列/镜像/变换 ====================


def op_apply_pattern(rootComp, op):
    """阵列操作"""
    pattern_type = op.get("type")
    target_id = op.get("target_entity")
    params = op.get("params", {})

    body = state.get_entity(target_id)
    if not body:
        raise Exception(f"实体不存在: {target_id}")

    comp = body.parentComponent

    input_bodies = adsk.core.ObjectCollection.create()
    input_bodies.add(body)

    if pattern_type == "linear":
        direction = params.get("direction", "x")
        count = params.get("count", 2)
        distance = mm_to_cm(params["distance"])

        axis_map = {
            "x": comp.xConstructionAxis,
            "y": comp.yConstructionAxis,
            "z": comp.zConstructionAxis,
        }
        axis = axis_map.get(direction, comp.xConstructionAxis)

        patterns = comp.features.patternFeatures
        patternInput = patterns.createInput(
            input_bodies,
            axis,
            adsk.core.ValueInput.createByReal(count),
            adsk.core.ValueInput.createByReal(distance),
            adsk.fusion.PatternDistanceType.PatternDistanceTypeExtent,
        )
        patterns.add(patternInput)

    elif pattern_type == "circular":
        count = params.get("count", 6)
        angle = params.get("angle", 360)
        axis_name = params.get("axis", "z")

        axis_map = {
            "x": comp.xConstructionAxis,
            "y": comp.yConstructionAxis,
            "z": comp.zConstructionAxis,
        }
        axis = axis_map.get(axis_name, comp.zConstructionAxis)

        patterns = comp.features.patternFeatures
        patternInput = patterns.createInput(
            input_bodies,
            axis,
            adsk.core.ValueInput.createByReal(count),
            adsk.core.ValueInput.createByString(f"{angle} deg"),
            adsk.fusion.PatternDistanceType.PatternDistanceTypeExtent,
        )
        patterns.add(patternInput)

    state.add_to_history(f"阵列{pattern_type} [{target_id}]", "成功")
    return f"应用阵列: {pattern_type} -> {target_id}"


def op_apply_mirror(rootComp, op):
    """镜像操作"""
    target_id = op.get("target_entity")
    plane_name = op.get("plane", "xz")

    body = state.get_entity(target_id)
    if not body:
        raise Exception(f"实体不存在: {target_id}")

    comp = body.parentComponent

    input_bodies = adsk.core.ObjectCollection.create()
    input_bodies.add(body)

    plane_map = {
        "xy": comp.xYConstructionPlane,
        "yz": comp.yZConstructionPlane,
        "xz": comp.xZConstructionPlane,
    }
    mirror_plane = plane_map.get(plane_name, comp.xZConstructionPlane)

    mirrors = comp.features.mirrorFeatures
    mirrorInput = mirrors.createInput(input_bodies, mirror_plane)
    mirrors.add(mirrorInput)

    state.add_to_history(f"镜像 [{target_id}]", "成功")
    return f"应用镜像: {target_id}"


def op_apply_transform(rootComp, op):
    """变换操作"""
    transform_type = op.get("type")
    target_id = op.get("target_entity")
    params = op.get("params", {})

    body = state.get_entity(target_id)
    if not body:
        raise Exception(f"实体不存在: {target_id}")

    if transform_type == "move":
        x = mm_to_cm(params.get("x", 0))
        y = mm_to_cm(params.get("y", 0))
        z = mm_to_cm(params.get("z", 0))
        _move_body(body, x, y, z)

    elif transform_type == "rotate":
        axis_name = params.get("axis", "z")
        angle = params.get("angle", 90)

        comp = body.parentComponent
        axis_map = {
            "x": comp.xConstructionAxis,
            "y": comp.yConstructionAxis,
            "z": comp.zConstructionAxis,
        }
        axis = axis_map.get(axis_name, comp.zConstructionAxis)

        moves = comp.features.moveFeatures
        input_bodies = adsk.core.ObjectCollection.create()
        input_bodies.add(body)
        angle_input = adsk.core.ValueInput.createByString(f"{angle} deg")
        moveInput = moves.createInput(input_bodies, axis, angle_input)
        moves.add(moveInput)

    state.add_to_history(f"变换{transform_type} [{target_id}]", "成功")
    return f"应用变换: {transform_type} -> {target_id}"


def op_apply_boolean(rootComp, op):
    """布尔运算"""
    operation = op.get("operation", "join")
    target_id = op.get("target_entity")
    tool_id = op.get("tool_entity")

    target_body = state.get_entity(target_id)
    tool_body = state.get_entity(tool_id)

    if not target_body:
        raise Exception(f"目标实体不存在: {target_id}")
    if not tool_body:
        raise Exception(f"工具实体不存在: {tool_id}")

    comp = target_body.parentComponent
    combines = comp.features.combineFeatures

    tool_bodies = adsk.core.ObjectCollection.create()
    tool_bodies.add(tool_body)

    op_map = {
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    feature_op = op_map.get(operation, adsk.fusion.FeatureOperations.JoinFeatureOperation)

    combineInput = combines.createInput(target_body, tool_bodies)
    combineInput.operation = feature_op
    combines.add(combineInput)

    state.add_to_history(f"布尔{operation} [{target_id}, {tool_id}]", "成功")
    return f"布尔运算: {operation} ({target_id} + {tool_id})"
