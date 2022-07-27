#coding=UTF-8

# FriBox Air Sensor v1.1.0
# Create by Stream.Wang 2022-06-22
# Modify by Stream.Wang 2022-07-23

#引入基本库
import sys,os,utime,json,network,hmac,math,time,datetime,machine;
import ustruct as struct
from machine import UART,Pin, I2C;
#引入扩展库
import FB_NTP; #NTP库

#系统全局变量
global SysConfig; #系统配置
#wifi全局变量
global WifiEnable; #是否开启Wifi，0为不启用，1为启用；
global ap; #AP模式连接
global wifi; #wifi连接
global WifiConn; #wifi连接状态
global essid; #wifi SSID
global password; #wifi Pass
global WifiCnfCount; #Wifi配置序列的个数
global FirstWifi; #wifi初始化状态
#硬件相关全局变量
global HDName; #系统名称
global HDVer; #系统版本号
global HDAPName; #系统AP名称
global HWHID; #硬件ID
#时间日期相关全局变量
global HD_Date; #系统日期
global HD_Time; #系统时间
global HD_DateTime; #系统日期时间
global HD_Week; #系统星期
global HD_WeekZH; #系统星期中文
global TimeZone; #时区，默认为+8；
global SetDTTF; #设置日期和时间开关，切换到设置页面更新一次时间，然后马上设置SetDTTF=1，这样不会每秒更新，即只在切换到设置页面时更新一次；
#其他相关全局变量
global HMIBrightness; #屏幕亮度
global DebugTF; #是否输出调试信息，0为不显示调试信息，1为显示调试信息；

#初始化变量
DebugTF=0; #是否输出调试信息，0为不显示调试信息，1为显示调试信息；
HDName='FriBox Air Sensor'; #系统名称
HDVer='v0.99b'; #系统版本号
HDAPName='FriBox-AirSensor'; #系统AP名称
SysConfig={}; #系统配置信息
WifiEnable=0; #启用Wifi开关，0为不启用，1为启用。
WifiCnfCount=-1; #Wifi配置序列的个数
FirstWifi=0; #wifi初始化状态
TimeZone=+8; #时区，默认为+8；
HMIBrightness=90; #屏幕亮度，默认为 90 ；
SetDTTF=0; #设置日期和时间开关
sys.path.append('examples'); # 添加路径
print(' # >> System >> Initializing . . .');

#wCount 内部计数器，用于每2秒读取一次传感器信息；
global wCount;
wCount=0;
#wSyncDateTime 同步时间计数器，计数到一定值就同步一次时间；
global wSyncDateTime;
wSyncDateTime=0;
#wPage 屏幕页面计数器，记录当前在屏幕第几页；
global wPage;
wPage=0;
#初始化时间，+8时区时时间初始化为 2022-01-01 08:00:00 ；
machine.RTC().datetime(( 2022 , 1 , 1 , 5 , 0 , 0 , 0 , 0 ));

def ReadConfig(inFileName='Config.json'): 
    #读取系统配置信息
    global HMIBrightness;
    global WifiEnable;
    try:
        with open(inFileName,'r') as f: 
            vConfig = json.loads(f.read());
            f.close();
            print(' # >> System >> Read System Config file OK ! ');
            try:
                HMIBrightness=int(vConfig['Brightness']); #获取屏幕亮度
            except:
                HMIBrightness=90;
            try:
                WifiEnable=int(vConfig['WifiEnable']); #获取是否启用Wifi
            except:
                WifiEnable=0;
    except:
        #若初次运行,则将进入excpet,执行配置文件的创建
        print(' # >> System >> ERR : System config file does not exist ! ');
        vConfig = {};
        vConfig['Brightness']=int(HMIBrightness);
        HMIBrightness=int(vConfig['Brightness']); #获取屏幕亮度
        vConfig['WifiEnable']=int(WifiEnable);
        WifiEnable=int(vConfig['WifiEnable']); #获取是否启用Wifi
        vConfig['WifiCnfCount']=1;
        vConfig['essid1']='FirBox-IOT';
        vConfig['password1']='FriBox-AirSensor';
        with open(inFileName,'w') as f:
            f.write(json.dumps(vConfig)); #将字典序列化为json字符串,存入Config.json
            f.close();
        print(' # >> System >> Create System config file OK ! ');
    return vConfig;

