# Copyright 2023 ShadowOfHassen
# Imports
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
import enchant

try:
    import savvy
except ImportError:
    has_savvy = None
MAX_BUFFER = 5000
# Broken!!!
class EnchantIssue:
    def __init__(self, startpos, endpos, suggestions):
        self.start = startpos
        self.end = endpos
        self.replacements = suggestions
        self.offset = self.start
        self.length = self.end - self.start
        self.message = 'MISPELLED'
        self.type = 'bad_spell'
        
class EnchantChecker:
    def __init__(self):
        self.enchant_server = enchant.Dict('en_US')
    def check(self, text):
        count = 0
        errors = []
        text.replace('  ',' ')
        words = text.split()
        print(words)
        for word in words:
            suggestions = self.enchant_server.suggest(word)
            if suggestions != []:
                errors.append(EnchantIssue(count, count+len(word), suggestions))
        
            count += len(word)
        return errors
            

class Match:
    def __init__(self, start, end, des, cor, type):
        self.start = start
        self.end = end
        self.description =des
        self.range = (self.start, self.end)
        self.correction = cor
        self.type = type
    def return_text(self, text):
        text[self.start:self.end]


def get_matches_from_pos(mchs, pos):
    matches = []
    for m in mchs:
        if pos >= m.range[0] and pos <= m.range[1]:
            matches.append(m)
    return matches

class SpellChecker:
    
    def click_move_button(self, widget, event):
        if event.button == 3:
            self.move_mark_for_input(event.x, event.y)
    
    def click_move_popup(self, *args):
        self.text_buffer.move_mark(self.iter,  self._buffer.get_iter_at_mark(self._buffer.get_insert()))
    
    def move_mark_for_input(self, input_x, input_y):
        x, y = self.textview.window_to_buffer_coords(2, int(input_x), int(input_y))
        iter = self.textview.get_iter_at_location(x, y)
        if isinstance(iter, tuple):
            iter = iter[1]
        self.text_buffer.move_mark(self.iter,iter)
    
    def replace_word(self, d,match):
        start_iter = self.text_buffer.get_iter_at_offset(match.start)
        end_iter = self.text_buffer.get_iter_at_offset(match.end)
        self.text_buffer.delete(start_iter, end_iter)
        self.text_buffer.insert(start_iter,match.correction[0])
        self.on_key_insert(self.text_buffer,self.text_buffer.get_iter_at_offset(1),2,3)

        
        
    def __init__(self, textview, checker):
        self.textview = textview
        self.matches = []
        self.text_buffer = self.textview.get_buffer()
        self.checker =checker
        self.text_buffer.connect('insert-text', self.on_key_insert)
        self.misspelled =self.text_buffer.create_tag("misspelled",underline=4)#("underline", 4))# Gtk.TextTag.new("misspelled".format())
       # self.misspelled.set_property("underline", 4)
        self._table = self.text_buffer.get_tag_table()
        self._table.add(self.misspelled)
        self.iter= self.text_buffer.create_mark('iter', self.text_buffer.get_iter_at_offset(0))
        self.textview.connect("button-press-event", self.click_move_button)
        self.textview.connect("popup-menu", self.click_move_popup)
        self.textview.connect("populate-popup",  self.on_populate_text_popup)
        self.textview.connect('paste-clipboard', self.on_text_done)
        self.on_key_insert(self.text_buffer,self.text_buffer.get_iter_at_offset(1),2,3)

        
    def on_text_done(self,d):
        self.on_key_insert(self.text_buffer, 1,2,3)
        
    def on_populate_text_popup(self, item, menu, ):
        separator = Gtk.SeparatorMenuItem.new()
        separator.show()
        spellcheck_item = Gtk.MenuItem.new_with_label('Suggestions')
        spellcheck_item.show()
        submenu = Gtk.Menu.new()
        d = self.text_buffer.get_iter_at_mark(self.iter).get_offset()
        matches = get_matches_from_pos(self.matches, d)
        for m in matches:
            if m.correction != []:
                text_thing = m.description + '   ('+m.correction[0]+')'
            else:
                text_thing = m.description

            item = Gtk.MenuItem()
            label = Gtk.Label(label=text_thing)

            item.add(label)
            item.connect('activate', self.replace_word, m)
            submenu.append(item)
        submenu.show()
        spellcheck_item.set_submenu(submenu)
        menu.prepend(separator)
        menu.prepend(spellcheck_item)

        menu.show_all()


    def on_key_insert( self, buffer, inter, text, iteg,):
        d= self.text_buffer.get_end_iter()
        s= self.text_buffer.get_start_iter()
        text =self.text_buffer.get_text(d, s, True)
        if len(text)< MAX_BUFFER:
            offset = 0
            check_text = text
        else:
            raw_ammount = inter.get_offset()
            offset = (raw_ammount- int(MAX_BUFFER/2))
            start = buffer.get_iter_at_offset(raw_ammount- int(MAX_BUFFER/2))
            offset -=  start.get_line_offset()
            start.set_line_offset(0)
            end = buffer.get_iter_at_offset(raw_ammount+ int(MAX_BUFFER/2))
            end.set_line_offset(0)
            raw_text =self.text_buffer.get_text(start, end, True)
            check_text = raw_text
        #print(Server.get_languages())
        checks = self.checker.check(check_text)
        
        self.matches = []
        for c in checks:
            self.matches.append(Match(c.offset+offset, c.offset+c.length+offset, c.message, c.replacements, c.type ))
        end= self.text_buffer.get_end_iter()
        start= self.text_buffer.get_start_iter()
        self.text_buffer.remove_all_tags(start, end)
        for m in self.matches:
            start_iter = buffer.get_iter_at_offset(m.start)
            end_iter = buffer.get_iter_at_offset(m.end)
            self.text_buffer.apply_tag(self.misspelled, start_iter, end_iter)
