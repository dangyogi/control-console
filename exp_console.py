# exp_console.py

from alignment import *
import screen
from controls import *
import traffic_cop


def run():
    p = player()
    print(f"player: width={p.width}, height={p.height}")
    p2 = player2()
    print(f"player2: width={p2.width}, height={p2.height}")
    n = note(title="Strong Accent", cc_channel=2, cc_param_offset=0)
    print(f"note: width={n.width}, height={n.height}")
    g = grace_note(title="Grace", cc_channel=2, cc_param_offset=80)
    print(f"grace_note: width={g.width}, height={g.height}")
    t = trill()
    print(f"trill: width={t.width}, height={t.height}")
    f = fermata()
    print(f"fermata: width={f.width}, height={f.height}")
    with screen.Screen.update():
        x = S(2)
        p.draw(x, S(2))
        x += 2+p.width
        p2.draw(x, S(2))
        x = S(2)
        n.draw(x, S(540))
        x += 2+n.width
        g.draw(x, S(540))
        x += 2+g.width
        t.draw(x, S(540))
        x += 2+t.width
        f.draw(x, S(540))
    traffic_cop.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    # screen: width=1920 (20.75" == 0.0108"/pixel, height=1080 (11.11/16" == 0.0108"/pixel)
    with screen.Screen_class():
        print(f"{screen.Screen.width=}, {screen.Screen.height=}")
        run()

