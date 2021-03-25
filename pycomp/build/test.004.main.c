# include <stdio.h>
# include <stdint.h>
# include <assert.h>
# include <stdlib.h>

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
extern void test_local();

extern void branch_1();
int branch_1_cond = 0;
int branch_1_res = 0;

extern void args_1(int a1, int a2);
int args_1_res = 0;

extern int return_1(int a1,int a2);
extern int return_2(int a1,int a2);
extern int return_2_err;

extern void args_001(int a1,int a2,int a3,int a4,int a5,int a6,int a7,int a8,int a9, int a10);
int args_001_res = 0;
extern void args_002(float a1,float a2,float a3,float a4,float a5,float a6,float a7,float a8,float a9, float a10);
float args_002_res = 0;

extern int array_r(int* a, int i);

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
	
	printf("\n");
	printf("test_local, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	test_local();
	printf("test_local, %d, %d, %d, %ld, %d, %ld\n",num1,num2,num3,num4,num5,num6);
	
	printf("\n");
	for(int i=-10;i<10;i++){
		printf("branch_1 %d\n",i);
		branch_1_cond = i;
		branch_1();
		printf("res: %d\n",branch_1_res);
	}
	
	printf("\n");
	for(int a1=-10;a1<10;a1++){
		for(int a2=-10;a2<10;a2++){
			args_1(a1,a2);
			assert(a1*2+a2 == args_1_res);
		}
	}

	for(int i=0;i<1000;i++){
		int a1 = rand();
		int a2 = rand();
		int a3 = rand();
		int a4 = rand();
		int a5 = rand();
		int a6 = rand();
		int a7 = rand();
		int a8 = rand();
		int a9 = rand();
		int a10 = rand();
		args_001(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10);
		assert(1*a1+2*a2+3*a3+4*a4+5*a5+6*a6+7*a7+8*a8+9*a9+10*a10 == args_001_res);
	}

	for(int i=0;i<1000;i++){
		float a1 = 0.3 * rand();
		float a2 = 0.3 * rand();
		float a3 = 0.3 * rand();
		float a4 = 0.3 * rand();
		float a5 = 0.3 * rand();
		float a6 = 0.3 * rand();
		float a7 = 0.3 * rand();
		float a8 = 0.3 * rand();
		float a9 = 0.3 * rand();
		float a10 = 0.3 * rand();
		args_002(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10);
		//printf("arg: %f %f %f %f %f %f %f %f %f %f\n",a1,a2,a3,a4,a5,a6,a7,a8,a9,a10);
		float calc = 0.0+1.0*a1+2.0*a2+3.0*a3+4.0*a4+5.0*a5+6.0*a6+7.0*a7+8.0*a8+9.0*a9+10.0*a10;
		//printf("res: calc %f res %f diff %f\n",calc, args_002_res, args_002_res-calc);
		//printf("arg: %f %f %f %f %f %f %f %f %f %f\n",a1,a2,a3,a4,a5,a6,a7,a8,a9,a10);
		assert(calc == args_002_res);
	}

	for(int a1=-10;a1<10;a1++){
		for(int a2=-10;a2<10;a2++){
			int r = return_1(a1,a2);
			assert(r == 2*a1+3*a2);
		}
	}
	for(int a1=-10;a1<10;a1++){
		for(int a2=-10;a2<10;a2++){
			int r = return_2(a1,a2);
			assert(return_2_err==0);
			if(a1){assert(r==a2+1);}else{assert(r==a2+2);}
		}
	}

	int* a = (int*)malloc(100*sizeof(int));
	for(int i=0;i<100;i++){
		a[i]=i;
	}
	for(int i=0;i<100;i++){
		int val = array_r(a,i);
		//printf("%d %d %d\n",i,val,a[i]);
		assert(a[i] == val);
	}
}


