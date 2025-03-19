#This is part of the source code for the Paineira Graphical User Interface - Iguape
#The code is distributed under the GNU GPL-3.0 License. Please refer to the main page (https://github.com/cnpem/iguape) for more information

"""
This is the main script for the excution of the Paineira Graphical User Interface, a GUI for visualization and data processing during in situ experiments at Paineira.
In this script, both GUIs used by the program are called and all of the backend functions and processes are defined. 
"""

import sys, time
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QFileDialog, QDialog, QProgressDialog, QPushButton
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.widgets import SpanSelector
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox
)
from Monitor import FolderMonitor
from GUI.iguape_GUI import Ui_MainWindow
from GUI.pk_window import Ui_pk_window
from Monitor import peak_fit, counter, peak_fit_split_gaussian
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QVBoxLayout

if getattr(sys, 'frozen', False): 
    import pyi_splash #If the program is executed as a pyinstaller executable, import pyi_splash for the Splash Screen

license  = 'GNU GPL-3.0 License'
    
counter.count = 0

class Window(QMainWindow, Ui_MainWindow):
    """ 
    Main window Class
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.create_graphs_layout()
        if getattr(sys, 'frozen', False):
            pyi_splash.close() #After the GUI initialization, close the Splash Screen

    def create_graphs_layout(self):
        """
        Routine to create the layout for the XRD and Fitting Data Graphs
        """
        self.XRD_data_layout = QVBoxLayout()
        # Creating the main Figure and Layout #
        self.fig_main = Figure(figsize=(8, 6), dpi=100)
        self.gs_main = self.fig_main.add_gridspec(1, 1)
        self.ax_main = self.fig_main.add_subplot(self.gs_main[0, 0])
        self.fig_main.set_layout_engine('compressed')
        self.canvas_main = FigureCanvas(self.fig_main)
        self.XRD_data_layout.addWidget(self.canvas_main)
        self.XRD_data_tab.setLayout(self.XRD_data_layout)
    
        self.peak_fit_layout = QVBoxLayout()
        #Creating the fitting parameter Figure and Layout#
        self.fig_sub = Figure(figsize=(8, 5), dpi=100)
        self.gs_sub = self.fig_sub.add_gridspec(1, 3)
        self.ax_2theta = self.fig_sub.add_subplot(self.gs_sub[0, 0])
        self.ax_area = self.fig_sub.add_subplot(self.gs_sub[0, 2])
        self.ax_FWHM = self.fig_sub.add_subplot(self.gs_sub[0, 1])
        self.fig_sub.set_layout_engine('compressed')
        self.canvas_sub = FigureCanvas(self.fig_sub)
        self.peak_fit_layout.addWidget(self.canvas_sub)
        self.peak_fit_tab.setLayout(self.peak_fit_layout)

        #Creating a colormap on the main canvas#
        self.cmap = plt.get_cmap('coolwarm') 
        self.norm = plt.Normalize(vmin=0, vmax=1) # Initial placeholder values for norm #
        self.sm = ScalarMappable(cmap=self.cmap, norm=self.norm)
        self.sm.set_array([])
        self.cax = self.fig_main.colorbar(self.sm, ax=self.ax_main) # Creating the colorbar axes #
        self.cax_2 = self.fig_sub.colorbar(self.sm, ax=self.ax_area) # Creating the colorbar axes #
        #Connecting functions to buttons#
        self.refresh_button.clicked.connect(self.update_graphs)
        
        self.reset_button.clicked.connect(self.reset_interval)
        
        self.peak_fit_button.clicked.connect(self.select_fit_interval)
        self.save_peak_fit_data_button.clicked.connect(self.save_data_frame)
    
        self.plot_with_temp = False
        self.selected_interval = None
        self.fit_interval = None
        
        self.folder_selected = False
        self.temp_mask_signal = False
        self.plot_data = pd.DataFrame()

        #Create span selector on the main plot#
        self.span = SpanSelector(self.ax_main, self.onselect, 'horizontal', useblit=True,
                                props=dict(alpha=0.3, facecolor='red', capstyle='round'))
        
        self.peak_fit_layout.addWidget(NavigationToolbar2QT(self.canvas_sub, self))
        self.toolbar = NavigationToolbar2QT(self.canvas_main, self)
        self.XRD_data_layout.addWidget(self.toolbar)
        self.canvas_main.mpl_connect("motion_notify_event", self.on_mouse_move)


        self.actionOpen_New_Folder.triggered.connect(self.select_folder)
        self.actionAbout.triggered.connect(self.about)
        
        

        self.offset_slider.setMinimum(1)
        self.offset_slider.setMaximum(99)
        self.offset_slider.setValue(90)

    
        self.XRD_measure_order_checkbox.stateChanged.connect(self.measure_order_index)
        self.temperature_checkbox.stateChanged.connect(self.temp_index)
        self.filter_button.clicked.connect(self.apply_temp_mask)

    def update_graphs(self):
        """
        Clears plotted axis, updates the colormap normalization and calls refreshing routines (_update_main_figure and _plot_fitting_parameters)
        """
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            self.ax_main.clear()
        
            self._update_main_figure()
            self._plot_fitting_parameters()

            self.canvas_main.draw()
            self.canvas_sub.draw()
            self.cax.update_normal(self.sm)
            self.cax_2.update_normal(self.sm)

        except Exception as e:
            print(f'Please, initialize the monitor! Error: {e}')
            QMessageBox.warning(self, '','Please initialize the monitor!') 
            pass

        QApplication.restoreOverrideCursor()
        

    def _get_mask(self, i):
        """
        Creates a mask, based on the interval selected by the user, for the i-th XRD measure.
        If no interval is selected, returns None.

        Parameters
        ----------
            i (int): Index of the XRD measure
        
        Returns
        -------
            slice: Slice object for the mask
        """
        if self.selected_interval:
            return (self.plot_data['theta'][i] >= self.selected_interval[0]) & (self.plot_data['theta'][i] <= self.selected_interval[1])
        return slice(None)

    def update_colormap(self, color_map_type, label):
            """
            Updates the colormap based on the selected color map type (temperature or XRD measure order)

            Parameters
            ----------
                color_map_type (str): Type of colormap to be used
                label (str): Label for the colorbar
            """
            self.norm.vmin, self.norm.vmax = min(self.plot_data[color_map_type]), max(self.plot_data[color_map_type])
            self.sm.set_norm(self.norm)
            self.cax.set_label(label)
            self.cax_2.set_label(label)

    def _update_main_figure(self):
        """
        Main Figure (XRD Data) refreshing routine. It plots the XRD patterns, with the customizations selected by the user (2theta mask, temperature mask, XRD index, etc.)
        """
        try:
            self.plot_data = self.monitor.data_frame[self.temp_mask].reset_index(drop=True) if self.temp_mask_signal else self.monitor.data_frame
        except (AttributeError, pd.errors.IndexingError):
            pass

        if self.plot_with_temp:
            self.update_colormap('temp', 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)')
            self.min_temp_doubleSpinBox.setRange(min(self.monitor.data_frame['temp']), max(self.monitor.data_frame['temp']))
            self.max_temp_doubleSpinBox_2.setRange(min(self.monitor.data_frame['temp']), max(self.monitor.data_frame['temp']))
            self.min_temp_doubleSpinBox.setValue(min(self.plot_data['temp']))
            self.max_temp_doubleSpinBox_2.setValue(max(self.plot_data['temp']))
        else:
            self.update_colormap('file_index', 'XRD acquisition time')
            self.min_temp_doubleSpinBox.setRange(min(self.monitor.data_frame['file_index']), max(self.monitor.data_frame['file_index']))
            self.max_temp_doubleSpinBox_2.setRange(min(self.monitor.data_frame['file_index']), max(self.monitor.data_frame['file_index']))
            self.min_temp_doubleSpinBox.setValue(min(self.plot_data['file_index']))
            self.max_temp_doubleSpinBox_2.setValue(max(self.plot_data['file_index']))
        self.spacing = max(self.plot_data['max']) / (100 - self.offset_slider.value())
        offset = 0
        for i in range(len(self.plot_data['theta'])):
            norm_col = 'temp' if self.plot_with_temp else 'file_index' #Flag for chosing the XRD pattern index
            color = self.cmap(self.norm(self.plot_data[norm_col][i])) #Selecting the pattern's color based on the colormap
            mask = self._get_mask(i)
            self.ax_main.plot(self.plot_data['theta'][i][mask], self.plot_data['intensity'][i][mask] + offset, color=color, label=f'XRD pattern #{self.plot_data["file_index"][i]} - Temperature {self.plot_data["temp"][i]} K' 
                                                                                                                                    if self.monitor.kelvin_sginal else f'XRD pattern #{self.plot_data["file_index"][i]} - Temperature {self.plot_data["temp"][i]} °C' 
                                                                                                                                    if self.plot_with_temp else f'XRD pattern #{self.plot_data["file_index"][i]}')
            offset += self.spacing

        self.ax_main.set_xlabel('2θ (°)')
        self.ax_main.set_ylabel('Intensity (u.a.)')

    def _plot_fitting_parameters(self):
        """
        Calls the fitting parameters plotting routines (_plot_single_peak or _plot_double_peak) 
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
        
    def _plot_single_peak(self):
        """
        Based on the x data type flag (temperature/XRD measure order), plots the fitting parameters (Peak Postion, Integrated Area and FWHM) as a function of x.
        """
        x_data_type = 'temp' if self.plot_with_temp else 'file_index'
        x_label = 'XRD measure' if not self.plot_with_temp else 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)'
        self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type], self.monitor.fit_data['dois_theta_0'], 'Peak position (°)', x_label, color='red')
        self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type], self.monitor.fit_data['area'], 'Peak integrated area', x_label, color='green')
        self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type], self.monitor.fit_data['fwhm'], 'FWHM (°)', x_label, color='blue')

    def _plot_double_peak(self):
        """
        Based on the x data type flag (temperature/XRD measure order), plots the fitting parameters (Peak Postion, Integrated Area and FWHM) as a function of x. In this version, the fitting model is the Split Pseudo-Voigt Model (2x Pseudo-Voigt)
        """
        x_data_type = 'temp' if self.plot_with_temp else 'file_index'
        x_label = 'Cryojet Temperature (K)' if self.monitor.kelvin_sginal else 'Temperature (°C)' if self.plot_with_temp else 'XRD measure'

        self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type], self.monitor.fit_data['dois_theta_0'], 'Peak position (°)', x_label, label=True, color='red')
        self._plot_parameter(self.ax_2theta, self.monitor.fit_data[x_data_type], self.monitor.fit_data['dois_theta_0_#2'], 'Peak position (°)', x_label, label=True, color='red', marker='x')

        self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type], self.monitor.fit_data['area'], 'Peak integrated area', x_label, label=True, color='green')
        self._plot_parameter(self.ax_area, self.monitor.fit_data[x_data_type], self.monitor.fit_data['area_#2'], 'Peak integrated area', x_label, label=True, color='green', marker='x')

        self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type], self.monitor.fit_data['fwhm'], 'FWHM (°)', x_label, label = True, color='blue')
        self._plot_parameter(self.ax_FWHM, self.monitor.fit_data[x_data_type], self.monitor.fit_data['fwhm_#2'], 'FWHM (°)', x_label, label = True, color='blue', marker='x')

    def _plot_parameter(self, ax, x, y, ylabel, xlabel, label=None, color=None, marker='o'):
        """
        Routine for plotting x and y on given axis (ax)
        """
        for i in range(len(x)):
            norm_col = 'temp' if self.plot_with_temp else 'file_index'
            color = self.cmap(self.norm(self.plot_data[norm_col][i]))
            ax.plot(x[i], y[i], marker, color = color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if label:
            peak1 = Line2D([0], [0], color='black', marker='o', markersize=5, linestyle="", label='PseudoVoigt #1')
            peak2 = Line2D([0], [0], color='black', marker='x', markersize=5, linestyle="", label='PseudoVoigt #2')
            ax.legend(handles = [peak1, peak2])

    def select_folder(self):
        """
        Routine for selecting the folder to be monitored. It creates a FolderMonitor object and starts the monitoring process.
        """
        if self.folder_selected:
            self.monitor.data_frame = self.monitor.data_frame.iloc[0:0]
            self.monitor.fit_data = self.monitor.fit_data.iloc[0:0]
        counter.count = 0
        self.plot_with_temp = False
        self.selected_interval = None
        self.fit_interval = None
        
        self.folder_selected = False
        self.temp_mask_signal = False
        folder_path = QFileDialog.getExistingDirectory(self, 'Select the data folder to monitor', '', options=QFileDialog.Options()) # Selection of monitoring folder
        if folder_path:
            
            self.folder_selected = True
            self.monitor = FolderMonitor(folder_path=folder_path)
            self.monitor.new_data_signal.connect(self.handle_new_data)
            self.monitor.start()

        else:
            print('No folder selected. Exiting')
            

    def handle_new_data(self, new_data):
        """
        Handles new data received from the FolderMonitor object. It updates the plot_data DataFrame and calls the update_graphs routine.

        Parameters
        ----------
            new_data (DataFrame): New data received from the FolderMonitor object
        """
        self.plot_data = pd.concat([self.plot_data, new_data], ignore_index=True)
        
    def onselect(self, xmin, xmax):
        """
        Routine for selecting the fitting interval. It updates the selected_interval attribute and calls the update_graphs routine.

        Parameters
        ----------
            xmin (float): Minimum x value of the selected interval
            xmax (float): Maximum x value of the selected interval
        """
        self.selected_interval = (xmin, xmax)
        #print(f'Selected Interval: {self.selected_interval}')
        self.update_graphs()
    # Reset button function #     
    def reset_interval(self):
        """
        Routine for resetting the selected interval. It sets the selected_interval attribute to None and calls the update_graphs routine.
        """
        self.selected_interval = None
        self.update_graphs()
    # Peak fit interval selection routine # 
    def select_fit_interval(self):
        """
        Routine for selecting the fitting interval. It checks if the monitor has been initialized and calls the FitWindow object.
        """
        if not self.folder_selected:
            QMessageBox.warning(self, '','Please initialize the monitor!')
            pass
        else: 
            try:
                if len(self.plot_data['theta']) == 0:
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
    
    def on_mouse_move(self, event):
        """
        Tracks the mouse motion and updates the toolbar with the event information.

        Parameters
        ----------
            event (MouseEvent): Mouse event. Inherited from matplotlib.backend_bases.MouseEvent
        """
        self.canvas_main.mouse_event = event
        x, y = event.xdata, event.ydata
        label = None
        try:
            min_dist = self.spacing #float('inf')
        except AttributeError:
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
                    if dist < min_dist:
                        min_dist = dist 
                        label = line.get_label()
        
        #print(f'Distance: {dist}', f'X_curve: {x_data[idx]}', f'Y_Curve: {y_data[idx]}', f'X_mouse: {x}', f'Y_mouse: {y}', f'Cruve label: {label}')
                            
        #print(label)
        if label is not None and x is not None and y is not None:
            s = f"Label: {label} | 2theta={x:.2f}, Intensity={y:.2f}"
            self.toolbar.set_message(s)
        else:
            try:
                s = f"2theta={x:.2f}, Intensity={y:.2f}"
                self.toolbar.set_message(s)
            except TypeError:
                self.toolbar.set_message("")
        
    def save_data_frame(self):
        """
        Saves the fitting data to a CSV file. The user is prompted to select the file path.
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
        """
        Creates a DataFrame with the fitting data for the PseudoVoigt model.

        Returns
        -------
            DataFrame: DataFrame with the fitting data
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
        """
        Creates a DataFrame with the fitting data for the Split PseudoVoigt model (2x PseudoVoigt).

        Returns
        -------
            DataFrame: DataFrame with the fitting data
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
        """
        Validates the temperature selected at the SpinBoxes.

        Parameters
        ----------
            min_value (float): Minimum temperature value
            max_value (float): Maximum temperature value

        Returns
        -------
            tuple: Tuple with the minimum and maximum temperature values
        """
        min_temp = min(self.monitor.data_frame['temp'], key=lambda x: abs(x-min_value))
        max_temp = min(self.monitor.data_frame['temp'], key=lambda x: abs(x-max_value))
        return min_temp, max_temp
    
    def apply_temp_mask(self):
        """
        Applies the temperature mask to the data. It validates the temperature selected at the SpinBoxes and updates the plot_data DataFrame.
        """
        try:
            if self.plot_with_temp:
                min_temp, max_temp = self.validate_temp(self.min_temp_doubleSpinBox.value(), self.max_temp_doubleSpinBox_2.value())
                self.temp_mask = (self.monitor.data_frame['temp'] >= min_temp) & (self.monitor.data_frame['temp'] <= max_temp)
            else:
                self.temp_mask = (self.monitor.data_frame['file_index'] >= self.min_temp_doubleSpinBox.value()) & (self.monitor.data_frame['file_index'] <= self.max_temp_doubleSpinBox_2.value())
            self.temp_mask_signal = True
            self.update_graphs()
        except AttributeError as e:
            print(f"No data available! Please, initialize the monitor! Error: {e}")
            QMessageBox.warning(self, '','Please initialize the monitor!')
        except Exception as e:
            print(f'Exception {e} encountered')

    def measure_order_index(self, checked):
        """
        Routine for selecting the XRD measure order index. It updates the plot_with_temp flag and calls the update_graphs routine.

        Parameters
        ----------
            checked (bool): Flag for the XRD measure order index checkbox
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
        """
        Routine for selecting the temperature index. It updates the plot_with_temp flag and calls the update_graphs routine.

        Parameters
        ----------
            checked (bool): Flag for the temperature index checkbox
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
            
        
    def about(self):
        """
        Displays the About message box from PyQt.
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


class Worker(QThread):
    """
    QThread Class for performing the Peak Fit. It emits signals for progress, finished and error.

    Parameters
    ----------
        interval (list): List with the fitting interval
    """
    progress = pyqtSignal(int)
    finished = pyqtSignal(float) 
    error = pyqtSignal(str) # Changed to emit multiple arrays

    def __init__(self, interval):
        super().__init__()
        self.fit_interval = interval
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def run(self):
        """
        Peak Fitting routine. It calls the peak_fit or peak_fit_split_gaussian routine based on the selected fitting model.
        """
        
        try:
            start = time.time()
            for i in range(len(win.plot_data['theta'])):
                if win.fit_interval_window.fit_model == 'PseudoVoigt':
                    fit = peak_fit(win.plot_data['theta'][i], win.plot_data['intensity'][i], self.fit_interval)
                    new_fit_data = pd.DataFrame({'dois_theta_0': [fit[0]], 'fwhm': [fit[1]], 'area': [fit[2]], 'temp': [win.plot_data['temp'][i]], 'file_index': [win.plot_data['file_index'][i]], 'R-squared': [fit[3]]})
                    win.monitor.fit_data = pd.concat([win.monitor.fit_data, new_fit_data], ignore_index=True)
                    progress_value = int((i + 1) / len(win.plot_data['theta']) * 100)
                    self.progress.emit(progress_value)  # Emit progress signal with percentage
                else:
                    fit = peak_fit_split_gaussian(win.plot_data['theta'][i], win.plot_data['intensity'][i], self.fit_interval, height = win.fit_interval_window.height, distance=win.fit_interval_window.distance)
                    new_fit_data = pd.DataFrame({'dois_theta_0': [fit[0][0]], 'dois_theta_0_#2': [fit[0][1]], 'fwhm': [fit[1][0]], 'fwhm_#2': [fit[1][1]], 'area': [fit[2][0]], 'area_#2': [fit[2][1]], 'temp': [win.plot_data['temp'][i]], 'file_index': [win.plot_data['file_index'][i]], 'R-squared': [fit[3]]})
                    win.monitor.fit_data =pd.concat([win.monitor.fit_data, new_fit_data], ignore_index=True)
               

                    progress_value = int((i + 1) / len(win.plot_data['theta']) * 100)
                    self.progress.emit(progress_value)  # Emit progress signal with percentage
            #self.finished.emit(win.monitor.fit_data['dois_theta_0'], win.monitor.fit_data['area'], win.monitor.fit_data['fwhm'])  # Emit finished signal with results
            finish = time.time()
            self.finished.emit(finish-start)

        except Exception as e:
            self.error.emit(f'Error during peak fitting: {str(e)}. Please select a new Fit Interval')
            print(f'Exception {e}. Please select a new Fit Interval')


class FitWindow(QDialog, Ui_pk_window):
    """
    Fit Window Class. It creates a new window for the Peak Fitting routine. 
    It allows the user to select the fitting model, the fitting interval and the fitting parameters.
    It inherits the QDialog class from PyQt.
    """

    def __init__(self, parent=None):
        """
        Constructor for the FitWindow class. It initializes the window and sets up the layout.

        Parameters
        ----------
            parent (QWidget): Parent widget for the window
        """
        super().__init__(parent)
        self.setupUi(self)
        self.fit_interval= None
        self.text = None
        self.fit_model = 'PseudoVoigt'
        win.monitor.set_fit_model = "PseudoVoigt"
        self.distance = 25
        self.height = 1e+09
        self.setup_layout()

    def setup_layout(self):
        """
        Routine for setting up the layout of the FitWindow. It creates the Figure and the layout for the Peak Fitting plot.
        """
        self.setWindowTitle('Peak Fit')
        self.pk_layout = QVBoxLayout()
        self.fig = Figure(figsize=(20,10), dpi=100)
        self.ax = self.fig.add_subplot(1,1,1)
        if win.plot_with_temp:
            self.ax.plot(win.plot_data['theta'][0], win.plot_data['intensity'][0],'o', markersize=3, label = 'XRD pattern ' + str(win.plot_data['temp'][0]) + '°C')
        
        else:
            self.ax.plot(win.plot_data['theta'][0], win.plot_data['intensity'][0], 'o', markersize=3, label = 'XRD pattern #' + str(win.plot_data['file_index'][0]))
        self.ax.set_xlabel("2θ (°)")
        self.ax.set_ylabel("Intensity (u.a.)")
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

    def onChanged_xrd_combo_box(self, text):
        """
        Routine for selecting the XRD pattern to be displayed on the plot via the ComboBox.

        Parameters
        ----------
            text (str): Text selected on the ComboBox
        """

        self.text = text
        if len(self.ax.lines) == 2:
            QMessageBox.warning(self, '','Warning! It is possible to display only two XRD patterns in this window! Please press the Clear Plot button and select up to 2 XRD patterns to be displayed.')
            pass
        else:
            i = self.xrd_combo_box.currentIndex()
            self.indexes.append(i)
            if win.plot_with_temp:
                self.ax.plot(win.plot_data['theta'][i], win.plot_data['intensity'][i], 'o', markersize=3, label = ('XRD pattern ' + text))
            else:
                self.ax.plot(win.plot_data['theta'][i], win.plot_data['intensity'][i], 'o', markersize=3, label = ('XRD pattern #' + text))
        
            self.ax.set_xlabel("2θ (°)")
            self.ax.set_ylabel("Intensity (u.a.)")
            self.ax.legend(fontsize='small')
            self.canvas.draw()
    
    def onChanged_pk_combo_box(self, text):
        """
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
        else:
            self.fit_model = '2x PseudoVoigt(SPV)'
            win.monitor.set_fit_model = '2x PseudoVoigt(SPV)'
            self.distance_spinBox.setReadOnly(False)
            self.height_spinBox.setReadOnly(False)
    def onChanged_bkg_combo_box(self, text):
        """
        Routine for selecting the Background Model via the ComboBox.

        Parameters
        ----------
            text (str): Text selected on the ComboBox
        """

        if text == 'Linear Model': 
            self.bkg_model = 'Linear'
        else:
            self.bkg_model = 'Spline'

    def onselect(self, xmin, xmax):
        """
        Routine for selecting the fitting interval. It updates the fit_interval attribute and the interval_label label.

        Parameters
        ----------
            xmin (float): Minimum x value of the selected interval
            xmax (float): Maximum x value of the selected interval
        """

        if self.shade:
            self.shade.remove()
        self.fit_interval = [xmin, xmax]
        self.interval_label.setText(f'[{xmin:.3f}, {xmax:.3f}]')
        self.shade = self.ax.axvspan(self.fit_interval[0], self.fit_interval[1], color='grey', alpha=0.5, label='Selected Fitting Interval')
        self.canvas.draw()
        
    def onChanged_distance_spinbox(self, value):
        """
        Method for setting the distance between the two peaks for the Split Pseudo-Voigt Model.

        Parameters
        ----------
            value (int): Value selected on the SpinBox
        """
        self.distance = value

    def onChanged_height_spinbox(self, value):
        """
        Method for setting the height for the peak search for the Split Pseudo-Voigt Model.

        Parameters
        ----------
            value (int): Value selected on the SpinBox
        """
        self.height = value*(1e+09)
        

    def clear_plot(self):
        """
        Clears the plot on the FitWindow.
        """
        self.ax.clear()
        self.canvas.draw()
        self.indexes.clear()

    def preview(self):
        """
        Returns a Preview of the Peak Fitting for the selected Model and 2theta Interval.
        """
        if len(self.ax.lines) > 2:
            while len(self.ax.lines) > 2:
                self.ax.lines[len(self.ax.lines)-1].remove()
        if self.fit_model == "PseudoVoigt":
            for i in range(len(self.indexes)):
                data = peak_fit(win.plot_data['theta'][self.indexes[i]], win.plot_data['intensity'][self.indexes[i]], self.fit_interval)
                if win.plot_with_temp:
                    self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - {win.plot_data["temp"][self.indexes[i]]} °C')
                    self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - {win.plot_data["temp"][self.indexes[i]]} °C')
                else:
                    self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - #{win.plot_data["file_index"][self.indexes[i]]}')
                    self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - #{win.plot_data["file_index"][self.indexes[i]]}')
                self.ax.legend(fontsize='small')
                self.canvas.draw()
        else:
            for i in range(len(self.indexes)):
                try:
                    data = peak_fit_split_gaussian(win.plot_data['theta'][self.indexes[i]], win.plot_data['intensity'][self.indexes[i]], self.fit_interval, height = self.height, distance=self.distance)
                    if win.plot_with_temp:
                        self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - {win.plot_data["temp"][self.indexes[i]]} °C')
                        self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - {win.plot_data["temp"][self.indexes[i]]} °C')
                    else:
                        self.ax.plot(data[6], data[4].best_fit, '--', label = f'Best Fit - #{win.plot_data["file_index"][self.indexes[i]]}')
                        self.ax.plot(data[6], data[5]['bkg_'], '-', label = f'Background - #{win.plot_data["file_index"][self.indexes[i]]}')
                    self.ax.legend(fontsize='small')
                    self.canvas.draw()
                except UnboundLocalError as e:
                    QMessageBox.warning(self, '', 'The value given for distance and/or height for peak search are out of bounds, i.e., it was not possible to find two peaks mtaching the given parameters! Please, try again with different values for distance and height!')

    def fit(self):
        """
        Routine for starting the Peak Fitting process. It sets the fitting interval, the fitting model, the distance and the height for the Split Pseudo-Voigt Model.
        It starts the Worker thread for the Peak Fitting process.
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
        """
        Routine for updating the progress bar on the Peak Fitting process.

        Parameters
        ----------
            value (int): Value for the progress bar
        """

        self.progress_dialog.setValue(value)

    def peak_fitting_finished(self, time):
        """
        Routine for handling the Peak Fitting process completion. It updates the graphs and displays a message box with the elapsed time.

        Parameters
        ----------
            time (float): Elapsed time for the Peak Fitting process
        """

        self.progress_dialog.setValue(100)
        QMessageBox.information(self, "Peak Fitting", f"Peak fitting completed successfully! Elapsed time: {int(time)}s")
        win.update_graphs()
        
        self.close()

    def peak_fitting_error(self, error_message):
        """
        Routine for handling the Peak Fitting process error. It displays a message box with the error message.

        Parameters
        ----------
            error_message (str): Error message for the Peak Fitting process
        """
        self.progress_dialog.cancel()
        QMessageBox.warning(self, "Peak Fitting Error", error_message)
        self.show()

        

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
