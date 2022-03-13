#include <iostream>

class ArrayList 
{
    private:
        int *ptr;
        int arraySize;
        int Capacity;
        
    public:
        ArrayList();
        
        void push(int m);
        void erase(int m);
        void toString();
        bool isFull();
        
};