#This is part of the source code for the Paineira Graphical User Interface - Iguape
#The code is distributed under the GNU GPL-3.0 License. Please refer to the main page (https://github.com/cnpem/iguape) for more information

"""
This is the main script for the excution of the Paineira Graphical User Interface, a GUI for visualization and data processing during in situ experiments at Paineira.
In this script, both GUIs used by the program are called and all of the backend functions and processes are defined. 
"""

import sys, time, gc, copy, matplotlib
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import matplotlib.colorbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.widgets import SpanSelector, Cursor
from matplotlib.cm import ScalarMappable
import matplotlib.font_manager
from matplotlib.colors import LogNorm, PowerNorm, CenteredNorm
import numpy as np
import pandas as pd
from Monitor import FolderMonitor
from GUI.iguape_GUI import Ui_MainWindow
from GUI.pk_window import Ui_pk_window
from GUI.export_figure import Ui_Export_Figure
from GUI.filter_gui import Ui_Filter_Dialog
from Monitor import *


if getattr(sys, 'frozen', False): 
    import pyi_splash #If the program is executed as a pyinstaller executable, import pyi_splash for the Splash Screen

license  = 'GNU GPL-3.0 License'
    
counter.count = 0
fonts_list = [font.name for font in matplotlib.font_manager.fontManager.ttflist]
cmaps = [cmap for cmap in plt.colormaps()]

