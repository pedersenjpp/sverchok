import bpy, bmesh, mathutils
from mathutils import Matrix
from util import *
from node_s import *
import webbrowser
import os
import urllib

# needed to show current version
script_paths = bpy.utils.script_paths()[1]
svversion = os.path.normpath(os.path.join(script_paths, 'addons', 'sverchok-master', 'version'))
svlocal_file = open(svversion,'r+')
svversion_local = svlocal_file.read()[:-1]
svlocal_file.close()

class SverchokUpdateAll(bpy.types.Operator):
    """Sverchok update all"""
    bl_idname = "node.sverchok_update_all"
    bl_label = "Sverchok update all"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeTreeUpdate2()
        speedUpdate()
        return {'FINISHED'}

class SverchokPurgeCache(bpy.types.Operator):
    """Sverchok purge cache"""
    bl_idname = "node.sverchok_purge_cache"
    bl_label = "Sverchok purge cache"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print(bpy.context.space_data.node_tree.name)
        return {'FINISHED'}
    
class SverchokHome(bpy.types.Operator):
    """Sverchok Home"""
    bl_idname = "node.sverchok_home"
    bl_label = "Sverchok go home"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        page = 'http://nikitron.cc.ua/blend_scripts.html'
        if context.scene.use_webbrowser:
            try:
                webbrowser.open_new_tab(page)
            except:
                self.report({'WARNING'}, "Error in opening the page %s." % (page))
        return {'FINISHED'}

class SverchokUpdateAddon(bpy.types.Operator):
    """ Sverchok update addon without any browsing and so on. After - press F8 to reload addons """
    bl_idname = "node.sverchok_update_addon"
    bl_label = "Sverchok update addon in linux"
    bl_options = {'REGISTER', 'UNDO'}
    
    #version = bpy.props.StringProperty(name='Your Blender version is', default='2.70')
    
    def execute(self, context):
        
        #if os.sys.platform == 'linux':
        try:
            os.curdir = os.path.normpath(os.path.join(bpy.utils.script_paths()[1], 'addons/sverchok-master')) 
            #os.environ['HOME']+'/.config/blender/'+bpy.app.version_string[:4]
            os.chdir(os.curdir)
            version_url = urllib.request.urlretrieve('https://raw.githubusercontent.com/nortikin/sverchok/master/version')
            url_file = open(version_url[0],'r')
            version_url = url_file.read()[:-1]
            url_file.close()
            local_file = open(os.path.join(os.curdir, 'version'), 'r')
            version_local = local_file.read()[:-1]
            local_file.close()
            
            if version_local == version_url:
                self.report({'INFO'}, "You already have latest version of Sverchok, no need to upgrade.")
                return {'CANCELLED'}
            else:
                os.curdir = os.path.normpath(bpy.utils.script_paths()[1]+'/addons')
                os.chdir(os.curdir)
                #os.system('wget https://github.com/nortikin/sverchok/archive/master.zip')
                try:
                    url = 'https://github.com/nortikin/sverchok/archive/master.zip'
                    file = urllib.request.urlretrieve(url,os.path.normpath(os.curdir+'/master.zip'))
                    ZipFile(file[0]).extractall(path=os.curdir, members=None, pwd=None)
                    os.remove(file[0])
                    #os.system('unzip -o master.zip -d '+os.curdir)
                    #os.system('rm master.zip')
                    self.report({'INFO'}, "Unzipped, reload addons with F8 button")
                    
                except:
                    self.report({'ERROR'}, "cannot unzip archive somehow")
                    os.system('rm master.zip')
        except:
            self.report({'ERROR'}, "Cannot download archive or compare versions")
        #else:
        #    self.report({'WARNING'}, "It is not Linux, install Linux")
        return {'FINISHED'}
    
    #def invoke(self, context, event):
        #wm = context.window_manager
        #wm.invoke_props_dialog(self, 250)
        #return {'RUNNING_MODAL'}

