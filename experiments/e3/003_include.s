	.file	"003_include.c"
	.text
	.globl	add
	.type	add, @function
add:
.LFB0:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	movl	%edi, -4(%rbp)
	movl	%esi, -8(%rbp)
	movl	-4(%rbp), %edx
	movl	-8(%rbp), %eax
	addl	%edx, %eax
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.size	add, .-add
	.globl	other_num
	.data
	.align 4
	.type	other_num, @object
	.size	other_num, 4
other_num:
	.long	15
	.globl	num2
	.align 8
	.type	num2, @object
	.size	num2, 8
num2:
	.quad	-1
	.globl	num3
	.align 4
	.type	num3, @object
	.size	num3, 4
num3:
	.long	-1
	.globl	str1
	.section	.rodata
.LC0:
	.string	"hello"
	.section	.data.rel.local,"aw",@progbits
	.align 8
	.type	str1, @object
	.size	str1, 8
str1:
	.quad	.LC0
	.globl	str2
	.section	.rodata
.LC1:
	.string	"world"
	.section	.data.rel.local
	.align 8
	.type	str2, @object
	.size	str2, 8
str2:
	.quad	.LC1
	.globl	num4
	.data
	.align 4
	.type	num4, @object
	.size	num4, 4
num4:
	.long	-1
	.globl	str3
	.section	.rodata
.LC2:
	.string	"again"
	.section	.data.rel.local
	.align 8
	.type	str3, @object
	.size	str3, 8
str3:
	.quad	.LC2
	.globl	num5
	.data
	.type	num5, @object
	.size	num5, 1
num5:
	.byte	5
	.globl	str4
	.section	.rodata
.LC3:
	.string	"argh"
	.section	.data.rel.local
	.align 8
	.type	str4, @object
	.size	str4, 8
str4:
	.quad	.LC3
	.globl	num6
	.data
	.align 2
	.type	num6, @object
	.size	num6, 2
num6:
	.value	5
	.section	.rodata
.LC4:
	.string	"%d\n"
	.text
	.globl	main
	.type	main, @function
main:
.LFB1:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	movl	other_num(%rip), %eax
	movl	$20, %esi
	movl	%eax, %edi
	call	add
	movl	%eax, other_num(%rip)
	movl	other_num(%rip), %eax
	movl	%eax, %esi
	leaq	.LC4(%rip), %rdi
	movl	$0, %eax
	call	printf@PLT
	movl	$0, %eax
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE1:
	.size	main, .-main
	.ident	"GCC: (Ubuntu 7.5.0-3ubuntu1~18.04) 7.5.0"
	.section	.note.GNU-stack,"",@progbits
