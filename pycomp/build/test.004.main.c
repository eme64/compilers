# include <stdio.h>

extern char num1;
extern short num2;
extern int num3;
extern size_t num4;
extern int num5;
extern size_t num6;
extern double num7;
extern float num8;
extern float num9;

extern void func1();

int main(){
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	printf("hello, %f, %f, %f\n",num7,num8,num9);
	func1();
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	printf("hello, %f, %f, %f\n",num7,num8,num9);
}