class SverchokToolsMenu(bpy.types.Panel):
    bl_idname = "Sverchok_tools_menu"
    bl_label = "Sverchok "+svversion_local
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin=True
    
    @classmethod
    def poll(cls,context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False
                
    def draw(self, context):
        layout = self.layout
        #layout.scale_y=1.1
        layout.active = True
        col = layout.column()
        col.scale_y=3.0
        
        col.operator(SverchokUpdateAll.bl_idname, text="UPDATE")
      
        box=layout.box()
        #box.label(text="Layout manager")
        little_width = 0.12
        col=box.column(align=True)
        row=col.row(align=True)
        row.label(text='Layout')
        col1=row.column(align=True)
        col1.scale_x=little_width
        col1.label(icon='RESTRICT_VIEW_OFF',text=' ')
        #row.label(text='Bake')
        col2=row.column(align=True)
        col2.scale_x=little_width
        col2.label(icon='ANIM',text=' ')
        col2.icon
      
        ng = bpy.data.node_groups
      
        for name,tree in ng.items():
            if tree.bl_idname == 'SverchCustomTreeType':
                
                row=col.row(align=True)
                
                if name==context.space_data.node_tree.name:
                    row.label(text=name,icon='LINK')
                else:
                    row.label(text=name)
                
                split = row.column(align=True)
                split.scale_x = little_width
                if tree.sv_show:
                    split.prop(tree, 'sv_show',icon='UNLOCKED',text=' ')
                else:
                    split.prop(tree, 'sv_show',icon='LOCKED',text=' ')
                split = row.column(align=True)
                split.scale_x = little_width
                if tree.sv_animate:
                    split.prop(tree, 'sv_animate',icon='UNLOCKED',text=' ')
                else:
                    split.prop(tree, 'sv_animate',icon='LOCKED',text=' ')
                    
        
        layout.column().operator(SverchokUpdateAddon.bl_idname, text='Upgrade Sverchok addon')
        #       row.prop(tree, 'sv_bake',text=' ')
  
        #box = layout.box()
        #col = box.column(align=True)
        #col.label(text="Sverchok v_0.2.8")
        #col.label(text='layout: '+context.space_data.node_tree.name)
        #row = col.row(align=True)
        #row.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        #row.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        #row = col.row(align=True)
        #row.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        #row.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'
  
        
        


class ToolsNode(Node, SverchCustomTreeNode):
    ''' Tools for different purposes '''
    bl_idname = 'ToolsNode'
    bl_label = 'Tools node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    #bl_height_default = 110
    #bl_width_min = 20
    #color = (1,1,1)
    color_ = bpy.types.ColorRamp
    
    def init(self, context):
        pass
        
    def draw_buttons(self, context, layout):
        col = layout.column()
        col.scale_y=15
        col.template_color_picker
        col.operator(SverchokUpdateAll.bl_idname, text="UPDATE")
        #box = layout.box()
        
        #col = box.column(align=True)
        #col.template_node_socket(color=(0.0, 0.9, 0.7, 1.0))
        #col.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        #col.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        #col.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        #col.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'
        
        lennon = len(bpy.data.node_groups[self.id_data.name].nodes)
        group = self.id_data.name
        tex = str(lennon) + ' | ' + str(group)
        layout.label(text=tex)
        #layout.template_color_ramp(self, 'color_', expand=True)
    
    def update(self):
        self.use_custom_color = True
        self.color = (1.0,0.0,0.0)
        
                
    def update_socket(self, context):
        pass

def register():
    bpy.utils.register_class(SverchokUpdateAll)
    bpy.utils.register_class(SverchokUpdateAddon)
    bpy.utils.register_class(SverchokPurgeCache)
    bpy.utils.register_class(SverchokHome)
    bpy.utils.register_class(SverchokToolsMenu)
    bpy.utils.register_class(ToolsNode)
    
def unregister():
    bpy.utils.unregister_class(ToolsNode)
    bpy.utils.unregister_class(SverchokToolsMenu)
    bpy.utils.unregister_class(SverchokHome)
    bpy.utils.unregister_class(SverchokPurgeCache)
    bpy.utils.unregister_class(SverchokUpdateAddon)
    bpy.utils.unregister_class(SverchokUpdateAll)

if __name__ == "__main__":
    register()
