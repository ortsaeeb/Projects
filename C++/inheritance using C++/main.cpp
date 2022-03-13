#include "Circle.h"

int main()
{
   Rectangle rectangle(10, 10);
   cout << "Rectangle Area: " << rectangle.area() << endl;
  
   Circle circle(20);
   cout << "Circle Area: " << circle.area() << endl;
   return 0;
}