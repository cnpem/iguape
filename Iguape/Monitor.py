#This is part of the source code for the Paineira Graphical User Interface - Iguape
#The code is distributed under the GNU GPL-3.0 License. Please refer to the main page (https://github.com/cnpem/iguape) for more information

"""
This is Monitor Class. It was built to track and read a given Folder for new XRD Data. It's dependent on the iguape_fileslist.txt text file.
It was built to work only for Paineira XRD Data, but it can easily be adjusted for other situations.
"""

import time, os, math, sys
import numpy as np
import lmfit as lm
from lmfit.models import PseudoVoigtModel, LinearModel, GaussianModel
import pandas as pd
from scipy.signal import find_peaks
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QFileDialog

# --- Monitor - Reading a '.txt' file for new data --- #
class FolderMonitor(QThread):
	"""
	The Folder Monitor operates by tracking new or exiting data in a specified folder.

	This class inherits the QThread class from PyQt. By reading the 'iguape_filelist.txt' file, it can track new or existing data files in the specified folder.
	Later, it reads the data and stores it in a pandas DataFrame. If a fitting interval is specified, it fits the data to a desired model and stores the fitting parameters in another DataFrame.
	

	Parameters
	----------
		folder_path (str): Path to the data folder.
		fit_interval (list): 2theta interval selected to perform the peak fit.
	""" 
	new_data_signal = pyqtSignal(pd.DataFrame)
	def __init__(self, folder_path, fit_interval=None):
		"""
		The constructor for the FolderMonitor class. It defines all the flags necessary for the class to work,
		like the folder path, the fit interval, the fit model and the DataFrames.

		Parameters
		----------
			folder_path (str): Path to the data folder.
			fit_interval (list, optional): 2theta interval selected to perform. Default is None

		"""
		super().__init__()
		self.folder_path = folder_path
		self.fit_interval = fit_interval
		self.fit_model = 'PseudoVoigt'
		self.kelvin_sginal = False
		self.data_frame = pd.DataFrame(columns=['file_name', 'temp', 'file_index', 'max'])
		self.fit_data = pd.DataFrame(columns=['dois_theta_0', 'fwhm', 'area', 'temp', 'file_index', 'R-squared'])

	def run(self):
		"""
		The run method is the main method of the FolderMonitor class. It reads the 'iguape_filelist.txt' file 
		tracking all the XRD data in the folder. Then it reads the data and stores it as DataFrames. I also performs
		the peak fit, if a fit interval is specified.
		"""
		reading_status = 1
		i = 0
		print(f'Monitoring folder: {self.folder_path}')
		print('Waiting for XRD data! Please, wait')
		while reading_status == 1:
			while True:
				try:
					with open(os.path.join(self.folder_path,'iguape_filelist.txt'),"r") as file:
						lines = file.read().splitlines()
						line = lines[i+1]
						data = data_read(os.path.join(self.folder_path,line))
						self.kelvin_sginal = data[3]
						file_index = counter()
						new_data = pd.DataFrame({'file_name':[os.path.join(self.folder_path,line)], 'temp': [data[2]], 'file_index': [file_index], 'max': [data[1].max()]})
						self.data_frame = pd.concat([self.data_frame, new_data], ignore_index=True)
						self.new_data_signal.emit(new_data)
						print(f"New data created at: {self.folder_path}. File name: {lines[i+1]}")
						if self.fit_interval:
							if self.fit_model == 'PseudoVoigt':
								fit = peak_fit(data[0], data[1], self.fit_interval)
								new_fit_data = pd.DataFrame({'dois_theta_0': [fit[0]], 'fwhm': [fit[1]], 'area': [fit[2]], 'temp': [data[2]], 'file_index': [file_index], 'R-squared': [fit[3]]})
								self.fit_data = pd.concat([self.fit_data, new_fit_data], ignore_index=True)
							else:
								fit = peak_fit_split_gaussian(data[0], data[1], self.fit_interval, height=self.height, distance = self.distance)
								new_fit_data = pd.DataFrame({'dois_theta_0': [fit[0]][0], 'fwhm': [fit[1][0]], 'area': [fit[2][0]], 'temp': [data[2]], 'file_index': [file_index], 'R-squared': [fit[3]]})
								self.fit_data = pd.concat([self.fit_data, new_fit_data], ignore_index=True)
								self.fit_data.insert(1,'dois_theta_0_#2', [fit[0][1]])
								self.fit_data.insert(3, 'fwhm_#2', [fit[1][1]])
								self.fit_data.insert(5, 'area_#2', [fit[2][1]])

						reading_status = int(lines[i+2])

					break
				except Exception as e:
					pass
			
			i+=2
		

	def set_fit_interval(self, interval):
		"""
		Method for defining the fit interval.

		Parameters
		----------
			interval (list): The 2theta interval to be used for the peak fitting.
		"""
		self.fit_interval = interval
	def set_fit_model(self, model):
		"""
		Method for defining the fit model.

		Parameters
		----------
			model (str): The model to be used for the peak fitting. It can be 'PseudoVoigt' or 'SplitPseudoVoigt'.
		"""
		self.fit_model= model
	def set_distance(self, distance):
		"""
		Method for defining the minimum distance between the two peak centers. Only used when the model is
		Split PseduoVoigt.

		Parameters
		----------
			distance (float): The minimum distance between the two peak centers.
		"""
		self.distance = distance
	def set_height(self, height):
		"""
		Method for defining the minimum height of the two peaks. Only used when the model is
		Split PseduoVoigt.

		Parameters
		----------
			height (float): The minimum height of the two peaks.
		"""
		self.height = height
