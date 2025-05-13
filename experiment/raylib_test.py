# raylib_test.py

import time
from pyray import *

init_window(800, 450, "Hello")
print("init_window done")
begin_drawing()
print("begin_drawing done")
clear_background(WHITE)
print("clear_background done")
draw_text("Hello world", 190, 200, 20, VIOLET)
print("draw_text done")
end_drawing()
print("end_drawing done")
time.sleep(10)
print("sleep done")
close_window()

#init_window(800, 450, "Hello")
#while not window_should_close():
#    begin_drawing()
#    clear_background(WHITE)
#    draw_text("Hello world", 190, 200, 20, VIOLET)
#    end_drawing()
#close_window()
