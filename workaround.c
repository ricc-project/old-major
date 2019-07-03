#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    if (fork() > 0) {
        system("oldmajor");
    } else {
        system("redemesh");
    }
}