def SaveConfig(inFileName='Config.json'): 
    #保存系统配置信息
    global HMIBrightness;
    global WifiEnable;
    vHMIBrightness=HMIBrightness;
    vWifiEnable=WifiEnable;
    vConfig=ReadConfig(inFileName);
    HMIBrightness=vHMIBrightness;
    WifiEnable=vWifiEnable;
    vConfig['Brightness']=int(HMIBrightness);
    vConfig['WifiEnable']=int(WifiEnable);
    with open(inFileName,'w') as f:
        f.write(json.dumps(vConfig)); #将字典序列化为json字符串,存入Config.json
        f.close();
    print(' # >> System >> Save System config file OK ! ');
    return vConfig;

#读取配置文件
SysConfig=ReadConfig(); #默认配置文件名为 Config.json
print(' # >> System >> Config.Brightness ['+str(HMIBrightness)+']');
print(' # >> System >> Config.WifiEnable ['+str(WifiEnable)+']');

#PMS5003ST 复位传感器
PMS_Rst=Pin(21, Pin.OUT);
PMS_Rst.value(0);
global PMSData;
PMSData= dict();
PMSData['PM1.0CF']='0.00'; PMSData['PM2.5CF']='0.00'; PMSData['PM10CF']='0.00';
PMSData['PM1.0']='0.00'; PMSData['PM2.5']='0.00'; PMSData['PM10']='0.00';
PMSData['GTR0.3um']='0.00'; PMSData['GTR0.5um']='0.00'; PMSData['GTR1.0um']='0.00'; PMSData['GTR2.5um']='0.00'; PMSData['GTR5.0um']='0.00'; PMSData['GTR10um']='0.00';
PMSData['HCHO']='0.000'; PMSData['Temperature']='00.0'; PMSData['Humidity']='00..0';
PMSData['PM2.5QX']=0; PMSData['HCHOQX']=0.000;
global PM25;
PM25=0.00;
global HCHO;
HCHO=0.000;
global TC; #补偿温度，由于传感器内部气流，可能导致温度检测值低于实际温度，估添加补偿值。
TC=+1.8; #补偿温度