# --- Defining the functions for data reading and peak fitting --- #
def data_read(path):
	"""
	Data reading function. 
	
	It reads the data from a given path and returns the 2theta and Intensity arrays, Temperature and Kelvin Signal tag.

	Parameters
	----------
		path (str): Path to the data file.

	Returns
	-------
		x (np.array): 2theta array.
		y (np.array): Intensity array.
		temp (float): Temperature.
		kelvin_signal (bool): Kelvin Signal tag.
	"""
	done = False
	while not done:

		try:
			data = pd.read_csv(path, sep = ',', header=0, comment="#")
			x = np.array(data.iloc[:, 0])
			y = np.array(data.iloc[:, 1])
			file_name = path.split(sep='/')[len(path.split(sep='/'))-1]
			temp = None
			kelvin_signal = None
			for i in file_name.split(sep='_'):
				if 'Celsius' in i: 
					temp = float(i.split(sep='Celsius')[0]) #Getting the temperature
				elif 'Kelvin' in i:
					temp = float(i.split(sep='Kelvin')[0])
					kelvin_signal = True
			done = True
			return x, y, temp, kelvin_signal
		except pd.errors.EmptyDataError:
			print(f"Warning: Empty file encountered: {path}. Trying to read the data again!")

		except Exception as e:
			print(f"An error occurred while reading data: {e}. Trying to read the data again!")


# --- Defining the storaging lists --- #		


def peak_fit(theta, intensity, interval, bkg = 'Linear', pars = None):
	"""
	Peak fitting function for the PseudoVoigt model.
	Given a set of 2theta and Intensity arrays, it fits the data to the
	PseudoVoigt model and 2theta interval selected. It returns the fitting parameters.

	Parameters
	----------
		theta (np.array): 2theta array.
		intensity (np.array): Intensity array.
		interval (list): 2theta interval for the peak fitting.
		bkg (str, optional): Background model. Default is 'Linear'.

	Returns
	-------
		dois_theta_0 (float): Peak center.
		fwhm (float): Full Width at Half Maximum.
		area (float): Area under the peak.
		r_squared (float): R-squared value of the fit.
		out (lmfit.ModelResult): ModelResult. Inherited from the lmfit package.
		comps (dict): Fitting components such as the backgroud and model function. Inherited from the lmfit package.
		theta_fit (np.array): 2theta array for the fitting interval.
	"""
	done = False
	while not done:

		try:
			theta_fit = []
			intensity_fit = []

		# Slicing the data for the selected peak fitting interval #
			for i in range(len(theta)):
				if theta[i] > interval[0] and theta[i] < interval[1]: 
					theta_fit.append(theta[i])
					intensity_fit.append(intensity[i])
			theta_fit=np.array(theta_fit)
			intensity_fit=np.array(intensity_fit)
		# Building the Voigt model with lmfit #
			
			mod = PseudoVoigtModel(nan_policy='omit')
			if pars == None:
				pars = mod.guess(data= intensity_fit, x = theta_fit)
			background = LinearModel(prefix='bkg_')
			pars.update(background.guess(data=intensity_fit, x = theta_fit))
			mod += background
			
			out = mod.fit(intensity_fit, pars, x=theta_fit) # Fitting the data to the Voigt model #
			comps = out.eval_components(x=theta_fit)
		# Getting the parameters from the optimal fit #, bkg= self.bkg_model
			
			dois_theta_0 = out.params['center'].value
			#dois_theta_0_stderr = out.params['center'].stderr*1
			fwhm = out.params['fwhm'].value
			#fwhm_stderr = out.params['fwhm'].stderr*1
			area = out.params['amplitude'].value
			#area_stderr = out.params['amplitude'].stderr*1
			r_squared = out.rsquared

			done = True
			
			return dois_theta_0, fwhm, area, r_squared, out, comps, theta_fit, out.params
		except ValueError or TypeError as e:
			print(f'Fitting error, please wait: {e}! Please select a new fitting interval')
			done = True
			pass

