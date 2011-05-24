/*
 * serial2Socket.c
 *
 *  Reads from a collection of serial ports. When a \r is encountered, 
 *   all characters up to and including the \r are timestamped, labelled
 *   with the serial port identifier and sent via a TCP socket.
 */
#include <windows.h>
#include <winsock2.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "CuTest.h"
#include "ini.h"

#define MAXPORTS (4)
#define MAXDELIM (8)
#define NOHANDSHAKE (0)
#define HWHANDSHAKE (1)
#define SWHANDSHAKE (2)

#define IN_DATA_STATE (1)
#define IN_DELIM_STATE (2)

typedef struct
{
    char *portNames[MAXPORTS];
    int  portBaud[MAXPORTS];
    int  portStopBits[MAXPORTS];
    int  portParity[MAXPORTS];
    int  portHandshake[MAXPORTS];
    int  portBlocksize[MAXPORTS];
    char portDelim[MAXPORTS][MAXDELIM];
    int  portDelimBytes[MAXPORTS];
} configuration;

static void init_config(configuration *config)
// Set up sensible defaults for the serial ports
{
    int i;
    for (i=0;i<MAXPORTS;i++) {
        config->portNames[i] = 0;   // Null pointer indicates no port
        config->portBaud[i] = 9600;
        config->portStopBits[i] = 1;
        config->portParity[i] = NOPARITY;
        config->portHandshake[i] = NOHANDSHAKE;
        config->portBlocksize[i] = 0;
        config->portDelim[i][0] = '\r';
        config->portDelimBytes[i] = 1;
    }
}

/* The following queue structure uses a buffer of "size" bytes, but
   we are only allowed to place up to size-1 characters in it. As a result
   the head and tail pointers coincide iff the queue is empty. 
   We also want to be able to scan the characters in the queue for delimiters,
   starting from the position scanned so far(scan_limit), up to the position 
   of the tail. Since the scan_limit is never lower than the head, we do not
   run into the problem of having the tail lap the scan_limit pointer */
   
typedef struct queue {
    char *buffer;
    int size;
    int head;
    int tail;
    int count;
    int scan_limit;
    int drop;
    int state;
    int pos_in_block;
    int pos_in_delim;
} Queue;

struct header {
    unsigned short int id;
    long long timestamp;
    char port;
    unsigned short int nbytes;
} __attribute__ ((__packed__));

typedef struct header Header;

void Queue_init(Queue *q, int max_char)
{
    q->buffer = (char*) calloc(max_char+1,sizeof(char));
    q->size = max_char+1;
    q->head = q->tail = q->count = q->scan_limit = 0;
    q->drop = 1;
    q->state = IN_DELIM_STATE;
    q->pos_in_block = 0;
    q->pos_in_delim = 0;
}

void Queue_reset(Queue *q)
{
    q->head = q->tail = q->count = q->scan_limit = 0;
    q->drop = 1;
    q->state = IN_DELIM_STATE;
    q->pos_in_block = 0;
    q->pos_in_delim = 0;
}

void Queue_destroy(Queue *q)
{
    free(q->buffer);
    q->buffer = 0;
}

int Queue_put(Queue *q, char c)
/* Put character c onto queue. Returns number of characters put, i.e., 1 on succcess, 
    0 on failure */
{
    if (q->count >= q->size-1) return 0;
    q->buffer[q->tail++] = c;
    if (q->tail >= q->size) q->tail -= q->size;
    q->count++;
    return 1;
}

int Queue_get(Queue *q, char *cp)
/* Get character c from queue. Returns number of characters got, i.e., 1 on succcess, 
    0 on failure */
{
    if (q->count == 0) return 0;
    *cp = q->buffer[q->head++];
    if (q->head >= q->size) q->head -= q->size;
    q->count--;
    return 1;
}

