import utime,FB_Ntptime;

def NtpSync():
    NtpErrs=0;
    FB_NtptimeTF=False;
    while NtpErrs<10:
        try:
            utime.sleep_ms(480);
            FB_Ntptime.settime();
            print(' # >> NTP >> Sync DateTime',utime.localtime(utime.mktime(utime.localtime()) + 8*3600));
            FB_NtptimeTF=True
            utime.sleep_ms(10);
            break;
        except:
            FB_NtptimeTF=False
            print(' # >> NTP >> ERR : ',utime.localtime(utime.mktime(utime.localtime()) + 8*3600));
            NtpErrs=NtpErrs+1;
    return FB_NtptimeTF
