#include "Rectangle.h"

Rectangle::Rectangle(double w, double h) : Shape()
{
   width = w;
   height = h;
}
double Rectangle::area()
{
   return(width * height);
}