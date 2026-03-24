extends SceneTree

func _init() -> void:
    var args = OS.get_cmdline_args()
    var script_index = args.find("--script")
    if script_index == -1 or args.size() <= script_index + 2:
        printerr("[ERROR] Usage: godot --headless --path <project> --script prepare_test_assets.gd <json_params>")
        quit(1)
        return

    var params_json = args[script_index + 2]
    var json = JSON.new()
    if json.parse(params_json) != OK:
        printerr("[ERROR] Failed to parse JSON params")
        quit(1)
        return

    var params = json.get_data()
    var action = str(params.get("action", ""))
    var success = false

    match action:
        "create_sprite_fixture":
            success = _create_sprite_fixture(
                str(params.get("scene_path", "")),
                str(params.get("texture_path", ""))
            )
        "create_animation_fixture":
            success = _create_animation_fixture(
                str(params.get("scene_path", "")),
                str(params.get("frames_dir", "")),
                params.get("frame_names", [])
            )
        "create_mesh_fixture":
            success = _create_mesh_fixture(str(params.get("scene_path", "")))
        _:
            printerr("[ERROR] Unknown action: " + action)
            quit(1)
            return

    if not success:
        quit(1)
        return

    print(JSON.stringify({
        "action": action,
        "ok": true
    }))
    quit()

func _create_sprite_fixture(scene_path: String, texture_path: String) -> bool:
    var full_scene_path = _normalize_res_path(scene_path)
    var full_texture_path = _normalize_res_path(texture_path)
    if full_scene_path.is_empty() or full_texture_path.is_empty():
        printerr("[ERROR] scene_path and texture_path are required")
        return false

    if not _ensure_directory_for_path(full_scene_path) or not _ensure_directory_for_path(full_texture_path):
        return false

    var gradient := Gradient.new()
    gradient.colors = PackedColorArray([Color(0.95, 0.2, 0.1), Color(0.1, 0.35, 0.9)])
    var texture := GradientTexture2D.new()
    texture.gradient = gradient
    texture.width = 16
    texture.height = 16

    var texture_error = ResourceSaver.save(texture, full_texture_path)
    if texture_error != OK:
        printerr("[ERROR] Failed to save texture fixture: " + str(texture_error))
        return false

    var root := Sprite2D.new()
    root.name = "SpriteRoot"

    var packed_scene := PackedScene.new()
    var pack_error = packed_scene.pack(root)
    if pack_error != OK:
        root.free()
        printerr("[ERROR] Failed to pack sprite fixture: " + str(pack_error))
        return false

    var save_error = ResourceSaver.save(packed_scene, full_scene_path)
    root.free()
    if save_error != OK:
        printerr("[ERROR] Failed to save sprite fixture: " + str(save_error))
        return false
    return true

func _create_mesh_fixture(scene_path: String) -> bool:
    var full_scene_path = _normalize_res_path(scene_path)
    if full_scene_path.is_empty():
        printerr("[ERROR] scene_path is required")
        return false

    if not _ensure_directory_for_path(full_scene_path):
        return false

    var root := Node3D.new()
    root.name = "MeshSource"

    var crate := MeshInstance3D.new()
    crate.name = "Crate"
    crate.mesh = BoxMesh.new()
    root.add_child(crate)
    crate.owner = root

    var collision := CollisionShape3D.new()
    collision.name = "Collision"
    collision.shape = BoxShape3D.new()
    crate.add_child(collision)
    collision.owner = root

    var packed_scene := PackedScene.new()
    var pack_error = packed_scene.pack(root)
    if pack_error != OK:
        root.free()
        printerr("[ERROR] Failed to pack mesh fixture: " + str(pack_error))
        return false

    var save_error = ResourceSaver.save(packed_scene, full_scene_path)
    root.free()
    if save_error != OK:
        printerr("[ERROR] Failed to save mesh fixture: " + str(save_error))
        return false
    return true

func _create_animation_fixture(scene_path: String, frames_dir: String, frame_names: Variant = []) -> bool:
    var full_scene_path = _normalize_res_path(scene_path)
    var full_frames_dir = _normalize_res_path(frames_dir)
    if full_scene_path.is_empty() or full_frames_dir.is_empty():
        printerr("[ERROR] scene_path and frames_dir are required")
        return false

    if not _ensure_directory_for_path(full_scene_path):
        return false

    var absolute_frames_dir = ProjectSettings.globalize_path(full_frames_dir)
    if not DirAccess.dir_exists_absolute(absolute_frames_dir):
        var dir_error = DirAccess.make_dir_recursive_absolute(absolute_frames_dir)
        if dir_error != OK:
            printerr("[ERROR] Failed to create frames directory: " + full_frames_dir)
            return false

    var resolved_names: Array = []
    if frame_names is Array and not (frame_names as Array).is_empty():
        resolved_names = frame_names
    else:
        resolved_names = ["idle_01.png", "idle_02.png", "idle_03.png"]

    var palette = [
        Color(0.95, 0.85, 0.2, 1.0),
        Color(0.2, 0.95, 0.85, 1.0),
        Color(0.85, 0.35, 0.95, 1.0),
        Color(0.95, 0.45, 0.15, 1.0),
        Color(0.35, 0.55, 0.95, 1.0)
    ]
    var frame_specs: Array = []
    for index in range(resolved_names.size()):
        frame_specs.append({
            "name": str(resolved_names[index]),
            "subject_x": 1 + (index % 5),
            "color": palette[index % palette.size()],
            "width": 8 + index
        })

    for frame_spec in frame_specs:
        var image = Image.create(int(frame_spec["width"]), 8, false, Image.FORMAT_RGBA8)
        image.fill(Color(1.0, 0.0, 1.0, 1.0))
        for y in range(2, 6):
            image.set_pixel(int(frame_spec["subject_x"]), y, frame_spec["color"])
            image.set_pixel(int(frame_spec["subject_x"]) + 1, y, frame_spec["color"])
        var frame_path = absolute_frames_dir.path_join(str(frame_spec["name"]))
        var save_image_error = image.save_png(frame_path)
        if save_image_error != OK:
            printerr("[ERROR] Failed to save animation frame: " + str(save_image_error))
            return false

    var root := AnimatedSprite2D.new()
    root.name = "SpriteAnimator"
    root.centered = false

    var packed_scene := PackedScene.new()
    var pack_error = packed_scene.pack(root)
    if pack_error != OK:
        root.free()
        printerr("[ERROR] Failed to pack animation fixture: " + str(pack_error))
        return false

    var save_error = ResourceSaver.save(packed_scene, full_scene_path)
    root.free()
    if save_error != OK:
        printerr("[ERROR] Failed to save animation fixture scene: " + str(save_error))
        return false
    return true

func _normalize_res_path(path_value: String) -> String:
    var path = path_value.strip_edges()
    if path.is_empty():
        return ""
    if path.begins_with("res://"):
        return path
    if path.begins_with("/"):
        path = path.substr(1)
    return "res://" + path

func _ensure_directory_for_path(target_path: String) -> bool:
    var target_directory = target_path.get_base_dir()
    if target_directory == "res://":
        return true

    var absolute_directory = ProjectSettings.globalize_path(target_directory)
    if DirAccess.dir_exists_absolute(absolute_directory):
        return true

    var error = DirAccess.make_dir_recursive_absolute(absolute_directory)
    if error != OK:
        printerr("[ERROR] Failed to create directory: " + target_directory)
        return false
    return true
