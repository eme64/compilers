#include <stdio.h>

size_t test = 1;
double test2 = 1;

int main() {
	test = 10 > 20;
	if (test) {
		test = 2;
	} else {
		test = 3;
	}
	if (test2) {
		test2 = 2.1;
	}
}
