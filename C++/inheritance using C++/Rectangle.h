#include "Shape.h"

class Rectangle : virtual public Shape
{
private:
   double width, height;
public:
   Rectangle(double, double);
   double area();
};
