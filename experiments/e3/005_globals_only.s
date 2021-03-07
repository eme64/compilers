	.file	"005_globals_only.c"
	.text
	.globl	v1
	.data
	.align 4
	.type	v1, @object
	.size	v1, 4
v1:
	.long	100
	.globl	v2
	.align 4
	.type	v2, @object
	.size	v2, 4
v2:
	.long	200
	.globl	v3
	.align 8
	.type	v3, @object
	.size	v3, 8
v3:
	.quad	300
	.globl	v4
	.type	v4, @object
	.size	v4, 1
v4:
	.byte	5
	.ident	"GCC: (Ubuntu 7.5.0-3ubuntu1~18.04) 7.5.0"
	.section	.note.GNU-stack,"",@progbits
