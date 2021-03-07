	.file	"001_globals.c"
	.text
	.globl	line
	.section	.rodata
.LC0:
	.string	"world"
	.section	.data.rel.local,"aw",@progbits
	.align 8
	.type	line, @object
	.size	line, 8
line:
	.quad	.LC0
	.globl	number
	.data
	.align 4
	.type	number, @object
	.size	number, 4
number:
	.long	123
	.globl	number2
	.align 8
	.type	number2, @object
	.size	number2, 8
number2:
	.quad	100
	.globl	number3
	.type	number3, @object
	.size	number3, 1
number3:
	.byte	5
	.section	.rodata
.LC1:
	.string	"asdf"
.LC2:
	.string	"Hello, %s, %d\n"
	.text
	.globl	main
	.type	main, @function
main:
.LFB0:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	leaq	.LC1(%rip), %rax
	movq	%rax, line(%rip)
	movl	global_var_not_from_here(%rip), %edx
	movq	line(%rip), %rax
	movq	%rax, %rsi
	leaq	.LC2(%rip), %rdi
	movl	$0, %eax
	call	printf@PLT
	movl	$0, %eax
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.size	main, .-main
	.ident	"GCC: (Ubuntu 7.5.0-3ubuntu1~18.04) 7.5.0"
	.section	.note.GNU-stack,"",@progbits
