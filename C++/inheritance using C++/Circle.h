#include "Rectangle.h"

class Circle : virtual public Shape
{
private:
   double radius;
public:
   Circle(double);
   double area();
};