def pseudo_voigt(x, amplitude, center, sigma, eta):
	r"""
	PseudoVoigt function, a linear combination of a Gaussian and a Lorentzian function.

	Parameters
	----------
		x (np.array): 2theta array.
		amplitude (float): Peak amplitude.
		center (float): Peak center.
		sigma (float): Sigma value or standard deviation.
		eta (float): Eta value (mixing parameter).

	Returns
	-------
		np.array: PseudoVoigt function.

	Notes
	-----
	The PseudoVoigt function is defined as:
	.. math::
			PV(x; A, \mu, \sigma, \eta) = \eta L(x; A, \mu, \sigma) + (1 - \eta) G(x; A, \mu, \sigma)
			where:
			- L(x; A, \mu, \sigma) is the Lorentzian function
			- G(x; A, \mu, \sigma) is the Gaussian function
	"""
	sigma_g = sigma/math.sqrt(2*math.log(2))
	gaussian = (amplitude/(sigma_g*math.sqrt(2*math.pi)))*np.exp(-(x-center)**2/(2*sigma_g** 2))
	lorentzian = ((amplitude/math.pi)*sigma)/((x - center)**2 + sigma**2)
	return eta*lorentzian + (1 - eta)*gaussian

def split_pseudo_voigt(x, amp1, cen1, sigma1, eta1, amp2, cen2, sigma2, eta2):
	r"""
	Split PseudoVoigt function, a linear combination of two PseudoVoigt functions.

	Parameters
	----------
		x (np.array): 2theta array.
		amp1 (float): Peak amplitude for the first peak.
		cen1 (float): Peak center for the first peak.
		sigma1 (float): Sigma value or standard deviation for the first peak.
		eta1 (float): Eta value for the first peak (mixing parameter).
		amp2 (float): Peak amplitude for the second peak.
		cen2 (float): Peak center for the second peak.
		sigma2 (float): Sigma value or standard deviation for the second peak.
		eta2 (float): Eta value for the second peak (mixing parameter).
	
	Returns
	-------
		np.array: Split PseudoVoigt function.

	Notes
	-----
	The Split PseudoVoigt function is defined as:
		.. math::
			SPV(x; A1, \mu1, \sigma1, \eta1, A2, \mu2, \sigma2, \eta2) = PV1(x; A1, \mu1, \sigma1, \eta1) + PV2(x; A2, \mu2, \sigma2, \eta2)
	

	"""
	return (pseudo_voigt(x, amplitude=amp1, center=cen1, sigma=sigma1, eta=eta1) +
			pseudo_voigt(x, amplitude=amp2, center=cen2, sigma=sigma2, eta=eta2))

