#ifndef N2_LOCAL_ELF32_H
#define N2_LOCAL_ELF32_H
#include <stdint.h>
/* ELF32 file-layout definitions; host tools use little-endian ELF32 only. */
#define ELFMAG "\177ELF"
#define SELFMAG 4
#define PT_LOAD 1
typedef struct { unsigned char e_ident[16]; uint16_t e_type,e_machine;
uint32_t e_version,e_entry,e_phoff,e_shoff,e_flags;
uint16_t e_ehsize,e_phentsize,e_phnum,e_shentsize,e_shnum,e_shstrndx;
} Elf32_Ehdr;
typedef struct {uint32_t p_type,p_offset,p_vaddr,p_paddr,p_filesz,p_memsz,p_flags,p_align;} Elf32_Phdr;
#define SHT_SYMTAB 2
typedef struct {uint32_t sh_name,sh_type,sh_flags,sh_addr,sh_offset,sh_size,sh_link,sh_info,sh_addralign,sh_entsize;} Elf32_Shdr;
typedef struct {uint32_t st_name,st_value,st_size;unsigned char st_info,st_other;uint16_t st_shndx;} Elf32_Sym;
#endif
