#include "ArrayList.h"
#include<iostream>
using namespace std;
int main()
{
   ArrayList obj;
   int value;

   cout << "Enter values for the array" << endl;

   for (int i = 0; i < 5; i++)
   {
       cout << "Elements" << i + 1 << ":";
       cin >> value;
       obj.push(value);
   }

   obj.toString();
   obj.erase(5);

   cout << "After erasing 4" << endl;
   obj.toString();
   
   cout<<"Assignment 2"<<endl;
}