int Queue_drop(Queue *q, int num_drop)
/* Drop num_drop characters from queue, return actual number dropped */
{
    int m;
    int n = min(num_drop,min(q->count,q->size-q->head));
    if (n>0) {
        q->head += n;
        if (q->head >= q->size) q->head -= q->size;
        q->count -= n;
    }
    m = min(q->count,num_drop-n);
    if (m>0) {
        q->head += m;
        if (q->head >= q->size) q->head -= q->size;
        q->count -= m;
    }
    return m+n;
}

int Queue_gets_simple(Queue *q, char *buf, int buflen)
/* Get up to buflen characters from the queue into buf. Returns number of characters 
    got */
{
    int n = 0;
    while (n<buflen) {
        if (!Queue_get(q,buf++)) break;
        n++;
    }
    return n;
}

int Queue_gets(Queue *q, char *buf, int buflen)
/* Get up to buflen characters from the queue into buf. Returns number of characters 
    got. Uses memmove to minimize looping. */
{
    int m;
    int n = min(buflen,min(q->count,q->size-q->head));
    if (n>0) {
        memmove(buf,q->buffer+q->head,n);
        q->head += n;
        if (q->head >= q->size) q->head -= q->size;
        q->count -= n;
    }
    m = min(q->count,buflen-n);
    if (m>0) {
        memmove(buf+n,q->buffer+q->head,m);
        q->head += m;
        if (q->head >= q->size) q->head -= q->size;
        q->count -= m;
    }
    return m+n;
}

int Queue_puts(Queue *q, char *buf, int buflen)
/* Puts up to buflen characters from buf. Returns number of characters put */
{
    int n = 0;
    while (n<buflen) {
        if (!Queue_put(q,*buf++)) break;
        n++;
    }
    return n;
}

int Queue_put_from(Queue *q, int maxchar, int (*source)(char *, int)) 
/* Puts up to maxchar characters onto the queue by calling the function 
    (*source)(char *s, int len) that fetches up to len characters into s
    and returns the number of characters obtained. The function may be
    called up to two times. Returns number of characters actually put
    onto the queue. If the source function returns a negative result, this
    is an error, which is immediately passed back to the caller */
{
    int k;
    // n is the maximum number of characters to put
    int n = min(maxchar,q->size-q->count-1);
    // m is the number that will not cause wrap-around
    int m = min(n,q->size-q->tail);
    if (m==0) return 0;
    k = (*source)(q->buffer+q->tail,m);
    if (k<0) return k; // Error return
    q->tail += k;
    if (q->tail >= q->size) q->tail -= q->size;
    q->count += k;
    if (k < m) return k;
    n -= m;
    if (n==0) return m;
    k = (*source)(q->buffer+q->tail,n);
    if (k<0) return k; // Error return
    q->tail += k;
    assert (q->tail < q->size);
    q->count += k;
    return k+m;
}    

int Queue_scan_limit_position(Queue *q)
/* Find number of characters between the head and the scan limit */
{
    return (q->scan_limit-q->head+q->size) % q->size;
}

static int Queue_scan_for_delim(Queue *q, char delim)
/* Scan from the current scan_limit towards the tail, stopping if a delim
    character is found. The scan_limit points after the position of the 
    delimiter or is set to the tail. A return value of 1 indicates the 
    delimiter was found, 0 indicates no delimiter is found and a -1 indicates
    that there is no delimiter and the queue is full. The last condition is an
    error since the queue will never be serviced. */
{
    int found = 0;
    while (!found && q->scan_limit != q->tail) {
        if (q->buffer[q->scan_limit++] == delim) found = 1;
        if (q->scan_limit >= q->size) q->scan_limit -= q->size;
    }
    if (!found && q->count == q->size-1) found = -1;
    return found;
}    

