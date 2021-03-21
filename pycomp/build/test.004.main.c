# include <stdio.h>
# include <stdint.h>

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
extern void func2();
extern void func3();
extern void func_cast_0();
extern void func_cast_1();
extern void func_cast_2();
extern void func_cast_3();

extern uint64_t var000;
extern int64_t var001;
extern float  var002;
extern double var003;

int main(){
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	printf("hello, %f, %f, %f\n",num7,num8,num9);
	func1();
	printf("after func1 call\n");
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	printf("hello, %f, %f, %f\n",num7,num8,num9);
	func2();
	printf("after func2 call\n");
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	printf("hello, %f, %f, %f\n",num7,num8,num9);
	func3();
	printf("after func3 call\n");
	printf("hello, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	printf("hello, %f, %f, %f\n",num7,num8,num9);
	printf("\n");
	printf("vars: %ld, %lu, %f, %lf\n",var000,var001,var002,var003);
	var000 = 1234567890;
	func_cast_0();
	printf("vars: %ld, %lu, %f, %lf\n",var000,var001,var002,var003);
	var001 = 321;
	func_cast_1();
	printf("vars: %ld, %lu, %f, %lf\n",var000,var001,var002,var003);
	var002 = 876.5432;
	func_cast_2();
	printf("vars: %ld, %lu, %f, %lf\n",var000,var001,var002,var003);
	var003 = 12345.678;
	func_cast_3();
	printf("vars: %ld, %lu, %f, %lf\n",var000,var001,var002,var003);
}


