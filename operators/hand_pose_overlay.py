import bpy

from ..estimated_hand_poses import HandType
from ..miae_utils import find_area
from ..hand_pose_image_manager import HandPoseImageManager, ImageStripData, HAND_POSES_DIRECTORY


class HandPoseOverlayOperator(bpy.types.Operator):
    """A modal operator for managing overlay generation."""
    bl_idname = "mia.hand_pose_overlay"
    bl_label = "Hand Pose Overlay"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        super().__init__()
        self.image_manager = None
        self.latest_current_frame = -1
        self.start_frame_offset = 0

    @classmethod
    def poll(cls, context):
        return context.scene.reference_active

    def execute(self, context):
        # Retrieve the necessary image strip data from the Image Manager
        fps = context.scene.render.fps / context.scene.render.fps_base
        image_strips = self.image_manager.get_frame_image_strip_data(
            context.scene.frame_current - self.start_frame_offset, fps, 1, 3)

        # Add strips to the Sequencer
        for strip in image_strips:
            strip.start_frame += self.start_frame_offset
            strip.end_frame += self.start_frame_offset
            self.__add_image_strip(context, strip)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        overlay_properties = context.window_manager.overlay_properties

        if overlay_properties.refresh_overlay:
            self.__refresh_overlay(context)
            context.window_manager.overlay_properties.refresh_overlay = False
            self.report({'INFO'}, "Refreshing Hand Pose Overlay...")

        if overlay_properties.clear_overlay:
            self.cancel(context)
            self.report({'INFO'}, "Clearing Hand Pose Overlay...")
            return {'CANCELLED'}

        # Do nothing if overlay generation is paused or the preview/sequencer is not open.ed
        sequencer_area = find_area(context, area_type='SEQUENCE_EDITOR')
        if overlay_properties.pause_overlay_generation or sequencer_area is None:
            return {'PASS_THROUGH'}

        if context.scene.frame_current != self.latest_current_frame:
            self.execute(context)
            self.latest_current_frame = context.scene.frame_current

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self.__clear_overlay(context)
        self.__set_attributes(context)

        # avoids multiple hand poses in one frame when hand pose frequency > fps
        context.scene.tool_settings.sequencer_tool_settings.overlap_mode = 'OVERWRITE'

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        self.__clear_overlay(context)
        context.window_manager.overlay_properties.overlay_active = False
        context.window_manager.overlay_properties.clear_overlay = False

    def __set_attributes(self, context):
        sequence_editor = context.scene.sequence_editor
        image_height = sequence_editor.sequences[0].elements[0].orig_height
        image_width = sequence_editor.sequences[0].elements[0].orig_width
        filepath = context.window_manager.overlay_properties.filepath
        self.start_frame_offset = context.scene.video_reference_properties.start_frame - 1
        self.image_manager = HandPoseImageManager((image_height, image_width), filepath)

    def __refresh_overlay(self, context):
        self.__clear_overlay(context)  # Clear previous overlay
        self.__set_attributes(context)  # Reassign the attributes

    def __clear_overlay(self, context):
        bpy.ops.sequencer.select_all(action='SELECT')
        if context.scene.sequence_editor.sequences:
            context.scene.sequence_editor.sequences[0].select = False
        bpy.ops.sequencer.delete()
        self.latest_current_frame = -1

    @staticmethod
    def __add_image_strip(context, image_strip_data: ImageStripData):
        sequencer_area = find_area(context, area_type='SEQUENCE_EDITOR')
        # sequencer_area shouldn't be None as self.modal() checks if it is present in the screen.
        with context.temp_override(area=sequencer_area):
            bpy.ops.sequencer.image_strip_add(
                directory=HAND_POSES_DIRECTORY,
                relative_path=True,
                files=[{"name": image_strip_data.filename}],
                frame_start=image_strip_data.start_frame,
                frame_end=image_strip_data.end_frame,
                channel=2 if image_strip_data.hand_type == HandType.RIGHT else 3,
                show_multiview=False, fit_method='FIT',
                overlap_shuffle_override=True)


class HandPoseOverlayProperties(bpy.types.PropertyGroup):
    """A property group for communicating with the HandPoseOverlayOperator."""
    refresh_overlay: bpy.props.BoolProperty(default=False)
    clear_overlay: bpy.props.BoolProperty(default=False)
    overlay_active: bpy.props.BoolProperty(default=False)
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    pause_overlay_generation: bpy.props.BoolProperty(
        default=False,
        name='Pause Generation',
        description='Toggle overlay generation.')