static int Queue_scan_for_delim_ex(Queue *q, int blocksize, char *delim, int ndelim)
/* Scan from the current scan_limit towards the tail, stopping if the delim
    character sequence of length ndelim is found. The scan_limit points after 
    the position of the delimiter or is set to the tail. A return value of 1 
    indicates the delimiter was found, 0 indicates no delimiter is found and 
    a -1 indicates that there is no delimiter and the queue is full. The last 
    condition is an error since the queue will never be serviced. 
    
    The parameter blocksize, if zero, indicates that the stream is record oriented,
        and that the presence of the delimiter always indicates the end of the record.
    If the blocksize is non-zero, the stream is organized as blocks of the specified
        size, and the last ndelim bytes of the block should be the delimiter. If the
        delimiter is not found in the expected location, this is a block framing error
        and the data should be dropped up to the next delimiter.
    */
{
    int found = 0;
    while (!found && q->scan_limit != q->tail) {
        char ch = q->buffer[q->scan_limit++];
        if (q->state == IN_DELIM_STATE) {
            if (ch == delim[q->pos_in_delim]) {
                q->pos_in_delim++;
                if (q->pos_in_delim == ndelim) {
                    found = 1;
                    q->pos_in_delim = 0;
                    if (blocksize) {
                        q->pos_in_block = 0;
                        q->state = IN_DATA_STATE;
                    }
                }
            }
            else {
                q->pos_in_delim = 0;
                if (blocksize) q->drop = 1;
            }
        }
        else if (q->state == IN_DATA_STATE) {
            q->pos_in_block++;
            if (q->pos_in_block >= blocksize-ndelim) {
                q->pos_in_delim = 0;
                q->state = IN_DELIM_STATE;
            }
        }
        if (q->scan_limit >= q->size) q->scan_limit -= q->size;
    }
    if (!found && q->count == q->size-1) found = -1;
    return found;
}    

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