class Window(QMainWindow, Ui_MainWindow):
    """Class for IGUAPE main window. It inherits QMainWindow from PyQt5 and Ui_MainWindow from GUI.iguape_GUI

    :param QMainWindow: QMainWindow from PyQt5
    :type QMainWindow: QMainWindow
    :param Ui_MainWindow: Ui_MainWindow from GUI.iguape_GUI
    :type Ui_MainWindow: QMainWindow
    """    
    def __init__(self, parent=None):
        """Constructor for Window class

        Args:
            parent (optional): Defaults to None.
        """        
        super().__init__(parent)
        self.setupUi(self)
        geometry = QGuiApplication.screens()[-1].availableGeometry()
        #print(geometry)
        
        self.setGeometry(geometry)
        self.create_graphs_layout()
        self.gc_collector = GarbageCollector()
        self.gc_collector.start()
        if getattr(sys, 'frozen', False):
            pyi_splash.close() #After the GUI initialization, close the Splash Screen

    def create_graphs_layout(self):
        """Routine to initialize and connect UI elements. All parameters and flags are initiated and UI element's signals are connected to its functions.
        """        
        self.url_data = {self.paineira_logo: "https://lnls.cnpem.br/facilities/paineira-en/", self.LNLS_logo: "https://lnls.cnpem.br/en/", self.CNPEM_logo: "https://cnpem.br/en/", self.iguape_logo: "https://cnpem.github.io/iguape/"}
        for logo in self.url_data.keys():
            logo.installEventFilter(self)
        #self.XRD_data_layout = QVBoxLayout()
        # Creating the main Figure and Layout #
        self.fig_main = Figure(figsize=(8, 6), dpi=100)
        self.gs_main = self.fig_main.add_gridspec(1, 1)
        self.ax_main = self.fig_main.add_subplot(self.gs_main[0, 0])
        self.fig_main.set_layout_engine('constrained')
        self.canvas_main = FigureCanvas(self.fig_main)
        self.ax_main.set_xlabel('2θ (°)', fontsize = 15)
        self.ax_main.set_ylabel('Intensity (a.u.)', fontsize = 15)
        self.XRD_data_layout.addWidget(self.canvas_main)
        #self.XRD_data_tab.setLayout(self.XRD_data_layout)
    
        #self.peak_fit_layout = QVBoxLayout()
        #Creating the fitting parameter Figure and Layout#
        self.fig_sub = Figure(figsize=(8, 5), dpi=100)
        self.gs_sub = self.fig_sub.add_gridspec(1, 3)
        self.ax_2theta = self.fig_sub.add_subplot(self.gs_sub[0, 0])
        self.ax_area = self.fig_sub.add_subplot(self.gs_sub[0, 2])
        self.ax_FWHM = self.fig_sub.add_subplot(self.gs_sub[0, 1])
        self.fig_sub.set_layout_engine('constrained')
        self.canvas_sub = FigureCanvas(self.fig_sub)
        self.peak_fit_layout.addWidget(self.canvas_sub)
        #self.peak_fit_tab.setLayout(self.peak_fit_layout)
        self.cursor = None #Cursor(self.ax_main, useblit=True, color='red', linewidth=1, horizOn=False)
        
        
        self.fig_contour = Figure(figsize=(8, 6), dpi = 100)
        self.gs_contour = self.fig_contour.add_gridspec(1,1)
        self.ax_contour = self.fig_contour.add_subplot(self.gs_contour[0,0])
        self.fig_contour.set_layout_engine('constrained')
        self.canvas_contour = FigureCanvas(self.fig_contour)
        self.ax_contour.set_xlabel('2θ (°)', fontsize = 15)
        self.contour_layout.addWidget(self.canvas_contour)

        self.fig_norm = Figure(figsize=(8,6), dpi= 100)
        self.gs_norm = self.fig_norm.add_gridspec(1,1)
        self.ax_norm = self.fig_norm.add_subplot(self.gs_norm[0,0])
        self.fig_norm.set_layout_engine('constrained')
        self.canvas_norm = FigureCanvas(self.fig_norm)
        self.ax_norm.set_xlabel('2θ (°)', fontsize = 15)
        self.normalization_layout.addWidget(self.canvas_norm)
        

        #Creating a colormap on the main canvas#
        self.cmap = plt.get_cmap("coolwarm") 
        self.norm = plt.Normalize(vmin=0, vmax=1) # Initial placeholder values for norm #
        self.sm = ScalarMappable(cmap=self.cmap, norm=self.norm)
        self.sm.set_array([])
        self.cax = self.fig_main.colorbar(self.sm, ax=self.ax_main) # Creating the colorbar axes #
        self.cax_2 = self.fig_sub.colorbar(self.sm, ax=self.ax_area) # Creating the colorbar axes #
        self.cax_3 = self.fig_contour.colorbar(self.sm, ax = self.ax_contour)
        self.cax_4 = self.fig_norm.colorbar(self.sm, ax = self.ax_norm)
        #Connecting functions to buttons#
        self.refresh_button.clicked.connect(self.update_graphs)
        self.refresh_button_peak_fit.clicked.connect(self.update_graphs)
        
        self.reset_button.clicked.connect(self.reset_interval)
        
        self.peak_fit_button.clicked.connect(self.select_fit_interval)
        self.save_peak_fit_data_button.clicked.connect(self.save_data_frame)
        self.contour_button.clicked.connect(self.contour)
        self.color_pallete_comboBox.activated.connect(self.on_change_color_pallete)
        self.color_pallete_comboBox_2.activated.connect(self.on_change_color_pallete)
        #self.checkBox.setChecked(True)
        self.checkBox.stateChanged.connect(self.on_change_vline_checkbox)
        self.plot_with_temp = False
        self.export_window = None
        self.selected_interval = None
        self.filter_window = None
        self.fit_interval = None
        self.monitor = None
        self.normalize_state = False
        self.norms = {'LogNorm': LogNorm(), "PowerNorm": PowerNorm(gamma=0.5), 'CenteredNorm': CenteredNorm()}
        
        self.folder_selected = False
        self.temp_mask_signal = False
        self.temp_mask = slice(None)
        self.plot_data = pd.DataFrame()

        #Create span selector on the main plot#
        self.span = SpanSelector(self.ax_main, self.onselect, 'horizontal', useblit=True,
                                props=dict(alpha=0.3, facecolor='red', capstyle='round'))
        
        self.color_pallete_comboBox.addItems(cmaps)
        self.color_pallete_comboBox.setCurrentIndex(44)

        self.color_pallete_comboBox_2.addItems(cmaps)
        self.color_pallete_comboBox_2.setCurrentIndex(44)

        self.peak_fit_layout.addWidget(NavigationToolbar2QT(self.canvas_sub, self))
        self.toolbar = NavigationToolbar2QT(self.canvas_main, self)
        self.contour_layout.addWidget(NavigationToolbar2QT(self.canvas_contour, self))
        self.normalization_layout.addWidget(NavigationToolbar2QT(self.canvas_norm, self))
        self.XRD_data_layout.addWidget(self.toolbar)
        self.canvas_main.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.normalize_button.clicked.connect(self.normalize)
        self.actionOpen_New_Folder.triggered.connect(self.select_folder)
        self.actionExport_Figure.triggered.connect(self.export_figure)
        self.actionAbout.triggered.connect(self.about)
        
        

        self.offset_slider.setMinimum(1)
        self.offset_slider.setMaximum(99)
        self.offset_slider.setValue(90)

    
        self.XRD_measure_order_checkbox.stateChanged.connect(self.measure_order_index)
        self.temperature_checkbox.stateChanged.connect(self.temp_index)
        self.filter_button.clicked.connect(self.apply_filter)
    
    
    def _open_url(self, url: str):
        """Uses QDesktopServices to open URL from logos.

        :param url: url to websites (as strings)
        :type url: str
        """        
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            pass
    
    def eventFilter(self, source: QLabel, event: QEvent):
        """eventFilter method for logo QLabel. It tracks a mouse press event and calls the :meth: `~Window._open_url`

        :param source: Object name of logo in IGUAPE UI (QLabel)
        :type source: QLabel
        :param event: QEvent to track mouse click
        :type event: QEvent
        :return: Boolean value that determines the excution of :meth: `~Window._open_url`
        :rtype: Bool
        """        
            
        if event.type() == QEvent.MouseButtonPress:
            if source in self.url_data:
                url = self.url_data[source]
                self._open_url(url)
                return True
          
        return super().eventFilter(source, event)

    def update_graphs(self):
        """_summary_
        """        
        #try:
        
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.ax_main.clear()
        

        self._update_main_figure()
        self._plot_fitting_parameters()
        

        self.canvas_main.draw()
        self.canvas_sub.draw()
        gc.collect()

        self.cax.update_normal(self.sm)
        self.cax_2.update_normal(self.sm)

        #except KeyError as e:
        #    print(f'Please, initialize the monitor! Error: {e}')
        #    QMessageBox.warning(self, '','Please initialize the monitor!') 
        #    pass

        QApplication.restoreOverrideCursor()


    def _get_mask(self, i):
        """_summary_

        Args:
            i (_type_): _description_

        Returns:
            _type_: _description_
        """    
        if self.selected_interval:
            dois_theta = self.read_data(self.plot_data['file_name'][i])[0]
            return (dois_theta >= self.selected_interval[0]) & (dois_theta <= self.selected_interval[1])
        return slice(None)

    def update_colormap(self, color_map_type, label):
        """_summary_

        Args:
            color_map_type (_type_): _description_
            label (_type_): _description_
        """        
        self.norm.vmin, self.norm.vmax = min(self.plot_data[color_map_type]), max(self.plot_data[color_map_type])
        self.sm.set_norm(self.norm)
        self.cax.set_label(label, fontsize = 15)
        self.cax_2.set_label(label, fontsize = 15)
        #self.cax_3.set_label(label)
        self.cmap = plt.get_cmap(self.color_pallete_comboBox.currentText())
        self.sm.set_cmap(self.cmap)
        gc.collect()

    def _update_main_figure(self):
        """_summary_
        """        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.plot_data = self.monitor.data_frame[self.temp_mask].reset_index(drop=True) if self.temp_mask_signal else self.monitor.data_frame
        except (AttributeError, pd.errors.IndexingError, ValueError):
            self.plot_data = self.monitor.data_frame
            pass

        if self.plot_with_temp:
            norm_col = 'temp'
            self.update_colormap('temp', 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)')
            self.min_temp_doubleSpinBox.setRange(min(self.monitor.data_frame['temp']), max(self.monitor.data_frame['temp']))
            self.max_temp_doubleSpinBox.setRange(min(self.monitor.data_frame['temp']), max(self.monitor.data_frame['temp']))
            self.min_temp_doubleSpinBox.setValue(min(self.plot_data['temp']))
            self.max_temp_doubleSpinBox.setValue(max(self.plot_data['temp']))
        else:
            norm_col = 'file_index'
            self.update_colormap('file_index', 'XRD acquisition time')
            self.min_temp_doubleSpinBox.setRange(min(self.monitor.data_frame['file_index']), max(self.monitor.data_frame['file_index']))
            self.max_temp_doubleSpinBox.setRange(min(self.monitor.data_frame['file_index']), max(self.monitor.data_frame['file_index']))
            self.min_temp_doubleSpinBox.setValue(min(self.plot_data['file_index']))
            self.max_temp_doubleSpinBox.setValue(max(self.plot_data['file_index']))
        
        self.spacing = max(self.plot_data['max']) / (100 - self.offset_slider.value())
        
        offset = 0
        mask = self._get_mask(0)
        for i in range(len(self.plot_data['file_name'])):
            color = self.cmap(self.norm(self.plot_data[norm_col][i])) #Selecting the pattern's color based on the colormap
            dois_theta, intensity = self.read_data(self.plot_data['file_name'][i], normalize=False)
            self.ax_main.plot(dois_theta[mask], intensity[mask] + offset, color=color, label=f'XRD pattern #{self.plot_data["file_index"][i]} - Temperature {self.plot_data["temp"][i]} K' 
                                                                                                                        if self.monitor.kelvin_sginal else f'XRD pattern #{self.plot_data["file_index"][i]} - Temperature {self.plot_data["temp"][i]} °C' 
                                                                                                                                    if self.plot_with_temp else f'XRD pattern #{self.plot_data["file_index"][i]}')
            offset += self.spacing
            del dois_theta, intensity

            self.ax_main.set_xlabel('2θ (°)', fontsize = 15)
            self.ax_main.set_ylabel('Intensity (a.u.)', fontsize = 15)
        QApplication.restoreOverrideCursor()
        gc.collect()

    def _plot_fitting_parameters(self):
        """_summary_
        """
        if not self.fit_interval:
            return

        self.ax_2theta.clear()
        self.ax_area.clear()
        self.ax_FWHM.clear()

    
        if self.fit_interval_window.fit_model == 'PseudoVoigt':
            self._plot_single_peak()
        else:
            self._plot_double_peak()

    
        avxspan = self.ax_main.axvspan(self.fit_interval[0], self.fit_interval[1], color='grey', alpha=0.5, label='Selected Fitting Interval')
        self.ax_main.legend(handles=[avxspan], loc='upper right')
       
       # self.canvas_sub.draw()
       # gc.collect()

        
       # self.cax_2.update_normal(self.sm)
        
    def _plot_single_peak(self):
        """_summary_
        """        
        
        mask = self.temp_mask if self.temp_mask_signal else slice(None)
        x_data_type = 'temp' if self.plot_with_temp else 'file_index'
        x_label = 'XRD measure' if not self.plot_with_temp else 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)'
        try:
            
            self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['dois_theta_0'].values[mask], 'Peak position (°)', x_label)#, yerr=self.monitor.fit_data['dois_theta_0_stderr'].values)
            self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['area'].values[mask], 'Peak integrated area', x_label)#, yerr=self.monitor.fit_data['area_stderr'].values)
            self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['fwhm'].values[mask], 'FWHM (°)', x_label)#, yerr=self.monitor.fit_data['fwhm_stderr'].values)
        
        except IndexError:
            
            self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['dois_theta_0'].values, 'Peak position (°)', x_label)#, yerr=self.monitor.fit_data['dois_theta_0_stderr'].values)
            self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['area'].values, 'Peak integrated area', x_label)#, yerr=self.monitor.fit_data['area_stderr'].values)
            self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['fwhm'].values, 'FWHM (°)', x_label)#, yerr=self.monitor.fit_data['fwhm_stderr'].values)

        
    def _plot_double_peak(self):
        """_summary_
        """        
        
        mask = self.temp_mask if self.temp_mask_signal else slice(None)
        x_data_type = 'temp' if self.plot_with_temp else 'file_index'
        x_label = 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)' if self.plot_with_temp else 'XRD measure'
        
        try:
            
            self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['dois_theta_0'].values[mask], 'Peak position (°)', x_label, label=True, color='red')
            self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['dois_theta_0_#2'].values[mask], 'Peak position (°)', x_label, label=True, color='red', marker='x')

            self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['area'].values[mask], 'Peak integrated area', x_label, label=True, color='green')
            self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['area_#2'].values[mask], 'Peak integrated area', x_label, label=True, color='green', marker='x')

            self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['fwhm'].values[mask], 'FWHM (°)', x_label, label = True, color='blue')
            self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type].values[mask], self.monitor.fit_data['fwhm_#2'].values[mask], 'FWHM (°)', x_label, label = True, color='blue', marker='x')
       
        except IndexError:
            
            self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['dois_theta_0'].values, 'Peak position (°)', x_label, label=True, color='red')
            self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['dois_theta_0_#2'].values, 'Peak position (°)', x_label, label=True, color='red', marker='x')

            self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['area'].values, 'Peak integrated area', x_label, label=True, color='green')
            self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['area_#2'].values, 'Peak integrated area', x_label, label=True, color='green', marker='x')

            self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['fwhm'].values, 'FWHM (°)', x_label, label = True, color='blue')
            self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type].values, self.monitor.fit_data['fwhm_#2'].values, 'FWHM (°)', x_label, label = True, color='blue', marker='x')

    def _plot_parameter(self, ax, x, y, ylabel, xlabel, label=None, color=None, marker='o', yerr = None):
        """_summary_

        Args:
            ax (_type_): _description_
            x (_type_): _description_
            y (_type_): _description_
            ylabel (_type_): _description_
            xlabel (_type_): _description_
            label (_type_, optional): _description_. Defaults to None.
            color (_type_, optional): _description_. Defaults to None.
            marker (str, optional): _description_. Defaults to 'o'.
            yerr (_type_, optional): _description_. Defaults to None.
        """
        
        for i in range(len(x)):
            norm_col = 'temp' if self.plot_with_temp else 'file_index'
            color = self.cmap(self.norm(x[i]))
            ax.plot(x[i], y[i], marker = marker, color = color)
            #ax.errorbar(x[i], y[i], ystderr, marker =marker, color = color, capsize=2)
        ax.set_xlabel(xlabel, fontsize = 15)
        ax.set_ylabel(ylabel, fontsize = 15)
        if label:
            peak1 = Line2D([0], [0], color='black', marker='o', markersize=5, linestyle="", label='PseudoVoigt #1')
            peak2 = Line2D([0], [0], color='black', marker='x', markersize=5, linestyle="", label='PseudoVoigt #2')
            ax.legend(handles = [peak1, peak2])

    def select_folder(self):
        """_summary_
        """        
        folder_path = QFileDialog.getExistingDirectory(self, 'Select the data folder to monitor', '', options=QFileDialog.Options()) # Selection of monitoring folder
        if folder_path == "":
            return
        if self.folder_selected:
            self.monitor.data_frame = pd.DataFrame(columns=['file_name', 'temp', 'max', 'file_index'])
            self.monitor.fit_data = pd.DataFrame(columns=['dois_theta_0', 'fwhm', 'area', 'temp', 'file_index', 'R-squared'])
            #self.monitor = None
            self.plot_data = None
            print(self.monitor.data_frame, self.monitor.fit_data, self.plot_data)
            gc.collect()
        counter.count = 0
        self.plot_with_temp = False
        self.selected_interval = None
        self.fit_interval = None
        
        self.folder_selected = False
        self.temp_mask_signal = False
        #folder_path = QFileDialog.getExistingDirectory(self, 'Select the data folder to monitor', '', options=QFileDialog.Options()) # Selection of monitoring folder
        if folder_path:
            self.folder_selected = True
            self.ax_main.clear()
            self.ax_contour.clear()
            self.ax_2theta.clear()
            self.ax_area.clear()
            self.ax_FWHM.clear()
            self.canvas_main.draw()
            self.monitor = FolderMonitor(folder_path=folder_path)
            self.monitor.new_data_signal.connect(self.handle_new_data)
            self.monitor.start()
            gc.collect()

        else:
            print('No folder selected. Exiting')
            

    def handle_new_data(self, new_data):
        """_summary_

        Args:
            new_data (_type_): _description_
        """        
        self.plot_data = pd.concat([self.plot_data, new_data], ignore_index=True)
        
    def onselect(self, xmin, xmax):
        """_summary_

        Args:
            xmin (_type_): _description_
            xmax (_type_): _description_
        """        
        self.selected_interval = (xmin, xmax)
        #print(f'Selected Interval: {self.selected_interval}')
        self.update_graphs()
    # Reset button function #     
    def reset_interval(self):
        """_summary_
        """        
        self.selected_interval = None
        self.update_graphs()
    # Peak fit interval selection routine # 
    def select_fit_interval(self):
        """_summary_
        """        
        if not self.folder_selected:
            QMessageBox.warning(self, '','Please initialize the monitor!')
            pass
        else: 
            try:
                if len(self.plot_data['file_name']) == 0:
                    print('No data available. Wait for the first measure!')
                else:
                    self.ax_2theta.clear()
                    self.ax_area.clear()
                    self.ax_FWHM.clear()
                    self.fit_interval=None
                    self.monitor.fit_data = self.monitor.fit_data.iloc[0:0] #Reset fitting data
                    self.fit_interval_window = FitWindow()
                    self.fit_interval_window.show()
            except AttributeError as e:
                print(f'Please, push the Refresh Button! Error: {e}')
                QMessageBox.warning(self, '','Please, push the Refresh Button!') 
            except Exception as e:
                print(f'Error: {e}')
    

    def export_figure(self):
        """_summary_
        """        
        tab_dict = {0: self.fig_main, 1: self.fig_sub, 2: self.fig_contour, 3: self.fig_norm}
        cur_index = self.tabWidget.currentIndex()
        self.export_window = ExportWindow(tab_dict[cur_index])
        self.export_window.show()
        gc.collect()

    def on_mouse_move(self, event):
        """_summary_

        Args:
            event (_type_): _description_
        """        
        self.canvas_main.mouse_event = event
        x, y = event.xdata, event.ydata
        label = None
        try:
            min_dist = self.spacing #float('inf')
        except AttributeError or UnboundLocalError:
            pass
        
        if x is not None and y is not None:
            # Iterate over all lines in the plot, fiding the closest line point to the mouse. 
            for line in self.canvas_main.figure.axes[0].get_lines():
                x_data, y_data = line.get_xdata(), line.get_ydata()
                if len(x_data) > 0:
                   #Find the closest point to the mouse on the line
                    idx = np.argmin(np.sqrt((x_data - x) ** 2 + (y_data - y) ** 2))
                    dist = np.sqrt((x_data[idx] - x) ** 2 + (y_data[idx] - y) ** 2)
                    #print(f'Distance: {dist}', f'X_curve: {x_data[idx]}', f'Y_Curve: {y_data[idx]}', f'X_mouse: {x}', f'Y_mouse: {y}')
                    try:
                        if dist < min_dist:
                            min_dist = dist 
                            label = line.get_label()
                    except UnboundLocalError:
                        pass
        #print(f'Distance: {dist}', f'X_curve: {x_data[idx]}', f'Y_Curve: {y_data[idx]}', f'X_mouse: {x}', f'Y_mouse: {y}', f'Cruve label: {label}')
                            
        #print(label)
        if label is not None and x is not None and y is not None:
            s = f"Label: {label} | 2theta={x:.2f}, Intensity={y:.2e}"
            self.toolbar.set_message(s)
        else:
            try:
                s = f"2theta={x:.2f}, Intensity={y:.2e}"
                self.toolbar.set_message(s)
            except TypeError:
                self.toolbar.set_message("")
        
    def save_data_frame(self):
        """_summary_
        """        
        try:
            options = QFileDialog.Options()

        # Select appropriate DataFrame generator based on model and temperature
            if self.fit_interval_window.fit_model == 'PseudoVoigt':
                df = self._create_single_peak_dataframe()
            else:
                df = self._create_double_peak_dataframe()

            if df is not None:
                file_path, _ = QFileDialog.getSaveFileName(self, "Save fitting Data", "", "CSV (*.csv);;All Files (*)", options=options)
                if file_path:
                    df.to_csv(file_path, index=False)
        except AttributeError as e:
            print(f"No data available! Please, initialize the monitor! Error: {e}")
            QMessageBox.warning(self, '','Please initialize the monitor!')
        except Exception as e:
            print(f'Exception {e} encountered')

    def _create_single_peak_dataframe(self):
        """_summary_

        Returns:
            _type_: _description_
        """        
        if self.plot_with_temp:
            temp_label = 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)'
            return pd.DataFrame({
            temp_label: self.monitor.fit_data['temp'],
            'Peak position (degree)': self.monitor.fit_data['dois_theta_0'],
            'Peak Integrated Area': self.monitor.fit_data['area'],
            'FWHM (degree)': self.monitor.fit_data['fwhm'],
            'R-squared (R²)': self.monitor.fit_data['R-squared']
        })
        else:
            return pd.DataFrame({
            'Measure': self.monitor.fit_data['file_index'],
            'Peak position (degree)': self.monitor.fit_data['dois_theta_0'],
            'Peak Integrated Area': self.monitor.fit_data['area'],
            'FWHM (degree)': self.monitor.fit_data['fwhm'],
            'R-squared (R²)': self.monitor.fit_data['R-squared']
        })

    def _create_double_peak_dataframe(self):
        """_summary_

        Returns:
            _type_: _description_
        """        
        if self.plot_with_temp:
            temp_label = 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)'
            return pd.DataFrame({
            temp_label: self.monitor.fit_data['temp'],
            'Peak position #1 (degree)': self.monitor.fit_data['dois_theta_0'],
            'Peak Integrated Area #1': self.monitor.fit_data['area'],
            'FWHM (degree) #1': self.monitor.fit_data['fwhm'],
            'Peak Position #2 (degree)': self.monitor.fit_data['dois_theta_0_#2'],
            'Peak Integrated Area #2': self.monitor.fit_data['area_#2'],
            'FWHM #2 (degree)': self.monitor.fit_data['fwhm_#2'],
            'R-squared (R²)': self.monitor.fit_data['R-squared']
        })
        else:
            return pd.DataFrame({
            'Measure': self.monitor.fit_data['file_index'],
            'Peak position #1 (degree)': self.monitor.fit_data['dois_theta_0'],
            'Peak Integrated Area #1': self.monitor.fit_data['area'],
            'FWHM (degree) #1': self.monitor.fit_data['fwhm'],
            'Peak Position #2 (degree)': self.monitor.fit_data['dois_theta_0_#2'],
            'Peak Integrated Area #2': self.monitor.fit_data['area_#2'],
            'FWHM #2 (degree)': self.monitor.fit_data['fwhm_#2'],
            'R-squared (R²)': self.monitor.fit_data['R-squared']
        })

    def validate_temp(self, min_value, max_value):
        """_summary_

        Args:
            min_value (_type_): _description_
            max_value (_type_): _description_

        Returns:
            _type_: _description_
        """        
        min_temp = min(self.monitor.data_frame['temp'], key=lambda x: abs(x-min_value))
        max_temp = min(self.monitor.data_frame['temp'], key=lambda x: abs(x-max_value))
        return min_temp, max_temp
    
    def apply_temp_mask(self, mask):
        """_summary_

        Args:
            mask (_type_): _description_
        """        
        def a():
            try:
                if self.plot_with_temp:
                    min_temp, max_temp = self.validate_temp(self.min_temp_doubleSpinBox.value(), self.max_temp_doubleSpinBox.value())
                    self.temp_mask = (self.monitor.data_frame['temp'] >= min_temp) & (self.monitor.data_frame['temp'] <= max_temp)
                else:
                    self.temp_mask = (self.monitor.data_frame['file_index'] >= self.min_temp_doubleSpinBox.value()) & (self.monitor.data_frame['file_index'] <= self.max_temp_doubleSpinBox.value())
                self.temp_mask_signal = True
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.ax_main.clear()
                self._update_main_figure()
                QApplication.restoreOverrideCursor()
                self.canvas_main.draw()
                
            except AttributeError as e:
                print(f"No data available! Please, initialize the monitor! Error: {e}")
                QMessageBox.warning(self, '','Please initialize the monitor!')
            except Exception as e:
                print(f'Exception {e} encountered')
        self.temp_mask = np.array(mask)
        
        
        self.temp_mask_signal = True
        #QApplication.setOverrideCursor(Qt.WaitCursor)
        self.ax_main.clear()
        self.update_graphs()
        #QApplication.restoreOverrideCursor()
        self.canvas_main.draw()

    def measure_order_index(self, checked):
        """_summary_

        Args:
            checked (_type_): _description_
        """        
        if checked:
            self.temperature_checkbox.setCheckState(False)
            self.plot_with_temp = False
            self.min_filter_label.setText('<u>Minimum:</u>')
            self.max_filter_label.setText('<u>Maximum:</u>')
            self.update_graphs()
        else:
            self.temperature_checkbox.setCheckable(True)

    def temp_index(self, checked):
        """_summary_

        Args:
            checked (_type_): _description_
        """        
        try:
            if checked:

                if self.monitor.data_frame['temp'][0] != None:
                    self.XRD_measure_order_checkbox.setCheckState(False)
                    self.plot_with_temp = True
                    self.min_filter_label.setText('<u>Minimum Temperature:</u>')
                    self.max_filter_label.setText('<u>Maximum Temperature:</u>')
                    self.update_graphs()
                else:
                    print("This experiment doesn't make use of temperature!")
                    self.temperature_checkbox.setCheckState(False)
            else:
                pass
                    
        except AttributeError as e:
            self.temperature_checkbox.setCheckState(False)
            print(f'Please initizalie the Monitor! Error {e}')
            QMessageBox.warning(self, '','Please initialize the monitor!')     
    
    def read_data(self, path, normalize = False):
        """_summary_

        Args:
            path (_type_): _description_
            normalize (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """        
        data = pd.read_csv(path, sep = ',', header=0, comment="#")
        theta = np.array(data.iloc[:, 0])
        intensity = np.array(data.iloc[:, 1])
        if normalize:
            return theta, normalize_array(intensity)
        return theta, intensity
    
    def normalize(self):
        """_summary_
        """        
        try:
            self.ax_norm.clear()
            mask = self._get_mask(0)
            offset = 0
            spacing = 1 / (100 - self.norm_offset_slider.value())
            for i in range(len(self.plot_data['file_name'])):
                norm_col = 'temp' if self.plot_with_temp else 'file_index' #Flag for chosing the XRD pattern index
                color = self.cmap(self.norm(self.plot_data[norm_col][i])) #Selecting the pattern's color based on the colormap
                dois_theta, intensity = self.read_data(self.plot_data['file_name'][i], normalize=True)
                self.ax_norm.plot(dois_theta[mask], intensity[mask] + offset, color=color, label=f'XRD pattern #{self.plot_data["file_index"][i]} - Temperature {self.plot_data["temp"][i]} K'                                                                                                                  if self.plot_with_temp else f'XRD pattern #{self.plot_data["file_index"][i]}')
                offset += spacing
                del dois_theta, intensity
            
            if self.plot_with_temp:
                self.update_colormap('temp', 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)')
                self.cax_4.set_label("Temperature (K)" if self.monitor.kelvin_sginal else "Temperature (°C)", fontsize = 15)
            else:
                self.update_colormap('file_index', 'XRD acquisition time')
                self.cax_4.set_label("XRD Acquistion time", fontsize=15)
            
            self.ax_norm.set_xlabel('2θ (°)', fontsize = 15)
            self.ax_norm.set_ylabel('Normalized Intensity (a.u.)', fontsize = 15)
            self.canvas_norm.draw()
            gc.collect()
            return
        except KeyError or Exception as e:
            QMessageBox.warning(self, "", "Please, select a folder!")
            print(f"Error: {e}")
    
    def contour(self):
        """_summary_
        """        
        try:
            self.ax_contour.clear()
            theta, intensity = self.read_data(self.plot_data['file_name'][0])
            if self.plot_with_temp:
                y = np.array(self.plot_data['temp'], dtype="float64")
                self.ax_contour.set_ylabel("Temperature (°C)", fontsize = 15)
            else:
                y = np.array(self.plot_data['file_index'], dtype="float64")
                self.ax_contour.set_ylabel("Acquisition time", fontsize = 15)
            mask = self._get_mask(0)
            X, Y = np.meshgrid(theta[mask], y)
            z = []
            for item in self.plot_data['file_name']:
                intensity = np.array(self.read_data(item)[1][mask]) 
                z.append(intensity)
            z = np.array(z)

            #print(f'Shape X and Y: {np.shape(X)}, {np.shape(Y)}. Z shape: {np.shape(z)}')
            norm = self.norms[self.norm_comboBox.currentText()]
            colormesh = self.ax_contour.pcolormesh(X, Y, z, cmap = self.color_pallete_comboBox.currentText(), norm = norm, shading='auto')
            self.cax_3.update_normal(colormesh)
            self.cax_3.set_label("Intensity (a.u.)", fontsize = 15)
            self.ax_contour.set_xlabel("2θ (°)", fontsize = 15)
            self.canvas_contour.draw()
            del X, Y, mask, z
            gc.collect()
            return
        except KeyError or Exception as e:
            QMessageBox.warning(self, "", "Please, select a folder!")
            print(f"Error: {e}")
    
    def on_change_color_pallete(self, index):
        """_summary_

        Args:
            index (_type_): _description_
        """        
        self.color_pallete_comboBox.setCurrentIndex(index)
        self.color_pallete_comboBox_2.setCurrentIndex(index)
        self.update_graphs()

    def apply_filter(self):
        """_summary_
        """        
        try:
            self.filter_window = FilterWindow(self.monitor.data_frame.iloc[:, 0:3], self.monitor.kelvin_sginal)
            self.filter_window.mask.connect(self.apply_temp_mask)
            self.filter_window.show()
        except AttributeError or Exception:
            QMessageBox.warning(self, "No folder was selected", "Select a folder to monitor!")

    def on_change_vline_checkbox(self):
        """_summary_
        """        
        
        if self.cursor == None:
            self.cursor = Cursor(self.ax_main, useblit=True, color='red', linewidth=1, horizOn=False)
        else:
            self.cursor = None
    
    def about(self):
        """_summary_
        """        
        QMessageBox.about(
            self,
            "About Iguape",
            "<p>This is the Paineira Graphical User Interface</p>"
            "<p>- Its usage is resttricted to data acquired via in-situ experiments at Paineira. The software is under the GNU GPL-3.0 License.</p>"
            "<p>- There's a brief tutorial for first time users, which can be helpful, altough the program's operation is very simple"
            "<p>- Paineira Beamline</p>"
            "<p>- LNLS - CNPEM</p>",
        )

