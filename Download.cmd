SET AppName="Esp32 Micropython Download"
Title %AppName%
SET DirRoot=%~dp0
SET Esptool=k:\Root.Data\Development\Python\Python3.x64.Miniconda\Scripts\

%Esptool%esptool.exe --port COM6 erase_flash
%Esptool%esptool.exe --chip esp32 --port COM6 --baud 460800 write_flash -z 0x1000 %DirRoot%esp32-20220618-v1.19.1.bin

%Esptool%ampy.exe --port COM6 put %DirRoot%boot.py
@ping -n 2 127.0.0.1>nul

%Esptool%ampy.exe --port COM6 put %DirRoot%wifi_config.json
@ping -n 2 127.0.0.1>nul
%Esptool%ampy.exe --port COM6 put %DirRoot%hmac.py
@ping -n 2 127.0.0.1>nul
%Esptool%ampy.exe --port COM6 put %DirRoot%warnings.py
@ping -n 2 127.0.0.1>nul
%Esptool%ampy.exe --port COM6 put %DirRoot%FB_NTP.py
@ping -n 2 127.0.0.1>nul
%Esptool%ampy.exe --port COM6 put %DirRoot%FB_Ntptime.py
@ping -n 2 127.0.0.1>nul

%Esptool%ampy.exe --port COM6 put %DirRoot%Main.py

@echo Download Complete !
pause