HANDLE makeSerial(char *portName,int baud, int stopBits, int parity, int handShake)
{
    HANDLE hSerial;
    DCB dcbSerialParams = {0};
    COMMTIMEOUTS timeouts = {0};

    printf("Makeserial, name: %s, baud: %d, stopBits: %d, parity: %d, handshake: %d\n", portName, baud, stopBits, parity, handShake);
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
    dcbSerialParams.BaudRate = baud;
    dcbSerialParams.ByteSize = 8;
    if (stopBits == 1) dcbSerialParams.StopBits = ONESTOPBIT;
    else dcbSerialParams.StopBits = TWOSTOPBITS;
    
    dcbSerialParams.Parity = parity;
    dcbSerialParams.fAbortOnError = 0;
    
    if (handShake == HWHANDSHAKE) {
        dcbSerialParams.fOutxCtsFlow = 1;
        dcbSerialParams.fOutxDsrFlow = 1;
        dcbSerialParams.fDtrControl = DTR_CONTROL_HANDSHAKE;
    }
    else if (handShake == NOHANDSHAKE) {
        dcbSerialParams.fOutxCtsFlow = 0;
        dcbSerialParams.fOutxDsrFlow = 0;
        dcbSerialParams.fDtrControl = 0;
    }

    if (!SetCommState(hSerial,&dcbSerialParams)) {
        printf("Error setting state.\n");
        printError();
        return NULL;
    }
    /* Make reads non-blocking (i.e., can return zero bytes) */
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

static char *getint(const char *str,int *result)
// Get an integer at str, returning value in *result. The returned value points beyond the
//  string parsed or is NULL if an error occured
{
    char *p;
    errno = 0;
    *result = strtol(str,&p,0);
    if (errno != 0 || p == str) return 0;
    return p;
}

static char *expect(const char *str, char *patt)
{
    char *s = (char *)str;
    while ((*s == ' ') && (*s != '\0')) s++;
    if (*s == '\0') return 0;
    while ((*patt != '\0') && (*s == *patt)) {
        s++;
        patt++;
    }
    if (*patt == '\0') return s;
    return 0;
}

#ifndef TEST

#define MAXPORTS (4)
#define BUFFSIZE (256)
#define DELIM ('\n')
#define PROTOPORT   5193
#define QLEN        6

static HANDLE h[MAXPORTS];
static Queue in_queue[MAXPORTS];
static Queue out_queue;
static int port_for_wrapper = 0;

int wrapped_ReadFile(char *s, int n)
/* Read up to n characters (non-blocking) from serial port port_from_wrapper into s
    and return number of characters actually read. Returns -1 on error.
   N.B. Be sure to set up the static variables port_from_wrapper and the array
    of handles h[] before calling this function. */
{
    DWORD dwBytesRead = 0;
    if (!ReadFile(h[port_for_wrapper],s,n,&dwBytesRead,NULL)) return -1;
    return dwBytesRead;
}

int wrapped_Queue_gets(char *s, int n)
/* Read up to n characters from in_queue[port_for_wrapper] into s
    and return number of characters actually read.
   N.B. Be sure to set up the static variables port_from_wrapper and the array
    of in_queue[] before calling this function. */
{
    return Queue_gets(&in_queue[port_for_wrapper],s,n);
}
    
int processSerialPort(int port)
{
    int recvd;
    Header header;
    Queue *qp = &in_queue[port];    
    header.id = 0xA55A;
    header.port = port;
    port_for_wrapper = port;
    recvd = Queue_put_from(qp,BUFFSIZE,wrapped_ReadFile);
    if (recvd > 0) {
        while (1) {
            int found = Queue_scan_for_delim(qp,DELIM);
            if (found == 0) break;
            else if (found == 1) {
                int bytesCopied, bytesToCopy = Queue_scan_limit_position(qp);
                header.timestamp = getTimestamp();
                header.nbytes = bytesToCopy;
                if (qp->drop) { // Drop characters received after connection but before first delimiter or 
                                //  if there is a block framing error
                    qp->drop = 0;
                    Queue_drop(qp,bytesToCopy);
                }
                else {
                    if (sizeof(header) != Queue_puts(&out_queue,(char *)&header,sizeof(header))) return -1;
                    bytesCopied = Queue_put_from(&out_queue,bytesToCopy,wrapped_Queue_gets);
                    if (bytesCopied != bytesToCopy) return -1; // Disconnect on error
                }
            }
            else {
                printf("No delimiter, resetting queue\n");
                Queue_reset(qp);
            }
        }
    }
    else if (recvd < 0) {
        // Handle error from ReadFile
        recvd = 0;
    }
    return recvd;
}

int processSerialPortEx(int port,int blocksize,char *delim,int ndelim)
/* Process data from serial port which is either:
        1) A data stream of records, each terminated by the delimiter sequence delim of length ndelim
        2) A collection of blocks each of length blocksize, terminated by the delimiter sequence delim of length ndelim
   The value of blocksize is set to zero to specify the first alternative.
*/
{
    int recvd;
    Header header;
    Queue *qp = &in_queue[port];    
    header.id = 0xA55A;
    header.port = port;
    port_for_wrapper = port;
    recvd = Queue_put_from(qp,BUFFSIZE,wrapped_ReadFile);
    if (recvd > 0) {
        while (1) {
            int found = Queue_scan_for_delim_ex(qp,blocksize,delim,ndelim);
            if (found == 0) break;
            else if (found == 1) {
                int bytesCopied, bytesToCopy = Queue_scan_limit_position(qp);
                header.timestamp = getTimestamp();
                header.nbytes = bytesToCopy;
                if (qp->drop) { // Drop characters received after connection but before first delimiter or 
                                //  if there is a block framing error
                    qp->drop = 0;
                    Queue_drop(qp,bytesToCopy);
                }
                else {
                    if (sizeof(header) != Queue_puts(&out_queue,(char *)&header,sizeof(header))) return -1;
                    bytesCopied = Queue_put_from(&out_queue,bytesToCopy,wrapped_Queue_gets);
                    if (bytesCopied != bytesToCopy) return -1; // Disconnect on error
                }
            }
            else {
                printf("No delimiter, resetting queue\n");
                Queue_reset(qp);
            }
        }
    }
    else if (recvd < 0) {
        // Handle error from ReadFile
        recvd = 0;
    }
    return recvd;
}

static int handler(void *user, const char *section, const char *name, const char *value)
{
    int portnum;
    configuration *pconfig = (configuration*) user;
    #define MATCH_S(s) (stricmp(section,s) == 0)
    #define MATCH_O(s) (stricmp(name,s) == 0)
    #define MATCH(s,n) (MATCH_S(s) && MATCH_O(n))
    if (MATCH_S("ports")) {
        if (strnicmp(name,"port",4) == 0) {
            if (!getint(name+4,&portnum)) return 0;
            if (portnum >= MAXPORTS) return 0;
            pconfig->portNames[portnum] = strdup(value);
            printf("Name: %10s, value: %s\n", name,pconfig->portNames[portnum]);
        }
    }
    else if (strnicmp(section,"port",4) == 0) {
        if (!getint(section+4,&portnum)) return 0;
        if (portnum >= MAXPORTS) return 0;
        if (MATCH_O("baud")) {
            if (!getint(value,&pconfig->portBaud[portnum])) return 0;
        }
        else if (MATCH_O("stopbits")) {
            if (!getint(value,&pconfig->portStopBits[portnum])) return 0;
            if (pconfig->portStopBits[portnum] != 1 && pconfig->portStopBits[portnum] != 2) return 0;
        }
        else if (MATCH_O("parity")) {
            if (stricmp(value,"noparity") == 0) pconfig->portParity[portnum] = NOPARITY;
            else if (stricmp(value,"evenparity") == 0) pconfig->portParity[portnum] = EVENPARITY;
            else if (stricmp(value,"oddparity") == 0) pconfig->portParity[portnum] = ODDPARITY;
            else return 0;
        }
        else if (MATCH_O("handshake")) {
            if (stricmp(value,"none") == 0) pconfig->portHandshake[portnum] = NOHANDSHAKE;
            else if (stricmp(value,"hardware") == 0) pconfig->portHandshake[portnum] = HWHANDSHAKE;
            else if (stricmp(value,"software") == 0) pconfig->portHandshake[portnum] = SWHANDSHAKE;
            else return 0;
        }
        else if (MATCH_O("blocksize")) {
            if (!getint(value,&pconfig->portBlocksize[portnum])) return 0;
        }
        else if (MATCH_O("delim")) {
            char *p = (char *) value;
            int delim, bytes = 0;
            pconfig->portDelimBytes[portnum] = 0;
            while ((p=getint(p,&delim)) && bytes<MAXDELIM) {
                pconfig->portDelim[portnum][bytes++] = delim;
                // Advance past a comma, or break if none
                if (!(p=expect(p,","))) break;
            }
            if (bytes == 0 || bytes == MAXDELIM) return 0;
            pconfig->portDelimBytes[portnum] = bytes;
        }
        else return 0;
    }
    else return 0;
    return 1;
}

int main(int argc, char *argv[])
{
    char inifilename[100] = "serial2socket.ini";
    int j, n = BUFFSIZE;
    long long start;
    struct  hostent     *ptrh;  /* Pointer to a host table entry */
    struct  protoent    *ptrp;  /* Pointer to a protocol table entry */
    struct  sockaddr_in sad;    /* Structure to hold server's address */
    struct  sockaddr_in cad;    /* Structure to hold client's address */
    int     sd, sd2;            /* Socket descriptors */
    int     port;               /* Protocol port number */
    int     alen;               /* Length of address */
    int     error;
    configuration config;
    
    if (argc>=2) strncpy(inifilename,argv[2],100);
    init_config(&config);
    if ((error = ini_parse(inifilename,handler,&config))<0) {
        printf("Cannot load %s\n",inifilename);
        return 1;
    }
    else if (error != 0) {
        printf("Error in line %d of %s\n",error,inifilename);
        return 1;
    }
    
#ifdef WIN32
    WSADATA wsaData;
    WSAStartup(0x0101, &wsaData);
#endif

    memset((char *)&sad,0,sizeof(sad)); /* clear sockaddr structure */
    sad.sin_family = AF_INET;           /* set family to Internet */
    sad.sin_addr.s_addr = INADDR_ANY;   /* set the local IP address */

    /* Check command line argument for protocol port and extract port number if one is specified.
     * Otherwise, use the default given by constant PROTOPORT */

    if (argc > 1) {
        port = atoi(argv[1]);
    } else {
        port = PROTOPORT;
    }

    if (port > 0) sad.sin_port = htons((u_short)port);
    else {
        fprintf(stderr,"bad port number %s\n",argv[1]);
        exit(1);
    }

    /* Map TCP transport protocol name to protocol number */

    if (((int)(ptrp = getprotobyname("tcp"))) == 0) {
        fprintf(stderr,"cannot map \"tcp\" to protocol number\n");
        exit(1);
    }

    /* Create a socket */

    sd = socket(PF_INET, SOCK_STREAM, ptrp->p_proto);
    if (sd < 0) {
        fprintf(stderr,"socket creation failed\n");
        exit(1);
    }

    /* Bind a local address to the socket */

    if (bind(sd,(struct sockaddr *)&sad,sizeof(sad)) < 0) {
        fprintf(stderr,"bind failed\n");
        exit(1);
    }

    /* Specify size of the request queue */

    if (listen(sd,QLEN) < 0) {
        fprintf(stderr,"listen failed\n");
        exit(1);
    }

    /* Initialize queues for serial ports and socket */
    
    for (j=0; j<MAXPORTS; j++) Queue_init(&in_queue[j],BUFFSIZE);
    Queue_init(&out_queue,2*(MAXPORTS*BUFFSIZE+sizeof(Header)));

    /* Main server loop - accept and handle requests */

    while (1) {
        int goodConnection;
        goodConnection = 1;
        alen = sizeof(cad);
        if ((sd2 = accept(sd,(struct sockaddr *)&cad,&alen)) < 0) {
            fprintf(stderr,"accept failed\n");
            exit(1);
        }
        /* Open the selected serial ports */
        for (j=0; j<MAXPORTS; j++) {
            if (config.portNames[j]) h[j] = makeSerial(config.portNames[j],
                config.portBaud[j],config.portStopBits[j],config.portParity[j],
                config.portHandshake[j]);
        }
        for (j=0; j<MAXPORTS; j++) Queue_reset(&in_queue[j]);
        Queue_reset(&out_queue);
        while (goodConnection) {
            int totBytesPut = 0;
            int bytesToSend, bytesSent;
            for (j=0; j<MAXPORTS; j++) {
                int bytesPut;
                if (config.portNames[j]) {
                    bytesPut = processSerialPortEx(j,config.portBlocksize[j],config.portDelim[j],config.portDelimBytes[j]);
                    if (bytesPut < 0) { goodConnection = 0; break; }
                    totBytesPut += bytesPut;
                }
            }
            if (!goodConnection) break;
            bytesToSend = min(out_queue.count,out_queue.size-out_queue.head);
            if (bytesToSend > 0) {
                bytesSent = send(sd2,&out_queue.buffer[out_queue.head],bytesToSend,0);
                if (bytesSent < 0) { goodConnection = 0; break; }
                Queue_drop(&out_queue,bytesSent);
                if (bytesSent == bytesToSend) {
                    bytesToSend = min(out_queue.count,out_queue.size-out_queue.head);
                    if (bytesToSend > 0) {
                        bytesSent = send(sd2,&out_queue.buffer[out_queue.head],bytesToSend,0);
                        if (bytesSent < 0) { goodConnection = 0; break; }
                        Queue_drop(&out_queue,bytesSent);
                    }
                }
            }
            if (totBytesPut == 0) Sleep(10);
        }
        printf("Disconnecting...\n");
        for (j=0; j<MAXPORTS; j++) {
            if (config.portNames[j]) CloseHandle(h[j]);
        }
        closesocket(sd2);
    }
    closesocket(sd);
    return 0;
}

#else
//******************************************************************************
//  UNIT TESTS
//******************************************************************************/
void TestQueuePutGet1(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,0,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,5,q.count);
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[0]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[1]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[2]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[3]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[4]));
    CuAssertIntEquals(tc,0,Queue_get(&q,&result[5]));
    CuAssertIntEquals(tc,0,q.count);
    CuAssertStrEquals(tc,"abcde",result);
    Queue_destroy(&q);
}

