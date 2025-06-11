from kivy.app import App
from kivy.uix.label import Label

class myapp(App):
    def build(self):
        # self.icon = ""
        self.title = "My app"
        return Label(text="Hiiii")

# Run app
if __name__ == '__main__':
    app = myapp()
    app.run()