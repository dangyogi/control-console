# exp_console.py

from alignment import *
import screen
from controls import *
import traffic_cop


def run():
    p = player()
    print(f"player: width={p.width}, height={p.height}")
    n = note()
    print(f"note: width={n.width}, height={n.height}")
    with screen.Screen.update():
        p.draw(S(2), S(2))
        n.draw(S(2), S(540))
    traffic_cop.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    # screen: width=1920 (20.75" == 0.0108"/pixel, height=1080 (11.11/16" == 0.0108"/pixel)
    with screen.Screen_class():
        print(f"{screen.Screen.width=}, {screen.Screen.height=}")
        run()

