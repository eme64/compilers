#include <stdio.h>

char* line = "world";
int number = 123;
size_t number2 = 100;
char number3 = 5;
extern int global_var_not_from_here;
extern char* global_var_other;

int main(void) {
	line = "asdf";
	printf("Hello, %s, %d\n",line,global_var_not_from_here);
	return 0;
}