void TestQueuePutGet2(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[0]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[1]));
    CuAssertIntEquals(tc,1,q.count);
    CuAssertStrEquals(tc,"ab",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,0,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,5,q.count);
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[0]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[1]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[2]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[3]));
    CuAssertIntEquals(tc,1,Queue_get(&q,&result[4]));
    CuAssertIntEquals(tc,0,Queue_get(&q,&result[5]));
    CuAssertIntEquals(tc,0,q.count);
    CuAssertStrEquals(tc,"cdefg",result);
    Queue_destroy(&q);
}

void TestQueuePutGet3(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,3,Queue_gets(&q,result,6));
    CuAssertStrEquals(tc,"abc",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,0,Queue_put(&q,'i'));
    CuAssertIntEquals(tc,5,Queue_gets(&q,result,6));
    CuAssertStrEquals(tc,"defgh",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,3,Queue_gets(&q,result,3));
    result[3] = 0;
    CuAssertStrEquals(tc,"abc",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,5,Queue_gets(&q,result,6));
    CuAssertStrEquals(tc,"defgh",result);
    Queue_destroy(&q);
}

void TestQueuePutGet4(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,3,Queue_gets_simple(&q,result,6));
    CuAssertStrEquals(tc,"abc",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,0,Queue_put(&q,'i'));
    CuAssertIntEquals(tc,5,Queue_gets_simple(&q,result,6));
    CuAssertStrEquals(tc,"defgh",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,3,Queue_gets_simple(&q,result,3));
    result[3] = 0;
    CuAssertStrEquals(tc,"abc",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,5,Queue_gets_simple(&q,result,6));
    CuAssertStrEquals(tc,"defgh",result);
    Queue_destroy(&q);
}

