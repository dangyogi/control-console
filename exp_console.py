# exp_console.py

from collections import defaultdict

from alignment import *
import screen
from controls import *
import traffic_cop


Screens = dict(     # {screen_name: [panel]}
    home=[],        # staff_1, staff_2, slur_start, slur_middle, slur_stop, staccato, staccatissimo,
                    # strong_accent
    misc=[],        # accent, tenuto, detached_legato, grace, grace_slash, trill, fermata, player_2
    voice=[],       # voice_1-8
    chord=[],       # chord_1-7
    arpeggiate=[],  # arpeggiate_1-7
)

Player = None
Screen_menu = None

def load_new_screen():
    if screen.New_screen is None:
        return False
    load_screen(screen.New_screen)
    screen.New_screen = None
    return True

def load_screen(name):
    hgap = 2
    left_gap = 2
    top_gap = 2
    with screen.Screen.update(from_scratch=True):
        x = S(left_gap)
        y = S(top_gap)
        def draw(panel):
            nonlocal x, y
            panel.draw(x, y)
            x += hgap + panel.width
        draw(Player)
        for i, panel in enumerate(Screens[name], 1):
            draw(panel)
            if i == 4:
                x = S(left_gap)
                y = S(540)
                draw(Screen_menu)

def run():
    global Player, Screen_menu

    Player = player()
    print(f"player: width={Player.width}, height={Player.height}")
    Screen_menu = screens()
    print(f"screens: width={Screen_menu.width}, height={Screen_menu.height}")

    n = note(title="Staff 1", cc_channel=2, cc_param_offset=120)
    print(f"note: width={n.width}, height={n.height}")

    Screens["home"].append(n)
    Screens["home"].append(note(title="Staff 2", cc_channel=2, cc_param_offset=124))
    Screens["home"].append(note(title="Slur Start", cc_channel=3, cc_param_offset=0))
    Screens["home"].append(note(title="Slur Middle", cc_channel=3, cc_param_offset=4))
    Screens["home"].append(note(title="Slur End", cc_channel=3, cc_param_offset=8))
    Screens["home"].append(note(title="Staccato", cc_channel=2, cc_param_offset=12))
    Screens["home"].append(note(title="Staccatissimo", cc_channel=2, cc_param_offset=20))
    Screens["home"].append(note(title="Strong Accent", cc_channel=2, cc_param_offset=0))

    Screens["misc"].append(note(title="Accent", cc_channel=2, cc_param_offset=4))
    Screens["misc"].append(note(title="Tenuto", cc_channel=2, cc_param_offset=8))
    Screens["misc"].append(note(title="Detached Legato", cc_channel=2, cc_param_offset=16))
    Screens["misc"].append(grace_note(title="Grace", cc_channel=2, cc_param_offset=80))
    Screens["misc"].append(grace_note(title="Grace Slash", cc_channel=2, cc_param_offset=84))
    t = trill()
    print(f"trill: width={t.width}, height={t.height}")
    Screens["misc"].append(t)
    f = fermata()
    print(f"fermata: width={f.width}, height={f.height}")
    Screens["misc"].append(f)
    p2 = player2()
    print(f"player2: width={p2.width}, height={p2.height}")
    Screens["misc"].append(p2)

    Screens["voice"].append(note(title="Voice 1", cc_channel=2, cc_param_offset=88))
    Screens["voice"].append(note(title="Voice 2", cc_channel=2, cc_param_offset=92))
    Screens["voice"].append(note(title="Voice 3", cc_channel=2, cc_param_offset=96))
    Screens["voice"].append(note(title="Voice 4", cc_channel=2, cc_param_offset=100))
    Screens["voice"].append(note(title="Voice 5", cc_channel=2, cc_param_offset=104))
    Screens["voice"].append(note(title="Voice 6", cc_channel=2, cc_param_offset=108))
    Screens["voice"].append(note(title="Voice 7", cc_channel=2, cc_param_offset=112))
    Screens["voice"].append(note(title="Voice 8", cc_channel=2, cc_param_offset=116))

    Screens["chord"].append(note(title="Chord 1", cc_channel=2, cc_param_offset=52))
    Screens["chord"].append(note(title="Chord 2", cc_channel=2, cc_param_offset=56))
    Screens["chord"].append(note(title="Chord 3", cc_channel=2, cc_param_offset=60))
    Screens["chord"].append(note(title="Chord 4", cc_channel=2, cc_param_offset=64))
    Screens["chord"].append(note(title="Chord 5", cc_channel=2, cc_param_offset=68))
    Screens["chord"].append(note(title="Chord 6", cc_channel=2, cc_param_offset=72))
    Screens["chord"].append(note(title="Chord 7", cc_channel=2, cc_param_offset=76))

    Screens["arpeggiate"].append(note(title="Arpeggiate 1", cc_channel=2, cc_param_offset=24))
    Screens["arpeggiate"].append(note(title="Arpeggiate 2", cc_channel=2, cc_param_offset=28))
    Screens["arpeggiate"].append(note(title="Arpeggiate 3", cc_channel=2, cc_param_offset=32))
    Screens["arpeggiate"].append(note(title="Arpeggiate 4", cc_channel=2, cc_param_offset=36))
    Screens["arpeggiate"].append(note(title="Arpeggiate 5", cc_channel=2, cc_param_offset=40))
    Screens["arpeggiate"].append(note(title="Arpeggiate 6", cc_channel=2, cc_param_offset=44))
    Screens["arpeggiate"].append(note(title="Arpeggiate 7", cc_channel=2, cc_param_offset=48))

    load_screen("home")
    traffic_cop.load_new_screen = load_new_screen
    traffic_cop.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    # screen: width=1920 (20.75" == 0.0108"/pixel, height=1080 (11.11/16" == 0.0108"/pixel)
    with screen.Screen_class():
        print(f"{screen.Screen.width=}, {screen.Screen.height=}")
        run()

