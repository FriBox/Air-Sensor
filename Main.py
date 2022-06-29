#coding=UTF-8

# FriBox Air Sensor v0.99b
# Create by Stream.Wang 2022-06-22
# Modify by Stream.Wang 2022-05-23

#引入基本库
import sys,os,utime,json,network,hmac,math,time,machine;
import ustruct as struct
from machine import UART,Pin, I2C;
#引入扩展库
import FB_NTP; #NTP库

#wifi全局变量
global ap; #AP模式连接
global wifi; #wifi连接
global WifiConn; #wifi连接状态
global essid; #wifi SSID
global password; #wifi Pass
global WifiCnfCount;
#硬件相关全局变量
global HDName; #系统名称
global HDVer; #系统版本号
global HDAPName; #系统AP名称
global HWHID; #硬件ID
global HD_Date; #系统日期
global HD_Time; #系统时间
global HD_DateTime; #系统日期时间
global HD_Week; #系统星期
global HD_WeekZH; #系统星期中文
global FirstWifi; #wifi初始化状态

#初始化变量
HDName='FriBox Air Sensor';
HDVer='v0.99b';
HDAPName='FriBox-AirSensor';
WifiCnfCount=-1;
FirstWifi=0;
sys.path.append('examples'); # 添加路径
print(' # >> System >> Initializing . . .');

# wCount 内部计数器
global wCount;
wCount=0;
# wPage 屏幕页面计数器
global wPage;
wPage=0;

#PMS5003ST 复位传感器
PMS_Rst=Pin(21, Pin.OUT);
PMS_Rst.value(0);
global PMSData;
PMSData= dict();
PMSData['PM1.0CF']='0.00';
PMSData['PM2.5CF']='0.00';
PMSData['PM10CF']='0.00';
PMSData['PM1.0']='0.00';
PMSData['PM2.5']='0.00';
PMSData['PM10']='0.00';
PMSData['GTR0.3um']='0.00';
PMSData['GTR0.5um']='0.00';
PMSData['GTR1.0um']='0.00';
PMSData['GTR2.5um']='0.00';
PMSData['GTR5.0um']='0.00';
PMSData['GTR10um']='0.00';
PMSData['HCHO']='0.000';
PMSData['Temperature']='00.0';
PMSData['Humidity']='00..0';
PMSData['PM2.5QX']=0;
PMSData['HCHOQX']=0.000;
global PM25;
PM25=0.00;
global HCHO;
HCHO=0.000;
global TC; #补偿温度，由于传感器内部气流，可能导致温度检测值低于实际温度，估添加补偿值。
TC=+3.2;

#TJC4832T035_011 -- 串口触摸屏  /  inch:3.5(320X480) Flash:16M RAM:3584B Frequency:48M
global uartHMI; # TJC4832T035_011
uartHMI = UART(2, baudrate=115200, rx=26,tx=25,timeout=10);
uartHMI.write(b"rest"); # 发送串口屏命令
utime.sleep_us(2);
uartHMI.write(b"\xff\xff\xff"); # 发送结束符
#切换至启动页面
uartHMI.write(b"page 0"); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
global P0VAR1; # 进度条百分数值
P0VAR1=0;
utime.sleep_ms(350); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条


#获取MAC地址
sta_if = network.WLAN(network.STA_IF);
s = sta_if.config('mac');
DivMac = ('%02x%02x%02x%02x%02x%02x') %(s[0],s[1],s[2],s[3],s[4],s[5]);
DivMac = str(DivMac).upper();
HWHID='FBAS'+DivMac;
print(' # >> System >> Hardware HID is ['+HWHID+']');
utime.sleep_ms(350); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条


#初始化AP模式，等待客户端连入配置本设备
ap = network.WLAN(network.AP_IF);
ap.config(essid=HDAPName+'-'+HWHID,authmode=network.AUTH_WPA_WPA2_PSK, password="20121221");
ap.ifconfig(('192.168.199.1','255.255.255.0','192.168.199.1','1.1.1.1'));
ap.active(True);
print(' # >> Network >> AP mode started , Name is '+HDAPName+'-'+HWHID);
P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#初始化完成 

