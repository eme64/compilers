#include <stdio.h>

char* line1 = "world1";
char* line2 = "world2";
int number = 123;
size_t number2 = 100;
char number3 = 5;
extern int global_var_not_from_here;
extern char* global_var_other;

int main(void) {
	line1 = "asdf";
	line2 = "ghklk";
	printf("Hello, %s, %s, %d\n",line1,line2,global_var_not_from_here);
	return 0;
}

