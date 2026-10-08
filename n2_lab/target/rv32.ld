ENTRY(_start)
PROVIDE(__stack_reserve = 400);
SECTIONS {
 . = 0x1000;
 __image_start = .;
 .text : { *(.text*) }
 .rodata : ALIGN(4) { *(.rodata*) *(.srodata*) . = ALIGN(4); }
 .data : ALIGN(4) { *(.data*) *(.sdata*) . = ALIGN(4); }
 .bss (NOLOAD) : ALIGN(4) { *(.bss*) *(.sbss*) *(COMMON) . = ALIGN(4); }
 .stack (NOLOAD) : ALIGN(16) {
   __stack_bottom = .; . += __stack_reserve; __stack_top = .;
 }
 __image_end = .;
 /DISCARD/ : { *(.comment) *(.eh_frame*) }
 ASSERT((__image_end - __image_start + 3500) <= 131072, "Total guest image + stack + conservative LED budget exceeded")
}
