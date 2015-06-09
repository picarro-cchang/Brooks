#ifndef _RDHANDLERS_H_
#define _RDHANDLERS_H_

typedef struct QUEUE_INT
{
    int *queueArray;
    int head;
    int tail;
    int count;
    int size;
} QueueInt;

extern QueueInt bankQueue;
extern QueueInt rdBufferQueue;

void init_queue(QueueInt *q,int *array,int size);
int put_queue(QueueInt *q,int datum);
int get_queue(QueueInt *q,int *datumRef);

void edmaDoneInterrupt(int tccNum);
void edmaInit(void);
void ringdownInterrupt(unsigned int funcArg, unsigned int eventId);
void acqDoneInterrupt(unsigned int funcArg, unsigned int eventId);

void rdDataMoving(void);

#endif /* _RDHANDLERS_H_ */
