# include <stdio.h>

extern char num1;
extern short num2;
extern int num3;
extern size_t num4;

extern char* str1;

extern int func1(int a, int b, int c);
extern void func2();

int main(){
	int res = func1(1,2,3);
	printf("str1: %s\n",str1);
	func2();
	printf("hello, %d, %d, %d, %ld\n",num1,num2,num3,num4);
	printf("res: %d\n",res);
	printf("str1: %s\n",str1);
}
