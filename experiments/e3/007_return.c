#include <stdio.h>

#define T size_t

T res = 0;
void f011(T a1) {res = a1;}
void f021(T a1,T a2) {res = a1;}
void f022(T a1,T a2) {res = a2;}
void f031(T a1,T a2,T a3) {res = a1;}
void f032(T a1,T a2,T a3) {res = a2;}
void f033(T a1,T a2,T a3) {res = a3;}
void f042(T a1,T a2,T a3,T a4) {res = a2;}
void f052(T a1,T a2,T a3,T a4,T a5) {res = a2;}
void f055(T a1,T a2,T a3,T a4,T a5) {res = a5;}
void f061(T a1,T a2,T a3,T a4,T a5,T a6) {res = a1;}
void f066(T a1,T a2,T a3,T a4,T a5,T a6) {res = a6;}
void f071(T a1,T a2,T a3,T a4,T a5,T a6,T a7) {res = a1;}
void f077(T a1,T a2,T a3,T a4,T a5,T a6,T a7) {res = a7;}
void f081(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8) {res = a1;}
void f087(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8) {res = a7;}
void f088(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8) {res = a8;}
void f091(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8,T a9) {res = a9;}
void f097(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8,T a9) {res = a7;}
void f098(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8,T a9) {res = a8;}
void f099(T a1,T a2,T a3,T a4,T a5,T a6,T a7,T a8,T a9) {res = a9;}

#define A int
#define B float
void f1_a1(A a1,A a2,A a3,A a4,A a5,A a6,A a7,A a8,B b1,B b2,B b3,B b4,B b5,B b6,B b7,B b8,B b9){res = a1;}
void f1_a7(A a1,A a2,A a3,A a4,A a5,A a6,A a7,A a8,B b1,B b2,B b3,B b4,B b5,B b6,B b7,B b8,B b9){res = a7;}
void f1_b1(A a1,A a2,A a3,A a4,A a5,A a6,A a7,A a8,B b1,B b2,B b3,B b4,B b5,B b6,B b7,B b8,B b9){res = b1;}
void f1_b9(A a1,A a2,A a3,A a4,A a5,A a6,A a7,A a8,B b1,B b2,B b3,B b4,B b5,B b6,B b7,B b8,B b9){res = b9;}

void f2_a1(A a1,B b1,A a2,B b2,A a3,B b3,A a4,B b4,A a5,B b5,A a6,B b6,A a7,B b7,A a8,B b8,B b9){res = a1;}
void f2_a8(A a1,B b1,A a2,B b2,A a3,B b3,A a4,B b4,A a5,B b5,A a6,B b6,A a7,B b7,A a8,B b8,B b9){res = a8;}
void f2_b1(A a1,B b1,A a2,B b2,A a3,B b3,A a4,B b4,A a5,B b5,A a6,B b6,A a7,B b7,A a8,B b8,B b9){res = b1;}
void f2_b9(A a1,B b1,A a2,B b2,A a3,B b3,A a4,B b4,A a5,B b5,A a6,B b6,A a7,B b7,A a8,B b8,B b9){res = b9;}

int main() {
	printf("hello world\n");
}
