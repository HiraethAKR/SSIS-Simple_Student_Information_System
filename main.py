import manager
import ui

def main():
    manager.init_files()
    app = ui.App()
    app.mainloop()

if __name__ == "__main__":
    main()