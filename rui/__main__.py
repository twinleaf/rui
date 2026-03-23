if __name__ == "__main__":
    from rui.rui import rui
    try:
        rui()
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