def peak_fit_split_gaussian(theta, intensity, interval, bkg = 'Linear', height=1e+09, distance = 35, pars = None):
	"""
	Peak fitting function for the Split PseudoVoigt model.
	Given a set of 2theta and Intensity arrays, it fits the data to the
	Split PseudoVoigt model and 2theta interval selected. It returns the fitting parameters.

	Parameters
	----------
		theta (np.array): 2theta array.
		intensity (np.array): Intensity array.
		interval (list): 2theta interval for the peak fitting.
		bkg (str, optional): Background model. Default is 'Linear'.
		height (float, optional): Minimum height for the peaks. Default is 1e+09.
		distance (float, optional): Minimum distance between the peaks. Default is 35.
	
	Returns
	-------
		dois_theta_0 (list): Peak centers.
		fwhm (list): Full Width at Half Maximum.
		area (list): Area under the peaks.
		r_squared (float): R-squared value of the fit.
		out (lmfit.ModelResult): ModelResult. Inherited from the lmfit package.
		comps (dict): Fitting components such as the backgroud and model function. Inherited from the lmfit package.
		theta_fit (np.array): 2theta array for the fitting interval.
	"""
	done = False
	while not done:
		#time.sleep(0.5)
		try:
			theta_fit = []
			intensity_fit = []
  
  # Slicing the data for the selected peak fitting interval #
			for i in range(len(theta)):
				if theta[i] > interval[0] and theta[i] < interval[1]: 
					theta_fit.append(theta[i])
					intensity_fit.append(intensity[i])
			theta_fit=np.array(theta_fit)
			intensity_fit=np.array(intensity_fit)
  # Building the Voigt model with lmfit #
			
			peaks, properties = find_peaks(intensity_fit, height=height, distance=distance)
			if len(peaks) >= 2:
	# Sort peaks by prominence and pick the top two
				sorted_indices = np.argsort(properties['peak_heights'])[-2:]
				peak_positions = theta_fit[peaks][sorted_indices]
				peak_heights = properties['peak_heights'][sorted_indices]
				if peak_positions[0] > peak_positions[1]:
					amp2, cen2 = peak_heights[0], peak_positions[0]
					amp1, cen1 = peak_heights[1], peak_positions[1]
				else:
					amp1, cen1 = peak_heights[0], peak_positions[0]
					amp2, cen2 = peak_heights[1], peak_positions[1]

	# Estimate sigma using the width of the peaks at half height
				sigma1 = 0.1/2.355
				sigma2 = 0.1/2.355
				
				

			model = lm.Model(split_pseudo_voigt)
			if pars == None:
				pars = model.make_params(amp1=amp1, cen1=cen1, sigma1=sigma1, eta1=0.5, amp2=amp2, cen2=cen2, sigma2=sigma2, eta2=0.5)
			pars['eta1'].min, pars['eta1'].max = 0, 1
			pars['eta2'].min, pars['eta2'].max = 0, 1
			background = LinearModel(prefix='bkg_')
			pars.update(background.guess(data=intensity_fit, x = theta_fit))
			model += background		

			out = model.fit(intensity_fit, pars, x=theta_fit) # Fitting the data to the Voigt model #
			comps = out.eval_components(x=theta_fit)
			
  # Getting the parameters from the optimal fit #, bkg= self.bkg_model
			
			dois_theta_0 = [out.params['cen1']*1, out.params['cen2']*1]
			fwhm = [2.0*out.params['sigma1'], 2.0*out.params['sigma2']]
			area = [out.params['amp1']*1, out.params['amp2']*1]
			r_squared = out.rsquared
			done = True
			return dois_theta_0, fwhm, area, r_squared, out, comps, theta_fit, out.params
		except ValueError or TypeError as e:
			print(f'Fitting error, please wait: {e}! Please select a new fitting interval')
			done = True
			pass

def normalize_array(array: np.array):
    return array/np.max(array)

# --- A counter function to index the created curves --- #
def counter():
	"""
	Counter function. It counts the number of XRD data and returns its index.

	Returns
	-------
		int: Index of the XRD data.
	"""

	counter.count += 1
	return counter.count
	
counter.count = 0

if __name__ == "__main__":
	app = QApplication(sys.argv)
	path = QFileDialog.getExistingDirectory(None, 'Select the data folder to monitor', '', options=QFileDialog.Options()) # Selection of monitoring folder
	monitor = FolderMonitor(path)
	monitor.start()
	print(monitor.data_frame)
	sys.exit(app.exec())