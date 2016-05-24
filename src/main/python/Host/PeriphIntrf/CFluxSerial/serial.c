/*
 * serial1.c
 *
 *  Created on: Jan 8, 2011
 *      Author: stan
 */
#include <windows.h>
#include <stdio.h>

void printError() {
    char lastError[1024];
    FormatMessage(
            FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
            NULL,
            GetLastError(),
            MAKELANGID(LANG_NEUTRAL,SUBLANG_DEFAULT),
            lastError,
            1024,
            NULL);
    printf("%s\n",lastError);
}

long long getTimestamp() {
    /* Get 64 bit millisecond timestamp */
    /*
     * typedef struct _FILETIME {
          DWORD dwLowDateTime;
          DWORD dwHighDateTime;
        } FILETIME, *PFILETIME;
     *
     */
    ULARGE_INTEGER ts;
    FILETIME fileTime;
    GetSystemTimeAsFileTime(&fileTime);
    ts.LowPart = fileTime.dwLowDateTime;
    ts.HighPart = fileTime.dwHighDateTime;
    // Compensate for Jan 1, 1601 origin of FILETIME
    return ts.QuadPart/10000LL + 50491123200000LL;
}

HANDLE makeSerial(char *portName)
{
    HANDLE hSerial;
    DCB dcbSerialParams = {0};
    COMMTIMEOUTS timeouts = {0};

    hSerial = CreateFile(portName,GENERIC_READ | GENERIC_WRITE,0,0,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,0);
    if (INVALID_HANDLE_VALUE == hSerial) {
        if (ERROR_FILE_NOT_FOUND == GetLastError()) {
            printf("Serial port %s does not exist.\n",portName);
            printError();
            return NULL;
        }
        printf("Serial port cannot be opened.\n");
        printError();
        return NULL;
    }
    dcbSerialParams.DCBlength = sizeof(dcbSerialParams);
    if (!GetCommState(hSerial,&dcbSerialParams)) {
        printf("Error getting state.\n");
        printError();
        return NULL;
    }
    dcbSerialParams.BaudRate = CBR_57600;
    dcbSerialParams.ByteSize = 8;
    dcbSerialParams.StopBits = ONESTOPBIT;
    dcbSerialParams.Parity = NOPARITY;
    dcbSerialParams.fAbortOnError = 0;

    if (!SetCommState(hSerial,&dcbSerialParams)) {
        printf("Error setting state.\n");
        printError();
        return NULL;
    }

    timeouts.ReadIntervalTimeout = MAXDWORD;
    timeouts.ReadTotalTimeoutConstant = 0;
    timeouts.ReadTotalTimeoutMultiplier = 0;
    timeouts.WriteTotalTimeoutConstant = 50;
    timeouts.WriteTotalTimeoutMultiplier= 10;

    if (!SetCommTimeouts(hSerial,&timeouts)) {
        printf("Error setting timeouts.\n");
        printError();
        return NULL;
    }

    return hSerial;
}

#define MAXPORTS (4)
#define BUFFSIZE (256)
int main(int argc, char *argv[])
{
    char szBuff[MAXPORTS][BUFFSIZE];
    DWORD dwBytesRead = 0;
    int i, j, n = BUFFSIZE;
    long long start;
    FILE *fp[MAXPORTS];
    /*
     * typedef struct _SYSTEMTIME {
          WORD wYear;
          WORD wMonth;
          WORD wDayOfWeek;
          WORD wDay;
          WORD wHour;
          WORD wMinute;
          WORD wSecond;
          WORD wMilliseconds;
        } SYSTEMTIME, *PSYSTEMTIME;
     *
     */
    SYSTEMTIME systemTime;
    HANDLE h[MAXPORTS];

    h[0] = makeSerial("\\\\.\\COM9");
    h[1] = makeSerial("\\\\.\\COM10");
    h[2] = makeSerial("\\\\.\\COM11");
    h[3] = makeSerial("\\\\.\\COM12");

    // Read up to 256 bytes from the serial port

    GetSystemTime(&systemTime);

    start = getTimestamp();
    fp[0] = fopen("c:\\temp\\capture4a.txt","w");
    fp[1] = fopen("c:\\temp\\capture4b.txt","w");
    fp[2] = fopen("c:\\temp\\capture4c.txt","w");
    fp[3] = fopen("c:\\temp\\capture4d.txt","w");

    while (getTimestamp()-start < 12*3600*1000) {
        for (j=0; j<MAXPORTS; j++) {
            if (!ReadFile(h[j],szBuff[j],n,&dwBytesRead,NULL)) {
                printf("Error in ReadFile.\n");
                printError();
                return -1;
            }
            for (i=0;i<dwBytesRead;i++){
                if (szBuff[j][i] == 13) fprintf(fp[j],"%I64d\n",getTimestamp());
            }
        }
        Sleep(10);
    }

    printf("%4d%02d%02dT%02d%02d%02d.%03d\n",
            systemTime.wYear,
            systemTime.wMonth,
            systemTime.wDay,
            systemTime.wHour,
            systemTime.wMinute,
            systemTime.wSecond,
            systemTime.wMilliseconds);
    printf("%I64d\n",getTimestamp());
    for (j=0; j<MAXPORTS; j++) {
        CloseHandle(h[j]);
        fclose(fp[j]);
    }
    return 0;
}
