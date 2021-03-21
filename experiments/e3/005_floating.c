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

void help();

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
	num1 = num1 - 0.5;
	num1 = num1 * 0.5;
	num1 = num1 / 0.5;
	
	size_t tmp1 = 5;
	num3 = num3 + tmp1;
	num3 = num3 - tmp1;
	num3 = num3 * tmp1;
	num3 = num3 / tmp1;
	
	unsigned char tmp2 = 5;
	unsigned char var2 = 5;
	var2 += tmp2;
	var2 -= tmp2;
	var2 *= tmp2;
	var2 /= tmp2;


	num003 = num001 + num002;
	num004 = num003;
	num005 = num006;
	num006 = num005;

	num005 = num004;
	
	help();
}

unsigned int h_uint_001 = 100;
signed   int h_sint_001 = -100;

signed char h_sb_001 = -5;

float  h_f_001 = 5;
double h_d_001 = -5;

void help() {
	h_f_001 = h_uint_001;
	h_d_001 = h_uint_001;
	h_f_001 = h_sint_001;
	h_d_001 = h_sint_001;
	
	h_sint_001 = h_f_001;
	h_sint_001 = h_d_001;
	h_sb_001 = h_f_001;
	h_sb_001 = h_d_001;

	h_f_001 = h_d_001;
	h_d_001 = h_f_001;

	h_uint_001 = h_f_001;
	h_uint_001 = h_d_001;
}