void TestQueueScanForDelim1(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,-1,Queue_scan_for_delim(&q,'x'));
    Queue_destroy(&q);
}
    

void TestQueueScanForDelimEx1(CuTest *tc) {
    Queue q;
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,0,"c",1));
    CuAssertIntEquals(tc,3,q.scan_limit);
    CuAssertIntEquals(tc,1,q.drop);
    q.drop = 0;
    CuAssertIntEquals(tc,3,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,3,Queue_drop(&q,3));
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,0,"de",2));
    CuAssertIntEquals(tc,5,q.scan_limit);
    CuAssertIntEquals(tc,2,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,0,q.drop);
    Queue_destroy(&q);
}

void TestQueueScanForDelimEx2(CuTest *tc) {
    Queue q;
    Queue_init(&q,16);
    CuAssertIntEquals(tc,14,Queue_puts(&q,"abcxyzbcklmbcd",14));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,5,"bc",2));
    CuAssertIntEquals(tc,1,q.drop);
    q.drop = 0;
    CuAssertIntEquals(tc,3,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,3,Queue_drop(&q,3));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,5,"bc",2));
    CuAssertIntEquals(tc,0,q.drop);
    CuAssertIntEquals(tc,5,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,5,Queue_drop(&q,5));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,5,"bc",2));
    CuAssertIntEquals(tc,0,q.drop);
    CuAssertIntEquals(tc,5,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,5,Queue_drop(&q,5));
    CuAssertIntEquals(tc,1,q.count);
    CuAssertIntEquals(tc,10,Queue_puts(&q,"efgbcxyzbc",10));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,5,"bc",2));
    CuAssertIntEquals(tc,1,q.drop);
    q.drop = 0;
    CuAssertIntEquals(tc,6,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,6,Queue_drop(&q,6));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim_ex(&q,5,"bc",2));
    CuAssertIntEquals(tc,0,q.drop);
    CuAssertIntEquals(tc,5,Queue_scan_limit_position(&q));
    CuAssertIntEquals(tc,5,Queue_drop(&q,5));
    CuAssertIntEquals(tc,0,q.count);
    Queue_destroy(&q);
}

