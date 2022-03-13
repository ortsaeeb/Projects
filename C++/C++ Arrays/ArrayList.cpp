#include "ArrayList.h"
#include<iostream>
using namespace std;


ArrayList::ArrayList()
{
   Capacity= 1;
   arraySize = 0;
   ptr = new int[Capacity];

}

void ArrayList::push(int m)
{
  
   if (isFull())
   {
       cout << "Doubling the arrays" << endl;
       int newCap = Capacity * 2;
       int* temp = new int[newCap];// points to temp

       for (int i = 0; i < Capacity; i++)
       {
           temp[i] = ptr[i];
       }
       Capacity = newCap;// creating a new Capacity
       
       ptr = new int[Capacity];
       for (int i = 0; i < arraySize; i++)
       {
           ptr[i] = temp[i];
       }

   }

   else
   {
       ptr[arraySize] = m;
       arraySize++;

   }
}
void ArrayList::erase(int m)
{
   int i;

   for ( i = 0; i < arraySize; i++)
   {
       if (ptr[i] == m)
       {
           break;

       }
   }


   arraySize= arraySize - 1;
}

void ArrayList::toString()
{
   cout << "Elements in the Array" << endl;

   for (int i = 0; i < arraySize; i++)
   {
       cout << ptr[i] << ":";
   }
}

bool ArrayList::isFull()
{
   if (arraySize == Capacity)
   {
       return true;
       cout<<" Array is equal to Capacity" << endl;
   }

   else
   {
       return false;
        cout<<" Array is not equal to Capacity" << endl;
   }
}

