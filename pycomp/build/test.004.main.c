# include <stdio.h>

extern char num1;
extern short num2;
extern int num3;
extern size_t num4;
extern int num5;
extern size_t num6;


int main(){
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
}


