/*
 * Copyright 2012 Picarro Inc.
 */

#ifndef __CIRCULAR_BUFFER_H__
#define __CIRCULAR_BUFFER_H__

#include <stdint.h>


struct circularBuffer {
  uint8_t front;
  uint8_t rear;
  uint8_t size;
};


#define CIRC_BUF_INIT(b) \
  b.hdr.front = 0;       \
  b.hdr.rear  = 0;       \
  b.hdr.size  = sizeof(b.items) / sizeof(b.items[0])

#define CIRC_BUF_PUT(b, item) \
  b.items[b.hdr.rear] = item; \
  b.hdr.rear = (b.hdr.rear + 1) % b.hdr.size

#define CIRC_BUF_GET(b, item)  \
  item = b.items[b.hdr.front]; \
  b.hdr.front = (b.hdr.front + 1) % b.hdr.size

#define CIRC_BUF_FRONT(b, item) \
  item = b.items[b.hdr.front]

#define CIRC_BUF_EMPTY(b) (b.hdr.front == b.hdr.rear)
#define CIRC_BUF_FULL(b)  ((b.hdr.rear + 1) % b.hdr.size == b.hdr.front)

#endif /* __CIRCULAR_BUFFER_H__ */
