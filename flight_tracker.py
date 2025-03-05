from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from folium.plugins import MarkerCluster
from opensky_api import OpenSkyApi
from bs4 import BeautifulSoup
import sys
import folium
import os
import threading
class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flight Tracker")
        self.refresh_map()
        self.init_UI()

    def init_UI(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(self.file_path))
        
        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        self.btn_update_map = QPushButton("Update Map")
        self.btn_delete_markers = QPushButton("Delete All Markers") 
        button_layout.addWidget(self.btn_update_map)
        button_layout.addWidget(self.btn_delete_markers)
        self.btn_update_map.clicked.connect(self.update_map)
        self.btn_delete_markers.clicked.connect(self.delete_markers)

        pb_panel = QWidget()
        self.pbar = QProgressBar(self)
        pb_layout = QVBoxLayout()
        pb_panel.setLayout(pb_layout)
        pb_layout.addWidget(self.pbar)


        layout.addWidget(self.browser, 4)
        layout.addWidget(button_panel, 0)
        layout.addWidget(pb_panel, 0)

        self.setCentralWidget(main_widget)
        
    def inject_script(self):
        with open (self.file_path, "r", encoding = "utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        
        script = soup.new_tag("script")
        script.attrs["src"] = "map_limiter.js"
        soup.find("html").append(script)
        soup.find("html").append("\n")

        with open (self.file_path, "w", encoding = "utf-8") as f:
            f.write(str(soup))
    
    def refresh_map(self):
        self.file_path = os.path.abspath("map.html")

        self.map = folium.Map(
            max_bounds = True
        )

        self.map.save(self.file_path)
        self.inject_script()

    def delete_markers(self):
        self.refresh_map()
        self.browser.setUrl(QUrl.fromLocalFile(self.file_path))
        self.pbar.setValue(0)

    def update_map(self):
        self.btn_enable_disable(0)
        self.pbar.setRange(0, 0)

        api_call = threading.Thread(target = self.api_call, daemon = True)
        api_call.start()
        
    def api_call(self):
        api = OpenSkyApi()
        s = api.get_states()

        self.states_list = []
        for states in s.states:
            if states.latitude is not None and states.longitude is not None:
                self.states_list.append((states.icao24, states.latitude, states.longitude))

        QTimer.singleShot(0, self.updating_map)

    def updating_map(self):
        self.btn_enable_disable(1)
        self.pbar.setRange(0, 100)

        states_total = len(self.states_list)
        states_counter = 0
        marker_cluster = MarkerCluster().add_to(self.map)
        
        for states in self.states_list:
            states_counter += 1
            self.pbar.setValue(int((states_counter*100)/states_total))
            folium.Marker(
                location = [states[1], states[2]],
                popup = states[0],
                icon  = folium.Icon(icon = "plane", prefix = "fa")
            ).add_to(marker_cluster)

        self.map.save(self.file_path)
        self.inject_script()

        self.browser.setUrl(QUrl.fromLocalFile(self.file_path))

    def btn_enable_disable(self, option):
        if option == 0:
            self.btn_update_map.setEnabled(False)
            self.btn_delete_markers.setEnabled(False)
        elif option == 1:
            self.btn_update_map.setEnabled(True)
            self.btn_delete_markers.setEnabled(True)
        
if __name__ == "__main__":
    os.chdir(os.path.join(os.getcwd(), "flight_tracker"))
    app = QApplication(sys.argv) 
    app.setStyle("Fusion")
    window = MapWindow()
    window.show()

    sys.exit(app.exec_())