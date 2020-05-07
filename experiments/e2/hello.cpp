// I'm learning from here:
// https://solarianprogrammer.com/2018/01/10/writing-minimal-x86-64-jit-compiler-cpp/

#include <iostream>
#include <string>
#include <unistd.h>
#include <vector>
#include <sys/mman.h>

size_t estimate_memory_size(size_t machine_code_size) {
   size_t page_size_multiple = sysconf(_SC_PAGE_SIZE);     // Get the machine page size
   size_t factor = 1, required_memory_size;
   
   for(;;) {
      required_memory_size = factor * page_size_multiple;
      if(machine_code_size <= required_memory_size) break;
      factor++;
   }
   return required_memory_size;
}

int main() {
   std::cout << "hello!\n";
   
   std::string hello_name = "asdf zuyt...?\n";

   std::vector<uint8_t> machine_code {
      0x48, 0xc7, 0xc0, 0x01, 0x00, 0x00, 0x00, // use write syscall
      0x48, 0xc7, 0xc7, 0x01, 0x00, 0x00, 0x00, // write to stdout
      0x48, 0x8d, 0x35, 0x0a, 0x00, 0x00, 0x00, // offset: a = 10 -> 10 bytes after this instruction
      0x48, 0xc7, 0xc2, 0x00, 0x00, 0x00, 0x00, // last four items are for message size
      0x0f, 0x05, // syscall
      0xc3 // ret
   };
 
   size_t message_size = hello_name.length();
   machine_code[24] = (message_size & 0xFF) >> 0;
   machine_code[25] = (message_size & 0xFF00) >> 8;
   machine_code[26] = (message_size & 0xFF0000) >> 16;
   machine_code[27] = (message_size & 0xFF000000) >> 24;
  
   for(auto c : hello_name) {
      machine_code.emplace_back(c);
   }
   
   size_t required_memory_size = estimate_memory_size(machine_code.size());

   uint8_t *mem = (uint8_t*) mmap(NULL, required_memory_size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS ,-1, 0);
   if(mem == MAP_FAILED) {
      std::cerr << "Can't allocate memory\n"; std::exit(1);
   }
   
   // Copy the generated machine code to the executable memory
   for(size_t i = 0; i < machine_code.size(); ++i) {
      mem[i] = machine_code[i];
   }
   
   void (*func)();
   func = (void (*)()) mem;
   func();

   munmap(mem, required_memory_size);

   std::cout << "end.\n";
}