void TestQueueScanForDelim2(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim(&q,'c'));
    CuAssertIntEquals(tc,3,q.scan_limit);
    Queue_destroy(&q);
}
    
void TestQueueScanForDelim3(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    CuAssertIntEquals(tc,1,Queue_put(&q,'a'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'b'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'c'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'d'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'e'));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim(&q,'c'));
    CuAssertIntEquals(tc,3,q.scan_limit);
    CuAssertIntEquals(tc,3,Queue_gets(&q,result,Queue_scan_limit_position(&q)));
    CuAssertStrEquals(tc,"abc",result);
    CuAssertIntEquals(tc,1,Queue_put(&q,'f'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'g'));
    CuAssertIntEquals(tc,1,Queue_put(&q,'h'));
    CuAssertIntEquals(tc,1,Queue_scan_for_delim(&q,'h'));
    CuAssertIntEquals(tc,5,Queue_gets(&q,result,Queue_scan_limit_position(&q)));
    CuAssertStrEquals(tc,"defgh",result);    
    Queue_destroy(&q);
}

static int nsource = 0;
static char csource = 'a';

int simpleSource(char *s, int n)
{
    int i;
    n = min(n,nsource);
    for (i=0; i<n; i++) s[i] = csource++;
}

void TestQueuePutFrom(CuTest *tc) {
    Queue q;
    static char result[6];
    Queue_init(&q,5);
    nsource = 3; csource = 'a';
    CuAssertIntEquals(tc,3,Queue_put_from(&q,5,simpleSource));
    CuAssertIntEquals(tc,3,Queue_gets(&q,result,5));
    CuAssertStrEquals(tc,"abc",result);
    CuAssertIntEquals(tc,0,q.count);
    nsource = 8; csource = 'a';
    CuAssertIntEquals(tc,4,Queue_put_from(&q,4,simpleSource));
    CuAssertIntEquals(tc,4,Queue_gets(&q,result,5));
    CuAssertStrEquals(tc,"abcd",result);
    nsource = 8; csource = 'f';
    CuAssertIntEquals(tc,5,Queue_put_from(&q,5,simpleSource));
    CuAssertIntEquals(tc,5,Queue_gets(&q,result,5));
    CuAssertStrEquals(tc,"fghij",result);
    Queue_destroy(&q);
}

