#ifndef MATRIX_H
#define MATRIX_H
#include<iostream>
#include<stdlib.h>
using namespace std;

class Matrix
{

int myArray[3][3]; // declaring my 3x3 matrix

public:
    void toString();
    Matrix();
    Matrix operator*(Matrix);
};

#endif