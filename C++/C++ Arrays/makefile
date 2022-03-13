CC=g++
CFLAGS=-std=c++11

shape: ArrayList.o
    g++ -std=c++11 ArrayList.o -o out
ArrayList.o:ArrayList.cpp
    $(CC) $(CFLAGS) -c ArrayList.cpp
clean:
	rm *.o out