void TestExpect(CuTest *tc) {
    static char str[20], patt[20];
    char *cp;
    int value;
    strcpy(str," , Hello");
    strcpy(patt,", H");
    cp = expect(str,patt);
    CuAssertPtrEquals(tc,str+4,cp);
    strcpy(str," , Hello");
    strcpy(patt,"H");
    cp = expect(str,patt);
    CuAssertPtrEquals(tc,0,cp);
    strcpy(str,",0xAA,0x55");
    strcpy(patt,",");
    cp = expect(str,patt);
    CuAssertPtrEquals(tc,str+1,cp);
    cp = getint(cp,&value);
    CuAssertIntEquals(tc,0xAA,value);
    CuAssertPtrEquals(tc,str+5,cp);
    cp = expect(cp,",");
    CuAssertPtrEquals(tc,str+6,cp);
    cp = getint(cp,&value);
    CuAssertIntEquals(tc,0x55,value);
}

    
CuSuite* QHandlerGetSuite() {
    CuSuite* suite = CuSuiteNew();
    SUITE_ADD_TEST(suite, TestQueuePutGet1);
    SUITE_ADD_TEST(suite, TestQueuePutGet2);
    SUITE_ADD_TEST(suite, TestQueuePutGet3);
    SUITE_ADD_TEST(suite, TestQueuePutGet4);
    SUITE_ADD_TEST(suite, TestQueueScanForDelim1);
    SUITE_ADD_TEST(suite, TestQueueScanForDelim2);
    SUITE_ADD_TEST(suite, TestQueueScanForDelim3);
    SUITE_ADD_TEST(suite, TestQueueScanForDelimEx1);
    SUITE_ADD_TEST(suite, TestQueueScanForDelimEx2);
    SUITE_ADD_TEST(suite, TestQueuePutFrom);
    SUITE_ADD_TEST(suite, TestExpect);

    return suite;
}
//******************************************************************************
//  END OF TESTS
//******************************************************************************/
#endif
