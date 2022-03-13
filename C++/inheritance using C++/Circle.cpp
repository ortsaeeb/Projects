#include "Circle.h"

Circle::Circle(double r) : Shape()
{
   radius = r;
}
double Circle::area()
{
   return(3.141 * radius * radius);
}