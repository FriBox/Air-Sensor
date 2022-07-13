# FriBox Air Sensor
Open Source Air Sensor （开源空气质量监测仪/传感器）<br>
Esp32 +  Micropython + PMS5003ST + HmiLcd = FriBox Air Sensor<br>
<br>
<img src="/Demo/7.FriBoxAirSensor.v1.0.0.Demo6.png" width="480px"><br>
<img src="/Demo/0.FriBoxAirSensor.v1.0.0.渲染1.png" width="480px"><br>
<img src="/Demo/1.FriBoxAirSensor.v1.0.0.渲染2.png" width="480px"><br>

### 硬件组成
ESP32 -- Wifi蓝牙开发板  /  ESP32 Micropython 开发板<br>
PMS5003ST -- 攀藤颗粒物甲醛温湿度传感器  /  颗粒物 甲醛 温湿度<br>
TJC4832T035_011 -- 串口触摸屏  /  inch:3.5(320X480) Flash:16M RAM:3584B Frequency:48M<br>

### 线路链接定义
PMS5003ST  串口+复位  /  Rst21,Rx22,Tx23<br>
TJC4832T035_011 串口  /  Rx25,Tx26<br>

### 刷写程序
1. 修改 Download.cmd 中的对应的 Esptool 工具的路径<br>
2. 修改 Download.cmd 中的对应的串口名称<br>
3. 执行 Download.cmd 等待刷写完毕<br>

### 屏幕固件更新
准备一块TF卡，格式化为Fat32格式，把Main.v1.0.0-Lcd3.5.tft复制到TF卡，保证TF卡只有这一个文件，然后将TF卡插入屏幕，重新上电系统，等待屏幕固件写入完成后拔出TF卡，重新上电系统。

### 3D打印外壳
FDM打印机：使用Model文件夹下 FAS.v1.0.0.Print1.gcode 和 FAS.v1.0.0.Print2.gcode 这两个文件夹即可打印出显示屏外壳和主机底座。
光固化打印机：使用Model文件夹下 FAS.v1.0.0.Print1.stl 和 FAS.v1.0.0.Print2.stl 这两个文件夹即可打印出显示屏外壳和主机底座。
