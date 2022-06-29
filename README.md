# FriBox Air Sensor
Open Source Air Sensor （开源空气质量监测仪/传感器）
Esp32 +  Micropython + PMS5003ST + HmiLcd = FriBox Air Sensor

### 硬件组成
ESP32 -- Wifi蓝牙开发板  /  ESP32 Micropython 开发板
PMS5003ST -- 攀藤颗粒物甲醛温湿度传感器  /  颗粒物 甲醛 温湿度
TJC4832T035_011 -- 串口触摸屏  /  inch:3.5(320X480) Flash:16M RAM:3584B Frequency:48M

### 线路链接定义
PMS5003ST  串口+复位  /  Rst21,Rx22,Tx23
TJC4832T035_011 串口  /  Rx25,Tx26

### 刷写程序
1. 修改 Download.cmd 中的对应的 Esptool 工具的路径
2. 修改 Download.cmd 中的对应的串口名称
3. 执行 Download.cmd 等待刷写完毕

### 屏幕固件更新
准备一块TF卡，格式化为Fat32格式，把Main.v0.99b.tft复制到TF卡，保证TF卡只有这一个文件，然后将TF卡插入屏幕，重新上电系统，等待屏幕固件写入完成后拔出TF卡，重新上电系统。