class GarbageCollector(QThread):
    """_summary_

    Args:
        QThread (_type_): _description_
    """    
    def __init__(self):
        """_summary_
        """        
        super().__init__()
        
    def run(self):
        """_summary_
        """        
        while True:
            gc.collect()
            time.sleep(10)

class Worker(QThread):
    """_summary_

    Args:
        QThread (_type_): _description_
    """    
    progress = pyqtSignal(int)
    finished = pyqtSignal(float) 
    error = pyqtSignal(str) # Changed to emit multiple arrays

    def __init__(self, interval):
        """_summary_

        Args:
            interval (_type_): _description_
        """    
        super().__init__()
        self.fit_interval = interval
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def run(self):
        """_summary_
        """        
        
        try:
            start = time.time()
            pars = None
            for i in range(len(win.plot_data['file_name'])):
                if win.fit_interval_window.fit_model == 'PseudoVoigt':
                    theta, intensity = win.read_data(win.plot_data['file_name'][i])
                    fit = peak_fit(theta, intensity, self.fit_interval, pars)
                    new_fit_data = pd.DataFrame({'dois_theta_0': [fit[0]], 'fwhm': [fit[1]], 'area': [fit[2]], 'temp': [win.plot_data['temp'][i]], 'file_index': [win.plot_data['file_index'][i]], 'R-squared': [fit[3]]})
                    win.monitor.fit_data = pd.concat([win.monitor.fit_data, new_fit_data], ignore_index=True)
                    #pars = fit[7]
                    progress_value = int((i + 1) / len(win.plot_data['file_name']) * 100)
                    self.progress.emit(progress_value)  # Emit progress signal with percentage
                else:
                    theta, intensity = win.read_data(win.plot_data['file_name'][i])
                    fit = peak_fit_split_gaussian(theta, intensity, self.fit_interval, height = win.fit_interval_window.height, distance=win.fit_interval_window.distance, pars=pars)
                    new_fit_data = pd.DataFrame({'dois_theta_0': [fit[0][0]], 'dois_theta_0_#2': [fit[0][1]], 'fwhm': [fit[1][0]], 'fwhm_#2': [fit[1][1]], 'area': [fit[2][0]], 'area_#2': [fit[2][1]], 'temp': [win.plot_data['temp'][i]], 'file_index': [win.plot_data['file_index'][i]], 'R-squared': [fit[3]]})
                    win.monitor.fit_data =pd.concat([win.monitor.fit_data, new_fit_data], ignore_index=True)
                    pars = fit[7]
                    progress_value = int((i + 1) / len(win.plot_data['file_name']) * 100)
                    self.progress.emit(progress_value)  # Emit progress signal with percentage
            #self.finished.emit(win.monitor.fit_data['dois_theta_0'], win.monitor.fit_data['area'], win.monitor.fit_data['fwhm'])  # Emit finished signal with results
            finish = time.time()
            self.finished.emit(finish-start)

        except Exception as e:
            self.error.emit(f'Error during peak fitting: {str(e)}. Please select a new Fit Interval')
            print(f'Exception {e}. Please select a new Fit Interval')

