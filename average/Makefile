all: average

average: main.o
	ld main.o -o average

main.o: main.asm
	nasm -f elf64 main.asm -o main.o

run: average
	./average data.txt

clean:
	rm -f main.o average