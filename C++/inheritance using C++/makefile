CC=g++
CFLAGS=-std=c++11

shape: main.o Circle.o Rectangle.o
    g++ -std=c++11 main.o Circle.o Rectangle.o -o out
main.o:main.cpp
    $(CC) $(CFLAGS) -c main.cpp
Circle.o:Circle.cpp
    $(CC) $(CFLAGS) -c Circle.cpp
Rectangle.o:Rectangle.cpp
    $(CC) $(CFLAGS) -c Rectangle.cpp
clean:
	rm *.o out