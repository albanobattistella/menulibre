from gi.repository import Gtk, GdkPixbuf
import os

import subprocess

def detect_desktop_environment():
    desktop_environment = 'generic'
    if os.environ.get('KDE_FULL_SESSION') == 'true':
        desktop_environment = 'kde'
    elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
        desktop_environment = 'gnome'
    else:
        try:
            query = subprocess.Popen('xprop -root _DT_SAVE_MODE', shell=True, stdout=subprocess.PIPE)
            info = ''.join(query.stdout.readlines())
            if ' = "xfce4"' in info:
                desktop_environment = 'xfce'
        except (OSError, RuntimeError):
            pass
    return desktop_environment

de = detect_desktop_environment()
if de == 'gnome':
    import gconf
    client = gconf.Client()
    current_theme = client.get_string('/desktop/gnome/interface/icon_theme')
elif de == 'xfce':
    query = subprocess.Popen('xfconf-query -c xsettings -p /Net/IconThemeName', shell=True, stdout=subprocess.PIPE)
    current_theme = query.stdout.read().replace('\n', '')

    
home = os.getenv('HOME')



class IconTheme(Gtk.IconTheme):
    def __init__(self, theme_name, inherited=[], main=False):
        self.main_theme = main
        Gtk.IconTheme.__init__(self)
        if theme_name == '/usr/share/pixmaps':
            self.index = dict()
            for file in os.listdir(theme_name):
                if os.path.isfile(file):
                    name = os.path.splitext(file)[0]
                    self.index[name] = {'scalable': os.path.join( theme_name, file )}
            self.inherits = []
        else:
            if os.path.isdir( os.path.join(home, '.icons', theme_name) ):
                self.theme_dir = os.path.join(home, '.icons', theme_name)
            else:
                self.theme_dir = os.path.join('/usr', 'share', 'icons', theme_name)
            try:
                theme_index = open( os.path.join( self.theme_dir, 'index.theme' ), 'r' )
            except IOError:
                if os.path.isdir( os.path.join( self.theme_dir, theme_name ) ):
                    self.theme_dir = os.path.join( self.theme_dir, theme_name )
                    theme_index = open( os.path.join( self.theme_dir, 'index.theme' ), 'r' )
            inherited_themes = []
            for line in theme_index.readlines():
                if line[:9].lower() == 'inherits=':
                    inherited_themes = line.split('=')[1].split(',')
                    break
            inherited.append(theme_name)
            theme_index.close()
            self.index = dict()
            for toplevel_folder in os.listdir(self.theme_dir):
                try:
                    size = None
                    size_set_first = False
                    if os.path.isdir( os.path.join( self.theme_dir, toplevel_folder ) ):
                        if toplevel_folder.lower() == 'scalable':
                            size = 'scalable'
                            size_set_first = True
                        elif toplevel_folder.lower() == 'symbolic':
                            size = 'symbolic'
                            size_set_first = True
                        else:
                            try:
                                int(toplevel_folder.split('x')[0])
                                size = str(int(toplevel_folder.split('x')[0]))
                                size_set_first = True
                            except ValueError:
                                size = None
                        for second_dir in os.listdir( os.path.join( self.theme_dir, toplevel_folder ) ):
                            if second_dir == 'scalable':
                                size = 'scalable'
                            elif second_dir == 'symbolic':
                                size = 'symbolic'
                            elif not size or not size_set_first:
                                size = str(int(second_dir.split('x')[0]))
                            for filename in os.listdir( os.path.join( self.theme_dir, toplevel_folder, second_dir ) ):
                                if os.path.isfile( os.path.join( self.theme_dir, toplevel_folder, second_dir, filename ) ) and os.path.splitext(filename)[1] != '.icon':
                                    icon_name = os.path.splitext(filename)[0].replace('-symbolic', '')
                                    if icon_name not in self.index.keys():
                                        self.index[icon_name] = dict()
                                    self.index[icon_name][size] = os.path.join( self.theme_dir, toplevel_folder, second_dir, filename )
                except ValueError:
                    pass
            self.inherits = []
            for theme in inherited_themes:
                if theme not in inherited:
                    self.inherits.append(IconTheme(theme.replace('\n', ''), inherited))
            self.inherits.append(IconTheme('/usr/share/pixmaps', None))

    def get_theme_GdkPixbuf(self, name, IconSize):
        try:
            unused, width, height = Gtk.icon_size_lookup(IconSize)
            filename, sized = self.get_theme_image(name, IconSize)
            print filename
            try:
                if 'missing' in filename and 'missing' not in name:
                    if 'applications-' in filename:
                        return self.load_icon('applications-other', width, 0)
                    try:
                        return self.load_icon(name, width, 0)
                    except:
                        pass
            except TypeError:
                pass
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
            if not sized:
                return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.HYPER)
            return pixbuf
        except:
            pass

    def load_theme_image(self, GtkImage, name, IconSize):
        pass

    def get_all_icons(self, IconSize):
        print 'Getting all icons'
        uniques = dict()
        for icon in self.index.keys():
            uniques[icon] = self.get_theme_image(icon, IconSize)
        for theme in self.inherits:
            icons = theme.get_all_icons(IconSize)
            for icon in icons.keys():
                if icon not in uniques.keys():
                    uniques[icon] = icons[icon]
        return uniques
        
    def get_theme_image(self, name, IconSize):
        try:
            if os.path.isfile(name):
                return (name, False)
            unused, width, height = Gtk.icon_size_lookup(IconSize)
            if name in self.index.keys():
                if str(width) in self.index[name].keys():
                    return (self.index[name][str(width)], True)
                else:
                    try:
                        return (self.index[name]['scalable'], False)
                    except KeyError:
                        sizes = self.index[name].keys()
                        closest = None
                        difference = None
                        for size in sizes:
                            try:
                                length = int(size)
                                if difference == None or abs(width-length) < difference:
                                    difference = abs(width-length)
                                    closest = size
                            except ValueError:
                                return (self.index[name][size], False)
                        return (self.index[name][closest], False)
            else:
                for theme in self.inherits:
                    image = theme.get_theme_image(name, IconSize)
                    if image != None:
                        return image
                if self.main_theme:
                    try:
                        return (self.index['image-missing'][str(width)], True)
                    except KeyError:
                        for theme in self.inherits:
                            return theme.get_theme_image('image-missing', IconSize)
                else:
                    try:
                        return (self.index['image-missing'][str(width)], True)
                    except KeyError:
                        pass
                    return None
        except TypeError:
            try:
                return (self.index['image-missing'][str(width)], True)
            except KeyError:
                for theme in self.inherits:
                    return theme.get_theme_image('image-missing', IconSize)
        
class CurrentTheme(IconTheme):
    def __init__(self):
        IconTheme.__init__(self, current_theme, main=True)
