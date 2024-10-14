# Iguape - Paineira Graphical User Interface


## Description
Iguape is a graphical user interface designed to help users during *in situ* experiments at Paineira. Via Iguape the user can visualize the numerous XRD patterns generated throughout the experiments. The program allows for peak fitting at a selected angle interval.  

## Visuals
The GUI has two tabs and concentrate its features in a button panel at the bottom of the window. The XRD Data tab displays the diffraction patterns stacked by a user-defined offset. The Peak Fitting tab displays the data obtained through peak fitting of the XRD patterns on the selected 2theta interval.
![Iguape_XRD_Data_Main_Window](https://github.com/user-attachments/assets/fffae287-6076-495d-a3fe-dc6e4289b7c0)
![Iguape_Peak_Fit_PsdVoigt](https://github.com/user-attachments/assets/4c7c9224-88ac-41ad-bcb7-c248986fdfb3)
## Installation
#Windows
For Windows users we'll make available a installer.
#Linux
We're still evaluating the availability of installation vai Linux-terminal.
## Usage
# **Initialization**
The first step, once Iguape is initialized, is to select a folder to monitor. This can be done by clicking in the **Folder** option at the upper right corner of the window. It's important that the selected folder contains the iguape_fileslist.txt file. It is though this text document, that Iguape can read the XRD data available at the Folder. 
![Initialization](https://github.com/user-attachments/assets/01f48445-52b8-4c89-afb8-43136d05c2d8)
# **Custom Vizualization**
Iguape offers tools for custom visualization of the XRD patterns. These include: XRD patterns offset, 2theta and temperature/measure order masks, zoom, pan and figure saving.
[Iguape_tools.webm](https://github.com/user-attachments/assets/c93e1e50-0b08-4bf3-a910-51283d634559)
![Iguape_tools#2](https://github.com/user-attachments/assets/5d5267a4-516c-45af-b2d4-3173848b98b0)

# **Peak Fit**
Peak fitting is available in Iguape, helping the analysis of sample evotution during _in situ_ experiments. When the Peak Fit button is pressed, a new window will be opened. The user, then, can configure the fitting model and have a preview of the best fit achieved by Iguape.  
![PeakFIt](https://github.com/user-attachments/assets/3bedf4d9-e06d-4b84-a5a0-9cecd292adbd)
![Iguape_Peak_Fit_Window_2xPsdVoigt](https://github.com/user-attachments/assets/38ef0b40-ea7d-436d-a140-c3b40f8ac19b)
## Support
Any enquiries can be adressed to joao.neto@lnls.br. Please, fell free to suggest or correct anything.

## Authors and acknowledgment
João Luis Biondo Neto;
Junior Cintra Mauricio

## License


## Project status
Iguape is fully operational at Paineira. Working on distribution for Paineira users. 
