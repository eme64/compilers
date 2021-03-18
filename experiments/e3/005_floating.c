#include <stdio.h>

float num1 = 1.1;
double num2 = 2.2;
size_t num3 = 100;

char num01 = 5;
short num02 = 1000;
int num03 = 1000000;

short num001 = 10;
int num002 = -200;
signed int num003 = 0;
unsigned int num004 = 10;

unsigned short num005 = 20;
signed short num006 = -30;

int main() {
	printf("hello\n");
	num1 = 4.3;
	num2 = 3.3;
	num3 = 2000;

	num01 = 10;
	num02 = 2000;
	num03 = 2000000;

	num3 = num3 + 100;

	num1 = num1 + 0.5;
	
	num003 = num001 + num002;
	num004 = num003;
	num005 = num006;
	num006 = num005;

	num005 = num004;
}


