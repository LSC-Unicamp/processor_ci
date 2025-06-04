# addi implementation
.text

.global _start;

_start:
    addi a1, zero, 5; # a1 = zero + 5

    nop;
    nop;
    nop; # 3 nops to not cause forwarding

    sw a1, 60(zero);