def do_connect():
    #链接wifi
    global wifi;#wifi连接
    global WifiConn;#wifi连接状态
    global essid;#wifi SSID
    global password;#wifi Pass
    global WifiCnfCount;
    global FirstWifi;
    #读取Wifi配置文件
    WifiCnfCount=1;
    try:
        with open('wifi_config.json','r') as f:
            config = json.loads(f.read());
            WifiCnfCount=config['WifiCnfCount'];
    except:
        #若初次运行,则将进入excpet,执行配置文件的创建
        config = {};
        config['WifiCnfCount']=1;
        config['essid1']='FriBox-Sensor';
        config['password1']='FriBox';
        WifiCnfCount=config['WifiCnfCount'];
        with open('wifi_config.json','w') as f:
            f.write(json.dumps(config)); # 将字典序列化为json字符串,存入wifi_config.json        
        print(' # >> Network >> ERR : WiFi config file does not exist ! ');
        print(' # >> Network >> Create WiFi config file OK ! ');
    print(' # >> Network >> Load WiFi config : wifi_config.json .');
    #print(config); #调试输出Wifi配置信息
    #以下为正常的WIFI连接流程        
    wifi = network.WLAN(network.STA_IF);
    if not wifi.isconnected(): 
        WifiCnfCount=config['WifiCnfCount'];
        print(' # >> Network >> WiFi Config Count is '+str(WifiCnfCount)+' .');
        wifi.active(True)
        print(' # >> Network >> Connecting to Network . . .');
        for i in range(WifiCnfCount+1):
            if i==0: continue;
            print(' # >> Network >> Try WiFi Config '+str(i)+' .');
            try:    
                wifi.connect(config['essid'+str(i)], config['password'+str(i)]);
                for i in range(40):
                    #尝试连接WIFI热点'
                    #print('.');
                    if wifi.isconnected(): break;
                    utime.sleep_ms(150);
            except:
                pass;
            if wifi.isconnected(): break;
            #有配置可用就不在尝试后续配置
        if not wifi.isconnected():
            if FirstWifi!=0:
                wifi.active(False);
                utime.sleep_ms(150);
                wifi.active(True);
                utime.sleep_ms(150);
                WifiConn=wifi.isconnected();
                return WifiConn;
            wifi.active(False) #关掉连接,免得repl死循环输出
            print(' # >> Network >> ERR : Wifi Connection Error, Please Config Wifi ! ');
            essid = '';
            password = '';
            essid = input('wifi name:'); # 输入essid
            password = input('wifi passwrod:'); # 输入password
            if len(essid) != 0 and len(password) != 0:
                WifiCnfCount=WifiCnfCount+1;
                config['WifiCnfCount']=WifiCnfCount;
                config['essid'+str(WifiCnfCount)]=essid;
                config['password'+str(WifiCnfCount)]=password;
                with open('wifi_config.json','w') as f:
                    f.write(json.dumps(config)); # 将字典序列化为json字符串,存入wifi_config.json
                print(' # >> Network >> WifiConfig >> Write WifiConfig File .');
                print(config);
            else:
                print(' # >> Network >> ERR : Please Input Right WIFI ! ');
            do_connect(); # 重新连接
        if wifi.isconnected():
            print(' # >> Network >> Config :', wifi.ifconfig());
            print(' # >> Network >> Wifi Connected .');
        utime.sleep_ms(150);
        WifiConn=wifi.isconnected();
    return WifiConn;

def Get_DateTime(inTimeZone=+8):
    #获取系统时间字符串
    global HD_Date;
    global HD_Time;
    global HD_DateTime;    
    global HD_Week;
    global HD_WeekZH;
    xWeekList=( 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday' )
    xWeekListZH=( '星期一','星期二','星期三','星期四','星期五','星期六','星期日' )
    xTimeVar=utime.localtime(utime.mktime(utime.localtime()) + int(inTimeZone)*3600);
    HD_Date='%04d-%02d-%02d' % ( xTimeVar[0],xTimeVar[1],xTimeVar[2] );
    HD_Time='%02d:%02d:%02d' % ( xTimeVar[3],xTimeVar[4],xTimeVar[5] );
    HD_DateTime=HD_Date+' '+HD_Time;
    xStrWeek1='W%d' % ( xTimeVar[6]+1 );
    HD_Week=xWeekList[xTimeVar[6]];
    HD_WeekZH=xWeekListZH[xTimeVar[6]];
    return HD_DateTime+' '+HD_Week,HD_DateTime,HD_Date,HD_Time,HD_Week,HD_WeekZH,xStrWeek1;

def read_PMS_line(InPort):
    #读取传感器串口数据
    tmpStr= b'';
    while True:
        tmpChr1 = InPort.read(1); #数据头1
        if tmpChr1 == b'\x42':
            tmpChr2 = InPort.read(1); #数据头2
            if tmpChr2 == b'\x4d':
                tmpStr = tmpStr+tmpChr1+tmpChr2;
                tmpStr = tmpStr+InPort.read(38); #剩余全部数据
                utime.sleep_us(100);
                InPort.any(); #清串口数据
                utime.sleep_us(100);
                return tmpStr;

def SyncDateTime():
    #同步NTP时间
    if WifiConn==True:
        try:
            print(' # >> NTP >> Ntp Client Sync DateTime ...');
            ntptimeTF=FB_NTP.NtpSync();
            print(' # >> NTP >> System DateTime is '+str(Get_DateTime()[0]) );
        except:
            ntptimeTF=False;
        if ntptimeTF==False : print(' # >> NTP >> ERR : Ntp Client Sync DateTime ! ');
    return str(Get_DateTime()[0]);

#PMS5003ST -- 攀藤颗粒物甲醛温湿度传感器  /  颗粒物 甲醛 温湿度
global uartPMS; # PMS5003ST
PMS_Rst.value(1); # 复位传感器完成
#连接传感器
uartPMS = UART(1, baudrate=9600, parity=None,rx=23,tx=22,timeout=10);
utime.sleep_ms(150); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#[Begin]
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#连接Wifi
do_connect();
P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

if wifi.isconnected():FirstWifi=1;
SyncDateTime(); #同步NTP
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#剩余进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#切换到数据首页
uartHMI.write(b"page 1"); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); #切换至主页面
wPage=1;