class MarkdownFormatter:
    def __init__(self, textview):
        self.textview = textview
        self.text_buffer = self.textview.get_buffer()
        self.text_buffer.connect('insert-text', self.on_key_insert)
        self.tag_bold = self.text_buffer.create_tag("bold",weight=Pango.Weight.BOLD)
        self.tag_italic = self.text_buffer.create_tag("italic",style=Pango.Style.ITALIC, )
        self.tag_underline = self.text_buffer.create_tag("underline",underline=Pango.Underline.SINGLE)
        self.bold= False
        self.italic = False
        self.italic_start_iter = Gtk.TextIter()
        self.italic_end_iter = Gtk.TextIter()
        self.underline = False
        
    def on_key_insert(self, buffer, inter, text, iteg):
        end= self.text_buffer.get_end_iter()
        start= self.text_buffer.get_start_iter()
        all_text = self.text_buffer.get_text(end, start, True)
        self.text_buffer.remove_all_tags(start, end)
        count = 0
        self.italic =  False
        for d in all_text:
            count+= 1
            if '*' in d:
                if self.italic == False:
                    self.italic = True
                    self.italic_start_iter = buffer.get_iter_at_offset(count)
                elif self.italic:
                    self.italic = False
                    self.italic_end_iter = buffer.get_iter_at_offset(count)
                    self.text_buffer.apply_tag(self.tag_italic, self.italic_start_iter, self.italic_end_iter)
                  

text = '''
*I is good.*
she is smart.
"Hi" he said.

ddf
'''

if has_savvy is not None:
    checker = savvy.LanguageToolChecker()
else:
    checker = EnchantChecker()

if __name__ == "__main__":

    def quit(*args):
        Gtk.main_quit()

    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    window.set_title("Example")
    view = Gtk.TextView()
    view.get_buffer().set_text(text)

    spellchecker = SpellChecker(view, checker)
   # formater = MarkdownFormatter(view)
    window.set_default_size(600, 400)
    sd = Gtk.ScrolledWindow()
    sd.add(view)
    window.add(sd)
    window.show_all()
    window.connect("delete-event", quit)
    Gtk.main()