#TJC4832T035_011 -- 串口触摸屏  /  inch:3.5(320X480) Flash:16M RAM:3584B Frequency:48M
global uartHMI; # TJC4832T035_011
uartHMI = UART(2, baudrate=115200, rx=26,tx=25,timeout=10);
uartHMI.write(b"rest"); # 发送串口屏命令
utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 发送结束符
utime.sleep_ms(500);
uartHMI.write(b'dims='+str(HMIBrightness)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
uartHMI.write(b'dim='+str(HMIBrightness)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");

#切换至启动页面
uartHMI.write(b"page Main01"); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
utime.sleep_ms(150);
#进度条百分数值
global P0VAR1;
P0VAR1=0; utime.sleep_ms(350); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#获取MAC地址
sta_if = network.WLAN(network.STA_IF);
s = sta_if.config('mac');
DivMac = ('%02x%02x%02x%02x%02x%02x') %(s[0],s[1],s[2],s[3],s[4],s[5]);
DivMac = str(DivMac).upper();
HWHID='FBAS'+DivMac;
print(' # >> System >> Hardware HID is ['+HWHID+']');
utime.sleep_ms(350); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#初始化AP模式，等待客户端连入配置本设备
if WifiEnable==1:
    ap = network.WLAN(network.AP_IF);
    ap.config(essid=HDAPName+'-'+HWHID,authmode=network.AUTH_WPA_WPA2_PSK, password="20121221");
    ap.ifconfig(('192.168.199.1','255.255.255.0','192.168.199.1','1.1.1.1'));
    ap.active(True);
    print(' # >> Network >> AP mode started , Name is '+HDAPName+'-'+HWHID);
P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#初始化完成  ================

def do_connect():
    #链接wifi
    global SysConfig; #系统配置信息
    global FirstWifi;
    global WifiEnable;
    global WifiCnfCount;
    global wifi; #wifi连接
    global WifiConn; #wifi连接状态
    global essid; #wifi SSID
    global password; #wifi Pass
    #开始处理Wifi连接
    if WifiEnable==0 : return False; #不启用Wifi就退出，不链接；
    wifi = network.WLAN(network.STA_IF);
    if not wifi.isconnected(): 
        WifiCnfCount=int( SysConfig['WifiCnfCount'] );
        print(' # >> Network >> WiFi Config Count is '+str(WifiCnfCount)+' .');
        wifi.active(True)
        print(' # >> Network >> Connecting to Network . . .');
        for i in range(WifiCnfCount+1):
            if i==0: continue;
            print(' # >> Network >> Try WiFi Config '+str(i)+' : SSID='+SysConfig['essid'+str(i)]+' , PassWord= '+SysConfig['password'+str(i)]+' .');
            try:    
                wifi.connect(SysConfig['essid'+str(i)], SysConfig['password'+str(i)]);
                for i in range(40):
                    #尝试连接WIFI热点'
                    #print('.');
                    if wifi.isconnected(): break;
                    utime.sleep_ms(150);
            except:
                print(' # >> Network >> Network Connection Error ! ');
                utime.sleep_ms(150);
                wifi.disconnect();#链接失败后要关闭一下连接
                pass;
            if wifi.isconnected(): break;
            #有配置可用就不在尝试后续配置
        if wifi.isconnected():
            print(' # >> Network >> Config :', wifi.ifconfig());
            print(' # >> Network >> Wifi Connected .');
            WifiEnable=1;
            FirstWifi=1;
        else :
            WifiEnable=0;
            print(' # >> Network >> ERR : Wifi Connection Error, Please Config Wifi ! ');
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
    global TimeZone;
    if WifiEnable==0 : return str(Get_DateTime(TimeZone)[0]);
    #同步NTP时间
    if WifiConn==True:
        try:
            print(' # >> NTP >> Ntp Client Sync DateTime ...');
            ntptimeTF=FB_NTP.NtpSync();
            print(' # >> NTP >> System DateTime is '+str(Get_DateTime(TimeZone)[0]) );
        except:
            ntptimeTF=False;
        if ntptimeTF==False : print(' # >> NTP >> ERR : Ntp Client Sync DateTime ! ');
    return str(Get_DateTime(TimeZone)[0]);

#PMS5003ST -- 攀藤颗粒物甲醛温湿度传感器  /  颗粒物 甲醛 温湿度
global uartPMS; # PMS5003ST
PMS_Rst.value(1); # 复位传感器完成
#连接传感器
uartPMS = UART(1, baudrate=9600, parity=None,rx=23,tx=22,timeout=10);
utime.sleep_ms(150); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#[Begin]
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#连接Wifi
if WifiEnable==1 : do_connect();
P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
if WifiEnable==1 : SyncDateTime(); #同步NTP
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#剩余进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条
utime.sleep_ms(100); P0VAR1=P0VAR1+10; uartHMI.write(b"VAR1.val="+str(P0VAR1)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新进度条

#切换到数据首页
uartHMI.write(b"page Main02"); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); #切换至主页面
wPage=1;

#系统开始运行
while True:
    start = time.ticks_ms() # 获取毫秒计数器

    #循环主代码开始 >>>>>>>>
    wCount=wCount+1;
    wSyncDateTime=wSyncDateTime+1;

    #刷新时间和日期显示
    utime.sleep_ms(50);
    vSJ='"'+str(Get_DateTime(TimeZone)[3])+'"';
    vRQz=str(Get_DateTime(TimeZone)[2]);
    vRQ='"'+vRQz.split("-")[0]+'年'+vRQz.split("-")[1]+'月'+vRQz.split("-")[2]+'日 '+str(Get_DateTime(TimeZone)[5])+'"';
    uartHMI.write(b'tFSJ.txt='+vSJ); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
    uartHMI.write(b'tFRQ.txt='+vRQ); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");#更新日期
    if DebugTF==1: print(' # >> Run >> Time : '+str(Get_DateTime(TimeZone)[1])+' '+str(Get_DateTime(TimeZone)[6]));

    #处理HMI屏幕反馈信息
    vHMIStr=uartHMI.readline();
    try:
        vHMIStrTemp=vHMIStr.decode("utf-8").strip();
        if DebugTF==1: print(' # >> Run >> Uart HMI : '+vHMIStrTemp);
    except :
        vHMIStrTemp='[Uart HMI Error]';
    if vHMIStr==b'SyncDateTime' :
        #同步NTP时间
        if WifiEnable==1 : 
            print(' # >> System >> SyncDateTime . . .');
            uartHMI.write(b'tFSJ.txt="??:??:??"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
            SyncDateTime(); #同步NTP
        else :
            uartHMI.write(b'tFSJ.txt="**:**:**"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
            utime.sleep_ms(50);
        uartHMI.write(b'tFSJ.txt='+'"'+str(Get_DateTime(TimeZone)[3])+'"' ); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
    elif vHMIStr==b'Restart' :
        #重启
        uartHMI.write(b'page Restart'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff"); # 更新时间
        SaveConfig();
        utime.sleep_ms(1024);
        print(' # >> System >> Restart . . .');
        machine.reset();#重启
    elif vHMIStr==b'page 0' :
        #启动进度页
        print(' # >> HMI >> Page 0 .');
        wPage=0; wCount=2;
    elif vHMIStr==b'page 1' :
        #系统首页
        print(' # >> HMI >> Page 1 .');
        wPage=1; wCount=2;
    elif vHMIStr==b'page 2' :
        #颗粒物详细页
        print(' # >> HMI >> Page 2 .');
        wPage=2; wCount=2;
    elif vHMIStr==b'page 3' :
        #数值坐标图页
        print(' # >> HMI >> Page 3 .');
        wPage=3; wCount=2;
    elif vHMIStr==b'page 4' :
        #设置页
        print(' # >> HMI >> Page 4 Setup .');
        SetDTTF=1;
        wPage=4; wCount=2;
    elif vHMIStrTemp[0:12]=='SetDateTime ' :
        #设置日期和时间
        print(' # >> Setup >> SetDateTime : '+vHMIStrTemp[12:]+' .');
        #输入日期
        vTmpD=vHMIStrTemp.split()[1].strip();
        vTmpT=vHMIStrTemp.split()[2].strip();
        vTmpD_Y=int(vTmpD.split('-')[0]);
        vTmpD_M=int(vTmpD.split('-')[1]);
        vTmpD_D=int(vTmpD.split('-')[2]);
        #检查2月最大天数
        if vTmpD_M==2 : 
            vTmpD_Dx=datetime.date(vTmpD_Y,3,1)-datetime.timedelta(days=1);
            vTmpD_Dx=vTmpD_Dx.day;
            if vTmpD_D>vTmpD_Dx : vTmpD_D=vTmpD_Dx
        #检查是否有31号
        if vTmpD_D>=31:
            if vTmpD_M==4 or vTmpD_M==6 or vTmpD_M==9 or vTmpD_M==11 : vTmpD_D=30;
        #输入时间
        vTmpT_H=int(vTmpT.split(':')[0]);
        vTmpT_M=int(vTmpT.split(':')[1]);
        vTmpT_S=int(vTmpT.split(':')[2]);
        vTmpDTtz=datetime.datetime(vTmpD_Y, vTmpD_M, vTmpD_D,vTmpT_H,vTmpT_M,vTmpT_S);
        vTmpDTtz=vTmpDTtz-datetime.timedelta(hours=TimeZone);
        #设置日期和时间
        machine.RTC().datetime(( int( vTmpDTtz.year ) , int( vTmpDTtz.month ) , int( vTmpDTtz.day ) , int( vTmpDTtz.weekday() ) , int( vTmpDTtz.hour ) , int( vTmpDTtz.minute ) , int( vTmpDTtz.second ) , 0 ));
    elif vHMIStr==b'Wifi=OFF' :
        #禁用Wifi
        print(' # >> Setup >> Set Wifi = OFF .');
        if WifiEnable==1 : 
            WifiEnable=0;
            uartHMI.write(b'page Restart'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            SaveConfig();
            utime.sleep_ms(1024);
            print(' # >> System >> Restart . . .');
            machine.reset();#重启
    elif vHMIStr==b'Wifi=ON' :
        #启用Wifi
        print(' # >> Setup >> Set Wifi = ON .');
        if WifiEnable==0 : 
            WifiEnable=1;
            uartHMI.write(b'page Restart'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            SaveConfig();
            utime.sleep_ms(1024);
            print(' # >> System >> Restart . . .');
            machine.reset();#重启自己
    elif vHMIStrTemp[0:14]=='SetBrightness ' :
        #更新屏幕亮度
        vTmpD=vHMIStrTemp.split()[1].strip();
        HMIBrightness=int(vTmpD);
        #SaveConfig();
        print(' # >> Setup >> Set Brightness = '+str(HMIBrightness)+' .');
    else :
        #其他未知命令
        uartHMI.any();
    
    #每6小时同步一次时间
    if wSyncDateTime>=21600 :
        if WifiEnable==1 : SyncDateTime(); #同步NTP
        wSyncDateTime=0;

    #每2秒执行一次获取传感器数据
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
        PMSData['GTR0.3um']="{:.0f}".format(PMS_Data_Frame[6]);
        PMSData['GTR0.5um']="{:.0f}".format(PMS_Data_Frame[7]);
        PMSData['GTR1.0um']="{:.0f}".format(PMS_Data_Frame[8]);
        PMSData['GTR2.5um']="{:.0f}".format(PMS_Data_Frame[9]);
        PMSData['GTR5.0um']="{:.0f}".format(PMS_Data_Frame[10]);
        PMSData['GTR10um']="{:.0f}".format(PMS_Data_Frame[11]);
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
        if DebugTF==1: print(' # >> Sensor >> Data : '+str(PMSData));
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
            uartHMI.write(b'tPM1_0CF.txt="'+PMSData['PM1.0CF']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPM2_5CF.txt="'+PMSData['PM2.5CF']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPM10CF.txt="'+PMSData['PM10CF']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPM1_0.txt="'+PMSData['PM1.0']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPM2_5.txt="'+PMSData['PM2.5']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPM10.txt="'+PMSData['PM10']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPMS03.txt="'+PMSData['GTR0.3um']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPMS05.txt="'+PMSData['GTR0.5um']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPMS10.txt="'+PMSData['GTR1.0um']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPMS25.txt="'+PMSData['GTR2.5um']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPMS50.txt="'+PMSData['GTR5.0um']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tPMS100.txt="'+PMSData['GTR10um']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
        elif wPage==3:
            uartHMI.write(b'tFB2.txt="'+PMSData['PM2.5CF']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'add 12,0,'+str(PMSData['PM2.5QX'])); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'tFB4.txt="'+PMSData['HCHO']+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
            uartHMI.write(b'add 13,0,'+str(PMSData['HCHOQX'])); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
        elif wPage==4:
            if SetDTTF==1:
                xTimeVar=utime.localtime(utime.mktime(utime.localtime()) + int(TimeZone)*3600);
                uartHMI.write(b'vH.val='+str(int(xTimeVar[3]))); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'vM.val='+str(int(xTimeVar[4]))); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'vS.val='+str(int(xTimeVar[5]))); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'vYear.val='+str(int(xTimeVar[0]))); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'vMonth.val='+str(int(xTimeVar[1]))); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'vDay.val='+str(int(xTimeVar[2]))); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'dims='+str(HMIBrightness)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'dim='+str(HMIBrightness)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'ValLD.val='+str(HMIBrightness)); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                uartHMI.write(b'ValLDTXT.txt="'+str(HMIBrightness)+'"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                if WifiEnable==1 : 
                    uartHMI.write(b'vWifi.txt="WiFi启用中"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                else :
                    uartHMI.write(b'vWifi.txt="WiFi已禁用"'); utime.sleep_us(2); uartHMI.write(b"\xff\xff\xff");
                SetDTTF=0;
        wCount=0;
        #页面信息显示完成
        
    #延时
    utime.sleep_ms(100);

    #循环主代码结束 <<<<<<<<
    delta = time.ticks_diff(time.ticks_ms(), start) #计算时间差
    if 1000-delta>=0: utime.sleep_ms(1000-delta); #延时补偿至1秒
    #取消以下2行注释可调试输出每次执行的确切毫秒数
    delta = time.ticks_diff(time.ticks_ms(), start) # 计算时间差
    if DebugTF==1: print(' # >> Run >> Process execution time: '+str(delta)+'ms' );
    #每秒循环执行完毕
pass;
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#[End]
