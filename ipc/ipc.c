#include "ipc.h"

#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define quq(__syscall, ...) _quq(#__syscall, __syscall(__VA_ARGS__))

static int _quq(const char *name, int ret)
{
    if (ret == -1) {
        fprintf(stderr, "%s() failed > < [errno %d]\n", name, errno);
        exit(1);
    }
    return ret;
}

static inline long diff_ms(const struct timespec t1, const struct timespec t2)
{
    long ret = (t2.tv_sec - t1.tv_sec) * 1000;
    ret += (1000000000 + t2.tv_nsec - t1.tv_nsec) / 1000000 - 1000;
    return ret;
}

static inline char tenacious_write(int fd, const char *buf, size_t len)
{
    size_t ptr = 0;
    while (ptr < len) {
        ssize_t written = write(fd, buf + ptr, len - ptr);
        if (written == -1) return -1;
        ptr += written;
    }
    return 0;
}

int ipc_send(int pipe, size_t len, const char *payload)
{
    if (len == 0) len = strlen(payload);
    if (len > 0xffffff) return IPC_ERR_TOOLONG;
    char len_buf[3] = {
        len & 0xff,
        (len >> 8) & 0xff,
        (len >> 16) & 0xff
    };
    if (tenacious_write(pipe, len_buf, 3) < 0 ||
        tenacious_write(pipe, payload, len) < 0)
    {
        fprintf(stderr, "write() failed with errno %d\n", errno);
        return IPC_ERR_SYSCALL;
    }
    return IPC_ERR_NONE;
}

char *ipc_recv(int pipe, size_t *o_len, int timeout)
{
    struct pollfd pfd = (struct pollfd){pipe, POLLIN, 0};
    char *ret = NULL;
    size_t len = 0, ptr = 0;
    char buf[4];
    struct timespec t1, t2;
    int loops = 0;

    while (len == 0 || ptr < len) {
        /* Unlikely; in case poll()'s time slightly differs
           from CLOCK_MONOTONIC, or rounding errors happen */
        if ((timeout <= 0 || ++loops >= 1000000) && timeout != -1) {
            fprintf(stderr, "Unidentifiable exception with errno %d\n", errno);
            if (ret) free(ret);
            *o_len = IPC_ERR_SYSCALL;
            return NULL;
        }

        /* Keep time */
        clock_gettime(CLOCK_MONOTONIC, &t1);
        /* Wait for reading */
        pfd.revents = 0;
        int poll_ret = poll(&pfd, 1, timeout);
        if (poll_ret == -1) {
            fprintf(stderr, "poll() failed with errno %d\n", errno);
            if (ret) free(ret);
            *o_len = IPC_ERR_SYSCALL;
            return NULL;
        }
        /* Calculate remaining time */
        clock_gettime(CLOCK_MONOTONIC, &t2);
        if (timeout > 0) timeout -= diff_ms(t1, t2);

        /* Is the pipe still open on the other side? */
        if (pfd.revents & POLLHUP) {
            if (ret) free(ret);
            *o_len = IPC_ERR_CLOSED;
            return NULL;
        }

        if (poll_ret == 1 && (pfd.revents & POLLIN)) {
            /* Ready for reading! Let's see */
            ssize_t read_len;

            if (ret == NULL) {
                read_len = read(pipe, buf, 3);
            } else {
                read_len = read(pipe, ret + ptr, len - ptr);
            }

            if (read_len == -1) {
                fprintf(stderr, "read() failed with errno %d\n", errno);
                if (ret) free(ret);
                *o_len = IPC_ERR_SYSCALL;
                return NULL;
            }

            if (ret == NULL) {
                if (read_len < 3) {
                    /* Invalid */
                    if (ret) free(ret);
                    *o_len = IPC_ERR_FMT;
                    return NULL;
                }
                /* Parse the length */
                len = ((unsigned char)buf[2] << 16) |
                    ((unsigned char)buf[1] << 8) |
                    (unsigned char)buf[0];
                ret = (char *)malloc(len + 1);
                if (len == 0) break;    /* Nothing to read */
            } else {
                /* Move buffer pointer */
                ptr += read_len;
            }
        } else {
            if (ret) free(ret);
            if (timeout <= 0) {
                *o_len = IPC_ERR_TIMEOUT;
            } else {
                fprintf(stderr, "poll() returns unexpected events %d\n", pfd.revents);
                *o_len = IPC_ERR_SYSCALL;
            }
            return NULL;
        }
    }

    *o_len = len;
    ret[len] = '\0';
    return ret;
}

void ipc_send_str(const char *s)
{
    ipc_send(STDOUT_FILENO, 0, s);
}

char *ipc_recv_str()
{
    size_t len;
    char *ret = ipc_recv(STDIN_FILENO, &len, -1);
    return ret;
}
