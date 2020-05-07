.global _start

.text
_start:
mov $1, %rax #write
mov $1, %rdi #stdout
mov $message, %rsi # string
mov $13, %rdx # length of string
syscall
ret

message:
.ascii "Hello, world\n"