#系统开始运行
while True:
    start = time.ticks_ms() # 获取毫秒计数器
    try:
        if not wifi.isconnected():
            utime.sleep_ms(150);
            do_connect(); #连接wifi
    except:
        pass;

    #循环主代码开始 >>>>>>>>
    wCount=wCount+1;
    #更新时间和日期
    utime.sleep_ms(50);
    vSJ='"'+str(Get_DateTime()[3])+'"';
    vRQz=str(Get_DateTime()[2]);
    vRQ='"'+vRQz.split("-")[0]+'年'+vRQz.split("-")[1]+'月'+vRQz.split("-")[2]+'日 '+str(Get_DateTime()[5])+'"';
    uartHMI.write(b'tFSJ.txt='+vSJ); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
    uartHMI.write(b'tFRQ.txt='+vRQ); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");#更新日期
    print(' # >> Run >> Time : '+str(Get_DateTime()[1])+' '+str(Get_DateTime()[6]));

    #处理页面信息
    vHMIStr=uartHMI.readline();
    if vHMIStr==b'SyncDateTime' :
        print(' # >> System >> SyncDateTime . . .');
        uartHMI.write(b'tFSJ.txt="??:??:??"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
        if wifi.isconnected():FirstWifi=1;
        SyncDateTime(); #同步NTP
        uartHMI.write(b'tFSJ.txt='+'"'+str(Get_DateTime()[3])+'"' ); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
    if vHMIStr==b'Restart' :
        print(' # >> System >> Restart . . .');
        machine.reset();#重启自己
    if vHMIStr==b'page 0' :
        print(' # >> HMI >> Page 0 .');
        wPage=0; wCount=2;
    if vHMIStr==b'page 1' :
        print(' # >> HMI >> Page 1 .');
        wPage=1; wCount=2;
    if vHMIStr==b'page 2' :
        print(' # >> HMI >> Page 2 .');
        wPage=2; wCount=2;
    if vHMIStr==b'page 3' :
        print(' # >> HMI >> Page 3 .');
        wPage=3; wCount=2;
    if vHMIStr==b'page 4' :
        print(' # >> HMI >> Page 4 Setup .');
        wPage=4; wCount=2;
    uartHMI.any();
    
    #2秒执行一次
    if wCount>=2:
        #读取PMS5003ST数据
        PMS_Data=read_PMS_line(uartPMS);
        PMS_Data_Frame = struct.unpack(">hhhhhhhhhhhhhhhh", bytes(PMS_Data[4:]))
        PMSData['PM1.0CF']="{:.2f}".format(PMS_Data_Frame[0]);
        PMSData['PM2.5CF']="{:.2f}".format(PMS_Data_Frame[1]);
        PMSData['PM10CF']="{:.2f}".format(PMS_Data_Frame[2]);
        PMSData['PM1.0']="{:.2f}".format(PMS_Data_Frame[3]);
        PMSData['PM2.5']="{:.2f}".format(PMS_Data_Frame[4]);
        PMSData['PM10']="{:.2f}".format(PMS_Data_Frame[5]);
        PMSData['GTR0.3um']="{:.2f}".format(PMS_Data_Frame[6]);
        PMSData['GTR0.5um']="{:.2f}".format(PMS_Data_Frame[7]);
        PMSData['GTR1.0um']="{:.2f}".format(PMS_Data_Frame[8]);
        PMSData['GTR2.5um']="{:.2f}".format(PMS_Data_Frame[9]);
        PMSData['GTR5.0um']="{:.2f}".format(PMS_Data_Frame[10]);
        PMSData['GTR10um']="{:.2f}".format(PMS_Data_Frame[11]);
        PMSData['HCHO']="{:.3f}".format(PMS_Data_Frame[12]/1000.0);
        PMSData['Temperature']="{:.1f}".format(PMS_Data_Frame[13]/10.0+TC);#加补偿温度
        PMSData['Humidity']="{:.1f}".format(PMS_Data_Frame[14]/10.0);
        PM25=PMS_Data_Frame[1]+0.00; #PM2.5
        HCHO=PMS_Data_Frame[12]/1000.0+0.000; #HCHO
        #计算曲线值 - PM2.5
        tmpPM25=PM25;
        if tmpPM25>300 : tmpPM25=300;
        bltmpPM25=int(round(tmpPM25/300*255,0));
        if bltmpPM25>255 : bltmpPM25=255;
        PMSData['PM2.5QX']=bltmpPM25;
        #计算曲线值 - HCHO
        tmpHCHO=HCHO;
        if tmpHCHO>0.8 : tmpHCHO=0.8;
        bltmpHCHO=int(round(tmpHCHO/0.8*255,0));
        if bltmpHCHO>255 : bltmpHCHO=255;
        PMSData['HCHOQX']=bltmpHCHO;
        print(' # >> Sensor >> Data : '+str(PMSData));
        #读取传感器完成

        #显示页面信息
        if wPage==1:
            uartHMI.write(b'tFB25.txt="'+PMSData['PM2.5CF']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tFBHCHO.txt="'+PMSData['HCHO']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tFBT.txt="'+PMSData['Temperature']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tFBH.txt="'+PMSData['Humidity']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            #2016,65504,64644,64324,63780,59392 // 颜色变量，绿、黄、橙色、深橙色、红、深红
            #PM2.5
            if PM25<=35 :
                uartHMI.write(b'tFB25T.txt="(优)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=2016'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif PM25>35 and PM25<=75 :
                uartHMI.write(b'tFB25T.txt="(良)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=65504'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif PM25>75 and PM25<=115 :
                uartHMI.write(b'tFB25T.txt="(轻度污染)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=64644'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif PM25>115 and PM25<=150 :
                uartHMI.write(b'tFB25T.txt="(中度污染)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=64324'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif PM25>150 and PM25<=250 :
                uartHMI.write(b'tFB25T.txt="(重度污染)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=63780'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif PM25>250 :
                uartHMI.write(b'tFB25T.txt="(严重污染)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=59392'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            else :
                uartHMI.write(b'tFB25T.txt="(未知)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFB25T.pco=65535'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            #HCHO
            if HCHO<=0.024 :
                uartHMI.write(b'tFBHCHOT.txt="(非常安全)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=34784'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif HCHO>0.024 and HCHO<=0.06 :
                uartHMI.write(b'tFBHCHOT.txt="(安全)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=2016'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif HCHO>0.06 and HCHO<=0.08 :
                uartHMI.write(b'tFBHCHOT.txt="(符合标准)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=65504'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif HCHO>0.08 and HCHO<=0.15 :
                uartHMI.write(b'tFBHCHOT.txt="(超出标准)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=64644'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif HCHO>0.15 and HCHO<=0.2 :
                uartHMI.write(b'tFBHCHOT.txt="(略有风险)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=64324'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif HCHO>0.2 and HCHO<=0.5 :
                uartHMI.write(b'tFBHCHOT.txt="(不安全)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=63780'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            elif HCHO>0.5 :
                uartHMI.write(b'tFBHCHOT.txt="(很不安全)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=59392'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            else :
                uartHMI.write(b'tFBHCHOT.txt="(未知)"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'tFBHCHOT.pco=65535'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
        elif wPage==2:
            pass;
        elif wPage==3:
            uartHMI.write(b'tFB2.txt="'+PMSData['PM2.5CF']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'add 12,0,'+str(PMSData['PM2.5QX'])); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tFB4.txt="'+PMSData['HCHO']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'add 13,0,'+str(PMSData['HCHOQX'])); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
        wCount=0;
        #页面信息显示完成
        
    #延时
    utime.sleep_ms(100);

    #循环主代码结束 <<<<<<<<
    delta = time.ticks_diff(time.ticks_ms(), start) #计算时间差
    if 1000-delta>=0: utime.sleep_ms(1000-delta); #延时补偿至1秒
    #取消以下2行注释可调试输出每次执行的确切毫秒数
    #delta = time.ticks_diff(time.ticks_ms(), start) # 计算时间差
    #print(' # >> Run >> Process execution time: '+str(delta)+'ms' );
    #break;
pass;
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#[End]
