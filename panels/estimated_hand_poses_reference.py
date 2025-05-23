import bpy
from ..operators.setup_video_reference import SetupVideoReferenceOperator


class EstimatedHandPosesReferencePanel(bpy.types.Panel):
    """A panel containing the general controls for operating the add-on."""
    bl_idname = "ESTIMATED_HAND_POSES_REFERENCE_PT_Panel"
    bl_label = "Estimated Hand Poses Reference"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Musical Instrument Animation"

    def draw(self, context):
        layout = self.layout
        # IMPORT VIDEO
        layout.label(text="Video Reference")
        layout.prop(context.scene.video_reference_settings, "start_frame")
        layout.operator("mia.check_sequencer_availability", text=SetupVideoReferenceOperator.bl_label,
                        icon='FILE_MOVIE')

        # IMPORT ESTIMATED HAND POSES
        layout.operator("mia.import_hand_poses", icon='IMPORT')

        # CLEAR REFERENCE
        layout.operator("mia.clear_reference", icon='TRASH')

        if context.window_manager.overlay_properties.overlay_active and context.scene.sync_mode != 'NONE':
            layout.label(text="For reliable overlay generation,", icon='WARNING_LARGE')
            layout.label(text="use \"Play Every Frame\" playback mode.",)

        # ----- OVERLAY CONTROLS -----
        overlay_controls = layout.box()
        overlay_controls.label(text='Overlay Controls')
        # RESUME/PAUSE OVERLAY GENERATION
        if context.window_manager.overlay_properties.pause_overlay_generation:
            overlay_controls.prop(context.window_manager.overlay_properties, "pause_overlay_generation",
                                  text='Resume Generation', icon='PLAY')
        else:
            overlay_controls.prop(context.window_manager.overlay_properties, "pause_overlay_generation", icon='PAUSE')

        row = overlay_controls.row()
        # REFRESH OVERLAY
        row.operator("mia.refresh_overlay", icon='FILE_REFRESH', text="Refresh")

        # CLEAR OVERLAY
        row.operator("mia.clear_overlay", icon='TRASH', text="Clear")
