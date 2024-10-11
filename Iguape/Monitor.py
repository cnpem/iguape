#This is part of the source code for the Paineira Graphical User Interface - Iguape
#The code is distributed under the GNU GPL-3.0 License. Please refer to the main page (https://github.com/cnpem/iguape) for more information

"""
This is Monitor Class. It was built to track and read a given Folder for new XRD Data. It's dependent on the iguape_fileslist.txt text file.
It was built to work only for Paineira XRD Data, but it can easily be adjusted for other situations.
"""

import time, os, math
import numpy as np
import lmfit as lm
from lmfit.models import PseudoVoigtModel, LinearModel
import pandas as pd
from scipy.signal import find_peaks
from PyQt5.QtCore import QThread, pyqtSignal

# --- Monitor - Reading a '.txt' file for new data --- #
class FolderMonitor(QThread):
	new_data_signal = pyqtSignal(pd.DataFrame)
	def __init__(self, folder_path, fit_interval=None):
		super().__init__()
		self.folder_path = folder_path
		self.fit_interval = fit_interval
		self.fit_model = 'PseudoVoigt'
		self.kelvin_sginal = False
		self.processed_files = set()  # Tracking the processed files
		self.data_frame = pd.DataFrame(columns = ['theta', 'intensity', 'temp', 'max', 'file_index'])
		self.fit_data = pd.DataFrame(columns=['dois_theta_0', 'fwhm', 'area', 'temp', 'file_index', 'R-squared'])

	def run(self):
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
						new_data = pd.DataFrame({'theta': [data[0]], 'intensity': [data[1]], 'temp': [data[2]], 'max': [data[1].max()], 'file_index': [file_index]})
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
					#print(f'Exception: {e}')
					time.sleep(0.1)
			
			i+=2
		

	def set_fit_interval(self, interval):
		self.fit_interval = interval
	def set_fit_model(self, model):
		self.fit_model= model
	def set_distance(self, distance):
		self.distance = distance
	def set_height(self, height):
		self.height = height
# --- Defining the functions for data reading and peak fitting --- #
def data_read(path):
	done = False
	while not done:
		time.sleep(0.1)
		try:
			dados = pd.read_csv(path, sep=',')
			x = np.array(dados.get('2theta (degree)'))
			y = np.array(dados.get('Intensity'))
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
			return x,y,temp, kelvin_signal
		except pd.errors.EmptyDataError:
			print(f"Warning: Empty file encountered: {path}. Trying to read the data again!")
			#return None
		except Exception as e:
			print(f"An error occurred while reading data: {e}. Trying to read the data again!")
			#return None

# --- Defining the storaging lists --- #		


def peak_fit(theta, intensity, interval, bkg = 'Linear'):
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
			
			mod = PseudoVoigtModel(nan_policy='omit')
			pars = mod.guess(data= intensity_fit, x = theta_fit)
			background = LinearModel(prefix='bkg_')
			pars.update(background.guess(data=intensity_fit, x = theta_fit))
			mod += background
			
			out = mod.fit(intensity_fit, pars, x=theta_fit) # Fitting the data to the Voigt model #
			comps = out.eval_components(x=theta_fit)
  # Getting the parameters from the optimal fit #, bkg= self.bkg_model
			
			dois_theta_0 = out.params['center']*1
			fwhm = out.params['fwhm']*1
			area = out.params['amplitude']*1
			r_squared = out.rsquared

			done = True
			return dois_theta_0, fwhm, area, r_squared, out, comps, theta_fit
		except ValueError or TypeError as e:
			print(f'Fitting error, please wait: {e}! Please select a new fitting interval')
			done = True
			pass

def pseudo_voigt(x, amplitude, center, sigma, eta):
    sigma_g = sigma/math.sqrt(2*math.log(2))
    gaussian = (amplitude/(sigma_g*math.sqrt(2*math.pi)))*np.exp(-(x-center)**2/(2*sigma_g** 2))
    lorentzian = ((amplitude/math.pi)*sigma)/((x - center)**2 + sigma**2)
    return eta*lorentzian + (1 - eta)*gaussian

def split_pseudo_voigt(x, amp1, cen1, sigma1, eta1, amp2, cen2, sigma2, eta2):
    return (pseudo_voigt(x, amplitude=amp1, center=cen1, sigma=sigma1, eta=eta1) +
            pseudo_voigt(x, amplitude=amp2, center=cen2, sigma=sigma2, eta=eta2))

def peak_fit_split_gaussian(theta, intensity, interval, bkg = 'Linear', height=1e+09, distance = 35):
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
			return dois_theta_0, fwhm, area, r_squared, out, comps, theta_fit
		except ValueError or TypeError as e:
			print(f'Fitting error, please wait: {e}! Please select a new fitting interval')
			done = True
			pass




# --- A counter function to index the created curves --- #
def counter():
	counter.count += 1
	return counter.count
	
counter.count = 0