class FilterWindow(QDialog, Ui_Filter_Dialog):
    """_summary_

    Args:
        QDialog (_type_): _description_
        Ui_Filter_Dialog (_type_): _description_
    """    
    mask = pyqtSignal(list)
    def __init__(self, data = None, kelvin_signal = None, parent = None):
        """_summary_

        Args:
            data (_type_, optional): _description_. Defaults to None.
            kelvin_signal (_type_, optional): _description_. Defaults to None.
            parent (_type_, optional): _description_. Defaults to None.
        """        
        super().__init__(parent)
        self.setupUi(self)
        
        if kelvin_signal:
            self.unit = 'K'
        else:
            self.unit = "°C"
        self.data = data
        self.setup_df()
        self.list = QListView(self)
        self.model = CustomListViewModel(self.data, self.unit)
        self.list.setModel(self.model)
        self.list.setSelectionMode(QListView.ExtendedSelection)
        self.verticalLayout.addWidget(self.list)
        self.apply_button.clicked.connect(self.apply)
        self.select_all_button.clicked.connect(self.set_state_checked)
        self.deselect_all_button.clicked.connect(self.set_state_unchecked)
        self.toggle_selected_button.clicked.connect(self.set_state_selected)
        
        
        
    def setup_df(self):
        """_summary_
        """        
        checked = np.full_like(np.array(self.data.iloc[:, 0]), False)
        self.data['checked'] = checked
        return
    
    def set_state_checked(self):
        """_summary_
        """        
        for row in range(self.model.rowCount()):
            index = self.model.index(row)
            self.model.setData(index, Qt.Checked, role=Qt.CheckStateRole)
    
    def set_state_unchecked(self):
        """_summary_
        """        
        for row in range(self.model.rowCount()):
            index = self.model.index(row)
            self.model.setData(index, Qt.Unchecked, role=Qt.CheckStateRole)
    
    def set_state_selected(self):
        """_summary_
        """        
        selected = self.list.selectedIndexes()
        for index in selected:
            self.model.setData(index, Qt.Checked, role=Qt.CheckStateRole)


    def apply(self):
        """_summary_
        """        
        if True in list(self.model._data.iloc[:, -1]):
            self.mask.emit(list(self.model._data.iloc[:, -1]))
            self.close()
        else:
            QMessageBox.warning(win, "No data was selected", "Please, select at least one XRD diffractogram!")
            return


