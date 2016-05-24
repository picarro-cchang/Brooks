/*
 * server.c
 *
 */

#ifndef unix
#define WIN32
#include <windows.h>
#include <winsock2.h>
#else
#define closesocket close
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#endif

#include <stdio.h>
#include <string.h>

#define PROTOPORT   5193
#define QLEN        6

int visits = 0;

int main(int argc, char *argv[])
{
    struct  hostent     *ptrh;  /* Pointer to a host table entry */
    struct  protoent    *ptrp;  /* Pointer to a protocol table entry */
    struct  sockaddr_in sad;    /* Structure to hold server's address */
    struct  sockaddr_in cad;    /* Structure to hold client's address */
    int     sd, sd2;            /* Socket descriptors */
    int     port;               /* Protocol port number */
    int     alen;               /* Length of address */
    char    buf[1000];          /* Buffer for string the server sends */

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

    /* Main server loop - accept and handle requests */

    while (1) {
        alen = sizeof(cad);
        if ((sd2 = accept(sd,(struct sockaddr *)&cad,&alen)) < 0) {
            fprintf(stderr,"accept failed\n");
            exit(1);
        }
        visits++;
        sprintf(buf,"This server has been contacted %d time%s\n",
                visits,visits==1?".":"s.");
        send(sd2,buf,strlen(buf),0);
        closesocket(sd2);
    }
}