class CustomListViewModel(QAbstractListModel):
    """_summary_

    Args:
        QAbstractListModel (_type_): _description_
    """    
    def __init__(self, data = None, unit = None):
        """_summary_

        Args:
            data (_type_, optional): _description_. Defaults to None.
            unit (_type_, optional): _description_. Defaults to None.
        """        
        super().__init__()
        self._data = data.copy()
        self.unit = unit

    def rowCount(self, parent=QModelIndex()):
        """_summary_

        Args:
            parent (_type_, optional): _description_. Defaults to QModelIndex().

        Returns:
            _type_: _description_
        """        
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        """_summary_

        Args:
            index (_type_): _description_
            role (_type_, optional): _description_. Defaults to Qt.DisplayRole.

        Returns:
            _type_: _description_
        """        
        if not index.isValid():
            return QVariant()

        row = index.row()
        if role == Qt.DisplayRole:
            entry = f"{self._data.at[row, 'file_name'].split('/')[-1]} | {self._data.at[row, 'temp']} {self.unit} |XRD Acquisition # {self._data.at[row, 'file_index']}"
            return entry
        elif role == Qt.CheckStateRole:
            return Qt.Checked if self._data.at[row, 'checked'] else Qt.Unchecked
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        """_summary_

        Args:
            index (_type_): _description_
            value (_type_): _description_
            role (_type_, optional): _description_. Defaults to Qt.EditRole.

        Returns:
            _type_: _description_
        """        
        if not index.isValid():
            return False

        row = index.row()
        if role == Qt.CheckStateRole:
            self._data.at[row, 'checked'] = (value == Qt.Checked)
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable



class ExportWindow(QDialog, Ui_Export_Figure):
    """_summary_

    Args:
        QDialog (_type_): _description_
        Ui_Export_Figure (_type_): _description_
    """    
    def __init__(self, figure, parent=None):
        """_summary_

        Args:
            figure (_type_): _description_
            parent (_type_, optional): _description_. Defaults to None.
        """        
        super().__init__(parent)
        self.setupUi(self)
        self.edit_fig = copy.deepcopy(figure)
        #geometry = QGuiApplication.screens()[-1].availableGeometry()
        #self.setGeometry(geometry)
        #self.setBaseSize(self.w, self.h)
        self.edit_fig.set_layout_engine('constrained')
        self.axes = self.edit_fig.axes
        if len(self.edit_fig.axes) > 2:
            self.xlabel_lineEdit.setEnabled(False)
            self.ylabel_lineEdit.setEnabled(False)
            self.cmap_label_lineEdit.setEnabled(False)
        self.cmap_ax = self.axes[-1]
        self.axes.pop()

        self.canvas = FigureCanvas(self.edit_fig)
        
        self.xlabel_lineEdit.setText('2θ (°)')
        self.ylabel_lineEdit.setText("Intensity (a.u.)")
        self.cmap_label_lineEdit.setText(self.cmap_ax.get_ylabel())
        self.dpi_spinBox.setValue(self.edit_fig.dpi)
        self.font_comboBox.addItems(fonts_list)
        self.verticalLayout.addWidget(self.canvas)
        self.redraw_button.clicked.connect(self.redraw_fig)
        self.font_comboBox.currentTextChanged.connect(self.on_change_font_comboBox)
        self.label_size_spinBox.valueChanged.connect(self.on_change_label_size_spinBox)
        self.label_style_comboBox.currentTextChanged.connect(self.on_change_label_style_comboBox)
        self.ticks_size_spinBox.valueChanged.connect(self.on_change_tick_size_spinBox)
        self.ticks_style_comboBox.currentTextChanged.connect(self.on_change_tick_style_comboBox)
        self.save_fig_button.clicked.connect(self.save_fig)
        self.color_pallete.clicked.connect(self.get_color)
        self.color_pallete.setFixedSize(QSize(22,22))
        #self.setGeometry(QRect(0, 0, 500,  500))
        self.height = None
        self.width = None
        self.label_font = {'family': self.font_comboBox.currentText(),
                     'color':  'black',
                     'weight': 'normal',
                     'size': self.label_size_spinBox.value(),
                     'style': 'normal',
                    }
        self.tick_font = {'family': self.font_comboBox.currentText(),
                     'color':  'black',
                     'weight': 'normal',
                     'size': self.ticks_size_spinBox.value(),
                     'style': 'normal',
                    }
    def get_color(self):
        """_summary_
        """        
        color = QColorDialog().getColor()
        if color.isValid():
            self.label_font['color'] = color.name()
            self.color_pallete.setStyleSheet("background-color: %s;" % color.name())
        return
    
    
    def on_change_font_comboBox(self, font):
        """_summary_

        Args:
            font (_type_): _description_
        """        
        self.label_font['family'] = font
        self.tick_font['family'] = font
        return
    
    def on_change_label_size_spinBox(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """        
        self.label_font['size'] = value
        return

    def on_change_tick_size_spinBox(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """        
        self.tick_font['size'] = value
        return

    def on_change_label_style_comboBox(self, style):
        """_summary_

        Args:
            style (_type_): _description_
        """        
        if style == 'bold':
            self.label_font['weight'] = style
            return
        self.label_font['style'] = style
        return

    def on_change_tick_style_comboBox(self, style):
        """_summary_

        Args:
            style (_type_): _description_
        """        
        if style == 'bold':
            self.tick_font['weight'] = style
            return
        self.tick_font['style'] = style
        return
    

    def redraw_fig(self):
        """_summary_
        """        
        
        try:
            self.height = self.height_doubleSpinBox.value()
            self.width = self.width_doubleSpinBox.value()
        except Exception as e:
            print('{e}')
            return
        tickfont = matplotlib.font_manager.FontProperties(family=self.tick_font['family'],
                                                          style=self.tick_font['style'],
                                                          weight=self.tick_font['weight'],
                                                          size=self.tick_font['size'])
        for ax in self.axes:
            ax.set_xlabel(self.xlabel_lineEdit.text(), fontdict = self.label_font)
            ax.set_ylabel(self.ylabel_lineEdit.text(), fontdict = self.label_font)
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(tickfont)
        
            

        self.cmap_ax.set_ylabel(self.cmap_label_lineEdit.text(), fontdict = self.label_font)
        for label in self.cmap_ax.get_yticklabels():
            label.set_fontproperties(tickfont)
        
        self.edit_fig.set_size_inches(self.width, self.height)
        #self.canvas.resize(int(width*self.edit_fig.dpi), int(height*self.edit_fig.dpi))
        #self.setGeometry(0, 0, int(width*self.edit_fig.dpi), int(height*self.edit_fig.dpi))
        
        

        
        self.canvas.draw()

        gc.collect()
        return
    
    def save_fig(self):
        """_summary_
        """        
        path = QFileDialog.getSaveFileName(self, "Select Save Path", os.path.expanduser('~'), options=QFileDialog.Options())[0]
        if path == "":
            QMessageBox.warning(self, 'Saving Error', "Please, select a valid path for your Figure")
            return
        print(path)
        #self.canvas.resize(int(width*self.edit_fig.dpi), int(height*self.edit_fig.dpi))
        self.edit_fig.set_size_inches(self.width, self.height)
        self.edit_fig.savefig(path+f".{self.format_comboBox.currentText()}", dpi = self.dpi_spinBox.value(),
                         format = self.format_comboBox.currentText(),
                         bbox_inches = 'tight')
        


            

class FitWindow(QDialog, Ui_pk_window):
    """_summary_

    Args:
        QDialog (_type_): _description_
        Ui_pk_window (_type_): _description_
    """    
    def __init__(self, parent=None):
        """_summary_

        Args:
            parent (_type_, optional): _description_. Defaults to None.
        """        
        
        super().__init__(parent)
        self.setupUi(self)
        self.fit_interval= None
        self.text = None
        self.fit_model = 'PseudoVoigt'
        win.monitor.set_fit_model = "PseudoVoigt"
        self.distance = 25
        self.height = 1e+09
        self.prominence = 50
        self.setup_layout()

    def setup_layout(self):
        """_summary_
        """        
        self.setWindowTitle('Peak Fit')
        self.pk_layout = QVBoxLayout()
        self.fig = Figure(figsize=(20,10), dpi=100)
        self.ax = self.fig.add_subplot(1,1,1)
        theta, intensity = win.read_data(win.plot_data['file_name'][0])
        if win.plot_with_temp:
            #theta, intensity = win.read_data(win.plot_data['file_name'][0])
            self.ax.plot(theta, intensity,'o', markersize=3, label = 'XRD pattern ' + str(win.plot_data['temp'][0]) + '°C')
            #self.ax.plot(win.plot_data['theta'][0], win.plot_data['intensity'][0],'o', markersize=3, label = 'XRD pattern ' + str(win.plot_data['temp'][0]) + '°C')
        
        else:
            self.ax.plot(theta, intensity, 'o', markersize=3, label = 'XRD pattern #' + str(win.plot_data['file_index'][0]))
            #self.ax.plot(win.plot_data['theta'][0], win.plot_data['intensity'][0], 'o', markersize=3, label = 'XRD pattern #' + str(win.plot_data['file_index'][0]))
        self.ax.set_xlabel("2θ (°)", fontsize = 15)
        self.ax.set_ylabel("Intensity (u.a.)", fontsize = 15)
        self.ax.legend(fontsize='small')
        self.canvas = FigureCanvas(self.fig)
        self.pk_layout.addWidget(self.canvas)
        self.pk_layout.addWidget(NavigationToolbar2QT(self.canvas, self))
        self.pk_frame.setLayout(self.pk_layout)
        self.span = SpanSelector(self.ax, self.onselect, 'horizontal', useblit=True,
                                props=dict(alpha=0.3, facecolor='red', capstyle='round'))
        
        self.clear_plot_button.clicked.connect(self.clear_plot)
        self.pk_button.clicked.connect(self.fit)
        self.indexes = [0]
        self.shade = False


        if win.plot_with_temp:
            items_list = [str(item) + '°C' for item in win.plot_data['temp']]
            self.xrd_combo_box.addItems(items_list)
        else:
            items_list = [str(item) for item in win.plot_data['file_index']]
            self.xrd_combo_box.addItems(items_list)
        
        self.xrd_combo_box.activated[str].connect(self.onChanged_xrd_combo_box)
        self.pk_combo_box.activated[str].connect(self.onChanged_pk_combo_box)
        self.bgk_combo_box.activated[str].connect(self.onChanged_bkg_combo_box)
        self.preview_button.clicked.connect(self.preview)
        self.distance_spinBox.setReadOnly(True)
        self.distance_spinBox.valueChanged[int].connect(self.onChanged_distance_spinbox)
        self.height_spinBox.setReadOnly(True)
        self.height_spinBox.valueChanged[int].connect(self.onChanged_height_spinbox)
        self.prominence_spinBox.valueChanged[int].connect(self.onChanged_prominence_spinbox)

    def onChanged_xrd_combo_box(self, text):
        """_summary_

        Args:
            text (_type_): _description_
        """        

        self.text = text
        if len(self.ax.lines) == 2:
            QMessageBox.warning(self, '','Warning! It is possible to display only two XRD patterns in this window! Please press the Clear Plot button and select up to 2 XRD patterns to be displayed.')
            pass
        else:
            i = self.xrd_combo_box.currentIndex()
            self.indexes.append(i)
            theta, intensity = win.read_data(win.plot_data['file_name'][i])
            if win.plot_with_temp:
                self.ax.plot(theta, intensity, 'o', markersize=3, label = ('XRD pattern ' + text))

                #self.ax.plot(win.plot_data['theta'][i], win.plot_data['intensity'][i], 'o', markersize=3, label = ('XRD pattern ' + text))
            else:
                self.ax.plot(theta, intensity, 'o', markersize=3, label = ('XRD pattern #' + text))
                #self.ax.plot(win.plot_data['theta'][i], win.plot_data['intensity'][i], 'o', markersize=3, label = ('XRD pattern #' + text))
        
            self.ax.set_xlabel("2θ (°)", fontsize = 15)
            self.ax.set_ylabel("Intensity (u.a.)", fontsize = 15)
            self.ax.legend(fontsize='small')
            self.canvas.draw()
    
    def onChanged_pk_combo_box(self, text):
        """_summary_

        Args:
            text (_type_): _description_
        """        """
        Routine for selecting the Peak Fitting Model via the ComboBox.
        
        Parameters 
        ----------
            text (str): Text selected on the ComboBox
        """

        if text == 'PseudoVoigt Model':
            self.fit_model = 'PseudoVoigt'
            win.monitor.set_fit_model = 'PseudoVoigt'
            self.distance_spinBox.setReadOnly(True)
            self.height_spinBox.setReadOnly(True)
        elif text == 'Split PseudoVoigt Model - 2x PseudoVoigt':
            self.fit_model = '2x PseudoVoigt(SPV)'
            win.monitor.set_fit_model = '2x PseudoVoigt(SPV)'
            self.distance_spinBox.setReadOnly(False)
            self.height_spinBox.setReadOnly(False)
        else:
            self.fit_model = '2x Gaussian'
            win.monitor.set_fit_model = '2x PseudoVoigt(SPV)'
            self.distance_spinBox.setReadOnly(False)
            self.height_spinBox.setReadOnly(False)
    def onChanged_bkg_combo_box(self, text):
        """_summary_

        Args:
            text (_type_): _description_
        """        

        if text == 'Linear Model': 
            self.bkg_model = 'Linear'
        else:
            self.bkg_model = 'Spline'

    def onselect(self, xmin, xmax):
        """_summary_

        Args:
            xmin (_type_): _description_
            xmax (_type_): _description_
        """        
        if self.shade:
            self.shade.remove()
        self.fit_interval = [xmin, xmax]
        self.interval_label.setText(f'[{xmin:.3f}, {xmax:.3f}]')
        self.shade = self.ax.axvspan(self.fit_interval[0], self.fit_interval[1], color='grey', alpha=0.5, label='Selected Fitting Interval')
        self.canvas.draw()
        
    def onChanged_distance_spinbox(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """        
        self.distance = value

    def onChanged_height_spinbox(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """        
        self.height = value*(1e+09)
    
    def onChanged_prominence_spinbox(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """        
        self.prominence = value

    def clear_plot(self):
        """_summary_
        """
        self.ax.clear()
        self.canvas.draw()
        self.indexes.clear()

    def preview(self):
        """_summary_
        """        
        if len(self.ax.lines) > 2:
            while len(self.ax.lines) > 2:
                self.ax.lines[len(self.ax.lines)-1].remove()
        if self.fit_model == "PseudoVoigt":
            for i in range(len(self.indexes)):
                theta, intensity = win.read_data(win.plot_data['file_name'][self.indexes[i]])
                #data = peak_fit(win.plot_data['theta'][self.indexes[i]], win.plot_data['intensity'][self.indexes[i]], self.fit_interval)
                data = peak_fit(theta, intensity, self.fit_interval)
                best_fit = data[4].best_fit
                #dely = data[4].eval_uncertainty(sigma = 3)
                if win.plot_with_temp:
                    self.ax.plot(data[6], best_fit, '--', label = f'Best Fit - {win.plot_data["temp"][self.indexes[i]]} °C')
                    self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - {win.plot_data["temp"][self.indexes[i]]} °C')
                    #self.ax.fill_between(data[6],best_fit-dely, best_fit+dely, color='darkslategrey', alpha=0.9, label=r"3-$\sigma$ uncertainty band")
                else:
                    self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - #{win.plot_data["file_index"][self.indexes[i]]}')
                    self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - #{win.plot_data["file_index"][self.indexes[i]]}')
                    #self.ax.fill_between(data[6],best_fit-dely, best_fit+dely, color = "darkslategrey", alpha=0.9, label=r"3-$\sigma$ uncertainty band")
                self.ax.legend(fontsize='small')
                self.canvas.draw()
        else:
            for i in range(len(self.indexes)):
                try:
                    theta, intensity = win.read_data(win.plot_data['file_name'][self.indexes[i]])
                    #data = peak_fit_split_gaussian(win.plot_data['theta'][self.indexes[i]], win.plot_data['intensity'][self.indexes[i]], self.fit_interval, height = self.height, distance=self.distance)
                    data = peak_fit_split_gaussian(theta, intensity, self.fit_interval, height = self.height, distance=self.distance)
                    best_fit = data[4].best_fit
                    #dely = data[4].eval_uncertainty(sigma = 3)
                    if win.plot_with_temp:
                        self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - {win.plot_data["temp"][self.indexes[i]]} °C')
                        self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - {win.plot_data["temp"][self.indexes[i]]} °C')
                        #self.ax.fill_between(data[6],best_fit-dely, best_fit+dely, color='darkslategrey', alpha=0.9, label=r"3-$\sigma$ uncertainty band")
                    else:
                        self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - #{win.plot_data["file_index"][self.indexes[i]]}')
                        self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - #{win.plot_data["file_index"][self.indexes[i]]}')
                        #self.ax.fill_between(data[6],best_fit-dely, best_fit+dely, color='darkslategrey', alpha=0.9, label=r"3-$\sigma$ uncertainty band")
                    self.ax.legend(fontsize='small')
                    self.canvas.draw()
                except UnboundLocalError as e:
                    QMessageBox.warning(self, '', 'The value given for distance and/or height for peak search are out of bounds, i.e., it was not possible to find two peaks mtaching the given parameters! Please, try again with different values for distance and height!')
                except UnboundLocalError as e:
                    QMessageBox.warning(self, '', 'The value given for distance and/or height for peak search are out of bounds, i.e., it was not possible to find two peaks mtaching the given parameters! Please, try again with different values for distance and height!')

    def fit(self):
        """_summary_
        """        
        win.monitor.set_fit_interval(self.fit_interval)
        win.monitor.set_distance(self.distance)
        win.monitor.set_height(self.height)
        win.fit_interval = self.fit_interval
        win.fit_interval_window.close()

        self.progress_dialog = QProgressDialog("Fitting peaks...", "", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()
        self.progress_dialog.setCancelButton(None)

        # Start the worker thread for peak fitting
        self.worker = Worker(self.fit_interval)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.peak_fitting_finished)
        self.worker.error.connect(self.peak_fitting_error)
        self.worker.start()

    def update_progress(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """        

        self.progress_dialog.setValue(value)

    def peak_fitting_finished(self, time):
        """_summary_

        Args:
            time (_type_): _description_
        """        

        self.progress_dialog.setValue(100)
        QMessageBox.information(self, "Peak Fitting", f"Peak fitting completed successfully! Elapsed time: {int(time)}s")
        win.update_graphs()
        
        self.close()

    def peak_fitting_error(self, error_message):
        """_summary_

        Args:
            error_message (_type_): _description_
        """        
        self.progress_dialog.cancel()
        QMessageBox.warning(self, "Peak Fitting Error", error_message)
        self.show()

        

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
